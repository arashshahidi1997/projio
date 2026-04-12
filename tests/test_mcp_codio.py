"""Tests for projio.mcp.codio — MCP wrapper delegation, error handling, availability."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.codio import (
    _codio_available,
    _func_doc_local,
    _func_doc_subprocess,
    _resolve_conda,
    _unavailable,
    codio_add,
    codio_add_urls,
    codio_discover,
    codio_func_doc,
    codio_get,
    codio_list,
    codio_rag_sync,
    codio_registry,
    codio_validate,
    codio_vocab,
)


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------


class TestCodioAvailability:
    def test_available_returns_bool(self) -> None:
        assert isinstance(_codio_available(), bool)

    def test_unavailable_when_import_fails(self) -> None:
        with mock.patch.dict("sys.modules", {"codio": None}):
            assert _codio_available() is False

    def test_unavailable_message_format(self) -> None:
        result = _unavailable("codio_list")
        assert "error" in result
        assert "codio_list" in result["error"]
        assert "pip install" in result["error"]


# ---------------------------------------------------------------------------
# Unavailability: all wrappers return error when codio is not installed
# ---------------------------------------------------------------------------

_WRAPPER_FUNCTIONS = [
    (codio_list, {}),
    (codio_get, {"name": "mne"}),
    (codio_registry, {}),
    (codio_vocab, {}),
    (codio_validate, {}),
    (codio_add_urls, {"urls": ["https://github.com/test/repo"]}),
    (codio_add, {"name": "test", "kind": "external_mirror"}),
    (codio_discover, {"query": "signal processing"}),
    (codio_rag_sync, {}),
]


class TestCodioUnavailable:
    @pytest.mark.parametrize(
        "func,kwargs",
        _WRAPPER_FUNCTIONS,
        ids=[f[0].__name__ for f in _WRAPPER_FUNCTIONS],
    )
    def test_unavailable_returns_error(self, func, kwargs) -> None:
        with mock.patch("projio.mcp.codio._codio_available", return_value=False):
            result = func(**kwargs)
        assert "error" in result
        assert "codio" in result["error"].lower()


# ---------------------------------------------------------------------------
# codio_func_doc: doesn't need codio to be installed
# ---------------------------------------------------------------------------


class TestCodioFuncDoc:
    def test_func_doc_local_lists_functions(self) -> None:
        result = _func_doc_local("os", "path", None)
        assert "module" in result
        assert result["module"] == "os.path"
        assert "functions" in result
        assert len(result["functions"]) > 0

    def test_func_doc_local_single_function(self) -> None:
        result = _func_doc_local("os", "path", "join")
        assert result["function"] == "join"
        assert "signature" in result
        assert "docstring" in result

    def test_func_doc_local_missing_module(self) -> None:
        result = _func_doc_local("nonexistent_pkg_xyz", "submod", None)
        assert "error" in result
        assert "Cannot import" in result["error"]

    def test_func_doc_local_missing_function(self) -> None:
        result = _func_doc_local("os", "path", "nonexistent_func_xyz")
        assert "error" in result
        assert "not found" in result["error"]

    def test_func_doc_routing_local(self) -> None:
        """Without env, uses local introspection."""
        with mock.patch(
            "projio.mcp.codio._func_doc_local",
            return_value={"module": "os.path", "functions": []},
        ) as m:
            codio_func_doc(package="os", module="path")
        m.assert_called_once_with("os", "path", None)

    def test_func_doc_routing_subprocess(self) -> None:
        """With env, uses subprocess introspection."""
        with mock.patch(
            "projio.mcp.codio._func_doc_subprocess",
            return_value={"module": "os.path", "functions": []},
        ) as m:
            codio_func_doc(package="os", module="path", env="cogpy")
        m.assert_called_once_with("cogpy", "os", "path", None)

    def test_func_doc_subprocess_timeout(self) -> None:
        import subprocess
        with mock.patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="conda", timeout=30),
        ):
            result = _func_doc_subprocess("cogpy", "os", "path", None)
        assert "error" in result
        assert "timed out" in result["error"]

    def test_func_doc_subprocess_not_found(self) -> None:
        with mock.patch(
            "subprocess.run",
            side_effect=FileNotFoundError("conda"),
        ):
            result = _func_doc_subprocess("cogpy", "os", "path", None)
        assert "error" in result
        assert "conda not found" in result["error"]


# ---------------------------------------------------------------------------
# _resolve_conda
# ---------------------------------------------------------------------------


class TestResolveConda:
    def test_returns_conda_from_config(self) -> None:
        with mock.patch(
            "projio.mcp.codio.get_project_root",
            return_value=Path("/fake"),
        ), mock.patch(
            "projio.init.load_projio_config",
            return_value={"runtime": {"conda": "/opt/conda/bin/conda"}},
        ):
            assert _resolve_conda() == "/opt/conda/bin/conda"

    def test_fallback_to_bare_conda(self) -> None:
        with mock.patch(
            "projio.mcp.codio.get_project_root",
            side_effect=RuntimeError("no project"),
        ):
            assert _resolve_conda() == "conda"


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------


class TestCodioDelegation:
    def _mock_codio(self):
        return mock.patch.multiple(
            "projio.mcp.codio",
            _codio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_codio_list_delegates(self) -> None:
        mock_reg = mock.MagicMock()
        with self._mock_codio(), mock.patch(
            "codio.load_config", create=True, return_value=mock.MagicMock(),
        ), mock.patch(
            "codio.Registry", create=True, return_value=mock_reg,
        ), mock.patch(
            "codio.mcp.mcp_list", create=True,
            return_value=[{"name": "mne"}, {"name": "yasa"}],
        ) as m:
            result = codio_list()
        assert "libraries" in result
        assert len(result["libraries"]) == 2

    def test_codio_get_delegates(self) -> None:
        with self._mock_codio(), mock.patch(
            "codio.load_config", create=True, return_value=mock.MagicMock(),
        ), mock.patch(
            "codio.Registry", create=True, return_value=mock.MagicMock(),
        ), mock.patch(
            "codio.mcp.mcp_get", create=True,
            return_value={"name": "mne", "kind": "external_mirror"},
        ) as m:
            result = codio_get("mne")
        assert result["name"] == "mne"

    def test_codio_get_not_found(self) -> None:
        with self._mock_codio(), mock.patch(
            "codio.load_config", create=True, return_value=mock.MagicMock(),
        ), mock.patch(
            "codio.Registry", create=True, return_value=mock.MagicMock(),
        ), mock.patch(
            "codio.mcp.mcp_get", create=True, return_value=None,
        ):
            result = codio_get("nonexistent")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_codio_vocab_delegates(self) -> None:
        with self._mock_codio(), mock.patch(
            "codio.mcp.mcp_vocab", create=True,
            return_value={"kinds": ["internal", "external_mirror"]},
        ):
            result = codio_vocab()
        assert "kinds" in result


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------


class TestCodioExceptionHandling:
    def _mock_codio(self):
        return mock.patch.multiple(
            "projio.mcp.codio",
            _codio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_codio_list_exception(self) -> None:
        with self._mock_codio(), mock.patch(
            "codio.load_config", create=True,
            side_effect=FileNotFoundError("catalog.yml"),
        ):
            result = codio_list()
        assert "error" in result

    def test_codio_discover_exception(self) -> None:
        with self._mock_codio(), mock.patch(
            "codio.load_config", create=True,
            side_effect=RuntimeError("bad config"),
        ):
            result = codio_discover("signal processing")
        assert "error" in result
