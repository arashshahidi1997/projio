# Cross-project dispatch

!!! note "Sources & anchors"
    - **Stack component:** Orchestration
    - **Canonical artifact:** survey component 7 §Captures→tasks pattern + this session's chain
    - **Workshop session:** Day-3 PM closing
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

`run_prompt`, `worklog_note(..., auto_dispatch=True, project_id=...)`,
`schedule_queue(after=...)` for chains.

## Why dispatch exists

The agentic chapter introduced one project, one Claude Code session,
three MCP servers, and a tightly-scoped permission allow-list. That
configuration is enough to do *one project's work* in one editor
session. It is not enough for the cross-project pattern this handbook
keeps citing: an idea filed against project A produces a task note
that the agent in project B picks up overnight; the result note lands
back in project A's `docs/log/result/` with cross-references to what
B did.

Cross-project dispatch is the orchestration layer's answer. It does
exactly one thing: **it runs Claude Code in a target project's
working tree with that project's MCP servers, allow-list, and notes,
and reports the outcome back to the queue.** A researcher can be
anywhere — in a different project's session, on the CLI, or on a
phone — and still cause work to happen against any project they
control.

The three primitives covered in this chapter are layers of the same
mechanism:

| Primitive | When to use |
|---|---|
| `run_prompt(project, prompt)` | Run synchronously, get the result back in this conversation. |
| `worklog_note(text, project_id, auto_dispatch=True, model=...)` | File-and-dispatch in one call. The capture promotes to a task note and the queue picks it up. |
| `schedule_queue([task_paths], project, scheduled_at=..., after=...)` | Run one or more existing task notes, optionally chained by dependency. |

Each goes through the same underlying executor; they differ in *who
authors the task* and *when it runs*.

## `run_prompt`: synchronous, in-band

`run_prompt(project, prompt)` is the simplest form. It blocks until
the target project's session finishes and returns the result inline:

```python
run_prompt(
    project="cogpy",
    prompt="check how electrode-impedance NaN values are handled "
           "in the lfp_e pipeline; report file path and behaviour",
)
```

This is appropriate when:

- The agent needs the answer *now* to continue its current work.
- The expected runtime is short (seconds to a couple of minutes).
- The output should land in the current conversation, not as a
  result note in the target project.

It is **inappropriate** when the work is long-running, when the
result should be reviewable later as an audit trail in the target
project's `docs/log/result/`, or when the dispatcher is content to
move on while the target session runs. For those cases the queue
mechanisms below are the right shape.

## `worklog_note(..., auto_dispatch=True)`: file and run

The pattern most often seen in cross-project work is **capture and
dispatch in a single call**:

```python
worklog_note(
    text="cogpy's electrode mapping silently drops channels with NaN "
         "impedance — fix or document",
    project_id="cogpy",
    kind="issue",
    auto_dispatch=True,
    model="opus",
)
```

What happens, step by step:

1. The capture is recorded in cogpy's inbox (`docs/log/issue/...`).
2. It is promoted to a task note (`docs/log/task/task-...md`) with a
   templated prompt body — for `kind="issue"`, the template is
   "fix-shaped"; for `kind="idea"`, "investigate-shaped"; for
   `kind="task"`, the text is used directly as the prompt.
3. The task is enqueued. The queue scheduler reserves a slot and
   runs a Claude Code session in cogpy's working tree with cogpy's
   `.claude/settings.json` allow-list and `.mcp.json` server set.
4. The session executes the prompt, edits files inside cogpy's
   bounded permission scope, and writes a result note to cogpy's
   `docs/log/result/`.
5. The queue entry status transitions
   `pending → running → completed | failed`.

The dispatcher *does not need access* to cogpy's filesystem. The
orchestration server resolves the path from the registry and runs
the executor as the user. The agent in project A does not get to
write to cogpy directly; it asks the orchestration layer to run an
agent **inside cogpy with cogpy's rules.** That is the
*hub-and-spoke* shape: cross-project communication routes through
the orchestration hub, never directly between project sessions.

### Model selection

The `model` argument selects the Claude model that will run the
dispatched task:

| Model | When to use |
|---|---|
| **`haiku`** | Trivial fixes, typos, single-file edits. |
| **`sonnet`** | Well-scoped issues, single-module changes, clear contract. |
| **`opus`** (default for `auto_dispatch`) | Multi-file architectural work, cross-package design, anything where synthesis matters. |

The rule is grounded in the cohort's actual usage pattern: opus for
synthesis (this includes most cross-project work), sonnet for
execution within a single module, haiku for triage.

`auto_dispatch=True` without a `model` defaults to opus on the
working assumption that anything important enough to dispatch
warrants the most capable model. The caller is free to override.

### `kind` and the prompt template

`worklog_note` accepts a `kind` parameter that shapes how the capture
gets promoted. Three kinds are special-cased:

- **`kind="issue"`** → fix-shaped prompt template. Body: "An issue
  was filed; reproduce, locate the cause, fix, write a result note."
- **`kind="idea"`** → investigate-shaped prompt template. Body:
  "An idea was filed; research the surrounding system, evaluate
  feasibility, produce a result note with recommendation."
