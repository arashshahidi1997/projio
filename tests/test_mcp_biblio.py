"""Tests for projio.mcp.biblio — MCP wrapper delegation, error handling, availability."""
from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.biblio import (
    _biblio_available,
    _unavailable,
    biblio_author_papers,
    biblio_compile,
    biblio_crossref_resolve,
    biblio_discover_authors,
    biblio_discover_institutions,
    biblio_docling,
    biblio_docling_batch,
    biblio_docling_status,
    biblio_enrich,
    biblio_enrich_topic_tags,
    biblio_extract,
    biblio_grobid,
    biblio_grobid_check,
    biblio_graph_expand,
    biblio_graph_promote,
    biblio_ingest,
    biblio_institution_authors,
    biblio_institution_works,
    biblio_library_quality,
    biblio_library_set,
    biblio_merge,
    biblio_openalex_resolve,
    biblio_pdf_fetch,
    biblio_pdf_fetch_oa,
    biblio_pdf_fetch_oa_status,
    biblio_pdf_validate,
    biblio_pool_promote,
    biblio_rag_sync,
    biblio_status,
    biblio_zotero_pull,
    biblio_zotero_push,
    biblio_zotero_status,
    citekey_resolve,
    library_get,
    paper_absent_refs,
    paper_context,
)


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------


class TestBiblioAvailability:
    def test_available_returns_bool(self) -> None:
        assert isinstance(_biblio_available(), bool)

    def test_unavailable_when_import_fails(self) -> None:
        with mock.patch.dict("sys.modules", {"biblio": None}):
            assert _biblio_available() is False

    def test_unavailable_message_format(self) -> None:
        result = _unavailable("citekey_resolve")
        assert "error" in result
        assert "citekey_resolve" in result["error"]
        assert "pip install" in result["error"]


# ---------------------------------------------------------------------------
# Unavailability: all wrappers return error when biblio is not installed
# ---------------------------------------------------------------------------

_WRAPPER_FUNCTIONS = [
    (citekey_resolve, {"citekeys": ["smith2020"]}),
    (paper_context, {"citekey": "smith2020"}),
    (paper_absent_refs, {"citekey": "smith2020"}),
    (library_get, {"citekey": "smith2020"}),
    (biblio_ingest, {"dois": ["10.1234/test"]}),
    (biblio_library_set, {"citekeys": ["smith2020"]}),
    (biblio_merge, {}),
    (biblio_openalex_resolve, {}),
    (biblio_crossref_resolve, {"dois": ["10.1234/test"]}),
    (biblio_compile, {}),
    (biblio_pdf_fetch, {}),
    (biblio_pdf_fetch_oa, {}),
    (biblio_pdf_fetch_oa_status, {"job_id": "j1"}),
    (biblio_docling, {"citekey": "smith2020"}),
    (biblio_docling_status, {"job_id": "j1"}),
    (biblio_docling_batch, {}),
    (biblio_grobid, {"citekey": "smith2020"}),
    (biblio_grobid_check, {}),
    (biblio_graph_expand, {"citekeys": ["smith2020"]}),
    (biblio_graph_promote, {}),
    (biblio_extract, {"citekey": "smith2020"}),
    (biblio_rag_sync, {}),
    (biblio_pdf_validate, {}),
    (biblio_library_quality, {}),
    (biblio_status, {}),
    (biblio_discover_authors, {"query": "test"}),
    (biblio_discover_institutions, {"query": "test"}),
    (biblio_institution_works, {"institution_id": "I1"}),
    (biblio_institution_authors, {"institution_id": "I1"}),
    (biblio_author_papers, {"author_id": "A1"}),
    (biblio_pool_promote, {"citekeys": ["smith2020"]}),
    (biblio_zotero_pull, {}),
    (biblio_zotero_push, {}),
    (biblio_zotero_status, {}),
    (biblio_enrich, {"citekeys": ["smith2020"]}),
    (biblio_enrich_topic_tags, {"citekeys": ["smith2020"]}),
]


