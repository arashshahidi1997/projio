# projio

Project knowledge orchestrator and MCP server for research repositories.

Scaffolds `.projio/` workspaces, builds project documentation sites, and exposes a FastMCP stdio server that gives Claude unified access to indexio (semantic search), biblio (bibliography), and notio (notes) tools — all scoped to the current project root.

## Tutorials

- [Project Setup Workflow](tutorial/project-setup.md)

---

## Current status

**Version:** 0.1.0 (scaffolded, not yet published to PyPI)

### What works

- **Workspace scaffolding** — `projio init` writes `.projio/config.yml`, `mkdocs.yml`, and `docs/index.md` into a project directory. Config schema covers `indexio`, `biblio`, and `notio` sections.
- **Status reporting** — `projio status` shows index presence, git working-tree summary, and enabled ecosystem integrations.
- **Site operations** — `projio site build / serve / publish` wrap mkdocs; `publish` deploys to GitHub Pages via `gh-deploy`.
- **MCP server** — `projio mcp` starts a FastMCP stdio server exposing 12 tools across four modules:
  - **rag** — `rag_query`, `rag_query_multi`, `corpus_list` (via indexio)
  - **biblio** — `citekey_resolve`, `paper_context`, `paper_absent_refs`, `library_get` (optional; graceful error if biblio not installed)
  - **notio** — `note_list`, `note_latest`, `note_search` (optional; graceful error if notio not installed)
  - **context** — `project_context`, `runtime_conventions`
- **Project root resolution** — MCP server reads `PROJIO_ROOT` env var, set automatically by `projio mcp --root .`
- **JSON serialization** — `ensure_json_serializable()` handles `Path`, dataclasses, sets throughout all MCP tool returns
- **Subdataset layout** — `packages/indexio`, `packages/biblio`, `packages/notio` registered as datalad subdatasets; `make dev` installs all editably

### What is not yet done

- No tests written
- Not published to PyPI
- No mkdocs site configured
- biblio/notio MCP tool implementations are stubs pending the actual API surface of those packages
- No authentication or access control on MCP server
- `corpus_list` loads all Chroma metadata into memory (not paginated)

---

## Future plan

### Near-term (v0.1.x)

- [ ] Write test suite (`tests/`) — mock projio config, check CLI entry points, test MCP tool dispatch
- [ ] Publish to PyPI as `projio 0.1.0`
- [ ] Set up mkdocs site (material theme) — usage guide, MCP tool reference, `.projio/config.yml` schema
- [ ] Wire biblio MCP tools to the actual biblio Python API once that API is stable
- [ ] Wire notio MCP tools to the actual notio Python API

### Medium-term (v0.2)

- [ ] **Claude Desktop config generator** — `projio mcp install` writes the correct `mcpServers` block into `~/.config/claude/claude_desktop_config.json`
- [ ] **`projio index`** — convenience wrapper around `indexio build` that reads config from `.projio/config.yml` (no need to pass `--config` separately)
- [ ] **Workspace validation** — `projio doctor` checks that all configured paths exist, stores are populated, biblio/notio configs are reachable
- [ ] **Multi-project context** — `project_context()` tool optionally aggregates context from multiple `.projio/` registries (e.g. a lab-level superdataset)

### Longer-term (v0.3+)

- [ ] **HTTP MCP transport** — option to run the server over SSE/HTTP in addition to stdio, for use with remote Claude environments
- [ ] **Tool filtering** — `.projio/config.yml` `mcp.tools` allowlist so a project can expose only a subset of tools
- [ ] **Per-corpus tool variants** — auto-generate `rag_query_<corpus>` tools from the indexio config so Claude can target corpora without knowing their names
- [ ] **Audit log** — append MCP tool calls + args to `.projio/mcp.log` for reproducibility tracking
