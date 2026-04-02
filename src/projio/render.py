"""Render config: .projio/render.yml schema, loading, and pandoc-defaults generation."""
from __future__ import annotations

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
    """Project-level render configuration."""

    pdf_engine: str = "lualatex"
    csl: str = ".projio/render/csl/apa.csl"
    bibliography: str = ".projio/render/compiled.bib"
    lua_filter: str = ".projio/filters/include.lua"
    conda_env: str = ""
    resource_path: list[str] = field(default_factory=lambda: [".", "docs", "docs/assets", "bib"])
    bib_sources: list[str] = field(
        default_factory=lambda: [".projio/biblio/merged.bib", ".projio/pipeio/modkey.bib"],
    )

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
        }


def load_render_config(root: Path) -> RenderConfig:
    """Load render config from .projio/render.yml, merging with defaults."""
    config_path = root / RENDER_CONFIG_PATH
    if not config_path.is_file():
        return RenderConfig()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return RenderConfig.from_dict(data)


def generate_pandoc_defaults(config: RenderConfig, root: Path) -> dict[str, Any]:
    """Produce a pandoc-defaults.yaml-compatible dict from render config."""
    defaults: dict[str, Any] = {}

    if config.pdf_engine:
        defaults["pdf-engine"] = config.pdf_engine

    if config.bibliography:
        defaults["metadata"] = {"bibliography": config.bibliography}
        defaults["citeproc"] = True

    if config.csl:
        defaults.setdefault("metadata", {})["csl"] = config.csl

    if config.lua_filter:
        defaults["filters"] = [config.lua_filter]

    if config.resource_path:
        defaults["resource-path"] = config.resource_path

    return defaults


def write_pandoc_defaults(
    config: RenderConfig,
    root: Path,
    output: Path | None = None,
) -> Path:
    """Write a pandoc-defaults.yaml file from render config.

    Returns the path written.
    """
    defaults = generate_pandoc_defaults(config, root)
    if output is None:
        output = root / ".projio" / "render" / "pandoc-defaults.yaml"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.dump(defaults, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return output


DEFAULT_RENDER_YML = """\
# Project render configuration — single source of truth for pandoc settings.
# Used by: manuscripto, master docs, projio render sync.
pdf_engine: xelatex
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
"""