class TestBiblioUnavailable:
    @pytest.mark.parametrize(
        "func,kwargs",
        _WRAPPER_FUNCTIONS,
        ids=[f[0].__name__ for f in _WRAPPER_FUNCTIONS],
    )
    def test_unavailable_returns_error(self, func, kwargs) -> None:
        with mock.patch("projio.mcp.biblio._biblio_available", return_value=False):
            result = func(**kwargs)
        assert "error" in result
        assert "biblio" in result["error"].lower()


# ---------------------------------------------------------------------------
# Delegation: verify wrappers call underlying functions
# ---------------------------------------------------------------------------


class TestBiblioDelegation:
    def _mock_biblio(self):
        return mock.patch.multiple(
            "projio.mcp.biblio",
            _biblio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_citekey_resolve_delegates(self) -> None:
        with self._mock_biblio(), mock.patch(
            "biblio.mcp.resolve_citekeys", create=True,
            return_value={"entries": [{"citekey": "smith2020"}]},
        ) as m:
            result = citekey_resolve(["smith2020"])
        m.assert_called_once_with(["smith2020"], root=Path("/fake/root"))
        assert "entries" in result

    def test_paper_context_delegates(self) -> None:
        with self._mock_biblio(), mock.patch(
            "biblio.mcp.paper_context", create=True,
            return_value={"citekey": "smith2020", "title": "A Paper"},
        ) as m:
            result = paper_context("smith2020")
        m.assert_called_once_with("smith2020", root=Path("/fake/root"))
        assert result["title"] == "A Paper"

    def test_library_get_delegates(self) -> None:
        with self._mock_biblio(), mock.patch(
            "biblio.mcp.library_get", create=True,
            return_value={"citekey": "smith2020", "status": "read"},
        ) as m:
            result = library_get("smith2020")
        assert result["status"] == "read"

    def test_grobid_check_delegates(self) -> None:
        fake_cfg = mock.MagicMock()
        with self._mock_biblio(), mock.patch(
            "projio.mcp.biblio._load_biblio_cfg",
            return_value=fake_cfg,
        ), mock.patch(
            "biblio.grobid.check_grobid_server_as_dict", create=True,
            return_value={"status": "running", "url": "http://localhost:8070"},
        ) as m:
            result = biblio_grobid_check()
        m.assert_called_once_with(fake_cfg.grobid)
        assert result["status"] == "running"

    def test_biblio_status_delegates(self) -> None:
        with self._mock_biblio(), mock.patch(
            "biblio.mcp.pipeline_status", create=True,
            return_value={"total": 42, "with_pdf": 30},
        ) as m:
            result = biblio_status()
        m.assert_called_once()


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------


class TestBiblioExceptionHandling:
    def _mock_biblio(self):
        return mock.patch.multiple(
            "projio.mcp.biblio",
            _biblio_available=mock.MagicMock(return_value=True),
            get_project_root=mock.MagicMock(return_value=Path("/fake/root")),
        )

    def test_citekey_resolve_exception(self) -> None:
        with self._mock_biblio(), mock.patch(
            "biblio.mcp.resolve_citekeys", create=True,
            side_effect=RuntimeError("merge conflict"),
        ):
            result = citekey_resolve(["smith2020"])
        assert "error" in result
        assert "merge conflict" in result["error"]
        assert result["citekeys"] == ["smith2020"]

    def test_paper_context_exception(self) -> None:
        with self._mock_biblio(), mock.patch(
            "biblio.mcp.paper_context", create=True,
            side_effect=FileNotFoundError("no pdf"),
        ):
            result = paper_context("smith2020")
        assert "error" in result

    def test_biblio_merge_exception(self) -> None:
        with self._mock_biblio(), mock.patch(
            "projio.mcp.biblio._load_biblio_cfg",
            return_value=(mock.MagicMock(), Path("/fake")),
        ), mock.patch(
            "biblio.bibtex.merge_bib_files", create=True,
            side_effect=ValueError("bad bibtex"),
        ):
            result = biblio_merge()
        assert "error" in result
