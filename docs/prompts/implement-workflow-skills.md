# Workflow Skills — Design Record

## Status: Implemented (2026-03-23)

This document records the design decisions and implementation outcome for
projio's workflow skills system.

## What was built

### Prompt-based skills (no Python wrappers)

The original spec proposed Python `src/projio/skills/` with Pydantic models
composing MCP tools. This was rejected as premature overengineering. Instead:

- **Skills are structured markdown prompts** (SKILL.md files) that guide agents
  through multi-tool workflows
- **No Python skill layer** — the prompts + populated ecosystem data ARE the skills
- Agents read skills via `agent_instructions()` discovery or direct file read

### Three skill layers

| Layer | Location | Scope |
|-------|----------|-------|
| **Ecosystem** | `docs/prompts/skills/` (bundled with projio) | Any projio project |
| **Tool-project** | `.projio/skills/` in tool repos (e.g. cogpy) | Package development |
| **Study-project** | `.projio/skills/` in study repos (e.g. pixecog) | Analysis workflows |

### Ecosystem skills (4)

| Skill | Grand routine step | Description |
|-------|-------------------|-------------|
| `idea-capture` | Step 1 | Capture analysis idea as structured note |
| `codelib-discovery` | Step 2 | Search code corpora for existing implementations |
| `literature-discovery` | Step 3 | Search paper corpus for methods and parameters |
| `rag-query` | Cross-cutting | Query code / docs / papers via RAG |

These live at `docs/prompts/skills/*/SKILL.md` and are discovered by
`_discover_skills()` as fallbacks when not overridden by project-level skills.

### Workflow prompts (5, pre-existing)

| Prompt | Phase | Grand routine steps |
|--------|-------|-------------------|
| `session-bootstrap.md` | Any | Context gathering at session start |
| `explore-idea.md` | Exploration | Steps 1-4: capture, discover, literature, decide |
| `implement-feature.md` | Exploration | Steps 5-7: implement, test, demo |
| `integrate-pipeline.md` | Production | Steps 8-9: Snakemake integration |
| `validate-and-deploy.md` | Production | Pre-flight, validation, deployment |

These live at `docs/prompts/workflows/` and are discovered by
`_discover_workflow_prompts()`.

### Discovery infrastructure

`agent_instructions()` now returns:
- `skills` — list of available skills with name, description, path
- `workflow_prompts` — list of workflow prompts with name, when-to-use, path

Discovery scans project `.projio/skills/` first, then falls back to
ecosystem skills bundled with projio. Project skills override ecosystem
skills by name.

### Dual-agent compatibility

Skills use the SKILL.md format with YAML frontmatter. Both Codex and
Claude Code can consume them via symlinks:

- `.codex/skills → ../.projio/skills` (directory symlink)
- `.claude/commands/<name>.md → ../../.projio/skills/<name>/SKILL.md` (per-file)

## Key design decisions

- **Prompts are the source of truth** for workflow logic. No Python
  wrappers duplicate what the prompts already describe.
- **Skills compose MCP tools via instructions**, not code. The agent
  reads the skill and calls tools itself.
- **No state machine.** Phase awareness is heuristic — check recent notes,
  pipeline state, and context. Formalize later if needed.
- **Ecosystem data is the real enabler.** Skills only work well when the
  project's codio catalog, indexio corpora, and pipeio registry are
  populated. The skill can't discover code if there's nothing to search.

## What was NOT built (and why)

| Proposed | Decision | Reason |
|----------|----------|--------|
| `src/projio/skills/*.py` | Rejected | Prompts handle composition; Python wrappers would duplicate logic |
| Pydantic skill models | Rejected | Structured output comes from the MCP tools themselves |
| MCP skill tools (`explore_idea()`) | Rejected | Agent reads the prompt and calls existing tools directly |
| Phase detection state machine | Deferred | Simple heuristics via notes + pipeline state are sufficient for now |

## Files

- `src/projio/mcp/context.py` — `_discover_skills()`, `_discover_workflow_prompts()`, `agent_instructions()`
- `docs/prompts/skills/*/SKILL.md` — 4 ecosystem skills
- `docs/prompts/workflows/*.md` — 5 workflow prompts
- `docs/prompts/workflows/README.md` — workflow design document
