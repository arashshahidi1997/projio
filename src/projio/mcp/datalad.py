"""MCP tools: datalad save, status, push, pull for projio-managed projects."""
from __future__ import annotations

import shlex
import subprocess
from typing import Any

from .common import JsonDict, get_project_root, json_dict, resolve_makefile_vars
from .context import _expand


def _conda_wrap(binary: str) -> list[str] | None:
    """If *binary* lives inside a conda env, return ``conda run -n <env> <name>``.

    Returns ``None`` when the binary is not inside a recognisable conda env.
    """
    import re as _re
    m = _re.search(r"/envs/([^/]+)/bin/([^/]+)$", binary)
    if not m:
        return None
    env_name = m.group(1)
    cmd_name = m.group(2)
    # Find the conda binary relative to the envs dir
    envs_dir = binary[: m.start() + len("/envs/") - len("/envs/")]
    for candidate in ("condabin/conda", "bin/conda"):
        conda_bin = f"{envs_dir}/{candidate}"
        from pathlib import Path
        if Path(conda_bin).is_file():
            return [conda_bin, "run", "-n", env_name, cmd_name]
    return None


def _resolve_datalad_cmd() -> list[str]:
    """Resolve the datalad command from Makefile/projio.mk variables.

    Returns a list of command tokens (e.g. ``["datalad"]`` or
    ``["/path/to/conda", "run", "-n", "labpy", "datalad"]``).

    When the resolved binary lives inside a conda environment, it is
    automatically wrapped with ``conda run -n <env>`` so that the full
    environment (including git-annex on PATH) is available.
    """
    vars_ = resolve_makefile_vars()
    if "DATALAD" in vars_:
        expanded = _expand(vars_["DATALAD"], vars_)
        tokens = shlex.split(expanded)
        # If it's already a multi-word command (e.g. conda run ...), use as-is
        if len(tokens) > 1:
            return tokens
        # Single binary path — check if it needs conda wrapping
        wrapped = _conda_wrap(tokens[0])
        if wrapped:
            return wrapped
        return tokens
    return ["datalad"]


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


def _resolve_dataset(root: Path, dataset: str | None) -> tuple[list[str], str]:
    """Return ``(-d, path)`` args and the cwd for a datalad command.

    When *dataset* is given (e.g. ``"packages/pipeio"``), the command targets
    that subdataset.  Otherwise the project root is used.
    """
    from pathlib import Path as _P
    if dataset:
        ds_path = (root / dataset).resolve()
        return ["-d", str(ds_path)], str(ds_path)
    return [], str(root)


def datalad_status(recursive: bool = True, dataset: str = "") -> JsonDict:
    """Show datalad status for the project dataset or a subdataset.

    Args:
        recursive: Include subdatasets (default True).
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
    """
    root = get_project_root()
    dl = _resolve_datalad_cmd()
    ds_args, cwd = _resolve_dataset(root, dataset or None)
    cmd = [*dl, "status", *ds_args]
    if recursive:
        cmd.append("-r")
    return json_dict(_run(cmd, cwd=cwd))


def datalad_save(message: str = "Update", recursive: bool = True, dataset: str = "", path: str = "") -> JsonDict:
    """Save changes in the project dataset or a subdataset.

    Args:
        message: Commit message for the save.
        recursive: Include subdatasets (default True).
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
        path: Specific path(s) to save (space-separated). Empty = save all changes.
    """
    root = get_project_root()
    dl = _resolve_datalad_cmd()
    ds_args, cwd = _resolve_dataset(root, dataset or None)
    cmd = [*dl, "save", *ds_args, "-m", message]
    if recursive:
        cmd.append("-r")
    if path:
        cmd.extend(path.split())
    return json_dict(_run(cmd, cwd=cwd))


def datalad_push(sibling: str = "github", dataset: str = "") -> JsonDict:
    """Push the project dataset (or a subdataset) to a sibling.

    Args:
        sibling: Name of the datalad sibling to push to (default "github").
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
    """
    root = get_project_root()
    dl = _resolve_datalad_cmd()
    ds_args, cwd = _resolve_dataset(root, dataset or None)
    cmd = [*dl, "push", *ds_args, "-r", "--to", sibling]
    return json_dict(_run(cmd, cwd=cwd))


def datalad_pull(sibling: str = "origin", dataset: str = "") -> JsonDict:
    """Pull (update + merge) from a datalad sibling.

    Args:
        sibling: Name of the datalad sibling to pull from (default "origin").
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
    """
    root = get_project_root()
    dl = _resolve_datalad_cmd()
    ds_args, cwd = _resolve_dataset(root, dataset or None)
    cmd = [*dl, "update", *ds_args, "-r", "--merge", "-s", sibling]
    return json_dict(_run(cmd, cwd=cwd))


def datalad_siblings(dataset: str = "") -> JsonDict:
    """List configured datalad siblings for the project dataset or a subdataset.

    Args:
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
    """
    root = get_project_root()
    dl = _resolve_datalad_cmd()
    ds_args, cwd = _resolve_dataset(root, dataset or None)
    cmd = [*dl, "siblings", *ds_args]
    return json_dict(_run(cmd, cwd=cwd))


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
