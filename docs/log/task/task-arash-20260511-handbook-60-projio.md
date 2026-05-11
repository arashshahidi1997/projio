---
title: "Handbook draft: 60-projio — stack-aware layer, notio, pipeio, biblio+indexio, figio, codio"
date: 2026-05-11
timestamp: 20260511-handbook-60-projio
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260511-172045-67fd34/note.md
completed: 2026-05-11T17:20:48+02:00
actionable: true
prompt: ""
source_note: docs/handbook/_outline.md
project_primary: projio
priority: high
due: ""
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [handbook, writing, stack-axis, agentic-workshop-2026-09, chapter-60-projio]
model_hint: opus
---

## Task

Draft prose for every sub-chapter under `docs/handbook/60-projio/`. Replace
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


**Graded introduction sequence (do not change the order).** Each sub-chapter
introduces a subsystem motivated by a pain felt in the prior stack stages.

| File | Words | Beats |
|---|---|---|
| `00-stack-aware-layer.md` | 700–1000 | The pivot: the stack already does the work; projio makes it *queryable*. `project_context()`, `runtime_conventions()` MCP tools; six-subsystem map (codio, biblio, notio, figio, pipeio, indexio + manuscript); `projio sync` as the meta-command; what projio is NOT (not an alternative to Snakemake or DataLad — it knows about them) |
| `10-notio.md` | 600–900 | Pain solved: *why was this run produced?* — `docs/log/{idea,task,result,issue,meeting,...}/` as structured project memory; agent-activity trail; weekly/daily indexes; how this chapter you're reading is *itself* a notio result; show one task→result chain (this session's idea→survey→spec→roadmap is the canonical example) |
| `20-pipeio.md` | 1000–1400 | Densest chapter. Pain solved: hand-constructed BIDS wildcards. Flow registry (`.projio/pipeio/registry.yml`); `BidsPaths` adapter; `manifest.yml` as the cross-flow contract; `pipeio_target_paths(flow, group, member)` resolves to a path; ~50 MCP tools; one end-to-end example: `pixecog/lfp_extrema/` flow + `manifest_assemble` cross-flow gather; placeholder for **E3** (`<!-- TODO: E3 -->`) |
| `30-biblio-indexio.md` | 700–1000 | Pain solved: claims drift from data. Citekey resolution (Zotero export → merged.bib → compiled.bib); docling/grobid for PDF extraction; indexio corpus indexing + chunking + embedding; RAG query examples; projio's own dual-corpus setup (1.3k docs + 75k codelib chunks) as the canonical example |
| `40-figio-and-manuscript.md` | 500–700 | FigureSpec YAML for composed multi-panel figures; one example from gecog's `2026-05-02-mlclassifier-cohort-figs/figurespec.yaml`; **honest gap: only 1 first-party FigureSpec across all 4 study projects** — mostly aspirational; manuscript subsystem listed but **not** taught as mature (`manuscript_list` returns `[]` across cohort); forward-link `99-honest-gaps.md` |
| `50-codio.md` | 600–900 | Pain solved: agent reinvents primitives. Library catalog with `role: core/shared/external`; `codio_discover` for cross-project code search; cogpy's ~40 external mirrors as one extreme; `code/lib/*` `role: core` as another (pixecog/gecog); how this enables "search before creation" workflow per `explanation/search-before-creation.md` |



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

