"""MCP tools: datalad save, status, push, pull for projio-managed projects."""
from __future__ import annotations

import subprocess
from typing import Any

from .common import JsonDict, get_project_root, json_dict
from .context import _parse_makefile_vars, _expand


def _resolve_datalad_bin() -> str:
    """Resolve the datalad binary from Makefile/projio.mk variables."""
    root = get_project_root()
    vars_: dict[str, str] = {}
    projio_mk = root / ".projio" / "projio.mk"
    makefile = root / "Makefile"
    if projio_mk.exists():
        vars_.update(_parse_makefile_vars(projio_mk.read_text(encoding="utf-8")))
    if makefile.exists():
        vars_.update(_parse_makefile_vars(makefile.read_text(encoding="utf-8")))
    if "DATALAD" in vars_:
        return _expand(vars_["DATALAD"], vars_)
    return "datalad"


def _run(args: list[str], cwd: str | None = None) -> dict[str, Any]:
    """Run a command and return structured output."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        payload: dict[str, Any] = {
            "command": " ".join(args),
            "returncode": result.returncode,
        }
        if result.stdout.strip():
            payload["stdout"] = result.stdout.strip()
        if result.stderr.strip():
            payload["stderr"] = result.stderr.strip()
        if result.returncode != 0:
            payload["error"] = f"Command exited with code {result.returncode}"
        return payload
    except subprocess.TimeoutExpired:
        return {"command": " ".join(args), "error": "Command timed out after 120s"}
    except FileNotFoundError:
        return {"command": " ".join(args), "error": f"Binary not found: {args[0]}"}


def datalad_status(recursive: bool = True) -> JsonDict:
    """Show datalad status for the project dataset.

    Args:
        recursive: Include subdatasets (default True).
    """
    root = get_project_root()
    dl = _resolve_datalad_bin()
    cmd = [dl, "status"]
    if recursive:
        cmd.append("-r")
    return json_dict(_run(cmd, cwd=str(root)))


def datalad_save(message: str = "Update", recursive: bool = True) -> JsonDict:
    """Save changes in the project dataset.

    Args:
        message: Commit message for the save.
        recursive: Include subdatasets (default True).
    """
    root = get_project_root()
    dl = _resolve_datalad_bin()
    cmd = [dl, "save", "-m", message]
    if recursive:
        cmd.append("-r")
    return json_dict(_run(cmd, cwd=str(root)))


def datalad_push(sibling: str = "github") -> JsonDict:
    """Push the project dataset to a sibling.

    Args:
        sibling: Name of the datalad sibling to push to (default "github").
    """
    root = get_project_root()
    dl = _resolve_datalad_bin()
    cmd = [dl, "push", "-r", "--to", sibling]
    return json_dict(_run(cmd, cwd=str(root)))


def datalad_pull(sibling: str = "origin") -> JsonDict:
    """Pull (update + merge) from a datalad sibling.

    Args:
        sibling: Name of the datalad sibling to pull from (default "origin").
    """
    root = get_project_root()
    dl = _resolve_datalad_bin()
    cmd = [dl, "update", "-r", "--merge", "-s", sibling]
    return json_dict(_run(cmd, cwd=str(root)))


def datalad_siblings() -> JsonDict:
    """List configured datalad siblings for the project dataset."""
    root = get_project_root()
    dl = _resolve_datalad_bin()
    cmd = [dl, "siblings"]
    return json_dict(_run(cmd, cwd=str(root)))


def git_status() -> JsonDict:
    """Per-project git state: branch, staged, unstaged, untracked files, and clean flag."""
    root = get_project_root()
    cwd = str(root)

    branch_result = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    branch = branch_result.get("stdout", "unknown")

    porcelain_result = _run(["git", "status", "--porcelain=v1"], cwd=cwd)
    if "error" in porcelain_result:
        return json_dict({**porcelain_result, "branch": branch})

    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []

    for line in porcelain_result.get("stdout", "").splitlines():
        if len(line) < 2:
            continue
        x, y, path = line[0], line[1], line[3:]
        if x == "?" and y == "?":
            untracked.append(path)
        else:
            if x != " " and x != "?":
                staged.append(f"{x} {path}")
            if y != " " and y != "?":
                unstaged.append(f"{y} {path}")

    payload: dict[str, Any] = {
        "branch": branch,
        "clean": not staged and not unstaged and not untracked,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
    }
    return json_dict(payload)
