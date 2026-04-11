from __future__ import annotations

from pathlib import Path

import yaml

from projio.config import (
    Layout,
    get_user_config_path,
    get_nested,
    load_effective_config,
    load_layout,
    load_project_config,
    load_user_config,
    print_effective_config,
    resolve_env_all,
    resolve_env_python,
    scaffold_user_config,
    set_python,
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


## get_nested tests


def test_get_nested_simple_key() -> None:
    assert get_nested({"a": 1}, "a") == 1


def test_get_nested_missing_key_returns_default() -> None:
    assert get_nested({"a": 1}, "b") is None
    assert get_nested({"a": 1}, "b", default="x") == "x"


def test_get_nested_deep_key() -> None:
    mapping = {"a": {"b": {"c": 42}}}
    assert get_nested(mapping, "a", "b", "c") == 42


def test_get_nested_partial_path_missing() -> None:
    mapping = {"a": {"b": 1}}
    assert get_nested(mapping, "a", "x", "y") is None


def test_get_nested_non_dict_mid_path_returns_default() -> None:
    mapping = {"a": "scalar"}
    assert get_nested(mapping, "a", "b") is None


def test_get_nested_empty_mapping() -> None:
    assert get_nested({}, "a") is None


## resolve_env_python tests


def test_resolve_env_python_missing_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    result = resolve_env_python(tmp_path / "nonexistent", "default")
    assert result is None


def test_resolve_env_python_missing_conda_prefix(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"code": {"envs": {"default": "myenv"}}}))
    result = resolve_env_python(tmp_path, "default")
    assert result is None  # no conda_prefix


def test_resolve_env_python_missing_env_name(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"code": {"conda_prefix": "/opt/conda", "envs": {}}}))
    result = resolve_env_python(tmp_path, "default")
    assert result is None  # no env name for purpose


def test_resolve_env_python_returns_path(tmp_path: Path, monkeypatch) -> None:
    import sys
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({
        "code": {"conda_prefix": "/opt/conda", "envs": {"default": "myenv"}},
    }))
    result = resolve_env_python(tmp_path, "default")
    assert result is not None
    assert "myenv" in result
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    assert bin_dir in result
    assert result.endswith("python")


def test_resolve_env_python_custom_binary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({
        "code": {"conda_prefix": "/opt/conda", "envs": {"datalad": "labpy"}},
    }))
    result = resolve_env_python(tmp_path, "datalad", binary="datalad")
    assert result is not None
    assert result.endswith("datalad")


## resolve_env_all tests


def test_resolve_env_all_returns_dict_with_expected_keys(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"project_name": "test"}))
    result = resolve_env_all(tmp_path)
    assert set(result.keys()) == {"python", "projio", "docs", "datalad", "pandoc", "matlab"}


def test_resolve_env_all_all_none_without_conda_config(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"project_name": "test"}))
    result = resolve_env_all(tmp_path)
    assert all(v is None for v in result.values())


def test_resolve_env_all_projio_fallback_to_docs(tmp_path: Path, monkeypatch) -> None:
    """projio falls back to docs env when projio env not configured."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({
        "code": {"conda_prefix": "/opt/conda", "envs": {"docs": "docenv"}},
    }))
    result = resolve_env_all(tmp_path)
    assert result["projio"] is not None
    assert "docenv" in result["projio"]


## set_python tests


def test_set_python_no_config_raises(tmp_path: Path) -> None:
    import pytest
    with pytest.raises(FileNotFoundError, match="No .projio/config.yml"):
        set_python(tmp_path)


def test_set_python_sets_current_interpreter(tmp_path: Path, monkeypatch) -> None:
    import sys
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"project_name": "test"}))
    # Patch _write_if_needed so we don't need a full init context
    monkeypatch.setattr("projio.init._write_if_needed", lambda *a, **kw: None)
    set_python(tmp_path)
    cfg = yaml.safe_load(config_path.read_text())
    assert cfg["runtime"]["python_bin"] == sys.executable


def test_set_python_explicit_path(tmp_path: Path, monkeypatch) -> None:
    import sys
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"project_name": "test"}))
    monkeypatch.setattr("projio.init._write_if_needed", lambda *a, **kw: None)
    set_python(tmp_path, python_path=sys.executable)
    cfg = yaml.safe_load(config_path.read_text())
    # set_python resolves symlinks, so compare resolved path
    assert cfg["runtime"]["python_bin"] == str(Path(sys.executable).resolve())


def test_set_python_nonexistent_path_raises(tmp_path: Path, monkeypatch) -> None:
    import pytest
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    config_path = tmp_path / ".projio" / "config.yml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump({"project_name": "test"}))
    with pytest.raises(FileNotFoundError, match="Python not found"):
        set_python(tmp_path, python_path="/nonexistent/python")


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
