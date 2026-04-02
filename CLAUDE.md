# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is Projio

Projio is a project-centric research assistance ecosystem that turns a repository into a queryable knowledge environment for humans and AI agents. It provides structured, machine-accessible knowledge layers over a repository by integrating code, papers, notes, design decisions, external libraries, and documentation through a unified MCP server interface.

Core design principle: **the repository is the primary unit of knowledge** — all project knowledge lives in or alongside the repo.

## Build & Development Commands

```bash
make dev          # Install projio + indexio editable with dev extras
make test         # Run pytest
make docs         # Build MkDocs site (strict)
make docs-serve   # Serve MkDocs locally
make build        # Build wheel and sdist
make check        # twine check on dist artifacts
make clean        # Remove build artifacts
make publish      # Publish to PyPI
make publish-test # Publish to TestPyPI
```

Run a single test:
```bash
PYTHONPATH=src python -m pytest tests/test_cli.py -q
```

## Architecture

### Ecosystem Components

Projio orchestrates six specialized subsystems, each managing a knowledge domain:

| Component | Domain | Description |
|-----------|--------|-------------|
| **indexio** (née texio) | retrieval | Domain-agnostic corpus indexing, chunking, embedding, semantic search |
| **biblio** | literature | Bibliography management, citekey resolution, paper context extraction |
| **notio** | notes + manuscripts | Structured project notes, idea capture; manuscript assembly & rendering via `notio.manuscript` subpackage |
| **codio** | code intelligence | Library registry, code reuse discovery, implementation strategy |
| **pipeio** | pipelines | Agent-facing pipeline authoring & discovery, contracts, notebook lifecycle |
| **figio** | figures | Declarative figure orchestration — FigureSpec YAML → panel rendering → SVG composition → PDF/PNG export |

These live as git submodules under `packages/` and are optional dependencies — the system degrades gracefully when any are absent.

The full paper production pipeline: **figio** (figures) + **biblio** (citations) + **notio/manuscript** (section assembly + pandoc render) = PDF/LaTeX.

### Source Layout

- `src/projio/cli.py` — CLI entry point (`projio` command), subcommand dispatch
- `src/projio/init.py` — Workspace scaffolding (three kinds: `generic`, `tool`, `study`)
- `src/projio/config.py` — Two-tier config: user (`~/.config/projio/config.yml`) merged with project (`.projio/config.yml`), project wins
- `src/projio/sync.py` — `projio sync`: auto-discover code/lib libraries → codio, detect code/utils → config, sync Lua filter + CSL files, generate pandoc-defaults.yaml
- `src/projio/render.py` — `.projio/render.yml` loader: single source of truth for PDF engine, CSL, bibliography, bib_sources, Lua filter, conda env. Generates `.projio/render/pandoc-defaults.yaml`
- `src/projio/data/filters/include.lua` — Bundled Lua transclusion filter for Pandoc (handles `{% include-markdown %}` and `--8<--` markers). Copied to `.projio/filters/` during `projio sync`
- `src/projio/data/csl/` — Bundled CSL citation styles (apa, ieee, chicago-author-date, vancouver). Copied to `.projio/render/csl/` during `projio sync`
- `src/projio/site.py` — MkDocs build/serve/publish wrappers
- `src/projio/helpers/` — DataLad sibling management (GitHub/GitLab/RIA), auth diagnostics, credential inspection. All sibling commands are **preview-first** (show command, require `--yes` to execute)
- `src/projio/mcp/` — FastMCP server exposing unified tools across all subsystems

### MCP Server

The MCP server (`src/projio/mcp/server.py`) is the primary agent interface. It registers tools from each subsystem module:

