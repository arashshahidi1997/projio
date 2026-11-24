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


PRESENT = ["note_read", "present_build", "present_list", "codio_get"]


def test_present_is_opt_in_by_default():
    assert toolset.opt_in_dropped(PRESENT, "", set()) == {"present_build", "present_list"}
    assert toolset.opt_in_dropped(PRESENT, "-codio", set()) == {"present_build", "present_list"}


def test_present_opt_in_by_packages_yml_or_spec(tmp_path):
    assert toolset.opt_in_dropped(PRESENT, "", {"present"}) == set()
    assert toolset.opt_in_dropped(PRESENT, "notio,present", set()) == set()
    assert toolset.opt_in_dropped(PRESENT, "present_build", set()) == {"present_list"}
    (tmp_path / ".projio").mkdir()
    (tmp_path / ".projio" / "packages.yml").write_text(
        "packages:\n  present:\n    enabled: true\n  figio:\n    enabled: false\n")
    assert toolset.enabled_packages(tmp_path) == {"present"}
    assert toolset.enabled_packages(tmp_path / "missing") == set()


def test_opt_in_applies_without_spec(monkeypatch, capsys):
    pytest.importorskip("fastmcp")
    from fastmcp import FastMCP
    srv = FastMCP("t")
    for n in ("codio_get", "present_build"):
        srv.tool(n)(lambda: None)
    monkeypatch.delenv(toolset.ENV_VAR, raising=False)
    toolset.apply_tool_filter(srv, enabled=set())
    assert [t.name for t in asyncio.run(srv.list_tools())] == ["codio_get"]
    assert "opt-in groups left out: present" in capsys.readouterr().err
