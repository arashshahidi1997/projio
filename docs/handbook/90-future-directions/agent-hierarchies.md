# Agent hierarchies

!!! note "Sources & anchors"
    - **Stack component:** Forward-looking (post-current-stack)
    - **Canonical artifact:** Claude Code's built-in `Agent` tool + the
      orchestration patterns in [`80-orchestration/`](../80-orchestration/worklog-overview.md)
    - **Workshop session:** Day-3 PM closing / post-workshop discussion
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Everything the handbook has taught so far assumes a *single agent session*
talking to the project through MCP. One Claude Code window, one main context,
one researcher reading the transcript. Dispatch crosses project boundaries
(chapter [cross-project-dispatch](../80-orchestration/cross-project-dispatch.md))
but each dispatched run is again one agent in one project — the *number of
agents working concurrently* is the only thing that changed.

This chapter looks at the next axis: **agents composed in a hierarchy.**
A parent agent fans out to specialised children, each with its own context
window and its own role, and the parent integrates their results. The
pattern exists today in fragmentary form; the question is how projio and
worklog grow into it.

## The one already in the room: `Agent(subagent_type=...)`

Claude Code already ships with a hierarchy primitive. The main session's
`Agent` tool launches a *subagent* with its own context window:

```python
Agent(
    subagent_type="Explore",
    description="Map the pipeio test layout",
    prompt="Inventory tests/ — list every test file under tests/pipeio, "
           "summarise what each one covers, and flag the three with "
           "lowest coverage relative to the corresponding mod.",
)
```

The subagent is a separate Claude process. It starts with no memory of the
parent conversation, runs its prompt to completion (using its own tool
calls — typically Read, Grep, Bash), and returns a single text result. The
parent receives that text as a tool result and continues. Subagents come in
named types: `Explore` (fast read-only searches), `Plan` (implementation
plans, no edits), `general-purpose` (full toolset, broader scope),
`code-reviewer`, and a few project-specific ones.

This is the **hierarchy primitive in its smallest form** — a parent that
needs a bounded slice of work done in a separate context, a child that does
it, a structured return. The parent's context window is protected from the
raw output (file lists, search results) of the child's work; the child gets
to focus on one well-scoped question.

Three properties matter:

- **Independent context windows.** The child's exploration does not consume
  the parent's tokens. A wide-ranging search that would have evicted the
  parent's working memory now lives in a sibling context that vanishes
  after returning.
- **Parallelism.** Multiple `Agent` calls in one parent turn run
  concurrently. The parent collects results when they all return.
- **Role specialisation.** `Explore` has a different system prompt and
  default tool set than `Plan` or `code-reviewer`. The hierarchy encodes
  *kinds of work*, not just *more workers*.

These three properties — bounded context, parallelism, role specialisation —
are the load-bearing features of any hierarchy worth scaling up.

## Where projio + worklog sit today

Today's projio + worklog stack is a **flat dispatch graph, not a hierarchy**.
The orchestration server enqueues runs; each run is a top-level Claude Code
session in some target project; there is no parent-child relationship
between runs except by `after=` dependency. The metaphor from chapter 80 is
*hub-and-spoke*: the orchestration hub routes work, the per-project
sessions do it.

The two layers do not currently compose:

1. **Inside a session**, the agent can fan out via `Agent(subagent_type=...)`.
   That hierarchy is opaque to worklog — the queue sees one running task,
   not the subtree of subagents inside it. There are no result notes for
   subagent runs.
2. **Across sessions**, worklog can chain runs via `schedule_queue(after=...)`.
   That graph is opaque to the in-session agent — the parent that dispatched
   a chain does not see its children's tool calls, only their result notes.

A real hierarchy would close that gap. A `Plan` subagent could itself
dispatch — through worklog — a queue of `Explore` runs across sibling
projects, integrate their results, and return a plan to its parent. The
parent would see a single subagent return; the queue would see a tree of
runs; each run's result note would record its place in the tree.

## What a composed hierarchy would look like

Sketch, not specification. The shape is:

```
parent session in project A
└── Agent(subagent_type=Plan, prompt="design the X migration")
    │
    ├── schedule_queue(task=..., project=B, model=sonnet)   ← worklog
    │   └── session in B writes result note, returns id
    ├── schedule_queue(task=..., project=C, model=sonnet)   ← worklog
    │   └── session in C writes result note, returns id
    └── Plan agent integrates both result notes, returns plan to parent
```

