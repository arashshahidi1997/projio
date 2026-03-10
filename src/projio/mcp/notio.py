"""MCP tools: note_list, note_latest, note_search."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict


def _notio_available() -> bool:
    try:
        import notio  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the notio package. Install with: pip install notio"}


def note_list(note_type: str = "", limit: int = 20) -> JsonDict:
    """List recent notes, optionally filtered by type.

    Args:
        note_type: Note type to filter (e.g. 'daily', 'weekly', 'event'). Empty = all.
        limit: Maximum number of notes to return.
    """
    if not _notio_available():
        return _unavailable("note_list")
    root = get_project_root()
    try:
        from notio import list_notes  # type: ignore[import]
        notes = list_notes(root=root, note_type=note_type or None, limit=limit)
        return json_dict({"notes": notes, "count": len(notes)})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_latest(note_type: str = "") -> JsonDict:
    """Content of the most recent note of the given type.

    Args:
        note_type: Note type (e.g. 'daily', 'weekly'). Empty = any type.
    """
    if not _notio_available():
        return _unavailable("note_latest")
    root = get_project_root()
    try:
        from notio import latest_note  # type: ignore[import]
        note = latest_note(root=root, note_type=note_type or None)
        return json_dict(note or {"error": "no notes found"})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_search(query: str, k: int = 5) -> JsonDict:
    """Semantic search over notes via indexio.

    Args:
        query: Search query.
        k: Number of results.
    """
    root = get_project_root()
    try:
        from projio.init import load_projio_config
        from indexio.query import query_index

        cfg = load_projio_config(root)
        idx_cfg = cfg.get("indexio") or {}
        config_rel = idx_cfg.get("config", "infra/indexio/config.yaml")
        config_path = str(root / config_rel)
        payload = query_index(
            config_path=config_path,
            root=str(root),
            query=query,
            corpus="notes",
            k=k,
            prefer_canonical=True,
        )
        return json_dict(payload)
    except Exception as exc:
        return json_dict({"error": str(exc), "query": query})
