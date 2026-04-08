# Scenario Book — Agentic Research Workflows

**Status:** draft
**Date:** 2026-04-08
**Purpose:** Demonstrate what real human-agent conversations look like when using the projio ecosystem for research work. Each scenario shows the full conversation flow, which tools fire behind the scenes, and where human judgment drives the process.

These scenarios use **pixecog** (Neuropixels + ECoG analysis) as the concrete project and **TTL artifact removal** as the running example — a real critical-path milestone that gates all downstream analysis.

---

## Scenarios

| # | Scenario | Primary loop | Ecosystem breadth |
|---|----------|-------------|-------------------|
| 1 | [TTL characterization and removal](scenarios/scenario-ttl-removal.md) | Orient → Ground → Iterate → Record | questio, pipeio, codio, biblio, notio, indexio, worklog |
| 2 | [Investigating an anomaly mid-pipeline](scenarios/scenario-anomaly-investigation.md) | Investigate | questio, pipeio, biblio, notio |
| 3 | [Reproduce Siapas & Wilson 1998 coupling results](scenarios/scenario-reproduce-paper.md) | Ground → Iterate → Record | biblio, questio, codio, pipeio, notio, worklog |
| 4 | [Evaluating a new detection method from literature](scenarios/scenario-method-evaluation.md) | Ground → Iterate | biblio, codio, pipeio, notio, questio |
| 5 | [Debugging a cross-flow anomaly](scenarios/scenario-cross-flow-debug.md) | Investigate → Iterate → Record | pipeio, codio, biblio, notio, questio |
| 6 | [Drafting manuscript results from accumulated evidence](scenarios/scenario-manuscript-drafting.md) | Orient → Iterate → Record | questio, notio, figio, manuscripto, biblio, pipeio |
| 7 | [Unexpected finding leads to new hypothesis](scenarios/scenario-unexpected-finding.md) | Iterate → Investigate → Record | pipeio, biblio, questio, notio, worklog, codio |
| 8 | [Multi-day scheduled research sprint](scenarios/scenario-research-sprint.md) | Orient → Schedule → Monitor | questio, pipeio, notio, worklog, codio, biblio |

---

## Reading guide

Each scenario follows a consistent structure:

- **Starting state** — what's already in place before the conversation begins
- **Phases** — the conversation unfolds in numbered phases, each showing Human/Agent exchanges
- **Admonitions** — `!!! info "Behind the scenes"` shows MCP tool calls; `!!! tip` explains design patterns; `!!! warning "Human checkpoint"` marks confirmation points
- **Ecosystem coverage** — which subsystems and tools are exercised
- **Loop patterns** — which agentic loops (orient, ground, iterate, investigate, record) appear in each phase
- **Recording trail** — the notes created during the conversation
- **Key insight** — the main takeaway for that scenario

---

## Tool reference — what fires when

| Conversation moment | MCP tools / skills used |
|---|---|
| "What's the state?" | `questio_status`, `questio_gap`, `pipeio_flow_status` |
| "What does literature say?" | `paper_context`, `codio_get`, `rag_query`, `skill_read` |
| "Run this notebook" | `pipeio_nb_exec`, `pipeio_nb_read` |
| "Run the full pipeline" | `pipeio_target_paths` (preview), `pipeio_run`, `pipeio_run_status` |
| "Something looks wrong" | `pipeio_target_paths`, `pipeio_log_parse`, `pipeio_mod_context`, `paper_context` |
| "Record it" | `note_create` (observation during loop, result at convergence) |
| "Update the milestone" | YAML edit to `milestones.yml` (after human confirmation) |
| "Schedule this for later" | `worklog_note(auto_dispatch=True)` or `schedule_queue` |
| Mid-loop capture | `note_create(kind="idea", tags=["observation", "<loop-type>"])` |

---

## Anti-patterns — what this workflow is NOT

| Anti-pattern | What we do instead |
|---|---|
| Pre-scripted validation notebook that produces pass/fail | Agent reads outputs, compares to literature, presents judgment |
| Autonomous pipeline dispatch without human confirmation | Dry-run preview → human confirms → execute |
| Silent re-iteration when results are unexpected | Agent flags surprises immediately, presents options |
| Milestone auto-update after pipeline completes | Propose-review-confirm: agent proposes, human confirms |
| Monolithic "run everything" session | Incremental: characterize → validate one subject → validate all → record |
| Recording only at the end | Observation notes at each iteration, result note at convergence |
