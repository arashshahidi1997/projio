"""Shared helper utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_nested, load_effective_config, load_project_config, load_user_config


def project_name(root: Path, cfg: dict[str, Any]) -> str:
    return str(cfg.get("project_name") or root.name)


def helper_defaults(
    root: Path,
    *parts: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    user_cfg = load_user_config()
    project_cfg = load_project_config(root)
    effective_cfg = load_effective_config(root)
    user_defaults = get_nested(user_cfg, *parts, default={}) or {}
    project_defaults = get_nested(project_cfg, *parts, default={}) or {}
    effective_defaults = get_nested(effective_cfg, *parts, default={}) or {}
    return user_defaults, project_defaults, effective_defaults
