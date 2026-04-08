---
title: "Spec: questio loop mechanisms — investigate, iterate, orient"
date: 2026-04-08
timestamp: 20260408-043830
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260408-044902-3c4129/note.md
completed: 2026-04-08T04:49:03+02:00
actionable: true
source_note: "docs/specs/research-orchestration/design.md"
project_primary: projio
tags: [task, questio, spec]
---

# Spec: questio loop mechanisms — investigate, iterate, orient

## Goal

Write a spec document at `docs/specs/research-orchestration/loop-mechanisms.md` that defines three agent-driven loop patterns for the questio layer. These replace the rigid "validation notebook" approach with agent-as-judge patterns where Claude Code uses existing projio MCP tools to explore, iterate, and assess.

## Context

The questio design spec (`docs/specs/research-orchestration/design.md`) defines three loop levels (inner/middle/outer) in section 8. These are good architectural framing but assume pre-scripted validation notebooks — an approach we've rejected because:
- Writing domain-specific validation notebooks is the hard 80%, not infrastructure
- The agent (Claude Code) IS the judgment layer — it can read outputs, reason about quality, and make assessment calls
- Pre-scripted notebooks encode fragile assumptions about "what good looks like"

The new approach: teach the agent *investigation strategies* via skill prompts, but leave *judgment* to the agent's reasoning over tool outputs.

## Prompt

Write the loop mechanisms spec at `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md`.

**Step 1: Read context.**
- Read the full questio design spec: `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md` (especially sections 8.1-8.5 on workflow loops)
- Read the two source ideas that motivated this spec:
  - Idea 1 (questio-dispatch): resolve via `mcp__projio__note_read` or read `/storage2/arash/projects/projio/docs/log/idea/idea-arash-20260408-035007-479946.md`
  - Idea 2 (auto-QC): read `/storage2/arash/projects/projio/docs/log/idea/idea-arash-20260408-035035-245990.md`
- Read existing questio skills if any exist under `.projio/skills/questio-*.md`

**Step 2: Write the spec with these sections:**

### Section 1: Design philosophy
- Agent-as-judge: the agent IS the validation/assessment layer, not pre-scripted notebooks
- Skills encode *investigation strategy* (where to look, what order, when to escalate), not *judgment*
- Lightweight mid-loop recording — capture observations during iteration, not just at the end
- Human-in-the-loop by default for milestone status changes; full autonomy is a dial to turn later

### Section 2: Investigate loop
Pattern: human spots an issue or anomaly → agent digs in using projio tools → narrows cause → proposes explanation/fix → iterates if needed.

Define:
- **Entry conditions**: human flags an issue, questio_gap surfaces a blocker, unexpected pipeline output
- **Tool composition**: what tools the agent uses at each step (pipeio_target_paths to find outputs, pipeio_nb_read to inspect, pipeio_log_parse for errors, rag_query for prior decisions, paper_context for literature comparison)
- **Investigation strategy**: how the agent navigates from symptom to cause — the skill prompt teaches the pattern, not the domain-specific logic
- **Recording**: mid-loop observations via lightweight note_create (kind=idea, tags=[observation]) — not just final result notes
- **Exit conditions**: cause identified and fix proposed, OR escalation to human with evidence gathered
- **Failure modes**: what to do when investigation hits a dead end (escalate with summary), when outputs are ambiguous (present alternatives), when the issue is environment/infra not science (flag differently)

### Section 3: Iterate loop
Pattern: human has an idea about parameters/approach → agent implements → runs → evaluates → human gives feedback → agent adjusts.

Define:
- **Entry conditions**: human proposes a change, questio-next suggests a pipeline to run, agent identifies a parameter to tune
- **Cycle structure**: modify (config/notebook/script) → execute (pipeio_run or pipeio_nb_exec) → assess (read outputs, compare to expectations) → report to human → receive feedback → next cycle
- **Convergence criteria**: what "done" looks like — human says stop, metrics stabilize, quality criteria met
- **Parameter tracking**: how iterations are recorded (each cycle gets a lightweight observation note with what changed and what resulted)
- **Dry-run/confirmation**: mandatory preview before committing compute on expensive pipeline runs
- **Failure modes**: pipeline fails (check logs, diagnose, fix), results degrade (revert, investigate), human redirects (capture context, pivot)

### Section 4: Orient loop
Pattern: agent surveys project state → surfaces what needs attention → feeds into investigate or iterate.

Define:
- **Trigger**: session start, scheduled agent run, human asks "what's next?"
- **Tool composition**: questio_status → questio_gap → pipeio_flow_status for actionable flows
- **Output**: prioritized list of actionable items, each tagged as "investigate" (something looks wrong) or "iterate" (ready to run/improve)
- **Connection to other loops**: orient produces the entry conditions for investigate and iterate
- **The milestone→flow structured link**: orient depends on being able to resolve from questio milestones to pipeio flows. Specify that milestones.yml should have a `flow` field (not free-text pipeline recommendations). This is the critical infrastructure piece.

### Section 5: Cross-cutting concerns
- **Failure mode taxonomy**: retry (transient), investigate (unexpected), escalate (needs human), skip (blocked by external dependency)
- **Recording granularity**: result notes for milestone evidence, observation notes for mid-loop findings, decision notes for human direction changes
- **Propose-review-confirm pattern**: agent proposes milestone updates, human confirms. The spec must be explicit that full autonomy is opt-in, not default
- **Relationship to existing design.md**: this spec extends section 8, does not replace it. The inner/middle/outer loop framing remains valid — investigate and iterate are patterns within those loops, orient is the entry point

### Section 6: Skill mapping
Map loop mechanisms to concrete skills:
- `questio-investigate` — investigation loop skill prompt
- `questio-iterate` — iteration loop skill prompt (this replaces the rejected `questio-dispatch` as a standalone skill)
- `questio-orient` — orient loop, likely folded into existing `questio-session` or `questio-next`
- Updates needed to `questio-record` for mid-loop use
- Updates needed to `questio-ground` for investigation context gathering

**Step 3: Cross-reference** with design.md section 8 and note where the new spec supersedes or extends the existing loop definitions.

**Step 4: Commit** with message: "Add loop mechanisms spec for questio investigate/iterate/orient patterns"

## Acceptance Criteria

- [ ] `docs/specs/research-orchestration/loop-mechanisms.md` exists with all 6 sections
- [ ] Each loop has entry conditions, tool composition, exit conditions, and failure modes
- [ ] Milestone→flow structured link is specified
- [ ] Propose-review-confirm pattern is explicit
- [ ] Cross-references design.md sections correctly
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `08b012e5b5c7`
- session: `f5d805ae-69f7-4207-809b-3ee4b88ea1bb`
- batch duration: 425.8s
