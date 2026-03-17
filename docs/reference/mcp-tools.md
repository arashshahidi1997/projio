# MCP Tools

The projio MCP server exposes tools across six categories. Optional tools require their ecosystem package to be installed.

## RAG tools (via indexio)

| Tool | Description |
|------|-------------|
| `rag_query(query, corpus="", k=8)` | Semantic search against the project index |
| `rag_query_multi(queries[], corpus="", k=5)` | Multi-query search, deduplicated |
| `corpus_list()` | List indexed corpora with chunk counts |

## Bibliography tools (via biblio)

### Read

| Tool | Description |
|------|-------------|
| `citekey_resolve(citekeys[])` | Resolve BibTeX citekeys to metadata |
| `paper_context(citekey)` | Full paper context with docling excerpt |
| `paper_absent_refs(citekey)` | Unresolved GROBID references |
| `library_get(citekey)` | Library ledger status and tags |

### Write

| Tool | Description |
|------|-------------|
| `biblio_ingest(dois[], tags=[], status="unread", collection="")` | Ingest papers by DOI via OpenAlex, generate citekeys, write BibTeX |
| `biblio_library_set(citekeys[], status="", tags=[], priority="")` | Bulk-update library ledger entries |

`biblio_ingest` resolves DOIs through the OpenAlex API, generates BibTeX citekeys, appends entries to the import bib file, and optionally sets library metadata and adds papers to a collection. Returns the list of generated citekeys.

`biblio_library_set` updates status (`unread`, `reading`, `processed`, `archived`), tags, and priority (`low`, `normal`, `high`) for multiple citekeys in a single call.

## Notes tools (via notio)

### Read

| Tool | Description |
|------|-------------|
| `note_list(note_type="", limit=20)` | List recent notes |
| `note_latest(note_type="")` | Most recent note content |
| `note_read(path)` | Read a specific note by path |
| `note_types()` | List configured note types and their modes |
| `note_search(query, k=5)` | Semantic search over notes |

### Write

| Tool | Description |
|------|-------------|
| `note_create(note_type, owner="", title="", date="")` | Create a new note from template |
| `note_update(path, fields)` | Update note frontmatter fields (JSON string) |

`note_create` renders the configured template for the given note type, creates the file, and returns the path. `note_update` parses `fields` as JSON and merges key-value pairs into the note's YAML frontmatter.

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

### Write

| Tool | Description |
|------|-------------|
| `codio_add_urls(urls[], clone=false)` | Add libraries from GitHub/GitLab URLs |

`codio_add_urls` parses repository URLs, fetches metadata from the GitHub API (language, license, description, topics), and creates catalog, profile, and repository entries automatically. Set `clone=true` to create local mirrors.

## Context tools

| Tool | Description |
|------|-------------|
| `project_context()` | Project config + README excerpt + key paths |
| `runtime_conventions()` | Parsed Makefile variables and commands |

## Site tools

| Tool | Description |
|------|-------------|
| `site_detect()` | Detect doc framework (mkdocs, sphinx, vite) |
| `site_serve(port, framework)` | Start doc server in background |
| `site_stop(port, pid)` | Stop a running doc server |
| `site_list()` | List running doc servers |

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
