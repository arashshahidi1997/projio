# Configure the MCP Server

## Start the server

```bash
projio mcp -C /path/to/project
```

The server runs over stdio using FastMCP.

## Generate `.mcp.json` for Claude Code

The fastest way to configure Claude Code is to generate the config automatically:

```bash
projio mcp-config -C .          # preview what will be written
projio mcp-config -C . --yes    # write .mcp.json to project root
```

This reads `runtime.python_bin` from your projio config (user or project level) and writes a `.mcp.json` that Claude Code picks up automatically on next launch.

### Configure the Python binary

If your projio ecosystem is installed in a specific conda environment, set the binary path in your user config so every project uses it:

```bash
# ~/.config/projio/config.yml
runtime:
  python_bin: /path/to/envs/projio/bin/python
```

This avoids needing `conda activate` — the MCP server is invoked directly with the correct Python binary.

If `runtime.python_bin` is not set, `projio mcp-config` falls back to the current `sys.executable`.

### Output

`projio mcp-config --yes` writes a `.mcp.json` like:

```json
{
  "mcpServers": {
    "projio": {
      "command": "/path/to/envs/projio/bin/python",
      "args": ["-m", "projio.mcp.server"],
      "env": { "PROJIO_ROOT": "/absolute/path/to/project" }
    }
  }
}
```

### Merging into an existing file

If `.mcp.json` already exists, projio merges into it. It writes its own `projio` (and `worklog`) entries. Any other entry that runs `-m projio.mcp.server`, such as a lab hub with its own `PROJIO_ROOT`, gets the same interpreter, and any entry that runs `-m worklog.mcp_server` gets the `worklog-mcp` command. Their `env` is kept. Entries for other servers are not changed. The preview lists each `[add]` and `[update]` and warns about any command that still runs from a conda env, so running `projio mcp-config -C . --yes` once moves every projio-managed server to the current runtime.

### Custom output path

```bash
projio mcp-config -C . --output /custom/path/.mcp.json --yes
```

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

Add to your project's `.mcp.json` (or use `projio mcp-config` to generate it):

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

## A second server with fewer tools

A project often adds a second projio server pointing at another project,
say a shared lab project for its code library and bibliography. Both are
the same `projio.mcp.server`, so every tool name loads twice. Set
`PROJIO_MCP_TOOLS` on the second entry to keep only what it is for:

```json
{
  "mcpServers": {
    "projio": {
      "command": "projio-python",
      "args": ["-m", "projio.mcp.server"],
      "env": { "PROJIO_ROOT": "/path/to/your/project" }
    },
    "lab": {
      "command": "projio-python",
      "args": ["-m", "projio.mcp.server"],
      "env": {
        "PROJIO_ROOT": "/path/to/lab/project",
        "PROJIO_MCP_TOOLS": "codio,biblio,rag"
      }
    }
  }
}
```

The value lists subsystems and tool-name globs, separated by commas or
spaces; a `-` prefix removes (`biblio,-biblio_zotero_*`), and a list of
removals only starts from every tool. Unset or empty keeps every tool.
The server prints the kept count, and any entry that matches nothing, to
stderr at startup.

| Subsystem | Tools |
|---|---|
| `rag` | `rag_query`, `rag_query_multi`, `corpus_list` |
| `indexio` | `indexio_*` |
| `biblio` | `biblio_*`, `paper_*`, `citekey_resolve`, `library_get` |
| `codio` | `codio_*` |
| `notio` | `note_*`, `notio_*` |
| `manuscript` | `manuscript_*`, `master_*` |
| `present`, `report`, `pipeio`, `figio`, `questio`, `site` | `<name>_*` |
| `datalad` | `datalad_*`, `git_status` |
| `context` | `project_context`, `runtime_conventions`, `agent_instructions`, `module_context`, `skill_read`, `projio_init`, `ecosystem_status`, `permissions_sync` |

## Context tools (available unless `PROJIO_MCP_TOOLS` leaves them out)

- `project_context` — project config, README excerpt, key paths
- `runtime_conventions` — parsed Makefile variables and targets
- `agent_instructions` — tool routing table, workflow conventions, enabled packages. Cross-project orchestrators (e.g. worklog) call this before dispatching prompts to a project.

## Ecosystem tools

The MCP server automatically registers tools for installed ecosystem packages:

- **indexio** — `rag_query`, `rag_query_multi`, `corpus_list`, `indexio_build`
- **biblio** — `citekey_resolve`, `paper_context`, `paper_absent_refs`, `library_get`, `biblio_ingest`, `biblio_library_set`, `biblio_merge`, `biblio_docling`, `biblio_grobid`, `biblio_grobid_check`
- **notio** — `note_list`, `note_latest`, `note_search`
- **codio** — `codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`, `codio_discover`, `codio_add_urls`

If a package is not installed, its tools are skipped gracefully — the server still starts with the remaining tools.

## Verify

After generating `.mcp.json`, restart Claude Code in the project. The MCP servers panel should show projio as connected:

![Claude Code MCP servers panel showing projio connected](../assets/img/claude-code-mcp-servers.png)

Try:

> "Call `project_context` to see the project metadata."

If tools appear but return errors, check that the Python binary path is correct and that the ecosystem packages are installed in that environment.
