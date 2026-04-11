"""Tests for projio.mcp.pipeio — conda resolution and snakemake command helpers."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.pipeio import (
    _conda_run_cmd,
    _pipeio_available,
    _resolve_snakemake_cmd,
    _unavailable,
)


# ---------------------------------------------------------------------------
# _conda_run_cmd
# ---------------------------------------------------------------------------


class TestCondaRunCmd:
    def test_uses_conda_on_path(self) -> None:
        with mock.patch("shutil.which", return_value="/usr/bin/conda"):
            result = _conda_run_cmd("myenv", "snakemake")
        assert result == ["/usr/bin/conda", "run", "-n", "myenv", "snakemake"]

    def test_returns_bare_cmd_when_conda_not_found(self, monkeypatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda x: None)
        # Also mock sys.prefix so the fallback path doesn't find conda
        with mock.patch.object(
            Path,
            "is_file",
            return_value=False,
        ):
            result = _conda_run_cmd("myenv", "snakemake")
        assert result == ["snakemake"]

    def test_includes_env_name_and_cmd(self) -> None:
        with mock.patch("shutil.which", return_value="/opt/conda/bin/conda"):
            result = _conda_run_cmd("cogpy", "python")
        assert "cogpy" in result
        assert "python" in result
        assert result[0] == "/opt/conda/bin/conda"
        assert result[1] == "run"
        assert result[2] == "-n"

    def test_fallback_to_sys_prefix(self, tmp_path: Path, monkeypatch) -> None:
        # Simulate conda not on PATH but found relative to sys.prefix
        conda_path = tmp_path / "condabin" / "conda"
        conda_path.parent.mkdir(parents=True)
        conda_path.write_text("#!/bin/sh")
        conda_path.chmod(0o755)

        monkeypatch.setattr(shutil, "which", lambda x: None)
        # sys.prefix.parent.parent / condabin/conda → tmp_path
        fake_prefix = tmp_path / "envs" / "myenv"
        fake_prefix.mkdir(parents=True)
        with mock.patch.object(sys, "prefix", str(fake_prefix)):
            result = _conda_run_cmd("cogpy", "snakemake")
        assert str(conda_path) in result
        assert "cogpy" in result


# ---------------------------------------------------------------------------
# _resolve_snakemake_cmd
# ---------------------------------------------------------------------------


class TestResolveSnakemakeCmd:
    def test_explicit_conda_env_takes_priority(self) -> None:
        with mock.patch("shutil.which", return_value="/usr/bin/conda"):
            result = _resolve_snakemake_cmd(use_conda="myenv")
        assert result == ["/usr/bin/conda", "run", "-n", "myenv", "snakemake"]

    def test_uses_makefile_snakemake_variable(self) -> None:
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={"SNAKEMAKE": "snakemake"},
        ), mock.patch(
            "projio.mcp.pipeio._expand",
            return_value="snakemake",
        ), mock.patch(
            "projio.mcp.datalad._conda_wrap",
            return_value=None,
        ):
            result = _resolve_snakemake_cmd()
        assert "snakemake" in result

    def test_finds_snakemake_on_path(self) -> None:
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "shutil.which",
            return_value="/usr/bin/snakemake",
        ), mock.patch(
            "projio.mcp.datalad._conda_wrap",
            return_value=None,
        ):
            result = _resolve_snakemake_cmd()
        assert result == ["/usr/bin/snakemake"]

    def test_falls_back_to_bare_snakemake(self, monkeypatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda x: None)
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._conda_run_cmd",
            return_value=["snakemake"],
        ):
            result = _resolve_snakemake_cmd()
        assert result == ["snakemake"]

    def test_returns_list(self) -> None:
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "shutil.which",
            return_value=None,
        ), mock.patch(
            "projio.mcp.pipeio._conda_run_cmd",
            return_value=["snakemake"],
        ):
            result = _resolve_snakemake_cmd()
        assert isinstance(result, list)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# _pipeio_available / _unavailable
# ---------------------------------------------------------------------------


class TestPipeioAvailability:
    def test_unavailable_returns_error_dict(self) -> None:
        result = _unavailable("pipeio_flow_list")
        assert "error" in result
        assert "pipeio_flow_list" in result["error"]
        assert "pip install pipeio" in result["error"]

    def test_pipeio_available_returns_bool(self) -> None:
        result = _pipeio_available()
        assert isinstance(result, bool)

    def test_pipeio_unavailable_when_import_fails(self) -> None:
        with mock.patch.dict("sys.modules", {"pipeio": None}):
            # When pipeio is None in sys.modules, import raises ImportError
            result = _pipeio_available()
            assert result is False
