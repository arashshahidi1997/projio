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
    resolve_profile,
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
        "default_profile", "profiles",
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
    defaults = generate_pandoc_defaults(cfg)
    assert defaults["pdf-engine"] == "xelatex"


def test_generate_pandoc_defaults_bibliography_and_citeproc(tmp_path: Path) -> None:
    cfg = RenderConfig(bibliography="refs.bib", csl="my.csl")
    defaults = generate_pandoc_defaults(cfg)
    assert defaults["citeproc"] is True
    assert defaults["metadata"]["bibliography"] == "refs.bib"
    assert defaults["metadata"]["csl"] == "my.csl"


def test_generate_pandoc_defaults_lua_filter(tmp_path: Path) -> None:
    cfg = RenderConfig(lua_filter="filters/include.lua")
    defaults = generate_pandoc_defaults(cfg)
    assert defaults["filters"] == ["filters/include.lua"]


def test_generate_pandoc_defaults_resource_path(tmp_path: Path) -> None:
    cfg = RenderConfig(resource_path=[".", "docs", "assets"])
    defaults = generate_pandoc_defaults(cfg)
    assert defaults["resource-path"] == [".", "docs", "assets"]


def test_generate_pandoc_defaults_empty_fields_omitted(tmp_path: Path) -> None:
    cfg = RenderConfig(pdf_engine="", bibliography="", csl="", lua_filter="", resource_path=[])
    defaults = generate_pandoc_defaults(cfg)
    assert "pdf-engine" not in defaults
    assert "filters" not in defaults
    assert "resource-path" not in defaults
    # bibliography and csl both empty → no metadata/citeproc
    assert "citeproc" not in defaults


def test_generate_pandoc_defaults_full_config(tmp_path: Path) -> None:
    cfg = RenderConfig()
    defaults = generate_pandoc_defaults(cfg)
    assert "pdf-engine" in defaults
    assert "metadata" in defaults
    assert "filters" in defaults
    assert "resource-path" in defaults


# ---------------------------------------------------------------------------
# write_pandoc_defaults
# ---------------------------------------------------------------------------


def test_write_pandoc_defaults_creates_file(tmp_path: Path) -> None:
    cfg = RenderConfig()
    paths = write_pandoc_defaults(cfg, tmp_path)
    main = paths[-1]
    assert main.exists()
    content = yaml.safe_load(main.read_text())
    assert "pdf-engine" in content


def test_write_pandoc_defaults_default_output_path(tmp_path: Path) -> None:
    cfg = RenderConfig()
    paths = write_pandoc_defaults(cfg, tmp_path)
    assert paths[-1] == tmp_path / ".projio" / "render" / "pandoc-defaults.yaml"


def test_write_pandoc_defaults_custom_output_path(tmp_path: Path) -> None:
    cfg = RenderConfig()
    custom = tmp_path / "output" / "pandoc.yaml"
    paths = write_pandoc_defaults(cfg, tmp_path, output=custom)
    assert paths[-1] == custom
    assert custom.exists()


def test_write_pandoc_defaults_creates_parent_dirs(tmp_path: Path) -> None:
    cfg = RenderConfig()
    deep_output = tmp_path / "a" / "b" / "c" / "pandoc.yaml"
    write_pandoc_defaults(cfg, tmp_path, output=deep_output)
    assert deep_output.exists()


def test_write_pandoc_defaults_returns_list_of_paths(tmp_path: Path) -> None:
    cfg = RenderConfig()
    result = write_pandoc_defaults(cfg, tmp_path)
    assert isinstance(result, list)
    assert result and all(isinstance(p, Path) for p in result)


# ---------------------------------------------------------------------------
# Named profiles
# ---------------------------------------------------------------------------


def test_generate_pandoc_defaults_profile_overrides_base() -> None:
    cfg = RenderConfig(pdf_engine="lualatex", bibliography="base.bib")
    defaults = generate_pandoc_defaults(
        cfg, {"pdf_engine": "xelatex", "citeproc": False, "toc": True}
    )
    assert defaults["pdf-engine"] == "xelatex"   # profile overrides base engine
    assert "citeproc" not in defaults            # profile disables citeproc
    assert defaults["toc"] is True


def test_default_profile_name_resolution() -> None:
    assert RenderConfig(
        profiles={"a": {}, "note": {}}, default_profile="a"
    ).default_profile_name() == "a"
    assert RenderConfig(profiles={"x": {}, "note": {}}).default_profile_name() == "note"
    assert RenderConfig(profiles={"x": {}}).default_profile_name() == "x"
    assert RenderConfig().default_profile_name() == ""


def test_write_pandoc_defaults_writes_per_profile_files(tmp_path: Path) -> None:
    cfg = RenderConfig(
        default_profile="note",
        profiles={"note": {"citeproc": False}, "manuscript": {"citeproc": True}},
    )
    paths = write_pandoc_defaults(cfg, tmp_path)
    render_dir = tmp_path / ".projio" / "render"
    assert render_dir / "pandoc-defaults-note.yaml" in paths
    assert render_dir / "pandoc-defaults-manuscript.yaml" in paths
    # default profile is mirrored into the plain pandoc-defaults.yaml
    assert (render_dir / "pandoc-defaults.yaml").exists()
    note = yaml.safe_load((render_dir / "pandoc-defaults-note.yaml").read_text())
    assert "citeproc" not in note


def test_resolve_profile_prefers_front_matter(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("---\nrender: report\n---\n# Hi\n", encoding="utf-8")
    cfg = RenderConfig(profiles={"note": {}, "report": {}}, default_profile="note")
    assert resolve_profile(md, cfg) == "report"


def test_resolve_profile_falls_back_to_default(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("# no front matter\n", encoding="utf-8")
    cfg = RenderConfig(profiles={"note": {}}, default_profile="note")
    assert resolve_profile(md, cfg) == "note"
