"""Corpus freshness, index health, and git status summary."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .init import load_projio_config


def _git_status(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "(clean)"
    except FileNotFoundError:
        return "(git not found)"


def _index_health(cfg: dict, root: Path) -> dict[str, Any]:
    idx_cfg = cfg.get("indexio") or {}
    persist_dir = idx_cfg.get("persist_dir", ".projio/index")
    persist_path = root / persist_dir
    return {
        "persist_dir": str(persist_dir),
        "exists": persist_path.exists(),
    }


def report(root: str | Path) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    cfg = load_projio_config(root)
    return {
        "project": cfg.get("project_name", root.name),
        "root": str(root),
        "git_status": _git_status(root),
        "index": _index_health(cfg, root),
        "biblio_enabled": bool((cfg.get("biblio") or {}).get("enabled", False)),
        "notio_enabled": bool((cfg.get("notio") or {}).get("enabled", False)),
    }


def print_report(root: str | Path) -> None:
    info = report(root)
    print(f"Project : {info['project']}")
    print(f"Root    : {info['root']}")
    print(f"Git     : {info['git_status']}")
    idx = info["index"]
    status = "exists" if idx["exists"] else "missing"
    print(f"Index   : {idx['persist_dir']}  [{status}]")
    print(f"biblio  : {'enabled' if info['biblio_enabled'] else 'disabled'}")
    print(f"notio   : {'enabled' if info['notio_enabled'] else 'disabled'}")
