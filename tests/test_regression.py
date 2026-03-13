from __future__ import annotations

import sys
import types
from pathlib import Path

from projio import cli
from projio.init import scaffold


def test_existing_init_scaffolds_workspace(tmp_path: Path) -> None:
    scaffold(tmp_path)
    assert (tmp_path / ".projio" / "config.yml").exists()
    assert (tmp_path / ".projio" / "projio.mk").exists()
    assert (tmp_path / "mkdocs.yml").exists()
    assert (tmp_path / "Makefile").exists()
    assert (tmp_path / ".gitignore").exists()
    assert (tmp_path / "docs" / "index.md").exists()
    config_text = (tmp_path / ".projio" / "config.yml").read_text(encoding="utf-8")
    assert "project_kind: generic" in config_text
    assert "framework: mkdocs" in config_text
    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "-include .projio/projio.mk" in makefile_text
    mk_text = (tmp_path / ".projio" / "projio.mk").read_text(encoding="utf-8")
    assert "$(DATALAD) save" in mk_text
    assert "$(DATALAD) push" in mk_text
    assert "$(PROJIO) url -C ." in mk_text
    assert "PROJIO  ?= projio" in mk_text
    gitignore_text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "# >>> projio >>>" in gitignore_text
    assert "site/" in gitignore_text


def test_init_does_not_overwrite_existing_makefile_without_force(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("CUSTOM=1\n", encoding="utf-8")
    scaffold(tmp_path)
    text = makefile.read_text(encoding="utf-8")
    assert text.startswith("CUSTOM=1")  # original content preserved
    assert "-include .projio/projio.mk" in text  # include injected


def test_include_injected_into_existing_makefile(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text("PYTHON ?= python3\n\nsave:\n\techo hi\n", encoding="utf-8")
    scaffold(tmp_path)
    text = makefile.read_text(encoding="utf-8")
    assert text.startswith("PYTHON ?= python3")
    assert "-include .projio/projio.mk" in text


def test_include_not_duplicated_on_reinit(tmp_path: Path) -> None:
    scaffold(tmp_path)
    scaffold(tmp_path)  # re-init
    text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert text.count("-include .projio/projio.mk") == 1


def test_projio_mk_always_overwritten_on_reinit(tmp_path: Path) -> None:
    scaffold(tmp_path)
    mk = tmp_path / ".projio" / "projio.mk"
    mk.write_text("# stale content\n", encoding="utf-8")
    scaffold(tmp_path)  # no --force
    text = mk.read_text(encoding="utf-8")
    assert "$(DATALAD) save" in text  # updated, not stale


def test_tool_kind_scaffolds_package_files(tmp_path: Path) -> None:
    scaffold(tmp_path, kind="tool")
    assert (tmp_path / "pyproject.toml").exists()
    assert (tmp_path / "tests").exists()
    assert (tmp_path / "src" / tmp_path.name / "__init__.py").exists()
    assert (tmp_path / ".projio" / "projio.mk").exists()
    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "-include .projio/projio.mk" in makefile_text
    assert ".PHONY: test build check publish-test publish clean" in makefile_text
    assert "$(PYTHON) -m twine upload --repository testpypi dist/*" in makefile_text
    assert "$(PYTHON) -m twine upload dist/*" in makefile_text


def test_init_vscode_flag_scaffolds_settings(tmp_path: Path) -> None:
    scaffold(tmp_path, vscode=True)
    settings_text = (tmp_path / ".vscode" / "settings.json").read_text(encoding="utf-8")
    assert "\"files.watcherExclude\"" in settings_text
    assert "\"**/site/**\": true" in settings_text


def test_init_github_pages_flag_scaffolds_workflow(tmp_path: Path) -> None:
    scaffold(tmp_path, github_pages=True)
    workflow_text = (tmp_path / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")
    assert "actions/deploy-pages@v4" in workflow_text
    assert "projio site build -C . --framework mkdocs --strict" in workflow_text
    assert "path: site" in workflow_text


def test_existing_gitignore_projio_section_is_updated_not_duplicated(tmp_path: Path) -> None:
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        "node_modules/\n\n# >>> projio >>>\nold-entry/\n# <<< projio <<<\n",
        encoding="utf-8",
    )
    scaffold(tmp_path)
    text = gitignore.read_text(encoding="utf-8")
    assert text.count("# >>> projio >>>") == 1
    assert "old-entry/" not in text
    assert "site/" in text


def test_init_detects_existing_sphinx_site(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "conf.py").write_text("project = 'demo'\n", encoding="utf-8")
    scaffold(tmp_path)
    config_text = (tmp_path / ".projio" / "config.yml").read_text(encoding="utf-8")
    assert "framework: sphinx" in config_text
    assert "output_dir: docs/_build/html" in config_text
    assert not (tmp_path / "mkdocs.yml").exists()


def test_init_github_pages_for_sphinx_uses_html_artifact(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "conf.py").write_text("project = 'demo'\n", encoding="utf-8")
    scaffold(tmp_path, github_pages=True)
    workflow_text = (tmp_path / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")
    assert "projio site build -C . --framework sphinx" in workflow_text
    assert "path: docs/_build/html" in workflow_text


def test_init_github_pages_for_vite_uses_frontend_setup(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{\"devDependencies\": {\"vite\": \"^5.0\"}}\n", encoding="utf-8")
    scaffold(tmp_path, github_pages=True)
    workflow_text = (tmp_path / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")
    assert "actions/setup-node@v4" in workflow_text
    assert "working-directory: ." in workflow_text
    assert "projio site build -C . --framework vite" in workflow_text


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


def test_existing_url_command_still_dispatches(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr("projio.url.print_urls", lambda root: calls.append(root))
    cli.main(["url", "-C", "/tmp/demo"])
    assert calls == ["/tmp/demo"]


def test_config_commands_dispatch(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr("projio.config.scaffold_user_config", lambda force=False: calls.append(("init-user", force)))
    monkeypatch.setattr("projio.config.print_effective_config", lambda root: calls.append(("show", root)))

    cli.main(["config", "init-user", "--force"])
    cli.main(["config", "-C", "/tmp/demo", "show"])

    assert calls == [("init-user", True), ("show", "/tmp/demo")]


def test_init_command_dispatches_kind(monkeypatch) -> None:
    calls: list[tuple[str, str, bool, bool, bool]] = []

    monkeypatch.setattr(
        "projio.init.scaffold",
        lambda root, kind="generic", force=False, vscode=False, github_pages=False: calls.append((root, kind, force, vscode, github_pages)),
    )
    cli.main(["init", ".", "--kind", "tool", "--force", "--vscode", "--github-pages"])
    assert calls == [(".", "tool", True, True, True)]


def test_existing_site_command_still_dispatches(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    monkeypatch.setattr("projio.site.build", lambda root, strict=False, framework=None: calls.append(("build", root, strict, framework)))
    monkeypatch.setattr("projio.site.serve", lambda root, port=None, framework=None, background=False, host=None: calls.append(("serve", root, port, framework)))
    monkeypatch.setattr("projio.site.publish", lambda root, framework=None: calls.append(("publish", root, framework)))

    cli.main(["site", "build", "-C", "/tmp/demo", "--strict"])
    cli.main(["site", "serve", "-C", "/tmp/demo"])
    cli.main(["site", "publish", "-C", "/tmp/demo"])

    assert calls == [
        ("build", "/tmp/demo", True, None),
        ("serve", "/tmp/demo", None, None),
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