- **`kind="task"`** → the body of the capture *is* the prompt. No
  LLM enrichment. This is how an agent files a direct, prompt-shaped
  task without an extra rewrite step.

Only voice captures trigger LLM enrichment when promoted. Agent-filed
captures use the templated prompts directly — cheap, deterministic,
auditable.

## `schedule_queue`: batches and dependency chains

For batches of pre-authored tasks, the orchestration layer exposes
`schedule_queue`:

```python
schedule_queue(
    task_paths=[
        "docs/log/task/task-arash-20260511-handbook-10-bids.md",
        "docs/log/task/task-arash-20260511-handbook-20-datalad.md",
        "docs/log/task/task-arash-20260511-handbook-30-snakemake.md",
    ],
    project="projio",
    scheduled_at="now",
)
```

Tasks in a single `schedule_queue` call **execute sequentially in
the order given**, regardless of the queue's concurrency setting.
Independent calls (different `schedule_id`) run in parallel up to
the scheduler's concurrency cap.

`scheduled_at` accepts:

- `"now"` — run as soon as a queue slot is free.
- An ISO timestamp — fire at the scheduled time.
- A short form like `"03:00"` — fire at the next local 3 AM.

### `after=` for explicit dependency chains

The ordering inside one `schedule_queue` call covers the common
"batch in sequence" case. For genuine dependency chains across
schedule boundaries, pass `after=<queue_id>`:

```python
queue_a = schedule_queue([task_a], project="projio", scheduled_at="now")
queue_b = schedule_queue([task_b], project="projio",
                          after=queue_a["queue_id"])
```

Task B will start when task A reports `completed`. Task A's `failed`
or `cancelled` status will leave B in `scheduled` indefinitely, where
the operator can decide to cancel, retry, or release the dependency.

**Hard rule:** do not use `auto_dispatch=True` for dependent chains.
`auto_dispatch` enqueues each task independently with no sequencing
guarantee. If task B reads outputs that task A must produce first,
use `schedule_queue` with explicit ordering — either within one call
or via `after=`. The mechanism exists; the discipline is choosing it.

## What happens inside a dispatched session

A dispatched session is a Claude Code subprocess. The orchestration
executor:

1. Resolves the project's filesystem path from the registry.
2. Reads the target project's `.claude/settings.json` `allowedTools`.
3. Launches `claude -p <prompt>` with `--allowedTools` populated
   from that list and `--permission-mode acceptEdits`.
4. Streams the session log to the queue entry's log file.
5. On exit, parses the session's *next steps* output and writes a
   result note to the project's `docs/log/result/`.

The dispatched agent has **exactly the permissions the target
project granted itself**. It cannot write outside the project's
scoped `Edit`/`Write` globs. It cannot reach into a sibling project's
filesystem except through the orchestration server's read-only
bridge tools (`worklog_read_file`, `worklog_search`,
`worklog_project_context`). This is the per-project sandboxing
contract: **the project owns its risk surface, the orchestration
layer respects it.**

## The session that produced this handbook

The canonical demonstration artifact for this chapter is the
session that produced the handbook itself:

- An **idea note** ([`docs/log/idea/idea-arash-20260507-221835-382557.md`](../../log/idea/idea-arash-20260507-221835-382557.md))
  capturing the workshop concept.
- A **synthesis task** that produced the
  [stack-axis survey](../../log/result/result-arash-20260508-stack-axis-survey.md)
  result note.
- A **goal note** ([`docs/log/goal/goal-arash-20260507-221912-674817.md`](../../log/goal/goal-arash-20260507-221912-674817.md))
  pinning the workshop deadline.
- A **batch of drafting tasks**, one per chapter
  (`task-arash-20260511-handbook-10-bids.md` …
  `-80-orchestration.md`), dispatched in parallel via independent
  `schedule_queue` calls so each chapter can run on its own model
  budget.
- A **result note** per chapter, written back to
  `docs/log/result/` by the dispatched session — this very file is
  one of them.

The chain is **the orchestration loop in one project**. Captures
become tasks become queued dispatches become result notes become
content. The handbook reader can walk the same trail by reading each
note in turn — the orchestration layer kept the receipts.

## Honest gap: dispatch is single-operator

The cohort survey records that cross-project dispatch is a real
working pattern, but only one operator currently uses it routinely.
The mechanism is well-defined; the practice is not yet shared. The
workshop introduces dispatch on Day 3 as the **closing pattern of
the agentic layer** — participants leave knowing how to file a
cross-project observation, dispatch a single-project run, and chain
two tasks by dependency. Multi-operator dispatch (multiple people
queuing into the same registry) is out of scope.

See [`99-honest-gaps.md`](../99-honest-gaps.md) for the cross-cutting
adoption gaps, including the single-author fragility note that
[`00-frame/single-author-fragility.md`](../00-frame/single-author-fragility.md)
expands on as a Day-1 framing concern.

## Further reading

- **[Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models)** — haiku / sonnet / opus capability tiers; guidance for matching model to task complexity in dispatch calls.
- **[Claude Code §Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)** — how the `Agent(...)` tool spawns isolated subagent contexts; the mechanism `run_prompt()` drives.
