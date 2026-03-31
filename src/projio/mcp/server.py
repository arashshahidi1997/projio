"""FastMCP stdio server — registers all projio tools."""
from __future__ import annotations

from fastmcp import FastMCP

from . import biblio, codio, context, datalad, manuscripto, notio, pipeio, rag, site as site_mcp

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
def indexio_build_tool(sources: list[str] = [], background: bool = False, update: bool = False):
    """Rebuild the search index. Full rebuild by default, or partial if sources specified.
    Set background=True to return immediately with a job_id for progress polling via indexio_build_status.
    Set update=True to auto-detect new/changed sources and only rebuild those (incremental mode)."""
    return rag.indexio_build(sources=sources or None, background=background, update=update)


@server.tool("indexio_build_status")
def indexio_build_status_tool(job_id: str):
    """Check progress of a background indexio_build job. Shows sources completed/total,
    current source being processed, elapsed time, and final result when done."""
    return rag.indexio_build_status(job_id=job_id)


@server.tool("indexio_status")
def indexio_status_tool():
    """Per-source index status with change detection. Shows files/chars/chunks per source,
    state (indexed/changed/not_yet_built/missing_files/empty_match), and actionable source IDs."""
    return rag.indexio_status()


@server.tool("indexio_sources_list")
def indexio_sources_list_tool():
    """List sources registered in the indexio config with last-build stats (files/chars/chunks)."""
    return rag.indexio_sources_list()


@server.tool("indexio_sources_sync")
def indexio_sources_sync_tool(build: bool = False, sources_filter: list[str] = []):
    """Sync all subsystem sources (biblio, codio) into the indexio config, then optionally rebuild.
    Calls biblio_rag_sync + codio_rag_sync. Set build=True to also trigger indexio_build."""
    return rag.indexio_sources_sync(build=build, sources_filter=sources_filter or None)


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
def biblio_docling_tool(citekey: str, force: bool = False, background: bool = False):
    """Run Docling on a paper's PDF to extract full text as markdown.
    Set background=True to return immediately with a job_id for polling via biblio_docling_status."""
    return biblio.biblio_docling(citekey=citekey, force=force, background=background)


@server.tool("biblio_docling_status")
def biblio_docling_status_tool(job_id: str):
    """Check the status of a background biblio_docling job. Returns status, result, or error."""
    return biblio.biblio_docling_status(job_id=job_id)


@server.tool("biblio_grobid")
def biblio_grobid_tool(citekey: str, force: bool = False):
    """Run GROBID on a paper's PDF to extract structured header and references."""
    return biblio.biblio_grobid(citekey=citekey, force=force)


@server.tool("biblio_grobid_check")
def biblio_grobid_check_tool():
    """Check whether the GROBID server is reachable."""
    return biblio.biblio_grobid_check()


@server.tool("biblio_rag_sync")
def biblio_rag_sync_tool(force_init: bool = False):
    """Register biblio docling sources into the indexio config. Run indexio_build after."""
    return biblio.biblio_rag_sync(force_init=force_init)


@server.tool("biblio_graph_expand")
def biblio_graph_expand_tool(
    citekeys: list[str] = [],
    direction: str = "references",
    merge: bool = True,
    force: bool = False,
):
    """Expand the OpenAlex reference graph from resolved seed records.
    Discovers references/citing works for seed papers and writes graph_candidates.json."""
    return biblio.biblio_graph_expand(
        citekeys=citekeys or None,
        direction=direction,
        merge=merge,
        force=force,
    )


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
def note_read_tool(path: str = "", note_id: str = "", note_type: str = ""):
    """Read a note by relative path (from note_list) or by note_id (timestamp/capture ID).

    Args:
        path: Relative path returned by note_list (e.g. 'docs/log/idea/idea-arash-...md').
        note_id: Timestamp ID, capture ID, or filename fragment (alternative to path).
        note_type: Optional note type hint (e.g. 'idea', 'issue') — used with note_id
            to narrow the search to a specific type folder.
    """
    return notio.note_read(path=path, note_id=note_id, note_type=note_type)


@server.tool("note_resolve")
def note_resolve_tool(note_id: str):
    """Resolve a note by timestamp ID, capture ID, or filename fragment."""
    return notio.note_resolve(note_id=note_id)


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


