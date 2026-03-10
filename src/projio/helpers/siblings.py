"""Datalad sibling helper commands."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import load_effective_config
from .common import helper_defaults, project_name
from .credentials import github_access_protocol, gitlab_site_config
from .runner import run_or_preview


def _alias_from_strategy(root: Path, cfg: dict[str, Any], fallback: str) -> str:
    alias_strategy = cfg.get("alias_strategy")
    if alias_strategy == "basename":
        return root.name
    return str(cfg.get("alias") or fallback)


def _project_slug(root_path: Path, effective_cfg: dict[str, Any], cfg: dict[str, Any], explicit: str | None) -> str:
    if explicit:
        return explicit
    template = cfg.get("project_template")
    name = project_name(root_path, effective_cfg)
    if isinstance(template, str) and template:
        return template.format(project_name=name, dataset_name=root_path.name)
    return name


def _credential_name(cfg: dict[str, Any], explicit: str | None) -> str | None:
    if explicit:
        return explicit
    value = cfg.get("credential")
    if isinstance(value, str) and value.strip():
        return value
    return None


def plan_sibling_github(
    *,
    root: str | Path,
    sibling: str | None = None,
    project: str | None = None,
    credential: str | None = None,
    access_protocol: str | None = None,
) -> tuple[Path, list[str], dict[str, str]]:
    root_path = Path(root).expanduser().resolve()
    effective_cfg = load_effective_config(root_path)
    _, _, cfg = helper_defaults(root_path, "helpers", "sibling", "github")
    repo_name = _project_slug(root_path, effective_cfg, cfg, project)
    sibling_name = sibling or str(cfg.get("sibling") or "github")
    access = access_protocol or github_access_protocol(root_path).value or "ssh"
    credential_name = _credential_name(cfg, credential)
    cmd = ["datalad", "create-sibling-github"]
    if credential_name:
        cmd.extend(["--credential", credential_name])
    cmd.extend(["--access-protocol", access, "-s", sibling_name, repo_name])
    return root_path, cmd, {}


def sibling_github(
    *,
    root: str | Path,
    sibling: str | None = None,
    project: str | None = None,
    credential: str | None = None,
    access_protocol: str | None = None,
    yes: bool = False,
) -> None:
    cwd, cmd, env = plan_sibling_github(
        root=root,
        sibling=sibling,
        project=project,
        credential=credential,
        access_protocol=access_protocol,
    )
    run_or_preview(cmd, cwd=cwd, yes=yes, extra_env=env)


def plan_sibling_gitlab(
    *,
    root: str | Path,
    sibling: str | None = None,
    project: str | None = None,
    site: str | None = None,
    layout: str | None = None,
    access: str | None = None,
    credential: str | None = None,
) -> tuple[Path, list[str], dict[str, str]]:
    root_path = Path(root).expanduser().resolve()
    effective_cfg = load_effective_config(root_path)
    _, _, cfg = helper_defaults(root_path, "helpers", "sibling", "gitlab")
    site_cfg = gitlab_site_config(root_path, explicit=site)
    project_slug = _project_slug(root_path, effective_cfg, cfg, project)
    sibling_name = sibling or str(cfg.get("sibling") or "gitlab")
    credential_name = _credential_name(cfg, credential)
    site_name = site_cfg["site"].value
    layout_name = layout or site_cfg["layout"].value
    access_name = access or site_cfg["access"].value
    cmd = ["datalad", "create-sibling-gitlab"]
    if site_name:
        cmd.extend(["--site", site_name])
    if layout_name:
        cmd.extend(["--layout", layout_name])
    cmd.extend(["--project", project_slug])
    if access_name:
        cmd.extend(["--access", access_name])
    cmd.extend(["-s", sibling_name])
    if credential_name:
        cmd.extend(["--credential", credential_name])
    return root_path, cmd, {}


def sibling_gitlab(
    *,
    root: str | Path,
    sibling: str | None = None,
    project: str | None = None,
    site: str | None = None,
    layout: str | None = None,
    access: str | None = None,
    credential: str | None = None,
    yes: bool = False,
) -> None:
    cwd, cmd, env = plan_sibling_gitlab(
        root=root,
        sibling=sibling,
        project=project,
        site=site,
        layout=layout,
        access=access,
        credential=credential,
    )
    run_or_preview(cmd, cwd=cwd, yes=yes, extra_env=env)


def plan_sibling_ria(
    *,
    root: str | Path,
    sibling: str | None = None,
    alias: str | None = None,
    storage_url: str | None = None,
    shared: str | None = None,
) -> tuple[Path, list[str], dict[str, str]]:
    root_path = Path(root).expanduser().resolve()
    _, _, cfg = helper_defaults(root_path, "helpers", "sibling", "ria")
    sibling_name = sibling or str(cfg.get("sibling") or "origin")
    alias_name = alias or _alias_from_strategy(root_path, cfg, root_path.name)
    storage = storage_url or str(cfg.get("storage_url") or "")
    if not storage:
        raise SystemExit("Missing RIA storage URL. Set helpers.sibling.ria.storage_url or pass --storage-url.")
    shared_name = shared or str(cfg.get("shared") or "group")
    cmd = [
        "datalad",
        "create-sibling-ria",
        "-s",
        sibling_name,
        "--alias",
        alias_name,
        "--shared",
        shared_name,
        storage,
    ]
    return root_path, cmd, {}


def sibling_ria(
    *,
    root: str | Path,
    sibling: str | None = None,
    alias: str | None = None,
    storage_url: str | None = None,
    shared: str | None = None,
    yes: bool = False,
) -> None:
    cwd, cmd, env = plan_sibling_ria(
        root=root,
        sibling=sibling,
        alias=alias,
        storage_url=storage_url,
        shared=shared,
    )
    run_or_preview(cmd, cwd=cwd, yes=yes, extra_env=env)
