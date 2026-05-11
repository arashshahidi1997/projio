---
title: "Stack-axis roadmap (handbook + workshop, May → Sept 2026)"
date: 2026-05-08
timestamp: 20260508-stack-axis-roadmap
tags: [result, handbook, workshop, roadmap, planning, stack-axis, agentic-workshop-2026-09]
source_task: docs/log/task/task-arash-20260508-160002-200003.md
source_idea: docs/log/idea/idea-arash-20260507-221835-382557.md
source_goal: docs/log/goal/goal-arash-20260507-221912-674817.md
source_survey: docs/log/result/result-arash-20260508-stack-axis-survey.md
source_outline: docs/handbook/_outline.md
source_spec: docs/log/result/result-arash-20260508-stack-axis-syllabus-spec.md
supersedes: docs/log/result/result-arash-20260508-handbook-workshop-roadmap.md
project_primary: projio
goal: agentic-workshop-2026-09
status: draft
---

## Purpose

Sequence and budget the handbook + workshop initiative working backwards
from the September 2026 workshop, **on the stack-component axis**. The
stack-axis survey
([`result-arash-20260508-stack-axis-survey.md`](result-arash-20260508-stack-axis-survey.md))
inventoried what's on disk; the syllabus spec
([`result-arash-20260508-stack-axis-syllabus-spec.md`](result-arash-20260508-stack-axis-syllabus-spec.md))
shaped the workshop sessions; the handbook outline
([`docs/handbook/_outline.md`](../../handbook/_outline.md)) fixed the
chapter list. This roadmap tells Arash **what to do, in what order, by
when, and what to cut first**.

Reuses methodology (calendar shape, risk categories, cut-list ranking
technique) from the prior substantive-axis roadmap
([`result-arash-20260508-handbook-workshop-roadmap.md`](result-arash-20260508-handbook-workshop-roadmap.md));
**does not** reuse its chapter list — that was substantive, this is
stack-axis. Planning only: no prose, no provisioning, no dispatch calls.

---

## 1. Backwards-planned milestone calendar (May → Sept 2026)

Anchor milestones from the goal note: workspace provisioned (May),
announcement (June), syllabus (July), days 1–3 materials + manim
(August), dry run + delivery + post-mortem (September). Competing pulls
named in the idea note `project_research_priorities.md`: **TAC III in May**
and **manuscript writing through June** dominate. May/June workshop
columns are deliberately light; heavy authoring lands in July–August.

Handbook track is now organized by stack component. A "chapter" below
means a top-level chapter directory (`10-bids/`, `20-datalad/`, ...);
sub-chapters within a chapter draft together as one work unit, with
**60-projio** as the exception (split per subsystem — see §3).

| Month | Workshop track | Handbook track (stack-axis) | Cross-cutting |
|---|---|---|---|
| **May (residual)** | Provision `teaching/agentic-workshop/2026-09/` (task A); move announcement into the new workspace; register in worklog. | Handbook tree stub created from outline (empty files with H1 + survey-artifact pointer per chapter); `mkdocs.yml` nav patched for `Handbook` + `Blog`. **Chapter 1 = `00-frame/why-this-stack.md` prose** (task C, residual half — outline portion is already discharged by `_outline.md`). | Move Deep Research PDF into projio (task B); **TAC III is the dominant claim — keep cross-cutting work small.** |
| **June** | Finalize announcement (room/dates/capacity/prereqs/credits); open registration. | Marimo-WASM prototype embedded in `00-frame/why-interactivity.md` as **E1** (task D). Chapter `10-bids/` drafted (3 sub-chapters: strict-raw, derivatives+manifest, beyond-electrophysiology). Chapter `20-datalad/` drafted (3 sub-chapters). | Manuscript writing remains the dominant pull; protect a 4-h weekly handbook slot via worklog `focus()`. |
| **July** | `2026-09/syllabus.qmd` authored from the stack-axis spec; pre-workshop setup checklist test-run on a fresh machine. | Chapter `30-snakemake/` drafted (4 sub-chapters; **E2** built into config-driven-pipelines). Chapter `40-marimo/` drafted (3 sub-chapters; explorables sub-chapter previews E3–E5 plumbing). Chapter `50-publication/` drafted (3 sub-chapters). Chapter `60-projio/00-stack-aware-layer.md` + `10-notio.md` drafted. | Manim opening animation: storyboard locked, render started (long pole; cut-threshold mid-July if not storyboarded). |
| **August** | Day 1–3 lecture.qmd + handout.qmd + exercises/ (marimo `.py`) per spec §B; revealjs theme finalized; teaching dataset (thinned `pixecog` slice) frozen in `shared/datasets/`. Day-4 rubric finalized. | Chapter `60-projio/20-pipeio.md` + `30-biblio-indexio.md` drafted (heaviest week — pipeio is the densest sub-chapter; **E3** built here). Chapter `60-projio/40-figio-and-manuscript.md` + `50-codio.md` drafted (lighter — figio is honest-aspirational). Chapter `70-agentic/` drafted (4 sub-chapters; **E4** built here). Chapter `80-orchestration/` drafted (3 sub-chapters; **E5** built here). | Cross-link audit: every workshop handout links into the correct handbook URL per outline §G; manim animation rendered final cut. |
| **early September** | Dry run with one volunteer through full day 1 (6 h); friction notes captured; iterate exercises. | `99-honest-gaps.md` written from survey §"Honest gaps" (8 items, verbatim mapping). | Pre-workshop email with setup checklist + Claude credit instructions sent to participants. |
| **mid September** | Workshop delivered (days 1–4). Day-4 participant presentations. | (frozen — no handbook edits during delivery week to avoid breaking links) | Live `notio` capture during workshop for post-mortem feedstock. |
| **late September** | `post-mortem.qmd` written same week; rubric outcomes captured; deltas for 2027 iteration logged in `shared/`. | Re-open handbook; back-port any clarifications discovered during teaching. | Goal `agentic-workshop-2026-09` closed; success criteria scored honestly (≥ 6 register, ≥ 5 present, ≥ 1 adopts). |

