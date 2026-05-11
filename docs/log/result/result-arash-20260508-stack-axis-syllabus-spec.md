---
title: "Stack-axis workshop syllabus spec (handbook + workshop, Sept 2026)"
date: 2026-05-08
timestamp: 20260508-stack-axis-syllabus-spec
tags: [result, workshop, spec, stack-axis, agentic-workshop-2026-09]
source_task: docs/log/task/task-arash-20260508-160001-200002.md
source_note: docs/log/idea/idea-arash-20260507-221835-382557.md
source_survey: docs/log/result/result-arash-20260508-stack-axis-survey.md
source_goal: docs/log/goal/goal-arash-20260507-221912-674817.md
companion: docs/handbook/_outline.md
supersedes: docs/log/result/result-arash-20260508-021908-627443.md
project_primary: projio
goal: agentic-workshop-2026-09
status: draft
---

## Purpose

Workshop syllabus structure for the 4-day department course, organized
along the **stack-component axis** (BIDS → DataLad → Snakemake → Marimo
→ Quarto/MkDocs → projio → agentic → orchestration). Companion to the
handbook outline at [`docs/handbook/_outline.md`](../../handbook/_outline.md).
Spec only — no exercise content, no slide prose, no rubric specifics
beyond skeleton.

The handbook ↔ workshop contract (see handbook outline §G) is
load-bearing: every workshop session points into one or more handbook
chapters; every handbook chapter has a workshop home.

Two-workspace contract, cross-link protocol, and Quarto-multi-output
decisions remain valid as defined in
[`result-arash-20260508-021908-627443.md`](result-arash-20260508-021908-627443.md)
§A, §E, §F.

---

## A. Day shape

| Day | Theme | Stack components introduced | projio? | Agent? |
|---|---|---|---|---|
| 1 | Stack foundations (raw → versioned → orchestrated) | BIDS, DataLad, Snakemake | no | no |
| 2 | Authoring + interactivity → projio enters | Marimo, Quarto/MkDocs, **projio (intro)** | partial (PM) | no |
| 3 | projio + agentic + orchestration | projio subsystems, Claude Code/MCP, worklog | yes | yes |
| 4 | Participant presentations + group discussion | (cross-cutting) | reference | reference |

Each working day: 6 hours = 3 h AM + 3 h PM, with one ~15 min coffee
break per half-day. Day 4: 3 h presentations (~20 min × 6–8
participants) + 1.5 h group discussion + 1.5 h next-step planning.

---

## B. Per-session breakdown

Each session row: **learning outcome** (single sentence), **prereq**,
**hands-on artifact** the participant produces, **dataset**, **handbook
chapter(s)** paired.

Datasets: `shared/datasets/` (workshop workspace) symlinks to teaching-safe
slices. The default teaching dataset is **a thinned `pixecog`-derived
slice**: 2 subjects, 1 task, ~1 GB total, BIDS-valid `raw/` + a single
existing `derivatives/<flow>/manifest.yml` example. msol-derived video
slice is the alternate for the "BIDS beyond electrophysiology" sidebar.

### Day 1 — Stack foundations

#### Day-1 AM kickoff (20 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can name the seven stack components and articulate why this stack (vs. ad-hoc folders + Jupyter + ad-hoc paths). |
| Prereq | none |
| Artifact | none (overview) |
| Dataset | none |
| Handbook | `00-frame/why-this-stack.md`, `00-frame/why-interactivity.md`, `00-frame/single-author-fragility.md` |

#### Day-1 AM session 1 — BIDS (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can take a flat directory of raw recordings and produce a BIDS-valid `raw/` with `participants.tsv`, `dataset_description.json`, and `sub-XX/ses-YY/...`. |
| Prereq | basic shell, basic git |
| Artifact | a teaching-dataset-derived `raw/` directory that passes the BIDS validator |
| Dataset | thinned `pixecog` slice (raw recordings only, pre-BIDS) |
| Handbook | `10-bids/strict-raw-root.md`, `10-bids/derivatives-and-manifest.md` (preview), `10-bids/bids-beyond-electrophysiology.md` (sidebar with msol video slice) |

#### Day-1 AM session 2 — DataLad (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can `datalad create` a superdataset, install one external library as a subdataset, and push to a RIA sibling. |
| Prereq | session 1 (`raw/` exists) |
| Artifact | superdataset wrapping the BIDS `raw/` with `code/lib/<external-lib>` as a subdataset; RIA sibling registered (preview-mode walk through; actual push only if RIA available locally during the workshop) |
| Dataset | continues from session 1 |
| Handbook | `20-datalad/superdataset-and-subdatasets.md`, `20-datalad/siblings-and-ria.md`, `20-datalad/code-as-subdataset.md` |

