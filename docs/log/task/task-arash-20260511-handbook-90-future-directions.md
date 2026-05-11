---
title: "Handbook draft: 90-future-directions — agent hierarchies + live agent communication"
date: 2026-05-11
timestamp: 20260511-handbook-90-future-directions
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260511-184247-a050ee/note.md
completed: 2026-05-11T18:43:02+02:00
actionable: true
prompt: ""
source_note: docs/handbook/_outline.md
project_primary: projio
priority: medium
due: ""
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [handbook, writing, stack-axis, agentic-workshop-2026-09, chapter-90-future-directions]
model_hint: opus
---

## Task

Draft prose for the two sub-chapters under `docs/handbook/90-future-directions/`.
This chapter is **forward-looking** — it covers ideas that go beyond the
current-stack baseline taught in chapters 00–80. Honest framing: speculation
grounded in concrete primitives that already exist (Claude Code SubAgent
pattern, Claude Agents SDK).

User directive (2026-05-11): *"future directions chapter: could cover some
new ideas with hierarchy of agents and agent-agent live communication via
claude agents sdk."*

User directive (2026-05-11, broader): *"always complete, never finished."*
Ship rough-but-complete drafts.

## Inputs (read first)

- Outline: [`docs/handbook/_outline.md`](../../handbook/_outline.md)
- Existing chapter 70-agentic for vocabulary continuity: [`docs/handbook/70-agentic/`](../../handbook/70-agentic/) (especially `captures-tasks-queues.md` — extends from chained dispatch to hierarchies + live dialogue)
- Existing chapter 80-orchestration for the worklog dispatch baseline: [`docs/handbook/80-orchestration/`](../../handbook/80-orchestration/)
- Stack-axis survey: [`docs/log/result/result-arash-20260508-stack-axis-survey.md`](../result/result-arash-20260508-stack-axis-survey.md) §"Captures → tasks pattern"
- 99-honest-gaps: [`docs/handbook/99-honest-gaps.md`](../../handbook/99-honest-gaps.md) — forward-link single-author fragility argument

## Sub-chapters to draft

| File | Words | Beats |
|---|---|---|
| `90-future-directions/agent-hierarchies.md` | 700–1100 | Claude Code's `Agent(subagent_type=...)` SubAgent pattern (Explore, Plan, code-reviewer, general-purpose); parent agent dispatching parallel specialists each with its own context window; the projio + worklog model as a *flat* dispatch graph today (each task in its own session) vs *hierarchical* (one parent session orchestrating live children); when hierarchy pays off (context-window isolation; specialization; parallel speculation) and when it doesn't (overhead, coordination cost, debugging surface); the workshop's chained-`after=` dispatch (this session's idea→survey→spec→roadmap) is a *temporal* hierarchy — the SubAgent model is a *spatial* hierarchy; honest gap: tooling for inspecting hierarchy state mid-run is immature |
| `90-future-directions/live-agent-communication.md` | 700–1100 | Beyond batch dispatch: live message-passing between concurrent agents via Claude Agents SDK; supervisor agents intervening mid-task; peer agents exchanging hypotheses; persistent multi-agent sessions (the SDK's stateful runtime); what this enables (real-time critique, parallel exploration with shared memory, collaborative writing); what it complicates (rate limits compound, blame attribution gets harder, race conditions in shared state); honest gap: the SDK is new (2025-2026) and patterns are not yet established — this chapter is a sketch, not a recipe; cite the SDK by name without pretending to specify its API (it will evolve) |

## Universal constraints

- **Prose only.** Replace the `## TBD` section in each stub. Preserve the existing admonition "Sources & anchors" block.
- **Forward-looking ≠ ungrounded.** Anchor each speculative claim in something that already exists: SubAgent invocations the workshop can demo today, the `worklog_note(auto_dispatch=True)` + `schedule_queue(after=...)` chains, the Claude Agents SDK as a named public artifact.
- **No code examples that don't run.** It's fine to gesture at API shape; do not invent fictitious code blocks.
- **Cross-link to chapter 70-agentic** for the current-baseline pattern; cross-link to chapter 99-honest-gaps for the fragility argument.
- **No new explorables.** Forward-looking content gets no E1–E5 budget.
- **Honest scope.** This chapter exists to set direction, not to recommend production patterns. Say so in the opening of each sub-chapter.
- Build validation: `conda run -n rag python -m mkdocs build --strict` should pass after edits.

## Acceptance

- Both sub-chapters have prose bodies replacing the `## TBD` section
- Word targets ±20%
- Each beat in the table above is covered
- Existing admonition block preserved
- Cross-references to chapters 70-agentic and 99-honest-gaps present
- Strict build passes