@server.tool("notio_reindex")
def notio_reindex_tool(note_type: str = ""):
    """Regenerate index.md files for note type directories. Empty note_type = all types."""
    return notio.notio_reindex(note_type=note_type)


# --- Manuscript tools ---

@server.tool("manuscript_init")
def manuscript_init_tool(name: str, template: str = "generic"):
    """Scaffold a new manuscript with default sections."""
    return manuscripto.manuscript_init(name=name, template=template)


@server.tool("manuscript_list")
def manuscript_list_tool():
    """List all manuscripts in the project."""
    return manuscripto.manuscript_list()


@server.tool("manuscript_status")
def manuscript_status_tool(name: str):
    """Show manuscript sections, figures, and completion status."""
    return manuscripto.manuscript_status(name=name)


@server.tool("manuscript_build")
def manuscript_build_tool(name: str, format: str = "pdf"):
    """Assemble sections and render to PDF/LaTeX/Markdown."""
    return manuscripto.manuscript_build(name=name, format=format)


@server.tool("manuscript_validate")
def manuscript_validate_tool(name: str):
    """Validate citations, figures, sections, and pandoc availability."""
    return manuscripto.manuscript_validate(name=name)


@server.tool("manuscript_assemble")
def manuscript_assemble_tool(name: str):
    """Generate assembled markdown without rendering."""
    return manuscripto.manuscript_assemble(name=name)


@server.tool("manuscript_figure_insert")
def manuscript_figure_insert_tool(name: str, section: str, figure_id: str, position: str = "end"):
    """Insert a figio figure reference into a manuscript section."""
    return manuscripto.manuscript_figure_insert(name=name, section=section, figure_id=figure_id, position=position)


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


@server.tool("codio_rag_sync")
def codio_rag_sync_tool(force_init: bool = False):
    """Register codio library sources (notes, catalog, src trees) into the indexio config.

    The target indexio config path is read from ``indexio.config`` in ``.projio/config.yml``
    (defaults to ``.projio/indexio/config.yaml``). Source-tree globs are language-dependent:
    Python → ``**/*.py``, MATLAB → ``**/*.m``, unknown languages → ``**/*``. After sync,
    run ``indexio_build`` to index the registered sources.
    """
    return codio.codio_rag_sync(force_init=force_init)


@server.tool("codio_add")
def codio_add_tool(
    name: str,
    kind: str,
    path: str = "",
    language: str = "",
    repo_url: str = "",
    pip_name: str = "",
    license: str = "",
    summary: str = "",
    capabilities: list[str] = [],
    priority: str = "tier2",
    runtime_import: str = "reference_only",
    status: str = "active",
):
    """Register a library into the codio registry with catalog + profile metadata."""
    return codio.codio_add(
        name=name, kind=kind, path=path, language=language,
        repo_url=repo_url, pip_name=pip_name, license=license, summary=summary,
        capabilities=capabilities or None, priority=priority,
        runtime_import=runtime_import, status=status,
    )


@server.tool("codio_func_doc")
def codio_func_doc_tool(package: str, module: str, function: str = "", env: str = ""):
    """Live introspection of an installed Python package. Returns function signatures and docstrings.
    If function is given, returns that function's full signature and docstring.
    If omitted, lists all public functions with signatures and first-line docstrings (browsing mode).
    Set env to a conda environment name to introspect packages in that env (e.g. "cogpy")."""
    return codio.codio_func_doc(package=package, module=module, function=function or None, env=env or None)


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
def pipeio_nb_status_tool(pipe: str = "", flow: str = "", name: str = ""):
    """Show notebook sync and publication status. Optionally filter by pipe, flow, or name."""
    return pipeio.pipeio_nb_status(pipe=pipe, flow=flow, name=name)


@server.tool("pipeio_nb_update")
def pipeio_nb_update_tool(
    pipe: str,
    flow: str,
    name: str,
    status: str = "",
    description: str = "",
    kind: str = "",
):
    """Update notebook metadata (status, description, kind) in notebook.yml.

    status: draft/active/stale/promoted/archived.
    kind: investigate/explore/demo/validate."""
    return pipeio.pipeio_nb_update(
        pipe=pipe, flow=flow, name=name,
        status=status, description=description, kind=kind,
    )


