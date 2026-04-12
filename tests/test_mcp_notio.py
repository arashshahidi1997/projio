"""Tests for projio.mcp.notio — MCP wrapper delegation, error handling, availability."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.notio import (
    _notio_available,
    _unavailable,
    note_capture,
    note_create,
    note_latest,
    note_list,
    note_promote,
    note_pull,
    note_read,
    note_remote_status,
    note_resolve,
    note_search,
    note_types,
    note_update,
    notio_log_nav,
    notio_reindex,
)


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------


class TestNotioAvailability:
    def test_available_returns_bool(self) -> None:
        assert isinstance(_notio_available(), bool)

    def test_unavailable_when_import_fails(self) -> None:
        with mock.patch.dict("sys.modules", {"notio": None}):
            assert _notio_available() is False

    def test_unavailable_message_format(self) -> None:
        result = _unavailable("note_list")
        assert "error" in result
        assert "note_list" in result["error"]
        assert "pip install" in result["error"]


# ---------------------------------------------------------------------------
# Unavailability: all wrappers return error when notio is not installed
# ---------------------------------------------------------------------------

_WRAPPER_FUNCTIONS = [
    (note_list, {}),
    (note_latest, {}),
    (note_read, {"path": "notes/test.md"}),
    (note_resolve, {"note_id": "20260101-120000"}),
    (note_create, {"note_type": "idea"}),
    (note_update, {"path": "notes/test.md", "fields": '{"status": "done"}'}),
    (note_types, {}),
    (notio_reindex, {}),
    (notio_log_nav, {}),
    (note_promote, {"note_path": "notes/test.md"}),
    (note_capture, {"remote": "github#42"}),
    (note_pull, {}),
    (note_remote_status, {}),
]


class TestNotioUnavailable:
    @pytest.mark.parametrize(
        "func,kwargs",
        _WRAPPER_FUNCTIONS,
        ids=[f[0].__name__ for f in _WRAPPER_FUNCTIONS],
    )
    def test_unavailable_returns_error(self, func, kwargs) -> None:
        with mock.patch("projio.mcp.notio._notio_available", return_value=False):
            result = func(**kwargs)
        assert "error" in result
        assert "notio" in result["error"].lower()


# ---------------------------------------------------------------------------
# note_read: input validation
# ---------------------------------------------------------------------------


class TestNoteReadValidation:
    def test_no_path_no_id_returns_error(self) -> None:
        """note_read requires either path or note_id."""
        result = note_read()
        assert "error" in result
        assert "provide" in result["error"].lower()


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------


class TestNotioDelegation:
    def _mock_notio(self):
        return mock.patch.multiple(
            "projio.mcp.notio",
            _notio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_note_list_delegates(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.list_notes", create=True,
            return_value=[{"path": "notes/idea/test.md"}],
        ) as m:
            result = note_list(note_type="idea", limit=10)
        m.assert_called_once_with(root=Path("/fake/root"), note_type="idea", limit=10)
        assert result["count"] == 1

    def test_note_list_empty_type_passes_none(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.list_notes", create=True,
            return_value=[],
        ) as m:
            note_list()
        m.assert_called_once_with(root=Path("/fake/root"), note_type=None, limit=20)

    def test_note_latest_delegates(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.latest_note", create=True,
            return_value={"path": "notes/daily/2026-04-12.md", "content": "today"},
        ) as m:
            result = note_latest(note_type="daily")
        m.assert_called_once_with(root=Path("/fake/root"), note_type="daily")
        assert "path" in result

    def test_note_latest_no_notes_returns_error(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.latest_note", create=True, return_value=None,
        ):
            result = note_latest()
        assert "error" in result
        assert "no notes" in result["error"]

    def test_note_read_by_path(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.query.read_note", create=True,
            return_value={"path": "notes/idea/test.md", "content": "body"},
        ) as m:
            result = note_read(path="notes/idea/test.md")
        m.assert_called_once_with(Path("/fake/root"), "notes/idea/test.md")
        assert result["content"] == "body"

    def test_note_read_by_id_resolves_then_reads(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.query.resolve_note", create=True,
            return_value={"path": "notes/idea/test.md"},
        ), mock.patch(
            "notio.query.read_note", create=True,
            return_value={"path": "notes/idea/test.md", "content": "resolved"},
        ) as m:
            result = note_read(note_id="20260101-120000")
        assert result["content"] == "resolved"

    def test_note_read_by_id_not_found(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.query.resolve_note", create=True, return_value=None,
        ):
            result = note_read(note_id="nonexistent")
        assert "error" in result
        assert "nonexistent" in result["error"]

    def test_note_resolve_delegates(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.query.resolve_note", create=True,
            return_value={"path": "notes/idea/test.md"},
        ) as m:
            result = note_resolve("20260101")
        m.assert_called_once_with(Path("/fake/root"), "20260101")

    def test_note_create_delegates(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.config.load_config", create=True,
            return_value=mock.MagicMock(),
        ), mock.patch(
            "notio.core.create_note", create=True,
            return_value=Path("/fake/root/notes/idea/new.md"),
        ) as m:
            result = note_create(note_type="idea", title="Test Idea")
        assert result["type"] == "idea"
        assert "path" in result

    def test_note_update_delegates(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.query.update_note_frontmatter", create=True,
            return_value={"status": "done"},
        ) as m:
            result = note_update("notes/test.md", '{"status": "done"}')
        m.assert_called_once_with(Path("/fake/root"), "notes/test.md", {"status": "done"})
        assert "status" in result["updated_fields"]

    def test_note_types_delegates(self) -> None:
        fake_config = mock.MagicMock()
        fake_type = mock.MagicMock()
        fake_type.mode = "date"
        fake_type.template = "idea.md"
        fake_type.filename = "{date}-{title}.md"
        fake_type.toc_keys = ["title", "date"]
        fake_config.note_types = {"idea": fake_type}

        with self._mock_notio(), mock.patch(
            "notio.config.load_config", create=True, return_value=fake_config,
        ):
            result = note_types()
        assert "types" in result
        assert "idea" in result["types"]


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------


class TestNotioExceptionHandling:
    def _mock_notio(self):
        return mock.patch.multiple(
            "projio.mcp.notio",
            _notio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_note_list_exception(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.list_notes", create=True,
            side_effect=RuntimeError("config missing"),
        ):
            result = note_list()
        assert "error" in result
        assert "config missing" in result["error"]

    def test_note_create_exception(self) -> None:
        with self._mock_notio(), mock.patch(
            "notio.config.load_config", create=True,
            side_effect=FileNotFoundError("notio.toml"),
        ):
            result = note_create(note_type="idea")
        assert "error" in result

    def test_note_update_bad_json(self) -> None:
        with self._mock_notio():
            result = note_update("notes/test.md", "not json")
        assert "error" in result