Counts: **9 chapter drafts** to land between June 1 and August 31
(handbook tree has 10 chapter dirs incl. `99-`; `00-frame` is the
chapter-1 task plus residual two-page draft folded into June). The
stack-axis chapter list is **denser than the prior 7-chapter
substantive-axis plan** — see §5 budget update.

---

## 2. Dispatch order for the four pending tasks

The user's stated order is "provision first." Same disagreement as the
prior roadmap holds: **task B (PDF move) first**, because it unblocks
chapter-1 prose and the marimo-WASM prototype, which together are the
fail-fast signal for the explorable strategy. The stack-axis spec
**does not** change this calculus; if anything it sharpens it, because
chapter-1 (`00-frame/why-this-stack.md`) is now the only frame chapter
authored in May while the rest of the `00-frame/` sub-chapters
(`why-interactivity.md`, `single-author-fragility.md`) defer to June.

One change vs. prior roadmap: **task C ("Handbook outline + chapter 1
draft") has had its outline deliverable already discharged** by
`_outline.md` (produced by the stack-axis chapter-1-spec task on
2026-05-08). The remaining work in task C is the chapter-1 *prose
draft* only.

Numbered order with rationale:

1. **`task-arash-20260507-222003-098400.md` — Move Deep Research PDF.**
   Cheapest action (single `cp -L`); unblocks chapter-1 prose (which
   cites the 7-paradigm taxonomy from the PDF — see outline §B,
   `00-frame/why-interactivity.md`); unblocks the E1 prototype host
   page. No upstream dependencies.

2. **`task-arash-20260507-221947-582556.md` — Provision workshop
   workspace.** Must precede *any* workshop authoring (announcement
   finalization, syllabus, day-N materials). Reveals the `projio init`
   ergonomics that day-3 PM session 2 then teaches. May provisioning is
   on-time per goal-note milestone 1; deferring compounds delay because
   June/July milestones (announcement/syllabus) sit on top of it.

3. **`task-arash-20260507-222028-504938.md` — Chapter 1 prose draft.**
   Outline portion is already done. Remaining: prose for
   `00-frame/why-this-stack.md` (the conceptual frame the rest of the
   handbook borrows vocabulary from). Should follow task B and can run
   in parallel with task A's later steps.

4. **`task-arash-20260507-222051-589638.md` — marimo-WASM prototype.**
   Now hosts as E1 in `00-frame/why-interactivity.md` per outline §F.
   Depends on chapter 1's existence to validate the embedding pattern
   on a real handbook page. **Go/no-go signal** for E2–E5 across the
   rest of the handbook. Defer until June so the prototype iterates
   without competing with TAC III.

**Disagreement explicit, trade-off stated:** the user's "provision
first" order would push the PDF move and chapter-1 prose behind the
workspace scaffold. The trade-off is small — task B is hours, not days.
Doing B before A means chapter-1 prose can begin the same evening and
the handbook nav patch lands in the same week. If the user prefers
literal stated order (A → B → C → D), the cost is roughly one week of
chapter-1 latency, no other consequence.

---

## 3. Proposed new tasks (descriptions only — do not file)

Each entry: title, priority, blocked-by, target month, one-paragraph
description, source ref, goal ref. Arash files the actual notes
himself.

### Workshop workspace + announcement track

> **Workshop announcement finalization** (priority: high; blocked-by:
> task A; target: 2026-06) — Finalize the announcement draft already
> moved into `2026-09/announcement.md`. Fill in: department + room +
> exact dates, capacity (idea note suggests 8–12), hardware/Claude
> credits policy, prereq strictness. Send to department mailing list
> once registration form is wired. Source: idea note §"Workshop
> announcement draft". Goal: `agentic-workshop-2026-09`.

> **Workshop syllabus drafting** (priority: high; blocked-by:
> announcement-finalization; target: 2026-07) — Author Quarto
> `2026-09/syllabus.qmd` directly from the stack-axis syllabus spec
> §A–E (day shape, per-session breakdown, pre-workshop checklist,
> day-4 rubric, backup plans). This is rendering, not re-design — the
> spec is authoritative. Source:
> `result-arash-20260508-stack-axis-syllabus-spec.md`. Goal:
> `agentic-workshop-2026-09`.

### Handbook chapter drafts (one task per stack component)

Each chapter draft task carries: H1 + frame (one paragraph) + per
sub-chapter prose anchored in the outline §B description and the
canonical artifact named in outline §C + cross-links to source
artifacts (repo-relative paths) + `99-honest-gaps.md` references for
the chapter's gaps from survey §"Honest gaps". Drafts are
markdown-only; explorables (E1–E5) are a separate task track.

> **Chapter `00-frame/` residual draft** (priority: medium;
> blocked-by: chapter-1 prose; target: 2026-06) — Draft
> `why-interactivity.md` (with **E1** embedded — see explorables
> track) and `single-author-fragility.md`. `why-this-stack.md` is
> already in flight as task C. Source: outline §B `00-frame`. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `10-bids/` draft** (priority: high; blocked-by: chapter-1
> prose; target: 2026-06) — 3 sub-chapters: `strict-raw-root.md`,
> `derivatives-and-manifest.md`, `bids-beyond-electrophysiology.md`.
> Anchor on `pixecog/raw/` + `pixecog/derivatives/preprocess_ieeg/manifest.yml`
> + msol video slice (outline §C rows 4–6). Workshop day-1 AM session
> 1 home. Source: outline §B `10-bids`; survey component 1. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `20-datalad/` draft** (priority: high; blocked-by: chapter-1
> prose; target: 2026-06) — 3 sub-chapters: `superdataset-and-subdatasets.md`,
> `siblings-and-ria.md`, `code-as-subdataset.md`. Anchor on
> `gecog/.gitmodules` (canonical) + `pixecog/.gitmodules` (`code/lib/*`
> rows). Workshop day-1 AM session 2 home. Source: outline §B
> `20-datalad`; survey component 2. Goal: `agentic-workshop-2026-09`.

> **Chapter `30-snakemake/` draft** (priority: high; blocked-by:
> chapter-1 prose; target: 2026-07) — 4 sub-chapters:
> `rules-and-the-dag.md`, `snakebids-wildcards.md`, `config-driven-pipelines.md`
> (hosts **E2** — DAG explorable), `three-idioms.md`. Anchor on cogpy
> `preprocess/Snakefile` (basics) + `pixecog/lfp_extrema/` (config-driven).
> Workshop day-1 PM home. Source: outline §B `30-snakemake`; survey
> component 3. Goal: `agentic-workshop-2026-09`.

> **Chapter `40-marimo/` draft** (priority: medium; blocked-by:
> chapter-1 prose + E1 validated; target: 2026-07) — 3 sub-chapters:
> `reactive-cells.md`, `analysis-notebooks.md`, `handbook-explorables.md`.
> Anchor on `pixecog/spectrogram_burst/notebooks/`. The
> handbook-explorables sub-chapter creates the first explorable as
> part of its writing (survey honest gap #4). Workshop day-2 AM home.
> Source: outline §B `40-marimo`; survey component 4. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `50-publication/` draft** (priority: medium; blocked-by:
> chapter-1 prose; target: 2026-07) — 3 sub-chapters:
> `mkdocs-for-the-site.md`, `quarto-for-deliverables.md`,
> `two-surfaces-one-cross-link-protocol.md`. Anchor on `pixecog/mkdocs.yml`
> + `projio/.projio/render/quarto.yml`. Workshop day-2 PM session 1
> home. Source: outline §B `50-publication`; survey component 5. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `60-projio/00-stack-aware-layer.md` + `10-notio.md` draft**
> (priority: high; blocked-by: chapters 10–50 stubs; target: 2026-07)
> — 2 sub-chapters: the projio framing chapter and notio. Anchor on
> `pixecog/.projio/config.yml` + `pixecog/.projio/pipeio/registry.yml`
> + `docs/log/{idea,task,result}/` cross-cohort. Workshop day-2 PM
> session 2 home. Source: outline §B `60-projio` rows 1–2; survey
> component 6 graded-introduction stages 0–1. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `60-projio/20-pipeio.md` draft** (priority: high;
> blocked-by: pipeio sub-chapter prereqs; target: 2026-08) — Densest
> projio sub-chapter. Anchor on `pixecog/code/pipelines/lfp_extrema/`
> end-to-end + `manifest_assemble` cross-flow contract. Hosts **E3**
> (`pipeio_target_paths` interactive). Workshop day-3 AM session 1
> home. Source: outline §B `60-projio` row 3; survey component 6
> graded-introduction stage 2. Goal: `agentic-workshop-2026-09`.

> **Chapter `60-projio/30-biblio-indexio.md` draft** (priority: medium;
> blocked-by: pipeio chapter; target: 2026-08) — One sub-chapter
> covering both biblio and indexio (they share the literature-corpus
> story). Anchor on projio's own corpus (1.3k+75k chunks) +
> docling/grobid pipeline. Workshop day-3 AM session 2 home. Source:
> outline §B `60-projio` row 4; survey component 6 graded-introduction
> stage 3. Goal: `agentic-workshop-2026-09`.

> **Chapter `60-projio/40-figio-and-manuscript.md` draft** (priority:
> low; blocked-by: pipeio chapter; target: 2026-08) — Honest
> "1-FigureSpec-across-cohort" framing. Anchor on gecog's first-party
> FigureSpec. Manuscript subsystem mention only (returns `[]` across
> cohort). Workshop day-3 AM session 2 sidebar. Source: outline §B
> `60-projio` row 5; survey component 6 divergent patterns. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `60-projio/50-codio.md` draft** (priority: medium;
> blocked-by: pipeio chapter; target: 2026-08) — Library catalog +
> `role: core/shared/external` + `codio_discover`. Anchor on cogpy's
> ~40 external mirrors and `code/lib/` `role: core` registrations.
> Workshop day-3 AM session 2 home. Source: outline §B `60-projio`
> row 6; survey component 6 graded-introduction stage 5. Goal:
> `agentic-workshop-2026-09`.

> **Chapter `70-agentic/` draft** (priority: high; blocked-by: 60-projio
> sub-chapters; target: 2026-08) — 4 sub-chapters:
> `claude-code-and-mcp.md`, `permissions-and-bounded-context.md`
> (hosts **E4** — permission-scope diagram), `skills.md`,
> `captures-tasks-queues.md`. Anchor on `pixecog/.claude/settings.json`
> + `pixecog/.mcp.json` + the gecog mlclassifier or this-very-session
> idea→task→result chain. **Day-3-PM-critical** — cannot be cut below
> stub + key beats. Source: outline §B `70-agentic`; survey component
> 7. Goal: `agentic-workshop-2026-09`.

> **Chapter `80-orchestration/` draft** (priority: medium; blocked-by:
> agentic chapter; target: 2026-08) — 3 sub-chapters:
> `worklog-overview.md`, `goals-and-critical-path.md` (hosts **E5** —
> goal critical-path), `cross-project-dispatch.md`. Honest framing per
> `feedback_worklog_personal.md`: present worklog as cross-project
> dispatch *infrastructure*, not as Arash's personal hub. Workshop
> day-3 PM closing home. Outline §C flags `[example: TBD]` for the
> first two sub-chapters — the chapter draft must resolve these
> placeholders or accept anonymized synthetic examples. Source:
> outline §B `80-orchestration`; survey component 7 §"Captures →
> tasks pattern". Goal: `agentic-workshop-2026-09`.

> **Chapter `99-honest-gaps.md` draft** (priority: medium; blocked-by:
> all stack chapters drafted; target: 2026-09 early) — One section per
> gap from survey §"Honest gaps" (8 gaps), each as: *gap* → *what the
> handbook does about it*. No new gaps introduced. Workshop day-1 + day-3
> closing read-through. Source: outline §B `99-honest-gaps`; survey
> §"Honest gaps". Goal: `agentic-workshop-2026-09`.

### Marimo-WASM explorables (E2–E5; E1 is the existing prototype task D)

Cap is 5 (outline §F). E1 is task D. The remaining four, listed in
the outline §F shortlist:

> **Marimo-WASM E2 — Snakemake DAG explorable** (priority: medium;
> blocked-by: chapter `30-snakemake/config-driven-pipelines.md` draft +
> E1 validated; target: 2026-07) — Render `lfp_extrema/Snakefile` as
> an interactive DAG; toggle config entries → DAG re-fans-out. Cost: S.
> Source: outline §F row E2. Goal: `agentic-workshop-2026-09`.

> **Marimo-WASM E3 — `pipeio_target_paths` explorable** (priority:
> medium; blocked-by: chapter `60-projio/20-pipeio.md` draft;
> target: 2026-08) — Pick (flow, group, member) wildcards → resolved
> BIDS path; teaches registry → manifest → path resolution. Cost: M
> (needs a small wrapper over the MCP tool's pure logic). Source:
> outline §F row E3. Goal: `agentic-workshop-2026-09`.

> **Marimo-WASM E4 — Permission-scope diagram** (priority: medium;
> blocked-by: chapter `70-agentic/permissions-and-bounded-context.md`
> draft; target: 2026-08) — Toggle MCP servers / Bash patterns / Read
> globs → highlighted slice of project surface area the agent can
> touch. Cost: S. Source: outline §F row E4. Goal:
> `agentic-workshop-2026-09`.

> **Marimo-WASM E5 — Goal critical-path render** (priority: low;
> blocked-by: chapter `80-orchestration/goals-and-critical-path.md`
> draft; target: 2026-08) — Render a goal's milestone graph + critical
> path; click a milestone → its captures and dispatched tasks. Cost: M
> (needs minimal critical-path renderer). Synthetic-anonymized goal,
> not Arash's actual goal. Source: outline §F row E5. Goal:
> `agentic-workshop-2026-09`.

### Cross-cutting workshop tasks

> **Manim opening animation** (priority: medium; blocked-by: none —
> long-pole render; target: storyboard 2026-07-15, render 2026-08) —
> 3–5 min animation showing data → pipeline → dispatch → result through
> projio architecture vs. a manual workflow. Lives under
> `teaching/agentic-workshop/shared/manim/`. Reusable across iterations
> and as blog/social asset. Source: idea note §"Tooling decisions" →
> "Manim". Goal: `agentic-workshop-2026-09`.

> **Pre-workshop setup checklist + dry-run** (priority: high;
> blocked-by: syllabus draft; target: 2026-08) — Author
> `2026-09/pre-workshop-setup.qmd` per syllabus spec §C; run end-to-end
> on a fresh VM or volunteer machine to flush hidden assumptions.
> Source: syllabus spec §C; goal-note milestone 3. Goal:
> `agentic-workshop-2026-09`.

> **Workshop dry run with one volunteer** (priority: high; blocked-by:
> day 1–3 materials drafted; target: early 2026-09) — Walk one
> volunteer through full day-1 (6 h) and capture friction notes via
> `notio`. Acceptance: post-dry-run friction log in
> `2026-09/dry-run-notes.qmd`; identified blockers fixed before
> workshop start. Source: goal-note milestone 5. Goal:
> `agentic-workshop-2026-09`.

> **Workshop post-mortem** (priority: medium; blocked-by: workshop
> delivery; target: late 2026-09) — Write `2026-09/post-mortem.qmd`
> the week after delivery. Score success criteria from the goal note
> (≥ 6 register, ≥ 5 present, ≥ 1 adopts). Capture deltas for 2027
> iteration in `shared/`. Source: goal-note milestone 7. Goal:
> `agentic-workshop-2026-09`.

### Open-question decision tasks

> **Open-question decision tasks** (priority: low; blocked-by: see §7;
> target: 2026-07 latest for #3, 2026-09-30 for #1, 2026-12-31 for #2)
> — Three small task notes corresponding to the deferred questions in
> §7 below: public-OSS decision (#1), blog co-residence decision (#2),
> public title (#3). Each is a half-day decision with the §7 evidence
> test. Source: idea note §"Open questions deferred". Goal:
> `agentic-workshop-2026-09`.

### Count check

Per spec acceptance: ≥ 10 proposed new tasks, one per chapter draft
minimum. Tally:

- 1 announcement + 1 syllabus = **2**
- 1 frame-residual + 1 bids + 1 datalad + 1 snakemake + 1 marimo + 1
  publication + 1 projio-intro+notio + 1 pipeio + 1 biblio-indexio +
  1 figio-manuscript + 1 codio + 1 agentic + 1 orchestration + 1
  honest-gaps = **14 chapter drafts**
- 4 explorables (E2–E5) = **4**
- 1 manim + 1 pre-workshop + 1 dry-run + 1 post-mortem + 1
  open-questions-bundle = **5**

**Total: 25 proposed tasks.** Comfortably above the ≥ 10 floor; the
projio chapter is split into 5 drafts because it carries 6
sub-chapters and pipeio alone is the densest single page in the
handbook.

---

## 4. Cadence + publishing rhythm (≤ 150 words)

**Recommendation: Willison-style note→blog promotion, with a *fixed*
weekly 4-h handbook slot until July, doubling to two slots
(Tue + Fri) in July–August. Reaffirmed against the larger chapter
count.**

- **May–June (TAC III + manuscript):** one 4-h slot/week. Target: one
  chapter stub + one short blog post promoted from the week's `notio`
  captures. Stack-axis chapter list is denser than substantive-axis
  was, but 10-bids and 20-datalad are short, well-anchored chapters —
  feasible at one slot/week.
- **July:** add a second slot/week. Target: two chapters drafted/month.
- **August:** chapters drop weekly. Workshop materials dominate but
  reuse chapter prose verbatim where possible (handbook ↔ workshop
  contract enables this).
- **September:** **freeze** during delivery week. Resume Willison-style
  posting with workshop reflections post-event.

Defended against: solo author, TAC pressure, workshop deadline. Larger
chapter count absorbed by July escalation, not by faster May/June.

---

## 5. Resource budget

Updated to reflect **stack-axis chapter density** (14 chapter drafts vs.
prior 7) and **graded projio introduction** (60-projio is 6
sub-chapters, of which 20-pipeio is the densest single page in the
handbook).

| Resource | Budget | Cut threshold |
|---|---|---|
| **Chapter drafting time** | 14 chapter drafts × ~6 h/draft median = **~84 h** between June and August. Pipeio sub-chapter alone: 12 h (densest). 99-honest-gaps: 4 h (verbatim mapping). Frame residual: 4 h total for two short sub-chapters. | If June slot count is < 4 (i.e., < 16 h logged), drop chapter `40-marimo/handbook-explorables.md` to a stub + cross-link to the prototype HTML. Drop `60-projio/40-figio-and-manuscript.md` to a one-paragraph "honest aspirational" pointer. |
| Manim opening animation | 25 h total (10 h storyboard, 15 h render+iterate) over July–August | If not storyboarded by **2026-07-15**, drop to a static figure-storyboard slide deck. Animation is high-leverage but not workshop-critical. |
| Marimo-WASM explorables | E1 prototype (chapter 1) in June; E2–E5 across July–August. Build cost: S = 4 h, M = 8 h. Total: E1 (S, 4 h) + E2 (S, 4 h) + E3 (M, 8 h) + E4 (S, 4 h) + E5 (M, 8 h) = **28 h**. | If E1 fails to embed in mkdocs by **2026-06-30**, freeze at zero explorables and use static figures + "open notebook" links. **Stack-axis update:** because workshop teaches Marimo natively in component 4 day-2 AM, WASM failure no longer cascades into "we lose Marimo coverage" — it only loses the in-handbook embeddings. |
| Workshop teaching dataset | Thinned `pixecog` slice: 2 subjects, 1 task, ~1 GB total, BIDS-valid `raw/` + one `derivatives/<flow>/manifest.yml`. Frozen in `shared/datasets/` by **2026-08-15**. | If not frozen by 2026-08-15, fall back to a small public OpenNeuro slice — loses lab-specific motivation but keeps the workshop runnable. |
| Slide design | One shared revealjs theme under `shared/slide-templates/` applied across all 3 lecture days. **8 h total**. | If theme work overruns, default to revealjs default theme. Aesthetic, not didactic. |
| Figio figures specifically authored for the handbook | **Zero new figio specs.** Reuse the gecog May-02 cohort spec (survey component 6, divergent patterns) as the sole demonstration; honest about "1 across cohort." | This is already a hard cut. Do not budget more. |
| Observable interactive blog essay | One essay by 2026-07-31 ("How a worklog goal becomes a dispatched task"). 12 h budget. | If not started by 2026-07-15, defer to post-workshop blog. Not workshop-critical. **First in the cut list (§8).** |

**Total cross-cutting investment ceiling: ~157 h** between now (May 8)
and Sept 1 (~17 weeks). At 4-h/week May–June + 8-h/week July–August
that's ~92 h available. **Gap of ~65 h is real**, and §8 cut-list is
the planning device that closes it: cuts in tiers 1–4 free 60–80 h
collectively without breaking workshop dependencies. The honest read:
this roadmap is feasible only if Tier-1+ cuts begin to land by July.

---

## 6. Risk register

Same six categories as prior roadmap. Mitigation specifics updated for
stack-axis structure where they shift.

| # | Risk | Likelihood | Impact | Mitigation | Trigger |
|---|---|---|---|---|---|
| 1 | TAC III overruns May | M | M | Cut May handbook track to chapter-1 outline (already done) + chapter-1 prose only; defer all 10-bids/20-datalad work to June. Protect workshop track (provision + announcement) at all costs. | TAC III deliverable not submitted by **2026-05-31**. |
| 2 | Manuscript writing overruns June | H | H | Reduce June workshop-track to announcement only. Freeze chapters 10-bids and 20-datalad at "stub + outline + survey-artifact pointer" (the May tree-stub state). Reschedule full drafts to July alongside 30-snakemake. The stack-axis structure makes this re-shuffle clean: 10-bids and 20-datalad are short, foundation-level chapters that can absorb one month of slip without losing teaching value. | Manuscript not submitted by **2026-06-30**; weekly handbook slot missed twice in a row. |
| 3 | marimo-WASM doesn't embed cleanly in mkdocs | M | M | **Stack-axis update:** workshop teaches Marimo natively in component 4 (day-2 AM session 1) regardless of WASM-export viability — that is now the bedrock the workshop relies on. WASM failure means: drop E1–E5; replace with static figures + "open notebook" iframe-less links. No cascading impact on workshop. Document fallback in chapter `40-marimo/handbook-explorables.md` and use that page as a discussion of *why* the explorable strategy is harder than it looks. | E1 prototype build fails or produces > 5 MB HTML or breaks mkdocs nav by **2026-06-30**. |
| 4 | Low workshop registrations (< 6) | M | H | Two weeks before, open registration to neighboring labs / collaborators; if still < 6, hold the workshop with the registered participants and publish materials as a self-paced course. **Don't cancel** — materials are sunk cost regardless. | < 4 registrations by **2026-08-15**. |
| 5 | Lab/sirocampus infrastructure interruption (gamma/storage downtime, EZProxy outage) | L | M | Ensure all workshop materials are buildable from a participant's laptop without lab infra (no `worklog_*` calls in handbook prose per `feedback_worklog_personal.md`; no sirocampus-specific paths in exercise scaffolds). Pre-workshop checklist tests this. **Stack-axis update:** the syllabus spec backup-plan §E ("no internet") already pre-caches scaffolds + datasets + docling/grobid outputs in `shared/scaffolds/` and `shared/datasets/`. | Any > 24 h infra interruption inside September. |
| 6 | Single-creator burnout | M | H | Hard cut to §8 list at first sign (missed slot 2 weeks running, or qualitative self-report). Goal note already cites this as the project's existential risk (Quantomatic warning). The workshop-with-fewer-chapters is a viable path; the workshop-with-burnt-out-author is not. **Stack-axis-specific note:** the larger chapter count amplifies this risk; the cut list (§8) ranks projio-subsystem chapters and explorables as the first depth cuts precisely so foundation chapters (10-bids/20-datalad/30-snakemake) stay protected. | Two consecutive missed weekly handbook slots, or self-reported drag on `notio` ≥ 1 week. |

Six entries. Per spec acceptance.

---

## 7. Open-question resolution plan

Same three questions as prior roadmap. Title deadline unchanged
(announcement send-out is still June). Stack-axis structure does not
shift the evidence/deadline schema.

| # | Question | Evidence needed | Latest decision date | Default if undecided |
|---|---|---|---|---|
| 1 | Will projio become a public open-source tool with external adopters? | Workshop registrations + post-workshop survey of ≥ 1 participant adopting projio (success criterion in goal note) | **2026-09-30** (workshop end). No decision needed before then; the architecture (handbook in `projio/docs/`) doesn't lock the answer. | Default: keep projio personal-stack-shaped. Revisit only if ≥ 2 external adopters appear within 6 months post-workshop. |
| 2 | Is the blog a section of the handbook site or its own surface? | Count and shape of first ~10 essays. If they're heavily projio-internal → stay co-resident. If they generalize beyond projio → consider extraction. | **2026-12-31** (after first 10 essays). | Default: stay co-resident on the projio mkdocs site (per idea note "Same site for now"). |
| 3 | Final public title (`coherence`, personal handle, …) | Working title *The Agentic Research Workflow* tested on the announcement audience. Reception of the announcement is the data. | **2026-06-15** (announcement send-out date). The title appears in the announcement — must be picked by then. | Default: ship with *The Agentic Research Workflow* as the workshop title; defer the "handbook brand" title to post-workshop. |

---

## 8. What gets cut first (ranked, hardest-to-easiest cut)

Re-ranked for the stack-axis structure. The hint from the spec is
correct: **chapters mapped to foundation components (BIDS, DataLad,
Snakemake, Marimo) cannot be cut without breaking the workshop's
day-1/day-2 dependencies**; **projio-subsystem sub-chapters are
individually cuttable**; **the agentic chapter (70-agentic) is
day-3-PM-critical**. Read top-down: first item is what gets cut at
first sign of slippage. Workshop delivery date is sacred; everything
below is content that can shrink to protect delivery.

1. **Observable blog essay.** Cut first. Pure outreach, not
   workshop-critical, not a goal-note success criterion. Frees ~12 h.
2. **Marimo-WASM explorables E2 + E5.** Keep E1 (chapter 1
   validation), E3 (pipeio — workshop day-3 anchor), and E4 (agentic
   permissions — also day-3 anchor). E2 and E5 are nice-to-have. Frees
   ~12 h.
3. **Chapter `60-projio/40-figio-and-manuscript.md`.** The honest
   "1-FigureSpec-across-cohort" framing means there's not much to
   teach yet. Reduce to a one-paragraph "see how-to/build-a-report"
   pointer. Workshop day-3 AM session 2 absorbs this content into a
   90-second mention. Frees ~6 h.
4. **Chapter `60-projio/50-codio.md` depth.** Reduce to stub +
   `codio_discover` example + cross-link to existing reference docs.
   Workshop day-3 AM still teaches codio via the live MCP call, not
   the chapter. Frees ~5 h.
5. **Marimo-WASM explorables E3 + E4 (further cut).** Last-resort
   explorable cut: keep only E1. Replace E3/E4 with static screenshots
   + "open notebook" links. **Workshop is unaffected** — this is
   handbook-only. Frees ~12 h additional. (Total explorable budget cut
   to E1 only saves ~24 h vs. all five.)
6. **Manim opening animation.** Cut threshold mid-July (storyboard) or
   early-August (full render). Replace with a hand-drawn slide-deck
   storyboard. Frees up to 25 h. Workshop loses visual punch but keeps
   content.
7. **Workshop day-4 rubric depth.** Default to one-page rubric
   (criterion, level, score) per syllabus spec §D skeleton. Frees ~6 h.
8. **One workshop teaching dataset slice (drop day-3's bespoke slice).**
   Reuse day-2's dataset for day-3 exercises with a different question.
   Frees ~8 h.
9. **Chapters `40-marimo/handbook-explorables.md` content depth.**
   Reduce to stub explaining the export pipeline and pointing to E1's
   HTML. Workshop day-2 AM does not depend on this sub-chapter. Frees
   ~4 h.
10. **Chapter `99-honest-gaps.md` written from verbal during teaching.**
    Last-resort cut: skip pre-workshop draft, gather verbal during
    teaching, back-port post-workshop. Frees ~4 h. **The 8 gaps are
    already enumerated in the survey; this is purely a rendering
    deferral.**

**What is NOT in this cut list, and why:**

- **Chapters `10-bids/`, `20-datalad/`, `30-snakemake/`.** Workshop
  day-1 depends on these end-to-end. Cutting them means cutting day 1.
  Not negotiable.
- **Chapters `40-marimo/reactive-cells.md` + `40-marimo/analysis-notebooks.md`.**
  Day-2 AM anchors. Not negotiable.
- **Chapter `50-publication/`.** Day-2 PM anchor and prerequisite for
  day-3 PM (participants need a working `.qmd` + mkdocs site to host
  later artifacts). Not negotiable.
- **Chapter `60-projio/00-stack-aware-layer.md` + `10-notio.md` +
  `20-pipeio.md`.** projio's identity-as-stack-aware-layer chapter,
  notio, and pipeio together are workshop day-2 PM + day-3 AM
  critical-path. Not negotiable.
- **Chapter `60-projio/30-biblio-indexio.md`.** Workshop day-3 AM
  session 2 anchor. Cuttable to stub but **not** to zero — the day-3
  AM session needs a handbook page to point at. Reduce, do not
  eliminate.
- **Chapter `70-agentic/` (all 4 sub-chapters).** Workshop day-3 PM
  critical. Cuttable to "stub + key beats" if pressure is severe; do
  **not** eliminate any sub-chapter.
- **Chapter `80-orchestration/`.** Workshop day-3 PM closing. Cuttable
  to one combined sub-chapter (merge the three) if extreme pressure;
  do not eliminate.
- **Workshop dry run with volunteer.** Absolute last cut. Removing
  this is a quality-of-delivery risk; the goal note's success
  criterion (≥ 5 present on day 4) likely requires day-1 to be smooth.

The cut list is genuinely ranked: items 1–4 are pure cuts (free
~35 h) without touching anything that hits a workshop dependency.
Items 5–10 dent depth or visual polish but preserve all workshop
teaching paths.

---

## Method note

- Read source task `task-arash-20260508-160002-200003.md`, the
  stack-axis survey, the stack-axis syllabus spec, the handbook
  outline `_outline.md`, the source idea note, the source goal note,
  the four pending-task notes, and the prior substantive-axis
  roadmap.
- Reused calendar shape (§1 monthly table), risk-register methodology
  (§6 categories), cut-list ranking technique (§8 top-down) from the
  prior roadmap; substituted stack-axis chapter list throughout.
- Verified: chapter list in §1 matches `_outline.md` §A; explorable
  shortlist in §3 + §5 matches `_outline.md` §F; canonical artifacts
  cited match survey §"Canonical teaching artifact" rows.
- No new files created outside `docs/log/result/`. No tasks filed
  (per hard rule). No code or chapter prose written. No workspace
  provisioned.
