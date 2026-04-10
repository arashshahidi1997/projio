"""Generate MCP configuration for multiple agent systems.

Supports Claude Code (.mcp.json), Codex (.codex/config.toml),
and VS Code / Copilot (.vscode/mcp.json).  All emitters share a
canonical list of ``McpServerDef`` built from project config.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Canonical server representation
# ---------------------------------------------------------------------------

@dataclass
class McpServerDef:
    """A single MCP server definition, agent-agnostic."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


def generate_server_defs(
    root: Path,
    *,
    python_bin: str | None = None,
) -> list[McpServerDef]:
    """Build the canonical list of MCP server definitions for this project.

    Args:
        root: Absolute project root path.
        python_bin: Python binary to use.  Falls back to ``sys.executable``.
    """
    python = python_bin or sys.executable
    servers: list[McpServerDef] = [
        McpServerDef(
            name="projio",
            command=python,
            args=["-m", "projio.mcp.server"],
            env={"PROJIO_ROOT": str(root)},
        ),
    ]
    # Add worklog if installed
    try:
        import worklog.mcp_server  # noqa: F401

        servers.append(
            McpServerDef(
                name="worklog",
                command=python,
                args=["-m", "worklog.mcp_server"],
            )
        )
    except ImportError:
        pass
    return servers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _server_dict(server: McpServerDef) -> dict[str, Any]:
    """Convert a McpServerDef to its JSON-friendly dict (command/args/env)."""
    d: dict[str, Any] = {"command": server.command, "args": server.args}
    if server.env:
        d["env"] = dict(server.env)
    return d


def _merge_json(existing_text: str | None, payload: dict) -> dict:
    """Parse existing JSON text and merge *payload* into it."""
    if existing_text:
        try:
            existing = json.loads(existing_text)
        except (json.JSONDecodeError, ValueError):
            existing = {}
    else:
        existing = {}
    # Merge at the top-level key (mcpServers or servers)
    for key, servers in payload.items():
        existing.setdefault(key, {}).update(servers)
    return existing


def _write_json(path: Path, payload: dict, *, dry_run: bool = False) -> Path:
    """Write JSON payload to *path*, merging with existing content."""
    existing_text = path.read_text(encoding="utf-8") if path.exists() else None
    merged = _merge_json(existing_text, payload)
    rendered = json.dumps(merged, indent=2) + "\n"

    if dry_run:
        print(f"Would write {path}")
        print(rendered)
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    print(f"[OK] wrote {path}")
    return path


# ---------------------------------------------------------------------------
# Emitter: Claude Code / Cursor / Continue (.mcp.json)
# ---------------------------------------------------------------------------

def emit_claude(servers: list[McpServerDef]) -> dict[str, Any]:
    """Return ``{"mcpServers": {...}}`` dict for Claude Code / Cursor / Continue."""
    return {
        "mcpServers": {s.name: _server_dict(s) for s in servers},
    }


def write_mcp_config(
    root: Path,
    *,
    python_bin: str | None = None,
    output: Path | None = None,
    yes: bool = False,
) -> Path:
    """Write (or merge into) ``.mcp.json`` at the project root.

    Backward-compatible entry point — wraps ``generate_server_defs`` + ``emit_claude``.
    """
    out_path = output or (root / ".mcp.json")
    servers = generate_server_defs(root, python_bin=python_bin)
    payload = emit_claude(servers)
    return _write_json(out_path, payload, dry_run=not yes)


# Backward compat: callers that use the old dict-returning API
def generate_mcp_config(
    root: Path,
    *,
    python_bin: str | None = None,
) -> dict[str, Any]:
    """Build ``{"mcpServers": {...}}`` — legacy wrapper over new pipeline."""
    servers = generate_server_defs(root, python_bin=python_bin)
    return emit_claude(servers)


# ---------------------------------------------------------------------------
# Emitter: Codex (.codex/config.toml)
# ---------------------------------------------------------------------------

def emit_codex(servers: list[McpServerDef]) -> str:
    """Return TOML text for the ``[mcp_servers.*]`` section.

    Uses a simple template approach — no ``tomli_w`` dependency.
    The MCP server TOML format is flat enough for reliable string emission.
    """
    lines: list[str] = []
    for s in servers:
        lines.append(f"[mcp_servers.{s.name}]")
        lines.append(f'command = "{s.command}"')
        args_str = ", ".join(f'"{a}"' for a in s.args)
        lines.append(f"args = [{args_str}]")
        if s.env:
            lines.append("")
            lines.append(f"[mcp_servers.{s.name}.env]")
            for k, v in s.env.items():
                lines.append(f'{k} = "{v}"')
        lines.append("")
    return "\n".join(lines)


# Managed block markers for TOML
_CODEX_TOML_BEGIN = "# >>> projio >>>"
_CODEX_TOML_END = "# <<< projio <<<"


def write_codex_config(
    root: Path,
    *,
    python_bin: str | None = None,
    dry_run: bool = False,
) -> Path:
    """Write (or merge into) ``.codex/config.toml`` at the project root.

    Uses managed-block markers to update only the projio-managed MCP servers
    while preserving any other Codex configuration.
    """
    import re

    out_path = root / ".codex" / "config.toml"
    servers = generate_server_defs(root, python_bin=python_bin)
    toml_body = emit_codex(servers)

    block = f"{_CODEX_TOML_BEGIN}\n{toml_body}{_CODEX_TOML_END}\n"

    if out_path.exists():
        text = out_path.read_text(encoding="utf-8")
        pattern = rf"(?ms)^{re.escape(_CODEX_TOML_BEGIN)}\n.*?^{re.escape(_CODEX_TOML_END)}\n?"
        if re.search(pattern, text):
            new_text = re.sub(pattern, block, text)
        else:
            new_text = text.rstrip("\n") + "\n\n" + block
    else:
        new_text = block

    if dry_run:
        print(f"Would write {out_path}")
        print(new_text)
        return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(new_text, encoding="utf-8")
    print(f"[OK] wrote {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Emitter: VS Code / Copilot (.vscode/mcp.json)
# ---------------------------------------------------------------------------

def emit_copilot(servers: list[McpServerDef]) -> dict[str, Any]:
    """Return ``{"servers": {...}}`` dict for VS Code / Copilot."""
    return {
        "servers": {s.name: _server_dict(s) for s in servers},
    }


def write_copilot_config(
    root: Path,
    *,
    python_bin: str | None = None,
    dry_run: bool = False,
) -> Path:
    """Write (or merge into) ``.vscode/mcp.json`` at the project root."""
    out_path = root / ".vscode" / "mcp.json"
    servers = generate_server_defs(root, python_bin=python_bin)
    payload = emit_copilot(servers)
    return _write_json(out_path, payload, dry_run=dry_run)
