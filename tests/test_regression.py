from __future__ import annotations

import sys
import types
from pathlib import Path

from projio import cli
from projio.init import scaffold


def test_existing_init_scaffolds_workspace(tmp_path: Path) -> None:
    scaffold(tmp_path)
    assert (tmp_path / ".projio" / "config.yml").exists()
    assert (tmp_path / "mkdocs.yml").exists()
    assert (tmp_path / "Makefile").exists()
    assert (tmp_path / "docs" / "index.md").exists()
    config_text = (tmp_path / ".projio" / "config.yml").read_text(encoding="utf-8")
    assert "project_kind: generic" in config_text


def test_init_does_not_overwrite_existing_makefile_without_force(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("CUSTOM=1\n", encoding="utf-8")
    scaffold(tmp_path)
    assert makefile.read_text(encoding="utf-8") == "CUSTOM=1\n"


def test_tool_kind_scaffolds_package_files(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="tool")
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "tests").exists()
    assert (tmp_path / "src" / tmp_path.name / "__init__.py").exists()
    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert ".PHONY: test build check" in makefile_text


def test_study_kind_scaffolds_thin_study_overlay(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="study")
    assert (tmp_path / "docs" / "study-overview.md").exists()
    assert not (tmp_path / "pyproject.toml").exists()
    config_text = (tmp_path / ".projio" / "config.yml").read_text(encoding="utf-8")
    assert "project_kind: study" in config_text
    assert "biblio:\n  enabled: false" in config_text


def test_tool_kind_does_not_overwrite_existing_pyproject_without_force(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='custom'\n", encoding="utf-8")
    scaffold(tmp_path, kind="tool")
    assert pyproject.read_text(encoding="utf-8") == "[project]\nname='custom'\n"


def test_existing_status_command_still_dispatches(monkeypatch) -> None:
    calls: list[str] = []

    def fake_print_report(root: str) -> None:
        calls.append(root)

    monkeypatch.setattr("projio.status.print_report", fake_print_report)
    cli.main(["status", "-C", "/tmp/demo"])
    assert calls == ["/tmp/demo"]


def test_config_commands_dispatch(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr("projio.config.scaffold_user_config", lambda force=False: calls.append(("init-user", force)))
    monkeypatch.setattr("projio.config.print_effective_config", lambda root: calls.append(("show", root)))

    cli.main(["config", "init-user", "--force"])
    cli.main(["config", "-C", "/tmp/demo", "show"])

    assert calls == [("init-user", True), ("show", "/tmp/demo")]


def test_init_command_dispatches_kind(monkeypatch) -> None:
    calls: list[tuple[str, str, bool]] = []

    monkeypatch.setattr("projio.init.scaffold", lambda root, kind="generic", force=False: calls.append((root, kind, force)))
    cli.main(["init", ".", "--kind", "tool", "--force"])
    assert calls == [(".", "tool", True)]


def test_existing_site_command_still_dispatches(monkeypatch) -> None:
    calls: list[tuple[str, str, bool | None]] = []

    monkeypatch.setattr("projio.site.build", lambda root, strict=False: calls.append(("build", root, strict)))
    monkeypatch.setattr("projio.site.serve", lambda root: calls.append(("serve", root, None)))
    monkeypatch.setattr("projio.site.publish", lambda root: calls.append(("publish", root, None)))

    cli.main(["site", "build", "-C", "/tmp/demo", "--strict"])
    cli.main(["site", "serve", "-C", "/tmp/demo"])
    cli.main(["site", "publish", "-C", "/tmp/demo"])

    assert calls == [
        ("build", "/tmp/demo", True),
        ("serve", "/tmp/demo", None),
        ("publish", "/tmp/demo", None),
    ]


def test_existing_mcp_command_sets_default_root(monkeypatch) -> None:
    calls: list[bool] = []

    def fake_mcp_main() -> None:
        calls.append(True)

    fake_server = types.ModuleType("projio.mcp.server")
    fake_server.main = fake_mcp_main
    monkeypatch.setitem(sys.modules, "projio.mcp.server", fake_server)
    cli.main(["mcp", "-C", "/tmp/demo"])
    assert calls == [True]