@server.tool("pipeio_mod_list")
def pipeio_mod_list_tool(pipe: str, flow: str = ""):
    """List mods (logical modules) for a pipeline flow."""
    return pipeio.pipeio_mod_list(pipe=pipe, flow=flow)


@server.tool("pipeio_mod_resolve")
def pipeio_mod_resolve_tool(modkeys: list[str]):
    """Resolve modkeys (pipe-X_flow-Y_mod-Z) into metadata and doc locations."""
    return pipeio.pipeio_mod_resolve(modkeys=modkeys)


@server.tool("pipeio_mod_context")
def pipeio_mod_context_tool(pipe: str, flow: str = "", mod: str = ""):
    """Bundled read context for a mod: rules, scripts, doc, config params, bids signatures.

    Returns everything needed to understand and work on a mod in one MCP call."""
    return pipeio.pipeio_mod_context(pipe=pipe, flow=flow, mod=mod)


@server.tool("pipeio_registry_scan")
def pipeio_registry_scan_tool():
    """Scan filesystem for pipelines and rebuild the registry (auto-discovery)."""
    return pipeio.pipeio_registry_scan()


@server.tool("pipeio_modkey_bib")
def pipeio_modkey_bib_tool(output_path: str = "", project_name: str = ""):
    """Generate modkey.bib with @misc entries for all pipeline mods (for manuscript citations)."""
    return pipeio.pipeio_modkey_bib(output_path=output_path, project_name=project_name)


@server.tool("pipeio_docs_collect")
def pipeio_docs_collect_tool():
    """Collect flow-local docs and notebooks into docs/pipelines/ for MkDocs."""
    return pipeio.pipeio_docs_collect()


@server.tool("pipeio_docs_nav")
def pipeio_docs_nav_tool():
    """Generate MkDocs nav YAML fragment for collected pipeline docs."""
    return pipeio.pipeio_docs_nav()


@server.tool("pipeio_contracts_validate")
def pipeio_contracts_validate_tool():
    """Validate I/O contracts for all flows (config, dirs, registry groups)."""
    return pipeio.pipeio_contracts_validate()


@server.tool("pipeio_nb_create")
def pipeio_nb_create_tool(
    pipe: str,
    flow: str,
    name: str,
    kind: str = "investigate",
    description: str = "",
):
    """Scaffold a new notebook for a pipeline flow with bootstrap cells."""
    return pipeio.pipeio_nb_create(
        pipe=pipe, flow=flow, name=name,
        kind=kind, description=description,
    )


@server.tool("pipeio_nb_sync")
def pipeio_nb_sync_tool(
    pipe: str,
    flow: str,
    name: str,
    formats: list[str] = [],
    direction: str = "py2nb",
    force: bool = False,
):
    """Sync a notebook via jupytext. direction='py2nb' (default) regenerates
    .ipynb/.md from .py; direction='nb2py' updates .py from the .ipynb
    (use after human edits). Skips up-to-date files unless force=True."""
    return pipeio.pipeio_nb_sync(
        pipe=pipe, flow=flow, name=name,
        formats=formats or None,
        direction=direction, force=force,
    )


@server.tool("pipeio_nb_publish")
def pipeio_nb_publish_tool(pipe: str, flow: str, name: str):
    """Publish a notebook's myst markdown to the docs tree."""
    return pipeio.pipeio_nb_publish(pipe=pipe, flow=flow, name=name)


@server.tool("pipeio_nb_analyze")
def pipeio_nb_analyze_tool(pipe: str, flow: str, name: str):
    """Analyze a notebook's static structure: imports, RunCard fields, PipelineContext
    usage, section headers, and cogpy function calls."""
    return pipeio.pipeio_nb_analyze(pipe=pipe, flow=flow, name=name)


@server.tool("pipeio_nb_diff")
def pipeio_nb_diff_tool(pipe: str, flow: str, name: str):
    """Show sync state between .py and .ipynb: which is newer, whether in sync,
    and the recommended sync direction. Call before nb_sync to decide direction."""
    return pipeio.pipeio_nb_diff(pipe=pipe, flow=flow, name=name)


