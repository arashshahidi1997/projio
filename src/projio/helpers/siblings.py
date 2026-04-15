"""Datalad sibling helper commands."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from ..config import load_effective_config
from .common import helper_defaults, project_name
from .credentials import github_access_protocol, gitlab_site_config
from .runner import run_or_preview


def _alias_from_strategy(
    root: Path,
    cfg: dict[str, Any],
    fallback: str,
    *,
    proj_name: str | None = None,
) -> str:
    template = cfg.get("alias_template")
    if isinstance(template, str) and template:
        return template.format(
            project_name=proj_name or root.name,
            dataset_name=root.name,
        )
    alias_strategy = cfg.get("alias_strategy")
    if alias_strategy == "basename":
        return root.name
    return str(cfg.get("alias") or fallback)


def _dataset_id(root: Path) -> str:
    cfg = root / ".datalad" / "config"
    if not cfg.exists():
        return ""
    try:
        out = subprocess.run(
            ["git", "config", "-f", str(cfg), "datalad.dataset.id"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    return out.stdout.strip()


def _ria_store_path(storage_url: str) -> Path | None:
    if storage_url.startswith("ria+file://"):
        return Path(storage_url.removeprefix("ria+file://"))
    return None


def _check_ria_alias_collision(
    root: Path,
    storage_url: str,
    alias_name: str,
    *,
    allow_overwrite: bool = False,
) -> None:
    """Abort if *alias_name* in the RIA store already points at a different dataset.

    Only ria+file:// stores are checked locally. For other schemes we emit a warning
    and proceed — the user is responsible for verifying remotely.
    """
    store_path = _ria_store_path(storage_url)
    if store_path is None:
        print(
            f"[WARN] alias collision check only supported for ria+file://; "
            f"got {storage_url}. Proceeding without preflight."
        )
        return

    alias_link = store_path / "alias" / alias_name
    if not alias_link.is_symlink() and not alias_link.exists():
        return

    try:
        target = os.readlink(alias_link)
    except OSError as exc:
        raise SystemExit(
            f"Could not read alias symlink {alias_link}: {exc}"
        ) from exc

    parts = [p for p in target.split("/") if p and p != ".."]
    target_ds_id = "".join(parts[-2:]) if len(parts) >= 2 else target

    local_ds_id = _dataset_id(root)
    if local_ds_id and target_ds_id == local_ds_id:
        return  # idempotent — same dataset, safe

    if allow_overwrite:
        print(
            f"[WARN] alias '{alias_name}' currently bound to {target_ds_id}; "
            f"overwriting (allow_alias_overwrite=True)"
        )
        return

    raise SystemExit(
        f"[ABORT] alias '{alias_name}' in {store_path}/alias/ already bound to "
        f"dataset {target_ds_id}. Local dataset id is {local_ds_id or '(unknown)'}. "
        f"Pick a different project_name, remove the stale alias, or pass "
        f"--force-alias / set helpers.sibling.ria.allow_alias_overwrite=true."
    )


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
    force_alias: bool = False,
) -> tuple[Path, list[str], dict[str, str]]:
    root_path = Path(root).expanduser().resolve()
    effective_cfg = load_effective_config(root_path)
    _, _, cfg = helper_defaults(root_path, "helpers", "sibling", "ria")
    sibling_name = sibling or str(cfg.get("sibling") or "origin")
    proj_name = project_name(root_path, effective_cfg)
    alias_name = alias or _alias_from_strategy(
        root_path, cfg, root_path.name, proj_name=proj_name
    )
    storage = storage_url or str(cfg.get("storage_url") or "")
    if not storage:
        raise SystemExit(
            "Missing RIA storage URL. "
            "Set helpers.sibling.ria.storage_url or pass --storage-url."
        )
    shared_name = shared or str(cfg.get("shared") or "group")
    allow_overwrite = bool(force_alias or cfg.get("allow_alias_overwrite"))
    _check_ria_alias_collision(
        root_path, storage, alias_name, allow_overwrite=allow_overwrite
    )
    print(f"[plan] ria sibling='{sibling_name}' alias='{alias_name}' store='{storage}'")
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
    force_alias: bool = False,
    yes: bool = False,
) -> None:
    cwd, cmd, env = plan_sibling_ria(
        root=root,
        sibling=sibling,
        alias=alias,
        storage_url=storage_url,
        shared=shared,
        force_alias=force_alias,
    )
    run_or_preview(cmd, cwd=cwd, yes=yes, extra_env=env)
