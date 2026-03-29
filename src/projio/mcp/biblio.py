"""MCP tools: biblio read/write tools including merge, docling, grobid."""
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


def _load_biblio_cfg():
    """Load BiblioConfig from the project root."""
    from biblio.config import default_config_path, load_biblio_config
    root = get_project_root()
    config_path = default_config_path(root=root)
    return load_biblio_config(config_path, root=root)


def biblio_merge(dry_run: bool = False) -> JsonDict:
    """Merge source .bib files into the main bibliography (bib/main.bib).

    Args:
        dry_run: If true, report what would be merged without writing.
    """
    if not _biblio_available():
        return _unavailable("biblio_merge")
    try:
        cfg = _load_biblio_cfg()
        from biblio.bibtex import merge_srcbib
        n_sources, n_entries = merge_srcbib(cfg.bibtex_merge, dry_run=dry_run)
        return json_dict({
            "n_sources": n_sources,
            "n_entries": n_entries,
            "out_bib": str(cfg.bibtex_merge.out_bib),
            "dry_run": dry_run,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_docling(citekey: str, force: bool = False, background: bool = False) -> JsonDict:
    """Run Docling on a paper's PDF to extract full text as markdown.

    After a successful extraction, automatically runs ref-md standardization
    if GROBID TEI output already exists for this citekey.

    Args:
        citekey: BibTeX citekey to process.
        force: Re-run even if outputs already exist.
        background: If true, launch in background and return a job_id immediately.
                    Use biblio_docling_status(job_id) to check progress.
    """
    if not _biblio_available():
        return _unavailable("biblio_docling")

    if background:
        try:
            from biblio.jobs import launch_docling_background
            root = get_project_root()
            job_id = launch_docling_background(root, citekey, force=force)
            return json_dict({
                "background": True,
                "job_id": job_id,
                "citekey": citekey.lstrip("@"),
                "status": "running",
                "hint": "Use biblio_docling_status(job_id) to check progress.",
            })
        except Exception as exc:
            return json_dict({"error": str(exc), "citekey": citekey})

    try:
        cfg = _load_biblio_cfg()
        from biblio.docling import run_docling_for_key
        out = run_docling_for_key(cfg, citekey, force=force)
        result: JsonDict = {
            "citekey": citekey.lstrip("@"),
            "md_path": str(out.md_path),
            "json_path": str(out.json_path),
            "outdir": str(out.outdir),
        }
        # Auto-chain ref-md if GROBID TEI already exists
        try:
            from biblio.grobid import grobid_outputs_for_key
            from biblio.ref_md import run_ref_md_for_key
            grobid_out = grobid_outputs_for_key(cfg, citekey)
            if grobid_out.tei_path.exists():
                ref_out = run_ref_md_for_key(cfg, citekey, force=force)
                result["ref_md_path"] = str(ref_out.md_path)
                result["ref_md"] = "resolved"
            else:
                result["ref_md"] = "skipped (GROBID TEI not yet available)"
        except Exception as ref_exc:
            result["ref_md"] = f"failed: {ref_exc}"
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "citekey": citekey})


def biblio_docling_status(job_id: str) -> JsonDict:
    """Check the status of a background biblio_docling job.

    Args:
        job_id: Job ID returned by biblio_docling(..., background=True).
    """
    if not _biblio_available():
        return _unavailable("biblio_docling_status")
    try:
        from biblio.jobs import get_job_status
        root = get_project_root()
        info = get_job_status(root, job_id)
        if info is None:
            return json_dict({"error": f"No job found with id: {job_id}"})
        result: JsonDict = {
            "job_id": info.job_id,
            "status": info.status,
            "citekey": info.citekey,
            "started": info.started,
            "finished": info.finished,
        }
        if info.result is not None:
            result["result"] = info.result
        if info.error is not None:
            result["error"] = info.error
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "job_id": job_id})


def biblio_grobid(citekey: str, force: bool = False) -> JsonDict:
    """Run GROBID on a paper's PDF to extract structured header and references.

    After a successful extraction, automatically runs ref-md standardization
    if Docling markdown output already exists for this citekey.

    Args:
        citekey: BibTeX citekey to process.
        force: Re-run even if outputs already exist.
    """
    if not _biblio_available():
        return _unavailable("biblio_grobid")
    try:
        cfg = _load_biblio_cfg()
        from biblio.grobid import run_grobid_for_key
        out = run_grobid_for_key(cfg, citekey, force=force)
        result: JsonDict = {
            "citekey": citekey.lstrip("@"),
            "header_path": str(out.header_path),
            "references_path": str(out.references_path),
            "tei_path": str(out.tei_path),
            "outdir": str(out.outdir),
        }
        # Auto-chain ref-md if Docling markdown already exists
        try:
            from biblio.docling import outputs_for_key as docling_outputs_for_key
            from biblio.ref_md import run_ref_md_for_key
            docling_out = docling_outputs_for_key(cfg, citekey)
            if docling_out.md_path.exists():
                ref_out = run_ref_md_for_key(cfg, citekey, force=force)
                result["ref_md_path"] = str(ref_out.md_path)
                result["ref_md"] = "resolved"
            else:
                result["ref_md"] = "skipped (Docling markdown not yet available)"
        except Exception as ref_exc:
            result["ref_md"] = f"failed: {ref_exc}"
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "citekey": citekey})


def biblio_graph_expand(
    citekeys: list[str] | None = None,
    direction: str = "references",
    merge: bool = True,
    force: bool = False,
) -> JsonDict:
    """Expand the OpenAlex reference graph from resolved seed records.

    Args:
        citekeys: Optional list of citekeys to expand (default: all seeds).
        direction: Expansion direction: "references", "citing", or "both".
        merge: Merge with existing graph_candidates.json (default: True).
        force: Re-fetch cached OpenAlex records (default: False).
    """
    if not _biblio_available():
        return _unavailable("biblio_graph_expand")
    root = get_project_root()
    try:
        from biblio.mcp import graph_expand
        result = graph_expand(
            root=root,
            citekeys=citekeys,
            direction=direction,
            merge=merge,
            force=force,
        )
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_rag_sync(force_init: bool = False) -> JsonDict:
    """Register biblio docling sources into the indexio config.

    Wraps ``biblio rag sync``. After this, run ``indexio_build`` (optionally
    with ``sources=["biblio_docling"]``) to index the paper full-texts.

    Args:
        force_init: Re-initialize the RAG config even if it already exists.
    """
    if not _biblio_available():
        return _unavailable("biblio_rag_sync")
    root = get_project_root()
    try:
        from biblio.rag import sync_biblio_rag_config
        result = sync_biblio_rag_config(root, force_init=force_init)
        return json_dict({
            "config_path": str(result.config_path),
            "created": result.created,
            "initialized": result.initialized,
            "added": list(result.added),
            "updated": list(result.updated),
            "removed": list(result.removed),
            "follow_up_cmd": result.follow_up_cmd,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_grobid_check() -> JsonDict:
    """Check whether the GROBID server is reachable."""
    if not _biblio_available():
        return _unavailable("biblio_grobid_check")
    try:
        cfg = _load_biblio_cfg()
        from biblio.grobid import check_grobid_server_as_dict
        return json_dict(check_grobid_server_as_dict(cfg.grobid))
    except Exception as exc:
        return json_dict({"error": str(exc)})
