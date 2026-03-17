# projio

Project knowledge orchestrator and MCP server for research repositories.

Generates project scaffolding (`.projio/` workspace, `Makefile`, `mkdocs.yml`, and optional kind-specific starters), builds project websites, and exposes a FastMCP server (stdio) that gives Claude unified access to indexio, biblio, notio, and codio tools.

## Install

```bash
pip install projio
# or editable with all ecosystem packages:
make dev
```

## Quick start

```bash
# Scaffold .projio/ workspace
projio init .

# Scaffold a thin package/tool project
projio init . --kind tool

# Scaffold a thin study project
projio init . --kind study

# Generated Makefile shortcuts
make projio-status
make projio-auth

# Scaffold ~/.config/projio/config.yml
projio config init-user

# Show merged user + project config
projio config -C . show

# Show status
projio status -C .

# Start MCP server (stdio)
projio mcp -C .

# Site operations
projio site build
projio site serve

# Project helpers
projio sibling github
projio sibling gitlab
projio sibling ria
projio docs mkdocs-init
projio auth doctor
```

For MkDocs projects, `projio` can also mount the `indexio` chatbot.
Set `site.chatbot.enabled: true` in `.projio/config.yml`; `projio site serve` will auto-start a local `indexio` backend and inject the widget into the served site.

## Helper config

Project-local defaults live in `.projio/config.yml` under `helpers:`.
Optional user defaults live in `~/.config/projio/config.yml` and are merged first, with project config taking precedence.
For GitHub and GitLab, DataLad/Git config remains the source of truth for site, access, and stored credentials; `projio` only fills project-local conventions and previews the resulting commands.

Helper commands are preview-first. Pass `--yes` to execute the generated `datalad` command.

## MCP tools exposed

| Tool | Description |
|------|-------------|
| `rag_query` | Semantic search against the project index |
| `rag_query_multi` | Multi-query search, deduplicated |
| `corpus_list` | List indexed corpora with chunk counts |
| `citekey_resolve` | Resolve BibTeX citekeys (requires biblio) |
| `paper_context` | Full paper context with docling excerpt (requires biblio) |
| `paper_absent_refs` | Unresolved GROBID refs (requires biblio) |
| `library_get` | Library ledger status/tags (requires biblio) |
| `note_list` | List recent notes (requires notio) |
| `note_latest` | Most recent note content (requires notio) |
| `note_read` | Read a specific note by path (requires notio) |
| `note_create` | Create a new note from template (requires notio) |
| `note_update` | Update note frontmatter fields (requires notio) |
| `note_types` | List configured note types (requires notio) |
| `note_search` | Semantic search over notes (requires notio) |
| `codio_list` | Filtered library listing (requires codio) |
| `codio_get` | Full library record (requires codio) |
| `codio_registry` | Full registry snapshot (requires codio) |
| `codio_vocab` | Controlled vocabulary for registry fields (requires codio) |
| `codio_validate` | Registry consistency check (requires codio) |
| `codio_discover` | Capability search across libraries (requires codio) |
| `codio_add_urls` | Add libraries from GitHub/GitLab URLs (requires codio) |
| `biblio_ingest` | Ingest papers by DOI via OpenAlex (requires biblio) |
| `biblio_library_set` | Bulk-update library ledger entries (requires biblio) |
| `project_context` | Project config + README snapshot |
| `runtime_conventions` | Parsed Makefile vars and commands |
| `site_detect` | Detect doc framework (mkdocs, sphinx, vite) |
| `site_serve` | Start doc server in background |
| `site_stop` | Stop a running doc server |
| `site_list` | List running doc servers |

## Claude Desktop / MCP config

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
