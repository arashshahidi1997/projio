"""MCP tools: citekey_resolve, paper_context, paper_absent_refs, library_get."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict


def _biblio_available() -> bool:
    try:
        import biblio  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the biblio package. Install with: pip install biblio-tools"}


def citekey_resolve(citekeys: list[str]) -> JsonDict:
    """Resolve citekeys into title/authors/year/doi/abstract/tags/status.

    Args:
        citekeys: List of BibTeX citekeys to resolve.
    """
    if not _biblio_available():
        return _unavailable("citekey_resolve")
    root = get_project_root()
    try:
        from biblio.mcp import resolve_citekeys
        result = resolve_citekeys(citekeys, root=root)
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "citekeys": citekeys})


def paper_context(citekey: str) -> JsonDict:
    """Full structured context for a paper: bib entry, docling excerpt, local refs.

    Args:
        citekey: BibTeX citekey.
    """
    if not _biblio_available():
        return _unavailable("paper_context")
    root = get_project_root()
    try:
        from biblio.mcp import paper_context as _paper_context
        return json_dict(_paper_context(citekey, root=root))
    except Exception as exc:
        return json_dict({"error": str(exc), "citekey": citekey})


def paper_absent_refs(citekey: str) -> JsonDict:
    """References in the paper not matched locally (GROBID unresolved refs).

    Args:
        citekey: BibTeX citekey.
    """
    if not _biblio_available():
        return _unavailable("paper_absent_refs")
    root = get_project_root()
    try:
        from biblio.mcp import absent_refs
        return json_dict(absent_refs(citekey, root=root))
    except Exception as exc:
        return json_dict({"error": str(exc), "citekey": citekey})


def library_get(citekey: str) -> JsonDict:
    """Status/tags/priority from the library ledger for a citekey.

    Args:
        citekey: BibTeX citekey.
    """
    if not _biblio_available():
        return _unavailable("library_get")
    root = get_project_root()
    try:
        from biblio.mcp import library_get as _library_get
        return json_dict(_library_get(citekey, root=root))
    except Exception as exc:
        return json_dict({"error": str(exc), "citekey": citekey})


# --- Write tools ---


def biblio_ingest(
    dois: list[str],
    tags: list[str] | None = None,
    status: str = "unread",
    collection: str | None = None,
) -> JsonDict:
    """Ingest papers by DOI. Resolves metadata via OpenAlex, generates citekeys, writes BibTeX.

    Args:
        dois: List of DOIs to ingest.
        tags: Optional tags to set on all ingested papers.
        status: Library status for ingested papers (default: unread).
        collection: Optional collection name to add papers to.
    """
    if not _biblio_available():
        return _unavailable("biblio_ingest")
    root = get_project_root()
    try:
        from biblio.mcp import ingest_dois
        result = ingest_dois(
            dois,
            root=root,
            tags=tags or None,
            status=status,
            collection=collection or None,
        )
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "dois": dois})


def biblio_library_set(
    citekeys: list[str],
    status: str | None = None,
    tags: list[str] | None = None,
    priority: str | None = None,
) -> JsonDict:
    """Bulk-update library ledger entries (status/tags/priority) for multiple citekeys.

    Args:
        citekeys: List of BibTeX citekeys to update.
        status: Status to set (unread, reading, processed, archived).
        tags: Tags to set.
        priority: Priority to set (low, normal, high).
    """
    if not _biblio_available():
        return _unavailable("biblio_library_set")
    root = get_project_root()
    try:
        from biblio.mcp import library_set_bulk
        result = library_set_bulk(
            citekeys,
            root=root,
            status=status,
            tags=tags,
            priority=priority,
        )
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "citekeys": citekeys})
