# pipeio Specifications

Design specifications for **pipeio** — an agent-facing authoring and discovery layer for computational pipelines in research repositories.

pipeio makes pipeline knowledge (registry, configs, rules, contracts, notebooks) queryable and actionable for AI agents. It delegates execution to Snakemake, provenance to DataLad, path resolution to snakebids, and app lifecycle to snakebids deployment modes.

## Spec Documents

| Spec | Domain | Status |
|------|--------|--------|
| [Ontology](ontology.md) | Concepts, entity relationships, directory conventions, naming | **Current** |
| [Overview & Architecture](overview.md) | Package scope, design principles, ecosystem fit | **Implemented** |
| [Registry](registry.md) | Pipe/flow/mod hierarchy, YAML schema, scan & validation | **Implemented** |
| [Flow Config](flow-config.md) | Per-flow `config.yml` schema, output registry (data contracts) | **Implemented** |
| [Path Resolution](path-resolution.md) | `PathResolver` protocol, `PipelineContext`, `Session`, `Stage` | **Implemented** (SimpleResolver + BidsResolver) |
| [Notebook Lifecycle](notebook.md) | Pair, sync, execute, publish — replacing Makefile shell scripts | **Implemented** |
| [Scaffolding](scaffolding.md) | Flow and mod creation from templates | **Implemented** (`flow new` + `mod_create`) |
| [Contracts](contracts.md) | Declarative input/output validation framework | **Implemented** (models + validation) |
| [CLI](cli.md) | Command-line interface design | **Implemented** (full surface + `pf` helper) |
| [MCP Tools](mcp-tools.md) | Agent-facing tools via projio MCP server (38 tools) | **Implemented** |

## Reference Implementation

These specs are derived from an audit of the pixecog project's pipeline infrastructure (`code/utils/io/`, `code/pipelines/`, `workflow/`). The audit document lives at `pixecog/prompts/plan/pipeio-audit-and-design.md`.

## Design Principles

1. **Agent-facing authoring layer** — pipeio makes pipeline knowledge queryable and provides safe authoring operations; it does not own execution, provenance, or path resolution
2. **One flow = one derivative** — each flow is a self-contained snakebids app producing one derivative directory; `pipe` is a category tag
3. **Delegation over duplication** — execution → Snakemake, provenance → DataLad, paths → snakebids `bids()`, app lifecycle → snakebids
4. **Declarative over imperative** — registries and configs are YAML; validation is schema-driven
5. **Graceful degradation** — pipeio works without optional extras (`[bids]`, `[notebook]`)
6. **Search before creation** — registry queries help discover existing flows before scaffolding new ones
7. **Notebook as first-class artifact** — the lifecycle (pair/sync/exec/publish) is managed, not ad-hoc
