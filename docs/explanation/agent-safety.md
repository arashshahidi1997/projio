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

Running `projio add claude` or `projio claude update-permissions` scaffolds `.claude/settings.json` with pre-approved tools:

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
    "mcp__projio__agent_instructions",
    "mcp__projio__module_context",
    "mcp__projio__skill_read",
    "mcp__projio__rag_query",
    "mcp__projio__rag_query_multi",
    "mcp__projio__corpus_list",
    "mcp__projio__indexio_sources_list",
    "mcp__projio__indexio_status",
    "mcp__projio__indexio_build_status",
    "mcp__projio__citekey_resolve",
    "mcp__projio__paper_context",
    "mcp__projio__paper_absent_refs",
    "mcp__projio__library_get",
    "mcp__projio__biblio_grobid_check",
    "mcp__projio__biblio_docling_status",
    "mcp__projio__codio_list",
    "mcp__projio__codio_get",
    "mcp__projio__codio_registry",
    "mcp__projio__codio_vocab",
    "mcp__projio__codio_validate",
    "mcp__projio__codio_discover",
    "mcp__projio__codio_func_doc",
    "mcp__projio__note_list",
    "mcp__projio__note_latest",
    "mcp__projio__note_read",
    "mcp__projio__note_resolve",
    "mcp__projio__note_search",
    "mcp__projio__note_types",
    "mcp__projio__manuscript_list",
    "mcp__projio__manuscript_status",
    "mcp__projio__manuscript_validate",
    "mcp__projio__pipeio_flow_list",
    "mcp__projio__pipeio_flow_status",
    "mcp__projio__pipeio_nb_status",
    "mcp__projio__pipeio_nb_read",
    "mcp__projio__pipeio_nb_analyze",
    "mcp__projio__pipeio_nb_diff",
    "mcp__projio__pipeio_nb_audit",
    "mcp__projio__pipeio_nb_scan",
    "mcp__projio__pipeio_mod_list",
    "mcp__projio__pipeio_mod_resolve",
    "mcp__projio__pipeio_mod_context",
    "mcp__projio__pipeio_rule_list",
    "mcp__projio__pipeio_config_read",
    "mcp__projio__pipeio_registry_validate",
    "mcp__projio__pipeio_contracts_validate",
    "mcp__projio__pipeio_target_paths",
    "mcp__projio__pipeio_completion",
    "mcp__projio__pipeio_cross_flow",
    "mcp__projio__pipeio_dag_export",
    "mcp__projio__pipeio_run_status",
    "mcp__projio__pipeio_run_dashboard",
    "mcp__projio__datalad_status",
    "mcp__projio__datalad_siblings",
    "mcp__projio__site_detect",
    "mcp__projio__site_list"
  ]
}
```

With this configuration, the agent can freely query project knowledge but will prompt before calling write tools like `biblio_ingest`, `biblio_merge`, `biblio_docling`, `biblio_grobid`, `codio_add_urls`, `codio_add`, `indexio_build`, `indexio_sources_sync`, `note_create`, `note_update`, `notio_reindex`, `biblio_library_set`, `datalad_save`, `datalad_push`, `pipeio_run`, `pipeio_nb_create`, `pipeio_nb_sync`, `pipeio_nb_exec`, `pipeio_mod_create`, `pipeio_rule_insert`, `manuscript_build`, `manuscript_assemble`, or `site_build`/`site_serve`/`site_stop`/`site_deploy`.

## What the agent cannot do

Even with `mcp__projio__*` allowed, the projio MCP server does **not** expose:

- Shell execution or arbitrary command running
- File system access outside `PROJIO_ROOT`
- Network requests to arbitrary URLs (only structured API calls to OpenAlex, GitHub API, etc. as part of ingestion)
- Deletion of files from disk

Note: `pipeio_flow_deregister` removes a flow's entry from the registry YAML, but leaves all code and data files on disk. `pipeio_run_kill` terminates a `screen` session but does not delete outputs.

## Recommendations

| Scenario | Recommended permission |
|----------|----------------------|
| Personal research project, single user | `mcp__projio__*` — full autonomy |
| Shared repo, multiple contributors | Explicit read-only list — prompt for writes |
| CI/automated pipeline | No MCP permissions — use CLI commands directly |

## Setup commands

```bash
projio mcp-config -C . --yes        # generate .mcp.json (server config)
projio add claude                    # scaffold .claude/settings.json (client permissions)
projio claude -C . update-permissions  # update existing permissions to project root scope
```

Both `mcp-config` and `add claude` are idempotent — they skip files that already exist. To regenerate, delete the file and re-run. `claude update-permissions` always writes the updated permissions regardless of whether the file already exists.
