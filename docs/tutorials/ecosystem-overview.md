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

To install individual components:

```bash
pip install projio           # core only
pip install "projio[biblio]" # core + bibliography
pip install "projio[indexio,notio]" # core + search + notes
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

## Step 3: Initialize subsystems

Each ecosystem component scaffolds its own workspace:

```bash
# Bibliography workspace
biblio init .

# Notes workspace
notio init --write-config

# Code intelligence
codio init

# Semantic search (configure sources)
indexio init-config
```

After initialization, your project will have:

```
your-project/
├── .projio/config.yml      # projio config
├── bib/                    # biblio workspace
│   ├── main.bib
│   ├── srcbib/
│   └── config/
├── .codio/                 # codio registry
│   ├── catalog.yml
│   └── profiles.yml
├── notio.toml              # notio config
├── docs/
│   └── log/                # notio notes
└── infra/indexio/           # indexio config
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

## Step 5: Verify tools are available

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

## Step 6: Check project status

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

## Next steps

- [Agent-Driven Ingestion](agent-ingestion.md) — use Claude Code to ingest papers and code libraries
- [Project Setup Workflow](project-setup.md) — full bootstrap with DataLad siblings
- [Note-Driven Workflow](note-workflow.md) — create, search, and manage notes through MCP
- [Semantic Search Pipeline](search-pipeline.md) — build and query a project corpus
