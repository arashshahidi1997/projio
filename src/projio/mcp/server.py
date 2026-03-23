"""FastMCP stdio server — registers all projio tools."""
from __future__ import annotations

from fastmcp import FastMCP

from . import biblio, codio, context, notio, pipeio, rag, site as site_mcp

server = FastMCP("projio")


# --- RAG tools ---

@server.tool("rag_query")
def rag_query_tool(query: str, corpus: str = "", k: int = 8):
    """Similarity search against the project Chroma store."""
    return rag.rag_query(query=query, corpus=corpus, k=k)


@server.tool("rag_query_multi")
def rag_query_multi_tool(queries: list[str], corpus: str = "", k: int = 5):
    """Multi-query similarity search, deduplicated by source path."""
    return rag.rag_query_multi(queries=queries, corpus=corpus, k=k)


@server.tool("corpus_list")
def corpus_list_tool():
    """List indexed corpora with chunk counts."""
    return rag.corpus_list()


@server.tool("indexio_build")
def indexio_build_tool(sources: list[str] = []):
    """Rebuild the search index. Full rebuild by default, or partial if sources specified."""
    return rag.indexio_build(sources=sources or None)


# --- Biblio tools ---

@server.tool("citekey_resolve")
def citekey_resolve_tool(citekeys: list[str]):
    """Resolve citekeys into title/authors/year/doi/abstract/tags/status."""
    return biblio.citekey_resolve(citekeys)


@server.tool("paper_context")
def paper_context_tool(citekey: str):
    """Full structured context for a paper including docling excerpt and local refs."""
    return biblio.paper_context(citekey)


@server.tool("paper_absent_refs")
def paper_absent_refs_tool(citekey: str):
    """References in the paper not matched locally (GROBID unresolved refs)."""
    return biblio.paper_absent_refs(citekey)


@server.tool("library_get")
def library_get_tool(citekey: str):
    """Status/tags/priority from the library ledger for a citekey."""
    return biblio.library_get(citekey)


@server.tool("biblio_ingest")
def biblio_ingest_tool(dois: list[str], tags: list[str] = [], status: str = "unread", collection: str = ""):
    """Ingest papers by DOI. Resolves metadata via OpenAlex, generates citekeys, writes BibTeX.
    Optionally sets tags/status and adds to a collection."""
    return biblio.biblio_ingest(
        dois=dois, tags=tags or None, status=status, collection=collection or None,
    )


@server.tool("biblio_library_set")
def biblio_library_set_tool(citekeys: list[str], status: str = "", tags: list[str] = [], priority: str = ""):
    """Bulk-update library ledger entries (status/tags/priority) for multiple citekeys."""
    return biblio.biblio_library_set(
        citekeys=citekeys, status=status or None, tags=tags or None, priority=priority or None,
    )


@server.tool("biblio_merge")
def biblio_merge_tool(dry_run: bool = False):
    """Merge source .bib files into the main bibliography (bib/main.bib)."""
    return biblio.biblio_merge(dry_run=dry_run)


@server.tool("biblio_docling")
def biblio_docling_tool(citekey: str, force: bool = False):
    """Run Docling on a paper's PDF to extract full text as markdown."""
    return biblio.biblio_docling(citekey=citekey, force=force)


@server.tool("biblio_grobid")
def biblio_grobid_tool(citekey: str, force: bool = False):
    """Run GROBID on a paper's PDF to extract structured header and references."""
    return biblio.biblio_grobid(citekey=citekey, force=force)


@server.tool("biblio_grobid_check")
def biblio_grobid_check_tool():
    """Check whether the GROBID server is reachable."""
    return biblio.biblio_grobid_check()


# --- Notio tools ---

@server.tool("note_list")
def note_list_tool(note_type: str = "", limit: int = 20):
    """List recent notes, optionally filtered by type."""
    return notio.note_list(note_type=note_type, limit=limit)


@server.tool("note_latest")
def note_latest_tool(note_type: str = ""):
    """Content of the most recent note of a given type."""
    return notio.note_latest(note_type=note_type)


@server.tool("note_read")
def note_read_tool(path: str):
    """Read a specific note by its relative path."""
    return notio.note_read(path=path)


@server.tool("note_create")
def note_create_tool(note_type: str, owner: str = "", title: str = "", date: str = ""):
    """Create a new note of the given type."""
    return notio.note_create(note_type=note_type, owner=owner, title=title, date=date)