@server.tool("pipeio_nb_lab")
def pipeio_nb_lab_tool(pipe: str = "", flow: str = "", sync: bool = False):
    """Build/refresh Jupyter Lab symlink manifest in .projio/pipeio/lab/.
    Creates symlinks to active .ipynb notebooks. Pass sync=True to sync py→ipynb first.
    Returns manifest state (linked notebooks, lab_dir)."""
    return pipeio.pipeio_nb_lab(pipe=pipe, flow=flow, sync=sync)


@server.tool("pipeio_nb_scan")
def pipeio_nb_scan_tool(register: bool = False):
    """Scan for unregistered percent-format .py notebooks in notebooks/ directories.
    Pass register=True to auto-add them to notebook.yml."""
    return pipeio.pipeio_nb_scan(register=register)


@server.tool("pipeio_nb_read")
def pipeio_nb_read_tool(pipe: str, flow: str, name: str):
    """Read a notebook's .py content with metadata, sync state, and structural
    analysis (sections, imports, RunCard, cogpy calls) in a single call."""
    return pipeio.pipeio_nb_read(pipe=pipe, flow=flow, name=name)


@server.tool("pipeio_nb_audit")
def pipeio_nb_audit_tool():
    """Audit all notebooks: staleness, config completeness, mod coverage gaps.
    Returns per-notebook issues and flow-level coverage report."""
    return pipeio.pipeio_nb_audit()


@server.tool("pipeio_nb_pipeline")
def pipeio_nb_pipeline_tool(
    pipe: str,
    flow: str,
    name: str,
    formats: list[str] = [],
    build_site: bool = False,
):
    """Composite notebook publish: sync → publish → docs_collect → docs_nav in one call.
    Optionally triggers site_build at the end."""
    return pipeio.pipeio_nb_pipeline(
        pipe=pipe, flow=flow, name=name,
        formats=formats or None,
        build_site=build_site,
    )


@server.tool("pipeio_mkdocs_nav_patch")
def pipeio_mkdocs_nav_patch_tool():
    """Apply pipeio docs nav fragment to mkdocs.yml (find/replace Pipelines section)."""
    return pipeio.pipeio_mkdocs_nav_patch()


@server.tool("pipeio_rule_list")
def pipeio_rule_list_tool(pipe: str, flow: str = ""):
    """List Snakemake rules for a flow with input/output signatures and mod membership.

    Parses the Snakefile (and .smk includes) and returns structured metadata
    per rule: name, input/output/params dicts of {name: raw_expression},
    script path, and which mod the rule belongs to."""
    return pipeio.pipeio_rule_list(pipe=pipe, flow=flow)


@server.tool("pipeio_rule_stub")
def pipeio_rule_stub_tool(
    pipe: str,
    flow: str,
    rule_name: str,
    inputs: dict = {},
    outputs: dict = {},
    params: dict = {},
    script: str = "",
):
    """Generate a syntactically correct Snakemake rule stub from a contract spec.

    Returns formatted rule text for human review (not auto-inserted).
    inputs: {name: bids_pattern} or {name: {source_rule, member}}.
    outputs: {name: bids_kwargs_dict} or {name: bids_pattern_str}.
    params: {name: config_dot_path} e.g. {"ttl_freq": "ttl_removal.ttl_freq"}."""
    return pipeio.pipeio_rule_stub(
        pipe=pipe,
        flow=flow,
        rule_name=rule_name,
        inputs=inputs or None,
        outputs=outputs or None,
        params=params or None,
        script=script,
    )


@server.tool("pipeio_rule_insert")
def pipeio_rule_insert_tool(
    pipe: str,
    flow: str = "",
    rule_name: str = "",
    rule_text: str = "",
    target_file: str = "",
    after_rule: str = "",
    inputs: dict = {},
    outputs: dict = {},
    params: dict = {},
    script: str = "",
):
    """Insert a Snakemake rule into the correct .smk or Snakefile.

    Provide rule_text directly, or inputs/outputs/params/script to generate it.
    Auto-selects the target file by mod prefix if not specified.
    after_rule: insert after this rule (appends at end if omitted)."""
    return pipeio.pipeio_rule_insert(
        pipe=pipe,
        flow=flow,
        rule_name=rule_name,
        rule_text=rule_text,
        target_file=target_file,
        after_rule=after_rule,
        inputs=inputs or None,
        outputs=outputs or None,
        params=params or None,
        script=script,
    )


