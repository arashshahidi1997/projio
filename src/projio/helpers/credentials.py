"""Inspect DataLad and Git configuration used by helper commands."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConfigValue:
    value: str | None
    source: str


def _git_config_get(cwd: Path, key: str, *, global_only: bool = False) -> ConfigValue:
    cmd = ["git", "config"]
    if global_only:
        cmd.append("--global")
    cmd.extend(["--get", key])
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return ConfigValue(result.stdout.strip() or None, "global" if global_only else "local")
    if not global_only:
        return _git_config_get(cwd, key, global_only=True)
    return ConfigValue(None, "unset")


def git_config_get(cwd: Path, key: str) -> ConfigValue:
    return _git_config_get(cwd, key)


def git_remote_names(cwd: Path) -> list[str]:
    result = subprocess.run(
        ["git", "remote"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def remote_publish_depends(cwd: Path, remote: str) -> ConfigValue:
    return git_config_get(cwd, f"remote.{remote}.datalad-publish-depends")


def gitlab_site_name(cwd: Path, explicit: str | None = None) -> ConfigValue:
    if explicit:
        return ConfigValue(explicit, "cli")
    return git_config_get(cwd, "datalad.gitlab-default-site")


def gitlab_site_config(cwd: Path, explicit: str | None = None) -> dict[str, ConfigValue]:
    site = gitlab_site_name(cwd, explicit=explicit)
    payload = {"site": site}
    if not site.value:
        for field in ("url", "layout", "project", "access"):
            payload[field] = ConfigValue(None, "unset")
        return payload

    for field in ("url", "layout", "project", "access"):
        payload[field] = git_config_get(cwd, f"datalad.gitlab-{site.value}-{field}")
    return payload


def github_access_protocol(cwd: Path) -> ConfigValue:
    return git_config_get(cwd, "datalad.github.access-protocol")
