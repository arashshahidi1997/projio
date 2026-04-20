"""Tests for projio.init — scaffold, profiles, config overlay, kinds."""
from __future__ import annotations

from pathlib import Path

import yaml

from projio.init import (
    PROFILES,
    KIND_CHOICES,
    _apply_config_overlay,
    _deep_merge,
    _gitignore_entries_for_framework,
    scaffold,
)
from projio.config import Layout


def _read_config(root: Path) -> dict:
    return yaml.safe_load((root / ".projio" / "config.yml").read_text()) or {}


# ---------------------------------------------------------------------------
# _deep_merge
# ---------------------------------------------------------------------------


def test_deep_merge_flat() -> None:
    base = {"a": 1, "b": 2}
    result = _deep_merge(base, {"b": 3, "c": 4})
    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested() -> None:
    base = {"x": {"a": 1, "b": 2}}
    result = _deep_merge(base, {"x": {"b": 3, "c": 4}})
    assert result == {"x": {"a": 1, "b": 3, "c": 4}}


def test_deep_merge_adds_new_nested() -> None:
    base = {"x": 1}
    result = _deep_merge(base, {"y": {"a": 2}})
    assert result == {"x": 1, "y": {"a": 2}}


# ---------------------------------------------------------------------------
# _apply_config_overlay
# ---------------------------------------------------------------------------


def _write_config(root: Path, cfg: dict) -> None:
    path = root / ".projio" / "config.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")


def test_apply_config_overlay_merges(tmp_path: Path) -> None:
    _write_config(tmp_path, {"project_name": "test", "code": {"project_utils": ""}})
    _apply_config_overlay(tmp_path, {"code": {"project_utils": "utils"}, "new_key": "val"})
    cfg = _read_config(tmp_path)
    assert cfg["code"]["project_utils"] == "utils"
    assert cfg["new_key"] == "val"
    assert cfg["project_name"] == "test"  # preserved


def test_apply_config_overlay_noop_without_config(tmp_path: Path) -> None:
    # No config.yml — should not crash
    _apply_config_overlay(tmp_path, {"key": "val"})
    assert not (tmp_path / ".projio" / "config.yml").exists()


def test_apply_config_overlay_layout(tmp_path: Path) -> None:
    _write_config(tmp_path, {"project_name": "test", "layout": {"docs": "docs"}})
    _apply_config_overlay(tmp_path, {"layout": {"pipelines": "flows"}})
    cfg = _read_config(tmp_path)
    assert cfg["layout"]["pipelines"] == "flows"
    assert cfg["layout"]["docs"] == "docs"  # preserved


# ---------------------------------------------------------------------------
# scaffold — generic kind
# ---------------------------------------------------------------------------


