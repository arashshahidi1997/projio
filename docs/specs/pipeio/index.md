# pipeio Specifications

Design specifications for **pipeio** — pipeline registry, notebook lifecycle, and flow management for research repositories.

pipeio is the fifth ecosystem subsystem in projio, managing computational pipeline workflows organized in a **pipe / flow / mod** hierarchy.

## Spec Documents

| Spec | Domain | Status |
|------|--------|--------|
| [Overview & Architecture](overview.md) | Package scope, design principles, ecosystem fit | Draft |
| [Registry](registry.md) | Pipe/flow/mod hierarchy, YAML schema, scan & validation | Draft |
| [Flow Config](flow-config.md) | Per-flow `config.yml` schema, output registry (data contracts) | Draft |
| [Path Resolution](path-resolution.md) | `PathResolver` protocol, `PipelineContext`, `Session`, `Stage` | Draft |
| [Notebook Lifecycle](notebook.md) | Pair, sync, execute, publish — replacing Makefile shell scripts | Draft |
| [Scaffolding](scaffolding.md) | Flow and mod creation from templates | Draft |
| [Contracts](contracts.md) | Declarative input/output validation framework | Draft |
| [CLI](cli.md) | Command-line interface design | Draft |
| [MCP Tools](mcp-tools.md) | Agent-facing tools via projio MCP server | Draft |

## Reference Implementation

These specs are derived from an audit of the pixecog project's pipeline infrastructure (`code/utils/io/`, `code/pipelines/`, `workflow/`). The audit document lives at `pixecog/prompts/plan/pipeio-audit-and-design.md`.

## Design Principles

1. **Workflow-engine-agnostic core** — the `PathResolver` protocol abstracts away Snakemake/snakebids; adapters implement it
2. **Declarative over imperative** — registries and configs are YAML; validation is schema-driven
3. **Graceful degradation** — pipeio works without optional extras (`[bids]`, `[notebook]`)
4. **Search before creation** — registry queries help discover existing flows before scaffolding new ones
5. **Notebook as first-class artifact** — the lifecycle (pair/sync/exec/publish) is managed, not ad-hoc