@server.tool("note_update")
def note_update_tool(path: str, fields: str):
    """Update frontmatter fields of an existing note. Pass fields as JSON string."""
    return notio.note_update(path=path, fields=fields)


@server.tool("note_types")
def note_types_tool():
    """List all configured note types."""
    return notio.note_types()


@server.tool("note_search")
def note_search_tool(query: str, k: int = 5):
    """Semantic search over notes via indexio."""
    return notio.note_search(query=query, k=k)


# --- Codio tools ---

@server.tool("codio_list")
def codio_list_tool(kind: str = "", language: str = "", capability: str = "", priority: str = "", runtime_import: str = ""):
    """List libraries from the code reuse registry with optional filters."""
    return codio.codio_list(
        kind=kind or None, language=language or None,
        capability=capability or None, priority=priority or None,
        runtime_import=runtime_import or None,
    )


@server.tool("codio_get")
def codio_get_tool(name: str):
    """Full merged record for a single library from the code reuse registry."""
    return codio.codio_get(name)


@server.tool("codio_registry")
def codio_registry_tool():
    """Full snapshot of the code reuse registry (catalog + profiles)."""
    return codio.codio_registry()


@server.tool("codio_vocab")
def codio_vocab_tool():
    """Controlled vocabulary for the code reuse registry fields."""
    return codio.codio_vocab()


@server.tool("codio_validate")
def codio_validate_tool():
    """Validate code reuse registry consistency."""
    return codio.codio_validate()


@server.tool("codio_add_urls")
def codio_add_urls_tool(urls: list[str], clone: bool = False, shallow: bool = False):
    """Add libraries to the code reuse registry from GitHub/GitLab URLs.
    Fetches metadata (language, license, description) from GitHub API automatically."""
    return codio.codio_add_urls(urls=urls, clone=clone, shallow=shallow)


@server.tool("codio_discover")
def codio_discover_tool(query: str, language: str = ""):
    """Search for libraries matching a capability query."""
    return codio.codio_discover(query=query, language=language or None)


# --- Pipeio tools ---

@server.tool("pipeio_flow_list")
def pipeio_flow_list_tool(pipe: str = ""):
    """List pipeline flows, optionally filtered by pipe name."""
    return pipeio.pipeio_flow_list(pipe=pipe or None)


@server.tool("pipeio_flow_status")
def pipeio_flow_status_tool(pipe: str, flow: str):
    """Show status of a specific pipeline flow (config, outputs, notebooks)."""
    return pipeio.pipeio_flow_status(pipe=pipe, flow=flow)


@server.tool("pipeio_nb_status")
def pipeio_nb_status_tool():
    """Show notebook sync and publication status across all flows."""
    return pipeio.pipeio_nb_status()


@server.tool("pipeio_registry_validate")
def pipeio_registry_validate_tool():
    """Validate pipeline registry consistency (code vs docs, config schema)."""
    return pipeio.pipeio_registry_validate()


# --- Context tools ---

@server.tool("project_context")
def project_context_tool():
    """Structured snapshot of the project: config, README excerpt, key paths."""
    return context.project_context()


@server.tool("runtime_conventions")
def runtime_conventions_tool():
    """Parse Makefile variables and targets from the project root."""
    return context.runtime_conventions()


@server.tool("agent_instructions")
def agent_instructions_tool():
    """Agent execution context: tool routing, workflow conventions, enabled packages.
    Call this before executing prompts in this project to get tool-aware instructions."""
    return context.agent_instructions()


# --- Site tools ---

@server.tool("site_detect")
def site_detect_tool():
    """Detect the doc-site framework used by the project (mkdocs, sphinx, vite)."""
    return site_mcp.site_detect()


@server.tool("site_serve")
def site_serve_tool(port: int = 0, framework: str = ""):
    """Start the project doc server in background. Returns URL and PID."""
    return site_mcp.site_serve(
        port=port or None,
        framework=framework or None,
    )


@server.tool("site_stop")
def site_stop_tool(port: int = 0, pid: int = 0):
    """Stop a running doc server by port or PID."""
    return site_mcp.site_stop(port=port or None, pid=pid or None)


@server.tool("site_list")
def site_list_tool():
    """List running doc servers for this project."""
    return site_mcp.site_list()


def main() -> None:
    """Run the MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()
