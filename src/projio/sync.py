"""projio sync — auto-discover code libraries, sync filters, generate pandoc defaults."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Any

import yaml


def _discover_code_libs(root: Path, lib_rel: str = "code/lib") -> list[dict[str, Any]]:
    """Scan library directory for Python packages.

    Args:
        root: Project root.
        lib_rel: Relative path to the libraries directory (from Layout).

    Returns a list of dicts with keys: name, path, has_init.
    """
    lib_dir = root / lib_rel
    if not lib_dir.is_dir():
        return []
    libs = []
    for child in sorted(lib_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        has_init = (child / "__init__.py").exists() or (child / "src").is_dir()
        libs.append({
            "name": child.name,
            "path": str(child.relative_to(root)),
            "has_init": has_init,
        })
    return libs


def _detect_project_utils(root: Path, utils_rel: str = "code/utils") -> str | None:
    """Check if the utils directory exists and contains Python code.

    Args:
        root: Project root.
        utils_rel: Relative path to the utils directory (from Layout).
    """
    utils_dir = root / utils_rel
    if utils_dir.is_dir():
        return str(utils_dir.relative_to(root))
    return None


def _sync_codio_libraries(
    root: Path, libs: list[dict[str, Any]], *, dry_run: bool = False,
) -> list[dict[str, str]]:
    """Register discovered libraries in the codio catalog.

    Returns a list of actions taken (added, skipped, updated).
    """
    try:
        from codio import load_config, Registry
        from codio.models import LibraryCatalogEntry, ProjectProfileEntry
        from codio.skills.update import add_library
    except ImportError:
        return [{"action": "error", "name": "", "reason": "codio package not installed"}]

    try:
        config = load_config(root)
        registry = Registry(config=config)
    except Exception as exc:
        return [{"action": "error", "name": "", "reason": str(exc)}]

    actions = []
    existing = {lib.name for lib in registry.list()}

    for lib_info in libs:
        name = lib_info["name"]
        rel_path = lib_info["path"]

        if name in existing:
            # Check if role is already set; update if blank
            record = registry.get(name)
            if record is not None and not getattr(record, "role", ""):
                if dry_run:
                    actions.append({"action": "would_update", "name": name, "field": "role=core"})
                else:
                    cat = registry.catalog.get(name)
                    if cat is not None:
                        cat_dict = cat.model_dump()
                        cat_dict["role"] = "core"
                        updated = LibraryCatalogEntry(**cat_dict)
                        add_library(registry, updated)
                        actions.append({"action": "updated", "name": name, "field": "role=core"})
            else:
                actions.append({"action": "skipped", "name": name, "reason": "already registered"})
            continue

        if dry_run:
            actions.append({"action": "would_add", "name": name, "path": rel_path})
            continue

        catalog_entry = LibraryCatalogEntry(
            name=name,
            kind="internal",
            role="core",
            path=rel_path,
            language="python",
            summary=f"Project core library: {name}",
        )
        profile_entry = ProjectProfileEntry(
            name=name,
            priority="tier1",
            runtime_import="internal",
            status="active",
        )
        add_library(registry, catalog_entry, profile_entry)
        actions.append({"action": "added", "name": name, "path": rel_path})

    return actions


def _sync_project_utils_config(
    root: Path, utils_path: str | None, *, dry_run: bool = False,
) -> dict[str, Any]:
    """Ensure code.project_utils is set in .projio/config.yml if utils exist."""
    import yaml

    from projio.config import get_project_config_path

    config_path = get_project_config_path(root)
    if not config_path.exists():
        return {"action": "skipped", "reason": "no .projio/config.yml"}

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    code_section = cfg.get("code", {}) or {}
    current = code_section.get("project_utils", "")

    if utils_path and not current:
        if dry_run:
            return {"action": "would_set", "field": "code.project_utils", "value": utils_path}
        cfg.setdefault("code", {})["project_utils"] = utils_path
        config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return {"action": "set", "field": "code.project_utils", "value": utils_path}

    if current:
        return {"action": "skipped", "field": "code.project_utils", "reason": f"already set to {current}"}

    return {"action": "skipped", "field": "code.project_utils", "reason": "no code/utils/ found"}


def _get_bundled_filter() -> bytes:
    """Read the bundled include.lua from package data."""
    import importlib.resources

    ref = importlib.resources.files("projio") / "data" / "filters" / "include.lua"
    return ref.read_bytes()


def _sync_lua_filter(root: Path, *, dry_run: bool = False) -> dict[str, str]:
    """Copy include.lua to .projio/filters/ if missing or outdated.

    Compares content hashes to detect changes.
    """
    target = root / ".projio" / "filters" / "include.lua"
    try:
        bundled = _get_bundled_filter()
    except Exception as exc:
        return {"action": "error", "reason": f"cannot read bundled filter: {exc}"}

    bundled_hash = hashlib.sha256(bundled).hexdigest()

    if target.is_file():
        existing_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        if existing_hash == bundled_hash:
            return {"action": "skipped", "reason": "up to date"}
        if dry_run:
            return {"action": "would_update", "reason": "content changed"}
        target.write_bytes(bundled)
        return {"action": "updated", "path": str(target.relative_to(root))}

    if dry_run:
        return {"action": "would_copy", "path": ".projio/filters/include.lua"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bundled)
    return {"action": "copied", "path": str(target.relative_to(root))}


def _get_bundled_csl_files() -> dict[str, bytes]:
    """Read all bundled CSL files from package data."""
    import importlib.resources

    csl_dir = importlib.resources.files("projio") / "data" / "csl"
    result: dict[str, bytes] = {}
    for item in csl_dir.iterdir():
        if hasattr(item, "name") and item.name.endswith(".csl"):
            result[item.name] = item.read_bytes()
    return result


def _sync_csl_files(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Copy bundled CSL files to .projio/render/csl/ if missing or outdated."""
    target_dir = root / ".projio" / "render" / "csl"
    try:
        bundled = _get_bundled_csl_files()
    except Exception as exc:
        return {"action": "error", "reason": f"cannot read bundled CSL files: {exc}"}

    if not bundled:
        return {"action": "skipped", "reason": "no bundled CSL files found"}

    copied = []
    updated = []
    skipped = []

    for name, content in sorted(bundled.items()):
        target = target_dir / name
        bundled_hash = hashlib.sha256(content).hexdigest()

        if target.is_file():
            existing_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if existing_hash == bundled_hash:
                skipped.append(name)
                continue
            if not dry_run:
                target.write_bytes(content)
            updated.append(name)
        else:
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            copied.append(name)

    return {
        "action": "synced" if not dry_run else "would_sync",
        "copied": copied,
        "updated": updated,
        "skipped": skipped,
    }


_QUARTO_YML_DEFAULT = """\
# Projio Quarto defaults for docs/deliverables/reports/*.qmd.
# CSL + bibliography inherit from .projio/render.yml via report.qmd frontmatter;
# report_build enforces min_version as a runtime check.
min_version: "1.5"
"""


def _sync_quarto_config(root: Path, *, dry_run: bool = False) -> dict[str, str]:
    """Create .projio/render/quarto.yml with min_version defaults if missing.

    Leaves existing files untouched — users may override min_version.
    """
    target = root / ".projio" / "render" / "quarto.yml"
    if target.is_file():
        return {"action": "skipped", "reason": "already exists"}
    if dry_run:
        return {"action": "would_create", "path": ".projio/render/quarto.yml"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_QUARTO_YML_DEFAULT, encoding="utf-8")
    return {"action": "created", "path": str(target.relative_to(root))}


