"""Tests for projio.mcp.pipeio — MCP wrapper delegation, error handling, availability."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.pipeio import (
    _pipeio_available,
    _resolve_project_python,
    _unavailable,
    pipeio_completion,
    pipeio_config_init,
    pipeio_config_patch,
    pipeio_config_read,
    pipeio_contracts_validate,
    pipeio_cross_flow,
    pipeio_dag_export,
    pipeio_docs_collect,
    pipeio_docs_nav,
    pipeio_flow_deregister,
    pipeio_flow_fork,
    pipeio_flow_list,
    pipeio_flow_new,
    pipeio_flow_status,
    pipeio_log_parse,
    pipeio_mkdocs_nav_patch,
    pipeio_mod_audit,
    pipeio_mod_context,
    pipeio_mod_create,
    pipeio_mod_doc_refresh,
    pipeio_mod_list,
    pipeio_mod_resolve,
    pipeio_modkey_bib,
    pipeio_nb_analyze,
    pipeio_nb_audit,
    pipeio_nb_create,
    pipeio_nb_diff,
    pipeio_nb_exec,
    pipeio_nb_lab,
    pipeio_nb_pipeline,
    pipeio_nb_promote,
    pipeio_nb_publish,
    pipeio_nb_read,
    pipeio_nb_report,
    pipeio_nb_scan,
    pipeio_nb_snapshot,
    pipeio_nb_status,
    pipeio_nb_sync,
    pipeio_nb_sync_flow,
    pipeio_nb_update,
    pipeio_nb_validate,
    pipeio_nb_watch,
    pipeio_registry_scan,
    pipeio_registry_validate,
    pipeio_report,
    pipeio_rule_insert,
    pipeio_rule_list,
    pipeio_rule_stub,
    pipeio_rule_update,
    pipeio_run,
    pipeio_run_dashboard,
    pipeio_run_kill,
    pipeio_run_status,
    pipeio_script_create,
    pipeio_target_paths,
)


# ---------------------------------------------------------------------------
# _resolve_project_python
# ---------------------------------------------------------------------------


class TestResolveProjectPython:
    def test_returns_env_python_from_config(self) -> None:
        with mock.patch(
            "projio.config.resolve_env_python",
            return_value="/opt/conda/envs/cogpy/bin/python",
        ), mock.patch(
            "projio.mcp.pipeio.get_project_root",
            return_value=Path("/fake"),
        ):
            result = _resolve_project_python()
        assert result == "/opt/conda/envs/cogpy/bin/python"

    def test_falls_back_to_makefile_python(self) -> None:
        with mock.patch(
            "projio.config.resolve_env_python",
            return_value=None,
        ), mock.patch(
            "projio.mcp.pipeio.get_project_root",
            return_value=Path("/fake"),
        ), mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={"PYTHON": "/usr/bin/python3"},
        ), mock.patch(
            "projio.mcp.pipeio._expand",
            side_effect=lambda v, _: v,
        ):
            result = _resolve_project_python()
        assert result == "/usr/bin/python3"

    def test_returns_none_when_nothing_configured(self) -> None:
        with mock.patch(
            "projio.config.resolve_env_python",
            return_value=None,
        ), mock.patch(
            "projio.mcp.pipeio.get_project_root",
            return_value=Path("/fake"),
        ), mock.patch(
            "projio.mcp.pipeio.resolve_makefile_vars",
            return_value={},
        ):
            result = _resolve_project_python()
        assert result is None


# ---------------------------------------------------------------------------
# Unavailability: all public wrappers return correct error when pipeio missing
# ---------------------------------------------------------------------------

# List of (function, args) pairs for all public wrapper functions
_WRAPPER_FUNCTIONS = [
    (pipeio_flow_list, {}),
    (pipeio_flow_status, {"flow": "test"}),
    (pipeio_flow_fork, {"flow": "a", "new_flow": "b"}),
    (pipeio_flow_deregister, {"flow": "test"}),
    (pipeio_flow_new, {"flow": "test"}),
    (pipeio_nb_status, {}),
    (pipeio_nb_update, {"flow": "f", "name": "n"}),
    (pipeio_mod_list, {}),
    (pipeio_mod_resolve, {"modkeys": ["k"]}),
    (pipeio_mod_context, {}),
    (pipeio_registry_scan, {}),
    (pipeio_modkey_bib, {}),
    (pipeio_docs_collect, {}),
    (pipeio_docs_nav, {}),
    (pipeio_contracts_validate, {}),
    (pipeio_nb_create, {"flow": "f", "name": "n"}),
    (pipeio_nb_sync, {"flow": "f", "name": "n"}),
    (pipeio_nb_sync_flow, {"flow": "f"}),
    (pipeio_nb_publish, {"flow": "f", "name": "n"}),
    (pipeio_nb_analyze, {"flow": "f", "name": "n"}),
    (pipeio_nb_diff, {"flow": "f", "name": "n"}),
    (pipeio_nb_lab, {}),
    (pipeio_nb_scan, {}),
    (pipeio_nb_read, {"flow": "f", "name": "n"}),
    (pipeio_nb_audit, {}),
    (pipeio_nb_pipeline, {"flow": "f", "name": "n"}),
    (pipeio_mkdocs_nav_patch, {}),
    (pipeio_rule_list, {}),
    (pipeio_rule_stub, {"flow": "f", "rule_name": "r"}),
    (pipeio_rule_insert, {"flow": "f", "rule_name": "r"}),
    (pipeio_rule_update, {"flow": "f", "rule_name": "r"}),
    (pipeio_config_read, {}),
    (pipeio_config_patch, {"flow": "f", "registry_entry": ""}),
    (pipeio_config_init, {"flow": "f"}),
    (pipeio_registry_validate, {}),
    (pipeio_mod_create, {"flow": "f", "mod": "m"}),
    (pipeio_nb_exec, {"flow": "f", "name": "n"}),
    (pipeio_mod_audit, {"flow": "f"}),
    (pipeio_mod_doc_refresh, {"flow": "f", "mod": "m"}),
    (pipeio_script_create, {"flow": "f", "mod": "m", "script_name": "s"}),
    (pipeio_nb_promote, {"flow": "f", "name": "n", "mod": "m"}),
    (pipeio_nb_validate, {"flow": "f", "name": "n"}),
    (pipeio_nb_watch, {"flow": "f", "name": "n"}),
    (pipeio_nb_snapshot, {"flow": "f", "name": "n"}),
    (pipeio_nb_report, {"flow": "f", "name": "n"}),
    (pipeio_dag_export, {"flow": "f"}),
    (pipeio_report, {"flow": "f"}),
    (pipeio_target_paths, {"flow": "f", "group": "g", "member": "m"}),
    (pipeio_completion, {"flow": "f"}),
    (pipeio_cross_flow, {}),
    (pipeio_log_parse, {"flow": "f"}),
    (pipeio_run, {"flow": "f"}),
    (pipeio_run_status, {}),
    (pipeio_run_dashboard, {}),
    (pipeio_run_kill, {"run_id": "r"}),
]


class TestPipeioUnavailable:
    """All wrapper functions return a descriptive error when pipeio is not installed."""

    @pytest.mark.parametrize(
        "func,kwargs",
        _WRAPPER_FUNCTIONS,
        ids=[f[0].__name__ for f in _WRAPPER_FUNCTIONS],
    )
    def test_unavailable_returns_error(self, func, kwargs) -> None:
        with mock.patch("projio.mcp.pipeio._pipeio_available", return_value=False):
            result = func(**kwargs)
        assert "error" in result
        assert "pipeio" in result["error"].lower()
        assert "pip install" in result["error"]


# ---------------------------------------------------------------------------
# Delegation: verify wrapper calls underlying mcp function and returns result
# ---------------------------------------------------------------------------


class TestPipeioFlowDelegation:
    """Wrappers delegate to pipeio.mcp.mcp_* functions correctly."""

    def _mock_pipeio(self):
        """Create a context that makes pipeio available and mocks project root."""
        return mock.patch.multiple(
            "projio.mcp.pipeio",
            _pipeio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_flow_list_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_flow_list", create=True, return_value={"flows": []},
        ) as m:
            result = pipeio_flow_list(prefix="pre")
        m.assert_called_once_with(Path("/fake/root"), prefix="pre")
        assert result == {"flows": []}

    def test_flow_status_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_flow_status", create=True, return_value={"flow": "test", "status": "ok"},
        ) as m:
            result = pipeio_flow_status("test")
        m.assert_called_once_with(Path("/fake/root"), flow="test")
        assert result["flow"] == "test"

    def test_flow_fork_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_flow_fork", create=True, return_value={"forked": True},
        ) as m:
            result = pipeio_flow_fork("a", "b")
        m.assert_called_once_with(Path("/fake/root"), flow="a", new_flow="b")
        assert result["forked"] is True

    def test_flow_deregister_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_flow_deregister", create=True, return_value={"removed": "test"},
        ) as m:
            result = pipeio_flow_deregister("test")
        m.assert_called_once()
        assert result["removed"] == "test"

    def test_mod_list_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_mod_list", create=True, return_value={"mods": ["a", "b"]},
        ) as m:
            result = pipeio_mod_list(flow="f")
        m.assert_called_once_with(Path("/fake/root"), flow="f")
        assert result["mods"] == ["a", "b"]

    def test_mod_resolve_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_mod_resolve", create=True, return_value={"resolved": []},
        ) as m:
            result = pipeio_mod_resolve(modkeys=["flow-a_mod-b"])
        m.assert_called_once_with(Path("/fake/root"), modkeys=["flow-a_mod-b"])

    def test_registry_validate_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_registry_validate", create=True, return_value={"valid": True},
        ) as m:
            result = pipeio_registry_validate()
        m.assert_called_once()
        assert result["valid"] is True


class TestPipeioNotebookDelegation:
    """Notebook wrapper functions delegate correctly."""

    def _mock_pipeio(self):
        return mock.patch.multiple(
            "projio.mcp.pipeio",
            _pipeio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_nb_status_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_status", create=True, return_value={"notebooks": []},
        ) as m:
            result = pipeio_nb_status(flow="f", name="n")
        m.assert_called_once_with(Path("/fake/root"), flow="f", name="n")

    def test_nb_status_empty_params_become_none(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_status", create=True, return_value={"notebooks": []},
        ) as m:
            pipeio_nb_status()
        m.assert_called_once_with(Path("/fake/root"), flow=None, name=None)

    def test_nb_create_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_create", create=True, return_value={"created": True},
        ) as m:
            result = pipeio_nb_create(flow="f", name="n", kind="investigate")
        assert result["created"] is True

    def test_nb_read_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_read", create=True, return_value={"content": "# test"},
        ) as m:
            result = pipeio_nb_read(flow="f", name="n")
        m.assert_called_once_with(Path("/fake/root"), flow="f", name="n")
        assert result["content"] == "# test"

    def test_nb_analyze_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_analyze", create=True, return_value={"cells": 5},
        ) as m:
            result = pipeio_nb_analyze(flow="f", name="n")
        m.assert_called_once()

    def test_nb_validate_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_validate", create=True, return_value={"valid": True},
        ) as m:
            result = pipeio_nb_validate(flow="f", name="n")
        assert result["valid"] is True

    def test_nb_audit_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_audit", create=True, return_value={"issues": []},
        ) as m:
            result = pipeio_nb_audit()
        m.assert_called_once()

    def test_nb_promote_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_promote", create=True, return_value={"promoted": True},
        ) as m:
            result = pipeio_nb_promote(flow="f", name="n", mod="m")
        assert result["promoted"] is True


class TestPipeioRuleDelegation:
    """Rule and config wrappers delegate correctly."""

    def _mock_pipeio(self):
        return mock.patch.multiple(
            "projio.mcp.pipeio",
            _pipeio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_rule_list_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_rule_list", create=True, return_value={"rules": []},
        ) as m:
            result = pipeio_rule_list(flow="f")
        m.assert_called_once()

    def test_config_read_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_config_read", create=True, return_value={"config": {}},
        ) as m:
            result = pipeio_config_read(flow="f")
        m.assert_called_once()


class TestPipeioRunDelegation:
    """Run-related wrappers delegate correctly."""

    def _mock_pipeio(self):
        return mock.patch.multiple(
            "projio.mcp.pipeio",
            _pipeio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_run_status_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_run_status", create=True, return_value={"running": []},
        ) as m:
            result = pipeio_run_status()
        m.assert_called_once()

    def test_run_dashboard_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_run_dashboard", create=True, return_value={"dashboard": "ok"},
        ) as m:
            result = pipeio_run_dashboard()
        m.assert_called_once()

    def test_run_kill_delegates(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_run_kill", create=True, return_value={"killed": "r"},
        ) as m:
            result = pipeio_run_kill("r")
        m.assert_called_once()


# ---------------------------------------------------------------------------
# Exception handling: underlying function raises → error dict returned
# ---------------------------------------------------------------------------


class TestPipeioExceptionHandling:
    """Wrappers catch exceptions and return error dicts."""

    def _mock_pipeio(self):
        return mock.patch.multiple(
            "projio.mcp.pipeio",
            _pipeio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_flow_list_exception_returns_error(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_flow_list", create=True, side_effect=RuntimeError("boom"),
        ):
            result = pipeio_flow_list()
        assert "error" in result
        assert "boom" in result["error"]

    def test_nb_read_exception_returns_error(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_nb_read", create=True, side_effect=FileNotFoundError("missing"),
        ):
            result = pipeio_nb_read(flow="f", name="n")
        assert "error" in result
        assert "missing" in result["error"]

    def test_run_exception_returns_error(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_run", create=True, side_effect=ValueError("bad wildcard"),
        ):
            result = pipeio_run(flow="f")
        assert "error" in result
        assert "bad wildcard" in result["error"]

    def test_mod_create_exception_returns_error(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_mod_create", create=True, side_effect=OSError("permission denied"),
        ):
            result = pipeio_mod_create(flow="f", mod="m")
        assert "error" in result

    def test_dag_export_exception_returns_error(self) -> None:
        with self._mock_pipeio(), mock.patch(
            "pipeio.mcp.mcp_dag_export", create=True, side_effect=RuntimeError("snakemake failed"),
        ):
            result = pipeio_dag_export(flow="f")
        assert "error" in result
