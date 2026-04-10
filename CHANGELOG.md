# Changelog

## Unreleased

### Added
- **`pipeio_nb_report` MCP tool** — extract figures, markdown, and text outputs from an executed notebook into a structured payload for report writing; saves figures to `{flow}/docs/reports/{name}/`; supports percent-format (nbconvert) and marimo (`marimo export md`); detects interactive widget outputs (holoviews, bokeh, plotly) that can't be extracted as static images and returns guidance
- **`/report` skill** — orchestrates `pipeio_nb_report` extraction + agent-written curated report at `{flow}/docs/reports/{name}.md`; reports are git-tracked source files published via `docs_collect`
- **`pipeio_nb_move` MCP tool** — move a notebook between flows (files + notebook.yml update in both source and target)

### Fixed
- **`pipeio_nb_exec` output in `.src/`** — executed notebook now overwrites the workspace `.ipynb` instead of creating `_executed.ipynb` inside `.src/`
- **Duplicate `"flow"` keys** in `mcp_nb_exec` and `mcp_mod_list` return dicts

### Added
- **`biblio_openalex_resolve` MCP tool** — wraps `biblio openalex resolve` CLI for agentic workflows; creates `resolved.jsonl` required by `biblio_enrich`, `biblio_pdf_fetch_oa`, `biblio_graph_expand`, and `biblio_enrich_topic_tags`
- **`biblio_status` MCP tool** — per-citekey pipeline completeness dashboard showing bib/resolved/pdf/docling/grobid/enriched/rag stage status with recommended next actions; complements `biblio_library_quality` (field quality) with derivative-file existence checks
- **`biblio_crossref_resolve` MCP tool** — standalone Crossref DOI resolver for preprints and niche journals missed by OpenAlex; also integrated as automatic fallback in `biblio_openalex_resolve` pipeline
- **`biblio_graph_promote` MCP tool** — promotes citation graph expansion candidates into the bibliography; reads `graph_candidates.json`, filters by citations/year/keyword, deduplicates against library, and feeds to `biblio_ingest`; supports `dry_run` preview
- **`biblio_extract` MCP tool** — LLM-driven extraction of paper relevance against `plan/questions.yml`; reads docling markdown, outputs structured YAML to `bib/derivatives/claude/{citekey}/extract.yml` with per-hypothesis relevance, methods, dataset opportunities, and key findings
- **`questio_prior_art` MCP tool** — aggregates `biblio_extract` outputs per research question into markdown tables at `docs/plan/prior_art/`; connects literature to hypotheses bidirectionally
- **`questio_gap` literature expectations** — gap analysis response now includes a `literature` field with high/medium relevance papers from `biblio_extract` output, surfacing what the literature expects for each hypothesis

### Fixed
- **Citekey diacritic mangling** — `biblio_ingest` citekey generation now transliterates Unicode diacritics (e.g. Molle → molle, Buzsaki → buzsaki) instead of stripping them (was: Molle → mlle)
- **Silent zero returns in biblio pipeline** — `biblio_enrich` and `biblio_pdf_fetch_oa` now return clear error messages with pipeline hints when `resolved.jsonl` is missing, instead of silently returning `{"enriched": 0}` or empty results
- **notio `note_links` missing `.md` extension** — LLM-returned link targets are now normalized to strip path prefixes and ensure `.md` extension, preventing wikilinks like `[[note-idmd]]` instead of `[[note-id.md]]`
- **questio `docs_collect` broken result links** — evidence and milestone tables linked to `../log/result/{stem}/` (bare dir, no extension); now uses `../log/result/{stem}.md`; backlog link in plan index changed from `../log/result/` to `../log/result/index.md`
- **pipeio `docs_collect` bare directory links** — generated `docs/pipelines/index.md` used `{flow}/` instead of `{flow}/index.md`; copied markdown files (e.g. `architecture.md`) now have bare directory links normalized to `dir/index.md` during copy
- **questio `docs_collect` README/index conflict** — stopped generating `docs/plan/README.md` which conflicted with `docs/plan/index.md` in mkdocs strict builds; README content (source-of-truth, tools table) merged into index.md
- **questio `questio_status` double YAML load** — `_load_plan_yaml` was called twice per request (once for filtered questions, once for overall stats); now loads once and splits before filtering
- **questio result `_filename` stem pattern** — result note filenames stored as stems without `.md`, requiring every link site to append the extension; now stores full filename (`_filename`) with `.md` and separate `_label` for display
- **questio dangling cross-reference detection** — `questio_status` and `questio_docs_collect` now validate that result note `question`/`milestone` frontmatter fields reference IDs that exist in the YAML plan files; dangling refs surfaced as `warnings` in the response
- **questio `_find_roots` cycle safety** — dependency graph walker refactored from recursive to iterative; circular dependencies no longer silently produce an empty recommendation — cycle members are returned as actionable roots
- **`projio.mk` env resolution** — `PROJIO` and `MKDOCS` variables could resolve to the wrong conda env (e.g. `default` instead of `docs`) when `code.envs.projio` was not explicitly set; `resolve_env_all` now falls back `projio` → `docs` and `docs` → `projio` (both need projio + mkdocs); legacy `runtime.*` path now reads `runtime.docs_python` and falls back to `projio_python`; warns to stderr when no projio/docs env is configured

