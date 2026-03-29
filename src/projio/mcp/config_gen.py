"""Generate .mcp.json for Claude Code (or other MCP clients)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def generate_mcp_config(
    root: Path,
    *,
    python_bin: str | None = None,
) -> dict[str, Any]:
    """Build an MCP server config dict for this project.

    Args:
        root: Absolute project root path.
        python_bin: Python binary to use. Falls back to ``sys.executable``.
    """
    python = python_bin or sys.executable
    servers: dict[str, Any] = {
        "projio": {
            "command": python,
            "args": ["-m", "projio.mcp.server"],
            "env": {"PROJIO_ROOT": str(root)},
        },
    }
    # Add worklog if installed (use python -m, same pattern as projio)
    try:
        import worklog.mcp_server  # noqa: F401
        servers["worklog"] = {
            "command": python,
            "args": ["-m", "worklog.mcp_server"],
        }
    except ImportError:
        pass
    return {"mcpServers": servers}


def write_mcp_config(
    root: Path,
    *,
    python_bin: str | None = None,
    output: Path | None = None,
    yes: bool = False,
) -> Path:
    """Write (or merge into) .mcp.json at the project root.

    If the file already exists, merges generated servers into the existing
    config (updating projio/worklog entries, preserving others).

    Returns the output path.
    """
    out_path = output or (root / ".mcp.json")
    generated = generate_mcp_config(root, python_bin=python_bin)

    # Merge into existing file if present
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
        existing.setdefault("mcpServers", {}).update(generated["mcpServers"])
        payload = existing
    else:
        payload = generated

    rendered = json.dumps(payload, indent=2) + "\n"

    if not yes:
        print("Would write", out_path)
        print(rendered)
        print("Pass --yes to write.")
        return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(f"[OK] wrote {out_path}")
    return out_path