#### Day-1 PM session 1 — Snakemake basics (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can write a Snakefile with a 3-rule chain that goes `raw → preprocessed → summary` driven by snakebids wildcards. |
| Prereq | sessions 1–2; basic Python |
| Artifact | `code/pipelines/preprocess/{Snakefile, config.yml, scripts/}` running end-to-end on the teaching dataset; outputs land under `derivatives/preprocess/` |
| Dataset | continues |
| Handbook | `30-snakemake/rules-and-the-dag.md`, `30-snakemake/snakebids-wildcards.md` |

#### Day-1 PM session 2 — Snakemake advanced (~70 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can extend a config to fan-out outputs (registry-extension pattern) and read it back in a downstream rule. |
| Prereq | PM session 1 |
| Artifact | the same flow extended with a config-driven output fan-out (e.g., 3 different filter cutoffs → 3 derivative groups) |
| Dataset | continues |
| Handbook | `30-snakemake/config-driven-pipelines.md` |

#### Day-1 PM closing (~15 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can name the three Snakemake idioms (snakebids alone vs +`BidsPaths` vs plain) and recognize honest gaps in derivatives BIDS-validity. |
| Prereq | day 1 |
| Artifact | none (recap) |
| Dataset | none |
| Handbook | `30-snakemake/three-idioms.md`, `99-honest-gaps.md` (BIDS + DataLad + Snakemake subset) |

### Day 2 — Authoring + interactivity → projio enters

#### Day-2 AM session 1 — Marimo (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can author a marimo notebook that loads a `derivatives/preprocess/...` output, plot it, and live-edit reactively. |
| Prereq | day 1 |
| Artifact | one `notebooks/explore/.src/<slug>.py` marimo notebook bound to a derivative produced on day 1 |
| Dataset | day-1 outputs |
| Handbook | `40-marimo/reactive-cells.md`, `40-marimo/analysis-notebooks.md`, `40-marimo/handbook-explorables.md` (preview only) |

#### Day-2 AM session 2 — Snakemake ↔ notebook glue (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can register the marimo notebook as part of the flow's `notebooks/` and snapshot it (still without projio's notebook tools — done by hand). |
| Prereq | AM session 1 |
| Artifact | flow with both rules and a hand-organized `notebooks/explore/` |
| Dataset | continues |
| Handbook | `40-marimo/analysis-notebooks.md` (continued) |

#### Day-2 PM session 1 — Quarto + MkDocs (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can write one `.qmd` report that renders to HTML with a citation, and stand up a minimal mkdocs-material site for the project. |
| Prereq | day 1 + AM |
| Artifact | one `docs/deliverables/reports/<slug>.qmd` + minimal `mkdocs.yml` rendering to a local site; the report cites one paper from a sample `.bib`. |
| Dataset | continues |
| Handbook | `50-publication/mkdocs-for-the-site.md`, `50-publication/quarto-for-deliverables.md` |

#### Day-2 PM session 2 — projio enters (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can run `projio init` + `projio sync` on the day-1/2 project and read the result via `project_context()` and `runtime_conventions()`; can make a first `idea`/`task`/`result` notio entry. |
| Prereq | day 1 + day 2 AM + PM session 1 |
| Artifact | the same project with `.projio/` populated; `docs/log/{idea,task,result}/` initialized; one note created. |
| Dataset | continues |
| Handbook | `50-publication/two-surfaces-one-cross-link-protocol.md`, `60-projio/00-stack-aware-layer.md`, `60-projio/10-notio.md` |

#### Day-2 PM closing (~15 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants understand the *pain → projio* mapping: each subsystem earns its complexity by solving a stage-N pain. |
| Prereq | PM session 2 |
| Artifact | none |
| Dataset | none |
| Handbook | survey component 6 graded-introduction table, recapped |

### Day 3 — projio + agentic + orchestration

#### Day-3 AM session 1 — pipeio (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can convert their day-1 flow into a pipeio-managed flow (`pipeio_flow_new` or in-place adoption), read paths via `pipeio_target_paths`, and emit/consume a `manifest.yml`. |
| Prereq | day 2 |
| Artifact | the day-1 flow registered in `.projio/pipeio/registry.yml`; a `manifest.yml` written by one rule and consumed by a second flow's `BidsPaths(...manifest.yml)` |
| Dataset | continues |
| Handbook | `60-projio/20-pipeio.md` |

#### Day-3 AM session 2 — biblio + indexio + figio + codio (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can ingest one DOI through biblio (citekey resolved, PDF fetched OA, docling extraction), query the project corpus via `rag_query`, and recognize figio + codio as the publication and code-reuse layers. |
| Prereq | AM session 1 |
| Artifact | one paper ingested into project `bib/`, one `rag_query` returning a chunk; a `codio_discover` query returning a registered library; one figio FigureSpec scaffold (not built — buildable as homework). |
| Dataset | a sample DOI list provided in `shared/datasets/sample-bib/` |
| Handbook | `60-projio/30-biblio-indexio.md`, `60-projio/40-figio-and-manuscript.md`, `60-projio/50-codio.md` |

