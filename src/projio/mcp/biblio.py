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
    """Merge source .bib files into .projio/biblio/merged.bib (intermediate).

    Run biblio_compile() after this to produce the final compiled.bib.

    Args:
        dry_run: If true, report what would be merged without writing.
    """
    if not _biblio_available():
        return _unavailable("biblio_merge")
    try:
        cfg = _load_biblio_cfg()
        from biblio.bibtex import merge_srcbib
        n_sources, n_entries, quality_warnings = merge_srcbib(cfg.bibtex_merge, dry_run=dry_run)
        result = {
            "n_sources": n_sources,
            "n_entries": n_entries,
            "out_bib": str(cfg.bibtex_merge.out_bib),
            "dry_run": dry_run,
        }
        if quality_warnings:
            result["quality_warnings"] = len(quality_warnings)
            result["low_quality_entries"] = quality_warnings[:10]
            if len(quality_warnings) > 10:
                result["low_quality_log"] = str(cfg.bibtex_merge.duplicates_log.parent / "low_quality_entries.txt")
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_compile(
    sources: list[str] | None = None,
    output: str = "",
) -> JsonDict:
    """Compile .bib intermediates into .projio/render/compiled.bib.

    Merges merged.bib + modkey.bib (and any other bib_sources) into the
    single bibliography used by pandoc and mkdocs. Missing sources are
    skipped gracefully.

    Sources and output default to render.yml's ``bib_sources`` and
    ``bibliography`` fields.

    Args:
        sources: List of .bib file paths relative to project root.
                 Default: reads bib_sources from .projio/render.yml.
        output: Output path relative to project root.
                Default: reads bibliography from .projio/render.yml.
    """
    if not _biblio_available():
        return _unavailable("biblio_compile")
    root = get_project_root()
    try:
        from biblio.mcp import biblio_compile as _biblio_compile
        return json_dict(_biblio_compile(
            root=root,
            sources=sources or None,
            output=output or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_pdf_fetch(dry_run: bool = False, force: bool = False) -> JsonDict:
    """Copy/symlink PDFs referenced by ``file`` fields in bib/srcbib/*.bib into bib/articles/.

    Parses Zotero-exported BibTeX ``file`` fields, copies or symlinks the
    referenced PDFs into the canonical ``bib/articles/<citekey>/`` layout,
    and tracks MD5 hashes to skip unchanged files.

    Args:
        dry_run: Preview the operation without writing any files.
        force: Overwrite/recopy even if the PDF is unchanged.
    """
    if not _biblio_available():
        return _unavailable("biblio_pdf_fetch")
    try:
        cfg = _load_biblio_cfg()
        from biblio.pdf_fetch import fetch_pdfs
        counts = fetch_pdfs(cfg.pdf_fetch, dry_run=dry_run, force=force)
        result = {
            "sources": counts["sources"],
            "linked": counts["linked"],
            "skipped": counts["skipped"],
            "missing": counts["missing"],
            "dry_run": dry_run,
        }
        if counts["missing"] > 0:
            result["missing_log"] = str(cfg.pdf_fetch.missing_log)
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_pdf_fetch_oa(
    force: bool = False,
    citekeys: list[str] | None = None,
    background: bool = False,
) -> JsonDict:
    """Download PDFs via open-access cascade (pool → OpenAlex → Unpaywall → EZProxy).

    Attempts to fetch PDFs for all papers (or a filtered subset) using a
    configurable source cascade. Configure the cascade order, Unpaywall email,
    and EZProxy settings in ``bib/config/biblio.yml`` under ``pdf_fetch:``.

    Set ``background=True`` to run as a background job — returns immediately
    with a ``job_id`` for progress polling via ``biblio_pdf_fetch_oa_status``.

    Args:
        force: Download even if the PDF already exists locally.
        citekeys: Only fetch these citekeys (default: all papers).
        background: Run in background and return job_id for polling.
    """
    if not _biblio_available():
        return _unavailable("biblio_pdf_fetch_oa")
    try:
        if background:
            from biblio.jobs import launch_pdf_fetch_oa_background
            root = get_project_root()
            ck_filter = set(citekeys) if citekeys else None
            job_id, total = launch_pdf_fetch_oa_background(
                root, force=force, citekey_filter=ck_filter,
            )
            return json_dict({
                "background": True,
                "job_id": job_id,
                "status": "running",
                "total_papers": total,
                "hint": "Use biblio_pdf_fetch_oa_status(job_id) to check progress.",
            })

        cfg = _load_biblio_cfg()
        from biblio.pdf_fetch_oa import fetch_pdfs_oa, ALL_STATUSES
        ck_filter = set(citekeys) if citekeys else None
        results = fetch_pdfs_oa(cfg, force=force, citekey_filter=ck_filter)
        counts = {s: sum(1 for r in results if r.status == s) for s in ALL_STATUSES}
        result = {
            "total": len(results),
            **counts,
            "cascade_sources": list(cfg.pdf_fetch_cascade.sources),
        }
        errors = [{"citekey": r.citekey, "error": r.error} for r in results if r.error]
        if errors:
            result["errors"] = errors
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_pdf_fetch_oa_status(job_id: str) -> JsonDict:
    """Check the status of a background biblio_pdf_fetch_oa job.

    Args:
        job_id: Job ID returned by biblio_pdf_fetch_oa(..., background=True).
    """
    if not _biblio_available():
        return _unavailable("biblio_pdf_fetch_oa_status")
    try:
        from biblio.jobs import get_job_status
        root = get_project_root()
        info = get_job_status(root, job_id)
        if info is None:
            return json_dict({"error": f"No job found with id: {job_id}"})
        result: JsonDict = {
            "job_id": info.job_id,
            "status": info.status,
            "started": info.started,
            "finished": info.finished,
        }
        if info.result is not None:
            result["result"] = info.result
        if info.error is not None:
            result["error"] = info.error
        if info.progress is not None:
            result["progress"] = info.progress
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "job_id": job_id})


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
        # Auto-chain ref-md if GROBID TEI already exists (checks pool too)
        try:
            from biblio.grobid import resolve_grobid_outputs
            from biblio.ref_md import run_ref_md_for_key
            grobid_out, grobid_src = resolve_grobid_outputs(cfg, citekey)
            if grobid_src != "missing" and grobid_out.tei_path.exists():
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
        if info.progress is not None:
            result["progress"] = info.progress
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc), "job_id": job_id})


