"""MCP tools: citekey_resolve, paper_context, paper_absent_refs, library_get."""
from __future__ import annotations

from typing import Any

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
        from biblio.library import resolve_citekeys  # type: ignore[import]
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
        from biblio.library import paper_context as _paper_context  # type: ignore[import]
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
        from biblio.library import absent_refs  # type: ignore[import]
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
        from biblio.library import library_get as _library_get  # type: ignore[import]
        return json_dict(_library_get(citekey, root=root))
    except Exception as exc:
        return json_dict({"error": str(exc), "citekey": citekey})
