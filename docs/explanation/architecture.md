# Ecosystem Architecture

Projio follows a core design principle: **the repository is the primary unit of knowledge**. All project knowledge lives in or alongside the repository.

Projio does not replace existing research tools. Instead, it provides a unified query layer over the assets already present in the project.

## Components

Projio orchestrates four specialized subsystems, each managing a knowledge domain:

| Component | Domain | What it manages |
|-----------|--------|-----------------|
| indexio | retrieval | Corpus indexing, chunking, embedding, semantic search |
| biblio | literature | Bibliography management, citekey resolution, paper context |
| notio | notes | Structured project notes, experiment logs, decision records |
| codio | code intelligence | Library registry, code reuse discovery, implementation strategy |

Each component is an independent Python package. Projio integrates them through a shared MCP server, so agents and humans query a single tool surface regardless of how many subsystems are installed.

## Agent-first infrastructure

Projio is designed so that AI agents can interact with the repository in a structured way. Instead of relying on raw file search, agents query structured tools that expose project knowledge.

The MCP server registers tools from each installed subsystem. If a package is not installed, its tools are simply not registered — no errors, no stubs.

## Configuration merging

Two config files feed into the system:

1. **User config** (`~/.config/projio/config.yml`) — lab or personal defaults
2. **Project config** (`.projio/config.yml`) — project-specific overrides

These are deep-merged at runtime, with project values taking precedence. This lets a user maintain shared defaults across projects while keeping project-specific settings local.

## Repo-centric knowledge

All knowledge remains local to the project repository:

- Reproducibility through version control
- Offline access without external services
- Transparent provenance for all artifacts
- Long-term durability independent of cloud platforms

## Separation of concerns

Projio distinguishes between infrastructure it owns and infrastructure it delegates:

- **DataLad** owns credentials, hosting-site defaults, and sibling configuration
- **Git** owns transport and authentication
- **Projio** owns project-local conventions, preview UX, and cross-tool orchestration

Helper commands are preview-first: they compose a `datalad` command and display it, requiring `--yes` to execute.
