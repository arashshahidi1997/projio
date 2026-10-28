"""PROJIO_MCP_TOOLS: a reduced tool set per server entry."""
from __future__ import annotations

import asyncio

import pytest

from projio.mcp import toolset

NAMES = ["rag_query", "rag_query_multi", "corpus_list", "indexio_build", "biblio_status", "biblio_zotero_pull",
         "paper_lookup", "citekey_resolve", "library_get", "codio_get", "codio_list", "note_read", "pipeio_run"]


def test_unset_keeps_everything():
    assert toolset.select_tools(NAMES, "") == (NAMES, [])
    assert toolset.select_tools(NAMES, None) == (NAMES, [])


def test_subsystems_and_globs():
    kept, unmatched = toolset.select_tools(NAMES, "codio, biblio rag")
    assert kept == ["rag_query", "rag_query_multi", "corpus_list", "biblio_status", "biblio_zotero_pull",
                    "paper_lookup", "citekey_resolve", "library_get", "codio_get", "codio_list"]
    assert unmatched == []
    assert toolset.select_tools(NAMES, "note_read,pipeio_*")[0] == ["note_read", "pipeio_run"]


def test_exclusions_and_unmatched():
    kept, _ = toolset.select_tools(NAMES, "biblio,-biblio_zotero_*")
    assert kept == ["biblio_status", "paper_lookup", "citekey_resolve", "library_get"]
    kept, unmatched = toolset.select_tools(NAMES, "-pipeio,-nothing_*")
    assert "pipeio_run" not in kept and len(kept) == len(NAMES) - 1 and unmatched == ["nothing_*"]


def test_filter_applies_to_the_real_server(monkeypatch, capsys):
    pytest.importorskip("fastmcp")
    from fastmcp import FastMCP
    srv = FastMCP("t")
    for n in ("codio_get", "pipeio_run", "paper_lookup"):
        srv.tool(n)(lambda: None)
    monkeypatch.setenv(toolset.ENV_VAR, "codio,biblio")
    toolset.apply_tool_filter(srv)
    assert sorted(t.name for t in asyncio.run(srv.list_tools())) == ["codio_get", "paper_lookup"]
    assert "2 of 3 tools" in capsys.readouterr().err
