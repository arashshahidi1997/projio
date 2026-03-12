# MCP Tools

The projio MCP server exposes tools across five categories. Optional tools require their ecosystem package to be installed.

## RAG tools (via indexio)

| Tool | Description |
|------|-------------|
| `rag_query(query, corpus="", k=8)` | Semantic search against the project index |
| `rag_query_multi(queries[], corpus="", k=5)` | Multi-query search, deduplicated |
| `corpus_list()` | List indexed corpora with chunk counts |

## Bibliography tools (via biblio)

| Tool | Description |
|------|-------------|
| `citekey_resolve(citekeys[])` | Resolve BibTeX citekeys to metadata |
| `paper_context(citekey)` | Full paper context with docling excerpt |
| `paper_absent_refs(citekey)` | Unresolved GROBID references |
| `library_get(citekey)` | Library ledger status and tags |

## Notes tools (via notio)

| Tool | Description |
|------|-------------|
| `note_list(note_type="", limit=20)` | List recent notes |
| `note_latest(note_type="")` | Most recent note content |
| `note_search(query, k=5)` | Semantic search over notes |

## Code intelligence tools (via codio)

| Tool | Description |
|------|-------------|
| `codio_list(kind, language, capability, priority, runtime_import)` | Filtered library listing |
| `codio_get(name)` | Full library record |
| `codio_registry()` | Full registry snapshot |
| `codio_vocab()` | Controlled vocabulary for registry fields |
| `codio_validate()` | Registry consistency check |
| `codio_discover(query, language)` | Capability search across libraries |

## Context tools

| Tool | Description |
|------|-------------|
| `project_context()` | Project config + README excerpt + key paths |
| `runtime_conventions()` | Parsed Makefile variables and commands |

## Server configuration

The server reads `PROJIO_ROOT` from the environment to determine the project directory.

When started via `projio mcp -C .`, the CLI sets `PROJIO_ROOT` automatically.

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
