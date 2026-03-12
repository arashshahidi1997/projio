"""MCP tools: project_context, runtime_conventions."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import JsonDict, get_project_root, json_dict

_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\?=|:=|=)\s*(.*?)\s*$")
_VAR_REF_RE = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")


def _parse_makefile_vars(text: str) -> dict[str, str]:
    vars_: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        match = _ASSIGN_RE.match(line)
        if not match:
            continue
        name, _, value = match.groups()
        vars_[name] = value.strip()
    return vars_


def _expand(value: str, vars_: dict[str, str], max_rounds: int = 5) -> str:
    expanded = value
    for _ in range(max_rounds):
        new = _VAR_REF_RE.sub(lambda m: vars_.get(m.group(1), m.group(0)), expanded)
        if new == expanded:
            break
        expanded = new
    return expanded


def project_context() -> JsonDict:
    """Structured snapshot of the project: config, README excerpt, key paths.

    Reads .projio/config.yml and the project README.
    """
    root = get_project_root()
    try:
        from projio.init import load_projio_config
        cfg = load_projio_config(root)
    except FileNotFoundError:
        cfg = {}

    readme_excerpt = ""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        readme_path = root / name
        if readme_path.exists():
            text = readme_path.read_text(encoding="utf-8", errors="ignore")
            readme_excerpt = text[:2000]
            break

    payload: dict[str, Any] = {
        "project_name": cfg.get("project_name", root.name),
        "description": cfg.get("description", ""),
        "root": str(root),
        "config": cfg,
        "readme_excerpt": readme_excerpt,
    }
    return json_dict(payload)


def runtime_conventions() -> JsonDict:
    """Parse Makefile variables and targets from the project root, return as dict."""
    root = get_project_root()
    makefile = root / "Makefile"
    projio_mk = root / ".projio" / "projio.mk"
    exists = makefile.exists()
    vars_: dict[str, str] = {}
    if projio_mk.exists():
        vars_.update(_parse_makefile_vars(projio_mk.read_text(encoding="utf-8")))
    if exists:
        vars_.update(_parse_makefile_vars(makefile.read_text(encoding="utf-8")))
    command_keys = {
        "python": "PYTHON",
        "datalad": "DATALAD",
        "mkdocs": "MKDOCS",
        "projio": "PROJIO",
    }
    commands = {
        name: _expand(vars_[key], vars_)
        for name, key in command_keys.items()
        if key in vars_
    }
    payload: dict[str, Any] = {
        "makefile": {
            "path": str(makefile.relative_to(root)) if exists else "Makefile",
            "exists": exists,
        },
        "vars": vars_,
        "commands": commands,
    }
    return json_dict(payload)
