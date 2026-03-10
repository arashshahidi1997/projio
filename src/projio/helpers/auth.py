"""Authentication diagnostics for helper commands."""
from __future__ import annotations

from pathlib import Path

from ..config import load_effective_config
from .credentials import (
    github_access_protocol,
    git_remote_names,
    gitlab_site_config,
    remote_publish_depends,
)


def auth_doctor(root: str | Path) -> None:
    root_path = Path(root).expanduser().resolve()
    cfg = load_effective_config(root_path)
    remotes = git_remote_names(root_path)
    gitlab_cfg = gitlab_site_config(root_path)
    github_access = github_access_protocol(root_path)
    ria_storage = (
        (((cfg.get("helpers") or {}).get("sibling") or {}).get("ria") or {}).get("storage_url")
    )

    print(f"Project root : {root_path}")
    print(f"GitHub access : {github_access.value or '(unset)'} [{github_access.source}]")
    print(
        f"GitLab site   : {gitlab_cfg['site'].value or '(unset)'} [{gitlab_cfg['site'].source}] "
        f"url={gitlab_cfg['url'].value or '(unset)'} layout={gitlab_cfg['layout'].value or '(unset)'} "
        f"access={gitlab_cfg['access'].value or '(unset)'}"
    )
    print(f"RIA storage   : {ria_storage or '(unset in projio config)'}")
    if not remotes:
        print("Remotes       : (none)")
        return
    print(f"Remotes       : {', '.join(remotes)}")
    for remote in remotes:
        depends = remote_publish_depends(root_path, remote)
        print(f"  {remote}: publish-depends={depends.value or '(none)'} [{depends.source}]")
