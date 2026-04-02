"""Scaffold a .projio workspace inside a project directory."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import get_nested, load_effective_config, load_project_config

KIND_CHOICES = ("generic", "tool", "study")
SITE_FRAMEWORK_CHOICES = ("mkdocs", "sphinx", "vite")

KNOWN_PACKAGES = ("biblio", "notio", "codio", "indexio", "pipeio", "claude")

PROFILES: dict[str, tuple[str, ...]] = {
    "research": ("notio", "biblio", "indexio"),
    "full": ("notio", "biblio", "codio", "indexio", "pipeio"),
}

BASE_PROJIO_CONFIG = """\
# projio workspace config
project_name: {name}
project_kind: {kind}
description: ""

indexio:
  config: .projio/indexio/config.yaml
  persist_dir: .projio/indexio/index

biblio:
  enabled: true
  config: .projio/biblio/biblio.yml

notio:
  enabled: true
  notes_dir: notes/
  template_dir: .projio/notio/templates

codio:
  enabled: true
  catalog_path: .projio/codio/catalog.yml
  profiles_path: .projio/codio/profiles.yml
  notes_dir: docs/reference/codelib/libraries/

pipeio:
  enabled: true
  registry_path: .projio/pipeio/registry.yml
  pipelines_dir: code/pipelines

code:
  project_utils: ""

site:
  framework: {site_framework}
  output_dir: {site_output_dir}
  base_port: 8000
  host: "127.0.0.1"
  mkdocs:
    config_file: mkdocs.yml
    site_dir: site
  sphinx:
    source_dir: docs
    build_dir: docs/_build/html
  vite:
    app_dir: {vite_app_dir}
    build_dir: site
  chatbot:
    enabled: false
    backend_url: null
    host: "127.0.0.1"
    port: 9100
    title: "Docs Assistant"
    storage_key: "{name}_chat_v1"

runtime:
  python_bin: null

helpers:
  sibling:
    github:
      sibling: github
      credential: github
      project_template: "{{project_name}}"
    gitlab:
      sibling: gitlab
      credential: gitlab
      project_template: "{{project_name}}"
    ria:
      sibling: origin
      alias_strategy: basename
  docs:
    mkdocs:
      enabled: false
"""

STUDY_PROJIO_CONFIG = """\
# projio workspace config
project_name: {name}
project_kind: study
description: ""

indexio:
  config: .projio/indexio/config.yaml
  persist_dir: .projio/indexio/index

biblio:
  enabled: false
  config: .projio/biblio/biblio.yml

notio:
  enabled: false
  notes_dir: notes/
  template_dir: .projio/notio/templates

site:
  framework: {site_framework}
  output_dir: {site_output_dir}
  base_port: 8000
  host: "127.0.0.1"
  mkdocs:
    config_file: mkdocs.yml
    site_dir: site
  sphinx:
    source_dir: docs
    build_dir: docs/_build/html
  vite:
    app_dir: {vite_app_dir}
    build_dir: site
  chatbot:
    enabled: false
    backend_url: null
    host: "127.0.0.1"
    port: 9100
    title: "Docs Assistant"
    storage_key: "{name}_chat_v1"

runtime:
  python_bin: null

helpers:
  sibling:
    github:
      sibling: github
      credential: github
      project_template: "{{project_name}}"
    gitlab:
      sibling: gitlab
      credential: gitlab
      project_template: "{{project_name}}"
    ria:
      sibling: origin
      alias_strategy: basename
  docs:
    mkdocs:
      enabled: false
"""

PROJIO_MK = """\
# projio.mk — shared targets, managed by projio
# Include from your Makefile: -include .projio/projio.mk

PYTHON  ?= python
DATALAD ?= datalad
MKDOCS  ?= $(PYTHON) -m mkdocs
PROJIO  ?= $(PYTHON) -m projio
NOTIO   ?= $(PYTHON) -m notio
PANDOC  ?= pandoc
PUBLISH ?= $(PYTHON) -m twine upload
MSG     ?= Update

PANDOC_FILTER ?= .projio/filters/include.lua

.PHONY: save push url
.PHONY: projio-init projio-config-user projio-config-show projio-status projio-auth
.PHONY: projio-gh projio-gl projio-ria site-build site-serve site-stop site-list site-detect mcp mcp-config

# --- DataLad targets ---
save:
\t$(DATALAD) save -m "$(MSG)"

push:
\t$(DATALAD) push --to github

url:
\t$(PROJIO) url -C .

# --- Projio targets ---
projio-init:
\t$(PROJIO) init .

projio-config-user:
\t$(PROJIO) config init-user

projio-config-show:
\t$(PROJIO) config -C . show

projio-status:
\t$(PROJIO) status -C .

projio-auth:
\t$(PROJIO) auth -C . doctor

projio-gh:
\t$(PROJIO) sibling -C . github

projio-gl:
\t$(PROJIO) sibling -C . gitlab

projio-ria:
\t$(PROJIO) sibling -C . ria

site-build:
\t$(PROJIO) site build -C .

site-serve:
\t$(PROJIO) site serve -C .

site-stop:
\t$(PROJIO) site stop -C . --all

site-list:
\t$(PROJIO) site list -C .

site-detect:
\t$(PROJIO) site detect -C .

mcp:
\t$(PROJIO) mcp -C .

mcp-config:
\t$(PROJIO) mcp-config -C . --yes
"""

def _detect_manuscripts(root: Path) -> list[str]:
    """Return manuscript names found under docs/manuscript/*/manuscript.yml."""
    manuscript_dir = root / "docs" / "manuscript"
    if not manuscript_dir.is_dir():
        return []
    names = []
    for child in sorted(manuscript_dir.iterdir()):
        if child.is_dir() and (child / "manuscript.yml").is_file():
            names.append(child.name)
    return names


def _detect_masters(root: Path) -> list[str]:
    """Return master document names found under docs/*/master.md."""
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return []
    names = []
    for child in sorted(docs_dir.iterdir()):
        if child.is_dir() and (child / "master.md").is_file():
            # Exclude manuscript/ — those use manuscripto, not master build
            if child.name != "manuscript":
                names.append(child.name)
    return names


def _manuscript_targets(manuscripts: list[str]) -> str:
    """Generate Make targets for manuscripto-managed manuscripts."""
    if not manuscripts:
        return ""
    lines = ["\n# --- Manuscript targets (manuscripto) ---"]
    phony = []
    for name in manuscripts:
        ms_dir = f"docs/manuscript/{name}"
        phony.extend([f"manuscript-{name}-assemble", f"manuscript-{name}-pdf",
                       f"manuscript-{name}-latex", f"manuscript-{name}-validate"])
        lines.append(f"""
manuscript-{name}-assemble: {ms_dir}/manuscript.yml
\t@echo ">> Assembling manuscript: {name}"
\t@$(NOTIO) --root . manuscript assemble {name}

manuscript-{name}-pdf: {ms_dir}/manuscript.yml $(PANDOC_FILTER)
\t@echo ">> Building manuscript PDF: {name}"
\t@$(NOTIO) --root . manuscript assemble {name}
\t@mkdir -p _build/pdf
\t@$(PANDOC) {ms_dir}/_build/assembled.md $(PANDOC_COMMON_ARGS) $(PDF_ENGINE_ARGS) -o _build/pdf/{name}.pdf

manuscript-{name}-latex: {ms_dir}/manuscript.yml $(PANDOC_FILTER)
\t@echo ">> Building manuscript LaTeX: {name}"
\t@$(NOTIO) --root . manuscript assemble {name}
\t@mkdir -p _build/latex
\t@$(PANDOC) {ms_dir}/_build/assembled.md $(PANDOC_COMMON_ARGS) -t latex -o _build/latex/{name}.tex

