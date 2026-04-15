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
    _resolve_default_env_name,
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
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value=None,
        ), mock.patch(
            "shutil.which",
            return_value="/usr/bin/snakemake",
        ), mock.patch(
            "projio.mcp.datalad._conda_wrap",
            return_value=None,
        ):
            result = _resolve_snakemake_cmd()
        assert result == ["/usr/bin/snakemake"]

    def test_uses_config_default_env(self) -> None:
        """Step 2.5: code.envs.default is used before PATH search."""
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value="cogpy",
        ), mock.patch(
            "shutil.which",
            return_value="/usr/bin/conda",
        ):
            result = _resolve_snakemake_cmd()
        assert result == ["/usr/bin/conda", "run", "-n", "cogpy", "snakemake"]

    def test_config_default_env_skips_path_snakemake(self) -> None:
        """Step 2.5 prevents picking up snakemake from MCP server's own env."""
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value="cogpy",
        ), mock.patch(
            "shutil.which",
            return_value="/opt/conda/envs/rag/bin/conda",
        ):
            result = _resolve_snakemake_cmd()
        # Must use cogpy, not rag
        assert "cogpy" in result
        assert "rag" not in result

    def test_falls_back_to_bare_snakemake(self, monkeypatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda x: None)
        with mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value=None,
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
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value=None,
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
# _resolve_default_env_name
# ---------------------------------------------------------------------------


class TestResolveDefaultEnvName:
    def test_returns_env_name_from_config(self) -> None:
        cfg = {"code": {"envs": {"default": "cogpy"}, "conda_prefix": "/opt/conda"}}
        with mock.patch("projio.config.load_effective_config", return_value=cfg), \
             mock.patch("projio.mcp.pipeio.get_project_root", return_value=Path("/fake")):
            result = _resolve_default_env_name()
        assert result == "cogpy"

    def test_returns_none_when_key_absent(self) -> None:
        cfg: dict = {"code": {}}
        with mock.patch("projio.config.load_effective_config", return_value=cfg), \
             mock.patch("projio.mcp.pipeio.get_project_root", return_value=Path("/fake")):
            result = _resolve_default_env_name()
        assert result is None

    def test_returns_none_on_exception(self) -> None:
        with mock.patch(
            "projio.config.load_effective_config",
            side_effect=FileNotFoundError("no config"),
        ), mock.patch("projio.mcp.pipeio.get_project_root", return_value=Path("/fake")):
            result = _resolve_default_env_name()
        assert result is None


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
