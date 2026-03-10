"""Configuration loading for project and user-level projio settings."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_USER_CONFIG = """\
# projio user defaults
helpers:
  sibling:
    github:
      sibling: github
      credential: github
      project_template: "{project_name}"
    gitlab:
      sibling: gitlab
      credential: gitlab
      project_template: "{project_name}"
    ria:
      sibling: origin
      alias_strategy: basename
      storage_url: ria+file:///storage/share/git/ria-store
      shared: group
"""


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise TypeError(f"Expected mapping in {path}")
    return payload


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_user_config_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home.expanduser() / "projio" / "config.yml"


def get_project_config_path(root: str | Path) -> Path:
    return Path(root).expanduser().resolve() / ".projio" / "config.yml"


def load_user_config() -> dict[str, Any]:
    return _read_yaml_mapping(get_user_config_path())


def load_project_config(root: str | Path) -> dict[str, Any]:
    path = get_project_config_path(root)
    if not path.exists():
        raise FileNotFoundError(f"No .projio/config.yml found in {Path(root).expanduser().resolve()}. Run: projio init")
    return _read_yaml_mapping(path)


def load_effective_config(root: str | Path) -> dict[str, Any]:
    user_cfg = load_user_config()
    project_cfg = load_project_config(root)
    return _deep_merge(user_cfg, project_cfg)


def get_nested(mapping: dict[str, Any], *parts: str, default: Any = None) -> Any:
    current: Any = mapping
    for part in parts:
        if not isinstance(current, dict):
            return default
        current = current.get(part, default)
        if current is default:
            return default
    return current


def scaffold_user_config(*, force: bool = False) -> Path:
    path = get_user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        print(f"[SKIP] {path} already exists (--force to overwrite)")
        return path
    path.write_text(DEFAULT_USER_CONFIG, encoding="utf-8")
    print(f"[OK] wrote {path}")
    return path


def print_effective_config(root: str | Path) -> None:
    payload = load_effective_config(root)
    print(yaml.safe_dump(payload, sort_keys=False))
