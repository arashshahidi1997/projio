---
title: "Handbook draft: 70-agentic — Claude Code+MCP, permissions, skills, captures→tasks→queues"
date: 2026-05-11
timestamp: 20260511-handbook-70-agentic
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260511-170102-570c9e/note.md
completed: 2026-05-11T17:01:07+02:00
actionable: true
prompt: ""
source_note: docs/handbook/_outline.md
project_primary: projio
priority: high
due: ""
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [handbook, writing, stack-axis, agentic-workshop-2026-09, chapter-70-agentic]
model_hint: opus
---

## Task

Draft prose for every sub-chapter under `docs/handbook/70-agentic/`. Replace
the H1+stub body in each file with a rough-but-complete prose draft.

User directive (2026-05-11): *"complete the handbook asap, even today.
always complete, never finished."* Ship coverage of every beat in every
sub-chapter, not polish.


### Universal inputs (read first)

- Outline: [`docs/handbook/_outline.md`](../../handbook/_outline.md) — authoritative chapter spec
- Stack-axis survey: [`docs/log/result/result-arash-20260508-stack-axis-survey.md`](../result/result-arash-20260508-stack-axis-survey.md)
- Frame chapter drafts (just landed): [`docs/handbook/00-frame/`](../../handbook/00-frame/) — borrow vocabulary
- Workshop syllabus spec: [`docs/log/result/result-arash-20260508-stack-axis-syllabus-spec.md`](../result/result-arash-20260508-stack-axis-syllabus-spec.md) — to confirm workshop-session alignment


### Port source (read once if listed)

*No external port source. Greenfield draft from outline + survey.*

### Sub-chapters to draft


| File | Words | Beats |
|---|---|---|
| `claude-code-and-mcp.md` | 700–1000 | Claude Code as the editor + agent runtime; MCP server set (three-server baseline: projio + sirocampus + worklog); `.mcp.json` walkthrough on `pixecog/.mcp.json`; gecog's 4-server uniqueness (adds `cogpy`); MCP wire-shape (tool → schema → invocation); when to add a new MCP server vs use an existing tool |
| `permissions-and-bounded-context.md` | 700–1000 | `.claude/settings.json` walkthrough on `pixecog/.claude/settings.json`; the allow-list shape (`permissions.allow` + `allowedTools` must both contain `mcp__<server>__*` patterns); Bash command patterns; Read path globs; placeholder for **E4** (`<!-- TODO: E4 -->`) permission-scope diagram; bounded context as the agent's *real* constraint |
| `skills.md` | 500–800 | SKILL.md format (YAML frontmatter + body); ecosystem skills (under `src/projio/data/skills/`) vs project-local (`.projio/skills/`); `agent_instructions()` discovery; `skill_read(name)` MCP tool; honest: only 3/5 study projects have any project-local skill — introduce as "optional advanced," not baseline |
| `captures-tasks-queues.md` | 800–1100 | The capture→task→queue chain: `worklog_note(text, auto_dispatch=True)` → `promote_to_task` → `schedule_queue(after=...)`; model selection (haiku/sonnet/opus for triage/execution/synthesis); auto-dispatch vs scheduled chains; **this very session's idea→survey→spec→roadmap→tree-stub→frame-chapter→all-chapters chain is the canonical teaching artifact** — refer to it explicitly; the principle: agents work in a chain you can trace |



### Universal constraints

- **Prose only.** Do not create new chapter files. Do not rewrite `_outline.md`. Each stub already has an admonition block with "Sources & anchors" — preserve it. Append/replace under `## Frame` and replace `## TBD` with the prose.
- **Always complete, never finished.** Ship rough-but-complete drafts that cover every structural beat. Quality bar is "a reader can follow the argument end-to-end," not "publishable." Iteration comes later.
- **No bibliography wiring.** Cite source artifacts via repo-relative paths inline. The bib pipeline lands later.
- **No new explorables.** Marimo-WASM E1-E5 are separate tasks; if a chapter has a planned explorable per outline §F, leave a clearly-marked `<!-- TODO: Ex -->` HTML comment as placeholder.
- **Ground in the stack-axis survey** at `docs/log/result/result-arash-20260508-stack-axis-survey.md`. Every concrete example must trace to a survey artifact or be marked `[example: TBD]`.
- **Port source** (where listed in the chapter stub's admonition): read it once before drafting, extract structural ideas, but rewrite — do not paste verbatim. The port source is dated; the stack-axis frame is current.
- **Honest gaps reference forward.** If a chapter touches an honest gap from survey §"Honest gaps", mention it briefly and link to `99-honest-gaps.md`.
- **Build validation.** After all your edits in the chapter, run `conda run -n rag python -m mkdocs build --strict` (or skip if your environment lacks the `rag` env — note this in the result). Pre-existing INFO-level notio link warnings are not blocking; only fail on ERROR.
- **Cross-link policy** (from outline §D): handbook chapters cite source artifacts via repo-relative paths; do not link to `/storage2/...` working copies; do not mention worklog as a personal hub (per `feedback_worklog_personal.md` — worklog enters `80-orchestration/` as cross-project dispatch infrastructure only).


### Acceptance

- Every sub-chapter listed above has a prose body in place of the `## TBD` section
- Existing admonition block (Sources & anchors) preserved at top of each file
- Each draft hits the word target ±20% and covers all listed beats
- Cross-references to other handbook chapters use repo-relative paths
- `mkdocs build --strict` passes (or failure mode documented in result)

