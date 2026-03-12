# Configure the MCP Server

## Start the server

```bash
projio mcp -C /path/to/project
```

The server runs over stdio using FastMCP.

## Claude Desktop configuration

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

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

## Claude Code configuration

Add to your project's `.mcp.json`:

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

## Optional ecosystem tools

The MCP server automatically registers tools for installed ecosystem packages:

- **indexio** — `rag_query`, `rag_query_multi`, `corpus_list`
- **biblio** — `citekey_resolve`, `paper_context`, `paper_absent_refs`, `library_get`
- **notio** — `note_list`, `note_latest`, `note_search`
- **codio** — `codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`, `codio_discover`

If a package is not installed, its tools are skipped gracefully.