- `mcp/rag.py` — `rag_query`, `rag_query_multi`, `corpus_list`, `indexio_build`, `indexio_sources_list`, `indexio_sources_sync` (via indexio)
- `mcp/biblio.py` — `citekey_resolve`, `paper_context`, `paper_absent_refs`, `library_get`, `biblio_ingest`, `biblio_library_set`, `biblio_merge`, `biblio_compile`, `biblio_pdf_fetch`, `biblio_pdf_fetch_oa`, `biblio_docling`, `biblio_docling_batch`, `biblio_docling_status`, `biblio_grobid`, `biblio_grobid_check`, `biblio_graph_expand`, `biblio_rag_sync`
- `mcp/notio.py` — `note_list`, `note_latest`, `note_search`, `notio_reindex`
- `mcp/manuscripto.py` — `manuscript_init`, `manuscript_list`, `manuscript_status`, `manuscript_build`, `manuscript_validate`, `manuscript_assemble`, `manuscript_figure_insert`, `manuscript_section_context`, `manuscript_overview`, `manuscript_cite_check`, `manuscript_figure_build_all`, `master_list`, `master_build`, `master_generate`
- `mcp/codio.py` — `codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`, `codio_discover`, `codio_rag_sync`, `codio_add` (with `role` param: core/shared/external)
- `mcp/pipeio.py` — 50 tools across flow/mod/rule/config/notebook/docs/execution. Key additions: `pipeio_mod_audit`, `pipeio_mod_doc_refresh`, `pipeio_script_create`, `pipeio_nb_promote`. No `pipe` parameter — flows addressed by name only. See `skill_read("pipeio-guide")` for full reference.
- `mcp/datalad.py` — `datalad_save`, `datalad_status`, `datalad_push`, `datalad_pull`, `datalad_siblings`
- `mcp/site.py` — `site_detect`, `site_build`, `site_deploy`, `site_serve`, `site_stop`, `site_list`
- `mcp/context.py` — `project_context`, `runtime_conventions`, `agent_instructions`, `module_context`, `skill_read`, `projio_init`, `ecosystem_status`, `permissions_sync`

Server is run via `python -m projio.mcp.server` with `PROJIO_ROOT` env var pointing to the target project.

### Agent Workflow Philosophy

Projio promotes **search before creation**: discover existing implementations, consult notes and literature, then make an explicit engineering decision (reuse, wrap, depend, or implement new). The MCP tools support this workflow by providing structured queries rather than raw file inspection.

### Runtime Environment Convention

Projio-managed projects use two distinct environments, configured in `~/.config/projio/config.yml` under `runtime:`:

| Key | Env | Purpose |
|-----|-----|---------|
| `projio_python` | `rag` | Python used to run `projio` itself and project Python |
| `datalad_bin` | `labpy` | DataLad + git-annex binary |

The generated `.projio/projio.mk` substitutes these into `PROJIO ?=` and `DATALAD ?=`. `projio_python` takes precedence over `python_bin` for the `PROJIO` variable; `python_bin` still controls `PYTHON` for project code. Projects can override either key in their own `.projio/config.yml`.

### Claude Code Integration

Projio scaffolds `.claude/settings.json` with pre-approved tool permissions (including `mcp__projio__*` and `mcp__worklog__*`) and `.mcp.json` for the MCP server. Both files are gitignored via the `# >>> projio >>>` block. Use `projio git untrack` to stop tracking them if they were committed before being gitignored.

### Code Tiers and Codio

Projects organize code in three tiers with a promotion model (notebooks → scripts → utils → core library). Codio manages the library catalog with a `role` field that governs agent write access:

| Tier | Location | codio `role` | Description |
|------|----------|-------------|-------------|
| Core library | `code/lib/{name}/` | `core` | Dataset-agnostic, reusable. Agents may add code. |
| Project utils | `code/utils/` | — | Pipeline-aware glue (PipelineContext, bootstrap). Configured via `code.project_utils` in `.projio/config.yml`. |
| Flow scripts | `code/pipelines/{flow}/scripts/` | — | Snakemake wiring, one per rule. |

`projio sync` auto-discovers `code/lib/*/` and registers in codio with `role=core`, `kind=internal`. It also detects `code/utils/` and sets `code.project_utils` in config. The `project_context()` MCP tool returns the active code tier configuration.

Codio's five-layer architecture: physical code → catalog (with `role: core|shared|external`) → project profile → curated notes → MCP query tools. See `docs/specs/pipeio/code-tiers.md` for the full spec.

### Bibliography Architecture

Projects separate human-managed bibliography sources from generated artifacts. See `docs/specs/biblio/bib-architecture.md` for the full spec.

```
bib/
  srcbib/         # Zotero exports (human-managed .bib files)
  articles/       # PDFs
  derivatives/    # docling, grobid, openalex outputs

.projio/
  render.yml                        # render config (human-edited)
  render/
    compiled.bib                    # biblio_compile output — single bib for pandoc + mkdocs
    pandoc-defaults.yaml            # generated from render.yml
    csl/                            # CSL styles shipped by projio
  biblio/
    merged.bib                      # biblio_merge intermediate
    biblio.yml, library.yml         # biblio config (moved from bib/config/)
    logs/                           # merge/quality/duplicate logs
  pipeio/
    modkey.bib                      # pipeio_modkey_bib intermediate
```

Compilation pipeline: `srcbib/*.bib → biblio_merge → merged.bib` + `pipeio_modkey_bib → modkey.bib` → `biblio_compile → compiled.bib`.

`render.yml` declares `bib_sources` (list of intermediate .bib files) and `bibliography` (final compiled output). Missing sources are skipped gracefully.
