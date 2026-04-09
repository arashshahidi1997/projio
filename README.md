<p align="center">
  <img src="https://raw.githubusercontent.com/arashshahidi1997/projio/master/docs/assets/logo.png" alt="projio logo" width="200">
</p>

# projio

Project knowledge orchestrator and MCP server for research repositories.

Turns a research repository into a queryable knowledge environment for humans and AI agents. Provides structured, machine-accessible knowledge layers by integrating code, papers, notes, pipelines, figures, and documentation through a unified MCP server interface.

## Install

```bash
pip install projio                # core orchestrator + MCP server
pip install "projio[all]"         # all ecosystem packages
```

For development:

```bash
git clone https://github.com/arashshahidi1997/projio.git
cd projio
make dev
```

## Quick start

```bash
# Scaffold .projio/ workspace
projio init .

# Scaffold a study or tool project
projio init . --kind study
projio init . --kind tool

# Show project status
projio status -C .

# Start MCP server (stdio)
projio mcp -C .

# Site operations
projio site build
projio site serve
```

## Ecosystem

Projio orchestrates six specialized packages:

| Package | Domain | Description |
|---------|--------|-------------|
| **projio** | orchestration | Workspace scaffold, site workflows, MCP entrypoint |
| **indexio** | retrieval | Corpus indexing, chunking, embedding, semantic search |
| **biblio** | literature | Bibliography management, citekey resolution, paper context |
| **notio** | notes | Structured notes, idea capture, manuscript assembly & rendering |
| **codio** | code | Library registry, code reuse discovery, implementation strategy |
| **pipeio** | pipelines | Pipeline authoring, contracts, notebook lifecycle, Snakemake flows |
| **figio** | figures | Declarative figure specs, panel rendering, SVG/PDF composition |

Install individual extras: `pip install "projio[biblio]"`, `pip install "projio[pipeio]"`, etc.

## MCP tools

The MCP server exposes 70+ tools across all subsystems:

| Category | Tools | Examples |
|----------|-------|---------|
| **Retrieval** | 6 | `rag_query`, `rag_query_multi`, `corpus_list`, `indexio_build` |
| **Bibliography** | 26 | `biblio_ingest`, `citekey_resolve`, `paper_context`, `biblio_compile` |
| **Notes** | 10 | `note_create`, `note_list`, `note_search`, `notio_reindex` |
| **Manuscripts** | 16 | `manuscript_build`, `manuscript_assemble`, `manuscript_cite_check` |
| **Code** | 11 | `codio_list`, `codio_discover`, `codio_add`, `codio_registry` |
| **Pipelines** | 51 | `pipeio_flow_new`, `pipeio_run`, `pipeio_nb_exec`, `pipeio_dag_export` |
| **Figures** | 5 | `figio_build`, `figio_inspect`, `figio_validate` |
| **Project** | 10 | `project_context`, `ecosystem_status`, `site_build`, `datalad_save` |

See the [MCP tools reference](https://arashshahidi1997.github.io/projio/reference/mcp-tools/) for the full list.

## Configuration

Project-local defaults live in `.projio/config.yml`.
Optional user defaults in `~/.config/projio/config.yml` are merged first, with project config taking precedence.

```bash
# Scaffold user config
projio config init-user

# Show merged config
projio config -C . show
```

## Claude Code / MCP config

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

## Documentation

Full docs at [arashshahidi1997.github.io/projio](https://arashshahidi1997.github.io/projio/).

## License

MIT