#### Day-3 PM session 1 — Claude Code + MCP + permissions (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can wire `.mcp.json` (projio + worklog baseline) and `.claude/settings.json` (`mcp__projio__*` in both `permissions.allow` and `allowedTools`) and run one MCP tool through Claude Code on their project. |
| Prereq | AM |
| Artifact | working `.claude/settings.json` + `.mcp.json`; one Claude Code session showing successful MCP tool call (e.g., `note_list`, `pipeio_flow_status`) |
| Dataset | continues |
| Handbook | `70-agentic/claude-code-and-mcp.md`, `70-agentic/permissions-and-bounded-context.md`, `70-agentic/skills.md` (sidebar) |

#### Day-3 PM session 2 — captures → tasks → queues + cross-project dispatch (~80 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants can capture an idea, promote it to a task, dispatch it via worklog (auto_dispatch), tail the running agent, and read the produced result note. |
| Prereq | PM session 1 |
| Artifact | one `docs/log/idea/...` → `docs/log/task/...` → `docs/log/result/...` chain with status transitions visible in worklog `list_queue`. (Mirrors the iteration loop pattern from survey component 7 §"Captures → tasks pattern".) |
| Dataset | continues |
| Handbook | `70-agentic/captures-tasks-queues.md`, `80-orchestration/worklog-overview.md`, `80-orchestration/cross-project-dispatch.md` |

#### Day-3 PM closing (~15 min)

| Aspect | Spec |
|---|---|
| Outcome | Participants understand goal/critical-path framing and know what to prepare for day 4. |
| Prereq | day 3 |
| Artifact | one stub goal + 2–3 milestones in their workspace (preparation for day 4) |
| Dataset | participant's own data (day 4 prep) |
| Handbook | `80-orchestration/goals-and-critical-path.md`, `99-honest-gaps.md` (full read-through) |

### Day 4 — Participant presentations

| Aspect | Spec |
|---|---|
| Outcome | Each participant presents (~20 min) one task in their own research workflow that is now agent-assisted, showing the artifact and the captures→tasks→result chain that produced it. |
| Prereq | days 1–3 + ~1 evening of work on participant data |
| Artifact | per-participant: one slide deck (revealjs from a `.qmd` based on the workshop template), one BIDS-valid project, one Snakemake flow, one captures→tasks→result chain, one assistant-produced output. |
| Dataset | participant's own data (BYO) |
| Handbook | reference only — chapters serve as look-up during prep, not primary source |

Day 4 also includes: 1.5 h **group discussion** (what worked, what was
friction, what's still missing) and 1.5 h **next-step planning** (which
participants are interested in continued projio adoption; collect
contact info for follow-up channel).

---

## C. Pre-workshop setup checklist (skeleton)

Items participants must complete before day 1. Maintained in
`teaching/agentic-workshop/2026-09/pre-workshop-setup.qmd` (workshop
workspace, not provisioned yet — task
`task-arash-20260507-221947-582556.md`).

