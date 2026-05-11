# Captures, tasks, queues

!!! note "Sources & anchors"
    - **Stack component:** Agentic
    - **Canonical artifact:** this very session's `idea → task → result` chain (survey component 7 §Captures→tasks pattern)
    - **Workshop session:** Day-3 PM session 2 (iteration loop)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## The iteration loop

The previous three chapters set up an agent that knows the project, has
bounded permissions, and can read its own workflow skills. What remains
is the question of *where work comes from* and *where it goes*. The
answer is a three-stage flow:

```
worklog_note  →  promote_to_task  →  schedule_queue  →  execute_task
  (capture)       (notio note)         (queue entry)      (run + result)
```

A passing observation enters as a **capture**. Once it is worth acting
on, it is promoted to a **task** note in `docs/log/task/`. Once the task
is ready to run, it is enqueued. The agent on the queue executes it
into a **result** note in `docs/log/result/`. Each stage is durable on
disk; each transition is a discrete MCP call.

This chapter is the protocol for that loop.

## Stage 1 — Capture

The lowest-friction entry point is `worklog_note(text, project_id)`. It
takes a free-text observation and a project id, classifies it (idea,
issue, observation), and writes it to that project's `docs/log/<kind>/`
directory. The agent does not need to know the right project filesystem
layout; the worklog server handles it.

```python
worklog_note(
    text="lfp_extrema slow-wave config double-counts down→up zero-crossings — verify in detect_so_v2.",
    project_id="pixecog",
    kind="issue",
)
```

When the observation is well-scoped and obviously actionable, the same
call can dispatch it immediately:

```python
worklog_note(
    text="Add CHANGELOG.md to preprocess_motion flow per pipeline-docs.md spec.",
    project_id="pixecog",
    kind="issue",
    auto_dispatch=True,
    model="sonnet",
)
```

`auto_dispatch=True` performs the promotion-and-enqueue chain in one
call. The result is a queued task that an agent will pick up
automatically. **Use `auto_dispatch=True` only when the scope is clear
and the next step is unambiguous.** Otherwise, capture first and
promote later — the friction saves a confused run.

## Stage 2 — Promote to task

Captures that are not auto-dispatched accumulate. Periodically (or when
the queue is empty), promote the ones worth acting on:

```python
promote_to_task(source="idea-arash-20260507-221835-382557.md")
```

Promotion creates a new note in `docs/log/task/` with frontmatter
`status: scheduled` and a `## Prompt` body that the executing agent
reads. For agent-written captures the prompt body is a template pointing
back at the source; for voice captures the worklog server uses an LLM to
enrich the prompt — that is the only place LLM enrichment happens in the
pipeline. Agent-written notes get the template without an LLM call.

The promoted task note is the **single artifact** that the executing
agent reads. It contains the prompt, the model assignment, references
to source captures, and (once executed) backlinks to result notes. The
file is the protocol.

## Stage 3 — Schedule on the queue

`schedule_queue` enqueues a task for execution by a background runner:

```python
schedule_queue(
    task_path="docs/log/task/task-arash-20260511-handbook-70-agentic.md",
    project="projio",
    model="sonnet",
    scheduled_at="now",
)
```

Two scheduling modes matter:

- **Immediate.** `scheduled_at="now"` (the default) runs the task as
  soon as a worker is free.
- **After another task.** `after="<queue_id>"` chains the task behind a
  prior one — the new task does not start until the named entry has
  finished. This is the right tool for *dependent* work; do not use
  `auto_dispatch=True` for chains, because auto-dispatch starts
  immediately and cannot wait.

Queued entries have a 30-minute timeout. `tail_task(queue_id)` streams
output from a running task; `list_queue()` shows active entries
newest-first; `worklog queue cancel <id>` removes one.

## Model selection

Each queued task carries a model assignment. The cohort convention is
three tiers:

| Model | When to use |
|---|---|
| **haiku** | trivial scope: typo fixes, one-line config patches, single-file renames. Cheap and fast; not load-bearing. |
| **sonnet** | clear scope: a single module change with named files and acceptance criteria. The default for execution. |
| **opus** | open scope: multi-package refactors, architectural changes, synthesis tasks that require holding the whole project in context. The default for `auto_dispatch=True`. |

