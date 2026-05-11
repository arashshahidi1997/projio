# Goals and critical path

!!! note "Sources & anchors"
    - **Stack component:** Orchestration
    - **Canonical artifact:** [example: TBD] — `goal-arash-20260507-221912-674817` anonymized
    - **Workshop session:** Day-3 PM closing
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Goal definition, milestones, critical-path computation, weekly `focus()`.

## The planning gap the goal engine fills

The previous chapter introduced four orchestration components:
registry, captures, queue, goals. The first three are *event-driven*
— they react to whatever the researcher and the agent do. The fourth
is *control-driven* — it shapes what *should* be done next, given
deadlines and dependencies.

Research has no shortage of events. The shortage is a way to answer
three questions on Monday morning:

1. **What matters right now?**
2. **What should I do next?**
3. **What is drifting or blocked?**

Tasks alone do not answer these. A flat list of fifteen pending tasks
across six projects has no priority signal beyond what each task note
declared at creation time, no awareness of which deadlines have moved
closer since, and no model of which work blocks which other work. The
goal layer adds the missing structure.

## Goal notes

A goal is a markdown note in `docs/log/goal/` with frontmatter that
declares its planning identity:

```yaml
---
id: agentic-workshop-2026-09
title: "Deliver agentic-research workshop (4-day department course, Sept 2026)"
status: active
priority: 1
target_date: "2026-09-30"
progress: null
projects: [projio]
tags: [workshop, handbook, teaching]
---

## Objective
Deliver a 4-day practical workshop on the agentic research workflow…

## Milestones
1. Workspace provisioned — `teaching/agentic-workshop/` exists,
   registered in the orchestration registry, Quarto project
   scaffolded. (Target: 2026-05)
2. Announcement finalized & sent. (Target: 2026-06)
3. Syllabus drafted. (Target: 2026-07)
4. Day 1–3 materials drafted. (Target: 2026-08)
5. Dry run with 1 volunteer. (Target: mid 2026-09)
6. Workshop delivered (days 1–4). (Target: late 2026-09)
7. Post-mortem captured. (Target: early 2026-10)
```

The `id` is **stable** — once tasks reference a goal by id they must
not be silently renamed. Goal status follows a strict lifecycle:
`active → paused | done | dropped`. Priority is a manual ranking band
from 1 (critical) to 3 (nice-to-have). `target_date` is optional but
unlocks the urgency component of the agenda score; `progress` is an
optional 0–100 estimate that drives goal *pressure*.

The body sections are conventional but matter for the engine. The
**Milestones** list is the goal's decomposition into checkpoints. The
**Cross-references** section is where related ideas, prior task
notes, and dependent goals get cited. Both feed the critical-path
view.

## Tasks link to goals

Tasks gain four optional fields when a goal layer is in use:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `priority` | int | 2 | 1–3 manual ranking, same scale as goals |
| `due` | ISO date | `""` | Task-level deadline |
| `goal` | string | `""` | The goal `id` this task contributes to |
| `blocked` | bool | `false` | Whether the task is externally blocked |
| `blocked_by` | string | `""` | Free-text explanation (only when `blocked: true`) |

These are additive. A task without `goal: ...` is **unassigned** and
shows up in the agenda's *unassigned tasks* bucket. The agenda treats
this bucket as a low-priority backlog — visible, but not part of the
critical path.

## The agenda

`agenda()` (MCP) and `worklog agenda` (CLI) compute the prioritized
view that the planning loop consumes:

```python
{
  "generated": "2026-05-11T10:00:00+02:00",
  "goals": [
    {
      "id": "agentic-workshop-2026-09",
      "title": "Deliver agentic-research workshop…",
      "priority": 1,
      "target_date": "2026-09-30",
      "days_remaining": 142,
      "progress": 40,
      "pressure": 0.42,
      "projects": ["projio"],
      "tasks": [
        { "title": "Draft handbook chapter 80-orchestration",
          "status": "pending", "priority": 2, "due": "",
          "project": "projio", "blocked": false, "score": 4.42,
          "path": "docs/log/task/..." }
      ]
    }
  ],
  "unassigned_tasks": [ /* …pending tasks with no goal link */ ],
  "drift": [
    { "project": "cogpy", "days_silent": 4,
      "goals": ["agentic-workshop-2026-09"],
      "message": "cogpy: 4d silence, linked to workshop goal" }
  ],
  "next_action": {
    "title": "Draft handbook chapter 80-orchestration",
    "project": "projio",
    "goal": "agentic-workshop-2026-09",
    "reason": "P1 goal | goal pressure 0.42 | pending"
  }
}
```

The four fields encode the planning loop:

- **`goals`** — active goals, each annotated with `pressure` (how
  hard the goal is pushing on attention now), `days_remaining`, and
  the list of tasks attached to that goal.
