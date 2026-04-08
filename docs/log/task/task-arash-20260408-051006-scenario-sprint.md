---
title: "Scenario book: multi-day scheduled research sprint"
date: 2026-04-08
timestamp: 20260408-051006
status: done
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: multi-day scheduled research sprint

## Goal

Write a scenario showing a researcher using worklog scheduling to run a systematic milestone-clearing sprint over multiple days, with automated orient → execute → record cycles and human checkpoints between days.

## Context

This scenario exercises the **worklog + questio scheduling workflow** — the most autonomous pattern, where background agents run research sessions on a schedule and the researcher reviews progress daily. It demonstrates how the orient loop, iterate loop, and worklog scheduling compose for sustained autonomous research.

The scenario should be written at `docs/specs/research-orchestration/scenarios/scenario-research-sprint.md`.

**Pixecog context:**
- After TTL removal is validated, multiple milestones are unblocked: ieeg-preprocessing-stable, ecephys-preprocessing-stable, brainstate-classification-validated
- Each is relatively straightforward (configure flow, run pipeline, validate outputs, record evidence)
- The researcher wants to clear all three preprocessing milestones over a week while focusing on other work
- Worklog tools: `schedule_queue`, `enqueue_task`, `list_queue`, `agenda`, `focus`
- The researcher reviews progress each morning via `questio_status` and `questio-report`
- Background agents follow the iterate loop pattern but with propose-review-confirm — they create result notes and PROPOSE milestone updates, they don't auto-apply

## Prompt

Write the scenario at `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/scenario-research-sprint.md`.

**Step 1: Read context.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` for format
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md`
- Read pixecog milestones.yml for the preprocessing milestone chain

**Step 2: Write the scenario.**

Structure:
1. **Header** with starting state: ttl-removal-validated is complete, three preprocessing milestones are unblocked, researcher wants to clear them over a week
2. **Day 1 morning: Planning session** — researcher says "I want to clear all preprocessing milestones this week. Can you set up a sprint?" Agent orients (`questio_status`, `questio_gap`), identifies the three targets, checks `pipeio_flow_status` for each. Proposes a schedule:
   - Day 1: iEEG preprocessing (remaining steps after TTL)
   - Day 2: ecephys preprocessing
   - Day 3: brainstate classification
   - Day 4: review all results, update milestones
3. **Day 1: Scheduling** — Agent creates task notes for each day's work using `worklog_note(kind="issue")` with detailed prompts. Schedules them via `schedule_queue` with time-based triggers (each morning at 03:00) or dependency-based (`after` previous task). Shows the actual schedule_queue calls.
4. **Day 1 evening: Background agent runs** — The scheduled agent runs the iEEG preprocessing pipeline: orients → grounds → runs pipeline → assesses → creates observation notes → creates result note → PROPOSES milestone update (does not auto-apply). Agent sends notification.
5. **Day 2 morning: Review** — Researcher opens a new session. Agent calls `questio_status` and `list_queue`. Shows: "iEEG preprocessing completed overnight. Result note created. Milestone update proposed — ieeg-preprocessing-stable → complete. Pending your review." Researcher reviews the result note, approves the milestone update. Ecephys task is already running.
6. **Day 3 morning: Course correction** — Ecephys preprocessing had an issue overnight (one subject failed). Agent reports the failure and observation notes from the background agent's investigation. Researcher says "skip sub-04 for now, it has known electrode issues." Agent updates the brainstate task to exclude sub-04 and re-schedules.
7. **Day 4: Sprint review** — All three milestones addressed. Agent runs `questio-report` for the week. Shows: milestones completed, milestones with caveats (sub-04 excluded), what's unblocked next (event detection milestones). Researcher decides on next sprint priorities.

Use mkdocs material admonitions:
- `!!! info "Behind the scenes"` for tool calls and scheduling details
- `!!! tip "Autonomy levels"` for explaining what background agents can and cannot do
- `!!! warning "Human checkpoint"` for morning reviews and milestone approvals
- `!!! danger "Course correction"` for the Day 3 failure scenario
- `!!! note "Scheduling pattern"` for explaining schedule_queue with after= dependencies
- `!!! example "Morning report"` for questio-report output

End with: ecosystem coverage (worklog + questio + pipeio — the scheduling triad), loop patterns (orient → scheduled iterate → human review cycle), key insight (answer: autonomous research sprints work when background agents PROPOSE and humans APPROVE — the daily review is the essential human-in-the-loop checkpoint that prevents autonomous drift).

**Step 3: Commit** with message: "Add scenario: multi-day scheduled research sprint"

## Acceptance Criteria

- [ ] File at `docs/specs/research-orchestration/scenarios/scenario-research-sprint.md`
- [ ] Shows worklog schedule_queue with time and dependency triggers
- [ ] Background agents follow propose-review-confirm
- [ ] Includes a failure/course-correction day
- [ ] Morning review pattern is explicit
- [ ] Uses mkdocs material admonitions
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `140acc720c2b`
- session: `49cfe4a4-561d-4bb8-8fb6-d01b2ac17020`
- batch duration: 801.3s
