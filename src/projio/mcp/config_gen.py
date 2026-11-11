"""Generate MCP configuration for multiple agent systems.

Supports Claude Code (.mcp.json), Codex (.codex/config.toml),
and VS Code / Copilot (.vscode/mcp.json).  All emitters share a
canonical list of ``McpServerDef`` built from project config.
"""
from __future__ import annotations

import json
import re
import shutil
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
    # Add worklog if installed.  Prefer its own console script on PATH (e.g. a
    # separate ``uv tool install``), so it need not share projio's env.
    worklog_mcp = shutil.which("worklog-mcp")
    if worklog_mcp:
        servers.append(McpServerDef(name="worklog", command=worklog_mcp))
    else:
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


_PROJIO_MODULE = "projio.mcp.server"
_WORKLOG_MODULE = "worklog.mcp_server"
_CONDA_ENV_RE = re.compile(r"/(?:ana|mini)?conda\d*/envs/|/(?:mamba|mini)forge\d*/envs/", re.I)


def _entry_module(entry: Any) -> str | None:
    """Return the module an entry runs with ``python -m <module>``, if any."""
    if not isinstance(entry, dict):
        return None
    args = entry.get("args") or []
    if not isinstance(args, list):
        return None
    for i, arg in enumerate(args[:-1]):
        if arg == "-m":
            return args[i + 1]
    return None


def refresh_managed_entries(
    servers: dict[str, Any], generated: dict[str, Any],
) -> None:
    """Point projio-managed entries that projio did not generate at the current runtime.

    An entry that runs ``-m projio.mcp.server`` (e.g. a lab hub with its own
    ``PROJIO_ROOT``) gets the generated ``projio`` command.  An entry that runs
    ``-m worklog.mcp_server`` gets the generated ``worklog`` command and args
    (the ``worklog-mcp`` script when it is on PATH).  ``env`` is kept, and any
    other entry is left untouched.  Mutates *servers* in place.
    """
    projio_def = generated.get("projio")
    worklog_def = generated.get("worklog")
    for name, entry in servers.items():
        if name in generated:
            continue
        module = _entry_module(entry)
        if module == _PROJIO_MODULE and projio_def:
            entry["command"] = projio_def["command"]
        elif module == _WORKLOG_MODULE and worklog_def:
            entry["command"] = worklog_def["command"]
            entry["args"] = list(worklog_def.get("args", []))


def _describe_changes(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """One line per server entry that is added or whose command/args change."""
    lines: list[str] = []
    for name, entry in new.items():
        before = old.get(name)
        if before is None:
            lines.append(f"  [add] {name}: {entry.get('command')}")
            continue
        if not isinstance(before, dict) or not isinstance(entry, dict):
            continue
        if before.get("command") != entry.get("command"):
            lines.append(
                f"  [update] {name}: {before.get('command')} -> {entry.get('command')}"
            )
        elif before.get("args") != entry.get("args"):
            lines.append(f"  [update] {name}: args {before.get('args')} -> {entry.get('args')}")
    return lines


def _conda_warnings(servers: dict[str, Any]) -> list[str]:
    """Warn about entries whose command still runs from a conda env."""
    return [
        f"  [warn] {name}: command runs from a conda env ({entry.get('command')})"
        for name, entry in servers.items()
        if isinstance(entry, dict) and _CONDA_ENV_RE.search(str(entry.get("command", "")))
    ]


def _write_json(path: Path, payload: dict, *, dry_run: bool = False) -> Path:
    """Write JSON payload to *path*, merging with existing content.

    Existing entries that run projio's or worklog's server are pointed at the
    current runtime (see :func:`refresh_managed_entries`); the change list and
    any conda warnings are printed before the file.
    """
    existing_text = path.read_text(encoding="utf-8") if path.exists() else None
    old = _merge_json(existing_text, {})
    merged = _merge_json(existing_text, payload)
    report: list[str] = []
    for key, generated in payload.items():
        section = merged.get(key, {})
        refresh_managed_entries(section, generated)
        report += _describe_changes(old.get(key, {}) or {}, section)
        report += _conda_warnings(section)
    rendered = json.dumps(merged, indent=2) + "\n"

    if dry_run:
        print(f"Would write {path}")
        for line in report:
            print(line)
        print(rendered)
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    for line in report:
        print(line)
    print(f"[OK] wrote {path}")
    return path


def stale_managed_entries(path: Path, *, python_bin: str | None = None) -> list[str]:
    """Names of ``-m projio.mcp.server`` entries in *path* not run by the current interpreter."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return []
    servers = data.get("mcpServers") or {}
    python = python_bin or sys.executable
    return [
        name for name, entry in servers.items()
        if _entry_module(entry) == _PROJIO_MODULE and entry.get("command") != python
    ]


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
