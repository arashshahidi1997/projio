# Workflow Prompts

Composable, phase-specific prompt documents that guide an AI agent through the
projio research grand routine. Each prompt is self-contained: it lists the MCP
tools to use, the inputs it expects, and the structured output it should produce.

## Design

These prompts are **not code** — they are structured instructions an agent reads
(via RAG or direct file read) to self-direct through a workflow phase. They work
with any agent that has access to projio's MCP tools.

The key insight: agents have 33+ MCP tools but no idea *when* to use which. These
prompts provide the missing workflow awareness — the sequencing, gating, and
composition logic that turns a bag of tools into a coherent research workflow.

## Prompts

| Prompt | Phase | Grand Routine Steps |
|--------|-------|-------------------|
| `explore-idea.md` | Exploration | 1–4: capture, discover code, search literature, decide |
| `implement-feature.md` | Exploration | 5–7: implement, test, notebook demo |
| `integrate-pipeline.md` | Production | 8–9: Snakemake integration, registry, deploy |
| `session-bootstrap.md` | Any | Session start: context gathering, state awareness |
| `validate-and-deploy.md` | Production | Pre-flight checks, validation, site deployment |

## Usage

### From Claude Code

Point the agent at a workflow prompt:

```
Read docs/prompts/workflows/explore-idea.md and execute it for:
"Phase gradient travelling wave detection"
```

### Via RAG

Index the prompts directory so the agent can discover workflows:

```yaml
# .projio/indexio/config.yaml
sources:
  - id: "workflows"
    corpus: "docs"
    glob: "docs/prompts/workflows/*.md"
```

Then the agent can find the right workflow via:
```
rag_query("how to explore a new analysis idea", corpus="docs")
```

### As agent_instructions enhancement

Future: the `agent_instructions()` MCP tool could detect the current phase
(based on recent notes or active tasks) and return the appropriate workflow
prompt automatically.

## Composition

Prompts are designed to chain:

```
session-bootstrap → explore-idea → implement-feature → integrate-pipeline → validate-and-deploy
```

Each prompt produces structured output (usually a note) that the next prompt
consumes as input.
