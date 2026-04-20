"""Project status report — CLI wrapper over ``ecosystem_status`` MCP tool."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def _git_status(root: Path) -> tuple[str, int]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        out = result.stdout.strip()
        if not out:
            return ("clean", 0)
        lines = out.splitlines()
        return (out, len(lines))
    except FileNotFoundError:
        return ("(git not found)", 0)


def report(root: str | Path) -> dict[str, Any]:
    """Return the full ecosystem status dict, augmented with git status."""
    root_path = Path(root).expanduser().resolve()

    prev = os.environ.get("PROJIO_ROOT")
    os.environ["PROJIO_ROOT"] = str(root_path)
    try:
        from .mcp.context import ecosystem_status
        data = ecosystem_status()
    finally:
        if prev is None:
            os.environ.pop("PROJIO_ROOT", None)
        else:
            os.environ["PROJIO_ROOT"] = prev

    git_raw, git_count = _git_status(root_path)
    data["git"] = {"short": git_raw, "dirty_count": git_count}
    return data


def _fmt_subsystem(name: str, s: dict[str, Any]) -> str:
    if not s.get("enabled", True) and "enabled" in s:
        return f"{name:8}: disabled"
    parts: list[str] = []
    key_order = [
        "citekey_count",
        "library_count",
        "note_count",
        "flow_count",
        "mod_count",
        "figure_count",
        "corpus_count",
    ]
    for key in key_order:
        if key in s:
            label = key.replace("_count", "")
            parts.append(f"{s[key]} {label}")
    flags: list[str] = []
    if s.get("compiled_stale"):
        flags.append("bib stale")
    if s.get("stale"):
        flags.append("index stale")
    if s.get("registry_valid") is False:
        flags.append("registry invalid")
    if s.get("contracts_valid") is False:
        flags.append("contracts invalid")
    if s.get("valid") is False:
        flags.append("invalid")
    if s.get("available") is False:
        flags.append("unavailable")
    body = ", ".join(parts) if parts else "enabled"
    if flags:
        body += "  [" + ", ".join(flags) + "]"
    return f"{name:8}: {body}"


def print_report(root: str | Path, as_json: bool = False) -> None:
    info = report(root)
    if as_json:
        print(json.dumps(info, indent=2, sort_keys=True))
        return

    if "error" in info:
        print(f"error: {info['error']}")
        return

    health = "healthy" if info.get("healthy") else "issues"
    print(f"Project : {info.get('project_name', '?')}  [{health}]")
    print(f"Root    : {info.get('root', '?')}")

    git = info.get("git", {})
    if git.get("dirty_count", 0) == 0:
        print("Git     : clean")
    else:
        print(f"Git     : {git['dirty_count']} changed")

    for name in ("biblio", "codio", "notio", "pipeio", "figio", "indexio"):
        s = info.get("subsystems", {}).get(name)
        if s is None:
            continue
        print(_fmt_subsystem(name, s))
