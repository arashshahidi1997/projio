# Agent Safety & Permissions

How projio scopes agent access, and what to consider when granting tool permissions.

## Two layers of control

When an MCP-capable agent (Claude Code, Claude Desktop, etc.) interacts with a projio workspace, two independent layers govern what the agent can do:

| Layer | Controls | Configured in |
|-------|----------|---------------|
| **Client permissions** | Whether the agent can call a tool without prompting the user | `.claude/settings.json` (Claude Code) or equivalent |
| **Server scope** | What the tool can actually read or write | `PROJIO_ROOT` env var in `.mcp.json` |

These layers are independent. A tool can be *allowed* in the client but still restricted by the server — and vice versa.

## Server-side scope: `PROJIO_ROOT`

Every projio MCP tool receives the project root from the `PROJIO_ROOT` environment variable, set in `.mcp.json` at server launch:

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

All write operations — `biblio_ingest`, `codio_add_urls`, `note_create`, `biblio_library_set`, etc. — resolve paths relative to this root. The server does not accept absolute paths or `..` traversal. This means:

- **Papers** are ingested into `bib/srcbib/` under the project root
- **Library entries** are written to `.projio/codio/` under the project root
- **Notes** are created in `notes/` under the project root
- **Index data** lives in `.projio/indexio/` under the project root

The server enforces this boundary regardless of what the client allows.

## Client-side permissions: `projio add claude`

Running `projio add claude` scaffolds `.claude/settings.json` with pre-approved tools:

```json
{
  "allowedTools": [
    "Read",
    "Glob",
    "Grep",
    "Edit",
    "Write",
    "Bash(git:*)",
    "Bash(python:*)",
    "Bash(pip:*)",
    "Bash(pytest:*)",
    "Bash(make:*)",
    "mcp__projio__*"
  ]
}
```

The `mcp__projio__*` wildcard allows the agent to call any projio MCP tool without prompting. This is safe because:

1. **The server is project-scoped** — writes are confined to `PROJIO_ROOT`
2. **The tools are structured** — they accept typed parameters (DOIs, citekeys, URLs), not arbitrary shell commands
3. **The server is your own tooling** — projio is installed in your environment, not a third-party service

This is the same trust model as `Bash(make:*)` — you trust your Makefile to do reasonable things within the project.

## Granular permissions

If you prefer to auto-approve read tools but prompt for writes, replace the wildcard with explicit entries:

```json
{
  "allowedTools": [
    "mcp__projio__project_context",
    "mcp__projio__runtime_conventions",
    "mcp__projio__rag_query",
    "mcp__projio__rag_query_multi",
    "mcp__projio__corpus_list",
    "mcp__projio__citekey_resolve",
    "mcp__projio__paper_context",
    "mcp__projio__paper_absent_refs",
    "mcp__projio__library_get",
    "mcp__projio__codio_list",
    "mcp__projio__codio_get",
    "mcp__projio__codio_registry",
    "mcp__projio__codio_vocab",
    "mcp__projio__codio_validate",
    "mcp__projio__codio_discover",
    "mcp__projio__note_list",
    "mcp__projio__note_latest",
    "mcp__projio__note_read",
    "mcp__projio__note_search",
    "mcp__projio__note_types",
    "mcp__projio__site_detect",
    "mcp__projio__site_list",
    "mcp__projio__biblio_grobid_check"
  ]
}
```

With this configuration, the agent can freely query project knowledge but will prompt before calling write tools like `biblio_ingest`, `biblio_merge`, `biblio_docling`, `biblio_grobid`, `codio_add_urls`, `indexio_build`, `note_create`, `note_update`, `biblio_library_set`, or `site_serve`/`site_stop`.

## What the agent cannot do

Even with `mcp__projio__*` allowed, the projio MCP server does **not** expose:

- Shell execution or arbitrary command running
- File system access outside `PROJIO_ROOT`
- Network requests to arbitrary URLs (only structured API calls to OpenAlex, GitHub API, etc. as part of ingestion)
- Deletion of files or data (tools are append/update only)

## Recommendations

| Scenario | Recommended permission |
|----------|----------------------|
| Personal research project, single user | `mcp__projio__*` — full autonomy |
| Shared repo, multiple contributors | Explicit read-only list — prompt for writes |
| CI/automated pipeline | No MCP permissions — use CLI commands directly |

## Setup commands

```bash
projio mcp-config -C . --yes   # generate .mcp.json (server config)
projio add claude               # scaffold .claude/settings.json (client permissions)
```

Both are idempotent — they skip files that already exist. To regenerate, delete the file and re-run.
