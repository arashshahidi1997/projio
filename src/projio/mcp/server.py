"""FastMCP stdio server — registers all projio tools."""
from __future__ import annotations

from fastmcp import FastMCP

from . import biblio, codio, context, notio, rag

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


# --- Notio tools ---

@server.tool("note_list")
def note_list_tool(note_type: str = "", limit: int = 20):
    """List recent notes, optionally filtered by type."""
    return notio.note_list(note_type=note_type, limit=limit)


@server.tool("note_latest")
def note_latest_tool(note_type: str = ""):
    """Content of the most recent note of a given type."""
    return notio.note_latest(note_type=note_type)


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


@server.tool("codio_discover")
def codio_discover_tool(query: str, language: str = ""):
    """Search for libraries matching a capability query."""
    return codio.codio_discover(query=query, language=language or None)


# --- Context tools ---

@server.tool("project_context")
def project_context_tool():
    """Structured snapshot of the project: config, README excerpt, key paths."""
    return context.project_context()


@server.tool("runtime_conventions")
def runtime_conventions_tool():
    """Parse Makefile variables and targets from the project root."""
    return context.runtime_conventions()


def main() -> None:
    """Run the MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()
