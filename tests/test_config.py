from __future__ import annotations

from pathlib import Path

import yaml

from projio.config import (
    Layout,
    get_user_config_path,
    load_effective_config,
    load_layout,
    load_project_config,
    load_user_config,
    print_effective_config,
    scaffold_user_config,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_load_project_config_reads_local_file(tmp_path: Path) -> None:
    config_path = tmp_path / ".projio" / "config.yml"
    _write_yaml(config_path, {"project_name": "demo"})
    cfg = load_project_config(tmp_path)
    assert cfg["project_name"] == "demo"


def test_load_user_config_reads_xdg_file(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "projio" / "config.yml"
    _write_yaml(config_path, {"helpers": {"sibling": {"gitlab": {"site": "lrz"}}}})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = load_user_config()
    assert cfg["helpers"]["sibling"]["gitlab"]["site"] == "lrz"


def test_load_effective_config_merges_user_and_project(tmp_path: Path, monkeypatch) -> None:
    user_path = tmp_path / "xdg" / "projio" / "config.yml"
    project_path = tmp_path / "repo" / ".projio" / "config.yml"
    _write_yaml(user_path, {"helpers": {"sibling": {"gitlab": {"site": "lrz", "layout": "flat"}}}})
    _write_yaml(project_path, {"project_name": "repo", "helpers": {"sibling": {"gitlab": {"site": "custom"}}}})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    cfg = load_effective_config(tmp_path / "repo")
    assert cfg["helpers"]["sibling"]["gitlab"]["site"] == "custom"
    assert cfg["helpers"]["sibling"]["gitlab"]["layout"] == "flat"


def test_load_effective_config_handles_missing_sections(tmp_path: Path, monkeypatch) -> None:
    project_path = tmp_path / "repo" / ".projio" / "config.yml"
    _write_yaml(project_path, {"project_name": "repo", "project_kind": "generic"})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    cfg = load_effective_config(tmp_path / "repo")
    assert cfg["project_name"] == "repo"


def test_scaffold_user_config_writes_default_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    path = scaffold_user_config()
    assert path == get_user_config_path()
    assert path.exists()
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert payload["helpers"]["sibling"]["github"]["credential"] == "github"


## Layout tests


def test_layout_defaults_match_current_paths() -> None:
    layout = Layout()
    assert layout.docs == "docs"
    assert layout.notes == "docs/log"
    assert layout.pipelines == "code/pipelines"
    assert layout.libraries == "code/lib"
    assert layout.utils == "code/utils"
    assert layout.skills == ".projio/skills"
    assert layout.plan == "plan"


def test_layout_from_empty_config() -> None:
    layout = Layout.from_config({})
    assert layout == Layout()


def test_layout_from_config_overrides_single_key() -> None:
    layout = Layout.from_config({"layout": {"pipelines": "pipelines"}})
    assert layout.pipelines == "pipelines"
    # All other keys retain defaults
    assert layout.docs == "docs"
    assert layout.libraries == "code/lib"


def test_layout_from_config_ignores_unknown_keys() -> None:
    layout = Layout.from_config({"layout": {"pipelines": "pipelines", "bogus": "value"}})
    assert layout.pipelines == "pipelines"
    assert not hasattr(layout, "bogus")


def test_layout_from_config_ignores_non_string_values() -> None:
    layout = Layout.from_config({"layout": {"pipelines": 42}})
    assert layout.pipelines == "code/pipelines"  # default


def test_layout_resolve(tmp_path: Path) -> None:
    layout = Layout(pipelines="my/pipelines")
    assert layout.resolve(tmp_path, "pipelines") == tmp_path / "my" / "pipelines"
    assert layout.resolve(tmp_path, "docs") == tmp_path / "docs"


def test_load_layout_returns_defaults_without_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    layout = load_layout(tmp_path / "nonexistent")
    assert layout == Layout()


def test_load_layout_reads_from_project_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    _write_yaml(config_path, {"layout": {"pipelines": "flows", "libraries": "lib"}})
    layout = load_layout(tmp_path)
    assert layout.pipelines == "flows"
    assert layout.libraries == "lib"
    assert layout.docs == "docs"  # default


def test_print_effective_config_outputs_merged_yaml(tmp_path: Path, monkeypatch, capsys) -> None:
    user_path = tmp_path / "xdg" / "projio" / "config.yml"
    project_path = tmp_path / "repo" / ".projio" / "config.yml"
    _write_yaml(user_path, {"helpers": {"sibling": {"github": {"credential": "github"}}}})
    _write_yaml(project_path, {"project_name": "repo", "project_kind": "generic", "helpers": {"sibling": {"gitlab": {"credential": "gitlab-lrz"}}}})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    print_effective_config(tmp_path / "repo")
    out = capsys.readouterr().out
    assert "project_name: repo" in out
    assert "project_kind: generic" in out
    assert "credential: github" in out
    assert "credential: gitlab-lrz" in out
