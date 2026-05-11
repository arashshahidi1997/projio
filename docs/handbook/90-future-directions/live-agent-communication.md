# Live agent-agent communication

!!! note "Sources & anchors"
    - **Stack component:** Forward-looking (post-current-stack)
    - **Canonical artifact:** the `schedule_queue(after=...)` chain pattern
      in [`cross-project-dispatch`](../80-orchestration/cross-project-dispatch.md)
      as the *baseline* this chapter steps beyond
    - **Workshop session:** Day-3 PM closing / post-workshop discussion
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

The previous chapter described what changes when one agent calls another
through a hierarchy. This one describes what changes when agents stop
calling each other through *function-return* semantics and start
**talking** — exchanging messages while both are still running. The
mechanism is provided by the Claude Agents SDK; the convention work is
projio's.

The honest framing first: **no projio project does this today.** The
chapter is in `90-future-directions/` for a reason. What it lays out is the
shape the orchestration layer would take if and when live agent-agent
dialogue moves from "available in the SDK" to "load-bearing in research
practice." The shape is interesting now because it changes what the
on-disk artifact convention has to guarantee.

## The current contract: file-mediated, async, durable

Cross-project dispatch as it stands has three properties worth naming
because they are exactly what live communication relaxes.

1. **File-mediated.** The unit of inter-agent communication is a note on
   disk. Agent A writes a task note; agent B (the executor) reads it; on
   exit, B writes a result note that A can read on its next session.
2. **Asynchronous.** A is not running while B runs. The queue is the
   handoff point. A might be gone by the time B finishes; the result note
   survives independent of either session.
3. **Durable.** Every interaction step exists on disk before the next step
   starts. A reader two months later can reconstruct the entire trail by
   walking `docs/log/`.

This is the protocol the chapter [captures-tasks-queues](../70-agentic/captures-tasks-queues.md)
called *the audit trail is the workflow*. It is the projio convention. It
is also, by design, a low-bandwidth protocol — one durable artifact per
turn, no in-flight state.

## What live communication relaxes

The Claude Agents SDK lets two agent sessions hold an open channel and
exchange messages while both run. Concretely:

- A **peer channel** — two sibling agents on a shared task swap status,
  partial results, and queries without going through disk.
- A **supervisor channel** — a long-running supervisor watches a worker's
  trace, sends mid-task corrections, and can intervene before the worker
  commits a wrong direction to disk.
- A **persistent session** — multiple agents (and operators) attached to
  the same session over hours or days, with shared mutable state.

The shape generalises a pattern that already exists in human research:
a co-author reviews a draft section while the author is still writing the
next one, and they talk. Live agent-agent communication is that same
shape applied to agent sessions.

Three things become possible that the file-mediated contract makes
awkward:

- **Tight feedback loops.** A reviewer agent observing an executor mid-run
  can flag a wrong turn at the moment it happens, not three result notes
  later.
- **Shared mutable state.** Two agents converging on a design can edit a
  shared scratchpad in the same window, rather than serialising disagreements
  through task notes.
- **Cross-project conversation, not just dispatch.** A session in project A
  and a session in project B could be held open simultaneously, both
  receiving operator input, both contributing to a shared cross-project
  result.

## What it costs

Every property the current contract guarantees becomes optional. Each one
that becomes optional is a new failure mode.

**Audit-trail loss.** A live channel does not write to disk by default.
Two agents that converge on a decision through twenty messages and then
write a single short result note have not left a reconstructible trail —
*why* the decision was made lives in volatile session state. The mitigation
is convention: any live conversation that produces a load-bearing decision
must write the transcript (or a structured summary of it) into
`docs/log/`. The orchestration server should make this cheap; the rule
must be cultural.

**Deadlock.** Two agents waiting on each other do not time out the way a
queue entry does. Channel-blocking await semantics need a watchdog. The
queue's 30-minute timeout was load-bearing in the file-mediated model —
worst case, a stuck run dies and the operator restarts it. Live channels
need an equivalent, applied to each waiting party.

