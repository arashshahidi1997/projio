from __future__ import annotations

import os
from pathlib import Path

import yaml

from projio.helpers.auth import auth_doctor
from projio.helpers.credentials import (
    git_config_get,
    git_remote_names,
    gitlab_site_config,
    remote_publish_depends,
)
from projio.helpers.docs import mkdocs_init
from projio.helpers.runner import render_command, run_or_preview
from projio.helpers.siblings import (
    plan_sibling_github,
    plan_sibling_gitlab,
    plan_sibling_ria,
)
from projio.url import print_urls


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def _make_project(tmp_path: Path, payload: dict) -> Path:
    root = tmp_path / "repo"
    _write_yaml(root / ".projio" / "config.yml", payload)
    return root


def test_plan_github_command_uses_datalad_access_protocol_and_configured_credential(tmp_path: Path, monkeypatch) -> None:
    root = _make_project(
        tmp_path,
        {
            "project_name": "demo",
            "helpers": {"sibling": {"github": {"sibling": "github", "credential": "github", "project_template": "lab/{project_name}"}}},
        },
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(
        "projio.helpers.siblings.github_access_protocol",
        lambda cwd: type("Value", (), {"value": "ssh"})(),
    )
    cwd, cmd, env = plan_sibling_github(root=root)
    assert cwd == root.resolve()
    assert cmd == [
        "datalad",
        "create-sibling-github",
        "--credential",
        "github",
        "--access-protocol",
        "ssh",
        "-s",
        "github",
        "lab/demo",
    ]
    assert env == {}


def test_plan_gitlab_command_reads_site_defaults_and_configured_credential(tmp_path: Path, monkeypatch) -> None:
    root = _make_project(
        tmp_path,
        {
            "project_name": "demo",
            "helpers": {"sibling": {"gitlab": {"sibling": "gitlab", "credential": "gitlab-lrz", "project_template": "group/{project_name}"}}},
        },
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(
        "projio.helpers.siblings.gitlab_site_config",
        lambda cwd, explicit=None: {
            "site": type("Value", (), {"value": explicit or "lrz"})(),
            "layout": type("Value", (), {"value": "flat"})(),
            "access": type("Value", (), {"value": "ssh"})(),
            "url": type("Value", (), {"value": "https://gitlab.lrz.de"})(),
            "project": type("Value", (), {"value": None})(),
        },
    )
    cwd, cmd, env = plan_sibling_gitlab(root=root)
    assert cwd == root.resolve()
    assert cmd == [
        "datalad",
        "create-sibling-gitlab",
        "--site",
        "lrz",
        "--layout",
        "flat",
        "--project",
        "group/demo",
        "--access",
        "ssh",
        "-s",
        "gitlab",
        "--credential",
        "gitlab-lrz",
    ]
    assert env == {}


def test_plan_ria_command_uses_user_default_storage_and_project_alias(tmp_path: Path, monkeypatch) -> None:
    root = _make_project(
        tmp_path,
        {
            "project_name": "demo",
            "helpers": {"sibling": {"ria": {"sibling": "origin", "alias_strategy": "basename"}}},
        },
    )
    user_cfg = tmp_path / "xdg" / "projio" / "config.yml"
    _write_yaml(user_cfg, {"helpers": {"sibling": {"ria": {"storage_url": "ria+file:///tmp/store", "shared": "group"}}}})
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    _, cmd, _ = plan_sibling_ria(root=root)
    assert cmd == [
        "datalad",
        "create-sibling-ria",
        "-s",
        "origin",
        "--alias",
        "repo",
        "--shared",
        "group",
        "ria+file:///tmp/store",
    ]


def test_git_config_helpers_read_local_and_global_values(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False, env=None):
        calls.append(cmd)
        class Result:
            returncode = 1
            stdout = ""
        if cmd == ["git", "config", "--get", "datalad.gitlab-default-site"]:
            Result.returncode = 1
        if cmd == ["git", "config", "--global", "--get", "datalad.gitlab-default-site"]:
            Result.returncode = 0
            Result.stdout = "lrz\n"
        return Result()

    monkeypatch.setattr("projio.helpers.credentials.subprocess.run", fake_run)
    value = git_config_get(tmp_path, "datalad.gitlab-default-site")
    assert value.value == "lrz"
    assert value.source == "global"
    assert calls[0] == ["git", "config", "--get", "datalad.gitlab-default-site"]


def test_gitlab_site_config_uses_default_site_lookup(tmp_path: Path, monkeypatch) -> None:
    def fake_git_config_get(cwd: Path, key: str):
        mapping = {
            "datalad.gitlab-default-site": ("lrz", "global"),
            "datalad.gitlab-lrz-url": ("https://gitlab.lrz.de", "global"),
            "datalad.gitlab-lrz-layout": ("flat", "global"),
            "datalad.gitlab-lrz-project": (None, "unset"),
            "datalad.gitlab-lrz-access": ("ssh", "global"),
        }
        value, source = mapping[key]
        return type("Value", (), {"value": value, "source": source})()

    monkeypatch.setattr("projio.helpers.credentials.git_config_get", fake_git_config_get)
    cfg = gitlab_site_config(tmp_path)
    assert cfg["site"].value == "lrz"
    assert cfg["layout"].value == "flat"
    assert cfg["access"].value == "ssh"


def test_remote_helpers_report_remotes_and_publish_depends(tmp_path: Path, monkeypatch) -> None:
    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False, env=None):
        class Result:
            returncode = 0
            stdout = ""
        if cmd == ["git", "remote"]:
            Result.stdout = "github\ngitlab\n"
        elif cmd == ["git", "config", "--get", "remote.github.datalad-publish-depends"]:
            Result.stdout = "ria-storage\n"
        elif cmd == ["git", "config", "--get", "remote.gitlab.datalad-publish-depends"]:
            Result.returncode = 1
        elif cmd == ["git", "config", "--global", "--get", "remote.gitlab.datalad-publish-depends"]:
            Result.returncode = 1
        return Result()

    monkeypatch.setattr("projio.helpers.credentials.subprocess.run", fake_run)
    assert git_remote_names(tmp_path) == ["github", "gitlab"]
    depends = remote_publish_depends(tmp_path, "github")
    assert depends.value == "ria-storage"


def test_auth_doctor_reports_datalad_state(tmp_path: Path, monkeypatch, capsys) -> None:
    root = _make_project(
        tmp_path,
        {"project_name": "demo", "helpers": {"sibling": {"ria": {"storage_url": "ria+file:///tmp/store"}}}},
    )
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(
        "projio.helpers.auth.github_access_protocol",
        lambda cwd: type("Value", (), {"value": "ssh", "source": "global"})(),
    )
    monkeypatch.setattr(
        "projio.helpers.auth.gitlab_site_config",
        lambda cwd: {
            "site": type("Value", (), {"value": "lrz", "source": "global"})(),
            "url": type("Value", (), {"value": "https://gitlab.lrz.de", "source": "global"})(),
            "layout": type("Value", (), {"value": "flat", "source": "global"})(),
            "access": type("Value", (), {"value": "ssh", "source": "global"})(),
            "project": type("Value", (), {"value": None, "source": "unset"})(),
        },
    )
    monkeypatch.setattr("projio.helpers.auth.git_remote_names", lambda cwd: ["github"])
    monkeypatch.setattr(
        "projio.helpers.auth.remote_publish_depends",
        lambda cwd, remote: type("Value", (), {"value": "ria-storage", "source": "local"})(),
    )
    auth_doctor(root)
    out = capsys.readouterr().out
    assert "GitHub access : ssh [global]" in out
    assert "GitLab site   : lrz [global]" in out
    assert "Remotes       : github" in out
    assert "publish-depends=ria-storage [local]" in out


def test_run_or_preview_prints_preview_without_running(tmp_path: Path, capsys) -> None:
    run_or_preview(["echo", "hello"], cwd=tmp_path, yes=False)
    out = capsys.readouterr().out
    assert "$ echo hello" in out
    assert "[preview] pass --yes to execute" in out


def test_run_or_preview_executes_subprocess(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[list[str], str, dict[str, str] | None]] = []

    def fake_run(cmd, cwd, env=None):
        calls.append((cmd, str(cwd), env))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr("projio.helpers.runner.subprocess.run", fake_run)
    run_or_preview(["echo", "hello"], cwd=tmp_path, yes=True, extra_env={"TOKEN": "x"})
    assert calls
    assert calls[0][0] == ["echo", "hello"]
    assert calls[0][1] == str(tmp_path)
    assert calls[0][2]["TOKEN"] == "x"
    assert calls[0][2]["PATH"] == os.environ["PATH"]


def test_mkdocs_init_scaffolds_files(tmp_path: Path) -> None:
    mkdocs_init(tmp_path)
    assert (tmp_path / "mkdocs.yml").exists()
    assert (tmp_path / "docs" / "index.md").exists()
    assert render_command(["datalad", "create-sibling-ria", "-s", "origin"]) == "datalad create-sibling-ria -s origin"


def test_print_urls_normalizes_remote_urls_and_pages(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr("projio.url.git_remote_names", lambda cwd: ["origin", "gitlab"])

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False, env=None):
        class Result:
            returncode = 0
            stdout = ""

        if cmd == ["git", "remote", "get-url", "origin"]:
            Result.stdout = "git@github.com:octo/demo.git\n"
        elif cmd == ["git", "remote", "get-url", "gitlab"]:
            Result.stdout = "https://gitlab.com/lab/demo.git\n"
        else:
            Result.returncode = 1
        return Result()

    monkeypatch.setattr("projio.url.subprocess.run", fake_run)
    print_urls(tmp_path)
    out = capsys.readouterr().out
    assert "origin: https://github.com/octo/demo" in out
    assert "origin pages: https://octo.github.io/demo/" in out
    assert "gitlab: https://gitlab.com/lab/demo" in out
    assert "gitlab pages: https://lab.gitlab.io/demo/" in out
