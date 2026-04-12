"""Tests for projio.mcp.figio — MCP wrapper delegation, error handling, availability."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.figio import (
    _figio_available,
    _unavailable,
    figio_build,
    figio_edit_spec,
    figio_figure_list,
    figio_inspect,
    figio_query_output,
    figio_validate,
)


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------


class TestFigioAvailability:
    def test_available_returns_bool(self) -> None:
        assert isinstance(_figio_available(), bool)

    def test_unavailable_when_import_fails(self) -> None:
        with mock.patch.dict("sys.modules", {"figio": None}):
            assert _figio_available() is False

    def test_unavailable_message_format(self) -> None:
        result = _unavailable("figio_build")
        assert "error" in result
        assert "figio_build" in result["error"]
        assert "pip install" in result["error"]


# ---------------------------------------------------------------------------
# Unavailability: all wrappers return error when figio is not installed
# ---------------------------------------------------------------------------

_WRAPPER_FUNCTIONS = [
    (figio_figure_list, {}),
    (figio_inspect, {}),
    (figio_build, {"figure_id": "fig1"}),
    (figio_validate, {"figure_id": "fig1"}),
    (figio_edit_spec, {"figure_id": "fig1"}),
    (figio_query_output, {"figure_id": "fig1", "query": "dimensions"}),
]


class TestFigioUnavailable:
    @pytest.mark.parametrize(
        "func,kwargs",
        _WRAPPER_FUNCTIONS,
        ids=[f[0].__name__ for f in _WRAPPER_FUNCTIONS],
    )
    def test_unavailable_returns_error(self, func, kwargs) -> None:
        with mock.patch("projio.mcp.figio._figio_available", return_value=False):
            result = func(**kwargs)
        assert "error" in result
        assert "figio" in result["error"].lower()


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------


class TestFigioDelegation:
    def _mock_figio(self):
        return mock.patch.multiple(
            "projio.mcp.figio",
            _figio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_figure_list_delegates(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_figure_list", create=True,
            return_value={"figures": ["fig1", "fig2"]},
        ) as m:
            result = figio_figure_list()
        m.assert_called_once_with(Path("/fake/root"))
        assert result["figures"] == ["fig1", "fig2"]

    def test_inspect_delegates(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_inspect", create=True,
            return_value={"figure_id": "fig1", "panels": 3},
        ) as m:
            result = figio_inspect(figure_id="fig1")
        m.assert_called_once_with(Path("/fake/root"), figure_id="fig1")
        assert result["panels"] == 3

    def test_inspect_empty_id(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_inspect", create=True,
            return_value={"figures": []},
        ) as m:
            figio_inspect()
        m.assert_called_once_with(Path("/fake/root"), figure_id="")

    def test_build_delegates(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_build", create=True,
            return_value={"output": "/fake/fig1.svg", "valid": True},
        ) as m:
            result = figio_build(figure_id="fig1", panels="A,B", force=True)
        m.assert_called_once_with(
            Path("/fake/root"), figure_id="fig1", panels="A,B", force=True,
        )
        assert result["valid"] is True

    def test_validate_delegates(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_validate", create=True,
            return_value={"valid": True, "warnings": []},
        ) as m:
            result = figio_validate(figure_id="fig1", target="nature")
        m.assert_called_once_with(
            Path("/fake/root"), figure_id="fig1", target="nature",
        )
        assert result["valid"] is True

    def test_edit_spec_delegates(self) -> None:
        patch = {"layout": {"columns": 2}}
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_edit_spec", create=True,
            return_value={"updated": True},
        ) as m:
            result = figio_edit_spec(figure_id="fig1", patch=patch)
        m.assert_called_once_with(
            Path("/fake/root"), figure_id="fig1", patch=patch,
        )
        assert result["updated"] is True

    def test_query_output_delegates(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_query_output", create=True,
            return_value={"dimensions": {"width": 180, "height": 120}},
        ) as m:
            result = figio_query_output(figure_id="fig1", query="dimensions")
        m.assert_called_once_with(
            Path("/fake/root"), figure_id="fig1", query="dimensions",
        )
        assert result["dimensions"]["width"] == 180


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------


class TestFigioExceptionHandling:
    def _mock_figio(self):
        return mock.patch.multiple(
            "projio.mcp.figio",
            _figio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_build_exception(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_build", create=True,
            side_effect=RuntimeError("panel script failed"),
        ):
            result = figio_build(figure_id="fig1")
        assert "error" in result
        assert "panel script failed" in result["error"]

    def test_validate_exception(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_validate", create=True,
            side_effect=FileNotFoundError("spec not found"),
        ):
            result = figio_validate(figure_id="fig1")
        assert "error" in result

    def test_figure_list_exception(self) -> None:
        with self._mock_figio(), mock.patch(
            "figio.mcp.mcp_figure_list", create=True,
            side_effect=OSError("permission denied"),
        ):
            result = figio_figure_list()
        assert "error" in result
