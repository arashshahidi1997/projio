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

Projio orchestrates four specialized subsystems, each managing a knowledge domain:

| Component | Domain | Description |
|-----------|--------|-------------|
| **indexio** (née texio) | retrieval | Domain-agnostic corpus indexing, chunking, embedding, semantic search |
| **biblio** | literature | Bibliography management, citekey resolution, paper context extraction |
| **notio** | notes | Structured project notes (experiment logs, design decisions, idea capture) |
| **codio** | code intelligence | Library registry, code reuse discovery, implementation strategy |

These live as git submodules under `packages/` and are optional dependencies — the system degrades gracefully when any are absent.

### Source Layout

- `src/projio/cli.py` — CLI entry point (`projio` command), subcommand dispatch
- `src/projio/init.py` — Workspace scaffolding (three kinds: `generic`, `tool`, `study`)
- `src/projio/config.py` — Two-tier config: user (`~/.config/projio/config.yml`) merged with project (`.projio/config.yml`), project wins
- `src/projio/site.py` — MkDocs build/serve/publish wrappers
- `src/projio/helpers/` — DataLad sibling management (GitHub/GitLab/RIA), auth diagnostics, credential inspection. All sibling commands are **preview-first** (show command, require `--yes` to execute)
- `src/projio/mcp/` — FastMCP server exposing unified tools across all subsystems

### MCP Server

The MCP server (`src/projio/mcp/server.py`) is the primary agent interface. It registers tools from each subsystem module:

- `mcp/rag.py` — `rag_query`, `rag_query_multi`, `corpus_list` (via indexio)
- `mcp/biblio.py` — `citekey_resolve`, `paper_context`, `paper_absent_refs`, `library_get`
- `mcp/notio.py` — `note_list`, `note_latest`, `note_search`
- `mcp/codio.py` — `codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`, `codio_discover`
- `mcp/context.py` — `project_context`, `runtime_conventions`

Server is run via `python -m projio.mcp.server` with `PROJIO_ROOT` env var pointing to the target project.

### Agent Workflow Philosophy

Projio promotes **search before creation**: discover existing implementations, consult notes and literature, then make an explicit engineering decision (reuse, wrap, depend, or implement new). The MCP tools support this workflow by providing structured queries rather than raw file inspection.

### Codio Library System Layers

Codio implements a multi-layer code intelligence system:
1. **Physical layer** — local code resources (mirrors, packages) in `code/lib/`
2. **Catalog** — machine-readable registry (name, language, repo URL, license, source paths)
3. **Project profile** — per-project interpretation (priority, runtime policy, capabilities)
4. **Curated notes** — human-written usage guidance, patterns, caveats
5. **Query layer** — MCP tools for discovery and inspection