### Changed
- **questio YAML sources moved to `plan/`** — `questions.yml` and `milestones.yml` relocated from `docs/plan/` to `plan/` at project root (visible scientific content, like `bib/` for bibliography); generated pages remain in `docs/plan/` with `<!-- auto-generated -->` headers (convention B: human and generated content co-locate in `docs/` for relative linking); `questio_docs_collect` generates a monorepo sub-`mkdocs.yml` (`docs_dir: .`) with ordered nav; `projio sync` auto-wires the `!include` line; `plan` added to notio `_MANAGED_SECTIONS`; all skills and specs updated to reference `plan/` paths

### Added
- **`projio config help`** — prints a configuration reference covering `code.envs` (conda env resolution with fallback chains), legacy `runtime.*` keys, site config, push target, and subsystem toggles with inline examples
- **`projio-setup` skill** — guides agents through setting up or fixing projio ecosystem config: env resolution diagnostics, subsystem activation, site config, sync verification
- **ezlinks + bibtex mkdocs plugins** — `mkdocs-ezlinks-plugin` and `mkdocs-bibtex` added to `docs`/`dev` extras; `DEFAULT_MKDOCS` template includes both for new projects; `projio sync` auto-configures ezlinks, bibtex (with `bib_file` from render.yml) in existing projects' mkdocs.yml
- **Notio card feed styling** — note type indexes now render as a vertically-stacked card feed (title link + metadata chips + separator) styled via `stylesheets/cards.css`; `pymdownx.details` extension enabled for collapsible sections
- **Collapsible closed groups in note indexes** — `done`, `cancelled`, and `resolved` groups are rendered as collapsed `<details>` blocks with counts; active groups (`open`, `pending`, `in_progress`, `scheduled`, `partial`) appear first in a fixed order
- **Remote platform integration for notio** — bidirectional bridge between repo-local notes and GitHub/GitLab issues
  - `notio promote <path>` — creates a platform issue from a note, writes `remote: github#42` back to frontmatter
  - `notio capture github#42` — creates a local note from a platform issue, pulls comment thread
  - `notio pull [--all]` — fetches remote comments into `## Remote Thread` section (full mirror, idempotent)
  - `notio remote-status` — lists all notes linked to platform issues
  - `remote` frontmatter field rendered as clickable chip in card feed
  - Self-hosted GitLab support (e.g. `gitlab.lrz.de`) — host extracted from git remote URL
  - Platform auto-detected from all git remotes (not just origin); prefers remotes named `github`/`gitlab`
  - 4 MCP tools: `note_promote`, `note_capture`, `note_pull`, `note_remote_status` (registered in both notio and projio servers)
  - Uses `gh`/`glab` CLI for API access — no separate token management
  - Design spec: `docs/specs/notio/remote-integration.md`
