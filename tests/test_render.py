"""Tests for projio.render — RenderConfig, load_render_config, pandoc defaults generation."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from projio.render import (
    DEFAULTS,
    RenderConfig,
    generate_pandoc_defaults,
    load_render_config,
    write_pandoc_defaults,
)


# ---------------------------------------------------------------------------
# RenderConfig.from_dict
# ---------------------------------------------------------------------------


def test_render_config_defaults() -> None:
    cfg = RenderConfig()
    assert cfg.pdf_engine == "lualatex"
    assert cfg.csl == ".projio/render/csl/apa.csl"
    assert cfg.bibliography == ".projio/render/compiled.bib"
    assert cfg.lua_filter == ".projio/filters/include.lua"
    assert cfg.conda_env == ""
    assert "." in cfg.resource_path
    assert ".projio/biblio/merged.bib" in cfg.bib_sources


def test_render_config_from_empty_dict_uses_defaults() -> None:
    cfg = RenderConfig.from_dict({})
    assert cfg.pdf_engine == DEFAULTS["pdf_engine"]
    assert cfg.csl == DEFAULTS["csl"]
    assert cfg.bibliography == DEFAULTS["bibliography"]
    assert cfg.lua_filter == DEFAULTS["lua_filter"]
    assert cfg.conda_env == DEFAULTS["conda_env"]
    assert cfg.resource_path == DEFAULTS["resource_path"]
    assert cfg.bib_sources == DEFAULTS["bib_sources"]


def test_render_config_from_dict_overrides_pdf_engine() -> None:
    cfg = RenderConfig.from_dict({"pdf_engine": "xelatex"})
    assert cfg.pdf_engine == "xelatex"
    assert cfg.csl == DEFAULTS["csl"]  # other fields keep defaults


def test_render_config_from_dict_overrides_all_fields() -> None:
    data = {
        "pdf_engine": "pdflatex",
        "csl": "my.csl",
        "bibliography": "refs.bib",
        "lua_filter": "my.lua",
        "conda_env": "myenv",
        "resource_path": [".", "src"],
        "bib_sources": ["merged.bib"],
    }
    cfg = RenderConfig.from_dict(data)
    assert cfg.pdf_engine == "pdflatex"
    assert cfg.csl == "my.csl"
    assert cfg.bibliography == "refs.bib"
    assert cfg.lua_filter == "my.lua"
    assert cfg.conda_env == "myenv"
    assert cfg.resource_path == [".", "src"]
    assert cfg.bib_sources == ["merged.bib"]


# ---------------------------------------------------------------------------
# RenderConfig.to_dict
# ---------------------------------------------------------------------------


def test_render_config_to_dict_roundtrip() -> None:
    original = RenderConfig(pdf_engine="xelatex", conda_env="myenv")
    d = original.to_dict()
    recovered = RenderConfig.from_dict(d)
    assert recovered.pdf_engine == "xelatex"
    assert recovered.conda_env == "myenv"
    assert recovered.csl == original.csl


def test_render_config_to_dict_keys() -> None:
    cfg = RenderConfig()
    d = cfg.to_dict()
    assert set(d.keys()) == {
        "pdf_engine", "csl", "bibliography", "lua_filter",
        "conda_env", "resource_path", "bib_sources",
    }


# ---------------------------------------------------------------------------
# load_render_config
# ---------------------------------------------------------------------------


def test_load_render_config_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    cfg = load_render_config(tmp_path)
    assert cfg == RenderConfig()


def test_load_render_config_reads_yaml_file(tmp_path: Path) -> None:
    render_yml = tmp_path / ".projio" / "render.yml"
    render_yml.parent.mkdir(parents=True)
    render_yml.write_text(yaml.dump({"pdf_engine": "xelatex", "conda_env": "docenv"}))
    cfg = load_render_config(tmp_path)
    assert cfg.pdf_engine == "xelatex"
    assert cfg.conda_env == "docenv"
    assert cfg.csl == DEFAULTS["csl"]  # not overridden → defaults


def test_load_render_config_empty_file_returns_defaults(tmp_path: Path) -> None:
    render_yml = tmp_path / ".projio" / "render.yml"
    render_yml.parent.mkdir(parents=True)
    render_yml.write_text("")
    cfg = load_render_config(tmp_path)
    assert cfg == RenderConfig()


def test_load_render_config_partial_override(tmp_path: Path) -> None:
    render_yml = tmp_path / ".projio" / "render.yml"
    render_yml.parent.mkdir(parents=True)
    render_yml.write_text(yaml.dump({"bib_sources": ["custom.bib"]}))
    cfg = load_render_config(tmp_path)
    assert cfg.bib_sources == ["custom.bib"]
    assert cfg.pdf_engine == DEFAULTS["pdf_engine"]


# ---------------------------------------------------------------------------
# generate_pandoc_defaults
# ---------------------------------------------------------------------------


def test_generate_pandoc_defaults_pdf_engine(tmp_path: Path) -> None:
    cfg = RenderConfig(pdf_engine="xelatex")
    defaults = generate_pandoc_defaults(cfg, tmp_path)
    assert defaults["pdf-engine"] == "xelatex"


def test_generate_pandoc_defaults_bibliography_and_citeproc(tmp_path: Path) -> None:
    cfg = RenderConfig(bibliography="refs.bib", csl="my.csl")
    defaults = generate_pandoc_defaults(cfg, tmp_path)
    assert defaults["citeproc"] is True
    assert defaults["metadata"]["bibliography"] == "refs.bib"
    assert defaults["metadata"]["csl"] == "my.csl"


def test_generate_pandoc_defaults_lua_filter(tmp_path: Path) -> None:
    cfg = RenderConfig(lua_filter="filters/include.lua")
    defaults = generate_pandoc_defaults(cfg, tmp_path)
    assert defaults["filters"] == ["filters/include.lua"]


def test_generate_pandoc_defaults_resource_path(tmp_path: Path) -> None:
    cfg = RenderConfig(resource_path=[".", "docs", "assets"])
    defaults = generate_pandoc_defaults(cfg, tmp_path)
    assert defaults["resource-path"] == [".", "docs", "assets"]


def test_generate_pandoc_defaults_empty_fields_omitted(tmp_path: Path) -> None:
    cfg = RenderConfig(pdf_engine="", bibliography="", csl="", lua_filter="", resource_path=[])
    defaults = generate_pandoc_defaults(cfg, tmp_path)
    assert "pdf-engine" not in defaults
    assert "filters" not in defaults
    assert "resource-path" not in defaults
    # bibliography and csl both empty → no metadata/citeproc
    assert "citeproc" not in defaults


def test_generate_pandoc_defaults_full_config(tmp_path: Path) -> None:
    cfg = RenderConfig()
    defaults = generate_pandoc_defaults(cfg, tmp_path)
    assert "pdf-engine" in defaults
    assert "metadata" in defaults
    assert "filters" in defaults
    assert "resource-path" in defaults


# ---------------------------------------------------------------------------
# write_pandoc_defaults
# ---------------------------------------------------------------------------


def test_write_pandoc_defaults_creates_file(tmp_path: Path) -> None:
    cfg = RenderConfig()
    out = write_pandoc_defaults(cfg, tmp_path)
    assert out.exists()
    content = yaml.safe_load(out.read_text())
    assert "pdf-engine" in content


def test_write_pandoc_defaults_default_output_path(tmp_path: Path) -> None:
    cfg = RenderConfig()
    out = write_pandoc_defaults(cfg, tmp_path)
    assert out == tmp_path / ".projio" / "render" / "pandoc-defaults.yaml"


def test_write_pandoc_defaults_custom_output_path(tmp_path: Path) -> None:
    cfg = RenderConfig()
    custom = tmp_path / "output" / "pandoc.yaml"
    out = write_pandoc_defaults(cfg, tmp_path, output=custom)
    assert out == custom
    assert custom.exists()


def test_write_pandoc_defaults_creates_parent_dirs(tmp_path: Path) -> None:
    cfg = RenderConfig()
    deep_output = tmp_path / "a" / "b" / "c" / "pandoc.yaml"
    write_pandoc_defaults(cfg, tmp_path, output=deep_output)
    assert deep_output.exists()


def test_write_pandoc_defaults_returns_path(tmp_path: Path) -> None:
    cfg = RenderConfig()
    result = write_pandoc_defaults(cfg, tmp_path)
    assert isinstance(result, Path)
