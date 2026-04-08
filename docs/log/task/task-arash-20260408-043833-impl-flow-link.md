---
title: "Implement milestone→flow link in questio schema and tools"
date: 2026-04-08
timestamp: 20260408-043833
status: scheduled
actionable: true
source_note: "docs/specs/research-orchestration/design.md"
project_primary: projio
tags: [task, questio, impl]
---

# Implement milestone→flow link in questio schema and tools

## Goal

Add the `flow` field to the milestones.yml schema convention and update `questio_gap` to return it in structured output. Also update pixecog's milestones.yml with flow values.

## Context

The loop mechanisms spec requires the agent to resolve from questio milestones to pipeio flows without free-text parsing. The `flow` field in milestones.yml provides this structured link.

Read the updated design spec at `docs/specs/research-orchestration/design.md` (section 5.2) for the schema definition, and `docs/specs/research-orchestration/loop-mechanisms.md` (section 4) for how orient uses it.

## Prompt

**Step 1: Read the specs.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md` section 5.2 for the milestone schema with `flow` field
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md` for how the flow field is used

**Step 2: Update questio_gap tool** in `src/projio/mcp/questio.py`.
- When parsing milestones.yml, read the `flow` field
- Include `flow` in the structured output for each milestone returned by questio_gap
- If `flow` is not set, fall back to the first entry in `pipelines` list (backward compat)

**Step 3: Update questio_status tool** to also include the `flow` field in its output.

**Step 4: Update pixecog's milestones.yml** at `/storage2/arash/projects/pixecog/plan/milestones.yml`.
- Add `flow:` field to each milestone, mapping to the correct pipeio flow name
- For milestones spanning multiple flows (like preprocessing-stable), use the primary flow and keep `pipelines` for the full list

**Step 5: Validate** — run `questio_status` and `questio_gap` against pixecog to verify the flow field appears in output.

**Step 6: Commit** projio changes with: "Add flow field to questio milestone schema and tool output"
**Step 7: Commit** pixecog changes with: "Add flow field to milestones.yml"

## Acceptance Criteria

- [ ] questio_gap returns `flow` field per milestone
- [ ] questio_status returns `flow` field per milestone
- [ ] pixecog milestones.yml has flow values for all milestones
- [ ] Backward compatible when flow field is absent
- [ ] Both repos committed
