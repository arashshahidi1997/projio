---
title: "Spec: loop infrastructure — milestone→flow link, mid-loop recording, failure taxonomy"
date: 2026-04-08
timestamp: 20260408-043831
status: done
actionable: true
source_note: "docs/specs/research-orchestration/design.md"
project_primary: projio
tags: [task, questio, spec]
---

# Spec: loop infrastructure — milestone→flow link, mid-loop recording, failure taxonomy

## Goal

Extend the questio design spec (`docs/specs/research-orchestration/design.md`) with three infrastructure additions needed for the loop mechanisms to work. These are schema/convention changes, not new tools.

## Context

The loop mechanisms spec (task-arash-20260408-043830) defines investigate/iterate/orient patterns. Those patterns depend on infrastructure that doesn't exist yet:

1. **Milestone→flow link**: questio_gap returns milestone names and pipeline recommendations as free text. The agent has to parse natural language to resolve "Pipeline: preprocess_ieeg" to a pipeio flow. This is fragile. Milestones need a structured `flow` field.
2. **Mid-loop recording**: questio-record is designed for final evidence capture. The investigate and iterate loops need lightweight observation capture during iteration — "tried X, saw Y" notes that aren't full result notes.
3. **Failure taxonomy**: neither the design spec nor the loop spec defines what the agent should do when things go wrong. A shared vocabulary for failure modes enables consistent agent behavior.

## Prompt

Update the questio design spec in-place at `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md`.

**Step 1: Read the full design spec** to understand current schema and conventions.

**Step 2: Add milestone→flow link.**

In section 5.2 (milestones schema), add a `flow` field to the milestone schema:

```yaml
ttl-removal-validated:
  description: "TTL artifact removal validated for iEEG and neuropixels"
  flow: preprocess_ieeg          # NEW: pipeio flow name (structured, not free-text)
  pipelines: [preprocess_ieeg]   # keep for back-compat, but flow is the primary link
  depends_on: []
  status: in_progress
  evidence: []
```

Explain the design choice:
- `flow` is the primary structured link used by orient/dispatch logic
- `pipelines` remains for milestones that span multiple flows (e.g., preprocessing-stable needs both preprocess_ieeg and preprocess_ecephys)
- When `flow` is set, the agent can resolve directly to `pipeio_flow_status(flow)` without NLU
- `questio_gap` should return the `flow` field in its structured output

**Step 3: Add mid-loop recording convention.**

Add a new subsection (5.5 or similar) for observation notes:

- Observation notes use notio's existing `idea` type with `tags: [observation]`
- They do NOT need a dedicated note type — observations are lightweight, ephemeral
- Schema: `series` links to the flow, `tags: [observation, <loop-type>]` where loop-type is `investigate` or `iterate`
- Observations accumulate during a loop and are referenced when creating a final result note
- Convention: observation notes are *inputs to* result notes, not evidence themselves. They don't appear in milestone evidence lists.

**Step 4: Add failure mode taxonomy.**

Add a new section (8.6 or similar) defining shared failure vocabulary:

| Mode | Meaning | Agent action |
|------|---------|-------------|
| `retry` | Transient failure (timeout, resource contention) | Re-run with same parameters, max 2 attempts |
| `investigate` | Unexpected output (wrong values, empty files, partial results) | Enter investigate loop, gather evidence |
| `escalate` | Needs human judgment (ambiguous results, scientific interpretation) | Create observation note, present findings, ask human |
| `skip` | Blocked by external dependency (missing data, upstream incomplete) | Record blocker, move to next unblocked item |
| `abort` | Unrecoverable (corrupted data, infrastructure failure) | Stop loop, create detailed observation note, alert human |

Each mode has a max-iterations or timeout before escalating to the next level (retry→investigate→escalate).

**Step 5: Update questio_gap tool description** (section 6.1) to note that it returns the `flow` field from milestones.

**Step 6: Commit** with message: "Extend questio design spec: milestone→flow link, mid-loop recording, failure taxonomy"

## Acceptance Criteria

- [ ] `flow` field added to milestone schema in section 5.2 with rationale
- [ ] Mid-loop observation recording convention documented
- [ ] Failure mode taxonomy added with agent actions
- [ ] questio_gap tool description updated to include flow field
- [ ] Consistent with existing spec structure
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `08b012e5b5c7`
- session: `f5d805ae-69f7-4207-809b-3ee4b88ea1bb`
- batch duration: 425.8s
