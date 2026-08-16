"""Render config: .projio/render.yml schema, loading, pandoc-defaults generation, and per-doc rendering.

A single base config (`.projio/render.yml`) plus optional named *profiles* that
override the base. Each profile is emitted as its own `pandoc-defaults-<name>.yaml`,
and the default profile is also written to the plain `pandoc-defaults.yaml` (so
existing tasks keep working). A document selects its profile via front-matter
(`render: <profile>`), falling back to `default_profile`.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


RENDER_CONFIG_PATH = ".projio/render.yml"

DEFAULTS = {
    "pdf_engine": "lualatex",
    "csl": ".projio/render/csl/apa.csl",
    "bibliography": ".projio/render/compiled.bib",
    "lua_filter": ".projio/filters/include.lua",
    "conda_env": "",
    "resource_path": [".", "docs", "docs/assets", "bib"],
    "bib_sources": [".projio/biblio/merged.bib", ".projio/pipeio/modkey.bib"],
}


@dataclass
class RenderConfig:
    """Project-level render configuration (base) plus optional named profiles."""

    pdf_engine: str = "lualatex"
    csl: str = ".projio/render/csl/apa.csl"
    bibliography: str = ".projio/render/compiled.bib"
    lua_filter: str = ".projio/filters/include.lua"
    conda_env: str = ""
    resource_path: list[str] = field(default_factory=lambda: [".", "docs", "docs/assets", "bib"])
    bib_sources: list[str] = field(
        default_factory=lambda: [".projio/biblio/merged.bib", ".projio/pipeio/modkey.bib"],
    )
    # Profiles: name -> dict of overrides on the base. Recognized keys:
    #   citeproc (bool), csl, bibliography, pdf_engine, toc (bool),
    #   number_sections (bool), template (str), variables (dict).
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    default_profile: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RenderConfig:
        return cls(
            pdf_engine=data.get("pdf_engine", DEFAULTS["pdf_engine"]),
            csl=data.get("csl", DEFAULTS["csl"]),
            bibliography=data.get("bibliography", DEFAULTS["bibliography"]),
            lua_filter=data.get("lua_filter", DEFAULTS["lua_filter"]),
            conda_env=data.get("conda_env", DEFAULTS["conda_env"]),
            resource_path=data.get("resource_path", DEFAULTS["resource_path"]),
            bib_sources=data.get("bib_sources", DEFAULTS["bib_sources"]),
            profiles=data.get("profiles", {}) or {},
            default_profile=data.get("default_profile", "") or "",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "pdf_engine": self.pdf_engine,
            "csl": self.csl,
            "bibliography": self.bibliography,
            "lua_filter": self.lua_filter,
            "conda_env": self.conda_env,
            "resource_path": self.resource_path,
            "bib_sources": self.bib_sources,
            "default_profile": self.default_profile,
            "profiles": self.profiles,
        }

    def default_profile_name(self) -> str:
        """The default profile name: explicit `default_profile`, else 'note', else first."""
        if self.default_profile:
            return self.default_profile
        if "note" in self.profiles:
            return "note"
        return next(iter(self.profiles), "")


def load_render_config(root: Path) -> RenderConfig:
    """Load render config from .projio/render.yml, merging with defaults."""
    config_path = root / RENDER_CONFIG_PATH
    if not config_path.is_file():
        return RenderConfig()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return RenderConfig.from_dict(data)


def generate_pandoc_defaults(
    config: RenderConfig,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce a pandoc-defaults.yaml-compatible dict for the base + an optional profile delta.

    With `profile=None` this reproduces the pre-profiles behavior (citeproc on if a
    bibliography is set), so projects without profiles are unaffected.
    """
    p = profile or {}
    engine = p.get("pdf_engine", config.pdf_engine)
    bibliography = p.get("bibliography", config.bibliography)
    csl = p.get("csl", config.csl)
    citeproc = p.get("citeproc", bool(bibliography))

    defaults: dict[str, Any] = {}
    if engine:
        defaults["pdf-engine"] = engine
    if citeproc:
        meta: dict[str, Any] = {}
        if bibliography:
            meta["bibliography"] = bibliography
        if csl:
            meta["csl"] = csl
        if meta:
            defaults["metadata"] = meta
        defaults["citeproc"] = True
    if config.lua_filter:
        defaults["filters"] = [config.lua_filter]
    if config.resource_path:
        defaults["resource-path"] = config.resource_path
    if p.get("toc"):
        defaults["toc"] = True
    if p.get("number_sections"):
        defaults["number-sections"] = True
    if p.get("template"):
        defaults["template"] = p["template"]
    if p.get("variables"):
        defaults["variables"] = p["variables"]
    inc = p.get("include_in_header")
    if inc:
        defaults["include-in-header"] = [inc] if isinstance(inc, str) else list(inc)
    if p.get("highlight_style"):
        defaults["highlight-style"] = p["highlight_style"]
    return defaults


