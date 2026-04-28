"""Tests for projio.mcp.pipeio — runner resolution and snakemake command helpers."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.datalad import _conda_wrap
from projio.mcp.pipeio import (
    _conda_run_cmd,
    _pixi_run_cmd,
    _pipeio_available,
    _resolve_default_env_name,
    _resolve_runner,
    _resolve_snakemake_cmd,
    _run_cmd,
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
# _conda_wrap — pixi guard
# ---------------------------------------------------------------------------


class TestCondaWrapPixiGuard:
    def test_conda_env_binary_is_wrapped(self) -> None:
        with mock.patch("shutil.which", return_value="/opt/conda/bin/conda"):
            result = _conda_wrap("/opt/conda/envs/cogpy/bin/snakemake")
        assert result is not None
        assert result == ["/opt/conda/bin/conda", "run", "-n", "cogpy", "snakemake"]

    def test_pixi_env_binary_is_not_wrapped(self) -> None:
        result = _conda_wrap("/home/user/project/.pixi/envs/default/bin/snakemake")
        assert result is None

    def test_non_env_binary_is_not_wrapped(self) -> None:
        result = _conda_wrap("/usr/bin/snakemake")
        assert result is None


# ---------------------------------------------------------------------------
# _resolve_snakemake_cmd
# ---------------------------------------------------------------------------


class TestResolveSnakemakeCmd:
    def test_explicit_env_takes_priority_conda(self) -> None:
        with mock.patch("projio.mcp.pipeio._resolve_runner", return_value="conda"), \
             mock.patch("shutil.which", return_value="/usr/bin/conda"):
            result = _resolve_snakemake_cmd(use_env="myenv")
        assert result == ["/usr/bin/conda", "run", "-n", "myenv", "snakemake"]

    def test_explicit_env_takes_priority_pixi(self) -> None:
        with mock.patch("projio.mcp.pipeio._resolve_runner", return_value="pixi"), \
             mock.patch("shutil.which", return_value="/usr/bin/pixi"):
            result = _resolve_snakemake_cmd(use_env="datalad")
        assert result == ["/usr/bin/pixi", "run", "-e", "datalad", "snakemake"]

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

    def test_finds_snakemake_on_path_conda(self) -> None:
        """For conda projects, PATH search fires when no Makefile/config env set."""
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="conda",
        ), mock.patch(
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

    def test_pixi_skips_path_search(self) -> None:
        """For pixi projects, PATH search is skipped — pixi runner fires first.

        This prevents picking up the MCP server's own snakemake (e.g. from rag
        env) when the project's pixi env is the source of truth.
        """
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="pixi",
        ), mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value=None,
        ), mock.patch(
            "shutil.which",
            return_value="/opt/conda/envs/rag/bin/snakemake",  # MCP server's PATH
        ):
            result = _resolve_snakemake_cmd()
        # Must NOT pick up rag's snakemake from PATH
        assert "rag" not in result
        # Must use pixi run snakemake instead
        assert "pixi" in " ".join(result) or result[-1] == "snakemake"
        assert "run" in result
        assert "snakemake" in result

    def test_uses_config_default_env_conda(self) -> None:
        """Step 2.5: code.envs.default with conda runner."""
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="conda",
        ), mock.patch(
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

    def test_uses_config_default_env_pixi(self) -> None:
        """Step 2.5: code.envs.default with pixi runner."""
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="pixi",
        ), mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value="datalad",
        ), mock.patch(
            "shutil.which",
            return_value="/usr/bin/pixi",
        ):
            result = _resolve_snakemake_cmd()
        assert result == ["/usr/bin/pixi", "run", "-e", "datalad", "snakemake"]

    def test_config_default_env_skips_path_snakemake(self) -> None:
        """Step 2.5 prevents picking up snakemake from MCP server's own env."""
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="conda",
        ), mock.patch(
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
            "projio.mcp.pipeio._resolve_runner",
            return_value="conda",
        ), mock.patch(
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

    def test_pixi_fallback(self, monkeypatch) -> None:
        """Step 4: pixi runner falls back to bare pixi run snakemake."""
        monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/pixi" if x == "pixi" else None)
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="pixi",
        ), mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ), mock.patch(
            "projio.mcp.pipeio._resolve_default_env_name",
            return_value=None,
        ):
            result = _resolve_snakemake_cmd()
        assert result == ["/usr/bin/pixi", "run", "snakemake"]

    def test_returns_list(self) -> None:
        with mock.patch(
            "projio.mcp.pipeio._resolve_runner",
            return_value="conda",
        ), mock.patch(
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
# _pixi_run_cmd
# ---------------------------------------------------------------------------


class TestPixiRunCmd:
    def test_uses_pixi_on_path(self) -> None:
        with mock.patch("shutil.which", return_value="/usr/bin/pixi"):
            result = _pixi_run_cmd("snakemake")
        assert result == ["/usr/bin/pixi", "run", "snakemake"]

    def test_with_env_name(self) -> None:
        with mock.patch("shutil.which", return_value="/usr/bin/pixi"):
            result = _pixi_run_cmd("snakemake", env_name="datalad")
        assert result == ["/usr/bin/pixi", "run", "-e", "datalad", "snakemake"]

    def test_falls_back_to_bare_cmd(self) -> None:
        with mock.patch("shutil.which", return_value=None):
            result = _pixi_run_cmd("snakemake")
        assert result == ["snakemake"]


# ---------------------------------------------------------------------------
# _resolve_runner
# ---------------------------------------------------------------------------


class TestResolveRunner:
    def test_explicit_config_pixi(self) -> None:
        cfg = {"code": {"runner": "pixi"}}
        with mock.patch("projio.config.load_effective_config", return_value=cfg), \
             mock.patch("projio.mcp.pipeio.get_project_root", return_value="/fake"):
            assert _resolve_runner() == "pixi"

    def test_explicit_config_conda(self) -> None:
        cfg = {"code": {"runner": "conda"}}
        with mock.patch("projio.config.load_effective_config", return_value=cfg), \
             mock.patch("projio.mcp.pipeio.get_project_root", return_value="/fake"):
            assert _resolve_runner() == "conda"

    def test_autodetect_pixi_toml(self, tmp_path) -> None:
        (tmp_path / "pixi.toml").write_text("[workspace]\nname = 'test'\n")
        cfg: dict = {"code": {}}
        with mock.patch("projio.config.load_effective_config", return_value=cfg), \
             mock.patch("projio.mcp.pipeio.get_project_root", return_value=str(tmp_path)):
            assert _resolve_runner() == "pixi"

    def test_defaults_to_conda(self, tmp_path) -> None:
        cfg: dict = {"code": {}}
        with mock.patch("projio.config.load_effective_config", return_value=cfg), \
             mock.patch("projio.mcp.pipeio.get_project_root", return_value=str(tmp_path)):
            assert _resolve_runner() == "conda"


# ---------------------------------------------------------------------------
# _run_cmd
# ---------------------------------------------------------------------------


class TestRunCmd:
    def test_dispatches_to_conda(self) -> None:
        with mock.patch("projio.mcp.pipeio._resolve_runner", return_value="conda"), \
             mock.patch("shutil.which", return_value="/usr/bin/conda"):
            result = _run_cmd("cogpy", "snakemake")
        assert result == ["/usr/bin/conda", "run", "-n", "cogpy", "snakemake"]

    def test_dispatches_to_pixi(self) -> None:
        with mock.patch("projio.mcp.pipeio._resolve_runner", return_value="pixi"), \
             mock.patch("shutil.which", return_value="/usr/bin/pixi"):
            result = _run_cmd("datalad", "snakemake")
        assert result == ["/usr/bin/pixi", "run", "-e", "datalad", "snakemake"]

    def test_pixi_empty_env_omits_flag(self) -> None:
        with mock.patch("projio.mcp.pipeio._resolve_runner", return_value="pixi"), \
             mock.patch("shutil.which", return_value="/usr/bin/pixi"):
            result = _run_cmd("", "snakemake")
        assert result == ["/usr/bin/pixi", "run", "snakemake"]


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
