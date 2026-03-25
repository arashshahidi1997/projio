"""Shared JSON serialization helpers for projio MCP tools."""
from __future__ import annotations

import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Union, cast

JsonValue = Union[
    None,
    bool,
    int,
    float,
    str,
    List["JsonValue"],
    Dict[str, "JsonValue"],
]
JsonDict = Dict[str, JsonValue]


def get_project_root() -> Path:
    """Return the project root from PROJIO_ROOT env var, defaulting to cwd."""
    raw = os.environ.get("PROJIO_ROOT", ".")
    return Path(raw).expanduser().resolve()


def ensure_json_serializable(value: Any) -> JsonValue:
    """Convert known data structures into JSON-serializable types."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return ensure_json_serializable(asdict(value))
    if isinstance(value, dict):
        return {str(key): ensure_json_serializable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [ensure_json_serializable(item) for item in value]
    raise TypeError(f"Unsupported value for JSON serialization: {value!r}")


def json_dict(payload: Dict[str, Any]) -> JsonDict:
    return cast(JsonDict, ensure_json_serializable(payload))


def resolve_makefile_vars() -> Dict[str, str]:
    """Parse and merge Makefile variables from projio.mk and Makefile.

    Follows ``include`` / ``-include`` directives so that variables defined in
    included files (e.g. ``workflow/runtime.env``) are available for expansion.
    """
    from .context import _parse_makefile_vars

    root = get_project_root()
    vars_: Dict[str, str] = {}
    projio_mk = root / ".projio" / "projio.mk"
    makefile = root / "Makefile"
    if projio_mk.exists():
        vars_.update(_parse_makefile_vars(
            projio_mk.read_text(encoding="utf-8"),
            base_dir=projio_mk.parent,
        ))
    if makefile.exists():
        vars_.update(_parse_makefile_vars(
            makefile.read_text(encoding="utf-8"),
            base_dir=root,
        ))
    return vars_