The Plan subagent is a *worklog client*. It can enqueue, await, and read
result notes from peer projects, just as a human operator does from chapter
80. The parent never sees B's or C's tool calls — it sees the synthesised
plan. The worklog queue records B's and C's runs as **children of the Plan
subagent's session**, so a reader walking `docs/log/` can reconstruct the
tree.

Three pieces are missing for that picture to be real:

- **Parent-id propagation in the queue.** Each queue entry needs a
  `parent_run_id` field. Today there is none; runs are flat. With the
  field, `list_queue()` can render trees.
- **Result-note backlinks.** A result note produced inside a subagent's
  dispatch chain should link back to its parent task. The plumbing exists
  for `after=` dependencies — extending it to `parent=` is a small change.
- **A worklog-aware subagent type.** Today `Plan` does not know about
  `schedule_queue`. A `Synthesise` or `Coordinator` subagent type, given
  the worklog MCP tools by default, would be the natural seat for
  hierarchical dispatch.

None of these are research problems. They are convention and tooling work,
the same shape as gap 7 in chapter [99-honest-gaps](../99-honest-gaps.md).

## What hierarchies buy that flat dispatch does not

Three things are awkward with the current flat model and would become
natural with composition.

**Triage at the front.** A capture lands in worklog. Today, either a human
or an `auto_dispatch=True` call commits the capture to a specific model,
project, and prompt template. A `Triage` subagent — small, cheap, opus
default — could classify the capture, decide which project owns the work,
and dispatch a sonnet executor with a sharpened prompt. The capture →
triage → dispatch chain is **one Plan subagent away** from existing.

**Multi-project synthesis.** A goal-level question ("which projects use
snakemake's `checkpoint` rule, and what's the convention?") today requires
the operator to manually dispatch one Explore run per project, read each
result, write a synthesis note. A Plan subagent would do all three. The
operator sees the synthesis; the trail is still on disk.

**Review-as-you-go.** A long-running task could fan out a `code-reviewer`
subagent after each significant edit, integrate the review, and continue or
abort. Today the equivalent is a separate scheduled review run after the
task completes — not a tight loop.

## New failure modes

Hierarchies are not free. Three failure modes appear at the seams.

**Context-drift between parent and child.** The child has no memory of the
parent's conversation. A poorly-bounded prompt leaves the child guessing
about assumptions the parent treats as obvious. The mitigation is
prompt-engineering discipline: a subagent prompt should read like a
self-contained ticket, not a snippet from a longer conversation. This is
already a Claude Code convention; hierarchies make it load-bearing.

**Model-tier mismatch.** Dispatch via `schedule_queue` exposes a `model`
argument; the `Agent` tool also has model defaults. A Plan subagent
running on opus that dispatches itself onto sonnet workers is a sensible
configuration; one that dispatches onto opus workers from inside an opus
subagent is a way to set money on fire. Hierarchical dispatch needs a
default-budget convention — probably the same opus-for-synthesis,
sonnet-for-execution, haiku-for-triage rule from chapter 70, applied at
each level of the tree.

**Opaque audit trails.** The Claude Code `Agent` tool returns the child's
final text but not its tool calls. If a subagent decides to dispatch four
worklog runs and one of them deletes a file, the audit trail for *why*
lives in the subagent's transcript — which is typically discarded when the
subagent returns. The projio principle survives only if dispatch from
inside subagents writes notes the same way human-initiated dispatch does.
**The disk is the audit trail; subagents must respect that.**

## What participates in the workshop and what doesn't

This chapter is in `90-future-directions/` because composed hierarchies are
not a workshop-ready pattern. Day 3 of the workshop ends with the flat
dispatch model from chapter 80 — file a capture, dispatch a run, chain two
with `after=`. The hierarchy primitive (`Agent(subagent_type=...)`) is part
of Claude Code itself and will appear in the workshop only as a *capability
already available in the editor*, not as a projio convention to teach.

The composition story — subagents that dispatch through worklog and whose
runs appear as a tree in the queue — is on the post-workshop roadmap. The
right time to formalise it is when a second project beyond projio itself
genuinely needs cross-project synthesis as a routine operation; until then
the work is one operator's, and the flat dispatch graph is adequate.

The pairing chapter
[live-agent-communication.md](live-agent-communication.md) takes the next
step: what happens when those subagents stop *returning* and start *talking*.

## Further reading

- **[Claude Code §Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)** — the current `Agent(subagent_type=...)` primitive that two-tier hierarchies are built on today.
- **[Model Context Protocol](https://modelcontextprotocol.io/)** — the shared communication layer that makes tool-access portable across agent tiers.
