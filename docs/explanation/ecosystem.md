# Ecosystem

`projio` is the workspace and orchestration layer for a small documentation and knowledge-tool ecosystem.

The split is deliberate:

- `projio` owns project-local scaffolding, docs-site workflows, and MCP exposure
- `indexio` owns semantic search and chat-backed retrieval
- `biblio` owns bibliography ingestion, enrichment, and bibliography-first sites
- `notio` owns notes, structured project logs, and manuscript assembly
- `codio` owns code-library and code-context discovery
- `pipeio` owns pipeline authoring, contracts, notebook lifecycle, and Snakemake integration
- `figio` owns declarative figure orchestration — FigureSpec YAML to SVG/PDF composition

## Role diagram

```mermaid
flowchart TD
    U[Project repository] --> P[projio]

    P --> S[Scaffolding and repo conventions]
    P --> D[Site workflows and deployment glue]
    P --> M[MCP server and tool surface]

    M --> I[indexio]
    M --> B[biblio]
    M --> N[notio]
    M --> C[codio]
    M --> Pi[pipeio]
    M --> F[figio]

    I --> IR[Semantic search and chatbot retrieval]
    B --> BR[Bibliography workspace and publication]
    N --> NR[Notes, logs, manuscripts, and project memory]
    C --> CR[Code discovery and reuse intelligence]
    Pi --> PiR[Pipeline authoring, contracts, notebooks]
    F --> FR[Declarative figure orchestration]

    B -. registers sources .-> I
    N -. registers sources .-> I
    C -. registers sources .-> I
    Pi -. notebooks .-> N
    F -. panels .-> N
```

`projio` is the coordinator. The sibling packages stay focused on their own domain, and `indexio` acts as shared retrieval infrastructure where cross-package search is needed.

## GitHub Pages

- `projio`: <https://arashshahidi1997.github.io/projio/>
- `indexio`: <https://arashshahidi1997.github.io/indexio/>
- `biblio`: <https://arashshahidi1997.github.io/biblio/>
- `notio`: <https://arashshahidi1997.github.io/notio/>
- `codio`: <https://arashshahidi1997.github.io/codio/>
- `pipeio`: <https://arashshahidi1997.github.io/pipeio/>
- `figio`: <https://arashshahidi1997.github.io/figio/>

## Mental model

Use `projio` when you need a repo-wide entrypoint that ties those tools together. Use the tool-specific docs when you are working inside one subsystem in depth.
