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
- `src/projio/site.py` — MkDocs build/serve/publish wrappers
- `src/projio/helpers/` — DataLad sibling management (GitHub/GitLab/RIA), auth diagnostics, credential inspection. All sibling commands are **preview-first** (show command, require `--yes` to execute)
- `src/projio/mcp/` — FastMCP server exposing unified tools across all subsystems

### MCP Server

The MCP server (`src/projio/mcp/server.py`) is the primary agent interface. It registers tools from each subsystem module:

- `mcp/rag.py` — `rag_query`, `rag_query_multi`, `corpus_list`, `indexio_build`, `indexio_sources_list`, `indexio_sources_sync` (via indexio)
- `mcp/biblio.py` — `citekey_resolve`, `paper_context`, `paper_absent_refs`, `library_get`, `biblio_rag_sync`
- `mcp/notio.py` — `note_list`, `note_latest`, `note_search`, `notio_reindex`
- `mcp/manuscripto.py` — `manuscript_init`, `manuscript_list`, `manuscript_status`, `manuscript_build`, `manuscript_validate`, `manuscript_assemble`, `manuscript_figure_insert`
- `mcp/codio.py` — `codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`, `codio_discover`, `codio_rag_sync`, `codio_add`
- `mcp/pipeio.py` — `pipeio_flow_list`, `pipeio_flow_status`, `pipeio_nb_status`, `pipeio_nb_create`, `pipeio_nb_update`, `pipeio_nb_sync`, `pipeio_nb_diff`, `pipeio_nb_lab`, `pipeio_nb_publish`, `pipeio_nb_analyze`, `pipeio_nb_exec`, `pipeio_nb_pipeline`, `pipeio_mod_list`, `pipeio_mod_resolve`, `pipeio_mod_context`, `pipeio_mod_create`, `pipeio_rule_list`, `pipeio_rule_stub`, `pipeio_rule_insert`, `pipeio_rule_update`, `pipeio_config_read`, `pipeio_config_patch`, `pipeio_config_init`, `pipeio_target_paths`, `pipeio_completion`, `pipeio_cross_flow`, `pipeio_dag_export`, `pipeio_log_parse`, `pipeio_run`, `pipeio_run_status`, `pipeio_run_dashboard`, `pipeio_run_kill`, `pipeio_registry_scan`, `pipeio_registry_validate`, `pipeio_contracts_validate`, `pipeio_docs_collect`, `pipeio_docs_nav`, `pipeio_mkdocs_nav_patch`, `pipeio_modkey_bib`
- `mcp/datalad.py` — `datalad_save`, `datalad_status`, `datalad_push`, `datalad_pull`, `datalad_siblings`
- `mcp/site.py` — `site_detect`, `site_build`, `site_deploy`, `site_serve`, `site_stop`, `site_list`
- `mcp/context.py` — `project_context`, `runtime_conventions`

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

### Codio Library System Layers

Codio implements a multi-layer code intelligence system:
1. **Physical layer** — local code resources (mirrors, packages) in `code/lib/`
2. **Catalog** — machine-readable registry (name, language, repo URL, license, source paths)
3. **Project profile** — per-project interpretation (priority, runtime policy, capabilities)
4. **Curated notes** — human-written usage guidance, patterns, caveats
5. **Query layer** — MCP tools for discovery and inspection