**State divergence.** Two agents holding a shared mutable state have to
agree on its current value. The Agents SDK has primitives for this; the
projio question is what the on-disk projection looks like. A snapshot
written each time the shared state changes? A periodic checkpoint? A diff
log? Without a convention, the divergence lives only in the surviving
agent's memory.

**Operator surface area.** Each open live channel is a place an operator
might need to intervene. Today, an operator watches the queue; tomorrow,
they might be watching live channels for three concurrent sessions. The
single-author fragility from chapter [99-honest-gaps](../99-honest-gaps.md)
(gap 8) gets worse: the dispatch model can be operated by one person
because dispatch is asynchronous and bounded; live multi-agent operation
is not.

## What the projio convention will have to defend

Three principles from the rest of the handbook are at stake. Live
communication will be adoptable when the convention work is done to defend
each one.

**Receipts on disk.** Whatever the SDK provides for in-flight messaging,
the projio convention is non-negotiable: *no load-bearing decision lives
only in volatile state.* A live conversation that decides anything about
the project writes a note. The natural projio shape is a `kind=meeting`
note (already part of the notio note-type vocabulary) attached to the
channel session, periodically flushed.

**Per-project bounded permissions.** Chapter [permissions-and-bounded-context](../70-agentic/permissions-and-bounded-context.md)
established that each project owns its risk surface, and dispatched
sessions inherit the target project's permissions. Live channels cross
project boundaries differently from dispatch — both agents are running
*simultaneously*, both can edit files in their own project, and the channel
between them is a tool call rather than a filesystem write. The
permissions question is *which subset of channel operations* a project
allows. The shape probably mirrors the MCP allow-list — channels to named
peer projects, not arbitrary endpoints — but the spec is not written.

**Hub-and-spoke routing.** The current model routes through worklog as
the orchestration hub. Live channels could be peer-to-peer (two sessions
opening a direct channel) or hub-routed (channels brokered by worklog,
which can intervene). Hub-routed channels preserve the audit trail and
the intervention point; peer-to-peer channels are cheaper and lower-latency.
The default should be hub-routed, with peer-to-peer reserved for performance-sensitive cases.

## Why this chapter exists

It exists to mark a horizon line, not a milestone. The current orchestration
layer — flat dispatch, file-mediated handoff, durable notes — is **enough
for the workshop and the cohort.** Five projects, one operator, several
runs per day. The audit-trail-as-workflow contract holds because the
volume is small and the operator's memory fills the gaps.

The horizon arrives when one of three pressures appears:

- A second operator routinely dispatches into the same registry, and the
  asymmetric latency of file-mediated handoff (operator A's capture sits
  for hours before operator B sees the result) becomes the bottleneck.
- A single goal needs sustained cross-project synthesis — a multi-hour
  agent session spanning several projects, with intermediate decisions
  that don't naturally serialise to result notes.
- A class of agent work — review, triage, monitoring — that *belongs*
  alongside another agent's session rather than after it, and the
  schedule-after-completion model produces enough delay to lose context.

None of those pressures has materialised yet. The chapter exists so that
when they do, the convention work is not negotiated under deadline. The
gap is named, the principles to defend are named, and the workshop
attendees who will be the first to feel the pressure have a place in the
handbook to find the framing.

## Pointer to the rest

Where the rest of the handbook is the **current stack and the conventions
that hold it together**, these last two chapters mark the two open axes:
[agent-hierarchies](agent-hierarchies.md) (composition of agents into
trees) and this one (agents talking *across* the tree while still running).
Both axes share one constraint with everything else taught in the handbook:
**whatever the orchestration layer becomes, the project still has to be
able to answer the question "why does this file exist?" by reading what's
on disk.** That is the line the projio convention will defend at any
future scale.

## Further reading

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — the current session model; context for understanding what a persistent multi-agent session would extend.