- **`unassigned_tasks`** — pending and active tasks with no goal
  link; the backlog.
- **`drift`** — projects with no recent commits, captures, or queue
  activity but with active goals attached. The orchestration layer
  flags these so they don't quietly stall.
- **`next_action`** — the single highest-ranked task, with the
  reason it ranks first.

## Ranking: bands first, scores second

The agenda ranks tasks in two stages.

**Stage 1 — priority bands.** Tasks are grouped by their *effective*
priority, which is `min(task.priority, goal.priority)` when a goal
exists. A priority-2 task under a priority-1 goal gets promoted to
band 1. A task in band 1 always ranks above every task in band 2,
regardless of any computed score. **Manual priority dominates.**

**Stage 2 — score within band.** Inside each band, tasks sort by a
score combining three signals:

| Signal | What it captures |
|---|---|
| `goal_pressure` | `(100 − progress) / max(days_remaining, 1)`, capped at 10. Higher when the goal is behind and the deadline is near. 0 when no goal or no deadline. |
| `due_urgency` | Overdue → 10; due today → 7; due in N days → `7 / N`; no due date → 0. |
| `status_boost` | `+1` if the task is already in progress (`status: active`), 0 otherwise. |

The result is a number — useful for ordering, not for treating as a
measure of importance. **Bands carry the importance; scores break
ties within a band.**

## Critical path

The `critical_path` field on each goal is the ordered list of pending
tasks whose dependencies block the goal's earliest milestone. The
orchestration layer computes it by walking task `depends_on`
declarations and milestone references in the goal body. Where a task
declares no dependencies, it joins the critical path by recency on
the goal's last open milestone.

The critical path is a *suggestion*, not an authoritative scheduler.
The researcher reviews it, accepts or adjusts the order, and dispatches
the next step. The system never decides what to run unprompted.

## Weekly `focus()`

`focus()` is the planning surface that turns the agenda into a weekly
contract. It selects a small set of goals (or accepts an explicit
list) and pins them as **this week's focus**. The CLI:

```bash
worklog focus                          # show this week's focus
worklog focus -g workshop,handbook     # pin two goals
worklog focus --clear                  # reset
```

The pinned focus is consumed by every other tool in the orchestration
layer:

- `agenda()` highlights tasks under focused goals.
- Dispatch tools default to focused goals when no project is given
  explicitly.
- The drift detector raises warnings sooner for projects attached to
  the focused set.

The contract pattern is **soft**: focus does not prevent unrelated
work, it just changes what the planning surface foregrounds. The
researcher promises themselves they will spend most of the week on
the focused goals; the system makes that promise easier to keep.

## Capacity

`capacity()` complements `focus()`. It records the researcher's
declared availability in plain text:

```
54% session 2h25m | 69% weekly resets Wed 5PM
```

The orchestration layer reads this when ranking tasks: a long-running
dispatch (opus, multi-file) is deprioritized when session capacity is
near the cap; short tasks (haiku, single-file) are preferred. The
mechanism is intentionally soft — capacity is a hint, not a hard
schedule.

## The canonical example

The first end-to-end goal exercised in this repository is the
workshop goal cited at the top of this chapter. Its file (an
anonymized form of `docs/log/goal/goal-arash-20260507-221912-674817.md`)
contains:

- Stable `id` (`agentic-workshop-2026-09`) referenced by every
  handbook drafting task.
- A target date (`2026-09-30`) and milestones expressed as a numbered
  list with their own sub-deadlines.
- A `projects:` list (`[projio]`, since the workshop materials live
  in this repo) — though the work it enables touches several others.
- An *Objective* paragraph explaining what "done" looks like and a
  *Why this goal matters* section that names the constraints
  (the LSM Future Skills slot fixes the date; competing work on TAC
  + manuscript writing constrains the path).
- A *Cross-references* pointer to the originating idea note, so
  someone reading the goal cold can recover the design context.

That goal directly produced the task notes used to draft this chapter
and its siblings, and produced this very page as a result. The
captures → tasks → goals → result loop is **the artifact this
chapter is teaching**.

## Honest gap: goal coverage is shallow

At the time of the cohort survey, exactly one goal note exists in the
cohort (the workshop goal above). The goal engine is implemented and
exercised; the practice of authoring goal notes is not yet a baseline
discipline. The handbook treats the goal layer as a **graduated
practice**: install the surface, but expect a project to accumulate
its first goal only when it has multiple concurrent deadlines worth
coordinating. See [`99-honest-gaps.md`](../99-honest-gaps.md) for
the broader cross-cutting context.

The [final chapter](cross-project-dispatch.md) closes the loop:
*how* the orchestration layer turns a captured observation, ranked
against a goal, into a queued dispatch that returns a result note.

## Further reading

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — the agent primitives (tasks, sessions, captures) that goals decompose into when dispatched.
