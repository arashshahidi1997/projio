"""Preview-first command execution for helper actions."""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def render_command(cmd: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in cmd)


def run_or_preview(
    cmd: list[str],
    *,
    cwd: Path,
    yes: bool,
    extra_env: dict[str, str] | None = None,
) -> None:
    print(f"$ {render_command(cmd)}")
    if not yes:
        print("[preview] pass --yes to execute")
        return

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        sys.exit(result.returncode)
