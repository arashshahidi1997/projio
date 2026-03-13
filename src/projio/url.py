"""Print normalized remote and Pages URLs for the current repository."""
from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse

from .helpers.credentials import git_remote_names


def _remote_get_url(root: Path, remote: str) -> str | None:
    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _normalize_repo_url(raw: str) -> str:
    value = raw.strip()
    if value.startswith("git@"):
        host_path = value[4:]
        host, _, repo_path = host_path.partition(":")
        return f"https://{host}/{repo_path.removesuffix('.git')}"
    if value.startswith("ssh://git@"):
        parsed = urlparse(value)
        host = parsed.hostname or ""
        path = parsed.path.lstrip("/").removesuffix(".git")
        return f"https://{host}/{path}"
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        path = parsed.path.removesuffix(".git")
        return parsed._replace(path=path).geturl()
    return value


def _derive_pages_url(repo_url: str) -> str | None:
    parsed = urlparse(repo_url)
    host = parsed.hostname or ""
    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) < 2:
        return None
    owner = path_parts[-2]
    repo = path_parts[-1]
    if host == "github.com":
        return f"https://{owner}.github.io/{repo}/"
    if host == "gitlab.com":
        return f"https://{owner}.gitlab.io/{repo}/"
    return None


def print_urls(root: str | Path) -> None:
    root_path = Path(root).expanduser().resolve()
    remotes = git_remote_names(root_path)
    if not remotes:
        print("No git remotes configured.")
        return
    for remote in remotes:
        raw = _remote_get_url(root_path, remote)
        if raw is None:
            print(f"{remote}: (unavailable)")
            continue
        repo_url = _normalize_repo_url(raw)
        print(f"{remote}: {repo_url}")
        pages_url = _derive_pages_url(repo_url)
        if pages_url is not None:
            print(f"{remote} pages: {pages_url}")