def biblio_docling_batch(
    concurrency: int = 1,
    force: bool = False,
    filter_glob: str | None = None,
) -> JsonDict:
    """Run Docling on all pending papers in the background.

    Scans citekeys.md for entries that have PDFs but no docling output yet,
    then processes them with configurable concurrency. Returns a job_id for
    progress polling via biblio_docling_status(job_id).

    Args:
        concurrency: Max parallel docling jobs (default 1). Keep low on shared
                     HPC nodes — each docling run uses ~2.7 GB RAM and 300%+ CPU.
        force: Re-run even if outputs already exist.
        filter_glob: Optional fnmatch pattern to filter citekeys (e.g. ``smith*``).
    """
    if not _biblio_available():
        return _unavailable("biblio_docling_batch")
    try:
        from biblio.jobs import launch_docling_batch_background
        root = get_project_root()
        job_id, total = launch_docling_batch_background(
            root,
            concurrency=concurrency,
            force=force,
            filter_glob=filter_glob or None,
        )
        return json_dict({
            "background": True,
            "job_id": job_id,
            "status": "running",
            "total_pending": total,
            "concurrency": concurrency,
            "hint": "Use biblio_docling_status(job_id) to check progress.",
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


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
        # Auto-chain ref-md if Docling markdown already exists (checks pool too)
        try:
            from biblio.docling import resolve_docling_outputs
            from biblio.ref_md import run_ref_md_for_key
            docling_out, docling_src = resolve_docling_outputs(cfg, citekey)
            if docling_src != "missing" and docling_out.md_path.exists():
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


def biblio_pdf_validate(fix: bool = False) -> JsonDict:
    """Scan bib/articles/ for files that aren't valid PDFs (HTML paywall pages, etc.).

    Returns per-file validation results. Invalid files are typically HTML
    paywall/login pages that were saved as .pdf before the content-type check
    was added.

    Args:
        fix: If True, delete invalid files so they can be re-fetched
             with ``biblio_pdf_fetch_oa()``.
    """
    if not _biblio_available():
        return _unavailable("biblio_pdf_validate")
    root = get_project_root()
    try:
        from biblio.mcp import pdf_validate
        return json_dict(pdf_validate(root=root, fix=fix))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_library_quality() -> JsonDict:
    """Scan the merged bibliography for entry quality issues.

    Returns per-tier counts (good/sparse/stub/noise) and lists of problematic
    entries with specific issues. Noise entries are garbage (e.g. title="Abstract"),
    stubs have too few fields to be useful.
    """
    if not _biblio_available():
        return _unavailable("biblio_library_quality")
    root = get_project_root()
    try:
        from biblio.mcp import library_quality
        return json_dict(library_quality(root=root))
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


# --- Discovery tools ---


def biblio_discover_authors(
    query: str = "",
    author_id: str = "",
    orcid: str = "",
) -> JsonDict:
    """Search for authors by name, OpenAlex ID, or ORCID.

    Provide exactly one of the three parameters. Name search returns ranked
    candidates; ID/ORCID lookups return a single author profile.

    Args:
        query: Author name to search (e.g. "György Buzsáki").
        author_id: OpenAlex author ID (e.g. "A5023888391").
        orcid: ORCID identifier.
    """
    if not _biblio_available():
        return _unavailable("biblio_discover_authors")
    root = get_project_root()
    try:
        from biblio.mcp import discover_authors
        return json_dict(discover_authors(
            root=root,
            query=query or None,
            author_id=author_id or None,
            orcid=orcid or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_discover_institutions(
    query: str = "",
    institution_id: str = "",
) -> JsonDict:
    """Search for institutions by name or fetch by OpenAlex ID.

    Returns ranked candidates with country, type (education/facility/...),
    and publication metrics.

    Args:
        query: Institution name to search (e.g. "LMU Munich", "NYU").
        institution_id: OpenAlex institution ID (e.g. "I57206974").
    """
    if not _biblio_available():
        return _unavailable("biblio_discover_institutions")
    root = get_project_root()
    try:
        from biblio.mcp import discover_institutions
        return json_dict(discover_institutions(
            root=root,
            query=query or None,
            institution_id=institution_id or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_institution_works(
    institution_id: str,
    since_year: int | None = None,
    min_citations: int | None = None,
) -> JsonDict:
    """Fetch all works affiliated with an institution.

    Cross-references against the local library to flag already-ingested papers.

    Args:
        institution_id: OpenAlex institution ID (from biblio_discover_institutions).
        since_year: Only include works from this year onward.
        min_citations: Minimum citation count filter.
    """
    if not _biblio_available():
        return _unavailable("biblio_institution_works")
    root = get_project_root()
    try:
        from biblio.mcp import institution_works
        return json_dict(institution_works(
            root=root,
            institution_id=institution_id,
            since_year=since_year,
            min_citations=min_citations,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_institution_authors(
    institution_id: str,
    min_works: int | None = None,
) -> JsonDict:
    """Fetch authors affiliated with an institution (last known affiliation).

    Returns authors ranked by publication count. Use min_works to filter
    to active researchers.

    Args:
        institution_id: OpenAlex institution ID (from biblio_discover_institutions).
        min_works: Only include authors with at least this many publications.
    """
    if not _biblio_available():
        return _unavailable("biblio_institution_authors")
    root = get_project_root()
    try:
        from biblio.mcp import institution_authors
        return json_dict(institution_authors(
            root=root,
            institution_id=institution_id,
            min_works=min_works,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_author_papers(
    author_id: str = "",
    orcid: str = "",
    position: str = "",
    since_year: int | None = None,
    min_citations: int | None = None,
) -> JsonDict:
    """Fetch works by an author with optional position filtering.

    Provide ``author_id`` (OpenAlex ID) or ``orcid`` to identify the author.
    Use ``position`` to filter by authorship position:
    - "last" = PI/senior author papers (lab output)
    - "first" = first-author papers
    - "middle" = middle-author collaborations

    Args:
        author_id: OpenAlex author ID (e.g. "A5023888391").
        orcid: ORCID identifier (alternative to author_id).
        position: Filter by author position: "first", "middle", or "last".
        since_year: Only include works from this year onward.
        min_citations: Minimum citation count filter.
    """
    if not _biblio_available():
        return _unavailable("biblio_author_papers")
    root = get_project_root()
    try:
        from biblio.mcp import author_works_by_position
        return json_dict(author_works_by_position(
            root=root,
            author_id=author_id or None,
            orcid=orcid or None,
            position=position or None,
            since_year=since_year,
            min_citations=min_citations,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_pool_promote(
    citekeys: list[str],
    target: str = "",
    dry_run: bool = False,
) -> JsonDict:
    """Promote project-local papers into a shared pool.

    Copies PDFs, derivatives (docling, grobid, openalex), and BibTeX entries
    from the project into the configured pool. Replaces local PDFs with
    symlinks to the pool copies so other projects can access them.

    Args:
        citekeys: List of BibTeX citekeys to promote.
        target: Pool path override (default: pool.path from biblio.yml).
        dry_run: Report what would happen without writing.
    """
    if not _biblio_available():
        return _unavailable("biblio_pool_promote")
    root = get_project_root()
    try:
        from biblio.mcp import pool_promote
        return json_dict(pool_promote(
            citekeys=citekeys,
            root=root,
            target=target,
            dry_run=dry_run,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc), "citekeys": citekeys})


def biblio_zotero_pull(
    collection: str = "",
    tags: list[str] | None = None,
    dry_run: bool = False,
) -> JsonDict:
    """Pull items and PDFs from Zotero into the biblio workspace.

    Performs incremental sync using Zotero's version tracking. Downloads
    metadata as BibTeX to bib/srcbib/zotero.bib and PDFs to bib/articles/.
    Requires a ``zotero`` section in biblio.yml with at least ``library_id``.

    Args:
        collection: Zotero collection key to pull (overrides config).
        tags: Only pull items with these tags.
        dry_run: Report what would happen without writing.
    """
    if not _biblio_available():
        return _unavailable("biblio_zotero_pull")
    root = get_project_root()
    try:
        from biblio.mcp import zotero_pull
        return json_dict(zotero_pull(
            root=root,
            collection=collection or None,
            tags=tags,
            dry_run=dry_run,
        ))
    except ImportError as exc:
        return json_dict({"error": f"pyzotero required: {exc}"})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_zotero_status() -> JsonDict:
    """Show Zotero sync state — last sync time, item counts, library info.

    Requires a ``zotero`` section in biblio.yml.
    """
    if not _biblio_available():
        return _unavailable("biblio_zotero_status")
    root = get_project_root()
    try:
        from biblio.mcp import zotero_status
        return json_dict(zotero_status(root=root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_enrich(
    citekeys: list[str] | None = None,
    force: bool = False,
) -> JsonDict:
    """Run OpenAlex enrichment: persist topics, keywords, type, and retraction
    status per citekey from resolved.jsonl.

    Writes per-citekey YAML to ``bib/derivatives/openalex/{citekey}.yml``
    and builds a cross-paper topic index.

    Args:
        citekeys: Only enrich these citekeys (default: all resolved papers).
        force: Overwrite existing enrichment files.
    """
    if not _biblio_available():
        return _unavailable("biblio_enrich")
    root = get_project_root()
    try:
        from biblio.mcp import enrich
        return json_dict(enrich(root=root, citekeys=citekeys, force=force))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_enrich_topic_tags(
    citekeys: list[str] | None = None,
    dry_run: bool = False,
) -> JsonDict:
    """Populate library.yml tags from OpenAlex enrichment data.

    Maps OpenAlex topics/keywords to ``oa:``-prefixed tags and adds them
    to library.yml entries (union merge — never removes existing tags).

    Args:
        citekeys: Only process these citekeys (default: all in library).
        dry_run: Report changes without writing.
    """
    if not _biblio_available():
        return _unavailable("biblio_enrich_topic_tags")
    root = get_project_root()
    try:
        from biblio.mcp import enrich_topic_tags
        return json_dict(enrich_topic_tags(root=root, citekeys=citekeys, dry_run=dry_run))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def biblio_zotero_push(
    citekeys: list[str] | None = None,
    push_tags: bool = True,
    push_notes: bool = False,
    push_ids: bool = True,
    force: bool = False,
    dry_run: bool = False,
) -> JsonDict:
    """Push biblio enrichments (tags, notes, DOI/OpenAlex IDs) back to Zotero.

    Writes biblio-generated tags with ``biblio:`` prefix, optionally creates
    child notes from LLM summaries, and fills in missing DOI/OpenAlex IDs.
    Uses optimistic concurrency — skips items modified in Zotero since last sync
    unless ``force`` is True. Requires a ``zotero`` section in biblio.yml.

    Args:
        citekeys: Push only these citekeys (default: all synced items).
        push_tags: Push autotag/concept/status tags to Zotero.
        push_notes: Create Zotero child notes from LLM summaries.
        push_ids: Write DOI and OpenAlex ID to Zotero items.
        force: Push even if item was modified in Zotero since last sync.
        dry_run: Report what would happen without writing.
    """
    if not _biblio_available():
        return _unavailable("biblio_zotero_push")
    root = get_project_root()
    try:
        from biblio.mcp import zotero_push
        return json_dict(zotero_push(
            root=root,
            citekeys=citekeys,
            push_tags=push_tags,
            push_notes=push_notes,
            push_ids=push_ids,
            force=force,
            dry_run=dry_run,
        ))
    except ImportError as exc:
        return json_dict({"error": f"pyzotero required: {exc}"})
    except Exception as exc:
        return json_dict({"error": str(exc)})