- **Multi-agent MCP config generation** — `projio add codex` and `projio add copilot` scaffold MCP server configs for Codex (`.codex/config.toml`) and VS Code/Copilot (`.vscode/mcp.json`) alongside the existing `projio add claude` (`.mcp.json`); three emitters from a shared canonical `McpServerDef` representation cover seven+ MCP clients (Claude Code, Cursor, Continue, MCPHost, Codex, VS Code/Copilot); `projio sync` auto-regenerates enabled agent configs; spec at `docs/specs/multi-agent-mcp-config.md`
- **Deliverables convention** — `docs/deliverables/{reports,presentations,posters}/` for shareable artifacts (progress reports, slide decks, conference posters); frontmatter schema with type/audience/event/period/questions fields; spec at `docs/specs/deliverables.md`
- **Deliverables indexing in `questio_docs_collect`** — auto-generates overview, per-type indexes, and `mkdocs.yml` sub-nav when `docs/deliverables/` exists; gracefully skipped when absent
- **`questio-report` skill updated** — now persists reports to `docs/deliverables/reports/report-YYYY-MM-DD.md` with structured frontmatter instead of ephemeral text; calls `questio_docs_collect()` to regenerate indexes
- **`projio sync --index`** — incremental index rebuild during sync, auto-detects stale sources via file mtime/size comparison against last build manifest; opt-in via `automation.index.on_sync: true` in config or `--index` CLI flag; `--no-index` to skip
- **`projio sync --install-hooks`** — installs a projio-managed `.git/hooks/post-commit` that runs `projio sync --index` in the background after each commit; will not overwrite existing non-projio hooks
- **`automation.index` config section** — new top-level config key with `on_sync` (bool, default false) and `background` (bool, default true) to control automatic index rebuilds
- **Index staleness in `ecosystem_status()`** — indexio subsystem now reports `built_at`, `stale` flag, and `stale_sources` list; stale index sets `overall_healthy` to false

### Changed
- **Conda env rename: `rag` → `projio`** — default env name in code.envs, config scaffolds, and all documentation now uses `projio` as the canonical conda environment name; existing installs with `rag` continue to work via runtime config overrides
- **Cross-platform compatibility** — removed hardcoded `/storage/...` lab paths from source; conda discovery uses `shutil.which("conda")` with `sys.prefix` fallback instead of hardcoded base paths; `_conda_wrap()` regex now matches both Unix (`bin/`) and Windows (`Scripts/`) conda layouts; `resolve_env_python()` selects correct bin directory per platform; `os.kill`/`SIGTERM` replaced with cross-platform `_pid_alive()`/`_terminate_pid()` helpers (ctypes on Windows); git hook installation skipped on native Windows with informative message
- **Makefile portability** — removed hardcoded lab paths from Makefile variables; CLAUDE.md documents equivalent `pip`/`python -m` commands for platforms without `make`
- **Platform support documentation** — ecosystem-overview.md includes support matrix (Linux/macOS full, Windows WSL full, Windows native core-only)
- **`environment.yml`** — new conda env spec for single-env setup (`conda env create -f environment.yml`)
- **User config template** — `DEFAULT_USER_CONFIG` uses generic `/path/to/` placeholders instead of lab-specific paths; RIA sibling example commented out
- README rewritten for PyPI — ecosystem table (all 6 subsystems), MCP tool categories with counts, cleaner install/quickstart sections
- docs/index.md landing page rewritten — architecture diagram, install snippet, capabilities overview, Diataxis navigation table
- Ecosystem references updated to include pipeio and figio across docs/index.md, explanation/ecosystem.md, README
- pyproject.toml: added author email, Documentation URL, License and Information Analysis classifiers
- Fixed duplicate `plugins:` block in mkdocs.yml

## 0.1.1 — 2026-04-08

### Added
- **Questio research orchestration layer** — hypothesis-to-evidence-to-manuscript reasoning for agentic research workflows
  - `questio_status` MCP tool — research state overview (questions, milestone completion %, evidence counts, blockers)
  - `questio_gap` MCP tool — per-question evidence gap analysis with dependency resolution and actionable recommendations
  - `questio_docs_collect` MCP tool — auto-generates `docs/plan/` pages (questions table, milestones tracker, mermaid roadmap, evidence index)
  - Data model convention: `docs/plan/questions.yml` (research question registry) and `docs/plan/milestones.yml` (dependency-aware milestone tracker)
  - 5 skills: `questio-session` (full research session), `questio-next` (prioritization), `questio-ground` (literature/code grounding), `questio-record` (structured evidence capture), `questio-report` (supervisor summary)
  - Design spec: `docs/specs/research-orchestration/design.md`