- [ ] **Account / access** — institutional account with Claude API or
      department-issued Claude credits (policy TBD per idea note §"Open
      questions").
- [ ] **OS** — Linux or macOS (Windows via WSL2 acceptable; advise
      against bare Windows).
- [ ] **Shell + git** — bash/zsh; git ≥ 2.40; basic familiarity assumed.
- [ ] **Python** — Python 3.11+ via pixi or conda; pixi recommended.
- [ ] **git-annex** — installed (DataLad needs it).
- [ ] **DataLad** — `pip install datalad` or via conda (`labpy` env
      pattern).
- [ ] **Snakemake** — `pip install snakemake snakebids` or via pixi env.
- [ ] **Marimo** — `pip install marimo` or pixi.
- [ ] **Quarto** — `quarto >= 1.4` from quarto.org installer.
- [ ] **MkDocs** — `pip install mkdocs-material`.
- [ ] **Claude Code CLI** — installed and authenticated to participant
      account.
- [ ] **Sample dataset clone** — `datalad clone` of the teaching dataset
      from the workshop RIA (URL TBD pre-announcement).
- [ ] **BYO data prep** — one own-data slice, ≤ 5 GB, documented; bring
      to day 4.
- [ ] **Self-test script** — `pre-workshop-setup.qmd` ends with a
      one-command verification: prints versions of all expected tools
      and reports red/green per tool.

---

## D. Day-4 rubric skeleton

Maintained in `teaching/agentic-workshop/2026-09/day-4-presentations/rubric.qmd`.
Skeleton categories — concrete criteria are an open decision (idea note
§"Not yet decided").

| Category | Coarse criterion (refine before workshop) |
|---|---|
| **Stack adoption** | Does the project use BIDS-valid `raw/`, DataLad superdataset, at least one Snakemake flow? |
| **Agent integration** | Is `.claude/settings.json` + `.mcp.json` correctly configured? Does the project show at least one captures → tasks → result chain? |
| **One assist** | Is there at least one task in the participant's workflow that is now agent-assisted, with before/after evidence? |
| **Reproducibility** | Can a peer reviewer reproduce one figure/result from a clean clone in < 30 min? |
| **Honest scope** | Does the participant articulate what's *not* yet adopted and why (vs. claiming completeness)? |
| **Communication** | Is the 20-minute presentation clear; does the deck render from `.qmd`; does it cite at least one source paper? |

Scoring: pass / pass-with-feedback / re-do (no failure mode — workshop
is formative, not gating). Group discussion replaces letter grades.

---

## E. Backup-plan skeleton

Per scenario: trigger, fallback, fallback-of-fallback. Maintained in
`teaching/agentic-workshop/2026-09/backup-plans.qmd`.

### No internet / patchy internet

- **Primary**: pre-cached pixi/conda envs in `shared/scaffolds/`;
  pre-cached teaching dataset and sample bibliography PDFs in
  `shared/datasets/`; pre-cached docling/grobid outputs.
- **Fallback**: switch to local-only mode — projio + Snakemake +
  DataLad work fully offline; biblio offline-ingestable from the
  pre-cached sample bibliography.
- **Fallback²**: skip Claude Code interactive sections (day 3 PM);
  walk through pre-recorded screen captures of the iteration loop
  instead.

### Agent rate-limited / Claude API outage

- **Primary**: retry with exponential backoff; switch participants to
  haiku model (cheaper / different rate limit) for day 3 PM exercises.
- **Fallback**: replace live agent dispatch with pre-recorded
  task-execution traces from `docs/log/result/` examples; teach the
  workflow shape rather than live execution.
- **Fallback²**: shift agent content to day 4 morning + use day 3 PM
  for additional projio + worklog walkthroughs.

### Weird BYO data

- **Primary**: pre-workshop self-test script flags incompatibilities
  (filesize, permissions, format).
- **Fallback**: participant uses the teaching dataset for all hands-on,
  brings BYO conversion sketch to day 4 instead of a working pipeline.
- **Fallback²**: assistant + instructor pair-debug during a posted
  office hour at day-3 lunch; participant presents day-4 with a
  clearly-labeled "BYO conversion blocked here" slide rather than a
  working artifact.

### Install failures

- **Primary**: `shared/scaffolds/` includes a Docker image with the
  full stack pre-installed; use as last-resort dev container.
- **Fallback**: pair-up — failing participant works on a paired
  participant's machine for the day; revisit installation at lunch /
  evening.
- **Fallback²**: instructor's laptop + screen-share for the affected
  participant for that session.

### Instructor unavailable / illness mid-workshop

- **Primary**: this section deferred (idea note doesn't address
  contingency staffing). Open: do we recruit a co-presenter as backup?

---

## F. What this spec deliberately omits

- **Per-session slide content / handout prose** — workshop-side, in
  `teaching/agentic-workshop/2026-09/day-N-*/`.
- **Concrete dataset choice** — the "thinned `pixecog` slice" decision
  is pending dataset-prep task; size and exact subjects TBD when slice
  is built (`shared/datasets/`).
- **Manim opening animation storyboard** — separate task per idea note.
- **Day-4 rubric concrete criteria, capacity, room, dates, prereq
  strictness** — open decisions deferred per idea note §"Open questions
  deferred"; resolve before announcement (target 2026-06).
- **Workshop budget, Claude credits policy** — institutional decision;
  out of scope.

---

## G. Method note

- Read the source idea, goal, and stack-axis survey end-to-end.
- Reused two-workspace contract, cross-link protocol, and tooling
  decisions (Quarto-multi-output, MkDocs for handbook, Marimo for both,
  Manim for one asset, Observable for blog only) verbatim from prior
  spec [`result-arash-20260508-021908-627443.md`](result-arash-20260508-021908-627443.md)
  §A, §E, §F.
- Did **not** reuse the prior chapter list — that was substantive-axis;
  this syllabus is stack-axis.
- Every "example" claim in this syllabus and in the companion handbook
  outline traces to a specific artifact in
  [`result-arash-20260508-stack-axis-survey.md`](result-arash-20260508-stack-axis-survey.md);
  TBDs are explicitly flagged.
- No source projects modified. No workshop workspace provisioned (that
  remains task `task-arash-20260507-221947-582556.md`).