def _dump_yaml(defaults: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(defaults, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


DEFAULT_NOTE_PREAMBLE = r"""% note/report preamble (projio render profiles) — friendly, guide-style output.

% 1. Inline code wraps at any character, so long paths/commands don't overflow.
\usepackage{seqsplit}
\let\projiooldtexttt\texttt
\renewcommand{\texttt}[1]{\projiooldtexttt{\seqsplit{#1}}}
\emergencystretch=3em

% 2. Code-block lines wrap instead of overflowing the box.
\usepackage{fvextra}
\fvset{breaklines=true, breakanywhere=true}

% 3. Boxed code blocks: light background + accent left rule, page-breakable.
\usepackage{tcolorbox}
\tcbuselibrary{skins, breakable}
\definecolor{codebg}{HTML}{F6F7F8}
\definecolor{coderule}{HTML}{9AA7B1}
\makeatletter
\AtBeginDocument{\@ifundefined{Shaded}{}{%
  \renewenvironment{Shaded}{%
    \begin{tcolorbox}[breakable, enhanced, boxrule=0pt, sharp corners,
      colback=codebg, colframe=codebg,
      borderline west={2.2pt}{0pt}{coderule},
      left=6pt, right=6pt, top=3pt, bottom=3pt,
      before skip=6pt, after skip=6pt]%
  }{\end{tcolorbox}}}}
\makeatother
"""


def _ensure_referenced_preambles(config: RenderConfig, root: Path) -> None:
    """Scaffold the default note/report preamble if a profile references it and it's absent."""
    for delta in config.profiles.values():
        inc = delta.get("include_in_header")
        if not inc:
            continue
        for rel in [inc] if isinstance(inc, str) else inc:
            path = root / rel
            if path.name == "preamble-note.tex" and not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(DEFAULT_NOTE_PREAMBLE, encoding="utf-8")


def write_pandoc_defaults(
    config: RenderConfig,
    root: Path,
    output: Path | None = None,
) -> list[Path]:
    """Write pandoc-defaults YAML file(s) from render config.

    Without profiles: writes a single `pandoc-defaults.yaml` (legacy behavior).
    With profiles: writes `pandoc-defaults-<name>.yaml` for each, and mirrors the
    default profile into the plain `pandoc-defaults.yaml`.

    Returns the list of paths written.
    """
    render_dir = root / ".projio" / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    _ensure_referenced_preambles(config, root)
    written: list[Path] = []

    if config.profiles:
        for name, delta in config.profiles.items():
            path = render_dir / f"pandoc-defaults-{name}.yaml"
            _dump_yaml(generate_pandoc_defaults(config, delta), path)
            written.append(path)
        default_delta = config.profiles.get(config.default_profile_name(), {})
        main = output or (render_dir / "pandoc-defaults.yaml")
        _dump_yaml(generate_pandoc_defaults(config, default_delta), main)
        written.append(main)
    else:
        main = output or (render_dir / "pandoc-defaults.yaml")
        _dump_yaml(generate_pandoc_defaults(config), main)
        written.append(main)

    return written


def read_front_matter(path: Path) -> dict[str, Any]:
    """Parse a leading YAML front-matter block (--- ... ---); {} if none/invalid."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            try:
                data = yaml.safe_load("\n".join(lines[1:i])) or {}
            except yaml.YAMLError:
                return {}
            return data if isinstance(data, dict) else {}
    return {}


def resolve_profile(md_path: Path, config: RenderConfig) -> str:
    """Pick the profile for a document: front-matter `render:`/`profile:`, else default."""
    fm = read_front_matter(md_path)
    name = fm.get("render") or fm.get("profile")
    if name:
        return str(name)
    return config.default_profile_name()


def _defaults_path_for(config: RenderConfig, root: Path, profile_name: str) -> Path:
    render_dir = root / ".projio" / "render"
    if profile_name and profile_name != config.default_profile_name():
        candidate = render_dir / f"pandoc-defaults-{profile_name}.yaml"
        if candidate.is_file():
            return candidate
    return render_dir / "pandoc-defaults.yaml"


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def run_render(
    md_file: str,
    config: RenderConfig,
    root: Path,
    profile: str | None = None,
    output: str | None = None,
    yes: bool = True,
) -> None:
    """Render a markdown file to PDF using its resolved profile's pandoc defaults."""
    md_path = Path(md_file)
    if not md_path.is_absolute():
        md_path = root / md_path

    profile_name = profile or resolve_profile(md_path, config)

    # Always refresh the defaults files so they track render.yml.
    write_pandoc_defaults(config, root)
    defaults_path = _defaults_path_for(config, root, profile_name)

    out_path = Path(output) if output else (root / "_build" / "pdf" / f"{md_path.stem}.pdf")
    if not out_path.is_absolute():
        out_path = root / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pandoc_cmd = [
        "pandoc", _rel(md_path, root),
        "--defaults", _rel(defaults_path, root),
        "-o", _rel(out_path, root),
    ]
    cmd = ["conda", "run", "-n", config.conda_env, *pandoc_cmd] if config.conda_env else pandoc_cmd

    print(f"[render] profile={profile_name}  ->  {_rel(out_path, root)}")
    print(f"$ {' '.join(cmd)}")
    if not yes:
        return
    result = subprocess.run(cmd, cwd=str(root))
    if result.returncode != 0:
        sys.exit(result.returncode)


DEFAULT_RENDER_YML = """\
# Project render configuration — single source of truth for pandoc settings.
# Base fields apply to every profile; each profile overrides specific keys.
# Used by: manuscripto, master docs, projio render {sync,show,run}.
pdf_engine: lualatex
csl: .projio/render/csl/apa.csl
bibliography: .projio/render/compiled.bib
bib_sources:
  - .projio/biblio/merged.bib
  - .projio/pipeio/modkey.bib
lua_filter: .projio/filters/include.lua
conda_env: ""
resource_path:
  - .
  - docs
  - docs/assets
  - bib

# Render profiles: a document picks one via front-matter `render: <profile>`,
# else `default_profile`.
default_profile: note

# Friendly typography shared by the non-manuscript profiles.
doc_typography: &doc_typography
  geometry: a4paper,margin=2.2cm
  mainfont: DejaVu Sans
  monofont: DejaVu Sans Mono
  fontsize: 10pt
  linestretch: 1.15
  colorlinks: true
  linkcolor: RoyalBlue
  urlcolor: RoyalBlue

profiles:
  note:
    citeproc: false
    highlight_style: tango
    include_in_header: .projio/render/preamble-note.tex
    variables: *doc_typography
  report:
    citeproc: false
    toc: true
    number_sections: true
    highlight_style: tango
    include_in_header: .projio/render/preamble-note.tex
    variables: *doc_typography
  manuscript:
    citeproc: true
    number_sections: true
"""
