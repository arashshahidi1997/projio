# MCP Tools

The projio MCP server exposes tools across eight categories. Optional tools require their ecosystem package to be installed.

## RAG tools (via indexio)

### Read

| Tool | Description |
|------|-------------|
| `rag_query(query, corpus="", k=8)` | Semantic search against the project index |
| `rag_query_multi(queries[], corpus="", k=5)` | Multi-query search, deduplicated |
| `corpus_list()` | List indexed corpora with chunk counts |
| `indexio_sources_list()` | List configured index sources with IDs and paths |
| `indexio_status()` | Show current index size, last-build time, and source counts |
| `indexio_build_status(job_id)` | Poll a background indexio_build job by job_id |

### Write

| Tool | Description |
|------|-------------|
| `indexio_build(sources=[], background=false, update=false)` | Rebuild the search index (full or partial by source ID) |
| `indexio_sources_sync(build=false, sources_filter=[])` | Sync all subsystem sources into the index config, then optionally build |

`indexio_build` performs a full index rebuild by default. Pass a list of source IDs for a partial rebuild that only re-indexes the specified sources. Set `background=true` to return a `job_id` immediately and poll with `indexio_build_status`. Set `update=true` for incremental update (add new docs without re-embedding existing ones).

`indexio_sources_sync` discovers biblio, notio, and codio sources, writes them into the indexio config, and optionally triggers a build. Use this after adding new subsystem content or after a full `biblio_rag_sync` / `codio_rag_sync`.

## Bibliography tools (via biblio)

### Read

| Tool | Description |
|------|-------------|
| `citekey_resolve(citekeys[])` | Resolve BibTeX citekeys to metadata |
| `paper_context(citekey)` | Full paper context with docling excerpt |
| `paper_absent_refs(citekey)` | Unresolved GROBID references |
| `library_get(citekey)` | Library ledger status and tags |
| `biblio_docling_status(job_id)` | Poll a background biblio_docling job by job_id |
| `biblio_graph_expand(citekeys[], depth=1, direction="both", filter_status=[])` | Expand citation graph around seed citekeys |

### Write

| Tool | Description |
|------|-------------|
| `biblio_ingest(dois[], tags=[], status="unread", collection="")` | Ingest papers by DOI via OpenAlex, generate citekeys, write BibTeX |
| `biblio_library_set(citekeys[], status="", tags=[], priority="")` | Bulk-update library ledger entries |
| `biblio_merge(dry_run=false)` | Merge source .bib files into bib/main.bib |
| `biblio_docling(citekey, force=false, background=false)` | Extract full text from a paper's PDF via Docling |
| `biblio_grobid(citekey, force=false)` | Extract header and references from a paper's PDF via GROBID |
| `biblio_grobid_check()` | Check whether the GROBID server is reachable |
| `biblio_rag_sync(force_init=false)` | Sync bibliography sources into the search index |

`biblio_ingest` resolves DOIs through the OpenAlex API, generates BibTeX citekeys, appends entries to the import bib file, and optionally sets library metadata and adds papers to a collection. Returns the list of generated citekeys.

`biblio_library_set` updates status (`unread`, `reading`, `processed`, `archived`), tags, and priority (`low`, `normal`, `high`) for multiple citekeys in a single call.

`biblio_merge` folds all `.bib` files from `bib/srcbib/` into the main `bib/main.bib`. Use `dry_run=true` to preview without writing. Run this after `biblio_ingest` to make new entries available to downstream tools.

`biblio_docling` runs the Docling pipeline on a single paper's PDF, producing markdown and JSON extracts. Cached — skips if outputs exist unless `force=true`. Set `background=true` to return a `job_id` for polling via `biblio_docling_status` (useful for large PDFs).

`biblio_grobid` submits a paper's PDF to the GROBID server, extracting structured header metadata and parsed references. Use `biblio_grobid_check` first to verify the server is alive.

`biblio_graph_expand` walks the citation graph starting from seed citekeys. `direction` is `"forward"` (papers they cite), `"backward"` (papers that cite them), or `"both"`. `filter_status` restricts traversal to library entries with those statuses.

