"""Package-manager runner resolution: pixi (default), conda (legacy), none.

Single home for the "how do I invoke a command inside the project's
environment" logic.  projio is migrating to **pixi** as the sole environment
manager; the conda branch is retained only so un-migrated repos keep working
during the transition.  Projects with neither a pixi manifest nor conda
configuration resolve to ``"none"``: commands run bare from PATH (e.g. CLIs
installed with ``uv tool`` or ``pixi global``).

These helpers build command *token lists* (never shell strings), e.g.
``["pixi", "run", "-e", "compute", "snakemake"]`` or
``["/opt/conda/bin/conda", "run", "-n", "myenv", "snakemake"]``.  They are
imported by:

- ``projio.mcp.pipeio`` (snakemake / marimo execution) — via thin delegators
- ``projio.mcp.report`` (quarto) — via pipeio's delegators
- ``projio.render`` (pandoc)

pixi ``[tasks]`` do not use these: the environment is applied by how the
task is invoked (``pixi run [-e env] <task>``). These helpers are for code
paths where projio shells out to a compute binary directly.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


RUNNERS = ("pixi", "conda", "none")


def resolve_runner(root: str | Path | None) -> str:
    """Detect the package-manager runner for *root*: ``"pixi"``, ``"conda"`` or ``"none"``.

    Checks (in order):
    1. Explicit ``code.runner`` in the effective project config.
    2. Auto-detect ``pixi.toml`` in the project root.
    3. Legacy conda configuration (``code.conda_prefix``) → ``"conda"``.
    4. Default to ``"none"`` (bare commands on PATH).
    """
    if root is None:
        return "none"

    code: dict = {}
    try:
        from projio.config import load_effective_config

        code = (load_effective_config(root).get("code", {}) or {})
        runner = code.get("runner")
        if runner in RUNNERS:
            return runner
    except Exception:
        pass

    try:
        if (Path(root) / "pixi.toml").is_file():
            return "pixi"
    except Exception:
        pass

    if code.get("conda_prefix"):
        return "conda"

    return "none"


def conda_run_cmd(env_name: str, cmd_name: str) -> list[str]:
    """Build a ``conda run -n <env> <cmd>`` token list.

    Finds the conda binary on PATH, then relative to ``sys.prefix``.
    Returns bare ``[cmd_name]`` if conda cannot be found.
    """
    conda_bin = shutil.which("conda")
    if conda_bin:
        return [conda_bin, "run", "-n", env_name, cmd_name]

    # Fallback: check relative to sys.prefix (works inside a conda env)
    for rel in ("condabin/conda", "bin/conda"):
        candidate = Path(sys.prefix).parent.parent / rel
        if candidate.is_file():
            return [str(candidate), "run", "-n", env_name, cmd_name]

    return [cmd_name]


def pixi_run_cmd(cmd_name: str, env_name: str = "") -> list[str]:
    """Build a ``pixi run [-e <env>] <cmd>`` token list.

    Args:
        cmd_name: Command to run inside the pixi environment.
        env_name: Pixi environment/feature name (omit for the default env).

    Returns bare ``[cmd_name]`` if pixi cannot be found.
    """
    pixi_bin = shutil.which("pixi")
    if not pixi_bin:
        return [cmd_name]

    tokens = [pixi_bin, "run"]
    if env_name:
        tokens.extend(["-e", env_name])
    tokens.append(cmd_name)
    return tokens


def runner_cmd(runner: str, env_name: str, cmd_name: str) -> list[str]:
    """Build a command for *cmd_name* under an already-resolved *runner*.

    - ``pixi``: ``pixi run [-e <env>] <cmd>``
    - ``conda``: ``conda run -n <env> <cmd>`` (bare ``<cmd>`` without an env)
    - ``none``: bare ``<cmd>``; a named env is routed through pixi, the
      preferred manager (set ``code.runner: conda`` to use conda envs).
    """
    if runner == "conda":
        return conda_run_cmd(env_name, cmd_name) if env_name else [cmd_name]
    if runner == "pixi" or env_name:
        return pixi_run_cmd(cmd_name, env_name)
    return [cmd_name]


def run_cmd(root: str | Path | None, env_name: str, cmd_name: str) -> list[str]:
    """Build a runner command for *cmd_name*, resolving the runner from *root*."""
    return runner_cmd(resolve_runner(root), env_name, cmd_name)