manuscript-{name}-validate: {ms_dir}/manuscript.yml
\t@$(NOTIO) --root . manuscript validate {name}""")

    lines.insert(1, f".PHONY: {' '.join(phony)}")
    return "\n".join(lines) + "\n"


def _master_targets(masters: list[str]) -> str:
    """Generate Make targets for dual-marker master documents."""
    if not masters:
        return ""
    lines = ["\n# --- Master document targets (Lua transclusion) ---"]
    phony = []
    for name in masters:
        phony.extend([f"{name}-pdf", f"{name}-latex", f"{name}-md"])
        lines.append(f"""
{name}-pdf: docs/{name}/master.md $(PANDOC_FILTER)
\t@echo ">> Building {name} PDF"
\t@mkdir -p _build/pdf
\t@$(PANDOC) docs/{name}/master.md $(PANDOC_COMMON_ARGS) $(PDF_ENGINE_ARGS) -o _build/pdf/{name}-master.pdf

{name}-latex: docs/{name}/master.md $(PANDOC_FILTER)
\t@echo ">> Building {name} LaTeX"
\t@mkdir -p _build/latex
\t@$(PANDOC) docs/{name}/master.md $(PANDOC_COMMON_ARGS) -t latex -o _build/latex/{name}-master.tex

{name}-md: docs/{name}/master.md $(PANDOC_FILTER)
\t@echo ">> Building {name} resolved Markdown"
\t@mkdir -p _build/md
\t@$(PANDOC) docs/{name}/master.md --lua-filter=$(PANDOC_FILTER) -t gfm --wrap=none -o _build/md/{name}-master.md""")

    lines.insert(1, f".PHONY: {' '.join(phony)}")
    return "\n".join(lines) + "\n"


def _projio_mk(root: Path) -> str:
    """Generate projio.mk, substituting runtime bins if configured."""
    try:
        cfg = load_effective_config(root)
        runtime = cfg.get("runtime", {})
    except Exception:
        cfg = {}
        runtime = {}
    python_bin = runtime.get("python_bin")
    datalad_bin = runtime.get("datalad_bin")
    projio_python = runtime.get("projio_python")
    push_sibling = cfg.get("push_sibling") or cfg.get("datalad_remote") or "github"
    mk = PROJIO_MK
    if push_sibling != "github":
        mk = mk.replace(
            "$(DATALAD) push --to github",
            f"$(DATALAD) push --to {push_sibling}",
            1,
        )
    if python_bin:
        mk = mk.replace("PYTHON  ?= python", f"PYTHON  ?= {python_bin}", 1)
    if projio_python:
        mk = mk.replace(
            "PROJIO  ?= $(PYTHON) -m projio",
            f"PROJIO  ?= {projio_python} -m projio",
            1,
        )
        mk = mk.replace(
            "NOTIO   ?= $(PYTHON) -m notio",
            f"NOTIO   ?= {projio_python} -m notio",
            1,
        )
    elif python_bin:
        mk = mk.replace(
            "PROJIO  ?= $(PYTHON) -m projio",
            f"PROJIO  ?= {python_bin} -m projio",
            1,
        )
        mk = mk.replace(
            "NOTIO   ?= $(PYTHON) -m notio",
            f"NOTIO   ?= {python_bin} -m notio",
            1,
        )
    publish_script = runtime.get("publish_script")
    if publish_script:
        mk = mk.replace(
            "PUBLISH ?= $(PYTHON) -m twine upload",
            f"PUBLISH ?= {publish_script}",
            1,
        )
    labpy_python = None
    if datalad_bin:
        mk = mk.replace("DATALAD ?= datalad", f"DATALAD ?= {datalad_bin}", 1)
        # Derive labpy python for MKDOCS/PANDOC from datalad_bin path
        # e.g. .../envs/labpy/bin/datalad → .../envs/labpy/bin/python
        datalad_path = Path(datalad_bin)
        labpy_python = datalad_path.parent / "python"
        if labpy_python.exists():
            mk = mk.replace(
                "MKDOCS  ?= $(PYTHON) -m mkdocs",
                f"MKDOCS  ?= {labpy_python} -m mkdocs",
                1,
            )
        # Pandoc lives alongside datalad in labpy
        labpy_pandoc = datalad_path.parent / "pandoc"
        if labpy_pandoc.exists():
            mk = mk.replace(
                "PANDOC  ?= pandoc",
                f"PANDOC  ?= {labpy_pandoc}",
                1,
            )

    # Detect manuscripts and masters, append conditional targets
    manuscripts = _detect_manuscripts(root)
    masters = _detect_masters(root)

    if manuscripts or masters:
        # Add PANDOC_COMMON_ARGS block — projects can override in their Makefile
        render_vars = _render_vars_block(root)
        if render_vars:
            mk += render_vars
    mk += _manuscript_targets(manuscripts)
    mk += _master_targets(masters)

    return mk


def _render_vars_block(root: Path) -> str:
    """Generate PANDOC_*_ARGS variables from .projio/render.yml if present."""
    import yaml

    render_yml = root / ".projio" / "render.yml"
    if not render_yml.is_file():
        # Provide sensible defaults so targets still work
        return """
# --- Render variables (override in your Makefile or create .projio/render.yml) ---
PANDOC_BIB       ?=
PANDOC_CSL       ?=
PDF_ENGINE_ARGS  ?=
PANDOC_CITE_ARGS  = $(if $(PANDOC_BIB),--citeproc --bibliography=$(PANDOC_BIB)) $(if $(PANDOC_CSL),--csl=$(PANDOC_CSL))
PANDOC_COMMON_ARGS = --lua-filter=$(PANDOC_FILTER) $(PANDOC_CITE_ARGS)
"""

    data = yaml.safe_load(render_yml.read_text(encoding="utf-8")) or {}
    bib = data.get("bibliography", "")
    csl = data.get("csl", "")
    engine = data.get("pdf_engine", "")

    lines = [
        "",
        "# --- Render variables (from .projio/render.yml) ---",
    ]
    lines.append(f"PANDOC_BIB       ?= {bib}")
    lines.append(f"PANDOC_CSL       ?= {csl}")
    if engine:
        lines.append(f"PDF_ENGINE_ARGS  ?= --pdf-engine={engine}")
    else:
        lines.append("PDF_ENGINE_ARGS  ?=")
    lines.append(
        "PANDOC_CITE_ARGS  = $(if $(PANDOC_BIB),--citeproc --bibliography=$(PANDOC_BIB))"
        " $(if $(PANDOC_CSL),--csl=$(PANDOC_CSL))"
    )
    lines.append("PANDOC_COMMON_ARGS = --lua-filter=$(PANDOC_FILTER) $(PANDOC_CITE_ARGS)")
    lines.append("")
    return "\n".join(lines) + "\n"


_PROJIO_INCLUDE = "-include .projio/projio.mk"
_GITIGNORE_BEGIN = "# >>> projio >>>"
_GITIGNORE_END = "# <<< projio <<<"
_VSCODE_SITE_EXCLUDES = {
    "files.exclude": {"**/site": True},
    "search.exclude": {"**/site": True},
    "files.watcherExclude": {"**/site/**": True},
}

DEFAULT_MAKEFILE_SNIPPET = """\
# generated by projio init
PYTHON  ?= python
DATALAD ?= datalad
MSG     ?= Update

-include .projio/projio.mk
"""

TOOL_MAKEFILE_APPEND = """

.PHONY: test build check publish-test publish clean

test:
\tPYTHONPATH=src $(PYTHON) -m pytest tests -q

build:
\t$(PYTHON) -m build