`biblio_rag_sync` writes biblio-managed sources (docling extracts, notes) into the indexio source config so they appear in semantic search. Call `indexio_build` afterwards to re-embed.

## Notes tools (via notio)

### Read

| Tool | Description |
|------|-------------|
| `note_list(note_type="", limit=20)` | List recent notes |
| `note_latest(note_type="")` | Most recent note content |
| `note_read(path="", note_id="", note_type="")` | Read a specific note by path, ID, or type |
| `note_resolve(note_id)` | Find a note by timestamp fragment or capture ID |
| `note_types()` | List configured note types and their modes |
| `note_search(query, k=5)` | Semantic search over notes |

### Write

| Tool | Description |
|------|-------------|
| `note_create(note_type, owner="", title="", date="")` | Create a new note from template |
| `note_update(path, fields)` | Update note frontmatter fields (JSON string) |
| `notio_reindex(note_type="")` | Rebuild the note index.md for one or all note types |

`note_create` renders the configured template for the given note type, creates the file, and returns the path. `note_update` parses `fields` as JSON and merges key-value pairs into the note's YAML frontmatter.

`note_resolve` looks up a note by a short timestamp fragment (e.g. `"20260315-142301"`) or a capture ID. Returns the full path for use with `note_read`.

`notio_reindex` regenerates the `index.md` table-of-contents for one note type or all types. Run after bulk note creation or import.

## Manuscript tools (via notio)

### Read

| Tool | Description |
|------|-------------|
| `manuscript_list()` | List all manuscripts in the project |
| `manuscript_status(name)` | Show assembly and build status for a manuscript |
| `manuscript_validate(name)` | Validate manuscript spec against configured sections and figures |

### Write

| Tool | Description |
|------|-------------|
| `manuscript_init(name, template="generic")` | Scaffold a new manuscript directory with spec.yml and section stubs |
| `manuscript_assemble(name)` | Concatenate ordered sections into a single markdown document |
| `manuscript_build(name, format="pdf")` | Run pandoc to render the assembled manuscript to PDF/DOCX/HTML |
| `manuscript_figure_insert(name, section, figure_id, position="end")` | Insert a figio figure reference into a manuscript section |

`manuscript_init` creates `manuscripts/<name>/` with a `spec.yml` (section list, metadata, render config) and empty section stubs. Template choices: `generic`, `paper`, `thesis`.

`manuscript_assemble` reads `spec.yml`, strips frontmatter from each section file, adjusts heading levels, and concatenates them in order into `manuscripts/<name>/assembled.md`.

`manuscript_build` calls pandoc on the assembled document with the render config from `spec.yml`. Supports `pdf` (via LaTeX), `docx`, and `html` formats.

`manuscript_figure_insert` appends or prepends a `![](fig/<figure_id>.*)` reference at the specified position in a section file.

## Presentation tools (via notio.present)

Presentio treats presentation decks as first-class projio artifacts, parallel to manuscripts: a YAML spec + ordered section tree + dual-backend renderer (Marp or reveal.js via pandoc). Decks live under `docs/deliverables/presentations/<name>/` and are iterated section-by-section rather than one-shot-generated.

### Read

| Tool | Description |
|------|-------------|
| `present_list()` | List all decks under `docs/deliverables/presentations/` |
| `present_status(name)` | Per-section state, figure counts, bibliography inheritance, last-built outputs |
| `present_overview(name)` | Rich dashboard: per-section stats, missing/stale citations and figures, slide count estimate |
| `present_section_context(name, section)` | One-call context for drafting a slide section — body, citations, figures, RAG hits, related notes |
| `present_validate(name)` | Structural checks (section files exist, figure ids resolve, citekeys against bib, renderer availability) |
| `present_cite_check(name)` | Cross-check cited keys against the inherited bibliography; report docling fulltext availability; suggest `biblio_ingest` / `biblio_docling` follow-ups |
| `present_diff(name)` | Compare current sections against the last `assembled.md` — per-section word/citation/figure drift plus a full unified diff |