@server.tool("pipeio_rule_update")
def pipeio_rule_update_tool(
    pipe: str,
    flow: str = "",
    rule_name: str = "",
    add_inputs: dict = {},
    add_outputs: dict = {},
    add_params: dict = {},
    set_script: str = "",
    apply: bool = False,
):
    """Patch an existing Snakemake rule by merging new sections.

    Adds entries to input/output/params without overwriting existing ones.
    Returns a unified diff preview; set apply=True to write the patched file.
    add_inputs/add_outputs: {name: spec}. add_params: {name: config_dot_path}."""
    return pipeio.pipeio_rule_update(
        pipe=pipe,
        flow=flow,
        rule_name=rule_name,
        add_inputs=add_inputs or None,
        add_outputs=add_outputs or None,
        add_params=add_params or None,
        set_script=set_script,
        apply=apply,
    )


@server.tool("pipeio_config_read")
def pipeio_config_read_tool(pipe: str, flow: str = ""):
    """Read and parse a flow's config.yml with YAML anchor resolution and bids() signature mapping.

    Returns pybids_inputs, registry groups (with resolved members), _member_sets anchors,
    params, and a bids_signatures dict showing the effective bids() call per group+member."""
    return pipeio.pipeio_config_read(pipe=pipe, flow=flow)


@server.tool("pipeio_config_patch")
def pipeio_config_patch_tool(
    pipe: str,
    flow: str = "",
    registry_entry: dict = {},
    params_entry: dict = {},
    apply: bool = False,
):
    """Validate and optionally patch a flow's config.yml.

    Checks base_input against pybids_inputs, validates member suffix/extension schema,
    and returns a unified diff preview. Set apply=True to write the patched file.
    registry_entry: {group_name: group_dict} to add/replace in registry:.
    params_entry: {section: {key: value}} to update in top-level params."""
    return pipeio.pipeio_config_patch(
        pipe=pipe,
        flow=flow,
        registry_entry=registry_entry or None,
        params_entry=params_entry or None,
        apply=apply,
    )


@server.tool("pipeio_config_init")
def pipeio_config_init_tool(
    pipe: str,
    flow: str = "",
    input_dir: str = "",
    output_dir: str = "",
    pybids_inputs: dict = {},
    registry_groups: dict = {},
    params: dict = {},
):
    """Scaffold a new flow's config.yml with pybids_inputs and registry structure.

    Creates a well-structured config.yml for a flow that doesn't have one yet.
    Use config_patch to modify an existing config. Validates registry_groups schema.
    output_registry auto-set to {output_dir}/pipe-{pipe}_flow-{flow}_registry.yml."""
    return pipeio.pipeio_config_init(
        pipe=pipe,
        flow=flow,
        input_dir=input_dir,
        output_dir=output_dir,
        pybids_inputs=pybids_inputs or None,
        registry_groups=registry_groups or None,
        params=params or None,
    )


@server.tool("pipeio_registry_validate")
def pipeio_registry_validate_tool():
    """Validate pipeline registry consistency (code vs docs, config schema)."""
    return pipeio.pipeio_registry_validate()


@server.tool("pipeio_mod_create")
def pipeio_mod_create_tool(
    pipe: str,
    flow: str,
    mod: str,
    description: str = "",
    from_notebook: str = "",
    inputs: dict = {},
    outputs: dict = {},
    params_spec: dict = {},
    use_pipeline_context: bool = False,
):
    """Scaffold a new pipeline mod: scripts/<mod>.py skeleton + docs/mod-<mod>.md stub.

    When inputs/outputs/params_spec provided, generates Snakemake I/O unpacking
    and parameter binding so only processing logic needs filling in.
    inputs/outputs/params_spec: {var_name: description} for snakemake.input/output/params.
    use_pipeline_context: generate PipelineContext setup boilerplate."""
    return pipeio.pipeio_mod_create(
        pipe=pipe, flow=flow, mod=mod,
        description=description, from_notebook=from_notebook or None,
        inputs=inputs or None, outputs=outputs or None,
        params_spec=params_spec or None,
        use_pipeline_context=use_pipeline_context,
    )