check:
\t$(PYTHON) -m twine check dist/*

publish-test:
\t$(PUBLISH) --repository testpypi dist/*

publish:
\t$(PUBLISH) dist/*

clean:
\trm -rf build dist .pytest_cache .mypy_cache src/*.egg-info
"""

DEFAULT_MKDOCS = """\
site_name: {name}
docs_dir: docs
theme:
  name: material
"""

TOOL_PYPROJECT = """\
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{distribution_name}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.11"
authors = [{{ name = "" }}]
license = {{ text = "MIT" }}
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "build", "twine"]

[tool.setuptools.packages.find]
where = ["src"]
"""

TOOL_INIT = '''"""Top-level package for {package_name}."""\n'''

TOOL_TEST = """from __future__ import annotations


def test_import() -> None:
    import {package_name}

    assert {package_name}.__name__ == "{package_name}"
"""

STUDY_DOC = """# Study Overview

This project was scaffolded with `projio init . --kind study`.

Keep this thin:

- document project purpose and scope
- use `projio` for shared repo plumbing
- add domain-specific workflow structure only when the project actually needs it
"""

GITLAB_PAGES_CI_TEMPLATE = """\
# GitLab Pages CI — generated by projio init --gitlab-pages
pages:
  stage: deploy
  script:
    - cp -r {artifact_path} public
  artifacts:
    paths:
      - public
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
"""

GITHUB_PAGES_WORKFLOW_TEMPLATE = """\
name: docs

on:
  push:
    branches: [{default_branch}]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{setup_steps}
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: {artifact_path}

  deploy:
    if: github.ref == 'refs/heads/{default_branch}'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
"""


def _gitlab_pages_ci(root: Path, *, site_framework: str) -> str:
    artifact_path = "docs/_build/html" if site_framework == "sphinx" else "site"
    return GITLAB_PAGES_CI_TEMPLATE.format(artifact_path=artifact_path)


def _normalize_package_name(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", name.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    if not slug:
        slug = "proj"
    if slug[0].isdigit():
        slug = f"pkg_{slug}"
    return slug


def _write_if_needed(path: Path, content: str, root: Path, *, force: bool) -> None:
    if path.exists() and not force:
        print(f"[SKIP] {path.relative_to(root)} already exists")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[OK] wrote {path.relative_to(root)}")


def _detect_vite_app_dir(root: Path) -> str:
    if (root / "package.json").exists():
        return "."
    if (root / "docs" / "package.json").exists():
        return "docs"
    return "."


def _site_settings_for_framework(root: Path, site_framework: str) -> dict[str, str]:
    if site_framework == "sphinx":
        return {
            "site_framework": "sphinx",
            "site_output_dir": "docs/_build/html",
            "vite_app_dir": _detect_vite_app_dir(root),
        }
    return {
        "site_framework": site_framework,
        "site_output_dir": "site",
        "vite_app_dir": _detect_vite_app_dir(root),
    }


def _projio_config_for_kind(root: Path, name: str, kind: str, *, site_framework: str) -> str:
    site_settings = _site_settings_for_framework(root, site_framework)
    if kind == "study":
        return STUDY_PROJIO_CONFIG.format(name=name, **site_settings)
    return BASE_PROJIO_CONFIG.format(name=name, kind=kind, **site_settings)


def _makefile_for_kind(kind: str) -> str:
    if kind == "tool":
        return DEFAULT_MAKEFILE_SNIPPET + TOOL_MAKEFILE_APPEND
    return DEFAULT_MAKEFILE_SNIPPET


def _ensure_makefile_include(path: Path, root: Path) -> None:
    """Ensure an existing Makefile contains the projio.mk include directive."""
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if _PROJIO_INCLUDE in text:
        return
    path.write_text(text.rstrip("\n") + "\n\n" + _PROJIO_INCLUDE + "\n", encoding="utf-8")
    print(f"[OK] added projio.mk include to {path.relative_to(root)}")


def _detect_site_framework(root: Path) -> str:
    try:
        from .site import detect_framework
    except Exception:
        return "mkdocs"
    detected = detect_framework(root)
    if detected in SITE_FRAMEWORK_CHOICES:
        return detected
    return "mkdocs"


def _gitignore_entries_for_framework(site_framework: str) -> list[str]:
    entries = [
        ".mcp.json",
        ".claude/settings.json",
        ".projio/servers.json",
        ".projio/site/",
        ".projio/indexio/index/",
        ".projio.mkdocs.yml",
        "site/",
        "bib/logs/",
    ]
    if site_framework == "sphinx":
        entries.extend(["docs/_build/", "docs/_build/html/"])
    return entries


def _ensure_projio_gitignore(root: Path, *, site_framework: str) -> None:
    path = root / ".gitignore"
    block_lines = [_GITIGNORE_BEGIN, *sorted(dict.fromkeys(_gitignore_entries_for_framework(site_framework))), _GITIGNORE_END]
    block = "\n".join(block_lines) + "\n"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        pattern = rf"(?ms)^{re.escape(_GITIGNORE_BEGIN)}\n.*?^{re.escape(_GITIGNORE_END)}\n?"
        if re.search(pattern, text):
            new_text = re.sub(pattern, block, text)
        else:
            new_text = text.rstrip("\n") + "\n\n" + block
    else:
        new_text = block
    if path.exists() and path.read_text(encoding="utf-8") == new_text:
        return
    path.write_text(new_text, encoding="utf-8")
    print(f"[OK] updated {path.relative_to(root)}")


def untrack_gitignored(root: str | Path, *, dry_run: bool = False) -> list[str]:
    """Untrack files listed in the projio gitignore block that are still tracked by git.

    Returns the list of paths that were (or would be) untracked.
    """
    import subprocess

    root = Path(root).expanduser().resolve()
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        print("No .gitignore found.")
        return []

    # Parse the projio block
    text = gitignore.read_text(encoding="utf-8")
    pattern = rf"(?ms)^{re.escape(_GITIGNORE_BEGIN)}\n(.*?)^{re.escape(_GITIGNORE_END)}"
    match = re.search(pattern, text)
    if not match:
        print("No projio gitignore block found. Run: projio init")
        return []

    entries = [
        line.strip() for line in match.group(1).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    # Check which are still tracked
    untracked = []
    for entry in entries:
        # For directory entries (trailing /), use git ls-files to find tracked files
        if entry.endswith("/"):
            result = subprocess.run(
                ["git", "-C", str(root), "ls-files", entry.rstrip("/")],
                capture_output=True, text=True,
            )
            tracked = [f for f in result.stdout.strip().splitlines() if f]
        else:
            result = subprocess.run(
                ["git", "-C", str(root), "ls-files", entry],
                capture_output=True, text=True,
            )
            tracked = [f for f in result.stdout.strip().splitlines() if f]

        for f in tracked:
            if dry_run:
                print(f"  [dry-run] would untrack {f}")
            else:
                subprocess.run(
                    ["git", "-C", str(root), "rm", "--cached", f],
                    capture_output=True,
                )
                print(f"  [OK] untracked {f}")
            untracked.append(f)

    if not untracked:
        print("Nothing to untrack — all gitignored files are already untracked.")

    return untracked


def _ensure_vscode_settings(root: Path) -> None:
    settings_path = root / ".vscode" / "settings.json"
    payload: dict[str, object] = {}
    if settings_path.exists():
        try:
            payload = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
    changed = False
    for key, mapping in _VSCODE_SITE_EXCLUDES.items():
        existing = payload.get(key)
        if not isinstance(existing, dict):
            existing = {}
            payload[key] = existing
            changed = True
        for exclude_key, exclude_value in mapping.items():
            if existing.get(exclude_key) != exclude_value:
                existing[exclude_key] = exclude_value
                changed = True
    if settings_path.exists() and not changed:
        return
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] wrote {settings_path.relative_to(root)}")


def _github_pages_setup_steps(site_framework: str, *, vite_app_dir: str) -> str:
    if site_framework == "mkdocs":
        return """\
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install docs dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install mkdocs mkdocs-material
      - name: Build docs
        run: mkdocs build --strict
"""
    if site_framework == "sphinx":
        return """\
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install docs dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install projio sphinx
          if [ -f pyproject.toml ]; then python -m pip install -e .; fi
      - name: Build docs
        run: projio site build -C . --framework sphinx
"""
    return f"""\
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install projio
        run: |
          python -m pip install --upgrade pip
          python -m pip install projio
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install frontend dependencies
        working-directory: {vite_app_dir}
        run: |
          if [ -f package-lock.json ]; then npm ci; else npm install; fi
      - name: Build docs
        run: projio site build -C . --framework vite
"""


def _github_pages_workflow(root: Path, *, site_framework: str) -> str:
    vite_app_dir = _detect_vite_app_dir(root)
    artifact_path = "docs/_build/html" if site_framework == "sphinx" else "site"
    return GITHUB_PAGES_WORKFLOW_TEMPLATE.format(
        default_branch="master",
        setup_steps=_github_pages_setup_steps(site_framework, vite_app_dir=vite_app_dir),
        artifact_path=artifact_path,
    )


def _scaffold_base(root: Path, *, kind: str, force: bool, vscode: bool, github_pages: bool, gitlab_pages: bool) -> None:
    proj_dir = root / ".projio"
    proj_dir.mkdir(parents=True, exist_ok=True)
    _ensure_packages_yml(root)
    site_framework = _detect_site_framework(root)
    _write_if_needed(proj_dir / "config.yml", _projio_config_for_kind(root, root.name, kind, site_framework=site_framework), root, force=force)
    # projio.mk is projio-managed — always overwrite to pick up new targets
    _write_if_needed(proj_dir / "projio.mk", _projio_mk(root), root, force=True)
    if site_framework == "mkdocs":
        _write_if_needed(root / "mkdocs.yml", DEFAULT_MKDOCS.format(name=root.name), root, force=force)
    _write_if_needed(root / "Makefile", _makefile_for_kind(kind), root, force=force)
    _ensure_makefile_include(root / "Makefile", root)
    _ensure_projio_gitignore(root, site_framework=site_framework)
    if vscode:
        _ensure_vscode_settings(root)
    if github_pages:
        _write_if_needed(root / ".github" / "workflows" / "docs.yml", _github_pages_workflow(root, site_framework=site_framework), root, force=force)
    if gitlab_pages:
        _write_if_needed(root / ".gitlab-ci.yml", _gitlab_pages_ci(root, site_framework=site_framework), root, force=force)
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)
    _write_if_needed(docs_dir / "index.md", f"# {root.name}\n", root, force=force)


def _scaffold_tool(root: Path, *, force: bool) -> None:
    package_name = _normalize_package_name(root.name)
    _write_if_needed(
        root / "pyproject.toml",
        TOOL_PYPROJECT.format(distribution_name=root.name, package_name=package_name),
        root,
        force=force,
    )
    _write_if_needed(root / "src" / package_name / "__init__.py", TOOL_INIT.format(package_name=package_name), root, force=force)
    tests_dir = root / "tests"
    tests_dir.mkdir(exist_ok=True)
    _write_if_needed(root / "tests" / f"test_{package_name}.py", TOOL_TEST.format(package_name=package_name), root, force=force)


def _scaffold_study(root: Path, *, force: bool) -> None:
    _write_if_needed(root / "docs" / "study-overview.md", STUDY_DOC, root, force=force)
    # Scaffold render.yml for study projects
    from .render import DEFAULT_RENDER_YML
    _write_if_needed(root / ".projio" / "render.yml", DEFAULT_RENDER_YML, root, force=force)


def scaffold(
    root: str | Path,
    *,
    kind: str = "generic",
    profile: str | None = None,
    force: bool = False,
    vscode: bool = False,
    github_pages: bool = False,
    gitlab_pages: bool = False,
) -> None:
    """Scaffold project files inside *root*."""
    if kind not in KIND_CHOICES:
        raise ValueError(f"Unknown project kind: {kind}")
    if profile is not None and profile not in PROFILES:
        raise ValueError(
            f"Unknown profile: {profile}. Available: {', '.join(PROFILES)}"
        )
    root_path = Path(root).expanduser().resolve()
    _scaffold_base(root_path, kind=kind, force=force, vscode=vscode, github_pages=github_pages, gitlab_pages=gitlab_pages)
    if kind == "tool":
        _scaffold_tool(root_path, force=force)
    elif kind == "study":
        _scaffold_study(root_path, force=force)
    if profile is not None:
        for pkg in PROFILES[profile]:
            add_package(root_path, pkg)


def load_projio_config(root: str | Path) -> dict:
    return load_project_config(root)


# ---------------------------------------------------------------------------
# packages.yml management
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml  # type: ignore[import-untyped]

    def _load_yaml(text: str) -> dict:
        return _yaml.safe_load(text) or {}

    def _dump_yaml(data: dict) -> str:
        return _yaml.dump(data, default_flow_style=False, sort_keys=False)
except ImportError:  # minimal fallback for environments without PyYAML
    import json as _json

    def _load_yaml(text: str) -> dict:  # type: ignore[misc]
        # packages.yml is simple enough for JSON-compatible subset
        return _json.loads(text) if text.strip() else {}

    def _dump_yaml(data: dict) -> str:  # type: ignore[misc]
        return _json.dumps(data, indent=2) + "\n"


def _packages_path(root: Path) -> Path:
    return root / ".projio" / "packages.yml"


def _load_packages(root: Path) -> dict:
    path = _packages_path(root)
    if not path.exists():
        return {"packages": {}}
    return _load_yaml(path.read_text(encoding="utf-8")) or {"packages": {}}


def _save_packages(root: Path, data: dict) -> None:
    path = _packages_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(data), encoding="utf-8")


def _ensure_packages_yml(root: Path) -> None:
    """Create packages.yml if it does not exist."""
    path = _packages_path(root)
    if not path.exists():
        _save_packages(root, {"packages": {}})
        print(f"[OK] wrote {path.relative_to(root)}")


def _scaffold_component(root: Path, package: str, component_dir: Path) -> None:
    """Run the package's own scaffold targeting the managed directory."""
    if package == "codio":
        try:
            from codio.scaffold import init_codio_scaffold
            init_codio_scaffold(root, target_dir=component_dir)
        except ImportError:
            component_dir.mkdir(parents=True, exist_ok=True)
    elif package == "indexio":
        try:
            from indexio.config import scaffold_config
            scaffold_config(component_dir / "config.yaml", root=root)
        except ImportError:
            component_dir.mkdir(parents=True, exist_ok=True)
    elif package == "notio":
        try:
            from notio.config import load_config
            from notio.core import ensure_default_templates
            config = load_config(root, template_root=component_dir / "templates")
            ensure_default_templates(config)
        except ImportError:
            component_dir.mkdir(parents=True, exist_ok=True)
    elif package == "biblio":
        try:
            from biblio.scaffold import init_bib_scaffold
            init_bib_scaffold(root)
        except ImportError:
            pass
        # biblio uses visible bib/, component dir is just a marker
        component_dir.mkdir(parents=True, exist_ok=True)
    elif package == "pipeio":
        component_dir.mkdir(parents=True, exist_ok=True)
        reg_path = component_dir / "registry.yml"
        if not reg_path.exists():
            reg_path.write_text(
                "# pipeio pipeline registry\nflows: {}\n",
                encoding="utf-8",
            )
        templates_dir = component_dir / "templates" / "flow"
        templates_dir.mkdir(parents=True, exist_ok=True)
    elif package == "claude":
        _scaffold_claude(root, component_dir)
    else:
        component_dir.mkdir(parents=True, exist_ok=True)


def _scaffold_claude(root: Path, component_dir: Path) -> None:
    """Scaffold Claude Code settings for a project.

    Creates:
      - .claude/settings.json — tool permissions scoped to the project
      - CLAUDE.md — project context with MCP tool routing
      - .projio/claude/ — marker directory for projio tracking
    """
    import json

    component_dir.mkdir(parents=True, exist_ok=True)

    # .claude/settings.json — pre-approved tools for autonomous execution
    claude_dir = root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path = claude_dir / "settings.json"
    if not settings_path.exists():
        root_glob = f"{root}/**"
        settings = {
            "permissions": {
                "allow": [
                    "Read",
                    "Glob",
                    "Grep",
                    f"Edit({root_glob})",
                    f"Write({root_glob})",
                    "Bash(ls:*)",
                    "Bash(find:*)",
                    "Bash(git:*)",
                    "Bash(python:*)",
                    "Bash(pip:*)",
                    "Bash(pytest:*)",
                    "Bash(make:*)",
                    "mcp__projio__*",
                    "mcp__worklog__*",
                ],
            },
            "allowedTools": [
                "Read",
                "Glob",
                "Grep",
                f"Edit({root_glob})",
                f"Write({root_glob})",
                "Bash(ls:*)",
                "Bash(find:*)",
                "Bash(git:*)",
                "Bash(python:*)",
                "Bash(pip:*)",
                "Bash(pytest:*)",
                "Bash(make:*)",
                "mcp__projio__*",
                "mcp__worklog__*",
            ],
        }
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")
        print(f"  [OK] wrote {settings_path.relative_to(root)}")
    else:
        print(f"  [skip] {settings_path.relative_to(root)} already exists")

    # Update permissions to be path-scoped
    update_claude_permissions(root, dry_run=False)

    # .mcp.json — MCP server config for Claude Code
    from .mcp.config_gen import write_mcp_config
    mcp_json = root / ".mcp.json"
    if not mcp_json.exists():
        write_mcp_config(root, yes=True)
    else:
        print(f"  [skip] .mcp.json already exists")

    # CLAUDE.md — project context with tool routing
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        content = _generate_claude_md(root)
        claude_md.write_text(content)
        print(f"  [OK] wrote CLAUDE.md")
    else:
        print(f"  [skip] CLAUDE.md already exists")


def _mcp_server_wildcards(root: Path) -> list[str]:
    """Derive ``mcp__<server>__*`` wildcards from ``.mcp.json``."""
    mcp_json = root / ".mcp.json"
    if not mcp_json.exists():
        return []
    try:
        data = json.loads(mcp_json.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        return [f"mcp__{name}__*" for name in servers]
    except (json.JSONDecodeError, OSError):
        return []


def _codio_read_paths(root: Path) -> list[str]:
    """Derive ``Read()`` permission paths from codio repos and catalog entries."""
    paths: list[str] = []
    try:
        from codio import load_config, load_repos
        config = load_config(project_root=root)

        # From repos.yml: managed/attached repos with local_path
        repos = load_repos(config.repos_path)
        for _repo_id, entry in repos.items():
            if entry.storage in ("managed", "attached") and entry.local_path:
                local = Path(entry.local_path)
                abs_path = local if local.is_absolute() else root / local
                paths.append(f"Read({abs_path}/**)")

        # From catalog: entries with explicit path field
        from codio import load_catalog
        catalog = load_catalog(config.catalog_path)
        for _name, entry in catalog.items():
            if entry.path:
                local = Path(entry.path)
                abs_path = local if local.is_absolute() else root / local
                paths.append(f"Read({abs_path}/**)")
    except (ImportError, FileNotFoundError):
        pass
    return list(dict.fromkeys(paths))  # deduplicate, preserve order


def sync_claude_permissions(
    root: str | Path,
    *,
    dry_run: bool = False,
) -> dict:
    """Sync ``.claude/settings.json`` permissions from project config, codio deps, and ``.mcp.json``.

    Computes the full desired permission set by combining:
    1. Existing entries (never removed)
    2. Baseline path-scoped Edit/Write
    3. ``mcp__<server>__*`` wildcards from ``.mcp.json``
    4. ``Read()`` paths from codio managed/attached repos and catalog entries
    5. Explicit extras from ``claude.extra_permissions`` / ``claude.extra_mcp_wildcards`` in config

    Returns a summary dict: ``{"changed": bool, "added": [...], "path": str}``.
    """
    root = Path(root).expanduser().resolve()
    settings_path = root / ".claude" / "settings.json"

    if not settings_path.exists():
        msg = f"{settings_path} does not exist — run 'projio add claude' first"
        if not dry_run:
            print(f"  [skip] {msg}")
        return {"changed": False, "added": [], "path": str(settings_path), "error": msg}

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    root_glob = f"{root}/**"

    # --- Collect desired entries ---
    # Baseline permissions that every projio project should have
    baseline = [
        "Read",
        "Glob",
        "Grep",
        f"Edit({root_glob})",
        f"Write({root_glob})",
        "Bash(ls:*)",
        "Bash(find:*)",
        "Bash(git:*)",
        "Bash(python:*)",
        "Bash(pip:*)",
        "Bash(pytest:*)",
        "Bash(make:*)",
    ]

    # MCP server wildcards from .mcp.json
    mcp_wildcards = _mcp_server_wildcards(root)

    # Codio read paths
    codio_paths = _codio_read_paths(root)

    # Config extras
    try:
        cfg = load_effective_config(root)
    except FileNotFoundError:
        cfg = {}
    extra_perms = get_nested(cfg, "claude", "extra_permissions", default=[]) or []
    extra_mcp = get_nested(cfg, "claude", "extra_mcp_wildcards", default=[]) or []

    # Build the set of entries to inject
    desired: list[str] = []
    desired.extend(baseline)
    desired.extend(mcp_wildcards)
    desired.extend(codio_paths)
    desired.extend(extra_perms)
    desired.extend(extra_mcp)

    # --- Merge into both allowedTools and permissions.allow ---
    added: list[str] = []

    def _merge_list(existing: list[str]) -> list[str]:
        """Scope bare Edit/Write, then add missing desired entries."""
        result: list[str] = []
        for entry in existing:
            if entry in ("Edit", "Write"):
                scoped = f"{entry}({root_glob})"
                if scoped not in result:
                    result.append(scoped)
            else:
                result.append(entry)
        for entry in desired:
            if entry not in result:
                result.append(entry)
                if entry not in added:
                    added.append(entry)
        return result

    old_tools = settings.get("allowedTools", [])
    new_tools = _merge_list(old_tools)

    old_allow = settings.get("permissions", {}).get("allow", [])
    new_allow = _merge_list(old_allow)

    changed = new_tools != old_tools or new_allow != old_allow

    if not changed:
        if not dry_run:
            print(f"  [ok] permissions already synced in {settings_path.relative_to(root)}")
        return {"changed": False, "added": [], "path": str(settings_path)}

    settings["allowedTools"] = new_tools
    settings.setdefault("permissions", {})["allow"] = new_allow

    if dry_run:
        print(f"  [dry-run] would update {settings_path.relative_to(root)}:")
        print(f"  would add: {added}")
        print(json.dumps(settings, indent=2))
        return {"changed": True, "added": added, "path": str(settings_path), "dry_run": True}

    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"  [OK] synced permissions in {settings_path.relative_to(root)}")
    if added:
        print(f"  added: {added}")
    return {"changed": True, "added": added, "path": str(settings_path)}


def update_claude_permissions(root: str | Path, *, dry_run: bool = False) -> None:
    """Scope Edit/Write in .claude/settings.json to the project root.

    Delegates to :func:`sync_claude_permissions` which handles path scoping,
    MCP wildcard injection, codio read paths, and config extras.
    """
    sync_claude_permissions(root, dry_run=dry_run)


def _generate_claude_md(root: Path) -> str:
    """Generate a CLAUDE.md with MCP tool routing based on enabled packages."""
    # Infer project info
    project_name = root.name
    project_desc = ""
    projio_config = root / ".projio" / "config.yml"
    if projio_config.exists():
        try:
            cfg = _load_yaml(projio_config.read_text(encoding="utf-8"))
            project_name = cfg.get("project_name", project_name)
            project_desc = cfg.get("description", "")
        except Exception:
            pass

    # Detect enabled packages
    packages = _load_packages(root).get("packages", {})
    has_biblio = packages.get("biblio", {}).get("enabled", False)
    has_notio = packages.get("notio", {}).get("enabled", False)
    has_codio = packages.get("codio", {}).get("enabled", False)
    has_pipeio = packages.get("pipeio", {}).get("enabled", False)
    has_indexio = packages.get("indexio", {}).get("enabled", False)

    sections: list[str] = []

    # Header
    desc_line = f"\n{project_desc}\n" if project_desc else ""
    sections.append(f"# {project_name}\n{desc_line}")

    # Projio preamble
    sections.append("""\
## Projio workspace

This project uses **projio** — a project-centric research assistance ecosystem.
All project knowledge (papers, notes, code libraries, search indexes) is managed
through MCP tools. **Always use MCP tools instead of direct file manipulation**
for projio-managed resources.

**Tool preference:** When an MCP tool exists for an operation, always prefer it
over the Bash equivalent — even for simple commands like `git status` or
`datalad status`. MCP tools return structured output and resolve environment
variables (Python paths, conda envs) that differ from the MCP server's own env.
Only fall back to Bash when no MCP tool covers the operation.

At the start of a session, call `project_context()` to understand the workspace
and `runtime_conventions()` to see available Makefile targets.
""")

    # Tool routing table
    rows: list[str] = []

    # Core tools (always available)
    rows.append("| Understand the project | `project_context()` | Read config files directly |")
    rows.append("| See available commands | `runtime_conventions()` | Parse the Makefile manually |")

    if has_indexio:
        rows.append("| Search project knowledge | `rag_query(query)` | Grep through docs manually |")
        rows.append("| Multi-facet search | `rag_query_multi(queries)` | Run multiple greps |")
        rows.append("| Check indexed sources | `corpus_list()` | Inspect Chroma store directly |")
        rows.append("| Rebuild search index | `indexio_build()` | Run `indexio build` in terminal |")
        rows.append("| Check indexed sources | `indexio_sources_list()` | Inspect config files directly |")
        rows.append("| Sync all subsystem sources | `indexio_sources_sync(build=True)` | Run sync commands manually |")

    if has_biblio:
        rows.append("| Ingest papers by DOI | `biblio_ingest(dois)` | Write BibTeX by hand |")
        rows.append("| Look up a paper | `citekey_resolve(citekeys)` | Read .bib files directly |")
        rows.append("| Get full paper context | `paper_context(citekey)` | Read docling/GROBID outputs directly |")
        rows.append("| Find unresolved refs | `paper_absent_refs(citekey)` | Parse references.json manually |")
        rows.append("| Check paper status | `library_get(citekey)` | Read library.yml directly |")
        rows.append("| Update paper status | `biblio_library_set(citekeys)` | Edit library.yml directly |")
        rows.append("| Merge bibliography | `biblio_merge()` | Run `biblio merge` in terminal |")
        rows.append("| Fetch PDFs from BibTeX | `biblio_pdf_fetch(dry_run, force)` | Copy PDFs manually |")
        rows.append("| Fetch PDFs via OA cascade | `biblio_pdf_fetch_oa(force, citekeys)` | Run `biblio bibtex fetch-pdfs-oa` |")
        rows.append("| Extract full text | `biblio_docling(citekey)` | Run `biblio docling` in terminal |")
        rows.append("| Batch extract full text | `biblio_docling_batch(force, background)` | Run docling loop manually |")
        rows.append("| Check Docling job status | `biblio_docling_status(job_id)` | Poll job manually |")
        rows.append("| Extract references | `biblio_grobid(citekey)` | Run `biblio grobid` in terminal |")
        rows.append("| Check GROBID server | `biblio_grobid_check()` | Curl the GROBID API manually |")
        rows.append("| Expand reference graph | `biblio_graph_expand(citekeys)` | Run `biblio graph expand` |")
        rows.append("| Sync biblio sources to index | `biblio_rag_sync()` | Run `biblio rag sync` in terminal |")

    if has_notio:
        rows.append("| Create a note/task/idea | `note_create(note_type)` | Create markdown files directly |")
        rows.append("| List recent notes | `note_list()` | List files in notes/ directory |")
        rows.append("| Read a note | `note_read(path)` | Read the file directly |")
        rows.append("| Find note by ID/timestamp | `note_resolve(note_id)` | Grep filenames or semantic search |")
        rows.append("| Search notes | `note_search(query)` | Grep through notes/ |")
        rows.append("| Update note metadata | `note_update(path, fields)` | Edit frontmatter directly |")
        rows.append("| See note types | `note_types()` | Read notio.toml directly |")
        rows.append("| Rebuild note indexes | `notio_reindex(note_type?)` | Regenerate index.md manually |")

    if has_codio:
        rows.append("| Add a library | `codio_add_urls(urls)` | Edit YAML registry files |")
        rows.append("| Find libraries by capability | `codio_discover(query)` | Grep catalog.yml |")
        rows.append("| Inspect a library | `codio_get(name)` | Read catalog + profiles manually |")
        rows.append("| List all libraries | `codio_list()` | Parse registry files directly |")
        rows.append("| Check registry vocabulary | `codio_vocab()` | Read schema docs |")
        rows.append("| Validate registry | `codio_validate()` | Run consistency checks manually |")
        rows.append("| Register a library (with role) | `codio_add(name, kind, role)` | Edit YAML registry files |")
        rows.append("| Sync codio sources to index | `codio_rag_sync()` | Run `codio rag sync` in terminal |")

    if has_pipeio:
        # Flow & registry
        rows.append("| List flows | `pipeio_flow_list(prefix?)` | Parse registry YAML directly |")
        rows.append("| Flow status | `pipeio_flow_status(flow)` | Inspect flow dirs manually |")
        rows.append("| Scan for pipelines | `pipeio_registry_scan()` | Walk filesystem manually |")
        rows.append("| Validate registry | `pipeio_registry_validate()` | Check consistency manually |")
        # Mod management
        rows.append("| List mods | `pipeio_mod_list(flow)` | Parse registry manually |")
        rows.append("| Mod context (rules, scripts, doc, config) | `pipeio_mod_context(flow, mod)` | Multiple reads manually |")
        rows.append("| Scaffold mod (script + docs) | `pipeio_mod_create(flow, mod, inputs, outputs)` | Create files manually |")
        rows.append("| Add script to existing mod | `pipeio_script_create(flow, mod, script_name)` | Create script manually |")
        rows.append("| Audit mod health | `pipeio_mod_audit(flow, mod?)` | Manual inspection |")
        rows.append("| Refresh mod doc from code | `pipeio_mod_doc_refresh(flow, mod, facet, apply?)` | Rewrite spec.md manually |")
        # Rule authoring
        rows.append("| List rules | `pipeio_rule_list(flow)` | Parse Snakefiles manually |")
        rows.append("| Generate rule stub | `pipeio_rule_stub(flow, rule_name)` | Write rule text manually |")
        rows.append("| Insert rule into Snakefile | `pipeio_rule_insert(flow, rule_name)` | Edit Snakefiles manually |")
        rows.append("| Patch existing rule | `pipeio_rule_update(flow, rule_name, add_inputs)` | Edit Snakefiles manually |")
        # Config authoring
        rows.append("| Scaffold flow config | `pipeio_config_init(flow, input_dir, output_dir)` | Create config.yml manually |")
        rows.append("| Read flow config | `pipeio_config_read(flow)` | Parse config.yml directly |")
        rows.append("| Patch flow config | `pipeio_config_patch(flow, registry_entry, apply?)` | Edit config.yml directly |")
        # Notebook lifecycle
        rows.append("| Scaffold notebook (kind-aware) | `pipeio_nb_create(flow, name, kind, mod?)` | Create .py files manually |")
        rows.append("| Notebook status | `pipeio_nb_status(flow?, name?)` | Parse notebook.yml manually |")
        rows.append("| Audit notebook quality | `pipeio_nb_audit()` | Manual inspection |")
        rows.append("| Read notebook + metadata | `pipeio_nb_read(flow, name)` | Read .py + parse YAML manually |")
        rows.append("| Analyze notebook structure | `pipeio_nb_analyze(flow, name)` | Parse .py files manually |")
        rows.append("| Check sync state | `pipeio_nb_diff(flow, name)` | Compare mtimes manually |")
        rows.append("| Update notebook metadata | `pipeio_nb_update(flow, name)` | Edit notebook.yml directly |")
        rows.append("| Sync notebook | `pipeio_nb_sync(flow, name, direction?)` | Run jupytext manually |")
        rows.append("| Sync all in flow | `pipeio_nb_sync_flow(flow)` | Sync each manually |")
        rows.append("| Scan for unregistered | `pipeio_nb_scan(register?)` | Walk filesystem manually |")
        rows.append("| Publish notebook | `pipeio_nb_publish(flow, name)` | Copy files manually |")
        rows.append("| Execute notebook | `pipeio_nb_exec(flow, name, params)` | Run papermill manually |")
        rows.append("| Full notebook pipeline | `pipeio_nb_pipeline(flow, name)` | Chain sync/publish/collect |")
        rows.append("| Build Jupyter Lab manifest | `pipeio_nb_lab(flow?, sync?)` | Create symlinks manually |")
        rows.append("| Promote notebook to mod | `pipeio_nb_promote(flow, name, mod)` | Manual extraction |")
        # Contracts & validation
        rows.append("| Validate I/O contracts | `pipeio_contracts_validate()` | Check configs manually |")
        rows.append("| Cross-flow manifest chains | `pipeio_cross_flow(flow?)` | Compare configs manually |")
        rows.append("| Session completion | `pipeio_completion(flow)` | Glob output dirs manually |")
        # Paths & DAG
        rows.append("| Resolve output paths | `pipeio_target_paths(flow, group, member)` | Construct BIDS paths manually |")
        rows.append("| Export DAG | `pipeio_dag_export(flow, graph_type)` | Run snakemake --rulegraph |")
        rows.append("| Generate report | `pipeio_report(flow)` | Run snakemake --report |")
        rows.append("| Parse logs | `pipeio_log_parse(flow)` | Read log files manually |")
        # Documentation
        rows.append("| Collect pipeline docs | `pipeio_docs_collect()` | Copy doc files manually |")
        rows.append("| Generate docs nav | `pipeio_docs_nav()` | Build nav YAML manually |")
        rows.append("| Patch mkdocs nav | `pipeio_mkdocs_nav_patch()` | Edit mkdocs.yml manually |")
        rows.append("| Generate modkey bibliography | `pipeio_modkey_bib()` | Write BibTeX manually |")
        # Execution
        rows.append("| Launch Snakemake run | `pipeio_run(flow, wildcards?)` | Run snakemake in terminal |")
        rows.append("| Check run progress | `pipeio_run_status(run_id?)` | Check screen sessions |")
        rows.append("| Run dashboard | `pipeio_run_dashboard()` | Aggregate run info manually |")
        rows.append("| Kill a run | `pipeio_run_kill(run_id)` | Kill screen sessions |")

    # Site tools (always available)
    rows.append("| Build doc site | `site_build()` | Run `make docs` or `mkdocs build` |")
    rows.append("| Deploy to pages | `site_deploy(target)` | Run `make deploy` or push manually |")

    # Git & DataLad tools (always available)
    rows.append("| Check git status | `git_status()` | Run `git status` in Bash |")
    rows.append("| Save dataset changes | `datalad_save(message)` | Run `make save` or `datalad save` |")
    rows.append("| Check dataset status | `datalad_status()` | Run `make status` or `datalad status` |")
    rows.append("| Push to sibling | `datalad_push(sibling)` | Run `make push` or `datalad push` |")
    rows.append("| Pull from sibling | `datalad_pull(sibling)` | Run `make pull` or `datalad update` |")
    rows.append("| List siblings | `datalad_siblings()` | Run `datalad siblings` manually |")

    if rows:
        table_header = "| Intent | MCP tool | Do NOT |\n|--------|----------|--------|\n"
        sections.append("## Agent tool routing\n\n" + table_header + "\n".join(rows) + "\n")

    # Workflow guidance
    if has_biblio or has_codio or has_indexio:
        workflow_parts: list[str] = []
        if has_indexio or has_notio or has_codio:
            workflow_parts.append("1. **Search first** — check existing knowledge before creating new content")
        if has_biblio:
            workflow_parts.append(
                "2. **Ingest pipeline** — after `biblio_ingest`, run `biblio_merge` → "
                "`biblio_pdf_fetch_oa` → `biblio_docling_batch` → `biblio_grobid` → "
                "`biblio_graph_expand` → `indexio_build`"
                if has_indexio else
                "2. **Ingest pipeline** — after `biblio_ingest`, run `biblio_merge` → "
                "`biblio_pdf_fetch_oa` → `biblio_docling_batch` → `biblio_grobid` → "
                "`biblio_graph_expand`"
            )
        if has_notio:
            workflow_parts.append("3. **Record decisions** — create notes to capture analysis and decisions")

        if workflow_parts:
            sections.append("## Workflow conventions\n\n" + "\n".join(workflow_parts) + "\n")

    if has_pipeio:
        sections.append("""\
## pipeio entity management

pipeio manages pipeline entities through MCP tools. Read `skill_read("pipeio-guide")` for the full ontology reference.

### Capability matrix

| Entity | Create | Read | Update | Audit |
|--------|--------|------|--------|-------|
| **Flow** | `flow_new` (CLI, idempotent) | `flow_list`, `flow_status` | agent edits | `registry_validate` |
| **Mod** | `mod_create` (script + docs) | `mod_list`, `mod_context` | agent edits | `mod_audit` |
| **Rule** | `rule_stub`, `rule_insert` | `rule_list` | `rule_update` | `mod_audit` |
| **Config** | `config_init` | `config_read` | `config_patch` | `contracts_validate` |
| **Script** | `mod_create`, `script_create` | `mod_context` | agent edits | `mod_audit` |
| **Notebook** | `nb_create` (kind-aware) | `nb_read`, `nb_status`, `nb_analyze` | `nb_update` (metadata) | `nb_audit` |
| **Mod docs** | `mod_create` (theory + spec) | `mod_context` | `mod_doc_refresh` | `mod_audit` |
| **Promote** | `nb_promote` | — | — | — |
| **Manifest** | config sets path | `cross_flow` | agent edits | `contracts_validate` |
| **Site docs** | `docs_collect` | `docs_nav` | re-collect | — |
| **Core library** | `codio_add(role="core")` | `codio_get`, `codio_list` | agent edits | — |
| **Project utils** | `projio sync` (auto-detect) | `project_context` | agent edits | — |

**Scaffolding tools produce correct starting points.** `nb_create` generates kind-aware templates (investigate vs demo), `mod_create` and `script_create` discover the project's compute library via codio (role=core) and include imports. **Structured write helpers** (`config_patch`, `rule_insert`, `rule_update`) validate input and produce diffs. **Free-form code editing** is agent territory.

### Code tiers

Projects organize code in three tiers (see `docs/specs/pipeio/code-tiers.md`):

| Tier | Location | codio role | Agent policy |
|------|----------|------------|-------------|
| Core library | `code/lib/{name}/` | `core` | Agents can add code here |
| Project utils | `code/utils/` | — | Project-specific glue |
| Flow scripts | `code/pipelines/{flow}/scripts/` | — | One script per rule |

`projio sync` auto-discovers `code/lib/*/` and registers in codio with `role=core`. `project_context()` returns the active code tier configuration.

### Notebook workspaces

Notebooks route to workspaces by `kind`:
- `investigate`/`explore` → `notebooks/explore/.src/` (never published)
- `demo`/`validate` → `notebooks/demo/.src/` (published to site)

### Notebook lifecycle

```
pipeio_nb_create(flow, name, kind="investigate", mod="filter")  # scaffold
pipeio_nb_update(flow, name, status="archived")                 # lifecycle transition
pipeio_nb_promote(flow, name, mod="filter")                     # extract to mod
pipeio_nb_pipeline(flow, name)                                  # sync → publish → collect
```

### Mod documentation facets

Each mod has `docs/{mod}/theory.md` (rationale + citations) and `spec.md` (I/O contracts). `mod_doc_refresh(flow, mod, facet="spec", apply=True)` regenerates spec.md from current mod_context.

### Agentic workflow

1. **Discover:** `pipeio_nb_scan()` → find unregistered notebooks
2. **Triage:** `pipeio_nb_status(flow)` or `pipeio_nb_audit()` → quality report
3. **Understand:** `pipeio_nb_read(flow, name)` → content + metadata + analysis
4. **Check sync:** `pipeio_nb_diff(flow, name)` → which file is newer
5. **Fix config:** `pipeio_nb_update(...)` → set status, kind, mod, kernel
6. **Sync:** `pipeio_nb_sync(flow, name, direction='py2nb')` after editing .py
7. **Audit mods:** `pipeio_mod_audit(flow)` → contract drift, missing docs/scripts

**Addressing:** All tools use `(flow, name)` — no `pipe` parameter. Never use raw file paths.
""")

    # Cross-project dispatch guidance (worklog MCP is available everywhere)
    sections.append("""\
## Cross-project dispatch

When filing observations for another project via worklog MCP:

**Model selection:** haiku (trivial/typo) · sonnet (single-module, clear scope) · opus (default, multi-package, architectural)

**Dispatch decision:**
- Well-scoped bug with clear fix → `worklog_note(text, project_id, kind="issue", auto_dispatch=True, model="sonnet")`
- Complex/architectural issue → `worklog_note(text, project_id, kind="issue", auto_dispatch=True)` (opus is default)
- Direct task, no promotion needed → `worklog_note(text, project_id, kind="task", auto_dispatch=True)` (wraps body in ## Prompt, enqueues directly)
- Observation, no immediate action → `worklog_note(text, project_id)` (no auto_dispatch)
- Need result now → `run_prompt(project, prompt)` (synchronous)

Queue timeout is 30 minutes. Use `tail_task(queue_id)` to monitor running tasks.
`list_queue()` defaults to active entries only, newest-first, compact output.
Filter with `schedule_id=`, `since="24h"`, `project=`. Pass `status="all"` for history.
`schedule_queue` accepts `scheduled_at="now"` for immediate or `after="queue_id"` for dependency-based scheduling.
CLI: `worklog queue`, `worklog queue tail <id>`, `worklog queue cancel <id>`.

Use `note_resolve(note_id)` to find notes by timestamp/capture ID.

**Task promotion:** `promote_to_task` only uses LLM enrichment for voice captures.
Agent-written notes get a template prompt pointing at the source — no LLM call needed.
""")

    # Skills section
    skills_dir = root / ".projio" / "skills"
    if skills_dir.is_dir():
        skill_dirs = sorted(
            d for d in skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )
        if skill_dirs:
            skill_lines: list[str] = []
            for d in skill_dirs:
                skill_lines.append(f"- `/{d.name}` — `.projio/skills/{d.name}/SKILL.md`")
            sections.append(
                "## Project skills\n\n"
                "This project has agent skills in `.projio/skills/`. "
                "Read the SKILL.md file for a skill before executing it. "
                "Skills are available as Claude Code slash commands (`/<name>`) "
                "or can be read directly.\n\n"
                + "\n".join(skill_lines)
                + "\n"
            )

    # Development section
    sections.append("""\
## Development

```bash
make         # see available targets
make save    # datalad save
make push    # datalad push
```

Agents should prefer the MCP tools `datalad_save()`, `datalad_push()`, `datalad_pull()`,
and `datalad_status()` over running make/datalad commands directly.
""")

    return "\n".join(sections)


def add_package(root: str | Path, package: str) -> None:
    """Activate a package component in the workspace."""
    root_path = Path(root).expanduser().resolve()
    proj_dir = root_path / ".projio"
    if not proj_dir.exists():
        raise FileNotFoundError(
            f"No .projio/ workspace in {root_path}. Run: projio init"
        )
    if package not in KNOWN_PACKAGES:
        raise ValueError(
            f"Unknown package: {package}. Known: {', '.join(KNOWN_PACKAGES)}"
        )
    data = _load_packages(root_path)
    packages = data.setdefault("packages", {})
    component_path = f".projio/{package}"
    component_dir = root_path / component_path
    _scaffold_component(root_path, package, component_dir)
    packages[package] = {"enabled": True, "path": component_path}
    _save_packages(root_path, data)
    print(f"[OK] activated {package} -> {component_path}")


def remove_package(root: str | Path, package: str) -> None:
    """Deactivate a package component (data is preserved)."""
    root_path = Path(root).expanduser().resolve()
    proj_dir = root_path / ".projio"
    if not proj_dir.exists():
        raise FileNotFoundError(
            f"No .projio/ workspace in {root_path}. Run: projio init"
        )
    data = _load_packages(root_path)
    packages = data.setdefault("packages", {})
    packages[package] = {"enabled": False}
    _save_packages(root_path, data)
    print(f"[OK] deactivated {package}")


def list_packages(root: str | Path) -> list[dict[str, str | bool]]:
    """Return status of all known packages."""
    root_path = Path(root).expanduser().resolve()
    data = _load_packages(root_path)
    packages = data.get("packages", {})
    rows = []
    for name in KNOWN_PACKAGES:
        entry = packages.get(name, {})
        enabled = entry.get("enabled", False)
        path = entry.get("path", "-")
        # check if package is importable
        try:
            __import__(name)
            installed = True
        except ImportError:
            installed = False
        rows.append({
            "package": name,
            "enabled": enabled,
            "installed": installed,
            "path": path if enabled else "-",
        })
    return rows


def print_packages(root: str | Path) -> None:
    """Print package status table."""
    rows = list_packages(root)
    print(f"{'Package':<12} {'Enabled':<10} {'Installed':<12} {'Path'}")
    for r in rows:
        enabled = "yes" if r["enabled"] else "no"
        installed = "yes" if r["installed"] else "no"
        print(f"{r['package']:<12} {enabled:<10} {installed:<12} {r['path']}")
