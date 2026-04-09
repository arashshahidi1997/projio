# Ecosystem Overview

This tutorial walks through installing the full projio ecosystem, initializing a workspace, connecting the MCP server, and verifying that all tools are available.

By the end you will have a working project with semantic search, bibliography management, structured notes, and code intelligence — all accessible to AI agents via MCP.

## Prerequisites

- Python 3.11+
- A git repository (or a new empty directory)
- Claude Code or Claude Desktop for the MCP agent interface

## Step 1: Install the ecosystem

Install projio with all ecosystem packages:

```bash
pip install "projio[all]"
```

This pulls in:

| Package | PyPI name | Domain |
|---------|-----------|--------|
| projio | `projio` | Orchestrator + MCP server |
| indexio | `indexio` | Semantic search / RAG |
| biblio | `biblio-tools` | Bibliography management |
| notio | `notio` | Structured notes |
| codio | `codio-tools` | Code intelligence |
| pipeio | `pipeio` | Pipeline registry + notebook lifecycle |
| figio | `figio-tools` | Declarative figure orchestration |

To install individual components:

```bash
pip install projio           # core only
pip install "projio[biblio]" # core + bibliography
pip install "projio[indexio,notio]" # core + search + notes
pip install pipeio           # pipeline management (separate package)
```

## Step 2: Initialize the workspace

From your project root:

```bash
projio init .
```

This creates:

- `.projio/config.yml` — project configuration
- `.projio/projio.mk` — Makefile include with shortcuts
- `Makefile` — project Makefile (if none exists)
- `.gitignore` — with managed projio section
- `docs/index.md` — documentation landing page
- `mkdocs.yml` — site configuration (if no framework detected)

For a Python package project, use:

```bash
projio init . --kind tool
```

For a lightweight study/analysis project:

```bash
projio init . --kind study
```

## Step 3: Activate subsystems

Use `projio init` with the `-c` flag to activate components in one step:

```bash
projio init -c full    # activates notio, biblio, codio, indexio, pipeio
```

Or activate individually:

```bash
projio add notio
projio add biblio
projio add codio
projio add indexio
projio add pipeio
projio add claude      # set up Claude Code permissions + CLAUDE.md
```

After initialization, all components live under `.projio/`:

```
your-project/
├── .projio/
│   ├── config.yml         # projio config
│   ├── packages.yml       # enabled packages
│   ├── projio.mk          # Makefile include
│   ├── notio/             # note templates
│   ├── biblio/            # bibliography marker
│   ├── codio/             # catalog.yml + profiles.yml
│   │   ├── catalog.yml
│   │   └── profiles.yml
│   ├── indexio/           # search config + index
│   │   └── config.yaml
│   ├── pipeio/            # pipeline registry
│   │   └── registry.yml
│   └── skills/            # project-level skills (optional)
├── bib/                   # biblio workspace (visible)
│   ├── main.bib
│   └── config/
├── notes/                 # notio notes
└── docs/
```

## Step 4: Connect the MCP server

Generate the MCP configuration automatically:

```bash
projio mcp-config -C .          # preview
projio mcp-config -C . --yes    # write .mcp.json
```

This writes a `.mcp.json` that Claude Code picks up on next launch:

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

If your projio ecosystem lives in a specific conda/venv environment, set the binary path in your user config:

```yaml
# ~/.config/projio/config.yml
runtime:
  python_bin: /path/to/envs/rag/bin/python
```

## Step 5: Configure agent permissions

Set up Claude Code to auto-approve projio MCP tools:

```bash
projio add claude
```

This creates `.claude/settings.json` with `mcp__projio__*` in the allowed tools list, so the agent can call any projio tool without prompting. The MCP server is already scoped to your project via `PROJIO_ROOT`, so all writes stay within the repo.

For details on the security model and granular permission options, see [Agent Safety & Permissions](../explanation/agent-safety.md).

## Step 6: Verify tools are available

Start Claude Code in your project directory. The MCP servers panel should show projio as connected.

Ask the agent to list available tools:

````
You: Call project_context to see the project metadata.
````

The agent calls `project_context()` and returns your project name, README excerpt, config, and key paths.

### Verify each subsystem

**Semantic search:**
````
You: List the indexed corpora.
````
Agent calls `corpus_list()` — returns available corpora with chunk counts.

**Bibliography:**
````
You: What note types are configured?
````
Agent calls `note_types()` — lists all configured types and their modes.

**Code intelligence:**
````
You: Show the codio vocabulary.
````
Agent calls `codio_vocab()` — returns the controlled vocabulary for registry fields.

**Notes:**
````
You: List recent notes.
````
Agent calls `note_list()` — returns the most recent notes across all types.

## Step 7: Check project status

From the command line:

```bash
projio status -C .
```

This reports which ecosystem components are detected and their configuration state.

To print clickable URLs for your repo and documentation:

```bash
projio url -C .
```

## What each subsystem provides

### indexio — Semantic search

Build a searchable corpus from your project's documents, code, and papers:

```bash
indexio build          # chunk and embed registered sources
```

Then query via MCP: `rag_query("travelling wave methods")` returns ranked passages with source attribution.

### biblio — Bibliography

Manage papers as structured data:

- Ingest by DOI via OpenAlex
- Generate BibTeX entries with deterministic citekeys
- Extract full text with docling
- Parse references with GROBID
- Track reading status and tags in a library ledger

### notio — Structured notes

Create templated markdown notes with frontmatter:

```bash
notio note meeting --title "Sprint sync"
notio note idea --title "New analysis approach"
notio toc --all    # rebuild indexes
```

Note types: daily, weekly, meeting, idea, issue, task, commit, personal — all configurable.

### codio — Code intelligence

Maintain a registry of libraries with structured metadata:

- Catalog (identity) + Profile (project-local policy)
- Controlled vocabulary for fields
- Capability search across registered libraries
- Bulk-add from GitHub/GitLab URLs

### pipeio — Pipeline management

Manage computational pipelines in a pipe / flow / mod hierarchy:

```bash
pipeio registry scan    # discover flows from filesystem
pipeio registry validate  # check registry consistency
pipeio flow list        # list all flows
```

Query via MCP: `pipeio_flow_list()` returns the registry, `pipeio_mod_list(pipe, flow)` returns mods within a flow, `pipeio_mod_resolve(modkeys)` resolves modkey strings.

### Skills — Agent workflow guidance

Projio ships ecosystem-level skills that guide agents through common workflows:

| Skill | Purpose |
|-------|---------|
| `idea-capture` | Capture analysis idea as structured note |
| `codelib-discovery` | Search code corpora for existing implementations |
| `literature-discovery` | Search paper corpus for methods and parameters |
| `rag-query` | Query code / docs / papers via RAG |

Skills are discovered automatically by `agent_instructions()`. Projects can add their own skills in `.projio/skills/` — these override ecosystem skills by name.

## Next steps

- [Agent-Driven Ingestion](agent-ingestion.md) — use Claude Code to ingest papers and code libraries
- [Project Setup Workflow](project-setup.md) — full bootstrap with DataLad siblings
- [Note-Driven Workflow](note-workflow.md) — create, search, and manage notes through MCP
- [Semantic Search Pipeline](search-pipeline.md) — build and query a project corpus
- [Grand Routine](grand-routine.md) — end-to-end research workflow: idea to deployed pipeline