### Write

| Tool | Description |
|------|-------------|
| `present_init(name, format="marp", template="lab-meeting", title="")` | Scaffold a new deck with template-driven section stubs |
| `present_assemble(name)` | Write `build/assembled.md` without calling a renderer |
| `present_build(name, format="")` | Full render pipeline via the backend matching `spec.format` (marp-cli or pandoc `-t revealjs`) |
| `present_figure_insert(name, section, figure_id, position="end")` | Insert a `fig:<id>` placeholder into a section and auto-register in `deck.yml` |
| `present_seed_from_paper(name, citekey, template="journal-club", model="sonnet", force=false)` | Scaffold a deck and seed a `sections/seed.md` via `biblio.present.generate_slides` |
| `present_section_import(name, from_project, source_deck, section, key="", order=0, mode="reference")` | Import a section from another project's deck via worklog; caches under `imports/` and registers in `deck.yml` |
| `present_refresh_import(name, section)` | Re-fetch a previously imported section from its source project (reference mode only) |
| `present_freeze_import(name, section="")` | Lock one or all imported sections against future refreshes |

`present_init` accepts four templates: `lab-meeting` (5 sections), `journal-club` (6), `conference-talk` (8), `progress-report` (5). Two formats: `marp` (phase 1, requires `marp-cli`) and `revealjs` (phase 3, requires pandoc ≥ 2.19). Section files are scaffolded as markdown stubs with notio-compatible YAML frontmatter so notio indexing can surface them.

`present_status` and `present_overview` both return per-section counts. `present_status` is the fast version for quick checks; `present_overview` adds citation cross-checking, figure staleness detection, and total slide count (including intra-file `---` separators).

`present_section_context` is the agent's single entry point for drafting. It gathers the section body, extracts citekeys and figure refs, runs a RAG query seeded from the section key + deck title, and pulls related notes — everything needed to draft without multiple reads.

`present_assemble` dispatches by `spec.format`: Marp decks get a Marp frontmatter block; reveal.js decks get a pandoc YAML metadata block. Intra-file `---` separators are preserved in both backends; the section source files themselves are format-agnostic and can be rendered both ways by flipping `format:` in `deck.yml`.

`present_build` runs the full pipeline. For Marp: assemble → figure resolution → pandoc citeproc preresolve (if bibliography configured) → marp-cli render. For reveal.js: assemble (pandoc frontmatter) → figure resolution → pandoc `-t revealjs --slide-level=0 --citeproc` render. `--slide-level=0` is deliberate — it makes horizontal rules act as slide separators, matching Marp's convention so the same section source builds both formats.

`present_cite_check` walks every section, extracts citekey markers, cross-references them against the inherited bibliography, and reports which cited papers have docling fulltext available for RAG. Returns actionable suggestions (`Run biblio_ingest for missing citekeys: [...]`) the agent can execute directly.

`present_diff` compares the current assembled markdown against `build/assembled.md` from the last build. Reports per-section word-count deltas, citekey drift (added/removed), figure-ref drift, and a full unified diff. Useful after a round of edits to see what the next build would actually change.

`present_figure_insert` inserts `![caption](fig:<figure_id>)` into a section and appends the figure to `deck.yml`'s `figures:` list if not already there. At render time, `resolve_figure_paths` swaps the placeholder for the real figio output path with a format-aware extension preference (png for Marp, svg for reveal.js, png for pptx).

