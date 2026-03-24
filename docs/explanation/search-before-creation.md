# Search Before Creation

Before implementing new functionality or reading literature, the system encourages discovery of existing project knowledge.

## Typical order

1. Search local code intelligence (codio registry)
2. Inspect prior notes and documentation
3. Check external libraries
4. Consult literature
5. Implement new work

This reduces duplicated effort and improves reuse.

## From discovery to decision

Discovery results feed into explicit engineering decisions:

- **Reuse** existing internal implementation
- **Wrap** an external library with a project-specific interface
- **Depend** on an external library directly
- **Implement** new code

Projio aims to turn discovery into actionable engineering decisions rather than leaving agents to guess.

## Agent workflows

The MCP tool surface supports this workflow directly:

1. `codio_list` / `codio_discover` — search for existing implementations
2. `codio_get` — inspect curated library notes
3. `rag_query` — search code and documentation corpora
4. `note_search` — check prior design decisions
5. `citekey_resolve` / `paper_context` — consult literature

Parallel agents can study multiple libraries simultaneously. Results feed back into curated library notes for future reference.

## From tools to workflows

Having the right tools is necessary but not sufficient. The key bottleneck for autonomous agent productivity is **workflow awareness** — knowing when to use which tools in what sequence.

Projio addresses this at three levels:

### 1. Workflow prompts

Composable, phase-specific instruction documents at `docs/prompts/workflows/` that agents can read to self-direct:

| Prompt | Phase | Purpose |
|--------|-------|---------|
| `session-bootstrap.md` | Any | Context gathering at session start |
| `explore-idea.md` | Exploration | Capture idea, discover code, search literature, decide |
| `implement-feature.md` | Exploration | Implement, test, notebook demo |
| `integrate-pipeline.md` | Production | Snakemake integration, registry, docs |
| `validate-and-deploy.md` | Production | Pre-flight, validation, deployment |

These chain naturally: each prompt's output becomes the next prompt's input.

### 2. Cross-package skills (planned)

Python functions at `src/projio/skills/` that compose tools from multiple packages into a single call. For example, `explore_idea("phase gradient detection")` internally calls `codio_discover` + `rag_query` + `note_create` and returns a structured report.

### 3. Phase-aware routing (planned)

The `agent_instructions()` MCP tool will detect the current workflow phase from recent notes and active tasks, then suggest the appropriate workflow prompt — so the agent knows where it is in the routine without the user having to explain.

See the [Grand Routine tutorial](../tutorials/grand-routine.md) for the full end-to-end workflow.
