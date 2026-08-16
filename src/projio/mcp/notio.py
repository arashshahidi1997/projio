"""MCP tools: note CRUD, search, and type introspection."""
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


def note_read(path: str = "", note_id: str = "", note_type: str = "") -> JsonDict:
    """Read a specific note by its relative path or note ID.

    Args:
        path: Relative path to the note file (as returned by note_list).
        note_id: Timestamp ID, capture ID, or filename fragment (alternative to path).
        note_type: Optional note type hint (e.g. 'idea', 'issue') — used with note_id
            to narrow the search to a specific type folder.
    """
    if not _notio_available():
        return _unavailable("note_read")
    if not path and not note_id:
        return {"error": "provide either 'path' or 'note_id'"}
    root = get_project_root()
    try:
        from notio.query import read_note  # type: ignore[import]
        if not path and note_id:
            from notio.query import resolve_note  # type: ignore[import]
            resolved = resolve_note(root, note_id)
            if not resolved:
                return json_dict({"error": f"no note matching '{note_id}'"})
            path = resolved.get("path", "")
            if not path:
                return json_dict({"error": f"resolved note has no path: {resolved}"})
        note = read_note(root, path)
        return json_dict(note or {"error": f"note not found: {path}"})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_resolve(note_id: str) -> JsonDict:
    """Resolve a note by its timestamp ID, capture ID, or filename fragment.

    Args:
        note_id: Timestamp (e.g. '20260326-134127'), capture ID
            (e.g. '20260326-134127-9a803f'), or any substring of the filename.
    """
    if not _notio_available():
        return _unavailable("note_resolve")
    root = get_project_root()
    try:
        from notio.query import resolve_note  # type: ignore[import]
        note = resolve_note(root, note_id)
        return json_dict(note or {"error": f"no note matching '{note_id}'"})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_create(
    note_type: str,
    owner: str = "",
    title: str = "",
    date: str = "",
    body: str = "",
    frontmatter: str = "",
) -> JsonDict:
    """Create a new note of the given type, optionally fully populated in one call.

    Pass *body* and/or *frontmatter* to skip the template read-then-write
    round-trips that are otherwise required when creating notes as an agent.

    Args:
        note_type: Note type (e.g. 'daily', 'weekly', 'idea', 'meeting', 'result').
        owner: Note owner/author.
        title: Note title (for event-mode types).
        date: Date override (YYYY-MM-DD).
        body: Markdown body to use instead of the template body.  Everything
            below the frontmatter closing ``---`` is replaced with this text.
        frontmatter: JSON string of frontmatter fields to set/override,
            e.g. '{"tags": ["result"], "series": "preprocess", "confidence": "confirmed"}'.
    """
    if not _notio_available():
        return _unavailable("note_create")
    root = get_project_root()
    try:
        import json as _json
        from notio.config import load_config  # type: ignore[import]
        from notio.core import create_note  # type: ignore[import]
        config = load_config(root)

        extra_fm: dict | None = _json.loads(frontmatter) if frontmatter else None

        path = create_note(
            config,
            note_type,
            owner=owner or None,
            title=title or None,
            note_date=date or None,
            body=body or None,
            extra_frontmatter=extra_fm,
        )
        return json_dict({"path": str(path.relative_to(root)), "type": note_type})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_update(path: str, fields: str) -> JsonDict:
    """Update frontmatter fields of an existing note.

    Args:
        path: Relative path to the note file.
        fields: JSON string of fields to update, e.g. '{"status": "done"}'.
    """
    if not _notio_available():
        return _unavailable("note_update")
    root = get_project_root()
    try:
        import json
        from notio.query import update_note_frontmatter  # type: ignore[import]
        parsed_fields = json.loads(fields)
        meta = update_note_frontmatter(root, path, parsed_fields)
        return json_dict({"path": path, "updated_fields": list(parsed_fields.keys()), "frontmatter": meta})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_types() -> JsonDict:
    """List all configured note types."""
    if not _notio_available():
        return _unavailable("note_types")
    root = get_project_root()
    try:
        from notio.config import load_config  # type: ignore[import]
        config = load_config(root)
        types = {
            name: {
                "mode": t.mode,
                "template": t.template,
                "filename": t.filename,
                "toc_keys": list(t.toc_keys),
            }
            for name, t in config.note_types.items()
        }
        return json_dict({"types": types})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def notio_reindex(note_type: str = "") -> JsonDict:
    """Regenerate index.md files for note type directories and the root index.

    Args:
        note_type: Specific note type to reindex (e.g. 'idea', 'issue'). Empty = all types.
    """
    if not _notio_available():
        return _unavailable("notio_reindex")
    root = get_project_root()
    try:
        from notio.config import load_config  # type: ignore[import]
        from notio.core import build_root_index, build_type_index  # type: ignore[import]

        config = load_config(root)
        rebuilt: list[str] = []
        if note_type:
            if note_type not in config.note_types:
                return json_dict({"error": f"unknown note type: {note_type}", "available": sorted(config.note_types)})
            path = build_type_index(config, note_type)
            rebuilt.append(str(path.relative_to(root)))
        else:
            for name in sorted(config.note_types):
                path = build_type_index(config, name)
                rebuilt.append(str(path.relative_to(root)))
        root_path = build_root_index(config)
        rebuilt.append(str(root_path.relative_to(root)))
        return json_dict({"rebuilt": rebuilt, "count": len(rebuilt)})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def notio_log_nav() -> JsonDict:
    """Generate docs/log/mkdocs.yml for the monorepo plugin.

    Scans docs/log/ subdirectories for note types and writes a standalone
    mkdocs.yml consumed by ``!include ./docs/log/mkdocs.yml`` in the root
    mkdocs.yml.
    """
    if not _notio_available():
        return _unavailable("notio_log_nav")
    root = get_project_root()
    try:
        from notio.docs import log_nav  # type: ignore[import]

        yaml_str = log_nav(root, write=True)
        sub_mkdocs = root / "docs" / "log" / "mkdocs.yml"
        return json_dict({
            "action": "written" if sub_mkdocs.is_file() else "skipped",
            "path": "docs/log/mkdocs.yml",
            "yaml": yaml_str,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_promote(
    note_path: str,
    labels: str = "",
    assignee: str = "",
    milestone: str = "",
    dry_run: bool = False,
) -> JsonDict:
    """Promote a local note to a GitHub/GitLab issue.

    Creates a platform issue from the note title and body, then writes the
    ``remote`` reference back into the note frontmatter.

    Args:
        note_path: Relative path to the note file.
        labels: Comma-separated labels (default: derived from note tags).
        assignee: Issue assignee username.
        milestone: Issue milestone name.
        dry_run: Preview what would be created without calling the API.
    """
    if not _notio_available():
        return _unavailable("note_promote")
    root = get_project_root()
    try:
        from notio.remote import promote  # type: ignore[import]
        label_list = [l.strip() for l in labels.split(",") if l.strip()] if labels else None
        result = promote(
            root, note_path,
            labels=label_list,
            assignee=assignee,
            milestone=milestone,
            dry_run=dry_run,
        )
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_capture(
    remote: str,
    note_type: str = "issue",
    owner: str = "",
) -> JsonDict:
    """Create a local note from a GitHub/GitLab issue.

    Fetches the issue via ``gh``/``glab`` CLI, creates a note with mapped
    fields, and pulls the comment thread into the note.

    Args:
        remote: Remote reference, e.g. ``github#42`` or ``gitlab#15``.
        note_type: Note type to create (default: ``issue``).
        owner: Note owner (default: git user).
    """
    if not _notio_available():
        return _unavailable("note_capture")
    root = get_project_root()
    try:
        from notio.remote import capture  # type: ignore[import]
        result = capture(root, remote, note_type=note_type, owner=owner)
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_pull(
    note_path: str = "",
    note_type: str = "",
    all_notes: bool = False,
    dry_run: bool = False,
) -> JsonDict:
    """Fetch remote thread updates for linked notes.

    Replaces the ``## Remote Thread`` section with current platform comments.
    Pull is idempotent — running twice with no new comments produces no diff.

    Args:
        note_path: Pull a specific note by relative path.
        note_type: Pull all linked notes of this type.
        all_notes: Pull all linked notes across all types.
        dry_run: Preview what would be updated without writing.
    """
    if not _notio_available():
        return _unavailable("note_pull")
    root = get_project_root()
    try:
        from notio.remote import pull  # type: ignore[import]
        result = pull(
            root,
            note_path=note_path,
            note_type=note_type,
            all_notes=all_notes,
            dry_run=dry_run,
        )
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_remote_status() -> JsonDict:
    """List all notes linked to platform issues.

    Shows note type, path, remote reference, and current status for every
    note that has a ``remote`` frontmatter field.
    """
    if not _notio_available():
        return _unavailable("note_remote_status")
    root = get_project_root()
    try:
        from notio.remote import remote_status  # type: ignore[import]
        return json_dict(remote_status(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def note_search(query: str, k: int = 5, corpus: str = "notes") -> JsonDict:
    """Semantic search over notes via indexio.

    Args:
        query: Search query.
        k: Number of results.
        corpus: Corpus to search (default "notes"). When the default "notes" corpus
            is not present in the indexio config, auto-detects the best available
            alternative (prefers "docs", then searches all corpora).
    """
    root = get_project_root()
    try:
        from projio.init import load_projio_config
        from indexio.query import query_index

        cfg = load_projio_config(root)
        idx_cfg = cfg.get("indexio") or {}
        config_rel = idx_cfg.get("config", "infra/indexio/config.yaml")
        config_path = str(root / config_rel)

        resolved_corpus = corpus
        corpus_note: str | None = None
        if corpus == "notes":
            try:
                from indexio.config import load_indexio_config
                idx_config = load_indexio_config(config_path, root=str(root))
                available = {s.corpus for s in idx_config.sources}
                if "notes" not in available:
                    if "docs" in available:
                        resolved_corpus = "docs"
                    else:
                        resolved_corpus = ""
                    corpus_note = (
                        f"corpus 'notes' not found in indexio config; "
                        f"searched corpus={resolved_corpus!r} instead "
                        f"(available: {sorted(available)})"
                    )
            except Exception:
                pass

        payload = query_index(
            config_path=config_path,
            root=str(root),
            query=query,
            corpus=resolved_corpus or None,
            k=k,
            prefer_canonical=True,
        )
        if corpus_note:
            payload["corpus_note"] = corpus_note
        return json_dict(payload)
    except Exception as exc:
        return json_dict({"error": str(exc), "query": query})
