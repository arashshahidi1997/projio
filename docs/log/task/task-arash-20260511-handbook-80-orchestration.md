---
title: "Handbook draft: 80-orchestration — worklog, goals, cross-project dispatch"
date: 2026-05-11
timestamp: 20260511-handbook-80-orchestration
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260511-170051-a43585/note.md
completed: 2026-05-11T17:00:53+02:00
actionable: true
prompt: ""
source_note: docs/handbook/_outline.md
project_primary: projio
priority: medium
due: ""
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [handbook, writing, stack-axis, agentic-workshop-2026-09, chapter-80-orchestration]
model_hint: opus
---

## Task

Draft prose for every sub-chapter under `docs/handbook/80-orchestration/`. Replace
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
| `worklog-overview.md` | 500–800 | Worklog as cross-project dispatch infrastructure (NOT as personal hub — per `feedback_worklog_personal.md`); registry of projects with kind+status+tags; captures store (voice/text); queue with status transitions; per-project goals; **important**: keep examples generic; mark `[example: TBD]` rather than citing personal goals |
| `goals-and-critical-path.md` | 600–900 | Goal definition (title, milestones, success criteria); critical-path computation across milestones; weekly `focus()` contracts; placeholder for **E5** (`<!-- TODO: E5 -->`) goal critical-path render; use a synthetic goal example (anonymize, do not cite `agentic-workshop-2026-09` directly in handbook prose — too self-referential for an evergreen surface) |
| `cross-project-dispatch.md` | 600–900 | `run_prompt(project, prompt)` for ad-hoc; `worklog_note(..., auto_dispatch=True, project_id=...)` for capture→task→run; `schedule_queue(task_paths, project, after=...)` for chains; the gamma/gpu routing model (per `feedback_gamma2_dispatch_routing.md` — keep generic for handbook); how this session's chain is one example pattern (cite by reference, not by personal goal ID) |



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

