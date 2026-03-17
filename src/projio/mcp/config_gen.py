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
    return {
        "mcpServers": {
            "projio": {
                "command": python,
                "args": ["-m", "projio.mcp.server"],
                "env": {"PROJIO_ROOT": str(root)},
            },
        },
    }


def write_mcp_config(
    root: Path,
    *,
    python_bin: str | None = None,
    output: Path | None = None,
    yes: bool = False,
) -> Path:
    """Write (or preview) .mcp.json at the project root.

    Returns the output path.
    """
    out_path = output or (root / ".mcp.json")
    payload = generate_mcp_config(root, python_bin=python_bin)
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
