"""The task interface: CLI-first, pixi for project tasks, legacy make kept (docs/how-to/task-running.md)."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path

from projio.init import _ensure_pixi_scaffold, _resolve_task_runner, project_commands, scaffold


def test_task_runner_defaults_to_cli_then_make_if_makefile(tmp_path: Path) -> None:
    (tmp_path / ".projio").mkdir()
    (tmp_path / ".projio" / "config.yml").write_text("code: {}\n")
    assert _resolve_task_runner(tmp_path) == "cli"
    (tmp_path / "Makefile").write_text("# legacy\n")
    assert _resolve_task_runner(tmp_path) == "make"
    (tmp_path / ".projio" / "config.yml").write_text("code:\n  task_runner: cli\n")
    assert _resolve_task_runner(tmp_path) == "cli"        # explicit wins


def test_new_project_gets_no_task_file(tmp_path: Path) -> None:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        scaffold(tmp_path, kind="generic")
    for name in ("Makefile", ".projio/projio.mk", "Taskfile.yml", ".projio/Taskfile.yml"):
        assert not (tmp_path / name).exists(), name
    text = (tmp_path / "pixi.toml").read_text()
    assert '"win-64"' in text and "go-task" not in text and "projio sync" in text


def test_project_commands_are_plain_cli(tmp_path: Path) -> None:
    (tmp_path / "docs" / "manuscript" / "paper").mkdir(parents=True)
    (tmp_path / "docs" / "manuscript" / "paper" / "manuscript.yml").write_text("title: P\n")
    (tmp_path / "docs" / "report").mkdir(parents=True)
    (tmp_path / "docs" / "report" / "master.md").write_text("# R\n")
    cmds = dict(project_commands(tmp_path))
    assert {"projio sync", "projio status", "projio site build", "projio site serve"} <= set(cmds)
    assert "notio manuscript build paper --format pdf" in cmds
    assert "notio manuscript master-build report --format pdf" in cmds
    assert not any(c.split()[1] in ("auth", "mcp", "sibling", "config") for c in cmds)   # curated


def test_projio_tasks_cli(tmp_path: Path, capsys) -> None:
    from projio.cli import main
    main(["tasks", "-C", str(tmp_path)])
    out = capsys.readouterr().out
    assert "projio sync" in out and "pixi task list" in out


def test_pixi_scaffold_only_when_absent(tmp_path: Path) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        _ensure_pixi_scaffold(tmp_path)
    (tmp_path / "pixi.toml").write_text("[workspace]\nname='keep'\n")
    with contextlib.redirect_stdout(io.StringIO()):
        _ensure_pixi_scaffold(tmp_path)
    assert (tmp_path / "pixi.toml").read_text() == "[workspace]\nname='keep'\n"


def test_pixi_scaffold_package_mode(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "foo-tools"\nversion = "0.1"\n')
    with contextlib.redirect_stdout(io.StringIO()):
        _ensure_pixi_scaffold(tmp_path)
    txt = (tmp_path / "pixi.toml").read_text()
    assert 'foo-tools = { path = ".", editable = true }' in txt
    assert "[feature.dev.tasks]" in txt and "go-task" not in txt
    assert "projio = {" not in txt                        # a package does not depend on projio


def test_sync_summary_has_the_task_key(tmp_path: Path) -> None:
    from projio.sync import sync_workspace
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        scaffold(tmp_path, kind="generic")
        res = sync_workspace(str(tmp_path), dry_run=True)
    assert res["projio_mk"]["action"] == "skipped" and "taskfile" not in res