The rule of thumb: **opus for synthesis, sonnet for execution, haiku for
triage.** A task that is small but high-stakes (e.g. modifying a
permission file) should still go to sonnet — the model tier is not just
a price signal, it is a competence signal.

`auto_dispatch=True` defaults to opus because the default-use-case for
auto-dispatch is the multi-step synthesis path; if you want sonnet for
auto-dispatch, pass `model="sonnet"` explicitly.

## Three example flows

### A) Direct task — known scope, no promotion needed

```python
worklog_note(
    text="Refactor pipeio_target_paths to accept registry= override.",
    project_id="projio",
    kind="task",
    auto_dispatch=True,
    model="sonnet",
)
```

`kind="task"` wraps the body in `## Prompt`, writes the task note, and
enqueues it. One call, one queued task. Use this when you already know
what to do.

### B) Capture → promote → execute

```python
# In session: observation lands
worklog_note(
    text="Quarto reports keep losing CSL — investigate cause.",
    project_id="projio",
)
# Later: decided this is worth acting on
promote_to_task(source="idea-arash-20260511-...-csl-issue.md")
# At the end of the day: enqueue
schedule_queue(
    task_path="docs/log/task/task-arash-20260511-...-csl-issue.md",
    project="projio",
    model="opus",
)
```

Three separate calls give three opportunities to drop, refine, or
re-assign — the right shape for observations whose scope is not yet
clear.

### C) Dependency chain — sequential tasks

```python
# First task — block on its completion
q1 = schedule_queue(
    task_path="docs/log/task/task-...-handbook-70-agentic.md",
    project="projio",
    model="sonnet",
    scheduled_at="now",
)
# Second task waits for q1
schedule_queue(
    task_path="docs/log/task/task-...-handbook-80-orchestration.md",
    project="projio",
    model="sonnet",
    after=q1["queue_id"],
)
```

The chain runs sequentially. Use `after=` instead of `auto_dispatch=True`
when later steps need outputs from earlier ones. The
`feedback_schedule_queue.md` convention is explicit on this: chains use
`after=`, not auto-dispatch.

## This session as the canonical artifact

The chapter's own canonical artifact is **this very session's
`idea → task → result` chain.** A reader inspecting `docs/log/` in this
repository will find:

- `docs/log/idea/idea-arash-20260507-221835-382557.md` — the source idea
  note that seeded the handbook design.
- `docs/log/result/result-arash-20260508-stack-axis-roadmap.md` — the
  roadmap result note that derived the per-chapter drafting tasks from
  the idea.
- `docs/log/task/task-arash-20260511-handbook-70-agentic.md` (this
  chapter's task) and its siblings for chapters 10, 20, 30, 40, 50, 60,
  80 — each a `promote_to_task` output, each enqueued through
  `schedule_queue`.
- `docs/log/result/` — the result notes each task wrote on completion.

The chain is on-disk, reviewable, and reproducible. **The audit trail is
the workflow**, not metadata about the workflow. Two months from now,
the reason a result note exists will still be answerable: read its task
prompt, then the source idea note.

## Cross-project dispatch

Captures and tasks are routed by `project_id`. A note about pixecog
filed from a projio session lands in `pixecog/docs/log/...`, not in
projio's. The worklog server is the cross-project router; the registry
of projects (`worklog list_projects`) is its address book.

This means: **a session in any project can file work into any other.**
The agent does not need to switch projects to record an observation
about another. That is the property that closes the loop — observations
do not get lost between sessions because the agent had to "remember"
to come back. They are filed against the right project at the moment
they occur.

Cross-project orchestration — goals, critical paths, weekly focus — is
the subject of [`80-orchestration/`](../80-orchestration/worklog-overview.md).
This chapter has covered the unit of work; the next section covers how
many such units are coordinated across many projects.

## Further reading

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — the execution model underpinning `execute_task()` and `run_prompt()`; session and subagent lifecycle.
- **[Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models)** — haiku / sonnet / opus capability tiers; the basis for model selection in dispatch calls.