`present_seed_from_paper` is the bridge to biblio. It delegates to `biblio.present.generate_slides` (LLM-backed Marp generation from a paper's docling output and figures), strips the Marp frontmatter, and writes the result into the deck as `sections/seed.md`. The seed is a *starting point* for iteration, never a finished deck.

`present_section_import` fetches `docs/deliverables/presentations/<source_deck>/sections/<section>.md` from another project via `worklog_read_file`, strips the remote frontmatter, stamps a new header with provenance (`imported_from_project`, `imported_from_deck`, `imported_from_section`, `import_mode`), writes the cache file to `docs/deliverables/presentations/<name>/imports/<key>.md`, and registers a `DeckSection` in `deck.yml` with an `import:` block. Extracts citekeys and figure refs from the body and reports which citekeys are missing from the host project's bibliography.

`present_refresh_import` re-fetches a reference-mode import to pick up upstream edits. Preserves the cache file's provenance header. Refuses to operate on frozen imports — use `present_freeze_import` to unfreeze first if you really need to.

`present_freeze_import` flips `import_mode: reference → freeze` in both `deck.yml` and the cache file's frontmatter. Use before giving a talk from a deck that depends on another project's in-flight material.

## Code intelligence tools (via codio)

### Read

| Tool | Description |
|------|-------------|
| `codio_list(kind, language, capability, priority, runtime_import)` | Filtered library listing |
| `codio_get(name)` | Full library record |
| `codio_registry()` | Full registry snapshot |
| `codio_vocab()` | Controlled vocabulary for registry fields |
| `codio_validate()` | Registry consistency check |
| `codio_discover(query, language)` | Capability search across libraries |
| `codio_func_doc(package, module, function="", env="")` | Fetch docstrings for functions in an installed package |

### Write

| Tool | Description |
|------|-------------|
| `codio_add_urls(urls[], clone=false, shallow=false)` | Add libraries from GitHub/GitLab URLs |
| `codio_add(name, kind, language="", repo="", description="", capabilities=[], tags=[])` | Register a library manually |
| `codio_rag_sync(force_init=false)` | Sync codio sources into the search index |

`codio_add_urls` parses repository URLs, fetches metadata from the GitHub API (language, license, description, topics), and creates catalog, profile, and repository entries automatically. Set `clone=true` to create local mirrors. Set `shallow=true` for a shallow clone.

`codio_add` registers a library by hand when you already have the metadata. `kind` is one of the controlled vocabulary values from `codio_vocab()`.

`codio_func_doc` imports a package in the specified environment (conda or pixi) and returns the docstring for a function or an entire module. Useful for discovering API surface before implementing an integration.

`codio_rag_sync` writes codio catalog and notes files into the indexio source config. Run `indexio_build` afterwards to embed the updated content.

## Pipeline tools (via pipeio)

### Flow management

| Tool | Description |
|------|-------------|
| `pipeio_flow_list(pipe="")` | List pipeline flows, optionally filtered by pipe |
| `pipeio_flow_status(pipe, flow)` | Show config, outputs, and notebooks for a flow |
| `pipeio_flow_fork(pipe, flow, new_flow, new_pipe="")` | Copy a flow's code directory and register as a new flow |
| `pipeio_flow_deregister(pipe, flow)` | Remove a flow from the registry (files on disk are untouched) |
| `pipeio_registry_scan()` | Scan filesystem for pipelines and rebuild the registry |
| `pipeio_registry_validate()` | Validate pipeline registry consistency (code vs docs, config schema) |
| `pipeio_contracts_validate()` | Validate I/O contracts for all flows |
| `pipeio_cross_flow(pipe="", flow="")` | Map output_registry → input_registry chains across flows |
| `pipeio_completion(pipe, flow="", mod="")` | Check per-session completion against expected registry outputs |

### Notebook lifecycle

Notebook tools support multiple backends via the `NotebookBackend` protocol. Each notebook declares `format:` in `notebook.yml` (`"percent"` for jupytext, `"marimo"` for reactive; auto-detected when empty).

| Tool | Description |
|------|-------------|
| `pipeio_nb_status(flow="", name="")` | Show notebook sync and publication status (includes format) |
| `pipeio_nb_create(flow, name, kind="investigate", description="", format="")` | Scaffold a new notebook (format selects percent or marimo template) |
| `pipeio_nb_update(flow, name, status="", description="", kind="", mod="", kernel="")` | Update notebook metadata in notebook.yml |
| `pipeio_nb_sync(flow, name, formats=[], direction="py2nb", force=false)` | Sync notebook via jupytext (no-op for marimo) |
| `pipeio_nb_sync_flow(flow, direction="py2nb", force=false)` | Batch-sync all notebooks in a flow |
| `pipeio_nb_diff(flow, name)` | Show sync state between .py and .ipynb (always synced for marimo) |
| `pipeio_nb_read(flow, name)` | Read .py content with metadata and structural analysis |
| `pipeio_nb_analyze(flow, name)` | Analyze imports, RunCard fields, section headers (format-aware cell splitting) |
| `pipeio_nb_audit()` | Audit all notebooks for staleness, config gaps, and mod coverage |
| `pipeio_nb_scan(register=false)` | Scan for unregistered .py notebooks (detects both formats) |
| `pipeio_nb_lab(flow="", sync=false)` | Build/refresh Jupyter Lab symlink manifest (percent-format only) |
| `pipeio_nb_publish(flow, name)` | Publish notebook to docs (nbconvert for percent, marimo export for marimo) |
| `pipeio_nb_exec(flow, name, params={}, timeout=600)` | Execute notebook (papermill for percent, marimo run for marimo) |
| `pipeio_nb_pipeline(flow, name, formats=[], build_site=false)` | Composite: sync → publish → docs_collect → docs_nav in one call |
| `pipeio_nb_promote(flow, name, mod, rule_name="", description="", apply=false)` | Promote notebook to pipeline mod: analyze → script → rule stub → docs |
| `pipeio_nb_extract(flow, name, overwrite=false, tags_only=false)` | Extract figures/markdown/text from executed notebook for reporting (renamed from `pipeio_nb_report`) |
| `pipeio_nb_validate(flow, name)` | Structural validation (percent: AST + import isolation; marimo: `marimo check`) |
| `pipeio_nb_watch(flow, name, port=0, python_bin="")` | Launch `marimo edit --watch` for live human oversight (marimo-only) |
| `pipeio_nb_snapshot(flow, name, timeout=120, python_bin="")` | Execute marimo notebook and return cell outputs — agent's "eyes" (marimo-only) |

**Percent-format (jupytext):** `pipeio_nb_sync` direction `"py2nb"` (default) regenerates `.ipynb`/`.myst.md` from the source `.py`; use `"nb2py"` after human edits in JupyterLab. `pipeio_nb_exec` syncs `.py` → `.ipynb` first, then runs via papermill. `params` overrides RunCard fields.

**Marimo-format:** Single-file `.py` format — sync is a no-op, execution runs `marimo run` directly, validation runs `marimo check` for DAG integrity. Use `pipeio_nb_watch` to launch live editing with `--watch` for agent-human collaboration. Both `pipeio_nb_watch` and `pipeio_nb_snapshot` auto-resolve the project Python via `code.runner` config (conda or pixi) when `python_bin` is empty.

### Mod authoring

| Tool | Description |
|------|-------------|
| `pipeio_mod_list(pipe, flow="")` | List logical modules (mods) for a flow |
| `pipeio_mod_resolve(modkeys[])` | Resolve modkeys (pipe-X_flow-Y_mod-Z) to metadata and doc locations |
| `pipeio_mod_context(pipe, flow="", mod="")` | Bundled read context: rules, scripts, doc, config params in one call |
| `pipeio_mod_create(pipe, flow, mod, inputs={}, outputs={}, params_spec={}, ...)` | Scaffold mod script and doc stub with I/O wiring |
| `pipeio_modkey_bib(output_path="", project_name="")` | Generate modkey.bib with @misc entries for all mods (for citations) |

`pipeio_mod_context` returns everything needed to understand and work on a mod in one MCP call: Snakemake rules, script content, doc stub, and config param section.

`pipeio_mod_create` scaffolds `scripts/<mod>.py` and `docs/mod-<mod>.md`. When `inputs`/`outputs`/`params_spec` are provided, generates Snakemake I/O unpacking and parameter binding. Set `use_pipeline_context=true` for PipelineContext boilerplate.

### Snakemake rules

| Tool | Description |
|------|-------------|
| `pipeio_rule_list(pipe, flow="")` | List rules with input/output signatures and mod membership |
| `pipeio_rule_stub(pipe, flow, rule_name, inputs={}, outputs={}, params={}, script="")` | Generate a Snakemake rule stub for review |
| `pipeio_rule_insert(pipe, flow, rule_name, rule_text="", ...)` | Insert a rule into the correct Snakefile or .smk include |
| `pipeio_rule_update(pipe, flow, rule_name, add_inputs={}, add_outputs={}, apply=false)` | Patch an existing rule by merging new sections |

`pipeio_rule_stub` returns formatted rule text for human review — it does **not** auto-insert. Use `pipeio_rule_insert` to write it.

`pipeio_rule_update` returns a unified diff preview. Set `apply=true` to write the patched Snakefile.

### Config authoring

| Tool | Description |
|------|-------------|
| `pipeio_config_read(pipe, flow="")` | Read and parse a flow's config.yml with YAML anchor resolution |
| `pipeio_config_patch(pipe, flow, registry_entry={}, params_entry={}, apply=false)` | Validate and optionally patch a flow's config.yml |
| `pipeio_config_init(pipe, flow, input_dir="", output_dir="", ...)` | Scaffold a new flow's config.yml |

`pipeio_config_patch` returns a unified diff preview; set `apply=true` to write. `registry_entry`: `{group_name: group_dict}` to add/replace in `registry:`. `params_entry`: `{section: {key: value}}` to update in top-level params.

### DAG & Reporting

| Tool | Description |
|------|-------------|
| `pipeio_dag_export(pipe, flow="", graph_type="rulegraph", output_format="dot")` | Export rule/job DAG via Snakemake's native graph output |
| `pipeio_flow_report(flow="", output_path="", target="", max_embed_mb=200, warn_embed_mb=50, force=false)` | Generate Snakemake HTML report with runtime stats and provenance. Pre-flight sums resolved target sizes and refuses above `max_embed_mb` to prevent GB-scale HTML from dense-SVG plots (renamed from `pipeio_report`) |
| `pipeio_target_paths(pipe, flow="", group="", member="", entities={}, expand=false)` | Resolve output paths for a flow's registry entries |

`pipeio_dag_export` `graph_type`: `rulegraph` (compact), `dag` (full jobs), `d3dag` (JSON). `output_format`: `dot`, `mermaid`, `svg` (needs graphviz), `json` (d3dag only).

`pipeio_target_paths` has three modes: no group → list groups/members/patterns; group+member+entities → resolve a single path; `expand=true` → glob all matching paths filtered by entities.

### Docs

| Tool | Description |
|------|-------------|
| `pipeio_docs_collect()` | Collect flow-local docs and notebooks into docs/pipelines/ for MkDocs |
| `pipeio_docs_nav()` | Generate MkDocs nav YAML fragment for collected pipeline docs |
| `pipeio_mkdocs_nav_patch()` | Apply pipeio docs nav fragment to mkdocs.yml |

### Run management

| Tool | Description |
|------|-------------|
| `pipeio_run(flow="", targets=[], cores=1, dryrun=false, ...)` | Launch Snakemake in a detached screen session |
| `pipeio_run_status(run_id="", pipe="", flow="")` | Query progress of running or recent Snakemake runs |
| `pipeio_run_dashboard()` | Rich summary of all tracked runs: active/completed/failed per flow |
| `pipeio_run_kill(run_id)` | Gracefully stop a running Snakemake screen session |
| `pipeio_log_parse(pipe, flow="", run_id="", log_path="")` | Extract structured data from Snakemake logs |

`pipeio_run` launches Snakemake in a `screen` session, tracks state in `.pipeio/runs.json`, and returns a `run_id`. The snakemake command is resolved via `code.runner` config — either `conda run -n <env>` or `pixi run [-e <env>]` (auto-detected from `pixi.toml` when `code.runner` is not set). `wildcards`: entity filters for scoping (e.g. `{"subject": "01", "session": "04"}`). `use_conda=true` passes `--use-conda` to Snakemake (for snakemake's own conda env management, independent of the runner).

`pipeio_log_parse` extracts completed rules with timing, failed rules with error summaries, resource warnings, and missing inputs from the log file.

## DataLad tools

| Tool | Description |
|------|-------------|
| `datalad_status(recursive=true, dataset="")` | Show DataLad status for the project or a subdataset |
| `datalad_save(message="Update", recursive=true, dataset="", path="")` | Save dataset state with a commit message |
| `datalad_push(sibling="github", dataset="")` | Push to a DataLad sibling |
| `datalad_pull(sibling="origin", dataset="")` | Pull from a DataLad sibling |
| `datalad_siblings(dataset="")` | List configured DataLad siblings |

`datalad_save` runs `datalad save` with the given message. `path` limits the save to a specific file or directory. Use the configured `datalad_bin` environment (typically `labpy`).

`datalad_push` defaults to the `github` sibling. `dataset` can be a relative path to push a subdataset. `datalad_pull` defaults to `origin`.

## Context tools

| Tool | Description |
|------|-------------|
| `project_context()` | Project config + README excerpt + key paths |
| `runtime_conventions()` | Parsed Makefile variables and commands |
| `agent_instructions()` | Tool routing table, workflow conventions, enabled packages |
| `module_context(doc_path)` | Extract structured sections from a markdown document |
| `skill_read(name)` | Read a skill's full content by name |
| `ecosystem_status()` | One-shot health check across all subsystems with staleness detection |

`agent_instructions` returns the dynamic equivalent of the CLAUDE.md tool routing section. Cross-project orchestrators (e.g. worklog) should call this to get project-aware agent instructions before generating or executing prompts. The response includes enabled packages, a tool routing table (intent → MCP tool → anti-pattern), and workflow conventions.

`module_context` extracts goal, assumptions, parameters, I/O, and limitations sections from a markdown document. Useful for reading pipeline doc stubs without loading the full file.

`skill_read` returns metadata and the full markdown body for a named skill. Use `agent_instructions()` first to see available skill names.

`ecosystem_status` checks all enabled subsystems (biblio, codio, notio, pipeio, figio, indexio) and returns per-subsystem health. For indexio, it reports `built_at` timestamp, `stale` flag, and `stale_sources` list by comparing the status manifest against current file states. Stale sources set `overall_healthy` to false.

## Site tools

| Tool | Description |
|------|-------------|
| `site_detect()` | Detect doc framework (mkdocs, sphinx, vite) |
| `site_build(framework="", strict=false)` | Build the doc site |
| `site_serve(port=0, framework="")` | Start doc server in background; returns URL and PID |
| `site_stop(port=0, pid=0)` | Stop a running doc server |
| `site_list()` | List running doc servers |
| `site_deploy(target="gitlab")` | Deploy the doc site by pushing to the configured pages sibling |

`site_build` auto-detects the framework (`mkdocs build`, `sphinx-build`, or `vite build`). Pass `framework` to override detection. `strict=true` fails on warnings.

`site_deploy` pushes the built site to the GitLab Pages or GitHub Pages sibling. Set the target sibling in `.projio/config.yml` under `helpers.docs`.

## Server configuration

The server reads `PROJIO_ROOT` from the environment to determine the project directory.

When started via `projio mcp -C .`, the CLI sets `PROJIO_ROOT` automatically.

### Generate `.mcp.json` automatically

```bash
projio mcp-config -C .          # preview
projio mcp-config -C . --yes    # write .mcp.json
```

This reads `runtime.python_bin` from your projio config and generates the correct `.mcp.json` for Claude Code.

### Manual configuration

For Claude Desktop or Claude Code, set it explicitly in the MCP config:

```json
{
  "mcpServers": {
    "projio": {
      "command": "/path/to/python",
      "args": ["-m", "projio.mcp.server"],
      "env": { "PROJIO_ROOT": "/path/to/your/project" }
    }
  }
}
```