def test_scaffold_generic_creates_base_files(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic")
    assert (tmp_path / ".projio" / "config.yml").exists()
    assert (tmp_path / ".projio" / "projio.mk").exists()
    assert (tmp_path / "Makefile").exists()
    assert (tmp_path / "docs" / "index.md").exists()


def test_scaffold_generic_config_has_layout(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic")
    cfg = _read_config(tmp_path)
    assert "layout" in cfg
    layout = Layout.from_config(cfg)
    assert layout.pipelines == "code/pipelines"
    assert layout.docs == "docs"


def test_scaffold_generic_config_has_project_name(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic")
    cfg = _read_config(tmp_path)
    assert cfg["project_name"] == tmp_path.name


def test_scaffold_generic_idempotent(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic")
    config_before = (tmp_path / ".projio" / "config.yml").read_text()
    scaffold(tmp_path, kind="generic")
    config_after = (tmp_path / ".projio" / "config.yml").read_text()
    assert config_before == config_after


# ---------------------------------------------------------------------------
# scaffold — tool kind
# ---------------------------------------------------------------------------


def test_scaffold_tool_creates_src_layout(tmp_path: Path) -> None:
    root = tmp_path / "my_tool"
    root.mkdir()
    scaffold(root, kind="tool")
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "my_tool" / "__init__.py").exists()
    assert (root / "tests").is_dir()


# ---------------------------------------------------------------------------
# scaffold — study kind
# ---------------------------------------------------------------------------


def test_scaffold_study_creates_docs_subsections(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="study")
    for subdir in ("log", "plan", "pipelines", "manuscript"):
        assert (tmp_path / "docs" / subdir).is_dir()


def test_scaffold_study_creates_code_tiers(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="study")
    for subdir in ("pipelines", "lib", "scripts", "utils"):
        assert (tmp_path / "code" / subdir).is_dir()


def test_scaffold_study_creates_plan_stubs(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="study")
    assert (tmp_path / "plan" / "questions.yml").exists()
    assert (tmp_path / "plan" / "milestones.yml").exists()


def test_scaffold_study_creates_render_yml(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="study")
    assert (tmp_path / ".projio" / "render.yml").exists()


def test_scaffold_study_config_has_layout(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="study")
    cfg = _read_config(tmp_path)
    layout = Layout.from_config(cfg)
    assert layout.pipelines == "code/pipelines"


# ---------------------------------------------------------------------------
# scaffold — invalid inputs
# ---------------------------------------------------------------------------


def test_scaffold_invalid_kind_raises(tmp_path: Path) -> None:
    import pytest
    with pytest.raises(ValueError, match="Unknown project kind"):
        scaffold(tmp_path, kind="bogus")


def test_scaffold_invalid_profile_raises(tmp_path: Path) -> None:
    import pytest
    with pytest.raises(ValueError, match="Unknown profile"):
        scaffold(tmp_path, kind="generic", profile="bogus")


# ---------------------------------------------------------------------------
# scaffold — profiles
# ---------------------------------------------------------------------------


def test_profiles_dict_has_expected_keys() -> None:
    assert "research" in PROFILES
    assert "full" in PROFILES
    assert "flat" in PROFILES


def test_scaffold_flat_profile_layout(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic", profile="flat")
    cfg = _read_config(tmp_path)
    layout = Layout.from_config(cfg)
    assert layout.pipelines == "pipelines"
    assert layout.libraries == "lib"
    assert layout.utils == "utils"
    # docs stays default
    assert layout.docs == "docs"


def test_scaffold_flat_profile_pipeio_pipelines_dir(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic", profile="flat")
    cfg = _read_config(tmp_path)
    assert cfg["pipeio"]["pipelines_dir"] == "pipelines"


def test_scaffold_research_profile_enables_packages(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic", profile="research")
    packages_path = tmp_path / ".projio" / "packages.yml"
    assert packages_path.exists()
    data = yaml.safe_load(packages_path.read_text()) or {}
    pkgs = data.get("packages", {})
    for name in ("notio", "biblio", "indexio"):
        assert name in pkgs, f"{name} not in packages.yml"


def test_scaffold_full_profile_enables_all(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="generic", profile="full")
    packages_path = tmp_path / ".projio" / "packages.yml"
    data = yaml.safe_load(packages_path.read_text()) or {}
    pkgs = data.get("packages", {})
    for name in ("notio", "biblio", "codio", "indexio", "pipeio", "figio"):
        assert name in pkgs, f"{name} not in packages.yml"


# ---------------------------------------------------------------------------
# KIND_CHOICES constant
# ---------------------------------------------------------------------------


def test_kind_choices_complete() -> None:
    assert set(KIND_CHOICES) == {"generic", "tool", "study"}


# ---------------------------------------------------------------------------
# Gitignore entries
# ---------------------------------------------------------------------------


def test_gitignore_includes_quarto_report_caches() -> None:
    entries = _gitignore_entries_for_framework("mkdocs")
    assert "docs/deliverables/reports/*/_freeze/" in entries
    assert "docs/deliverables/reports/*/_files/" in entries
