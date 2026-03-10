from __future__ import annotations

from pathlib import Path

import yaml

from projio.config import (
    get_user_config_path,
    load_effective_config,
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
