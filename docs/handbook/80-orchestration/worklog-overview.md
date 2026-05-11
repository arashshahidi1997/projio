# Worklog overview

!!! note "Sources & anchors"
    - **Stack component:** Orchestration
    - **Canonical artifact:** [example: TBD] — placeholder
    - **Workshop session:** Day-3 PM closing
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Registry, captures, queue, goals.

## The orchestration layer

Every previous chapter is project-local. A single repository holds raw data
(BIDS), versioned subdatasets (DataLad), pipelines (Snakemake), notebooks
(Marimo), publication surfaces (MkDocs + Quarto), and the projio layer that
makes all of that queryable to an agent. Inside one project, that is enough.

A researcher rarely lives in one project. The cohort surveyed for this
handbook (`projio`, `cogpy`, `pixecog`, `gecog`, `msol`, plus
`sirocampus` as the lab-shared dataset) routinely interleaves work
across six or more repositories in a single week. An idea filed against
`pixecog` triggers a library change in `cogpy`; a manuscript-figure
request in `gecog` needs a data manifest from `pixecog`; a paper-ingest
batch lands in `sirocampus` and changes the citation set for every
project that imports it.

The **orchestration layer** sits one level above the projio layer and
answers cross-project questions: *which projects exist on this machine,
where do they live, what has been captured against them, what is queued
to run, what goals tie those captures together?* It is exposed through
its own MCP server (`mcp__worklog__*`) and a thin CLI.

The orchestration server is **independent of any one project**. It
holds no datasets, no pipelines, no manuscripts. Its store is a project
registry, a capture inbox, a task queue, and a goal index. Everything
substantive lives in the projects it points at.

## Four components

| Component | What it stores | What it answers |
|---|---|---|
| **Registry** | The list of projects (`workflow/projects.yml`) — id, kind, status, tags, per-environment paths | *What projects exist? Where does project X live on this host?* |
| **Captures** | Inbox of observations: voice notes, text notes, agent-filed `worklog_note(...)` calls | *What did I observe (or did an agent observe) and not yet act on?* |
| **Queue** | Scheduled and running task dispatches against specific projects | *What is the agent doing across projects right now?* |
| **Goals** | Cross-project goal notes (`docs/log/goal/<goal>.md`) with milestones, target dates, and per-project tasks | *Why is this work being done, and what is the path to done?* |

These are not four servers; they are four facets of one process. A
single MCP server (`worklog`) exposes tools across all four. The CLI
mirrors them — `worklog list`, `worklog queue`, `worklog goal_list`,
`worklog focus`. Either surface reaches the same underlying state.

## Registry: the cross-project index

The registry is a YAML file with one entry per project:

```yaml
- id: pixecog
  name: "Pixel-ECoG"
  kind: research
  status: active
  description: "Multi-host iEEG research project on stimulation effects"
  tags: [neuro, ecog, cognition]
  paths:
    local: /storage2/arash/projects/pixecog
    hpc:   /scratch/users/arash/pixecog
```

The two crucial fields are `id` (a short stable handle every other
worklog tool uses) and `paths` (per-environment absolute paths). A
researcher who works on a laptop locally and on a cluster remotely
gets the same `id` in both places; the registry resolves the host
appropriately. Not every project exists in every environment — the
registry simply records that absence.

The registry is **the single source of truth for what projects exist.**
Every cross-project query, including those routed by MCP tools to
agents in other repos, resolves a project handle through this file.

## Captures: observations before action

Captures are how observations *enter* the system without yet
committing to a task or a goal. The taxonomy is short:

- **Voice captures** — recorded into a Telegram-bot inbox and
  transcribed; tagged with a best-effort target project by an LLM
  classifier.
- **Text captures** — equivalent for typed input from the same
  surface.
- **Agent-filed captures** — every call to
  `worklog_note(text, project_id=<id>, kind=<kind>)` lands here. This
  is how an agent working in project A files an observation against
  project B without leaving its session.

A capture is **deliberately cheap**. It is a markdown note with a few
frontmatter fields (project, kind, source, classification confidence)
and a body of free text. It is *not* a task. Promoting a capture to
a task is a separate step (`promote_to_task(source)`), which lets the
researcher batch-triage captures rather than service every one the
moment it arrives.

Three capture surfaces matter for the workshop:

1. **`worklog_note(text, project_id)`** — the canonical MCP entry
   point. Used by agents during cross-project work; used by humans
   from the projio CLI as `projio note "..."` against the current
   repo.
