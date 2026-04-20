"""Tests for projio.sync — code discovery, utils detection, config sync."""
from __future__ import annotations

from pathlib import Path

import yaml

from projio.sync import (
    _detect_project_utils,
    _discover_code_libs,
    _get_bundled_filter,
    _sync_lua_filter,
    _sync_project_utils_config,
    _sync_quarto_config,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def _minimal_project(root: Path) -> None:
    """Create a minimal .projio/config.yml."""
    _write_yaml(root / ".projio" / "config.yml", {"project_name": root.name})


# ---------------------------------------------------------------------------
# _discover_code_libs
# ---------------------------------------------------------------------------


def test_discover_code_libs_empty_dir(tmp_path: Path) -> None:
    assert _discover_code_libs(tmp_path) == []


def test_discover_code_libs_no_lib_dir(tmp_path: Path) -> None:
    assert _discover_code_libs(tmp_path, "code/lib") == []


def test_discover_code_libs_finds_packages_with_init(tmp_path: Path) -> None:
    lib_dir = tmp_path / "code" / "lib" / "mylib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "__init__.py").write_text("")
    libs = _discover_code_libs(tmp_path)
    assert len(libs) == 1
    assert libs[0]["name"] == "mylib"
    assert libs[0]["path"] == "code/lib/mylib"
    assert libs[0]["has_init"] is True


def test_discover_code_libs_finds_packages_with_src(tmp_path: Path) -> None:
    lib_dir = tmp_path / "code" / "lib" / "srclib"
    (lib_dir / "src").mkdir(parents=True)
    libs = _discover_code_libs(tmp_path)
    assert len(libs) == 1
    assert libs[0]["has_init"] is True


def test_discover_code_libs_finds_dir_without_init(tmp_path: Path) -> None:
    lib_dir = tmp_path / "code" / "lib" / "rawlib"
    lib_dir.mkdir(parents=True)
    libs = _discover_code_libs(tmp_path)
    assert len(libs) == 1
    assert libs[0]["has_init"] is False


def test_discover_code_libs_skips_dotdirs(tmp_path: Path) -> None:
    lib_base = tmp_path / "code" / "lib"
    (lib_base / ".hidden").mkdir(parents=True)
    (lib_base / "visible").mkdir(parents=True)
    libs = _discover_code_libs(tmp_path)
    assert len(libs) == 1
    assert libs[0]["name"] == "visible"


def test_discover_code_libs_multiple_sorted(tmp_path: Path) -> None:
    lib_base = tmp_path / "code" / "lib"
    for name in ("zeta", "alpha", "mid"):
        (lib_base / name).mkdir(parents=True)
    libs = _discover_code_libs(tmp_path)
    assert [l["name"] for l in libs] == ["alpha", "mid", "zeta"]


def test_discover_code_libs_custom_path(tmp_path: Path) -> None:
    lib_dir = tmp_path / "lib" / "pkg"
    lib_dir.mkdir(parents=True)
    (lib_dir / "__init__.py").write_text("")
    libs = _discover_code_libs(tmp_path, "lib")
    assert len(libs) == 1
    assert libs[0]["path"] == "lib/pkg"


# ---------------------------------------------------------------------------
# _detect_project_utils
# ---------------------------------------------------------------------------


def test_detect_project_utils_missing(tmp_path: Path) -> None:
    assert _detect_project_utils(tmp_path) is None


def test_detect_project_utils_exists(tmp_path: Path) -> None:
    (tmp_path / "code" / "utils").mkdir(parents=True)
    result = _detect_project_utils(tmp_path)
    assert result == "code/utils"


def test_detect_project_utils_custom_path(tmp_path: Path) -> None:
    (tmp_path / "utils").mkdir()
    result = _detect_project_utils(tmp_path, "utils")
    assert result == "utils"


def test_detect_project_utils_custom_path_missing(tmp_path: Path) -> None:
    assert _detect_project_utils(tmp_path, "my/utils") is None


# ---------------------------------------------------------------------------
# _sync_project_utils_config
# ---------------------------------------------------------------------------


def test_sync_utils_config_no_config_file(tmp_path: Path) -> None:
    result = _sync_project_utils_config(tmp_path, "code/utils")
    assert result["action"] == "skipped"
    assert "no .projio/config.yml" in result["reason"]


def test_sync_utils_config_sets_value(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    result = _sync_project_utils_config(tmp_path, "code/utils")
    assert result["action"] == "set"
    assert result["value"] == "code/utils"
    # Verify written to config
    cfg = yaml.safe_load((tmp_path / ".projio" / "config.yml").read_text())
    assert cfg["code"]["project_utils"] == "code/utils"


def test_sync_utils_config_dry_run(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    result = _sync_project_utils_config(tmp_path, "code/utils", dry_run=True)
    assert result["action"] == "would_set"
    # Config unchanged
    cfg = yaml.safe_load((tmp_path / ".projio" / "config.yml").read_text())
    assert cfg.get("code") is None


def test_sync_utils_config_already_set(tmp_path: Path) -> None:
    _write_yaml(tmp_path / ".projio" / "config.yml", {
        "project_name": "test",
        "code": {"project_utils": "code/utils"},
    })
    result = _sync_project_utils_config(tmp_path, "code/utils")
    assert result["action"] == "skipped"
    assert "already set" in result["reason"]


def test_sync_utils_config_no_utils_found(tmp_path: Path) -> None:
    _minimal_project(tmp_path)
    result = _sync_project_utils_config(tmp_path, None)
    assert result["action"] == "skipped"
    assert "utils" in result["reason"]


# ---------------------------------------------------------------------------
# _get_bundled_filter
# ---------------------------------------------------------------------------


def test_get_bundled_filter_returns_bytes() -> None:
    content = _get_bundled_filter()
    assert isinstance(content, bytes)
    assert len(content) > 0


def test_get_bundled_filter_contains_lua_content() -> None:
    content = _get_bundled_filter()
    # The bundled Lua filter should contain Lua code
    text = content.decode("utf-8", errors="replace")
    assert "function" in text or "--" in text  # Lua function or comment


# ---------------------------------------------------------------------------
# _sync_lua_filter
# ---------------------------------------------------------------------------


def test_sync_lua_filter_copies_to_new_target(tmp_path: Path) -> None:
    result = _sync_lua_filter(tmp_path)
    assert result["action"] == "copied"
    target = tmp_path / ".projio" / "filters" / "include.lua"
    assert target.is_file()
    assert target.read_bytes() == _get_bundled_filter()


def test_sync_lua_filter_skips_if_up_to_date(tmp_path: Path) -> None:
    # First copy
    _sync_lua_filter(tmp_path)
    # Second call should skip
    result = _sync_lua_filter(tmp_path)
    assert result["action"] == "skipped"
    assert "up to date" in result["reason"]


def test_sync_lua_filter_updates_if_content_changed(tmp_path: Path) -> None:
    target = tmp_path / ".projio" / "filters" / "include.lua"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"old content")
    result = _sync_lua_filter(tmp_path)
    assert result["action"] == "updated"
    assert target.read_bytes() == _get_bundled_filter()


def test_sync_lua_filter_dry_run_would_copy(tmp_path: Path) -> None:
    result = _sync_lua_filter(tmp_path, dry_run=True)
    assert result["action"] == "would_copy"
    # Nothing should be written
    assert not (tmp_path / ".projio" / "filters" / "include.lua").exists()


def test_sync_lua_filter_dry_run_would_update(tmp_path: Path) -> None:
    target = tmp_path / ".projio" / "filters" / "include.lua"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"stale content")
    result = _sync_lua_filter(tmp_path, dry_run=True)
    assert result["action"] == "would_update"
    # File should remain unchanged
    assert target.read_bytes() == b"stale content"


# ---------------------------------------------------------------------------
# _sync_quarto_config
# ---------------------------------------------------------------------------


def test_sync_quarto_config_creates_when_missing(tmp_path: Path) -> None:
    result = _sync_quarto_config(tmp_path)
    assert result["action"] == "created"
    target = tmp_path / ".projio" / "render" / "quarto.yml"
    assert target.is_file()
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["min_version"] == "1.5"


def test_sync_quarto_config_skips_when_present(tmp_path: Path) -> None:
    target = tmp_path / ".projio" / "render" / "quarto.yml"
    target.parent.mkdir(parents=True)
    target.write_text('min_version: "1.6"\n', encoding="utf-8")
    result = _sync_quarto_config(tmp_path)
    assert result["action"] == "skipped"
    # Existing file left untouched
    assert "1.6" in target.read_text(encoding="utf-8")


def test_sync_quarto_config_dry_run_would_create(tmp_path: Path) -> None:
    result = _sync_quarto_config(tmp_path, dry_run=True)
    assert result["action"] == "would_create"
    assert not (tmp_path / ".projio" / "render" / "quarto.yml").exists()
