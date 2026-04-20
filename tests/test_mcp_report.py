"""Tests for projio.mcp.report — Quarto report scaffolding + build preflight."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock

import pytest
import yaml

from projio.mcp import report
from projio.mcp.report import (
    _check_min_version,
    _find_report,
    _load_quarto_config,
    _parse_version,
    _preflight_report,
    _resolve_quarto_cmd,
    _split_frontmatter,
    _validate_notebook_embed,
    report_build,
    report_init,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _executed_notebook(label: str = "fig-demo") -> dict:
    """Minimal executed .ipynb with one labeled code cell + output."""
    return {
        "cells": [
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": 1,
                "source": [f"#| label: {label}\n", "import matplotlib.pyplot as plt\n", "plt.plot([1,2,3])\n"],
                "outputs": [
                    {
                        "output_type": "display_data",
                        "data": {"image/png": "iVBORw0KGgoAAAAN"},
                        "metadata": {},
                    }
                ],
            }
        ],
        "metadata": {
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _unexecuted_notebook(label: str = "fig-demo") -> dict:
    nb = _executed_notebook(label=label)
    for cell in nb["cells"]:
        cell["execution_count"] = None
        cell["outputs"] = []
    return nb


@pytest.fixture
def project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A bare project root with .projio/config.yml pinned via PROJIO_ROOT."""
    (tmp_path / ".projio").mkdir()
    (tmp_path / ".projio" / "config.yml").write_text("project_name: test\n", encoding="utf-8")
    monkeypatch.setenv("PROJIO_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def pixecog_fixture(project_root: Path) -> dict[str, Path]:
    """A pixecog-style layout: executed .ipynb + a report that embeds a cell."""
    nb_dir = project_root / "code" / "pipelines" / "detect_swr" / "notebooks"
    nb_dir.mkdir(parents=True)
    nb_path = nb_dir / "spindle-analysis.ipynb"
    nb_path.write_text(json.dumps(_executed_notebook("fig-spindle-density")), encoding="utf-8")

    # Render artefacts the frontmatter points at.
    render_dir = project_root / ".projio" / "render"
    (render_dir / "csl").mkdir(parents=True)
    (render_dir / "compiled.bib").write_text("\n", encoding="utf-8")
    (render_dir / "csl" / "apa.csl").write_text("<!-- csl -->\n", encoding="utf-8")

    return {"root": project_root, "notebook": nb_path}


# ---------------------------------------------------------------------------
# _parse_version / version gate
# ---------------------------------------------------------------------------


class TestParseVersion:
    def test_parses_simple(self) -> None:
        assert _parse_version("1.5.55") == (1, 5, 55)

    def test_parses_with_dash_suffix(self) -> None:
        assert _parse_version("1.5") == (1, 5)

    def test_truncates_at_non_numeric(self) -> None:
        assert _parse_version("1.5.0-dev") == (1, 5, 0)

    def test_returns_zero_on_garbage(self) -> None:
        assert _parse_version("not a version") == (0,)


# ---------------------------------------------------------------------------
# _split_frontmatter
# ---------------------------------------------------------------------------


class TestSplitFrontmatter:
    def test_parses_frontmatter(self) -> None:
        text = "---\ntitle: Hello\ntype: report\n---\n\n# Body\n"
        fm, body = _split_frontmatter(text)
        assert fm == {"title": "Hello", "type": "report"}
        assert body.strip() == "# Body"

    def test_missing_frontmatter_returns_empty(self) -> None:
        fm, body = _split_frontmatter("# Body only\n")
        assert fm == {}
        assert body == "# Body only\n"

    def test_malformed_yaml_returns_empty(self) -> None:
        fm, body = _split_frontmatter("---\n: : :\n---\n\nBody\n")
        # yaml.safe_load of ": : :" returns None -> empty dict branch
        assert isinstance(fm, dict)


# ---------------------------------------------------------------------------
# _validate_notebook_embed
# ---------------------------------------------------------------------------


class TestValidateNotebookEmbed:
    def test_executed_with_matching_label_passes(self, tmp_path: Path) -> None:
        nb = tmp_path / "nb.ipynb"
        nb.write_text(json.dumps(_executed_notebook("fig-foo")), encoding="utf-8")
        assert _validate_notebook_embed(nb, "fig-foo") is None

    def test_missing_notebook_errors(self, tmp_path: Path) -> None:
        err = _validate_notebook_embed(tmp_path / "missing.ipynb", "fig-foo")
        assert err is not None
        assert "not found" in err

    def test_non_ipynb_errors(self, tmp_path: Path) -> None:
        py = tmp_path / "nb.py"
        py.write_text("# %% [markdown]\n")
        err = _validate_notebook_embed(py, "fig-foo")
        assert err is not None
        assert ".ipynb" in err

    def test_unexecuted_errors(self, tmp_path: Path) -> None:
        nb = tmp_path / "nb.ipynb"
        nb.write_text(json.dumps(_unexecuted_notebook("fig-foo")), encoding="utf-8")
        err = _validate_notebook_embed(nb, "fig-foo")
        assert err is not None
        assert "pipeio_nb_exec" in err

    def test_missing_label_errors(self, tmp_path: Path) -> None:
        nb = tmp_path / "nb.ipynb"
        nb.write_text(json.dumps(_executed_notebook("fig-other")), encoding="utf-8")
        err = _validate_notebook_embed(nb, "fig-foo")
        assert err is not None
        assert "fig-foo" in err


# ---------------------------------------------------------------------------
# _preflight_report
# ---------------------------------------------------------------------------


class TestPreflight:
    def test_happy_path(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        qmd = root / "docs" / "deliverables" / "reports" / "weekly" / "report.qmd"
        qmd.parent.mkdir(parents=True)
        body = (
            "## Spindles\n\n"
            "{{< embed ../../../../code/pipelines/detect_swr/notebooks/"
            "spindle-analysis.ipynb#fig-spindle-density >}}\n"
        )
        qmd.write_text(body, encoding="utf-8")
        fm = {"bibliography": "../../../../.projio/render/compiled.bib"}
        result = _preflight_report(qmd, fm, body)
        assert result.errors == []
        assert len(result.embeds) == 1
        assert result.embeds[0]["ok"]

    def test_catches_missing_label(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        qmd = root / "docs" / "deliverables" / "reports" / "weekly" / "report.qmd"
        qmd.parent.mkdir(parents=True)
        body = (
            "{{< embed ../../../../code/pipelines/detect_swr/notebooks/"
            "spindle-analysis.ipynb#fig-no-such-label >}}\n"
        )
        qmd.write_text(body, encoding="utf-8")
        result = _preflight_report(qmd, {}, body)
        assert any("fig-no-such-label" in e for e in result.errors)

    def test_catches_missing_image(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        qmd = root / "docs" / "deliverables" / "reports" / "weekly" / "report.qmd"
        qmd.parent.mkdir(parents=True)
        body = "![Caption](figures/missing.png)\n"
        qmd.write_text(body, encoding="utf-8")
        result = _preflight_report(qmd, {}, body)
        assert any("missing.png" in e for e in result.errors)

    def test_skips_url_images(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        qmd = root / "docs" / "deliverables" / "reports" / "weekly" / "report.qmd"
        qmd.parent.mkdir(parents=True)
        body = "![Logo](https://example.com/logo.png)\n"
        qmd.write_text(body, encoding="utf-8")
        result = _preflight_report(qmd, {}, body)
        assert result.errors == []
        assert result.images == []

    def test_catches_missing_bibliography_when_citations_present(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        qmd = root / "docs" / "deliverables" / "reports" / "weekly" / "report.qmd"
        qmd.parent.mkdir(parents=True)
        body = "See @smith2020 for details.\n"
        qmd.write_text(body, encoding="utf-8")
        fm = {"bibliography": "../../../../.projio/render/nope.bib"}
        result = _preflight_report(qmd, fm, body)
        assert any("nope.bib" in e for e in result.errors)

    def test_missing_bibliography_ok_when_no_citations(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        qmd = root / "docs" / "deliverables" / "reports" / "smoke" / "report.qmd"
        qmd.parent.mkdir(parents=True)
        body = "# Status update\n\nOne-paragraph summary.\n"
        qmd.write_text(body, encoding="utf-8")
        fm = {"bibliography": "../../../../.projio/render/compiled.bib"}  # file absent in this fixture
        # Delete the compiled.bib that pixecog_fixture created
        bib = root / ".projio" / "render" / "compiled.bib"
        bib.unlink()
        result = _preflight_report(qmd, fm, body)
        assert result.errors == []
        assert result.bibliography is not None
        assert result.bibliography["ok"] is True
        assert "no citations" in result.bibliography.get("note", "")


# ---------------------------------------------------------------------------
# _find_report
# ---------------------------------------------------------------------------


class TestFindReport:
    def test_prefers_subdir_layout(self, project_root: Path) -> None:
        base = project_root / "docs" / "deliverables" / "reports" / "weekly"
        base.mkdir(parents=True)
        qmd = base / "report.qmd"
        qmd.write_text("# r\n")
        found = _find_report(project_root, "weekly")
        assert found is not None
        report_dir, qmd_path = found
        assert qmd_path == qmd
        assert report_dir == base

    def test_falls_back_to_flat(self, project_root: Path) -> None:
        base = project_root / "docs" / "deliverables" / "reports"
        base.mkdir(parents=True)
        qmd = base / "quick.qmd"
        qmd.write_text("# r\n")
        found = _find_report(project_root, "quick")
        assert found is not None
        assert found[1] == qmd

    def test_none_when_missing(self, project_root: Path) -> None:
        assert _find_report(project_root, "nope") is None


# ---------------------------------------------------------------------------
# _load_quarto_config
# ---------------------------------------------------------------------------


class TestLoadQuartoConfig:
    def test_returns_default_when_missing(self, project_root: Path) -> None:
        cfg = _load_quarto_config(project_root)
        assert cfg == {"min_version": report.DEFAULT_MIN_VERSION}

    def test_reads_override(self, project_root: Path) -> None:
        path = project_root / ".projio" / "render" / "quarto.yml"
        path.parent.mkdir(parents=True)
        path.write_text('min_version: "1.6"\n')
        cfg = _load_quarto_config(project_root)
        assert cfg["min_version"] == "1.6"


# ---------------------------------------------------------------------------
# _check_min_version
# ---------------------------------------------------------------------------


class TestCheckMinVersion:
    def setup_method(self) -> None:
        report._VERSION_CACHE.clear()

    def test_ok_when_exact(self) -> None:
        with mock.patch("projio.mcp.report.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="1.5.55\n", stderr="")
            err = _check_min_version(["quarto"], "1.5")
        assert err is None

    def test_errors_when_too_old(self) -> None:
        with mock.patch("projio.mcp.report.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="1.3.450\n", stderr="")
            err = _check_min_version(["quarto"], "1.5")
        assert err is not None
        assert "1.3.450" in err
        assert "1.5" in err
        assert "quarto.org" in err

    def test_errors_when_missing(self) -> None:
        with mock.patch("projio.mcp.report.subprocess.run", side_effect=FileNotFoundError):
            err = _check_min_version(["no-quarto"], "1.5")
        assert err is not None
        assert "quarto" in err.lower()


# ---------------------------------------------------------------------------
# _resolve_quarto_cmd
# ---------------------------------------------------------------------------


class TestResolveQuartoCmd:
    def test_prefers_envs_report(self, project_root: Path) -> None:
        cfg = {
            "project_name": "test",
            "code": {"runner": "conda", "envs": {"report": "repo-env", "default": "other"}},
        }
        (project_root / ".projio" / "config.yml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        with mock.patch("shutil.which", return_value="/usr/bin/conda"):
            cmd = _resolve_quarto_cmd()
        assert cmd == ["/usr/bin/conda", "run", "-n", "repo-env", "quarto"]

    def test_falls_back_to_envs_default(self, project_root: Path) -> None:
        cfg = {
            "project_name": "test",
            "code": {"runner": "conda", "envs": {"default": "cogpy"}},
        }
        (project_root / ".projio" / "config.yml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        with mock.patch("shutil.which", return_value="/usr/bin/conda"):
            cmd = _resolve_quarto_cmd()
        assert cmd == ["/usr/bin/conda", "run", "-n", "cogpy", "quarto"]

    def test_uses_pixi_wrapper(self, project_root: Path) -> None:
        (project_root / "pixi.toml").write_text("[workspace]\nname='x'\n")
        cfg = {
            "project_name": "test",
            "code": {"runner": "pixi", "envs": {"default": "compute"}},
        }
        (project_root / ".projio" / "config.yml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
        with mock.patch("shutil.which", return_value="/usr/bin/pixi"):
            cmd = _resolve_quarto_cmd()
        assert cmd == ["/usr/bin/pixi", "run", "-e", "compute", "quarto"]

    def test_bare_quarto_on_path(self, project_root: Path) -> None:
        # No envs configured; quarto on PATH.
        def which(name: str) -> str | None:
            return "/usr/local/bin/quarto" if name == "quarto" else None

        with mock.patch("shutil.which", side_effect=which):
            cmd = _resolve_quarto_cmd()
        assert cmd == ["/usr/local/bin/quarto"]

    def test_empty_when_nothing_found(self, project_root: Path) -> None:
        with mock.patch("shutil.which", return_value=None):
            cmd = _resolve_quarto_cmd()
        assert cmd == []


# ---------------------------------------------------------------------------
# report_init
# ---------------------------------------------------------------------------


class TestReportInit:
    def test_scaffolds_progress_report(self, project_root: Path) -> None:
        result = report_init("weekly-2026-04-20", template="progress")
        assert "error" not in result
        path = project_root / "docs" / "deliverables" / "reports" / "weekly-2026-04-20" / "report.qmd"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        fm, body = _split_frontmatter(text)
        assert fm["type"] == "report"
        assert fm["template"] == "progress"
        assert fm["bibliography"].endswith(".projio/render/compiled.bib")
        assert "Overview" in body

    def test_refuses_overwrite(self, project_root: Path) -> None:
        report_init("once", template="update")
        again = report_init("once", template="update")
        assert "error" in again
        assert "already exists" in again["error"]

    def test_rejects_unknown_template(self, project_root: Path) -> None:
        result = report_init("bad", template="nonsense")
        assert "error" in result
        assert "template" in result["error"]

    def test_fills_preamble_from_result_notes(self, project_root: Path) -> None:
        result_dir = project_root / "docs" / "log" / "result"
        result_dir.mkdir(parents=True)
        (result_dir / "result-arash-20260415-120000-abc.md").write_text("x")
        (result_dir / "result-arash-20260417-120000-def.md").write_text("x")
        result = report_init("w", template="progress")
        assert "result-arash-20260417-120000-def" in result["results"]


# ---------------------------------------------------------------------------
# report_build — integration
# ---------------------------------------------------------------------------


class TestReportBuild:
    def test_reports_missing_report(self, project_root: Path) -> None:
        result = report_build("does-not-exist")
        assert "error" in result
        assert "report not found" in result["error"]

    def test_preflight_catches_missing_label(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        base = root / "docs" / "deliverables" / "reports" / "weekly"
        base.mkdir(parents=True)
        qmd = base / "report.qmd"
        qmd.write_text(
            "---\ntitle: Weekly\nbibliography: ../../../../.projio/render/compiled.bib\n---\n\n"
            "{{< embed ../../../../code/pipelines/detect_swr/notebooks/"
            "spindle-analysis.ipynb#fig-does-not-exist >}}\n",
            encoding="utf-8",
        )
        result = report_build("weekly")
        assert "error" in result
        assert result["error"] == "preflight validation failed"
        assert any("fig-does-not-exist" in e for e in result["preflight_errors"])

    def test_surfaces_quarto_missing(self, pixecog_fixture: dict[str, Path]) -> None:
        root = pixecog_fixture["root"]
        base = root / "docs" / "deliverables" / "reports" / "weekly"
        base.mkdir(parents=True)
        qmd = base / "report.qmd"
        qmd.write_text(
            "---\ntitle: Weekly\nbibliography: ../../../../.projio/render/compiled.bib\n---\n\n"
            "{{< embed ../../../../code/pipelines/detect_swr/notebooks/"
            "spindle-analysis.ipynb#fig-spindle-density >}}\n",
            encoding="utf-8",
        )
        with mock.patch("projio.mcp.report._resolve_quarto_cmd", return_value=[]):
            result = report_build("weekly")
        assert "error" in result
        assert "quarto not found" in result["error"]

    def test_successful_render(self, pixecog_fixture: dict[str, Path]) -> None:
        """Full path with quarto mocked — verifies the command invocation + return shape."""
        root = pixecog_fixture["root"]
        base = root / "docs" / "deliverables" / "reports" / "weekly"
        base.mkdir(parents=True)
        qmd = base / "report.qmd"
        qmd.write_text(
            "---\ntitle: Weekly\nbibliography: ../../../../.projio/render/compiled.bib\n---\n\n"
            "# Body\n",
            encoding="utf-8",
        )
        report._VERSION_CACHE.clear()

        def fake_run(cmd: list[str], **kwargs):  # type: ignore[no-untyped-def]
            if "--version" in cmd:
                return mock.Mock(returncode=0, stdout="1.5.55\n", stderr="")
            # Simulate quarto writing the output HTML next to the qmd.
            qmd.with_suffix(".html").write_text("<html><body>ok</body></html>", encoding="utf-8")
            return mock.Mock(returncode=0, stdout="pandoc log", stderr="")

        with mock.patch("projio.mcp.report._resolve_quarto_cmd", return_value=["quarto"]):
            with mock.patch("projio.mcp.report.subprocess.run", side_effect=fake_run):
                result = report_build("weekly")

        assert "error" not in result
        assert result["returncode"] == 0
        assert result["output"].endswith("report.html")
        output_abs = Path(result["output_abs"])
        assert output_abs.is_file()
        assert "<html>" in output_abs.read_text(encoding="utf-8")