2. **The voice inbox** — a non-stack surface (Telegram). The handbook
   mentions it for completeness but the workshop does not depend on it.
3. **`list_captures()` and `dismiss_capture(ids)`** — the triage
   surface. A researcher closes a capture either by dismissing it
   (not actionable) or by promoting it to a task.

## Queue: dispatched runs across projects

The queue is the orchestration layer's only piece of state with real
*timing*. A queue entry is a task note plus a model selection
(`haiku`/`sonnet`/`opus`), a target project, an optional `after`
dependency on another queue entry, and a status (`pending`,
`scheduled`, `running`, `completed`, `failed`, `cancelled`).

The queue answers *"what is the agent doing across projects right
now?"* and *"what is scheduled to run next?"* It is the artifact a
researcher consults in the morning to recall which dispatches finished
overnight and which need attention. From the CLI:

```bash
worklog queue           # active entries (pending/running/scheduled)
worklog queue list -s failed   # show recent failures
worklog queue tail <queue_id>  # follow a running task's log output
```

The queue exists so that **dispatching work is not the same as doing
work.** A researcher can file three task notes against three different
projects in a planning session, queue all three for the night, and
arrive next morning with three results notes to review. The
[next chapter on goals and critical path](goals-and-critical-path.md)
explains how the queue gets fed; the [final chapter on cross-project
dispatch](cross-project-dispatch.md) explains the dispatch mechanics
themselves.

## Goals: the *why* layer

Captures are observations. Tasks are scoped units of work. Goals are
the durable planning objects that bind tasks together over weeks or
months. A goal note (in `docs/log/goal/`) declares:

- A short stable `id` (e.g. `agentic-workshop-2026-09`).
- A title, status (`active`, `paused`, `done`, `dropped`), priority
  band (1–3), target date, and progress estimate.
- A list of `projects:` the goal spans.
- An *Objective* and a *Milestones* list in the body.

The goal layer is what makes the queue interpretable. A queue entry
that says "run pipeline X on project Y" is a unit of work; a goal
entry saying "deliver the agentic-research workshop by 2026-09-30"
explains *why* that work matters and *how it is progressing*. The
[goals-and-critical-path chapter](goals-and-critical-path.md) covers
the goal-engine mechanics in detail.

## The three-server baseline, revisited

The agentic chapter described the **three-server baseline** for a
projio-managed project: `projio`, `sirocampus`, `worklog`. Two of those
servers (`projio`, `sirocampus`) expose the same projio software
rooted at different repositories. The third (`worklog`) is *different
software entirely* — it exposes the orchestration tools described in
this chapter.

Every project-local agent therefore has, at every moment:

- A project-local view of its own knowledge (`mcp__projio__*`).
- A lab-shared view of the lab dataset (`mcp__sirocampus__*`).
- A cross-project orchestration view (`mcp__worklog__*`) — the
  registry, the capture inbox, the queue, the goals.

That third channel is what lets agents file observations against
sibling projects, query the project registry to resolve paths, and
report back into the queue when a dispatched task completes. Without
it, every cross-project interaction would have to be routed through
human-mediated `Read` and `Write` calls, and the agent would have no
way to discover what *projects* exist beyond its own root.

## Honest gap: orchestration adoption is uneven

The cohort survey records that the orchestration layer is functional
but unevenly load-bearing. The registry is universally consulted; the
queue is heavily used by the projects that practice scheduled
dispatch; goals are present in exactly one project at the time of the
survey (this one, projio, with the workshop goal cited as the canonical
example). The handbook treats orchestration as **infrastructure that
must be installed and configured before it pays off** — the *registry
+ queue* halves are baseline, the *goals + critical path* half is
graduated adoption.

The remaining two chapters of this section cover the parts that earn
their keep with sustained use: [goals and the critical path](goals-and-critical-path.md)
(planning surface, weekly focus), and [cross-project dispatch](cross-project-dispatch.md)
(how captures become queued runs that produce result notes).

See [`99-honest-gaps.md`](../99-honest-gaps.md) for the broader
context on the cohort's uneven adoption of agentic and orchestration
practices.

## Further reading

- **[Claude Code §Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)** — the subagent model that worklog's queue taps into; how sessions are isolated and parallelised.
- **[Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models)** — the model-tier ladder (haiku → sonnet → opus) that worklog uses for cost-sensitive dispatch.