@server.tool("pipeio_nb_exec")
def pipeio_nb_exec_tool(
    pipe: str,
    flow: str,
    name: str,
    params: dict = {},
    timeout: int = 600,
):
    """Execute a notebook via papermill with optional RunCard parameter overrides.
    Syncs py → ipynb first, returns status/errors/output path/elapsed time."""
    return pipeio.pipeio_nb_exec(
        pipe=pipe, flow=flow, name=name,
        params=params or None, timeout=timeout,
    )


@server.tool("pipeio_dag_export")
def pipeio_dag_export_tool(
    pipe: str,
    flow: str = "",
    graph_type: str = "rulegraph",
    output_format: str = "dot",
):
    """Export rule/job DAG via snakemake's native graph output.
    graph_type: rulegraph (compact), dag (full jobs), d3dag (JSON).
    output_format: dot, mermaid, svg (needs graphviz), json (d3dag only)."""
    return pipeio.pipeio_dag_export(
        pipe=pipe, flow=flow,
        graph_type=graph_type, output_format=output_format,
    )


@server.tool("pipeio_report")
def pipeio_report_tool(
    pipe: str,
    flow: str = "",
    output_path: str = "",
    target: str = "",
):
    """Generate snakemake HTML report with runtime stats, provenance, and annotated outputs.
    target: rule to run first (e.g. "report" for flows with partial outputs)."""
    return pipeio.pipeio_report(
        pipe=pipe, flow=flow,
        output_path=output_path, target=target,
    )


@server.tool("pipeio_target_paths")
def pipeio_target_paths_tool(
    pipe: str,
    flow: str = "",
    group: str = "",
    member: str = "",
    entities: dict[str, str] | None = None,
    expand: bool = False,
):
    """Resolve output paths for a flow's registry entries.
    Three modes: (1) no group → list groups/members/patterns,
    (2) group+member+entities → resolve single path,
    (3) expand=True → glob all matching paths filtered by entities."""
    return pipeio.pipeio_target_paths(
        pipe=pipe, flow=flow, group=group, member=member,
        entities=entities, expand=expand,
    )


@server.tool("pipeio_completion")
def pipeio_completion_tool(pipe: str, flow: str = "", mod: str = ""):
    """Check per-session completion: compare expected outputs (from registry) against filesystem.
    Reports complete/partial/missing sessions per registry group."""
    return pipeio.pipeio_completion(pipe=pipe, flow=flow, mod=mod)


@server.tool("pipeio_cross_flow")
def pipeio_cross_flow_tool(pipe: str = "", flow: str = ""):
    """Map output_registry → input_registry chains across flows.
    Shows which flows consume which outputs, detects stale references."""
    return pipeio.pipeio_cross_flow(pipe=pipe, flow=flow)


@server.tool("pipeio_log_parse")
def pipeio_log_parse_tool(pipe: str, flow: str = "", run_id: str = "", log_path: str = ""):
    """Extract structured data from Snakemake logs: completed rules with timing,
    failed rules with error summaries, resource warnings, missing inputs."""
    return pipeio.pipeio_log_parse(pipe=pipe, flow=flow, run_id=run_id, log_path=log_path)


@server.tool("pipeio_run")
def pipeio_run_tool(
    pipe: str,
    flow: str = "",
    targets: list[str] = [],
    cores: int = 1,
    dryrun: bool = False,
    use_conda: bool = False,
    extra_args: list[str] = [],
    wildcards: dict[str, str] | None = None,
):
    """Launch Snakemake in a detached screen session. State tracked in .pipeio/runs.json.
    Returns run_id and screen session name for later status queries.
    use_conda: pass --use-conda to snakemake (use conda envs defined in rules).
    wildcards: entity filters for scoping (e.g. {"subject": "01", "session": "04"}) → --filter-{key} {value}."""
    return pipeio.pipeio_run(
        pipe=pipe, flow=flow,
        targets=targets or None, cores=cores, dryrun=dryrun,
        use_conda=use_conda,
        extra_args=extra_args or None,
        wildcards=wildcards,
    )