def _sync_render_config(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """If .projio/render.yml exists, generate the pandoc defaults file(s).

    With render profiles this is one ``pandoc-defaults-<name>.yaml`` per
    profile plus the plain ``pandoc-defaults.yaml``; ``outputs`` lists them all.
    """
    render_yml = root / ".projio" / "render.yml"
    if not render_yml.is_file():
        return {"action": "skipped", "reason": "no .projio/render.yml"}

    from projio.render import load_render_config, write_pandoc_defaults

    config = load_render_config(root)
    render_dir = root / ".projio" / "render"
    if dry_run:
        paths = [render_dir / f"pandoc-defaults-{name}.yaml" for name in config.profiles or {}]
        paths.append(render_dir / "pandoc-defaults.yaml")
        return {"action": "would_generate", "outputs": [str(p.relative_to(root)) for p in paths]}
    written = write_pandoc_defaults(config, root, output=render_dir / "pandoc-defaults.yaml")
    return {"action": "generated", "outputs": [str(p.relative_to(root)) for p in written]}


def _pixi_env_names(root: Path) -> set[str] | None:
    """Return the environment names declared in the pixi manifest, or None."""
    import tomllib

    manifest = root / "pixi.toml"
    if not manifest.is_file():
        return None
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return {"default", *(data.get("environments", {}) or {})}


def _validate_code_envs(root: Path) -> dict[str, Any]:
    """Check that envs declared in code.envs actually exist.

    pixi projects are checked against the ``[environments]`` table of
    ``pixi.toml``; legacy conda projects against ``code.conda_prefix/envs``.
    Returns a dict with ``valid``, ``missing``, and ``warnings`` keys.
    """
    from projio.config import load_effective_config
    from projio.runners import resolve_runner

    try:
        cfg = load_effective_config(root)
    except FileNotFoundError:
        return {"valid": [], "missing": [], "warnings": ["no .projio/config.yml"]}

    code = cfg.get("code", {}) or {}
    conda_prefix = code.get("conda_prefix")
    envs = code.get("envs", {}) or {}

    if not envs:
        return {"valid": [], "missing": [], "warnings": []}
    if resolve_runner(root) == "pixi":
        declared = _pixi_env_names(root)
        if declared is None:
            return {"valid": [], "missing": [], "warnings": ["pixi runner but no readable pixi.toml"]}
        names = sorted({str(n) for n in envs.values() if n})
        return {
            "valid": [n for n in names if n in declared],
            "missing": [n for n in names if n not in declared],
            "warnings": [],
        }
    if not conda_prefix:
        return {
            "valid": [],
            "missing": [],
            "warnings": ["code.envs configured but code.conda_prefix is missing"],
        }

    prefix = Path(conda_prefix)
    valid: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []

    if not prefix.is_dir():
        warnings.append(f"conda_prefix does not exist: {prefix}")

    seen_envs: set[str] = set()
    for purpose, env_name in sorted(envs.items()):
        if env_name in seen_envs:
            continue
        seen_envs.add(env_name)
        env_dir = prefix / "envs" / env_name
        if env_dir.is_dir():
            valid.append(env_name)
        else:
            missing.append(env_name)

    return {"valid": valid, "missing": missing, "warnings": warnings}


def _sync_projio_mk(root: Path, *, dry_run: bool = False) -> dict[str, str]:
    """Regenerate projio.mk to pick up new manuscripts/masters."""
    from projio.init import _projio_mk

    mk_path = root / ".projio" / "projio.mk"
    new_content = _projio_mk(root)

    if mk_path.is_file():
        existing = mk_path.read_text(encoding="utf-8")
        if existing == new_content:
            return {"action": "skipped", "reason": "up to date"}

    if dry_run:
        return {"action": "would_update"}

    mk_path.parent.mkdir(parents=True, exist_ok=True)
    mk_path.write_text(new_content, encoding="utf-8")
    return {"action": "updated"}


def _sync_mkdocs_monorepo(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Ensure mkdocs.yml has monorepo plugin and !include lines for available subsystems.

    Handles three subsystems:
    - **pipeio**: ``!include ./docs/pipelines/mkdocs.yml`` (requires pipeio registry)
    - **notio log**: ``!include ./docs/log/mkdocs.yml`` (requires docs/log/)
    - **manuscript**: ``!include ./docs/manuscript/mkdocs.yml`` (requires docs/manuscript/)

    Uses text-level insertion to avoid YAML parsing issues with
    ``!!python/name:`` tags used by mkdocs-material.
    """
    mkdocs_path = root / "mkdocs.yml"
    if not mkdocs_path.exists():
        mkdocs_path = root / "mkdocs.yaml"
    if not mkdocs_path.exists():
        return {"action": "skipped", "reason": "no mkdocs.yml"}

    # Detect which subsystems are present
    def _has_flows(reg: Path) -> bool:
        if not reg.exists():
            return False
        try:
            data = yaml.safe_load(reg.read_text(encoding="utf-8")) or {}
        except Exception:
            return True                      # unreadable: let pipeio decide
        return bool(data.get("flows"))       # an empty registry has no pipeline docs to include

    has_pipeio = (
        _has_flows(root / ".projio" / "pipeio" / "registry.yml")
        or _has_flows(root / ".pipeio" / "registry.yml")
    )
    has_log = (root / "docs" / "log").is_dir()
    has_manuscript = (root / "docs" / "manuscript").is_dir()
    from projio.mcp.questio import questio_enabled
    has_plan = questio_enabled(root) and (
        (root / "plan" / "questions.yml").exists()
        or (root / "plan" / "milestones.yml").exists()
    )

    # Discover master doc sections (docs/*/master.md, excluding managed dirs)
    master_sections: list[str] = []
    try:
        from notio.manuscript.master import find_master_files  # type: ignore[import]
        from notio.docs import _MANAGED_SECTIONS  # type: ignore[import]
        for entry in find_master_files(root):
            sec = entry["section_root"]
            if sec not in _MANAGED_SECTIONS and sec not in master_sections:
                master_sections.append(sec)
    except Exception:
        pass

    if not (has_pipeio or has_log or has_manuscript or has_plan or master_sections):
        return {"action": "skipped", "reason": "no subsystems with docs"}

    text = mkdocs_path.read_text(encoding="utf-8")
    changed = False

    # --- Ensure monorepo in plugins ---
    if "- monorepo" not in text:
        if re.search(r"^plugins:", text, re.MULTILINE):
            text = re.sub(
                r"(^plugins:\n(?:  - .+\n)*)",
                r"\g<1>  - monorepo\n",
                text,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            anchor = re.search(r"^markdown_extensions:", text, re.MULTILINE)
            if anchor:
                text = text[:anchor.start()] + "plugins:\n  - search\n  - monorepo\n\n" + text[anchor.start():]
            else:
                text += "\nplugins:\n  - search\n  - monorepo\n"
        changed = True

    # --- Ensure ezlinks in plugins ---
    if "ezlinks" not in text:
        text = re.sub(
            r"(^plugins:\n(?:  - .+\n)*)",
            r"\g<1>  - ezlinks\n",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        changed = True

    # --- Ensure bibtex in plugins (when bibliography exists) ---
    has_bib = (
        (root / ".projio" / "render" / "compiled.bib").exists()
        or (root / ".projio" / "render.yml").exists()
    )
    if has_bib and "bibtex" not in text:
        from projio.render import RenderConfig, RENDER_CONFIG_PATH
        render_yml = root / RENDER_CONFIG_PATH
        if render_yml.exists():
            render_cfg = RenderConfig.from_dict(
                yaml.safe_load(render_yml.read_text(encoding="utf-8")) or {},
            )
        else:
            render_cfg = RenderConfig()
        bib_path = render_cfg.bibliography
        bibtex_block = (
            f"  - bibtex:\n"
            f"      bib_file: {bib_path}\n"
        )
        text = re.sub(
            r"(^plugins:\n(?:  - .+\n)*)",
            r"\g<1>" + bibtex_block,
            text,
            count=1,
            flags=re.MULTILINE,
        )
        changed = True

    # --- Generate sub-mkdocs.yml files ---
    generated: list[str] = []
    if not dry_run:
        if has_log:
            try:
                from notio.docs import log_nav  # type: ignore[import]
                log_nav(root, write=True)
                generated.append("docs/log/mkdocs.yml")
            except Exception:
                pass
        if has_manuscript:
            try:
                from notio.docs import manuscript_nav  # type: ignore[import]
                manuscript_nav(root, write=True)
                generated.append("docs/manuscript/mkdocs.yml")
            except Exception:
                pass
        if master_sections:
            try:
                from notio.docs import master_nav  # type: ignore[import]
                results = master_nav(root, write=True)
                for sec in results:
                    generated.append(f"docs/{sec}/mkdocs.yml")
            except Exception:
                pass
        if has_pipeio:
            try:
                from pipeio.docs import docs_nav  # type: ignore[import]
                docs_nav(root, write=True)
                generated.append("docs/pipelines/mkdocs.yml")
            except Exception:
                pass

    # --- Ensure !include lines in nav ---
    # Fixed subsystems: (label, include path, detection flag, insert-before hint)
    includes: list[tuple[str, str, bool, str | None]] = [
        ("Pipelines", "docs/pipelines/mkdocs.yml", has_pipeio, "Log"),
        ("Plan", "docs/plan/mkdocs.yml", has_plan, "Log"),
        ("Manuscript", "docs/manuscript/mkdocs.yml", has_manuscript, "Log"),
    ]
    # Master doc sections (inserted before Log)
    for sec in master_sections:
        label = sec.replace("-", " ").replace("_", " ").title()
        includes.append((label, f"docs/{sec}/mkdocs.yml", True, "Log"))
    # Log always last
    includes.append(("Log", "docs/log/mkdocs.yml", has_log, None))

    for label, include_path, present, insert_before in includes:
        include_line = f"  - {label}: '!include ./{include_path}'"
        target_exists = (root / include_path).is_file()
        if include_line + "\n" in text and not target_exists and not dry_run:
            # an include projio wrote whose sub-site is not there: mkdocs --strict would fail on it
            text = text.replace(include_line + "\n", "", 1)
            changed = True
            continue
        if not present or (not target_exists and not dry_run):
            continue
        include_marker = f"!include ./{include_path}"
        if include_marker in text:
            continue

        include_line = f"  - {label}: '!include ./{include_path}'"
        nav_match = re.search(r"^nav:", text, re.MULTILINE)
        if not nav_match:
            continue

        if insert_before:
            anchor = re.search(rf"^  - {insert_before}:", text, re.MULTILINE)
            if anchor:
                text = text[:anchor.start()] + include_line + "\n" + text[anchor.start():]
                changed = True
                continue

        # Fallback: append at end of nav
        text = text.rstrip("\n") + "\n" + include_line + "\n"
        changed = True

    if not changed and not generated:
        return {"action": "skipped", "reason": "already configured"}

    if dry_run:
        return {"action": "would_update"}

    if changed:
        mkdocs_path.write_text(text, encoding="utf-8")
    return {"action": "updated", "path": str(mkdocs_path.relative_to(root)), "generated": generated}


_PROJIO_VSCODE_BEGIN = "// >>> projio >>>"
_PROJIO_VSCODE_END = "// <<< projio <<<"


_PROJIO_WATCHER_EXCLUDES = [
    "**/site/**",
    "**/_site/**",
    "**/_build/**",
    "**/build/**",
    "**/.projio/indexio/index/**",
    "**/.snakemake/**",
    "**/__pycache__/**",
    "**/.git/**",
]


def _find_json_block(text: str, key: str) -> tuple[int, int] | None:
    """Find the span of a JSON key + brace-delimited value in JSONC text.

    Returns (start, end) covering from the key to the closing brace,
    including any trailing comma.  Uses brace counting to handle nested values.
    """
    key_pattern = rf'"{re.escape(key)}"\s*:\s*\{{'
    m = re.search(key_pattern, text)
    if not m:
        return None
    # Walk forward counting braces from the opening {
    brace_start = text.index("{", m.start() + len(key))
    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                # Consume trailing comma and whitespace
                rest = text[end:]
                trail = re.match(r'\s*,?', rest)
                if trail:
                    end += trail.end()
                # Include leading whitespace/newline before the key
                start = m.start()
                while start > 0 and text[start - 1] in " \t":
                    start -= 1
                if start > 0 and text[start - 1] == "\n":
                    start -= 1
                return (start, end)
    return None


def _collect_existing_excludes(text: str, key: str) -> list[str]:
    """Extract existing exclude patterns from a JSONC settings key."""
    span = _find_json_block(text, key)
    if not span:
        return []
    block = text[span[0]:span[1]]
    return re.findall(r'"([^"]+)"\s*:\s*true', block)


def _remove_unmanaged_excludes(text: str, key: str) -> str:
    """Remove the user-section exclude block so it doesn't conflict with the managed one."""
    managed_pattern = rf"{re.escape(_PROJIO_VSCODE_BEGIN)}.*?{re.escape(_PROJIO_VSCODE_END)}"
    managed_match = re.search(managed_pattern, text, flags=re.DOTALL)

    span = _find_json_block(text, key)
    if not span:
        return text
    # Skip if inside managed block
    if managed_match and managed_match.start() <= span[0] <= managed_match.end():
        return text
    return text[:span[0]] + text[span[1]:]


def _sync_vscode_settings(root: Path, render_cfg: Any, *, dry_run: bool = False) -> dict[str, str]:
    """Sync projio-managed VS Code settings: PandocCiter + watcher excludes.

    Uses a managed block (like gitignore) to avoid destroying JSONC comments
    or user settings.  The block is inserted/replaced between markers.

    For files.watcherExclude: merges projio's standard patterns with any
    existing user patterns, then writes the combined set into the managed
    block.  The unmanaged copy (if any) is removed to avoid conflicts.
    """
    settings_path = root / ".vscode" / "settings.json"
    if not settings_path.parent.is_dir():
        return {"action": "skipped", "reason": "no .vscode/"}
    if not settings_path.exists():
        return {"action": "skipped", "reason": "no .vscode/settings.json"}

    bib = render_cfg.bibliography or ""
    csl = render_cfg.csl or ""

    text = settings_path.read_text(encoding="utf-8")

    # Collect existing watcher excludes from BOTH user section and managed block
    existing_excludes = _collect_existing_excludes(text, "files.watcherExclude")
    # Merge: projio standard + existing user patterns (deduplicated, sorted)
    merged_excludes = sorted(set(_PROJIO_WATCHER_EXCLUDES + existing_excludes))

    # Remove unmanaged files.watcherExclude so it doesn't conflict
    text = _remove_unmanaged_excludes(text, "files.watcherExclude")

    # Build the managed block
    lines = [f"  {_PROJIO_VSCODE_BEGIN}"]
    if bib:
        lines.append(f'  "PandocCiter.DefaultBibs": ["{bib}"],')
        lines.append(f'  "PandocCiter.UseDefaultBib": true,')
    if csl:
        lines.append(f'  "pandocCiter.csl": "{csl}",')
    lines.append(f'  "files.watcherExclude": {{')
    for pattern in merged_excludes:
        lines.append(f'    "{pattern}": true,')
    lines.append(f'  }},')
    lines.append(f"  {_PROJIO_VSCODE_END}")
    block = "\n".join(lines)

    original = settings_path.read_text(encoding="utf-8")

    # Replace existing managed block, or insert before closing brace
    managed_re = rf"[ \t]*{re.escape(_PROJIO_VSCODE_BEGIN)}\n.*?{re.escape(_PROJIO_VSCODE_END)}"
    if re.search(managed_re, text, flags=re.DOTALL):
        text = re.sub(managed_re, block, text, flags=re.DOTALL)
    else:
        last_brace = text.rfind("}")
        if last_brace >= 0:
            text = text[:last_brace] + "\n" + block + "\n" + text[last_brace:]

    if text == original:
        return {"action": "skipped", "reason": "already up to date"}

    if dry_run:
        return {"action": "would_update"}

    settings_path.write_text(text, encoding="utf-8")
    return {"action": "updated"}


def _sync_agent_configs(root: Path, *, dry_run: bool = False) -> dict[str, dict[str, Any]]:
    """Regenerate MCP configs for enabled agent packages (codex, copilot).

    Checks packages.yml for ``codex.enabled`` / ``copilot.enabled`` and
    regenerates their config files using the current server definitions.
    """
    from .config import load_effective_config, get_nested

    results: dict[str, dict[str, Any]] = {}
    packages_path = root / ".projio" / "packages.yml"
    if not packages_path.exists():
        return results

    try:
        import yaml
        data = yaml.safe_load(packages_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return results

    packages = data.get("packages", {})

    # Resolve python binary (same logic as CLI mcp-config)
    try:
        cfg = load_effective_config(root)
    except FileNotFoundError:
        cfg = {}
    python_bin = get_nested(cfg, "runtime", "projio_python", default=None) or \
                 get_nested(cfg, "runtime", "python_bin", default=None)

    # Codex
    if packages.get("codex", {}).get("enabled"):
        try:
            from .mcp.config_gen import write_codex_config
            write_codex_config(root, python_bin=python_bin, dry_run=dry_run)
            results["codex"] = {"action": "would_update" if dry_run else "updated"}
        except Exception as exc:
            results["codex"] = {"action": "error", "reason": str(exc)}

    # Copilot
    if packages.get("copilot", {}).get("enabled"):
        try:
            from .mcp.config_gen import write_copilot_config
            write_copilot_config(root, python_bin=python_bin, dry_run=dry_run)
            results["copilot"] = {"action": "would_update" if dry_run else "updated"}
        except Exception as exc:
            results["copilot"] = {"action": "error", "reason": str(exc)}

    return results


def _sync_gitignore(root: Path, *, dry_run: bool = False) -> str:
    """Refresh the ``# >>> projio >>>`` .gitignore block so entry changes reach existing projects."""
    from projio.init import _detect_site_framework, _ensure_projio_gitignore

    return _ensure_projio_gitignore(
        root, site_framework=_detect_site_framework(root), dry_run=dry_run, quiet=True,
    )


def _with_project_root(root: Path, func):
    """Call *func* with ``PROJIO_ROOT`` pointing at *root* (the MCP helpers read it)."""
    import os

    old = os.environ.get("PROJIO_ROOT")
    os.environ["PROJIO_ROOT"] = str(root)
    try:
        return func()
    finally:
        if old is None:
            os.environ.pop("PROJIO_ROOT", None)
        else:
            os.environ["PROJIO_ROOT"] = old


def _sync_questio_docs(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Regenerate questio plan docs if plan/questions.yml exists and questio is not turned off.

    ``questio: {enabled: false}`` in the project config skips the step. The
    deliverables indexes are a separate step (``_sync_deliverables_index``).
    """
    from projio.mcp.questio import questio_enabled

    if not questio_enabled(root):
        return {"action": "disabled", "reason": "questio.enabled is false"}
    questions_path = root / "plan" / "questions.yml"
    if not questions_path.exists():
        return {"action": "skipped", "reason": "no plan/questions.yml"}
    if dry_run:
        return {"action": "would_generate"}
    try:
        from projio.mcp.questio import questio_docs_collect
        result = _with_project_root(root, lambda: questio_docs_collect(include_deliverables=False))
        if "error" in result:
            return {"action": "error", "reason": result["error"]}
        return {"action": "generated", "files": result.get("generated", 0)}
    except Exception as exc:
        return {"action": "error", "reason": str(exc)}


def _sync_deliverables_index(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Regenerate the docs/deliverables/ index pages, independent of questio.

    Runs where the project already has generated deliverables indexes, or where
    questio's plan exists (which generated them before this was its own step),
    so a project that never had them does not get new folders. A page without
    the generated marker is never overwritten.
    """
    from projio.mcp.questio import deliverables_docs_collect, deliverables_index_generated, questio_enabled

    d = root / "docs" / "deliverables"
    if not d.is_dir():
        return {"action": "skipped", "reason": "no docs/deliverables/"}
    uses_generated = (d / "index.md").is_file() and deliverables_index_generated(d / "index.md")
    had_questio = questio_enabled(root) and (root / "plan" / "questions.yml").exists()
    if not (uses_generated or had_questio):
        return {"action": "skipped", "reason": "docs/deliverables/ has no generated index"}
    if dry_run:
        return {"action": "would_generate"}
    try:
        result = deliverables_docs_collect(root)
        return {"action": "generated", "files": result["generated"], "deliverables": result["deliverables"],
                "kept": result["kept"]}
    except Exception as exc:
        return {"action": "error", "reason": str(exc)}


_CLAUDE_CMD_HEADER = "<!-- projio:skill-sync — regenerated by projio sync -->\n"


_SKILL_STAMP = ".projio-skill"          # marks a .claude/skills/<name>/ folder projio writes
_SKILL_FORMAT = 2                       # bump to rewrite every synced copy once (2: top header, read-only)
_SKILL_OWN = (_SKILL_STAMP, ".gitignore")  # projio's bookkeeping files in a synced copy
_SKILL_NOTE = "<!-- GENERATED by projio sync from {source}; edit the source, not this copy -->\n"


def _skill_source_files(src_dir: Path) -> list[Path]:
    return sorted(f for f in src_dir.rglob("*") if f.is_file() and "__pycache__" not in f.parts)


def _skill_digest(src_dir: Path, files: list[Path]) -> str:
    return hashlib.sha256(b"".join(f.relative_to(src_dir).as_posix().encode() + f.read_bytes()
                                   for f in files)).hexdigest()[:16]


def _render_skill(root: Path, src_md: Path, files: list[Path]) -> dict[str, bytes]:
    """The synced copy of a skill: its source files, with the GENERATED note in SKILL.md.

    The note goes right after the frontmatter (Claude Code needs the frontmatter
    first), or at the very top when there is none.
    """
    src_dir = src_md.parent
    try:
        shown = src_md.relative_to(root).as_posix()
    except ValueError:
        shown = str(src_md)
    note = _SKILL_NOTE.format(source=shown)
    out: dict[str, bytes] = {}
    for f in files:
        rel = f.relative_to(src_dir).as_posix()
        if rel in _SKILL_OWN:
            continue
        if rel == "SKILL.md":
            text = f.read_text(encoding="utf-8")
            if text.startswith("---"):
                end = text.find("\n---", 3)
                cut = text.find("\n", end + 4) + 1 if end != -1 else 0
                if end != -1 and cut == 0:          # frontmatter closes at end of file
                    text, cut = text + "\n", len(text) + 1
                text = text[:cut] + note + text[cut:]
            else:
                text = note + text
            out[rel] = text.encode("utf-8")
        else:
            out[rel] = f.read_bytes()
    return out


def _read_copy(dest: Path) -> dict[str, bytes]:
    """The files of a synced copy, without projio's own bookkeeping files."""
    return {f.relative_to(dest).as_posix(): f.read_bytes()
            for f in sorted(dest.rglob("*"))
            if f.is_file() and not (f.parent == dest and f.name in _SKILL_OWN)}


def _rmtree(path: Path) -> None:
    """Remove a synced copy; its files are read-only, which Windows refuses to unlink."""
    import os
    import shutil
    import stat

    def _retry(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_retry)
    else:
        shutil.rmtree(path, onerror=_retry)


def _skill_plan(root: Path) -> tuple[Path, list[dict[str, Any]], set[str]]:
    """Discovered skills paired with their synced copy: ``(skills_dir, entries, managed)``.

    Skills matching ``skills.disabled`` in the project config are left out, so
    their generated copies are removed; their sources are never touched.
    """
    import os

    from .skills import disabled_skills, is_disabled

    old_root = os.environ.get("PROJIO_ROOT")
    os.environ["PROJIO_ROOT"] = str(root)
    try:
        from projio.mcp.context import _discover_skills
        skills = _discover_skills(root)
    finally:
        if old_root is None:
            os.environ.pop("PROJIO_ROOT", None)
        else:
            os.environ["PROJIO_ROOT"] = old_root

    skills_dir = root / ".claude" / "skills"
    managed = {d.name for d in skills_dir.iterdir() if (d / _SKILL_STAMP).is_file()} if skills_dir.is_dir() else set()
    entries = []
    disabled = disabled_skills(root)
    for skill in skills:
        if is_disabled(skill["name"], disabled):
            continue
        src_md = Path(skill["path"])
        src_md = src_md if src_md.is_absolute() else root / src_md
        if not src_md.is_file():
            continue
        files = _skill_source_files(src_md.parent)
        stamp = {"source": str(src_md.parent), "sha": _skill_digest(src_md.parent, files),
                 "origin": skill.get("source", "project"), "format": _SKILL_FORMAT}
        entries.append({"name": skill["name"], "src_md": src_md, "files": files, "stamp": stamp,
                        "dest": skills_dir / skill["name"]})
    return skills_dir, entries, managed


def _sync_claude_skills(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Make every discovered skill a native Claude Code skill in ``.claude/skills/<name>/``.

    Claude Code picks a skill from the task by its frontmatter ``description``,
    and loads the body only when it is used; the old ``.claude/commands/``
    wrappers had no description and needed an MCP call to load the skill
    (docs/specs/agent-interface-layers.md). Each folder is a copy of the skill's
    source folder (project, installed package such as biblio, or projio's
    bundle) with a stamp recording the source and its hash, and a ``.gitignore``
    of ``*`` so the generated copy stays out of git (it is regenerated per
    machine, like the commands were). The copy's SKILL.md starts (after its
    frontmatter) with a GENERATED note naming the source, and every file is
    written read-only, so an agent does not edit the copy by mistake. A copy
    edited by hand anyway is restored, and the edited SKILL.md is kept beside it
    as ``.claude/skills/<name>.edited.md``. Folders without the stamp belong to
    the project and are never touched. The old managed command files are removed.
    """
    import json
    import stat

    skills_dir, entries, managed = _skill_plan(root)
    written: list[str] = []
    kept: list[str] = []
    restored: list[str] = []
    desired: set[str] = set()
    for e in entries:
        name, dest, stamp = e["name"], e["dest"], e["stamp"]
        if dest.exists() and name not in managed:
            kept.append(name)                     # the project's own skill of that name wins
            continue
        desired.add(name)
        rendered = _render_skill(root, e["src_md"], e["files"])
        edited = False
        try:
            current = json.loads((dest / _SKILL_STAMP).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = None
        if current == stamp:
            if _read_copy(dest) == rendered:
                continue                          # up to date
            edited = True                         # same source, different copy: edited by hand
        written.append(name)
        if edited:
            restored.append(name)
        if dry_run:
            continue
        if edited and (dest / "SKILL.md").is_file():
            backup = skills_dir / f"{name}.edited.md"
            backup.write_bytes((dest / "SKILL.md").read_bytes())
        if dest.exists():
            _rmtree(dest)
        dest.mkdir(parents=True)
        extra = {".gitignore": b"*\n", _SKILL_STAMP: (json.dumps(stamp, indent=1) + "\n").encode("utf-8")}
        for rel, data in {**rendered, **extra}.items():
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

    removed = sorted(managed - desired - set(kept))
    if not dry_run:
        for name in removed:
            _rmtree(skills_dir / name)

    # the old wrappers: .claude/commands/<name>.md files projio wrote
    cmd_dir = root / ".claude" / "commands"
    old_commands = []
    if cmd_dir.is_dir():
        for f in sorted(cmd_dir.glob("*.md")):
            try:
                if f.read_text(encoding="utf-8").startswith(_CLAUDE_CMD_HEADER):
                    old_commands.append(f.stem)
                    if not dry_run:
                        f.unlink()
            except OSError:
                continue

    if not (written or removed or old_commands):
        return {"action": "skipped", "reason": "all skills up to date", "total": len(desired), "kept": kept}
    return {"action": "would_update" if dry_run else "updated", "written": written, "removed": removed,
            "restored": restored, "kept": kept, "commands_removed": old_commands, "total": len(desired)}


def check_skills(root: str | Path) -> dict[str, Any]:
    """Compare every synced skill copy with its source, without writing anything.

    Each problem is ``{"skill", "status", "detail"}``; status is one of
    ``missing`` (no copy yet), ``stale`` (the source changed since the last
    sync, per the stamp's sha), ``outdated`` (written by an older projio sync),
    ``edited`` (the copy differs from what its source renders to),
    ``disabled`` (a copy of a skill in ``skills.disabled``) or ``orphaned``
    (a copy whose skill no longer exists).
    """
    from .skills import disabled_skills, is_disabled

    import json

    root = Path(root).expanduser().resolve()
    skills_dir, entries, managed = _skill_plan(root)
    drift: list[dict[str, str]] = []
    desired: set[str] = set()
    for e in entries:
        name, dest, stamp = e["name"], e["dest"], e["stamp"]
        if dest.exists() and name not in managed:
            continue                              # the project's own skill
        desired.add(name)
        src = e["src_md"]
        if not dest.exists():
            drift.append({"skill": name, "status": "missing", "detail": f"not synced yet from {src}"})
            continue
        try:
            current = json.loads((dest / _SKILL_STAMP).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = {}
        if current.get("format") != _SKILL_FORMAT:
            drift.append({"skill": name, "status": "outdated", "detail": "written by an older projio sync"})
        elif current.get("sha") != stamp["sha"] or current.get("source") != stamp["source"]:
            drift.append({"skill": name, "status": "stale", "detail": f"source changed since the last sync: {src}"})
        elif _read_copy(dest) != _render_skill(root, src, e["files"]):
            drift.append({"skill": name, "status": "edited",
                          "detail": f"the copy was edited by hand; move the edits to {src}"})
    disabled = disabled_skills(root)
    for name in sorted(managed - desired):
        if is_disabled(name, disabled):
            drift.append({"skill": name, "status": "disabled",
                          "detail": "listed in skills.disabled but its synced copy is still there"})
        else:
            drift.append({"skill": name, "status": "orphaned", "detail": "no source skill of that name any more"})
    return {"drift": drift}


# Env-manager commands a skill may tell the agent to run, by runner (projio.runners.resolve_runner).
_RUNNER_COMMANDS = {
    "conda": re.compile(r"\b(?:conda|mamba|micromamba)\s+(?:run|activate)\b"),
    "pixi": re.compile(r"\bpixi\s+(?:run|shell)\b"),
}
# Which of those contradict each configured runner. Under "none" (bare commands) a
# named env still routes through pixi, so only conda is wrong there.
_RUNNER_CONTRADICTS = {"pixi": ["conda"], "none": ["conda"], "conda": ["pixi"]}
# Names that skills used to point at and that no longer exist anywhere in the ecosystem.
_RETIRED_TERMS = ("notebook_bootstrap", "utility-promote")
_LINT_IGNORE = "projio-lint: ignore"


def lint_skills(root: str | Path) -> dict[str, Any]:
    """Flag skill text that contradicts the project's configuration.

    Reads the source of every discovered skill plus the project's own folders in
    ``.claude/skills/``, and reports a line when it tells the agent to use an env
    manager other than the configured runner (``conda run`` in a pixi project,
    and so on), or names a retired helper (``_RETIRED_TERMS`` plus the project's
    ``skills.lint.retired`` list in ``.projio/config.yml``). A line carrying
    ``projio-lint: ignore`` (say in an HTML comment) is skipped.
    """
    from .runners import resolve_runner

    root = Path(root).expanduser().resolve()
    runner = resolve_runner(root)
    try:
        from .config import load_effective_config
        cfg = load_effective_config(root)
    except Exception:
        cfg = {}
    extra = ((cfg.get("skills") or {}).get("lint") or {}).get("retired") or []
    retired = [*_RETIRED_TERMS, *(str(t) for t in extra)]
    wrong = {m: _RUNNER_COMMANDS[m] for m in _RUNNER_CONTRADICTS.get(runner, [])}

    skills_dir, entries, managed = _skill_plan(root)
    sources = [(e["name"], e["src_md"]) for e in entries]
    if skills_dir.is_dir():
        sources += [(d.name, d / "SKILL.md") for d in sorted(skills_dir.iterdir())
                    if d.is_dir() and d.name not in managed and (d / "SKILL.md").is_file()]
    findings: list[dict[str, Any]] = []
    for name, path in sources:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        try:
            shown = path.relative_to(root).as_posix()
        except ValueError:
            shown = str(path)
        for no, line in enumerate(lines, 1):
            if _LINT_IGNORE in line:
                continue
            for manager, pattern in wrong.items():
                m = pattern.search(line)
                if m:
                    findings.append({"skill": name, "path": shown, "line": no, "rule": "env-manager",
                                     "detail": f"`{m.group(0)}` but this project's runner is {runner}"})
            for term in retired:
                if term in line:
                    findings.append({"skill": name, "path": shown, "line": no, "rule": "retired",
                                     "detail": f"`{term}` no longer exists"})
    return {"runner": runner, "findings": findings}


def run_check(root: str | Path) -> int:
    """``projio sync --check``: report what is out of line, change nothing. Returns the exit code."""
    root = Path(root).expanduser().resolve()
    drift = check_skills(root)["drift"]
    for d in drift:
        print(f"[!] .claude/skills/{d['skill']}: {d['status']}: {d['detail']}")
    if drift:
        print(f"{len(drift)} synced skill copies out of line; `projio sync` rewrites them from their sources.")
    else:
        print("[=] .claude/skills/: every synced copy matches its source")
    lint = lint_skills(root)
    for f in lint["findings"]:
        print(f"[!] {f['path']}:{f['line']}: {f['rule']}: {f['detail']}")
    if lint["findings"]:
        print(f"{len(lint['findings'])} skill lines contradict the project config; edit the skill sources "
              f"(read commands from runtime_conventions() instead of naming an env manager).")
    else:
        print(f"[=] skills: no text contradicts the project config (runner: {lint['runner']})")
    return 1 if drift or lint["findings"] else 0


_PROJIO_HOOK_MARKER = "# projio-managed"


def _install_git_hooks(root: Path, *, dry_run: bool = False) -> dict[str, str]:
    """Install a projio-managed post-commit hook that runs ``projio sync --index``.

    Only writes if the hook doesn't exist or is already projio-managed.
    On Windows (outside WSL), hooks are skipped — use WSL for full support.
    """
    import sys

    if sys.platform == "win32":
        return {"action": "skipped", "reason": "git hooks not supported on Windows (use WSL)"}

    hook_path = root / ".git" / "hooks" / "post-commit"

    hook_content = f"""\
#!/bin/sh
{_PROJIO_HOOK_MARKER}
# Auto-rebuild stale indexio sources after commit
projio sync --index -C "$(git rev-parse --show-toplevel)" &
"""

    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8")
        if _PROJIO_HOOK_MARKER not in existing:
            return {"action": "skipped", "reason": "existing non-projio hook"}
        if existing == hook_content:
            return {"action": "skipped", "reason": "up to date"}
        if dry_run:
            return {"action": "would_update"}
        hook_path.write_text(hook_content, encoding="utf-8")
        hook_path.chmod(0o755)
        return {"action": "updated"}

    if dry_run:
        return {"action": "would_install"}
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(hook_content, encoding="utf-8")
    hook_path.chmod(0o755)
    return {"action": "installed"}


def _sync_index_rebuild(
    root: Path, cfg: dict[str, Any], *, force: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """Incrementally rebuild stale indexio sources.

    Args:
        root: Project root.
        cfg: Effective projio config.
        force: If True, rebuild regardless of ``automation.index.on_sync`` config.
        dry_run: If True, report what would happen without rebuilding.
    """
    indexio_cfg = cfg.get("indexio", {}) or {}
    if not indexio_cfg.get("config"):
        return {"action": "skipped", "reason": "indexio not configured"}

    auto_cfg = (cfg.get("automation", {}) or {}).get("index", {}) or {}
    if not force and not auto_cfg.get("on_sync", False):
        return {"action": "skipped", "reason": "automation.index.on_sync not enabled"}

    background = auto_cfg.get("background", True)

    try:
        import os
        os.environ.setdefault("PROJIO_ROOT", str(root))
        from projio.mcp.rag import _resolve_update_sources, indexio_build
    except ImportError:
        return {"action": "skipped", "reason": "indexio not installed"}

    if dry_run:
        try:
            stale = _resolve_update_sources()
        except Exception:
            stale = []
        if stale:
            return {"action": "would_rebuild", "stale_sources": stale}
        return {"action": "skipped", "reason": "all sources up to date"}

    try:
        result = indexio_build(update=True, background=background)
    except Exception as exc:
        return {"action": "error", "reason": str(exc)}

    return {"action": "rebuilt", "result": result}


def sync_workspace(root: str | Path, *, dry_run: bool = False, index: bool | None = None, install_hooks: bool = False) -> dict[str, Any]:
    """Run all sync operations on a projio workspace.

    1. Discover code/lib/*/ → register in codio with role=core
    2. Detect code/utils/ → set code.project_utils in config
    3. Copy include.lua to .projio/filters/
    4. Copy CSL files to .projio/render/csl/
    5. Generate .projio/render/pandoc-defaults.yaml from .projio/render.yml
    6. Validate code.envs conda configuration
    7. Regenerate projio.mk
    8. Ensure mkdocs.yml has monorepo plugin + pipeio !include
    9. Sync VS Code settings (PandocCiter + watcher excludes) via managed block
    10. Sync agent MCP configs (codex, copilot)
    10b. Refresh the managed # >>> projio >>> block in .gitignore
    11. Write .claude/skills/<name>/ (native Claude Code skills) from discovered skills
    12. Regenerate questio plan docs if plan/questions.yml exists (unless questio.enabled is false)
    12b. Regenerate docs/deliverables/ indexes, independent of questio
    13. Incrementally rebuild stale indexio sources (if --index or config)
    14. Install git hooks (if --install-hooks)

    Args:
        root: Project root directory.
        dry_run: If True, show what would change without writing.
        index: If True, force index rebuild; if False, skip; if None, check config.
        install_hooks: If True, install projio-managed git hooks.

    Returns:
        Summary of actions taken.
    """
    root_path = Path(root).expanduser().resolve()
    projio_dir = root_path / ".projio"
    if not projio_dir.is_dir():
        print(f"[ERROR] No .projio/ directory in {root_path}. Run: projio init")
        return {"error": "not initialized"}

    prefix = "[DRY RUN] " if dry_run else ""

    # Load layout for path resolution
    from projio.config import load_layout
    layout = load_layout(root_path)

    # 1. Discover code libraries
    libs = _discover_code_libs(root_path, layout.libraries)
    if libs:
        print(f"{prefix}Found {len(libs)} library(ies) in {layout.libraries}/: {', '.join(l['name'] for l in libs)}")
        lib_actions = _sync_codio_libraries(root_path, libs, dry_run=dry_run)
        for action in lib_actions:
            if action["action"] in ("added", "would_add"):
                print(f"  {prefix}[+] {action['name']} → codio (role=core, kind=internal)")
            elif action["action"] in ("updated", "would_update"):
                print(f"  {prefix}[~] {action['name']} → {action.get('field', '')}")
            elif action["action"] == "skipped":
                print(f"  [=] {action['name']} ({action.get('reason', '')})")
            elif action["action"] == "error":
                print(f"  [!] {action.get('reason', 'unknown error')}")
    else:
        lib_actions = []
        print(f"{prefix}No libraries found in {layout.libraries}/")

    # 2. Detect project utils
    utils_path = _detect_project_utils(root_path, layout.utils)
    utils_action = _sync_project_utils_config(root_path, utils_path, dry_run=dry_run)
    if utils_action["action"] in ("set", "would_set"):
        print(f"{prefix}[+] {utils_action['field']} = {utils_action['value']}")
    elif utils_action["action"] == "skipped":
        reason = utils_action.get("reason", "")
        if "already set" in reason:
            print(f"[=] code.project_utils ({reason})")
        elif "not found" not in reason:
            print(f"[=] code.project_utils ({reason})")

    # 3. Sync Lua filter
    filter_action = _sync_lua_filter(root_path, dry_run=dry_run)
    if filter_action["action"] in ("copied", "would_copy"):
        print(f"{prefix}[+] include.lua → .projio/filters/")
    elif filter_action["action"] in ("updated", "would_update"):
        print(f"{prefix}[~] include.lua updated in .projio/filters/")
    elif filter_action["action"] == "skipped":
        print(f"[=] include.lua ({filter_action.get('reason', '')})")
    elif filter_action["action"] == "error":
        print(f"[!] Lua filter: {filter_action.get('reason', '')}")

    # 4. Sync CSL files
    csl_action = _sync_csl_files(root_path, dry_run=dry_run)
    if csl_action.get("copied"):
        print(f"{prefix}[+] CSL files → .projio/render/csl/: {', '.join(csl_action['copied'])}")
    if csl_action.get("updated"):
        print(f"{prefix}[~] CSL files updated: {', '.join(csl_action['updated'])}")
    if csl_action.get("action") == "error":
        print(f"[!] CSL sync: {csl_action.get('reason', '')}")

    # 5. Generate pandoc defaults from render.yml
    from projio.render import RenderConfig, load_render_config
    try:
        render_cfg = load_render_config(root_path)
    except Exception:
        render_cfg = RenderConfig()
    # A broken render.yml must not abort the remaining sync steps.
    try:
        render_action = _sync_render_config(root_path, dry_run=dry_run)
    except Exception as exc:
        render_action = {"action": "error", "reason": f"{type(exc).__name__}: {exc}"}
    if render_action["action"] in ("generated", "would_generate"):
        print(f"{prefix}[+] pandoc defaults → {', '.join(render_action['outputs'])}")
    elif render_action["action"] == "error":
        print(f"[!] render config: {render_action['reason']}")

    # 5b. Scaffold .projio/render/quarto.yml (report_build reads min_version)
    quarto_action = _sync_quarto_config(root_path, dry_run=dry_run)
    if quarto_action["action"] in ("created", "would_create"):
        print(f"{prefix}[+] quarto.yml → {quarto_action.get('path', '.projio/render/quarto.yml')}")

    # 6. Validate code.envs configuration
    env_validation = _validate_code_envs(root_path)
    for w in env_validation.get("warnings", []):
        print(f"[!] code.envs: {w}")
    for m in env_validation.get("missing", []):
        print(f"[!] code.envs: env not found: {m}")
    if env_validation.get("valid"):
        print(f"[=] code.envs: validated {', '.join(env_validation['valid'])}")

    # 7. Task interface: regenerate projio.mk for make projects; CLI-first projects get pixi.toml
    from projio.init import _resolve_task_runner
    mk_action: dict[str, str] = {"action": "skipped", "reason": "task_runner=cli"}
    if _resolve_task_runner(root_path) == "make":
        mk_action = _sync_projio_mk(root_path, dry_run=dry_run)
        if mk_action["action"] in ("updated", "would_update"):
            print(f"{prefix}[~] projio.mk regenerated")
    elif not dry_run:
        from projio.init import _ensure_pixi_scaffold
        _ensure_pixi_scaffold(root_path)

    # 8. Ensure mkdocs monorepo plugin + subsystem !includes + sub-mkdocs.yml
    mkdocs_action = _sync_mkdocs_monorepo(root_path, dry_run=dry_run)
    if mkdocs_action["action"] in ("updated", "would_update"):
        generated = mkdocs_action.get("generated", [])
        if generated:
            print(f"{prefix}[+] mkdocs.yml: monorepo !includes + generated {', '.join(generated)}")
        else:
            print(f"{prefix}[+] mkdocs.yml: monorepo plugin + !includes")
    elif mkdocs_action["action"] == "skipped":
        reason = mkdocs_action.get("reason", "")
        if reason not in ("no mkdocs.yml", "no subsystems with docs"):
            print(f"[=] mkdocs.yml ({reason})")

    # 9. Sync VS Code settings (PandocCiter + watcher excludes)
    vscode_action = _sync_vscode_settings(root_path, render_cfg, dry_run=dry_run)
    if vscode_action["action"] in ("updated", "would_update"):
        print(f"{prefix}[+] .vscode/settings.json: projio managed block updated")
    elif vscode_action["action"] == "skipped":
        reason = vscode_action.get("reason", "")
        if "no .vscode" in reason:
            print(f"[!] {reason} — PandocCiter autocompletion won't work without it")

    # 10. Sync agent MCP configs (codex, copilot) if enabled in packages.yml
    agent_actions = _sync_agent_configs(root_path, dry_run=dry_run)
    for agent_name, action in agent_actions.items():
        if action["action"] in ("updated", "would_update"):
            print(f"{prefix}[~] {agent_name}: MCP config regenerated")
        elif action["action"] == "error":
            print(f"[!] {agent_name}: {action.get('reason', '')}")

    # 10b. Refresh the managed .gitignore block (same entries as projio init)
    gitignore_action = _sync_gitignore(root_path, dry_run=dry_run)
    if gitignore_action in ("created", "updated", "would_create", "would_update"):
        print(f"{prefix}[~] .gitignore: projio managed block refreshed (lines outside it untouched)")
    else:
        print("[=] .gitignore: projio managed block up to date")

    # 11. Write .claude/skills/<name>/ (native Claude Code skills) from discovered skills
    cmd_action = _sync_claude_skills(root_path, dry_run=dry_run)
    if cmd_action["action"] in ("updated", "would_update"):
        written = cmd_action.get("written", [])
        removed = cmd_action.get("removed", [])
        total = cmd_action.get("total", 0)
        parts = []
        if written:
            parts.append(f"{len(written)} written")
        if removed:
            parts.append(f"{len(removed)} removed")
        print(f"{prefix}[+] .claude/skills/: {', '.join(parts)} ({total} skills total)")
        for name in cmd_action.get("restored", []):
            print(f"[!] .claude/skills/{name}: the synced copy was edited by hand and is restored; "
                  f"the edited SKILL.md is kept as .claude/skills/{name}.edited.md. Edit the source instead.")
    elif cmd_action["action"] == "skipped":
        print(f"[=] .claude/skills/: {cmd_action.get('total', 0)} skills up to date")

    # 12. Regenerate questio plan docs if questions.yml exists
    questio_action = _sync_questio_docs(root_path, dry_run=dry_run)
    if questio_action["action"] == "would_generate":
        print(f"{prefix}[+] questio: would regenerate plan docs")
    elif questio_action["action"] == "generated":
        print(f"[+] questio: regenerated {questio_action.get('files', 0)} plan docs")
    elif questio_action["action"] == "disabled":
        print("[-] questio: disabled (config)")
    elif questio_action["action"] == "error":
        print(f"[!] questio: {questio_action.get('reason', '')}")

    # 12b. Regenerate docs/deliverables/ indexes (independent of questio)
    deliverables_action = _sync_deliverables_index(root_path, dry_run=dry_run)
    if deliverables_action["action"] == "would_generate":
        print(f"{prefix}[+] deliverables: would regenerate index pages")
    elif deliverables_action["action"] == "generated":
        print(f"[+] deliverables: regenerated {deliverables_action.get('files', 0)} index pages")
        for path in deliverables_action.get("kept", []):
            print(f"[=] deliverables: kept hand-written {Path(path).relative_to(root_path)}")
    elif deliverables_action["action"] == "error":
        print(f"[!] deliverables: {deliverables_action.get('reason', '')}")

    # 13. Incrementally rebuild stale indexio sources
    try:
        from projio.init import load_projio_config
        cfg = load_projio_config(root_path)
    except FileNotFoundError:
        cfg = {}
    index_force = index if index is not None else False
    index_action = _sync_index_rebuild(root_path, cfg, force=index_force, dry_run=dry_run)
    if index_action["action"] == "rebuilt":
        result_data = index_action.get("result", {})
        if result_data.get("status") == "up_to_date":
            print(f"[=] indexio: all sources up to date")
        elif result_data.get("background"):
            print(f"{prefix}[+] indexio: rebuild started (background, job {result_data.get('job_id', '?')})")
        else:
            print(f"{prefix}[+] indexio: index rebuilt")
    elif index_action["action"] == "would_rebuild":
        stale = index_action.get("stale_sources", [])
        print(f"{prefix}[~] indexio: would rebuild {len(stale)} stale source(s): {', '.join(stale)}")
    elif index_action["action"] == "error":
        print(f"[!] indexio: {index_action.get('reason', 'unknown error')}")
    elif index_action["action"] == "skipped":
        reason = index_action.get("reason", "")
        if reason not in ("indexio not configured", "automation.index.on_sync not enabled"):
            print(f"[=] indexio: {reason}")

    # 14. Install git hooks if requested
    hooks_action: dict[str, str] = {"action": "skipped", "reason": "not requested"}
    if install_hooks:
        hooks_action = _install_git_hooks(root_path, dry_run=dry_run)
        if hooks_action["action"] in ("installed", "would_install"):
            print(f"{prefix}[+] git hook: post-commit installed")
        elif hooks_action["action"] in ("updated", "would_update"):
            print(f"{prefix}[~] git hook: post-commit updated")
        elif hooks_action["action"] == "skipped":
            reason = hooks_action.get("reason", "")
            if "non-projio" in reason:
                print(f"[!] git hook: skipped (existing non-projio post-commit hook)")
            elif reason != "up to date":
                print(f"[=] git hook: {reason}")

    return {
        "libraries": lib_actions,
        "project_utils": utils_action,
        "lua_filter": filter_action,
        "csl_files": csl_action,
        "render": render_action,
        "quarto": quarto_action,
        "code_envs": env_validation,
        "projio_mk": mk_action,
        "mkdocs": mkdocs_action,
        "vscode": vscode_action,
        "agents": agent_actions,
        "claude_skills": cmd_action,
        "questio": questio_action,
        "deliverables": deliverables_action,
        "index": index_action,
        "hooks": hooks_action,
    }