- **`result` note type in notio** — dedicated note type for structured evidence records with `question`, `milestone`, `metric`, `value`, `confidence` frontmatter fields; own directory (`docs/log/result/`), template, and index
- **Questio documentation** — explanation doc (`docs/explanation/questio.md`) and setup tutorial (`docs/tutorials/questio-setup.md`)
- **`biblio_compile` MCP tool** — merges intermediate `.bib` files (merged.bib + modkey.bib) into `.projio/render/compiled.bib`, the single bibliography consumed by pandoc and mkdocs-bibtex
- **`bib_sources` field in render.yml** — declares inputs to `biblio_compile` (default: `.projio/biblio/merged.bib`, `.projio/pipeio/modkey.bib`)
- **CSL files shipped as package data** — apa, chicago-author-date, elsevier-harvard, ieee, nature, vancouver; copied to `.projio/render/csl/` during `projio sync`
- **`bib/README.md` scaffold template** — auto-generated overview of bib layout, pipeline flow, and CLI/MCP commands
- **`projio sync` step 9: PandocCiter** — auto-syncs `.vscode/settings.json` PandocCiter.DefaultBibs and pandocCiter.csl from render.yml; only touches PandocCiter keys, leaves other settings untouched
- **`load_active_citekeys(cfg)`** — new canonical API for listing active citekeys, reads from merged bib instead of a separate citekeys.md file
- **mkdocs-monorepo-plugin** integration — pipeio owns `docs/pipelines/mkdocs.yml`, root mkdocs.yml includes via `!include`
- `projio sync` step 8: auto-configures monorepo plugin + `!include` in project mkdocs.yml when pipeio is present
- `mkdocs-monorepo-plugin>=1.1` added to `docs` and `dev` extras in pyproject.toml
- snakemake added to codio registry as external reference mirror

### Changed
- **Bib architecture: sources vs artifacts separation** — `bib/` now holds only human-managed source data (srcbib/, articles/, derivatives/); all generated artifacts moved under `.projio/`
  - `biblio_merge` output: `bib/main.bib` → `.projio/biblio/merged.bib`
  - Merge/quality/fetch logs: `bib/logs/` → `.projio/biblio/logs/`
  - Biblio config: `bib/config/biblio.yml` → `.projio/biblio/biblio.yml`
  - Compiled bibliography: `.projio/render/compiled.bib` (new)
  - Pandoc defaults: `bib/pandoc-defaults.yaml` → `.projio/render/pandoc-defaults.yaml`
  - CSL styles: `bib/csl/` → `.projio/render/csl/` (shipped by projio)
- **Citekeys derived from bib** — `citekeys.md` eliminated; active citekeys are now derived from the merged bibliography. `--all` flags on docling/grobid/batch commands read from the bib directly. `biblio citekeys` simplified to a flat list command.
- **Biblio scaffold restructured** — config files (biblio.yml, tag_vocab.yml) now scaffold to `.projio/biblio/`; `bib/.gitignore` only created when `bib/` is a git subdataset
- **Render defaults updated** — `bibliography` defaults to `.projio/render/compiled.bib`, `csl` to `.projio/render/csl/apa.csl`
- **Root .gitignore** — replaced stale `bib/logs/` entry with `.projio/biblio/logs/`
- `pipeio_mkdocs_nav_patch` simplified — writes sub-mkdocs.yml instead of fragile YAML patching of root mkdocs.yml
- CLAUDE.md updated with `pipeio_target_paths`, `pipeio_dag_export` SVG auto-write, tool count corrected to 51
- **projio gitignore block** expanded — covers all generated artefacts across subsystems: indexio jobs, codio mirrors, render outputs, pipeio state (`.snakemake/`, `*.ipynb`, `runs.json`), docs/pipelines nav, biblio logs, filters

### Removed
- **`citekeys.md`** — scaffold template, config key, and all `load_citekeys_md` / `add_citekeys_md` / `remove_citekeys_md` usage in batch/site/grobid/ingest/graph/pool modules replaced by `load_active_citekeys(cfg)`
- `bib/Makefile` scaffold template (superseded by biblio MCP tools)
- `bib/config/rag.yaml` scaffold template (belongs to indexio)
