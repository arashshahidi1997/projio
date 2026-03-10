"""MkDocs build/serve/publish wrappers."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def build(root: str | Path, *, strict: bool = False) -> None:
    root = Path(root).expanduser().resolve()
    cmd = [sys.executable, "-m", "mkdocs", "build"]
    if strict:
        cmd.append("--strict")
    _run(cmd, cwd=root)


def serve(root: str | Path) -> None:
    root = Path(root).expanduser().resolve()
    _run([sys.executable, "-m", "mkdocs", "serve"], cwd=root)


def publish(root: str | Path) -> None:
    root = Path(root).expanduser().resolve()
    _run([sys.executable, "-m", "mkdocs", "gh-deploy", "--force"], cwd=root)