@server.tool("pipeio_run_status")
def pipeio_run_status_tool(run_id: str = "", pipe: str = "", flow: str = ""):
    """Query progress of running or recent Snakemake runs.
    Checks screen sessions alive, parses log tails for completion percentage."""
    return pipeio.pipeio_run_status(run_id=run_id, pipe=pipe, flow=flow)


@server.tool("pipeio_run_dashboard")
def pipeio_run_dashboard_tool():
    """Rich summary of all tracked Snakemake runs: active/completed/failed per flow."""
    return pipeio.pipeio_run_dashboard()


@server.tool("pipeio_run_kill")
def pipeio_run_kill_tool(run_id: str):
    """Gracefully stop a running Snakemake screen session by run_id."""
    return pipeio.pipeio_run_kill(run_id=run_id)


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


@server.tool("module_context")
def module_context_tool(doc_path: str):
    """Extract structured sections (goal, assumptions, parameters, IO, limitations) from a markdown document."""
    return context.module_context(doc_path=doc_path)


@server.tool("skill_read")
def skill_read_tool(name: str):
    """Read a skill's full content by name. Returns metadata and markdown body.
    Use agent_instructions() first to see available skills, then skill_read() to get one."""
    return context.skill_read(name=name)


# --- Site tools ---

@server.tool("site_build")
def site_build_tool(framework: str = "", strict: bool = False):
    """Build the doc site (mkdocs build / sphinx-build / vite build)."""
    return site_mcp.site_build(
        framework=framework or None,
        strict=strict,
    )


@server.tool("site_deploy")
def site_deploy_tool(target: str = "gitlab"):
    """Deploy the doc site by pushing to the configured pages sibling."""
    return site_mcp.site_deploy(target=target)


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


# --- DataLad tools ---

@server.tool("datalad_status")
def datalad_status_tool(recursive: bool = True, dataset: str = ""):
    """Show datalad status for the project dataset or a subdataset.

    Args:
        recursive: Include subdatasets (default True).
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
    """
    return datalad.datalad_status(recursive=recursive, dataset=dataset)


@server.tool("datalad_save")
def datalad_save_tool(message: str = "Update", recursive: bool = True, dataset: str = "", path: str = ""):
    """Save changes in the project dataset or a subdataset (datalad save).

    Args:
        message: Commit message.
        recursive: Include subdatasets (default True).
        dataset: Relative path to a subdataset (e.g. 'packages/pipeio'). Empty = project root.
        path: Specific path(s) to save (space-separated). Empty = all changes.
    """
    return datalad.datalad_save(message=message, recursive=recursive, dataset=dataset, path=path)


@server.tool("datalad_push")
def datalad_push_tool(sibling: str = "", dataset: str = ""):
    """Push the project dataset (or subdataset) to a sibling.

    Args:
        sibling: Sibling name. Defaults to push_sibling from config (typically 'github' or 'gitlab').
        dataset: Relative path to a subdataset. Empty = project root.
    """
    if not sibling:
        from projio.config import load_effective_config
        try:
            cfg = load_effective_config(".")
            sibling = cfg.get("push_sibling") or cfg.get("datalad_remote") or "github"
        except Exception:
            sibling = "github"
    return datalad.datalad_push(sibling=sibling, dataset=dataset)


@server.tool("datalad_pull")
def datalad_pull_tool(sibling: str = "origin", dataset: str = ""):
    """Pull (update + merge) from a datalad sibling.

    Args:
        sibling: Sibling name (default 'origin').
        dataset: Relative path to a subdataset. Empty = project root.
    """
    return datalad.datalad_pull(sibling=sibling, dataset=dataset)


@server.tool("datalad_siblings")
def datalad_siblings_tool(dataset: str = ""):
    """List configured datalad siblings for the project dataset or a subdataset.

    Args:
        dataset: Relative path to a subdataset. Empty = project root.
    """
    return datalad.datalad_siblings(dataset=dataset)


@server.tool("git_status")
def git_status_tool():
    """Per-project git state: branch, staged/unstaged/untracked files, clean flag."""
    return datalad.git_status()


def main() -> None:
    """Run the MCP server over stdio."""
    server.run()


if __name__ == "__main__":
    main()
