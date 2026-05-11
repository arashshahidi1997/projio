---
title: "Tool-use survey across projio + four study projects"
date: 2026-05-08
timestamp: 20260508-survey-tool-use
tags: [result, handbook, workshop, survey, agentic-workshop-2026-09]
source_task: docs/log/task/task-arash-20260508-020130-100001.md
source_note: docs/log/idea/idea-arash-20260507-221835-382557.md
project_primary: projio
status: complete
---

## Purpose

Empirical input for the handbook + 4-day workshop layout/spec. This survey
catalogs how the projio toolchain is *actually* used across the five active
projects (`projio`, `cogpy`, `pixecog`, `gecog`, `msol`) so the handbook draws
chapters from real artifacts and the workshop scaffolds exercises from real
flows. Read-only across all surveyed projects.

## Per-project sections

### 1. projio (the tool itself)

**Tool inventory**

- `.claude/settings.json`: pre-approves `mcp__projio__*`, `mcp__worklog__*`,
  `mcp__sirocampus__*`; standard Bash (`git`, `python`, `pip`, `pytest`, `make`);
  Read across `/storage2/arash/**` and 14 codio mirror trees (snakemake,
  openalex-*, grobid, pyzotero, oadoi, zotero translators, etc).
- `.mcp.json`: three servers (projio MCP rooted at this repo, sirocampus MCP,
  worklog MCP) — all share `rag` conda env Python.
- Skills present (project-local under `.projio/skills/`): `figio-guide`,
  `projio-setup`. Many ecosystem skills come in via `agent_instructions()`.

**Subsystem footprint**

| Subsystem | State | Signature artifact |
|---|---|---|
| indexio | active | 2 corpora — `docs` (1.3k chunks from `docs/**/*.md`) and `codelib` (75k chunks across 14 mirrored OSS sources) |
| biblio | active (config wired, render.yml present) | `bib/`, `.projio/biblio/` |
| notio | active | `docs/log/{idea,task,result,issue,...}/` with daily/weekly index pages |
| codio | active | catalog has 1 first-party entry (`marimo` candidate) + 14 indexed mirrors used as `Read` allow-listed RAG sources |
| pipeio | **disabled** in config (`enabled: false`); `flows: {}` | n/a — projio doesn't run pipelines on itself |
| figio | minimal | one example FigureSpec under `packages/figio/docs/guide/examples/multipanel/` |

**Conventions**

- BIDS: n/a (tool, not study).
- DataLad: subdatasets mounted under `packages/` (biblio, codio, figio, indexio,
  notio, pipeio). Editable installs from there.
- Notebook backend: not used here.
- Code tier layout: src + tests + packages/ submodules. Standard wheel project.

**Teaching-grade examples**

- The **packages/ submodule layout** itself — graceful-degradation pattern
  ("system works without any subsystem present"). Workshop demo for "compose
  optional subsystems".
- The **codelib mirror + indexio source pattern** — 14 OSS repos cloned into
  `.projio/codio/mirrors/` and indexed for cross-project RAG. Concrete
  illustration of the "external knowledge layer" handbook chapter.
- The **`docs/log/` notio layout** with daily/weekly indexes — clean reference
  example of structured project memory.

**Friction**

- `pipeio.enabled: false` here is correct but worth flagging in the handbook:
  the tool's own repo does not use the pipeline subsystem — workshop
  participants need a *study* project to exercise pipeio.
- `runtime.python_bin` hardcodes a path to `Anaconda3/envs/rag/bin/python` —
  see open feedback memory `feedback_no_lab_hardcoding.md`.

### 2. cogpy (library)

**Tool inventory**

- `.claude/settings.json`: same MCP triad; broad Bash (typing/lint stack
  pre-approved: `mypy`, `ruff`, `black`, `isort`, `tox`, `nox`, `coverage`).
  Read paths cover `/storage/share/codelib/<repo>/` for ~17 lab-shared mirrors.
- `.mcp.json`: projio + sirocampus + worklog (same shape as projio).
- Skills: one project-local skill `cogpy-dev`.

**Subsystem footprint**

| Subsystem | State | Signature artifact |
|---|---|---|
| indexio | active | `.projio/indexio/index/` |
| biblio | active | `bib/{srcbib,articles,config,logs}/` — full layout |
| notio | active | `docs/log/` (commit/daily/dev/idea/issue/meeting/personal trees) |
| codio | active | catalog ~40 external mirrors (mne, neurodsp, fooof, yasa, elephant, bokeh, panel, holoviews, ghostipy, tensorpac, ofamm, generalized-phase, neuropatttoolbox, …) — pure external-discovery role |
| pipeio | **registered but flows empty** (`flows: {}`); legacy `src/cogpy/workflows/preprocess/Snakefile` is snakebids-style, predates pipeio | snakebids preprocess pipeline; multiple `qc-wave-*` task notes for travelling-wave QC |
| figio | absent (no `.projio/figio/`) | n/a |

**Conventions**

- BIDS: yes — Snakefile uses `snakebids.generate_inputs`, BIDS path templates.
- DataLad: standard sibling configuration; package is dual-published to PyPI as
  `ecogpy` and import name `cogpy`.
- Notebook backend: jupytext percent for `features.ipynb` checked-in alongside
  scripts.
- Tier layout: `src/cogpy/<area>/` flat (no `code/lib/`); pipelines live inside
  the package at `src/cogpy/workflows/preprocess/`. **Distinct from the
  later code-tier convention.**
- Site: Sphinx (not MkDocs) — only project on Sphinx in this set.

**Teaching-grade examples**

- The **`src/cogpy/workflows/preprocess/Snakefile`** rule chain (raw_zarr →
  lowpass → downsample → feature → badlabel → interpolate) — clean snakebids
  pattern with `config['prep']` knobs. Good for workshop day-1 ("a real
  Snakemake pipeline").
- The **primitive catalog README** — composability pattern (`ThresholdDetector`
  → `perievent_epochs` → `estimate_template` → `subtract_template`). Handbook
  chapter "small operators, narrative compositions".
- The **codio external-mirror catalog** — concrete demonstration that a
  project can index dozens of upstream libraries for agent-discoverable
  reuse, without forking or vendoring.

**Friction**

- Two Snakefiles in the preprocess dir (`Snakefile` and `Snakefilenew`) —
  evidence of in-flight migration, not an example to teach with as-is.
- Sphinx vs MkDocs split with the rest of the ecosystem — be explicit in the
  handbook that projio doesn't impose a docs framework.
- `qc-wave-*` task notes look like an aborted travelling-wave QC sweep —
  confirm before using as an example.

### 3. pixecog (study, ECoG + Neuropixels)

**Tool inventory**

- `.claude/settings.json`: MCP triad + WebSearch enabled; Bash pre-approves
  `pixi search *`, `ssh gamma{1..4} uptime`, `ssh gpu uptime`, marimo-pair
  discovery script, and Read access to `code/lib/{cogpy,labbox,labpy}`. By far
  the most distinctive permission set — pixi-first, multi-host, marimo-aware.
- Pixi: `pixi.toml` + `pixi.lock` present; conda is **not** used.
- Skills: one project-local skill `pixecog-flow-setup`.

**Subsystem footprint**

| Subsystem | State | Signature artifact |
|---|---|---|
| indexio | active | `.projio/indexio/index/` |
| biblio | active | `.projio/biblio/biblio.yml` |
| notio | active | `docs/log/` (commit/daily/idea/issue/meeting/rag/result/task/weekly) |
| codio | active | mirrors include `sirotalab--spikeinterface_srlab`; cogpy/labbox/labpy used as in-tree subdatasets under `code/lib/` |
| pipeio | **most active** | 15 flows registered in `.projio/pipeio/registry.yml`: `brainstate`, `calibrate_{ecephys,ieeg,ieeg_clean,ieeg_notch}`, `coupling_spindle_ripple`, `detection_qc`, `lfp_extrema`, `manifest_assemble`, `preprocess_{ecephys,ieeg,motion}`, `sharpwaveripple`, `spectrogram_burst`, `spikesorting` |
| figio | dir exists but empty in `.projio/figio/`; figures kept as dated dirs under `docs/deliverables/figures/` (~10+ "coupling_h1_*" sets) |

**Conventions**

- BIDS: yes — `raw/{sub-XX,participants.tsv,...}` strict. Two BIDS roots in
  parallel: `raw/` (ecephys + ieeg) and `derivatives/preprocess_ieeg/` (ieeg
  re-rooted post-TTL cleaning).
- Manifest pattern: every flow emits `manifest.yml`; downstream flows consume
  it via `pipeio.adapters.bids.BidsPaths` and the cross-flow `registry`
  config block. **`manifest_assemble` is its own flow** that assembles
  detection events from many siblings.
- DataLad: `derivatives/<flow>/` registered as subdatasets.
- Notebook backend: split `notebooks/{explore,demo}/` per flow with
  `notebook.yml`.
- Tier layout: full `code/{lib,pipelines,scripts,utils}/` per the code-tiers
  spec.
- Site: MkDocs.

**Teaching-grade examples**

- **`code/pipelines/lfp_extrema/Snakefile`** — non-trivial registry-extension
  pattern: the Snakefile *programmatically extends* `config['registry']` with
  one group per detection-tuple from a declarative `detections:` list, then
  fans out 7 outputs per slow-wave detection (cycle + 6 transition methods).
  Excellent workshop dissection target for "config-driven pipelines".
- **`detection_qc` flow + `2026-04-30-tac-coupling-figures.md` deliverable
  chain** — a concrete *result* (figures + report) that an agent built end-
  to-end from upstream flows. Shows the full
  raw → preprocess → detect → QC → figure → report path.
- **`manifest_assemble`** as a meta-flow — pattern for "pipeline that gathers
  outputs of N other pipelines"; a real example of cross-flow composition the
  contracts spec describes abstractly.
- The **TTL-cleaning ieeg → re-BIDS pattern** (Apr 22 reports) — workshop
  example for derivative-of-derivative as a new BIDS root.

**Friction**

- Top-level scripts (`lpf_validation_sub01_ses04.py`) and `__marimo__/` cache
  in repo root — drift from the strict tier layout. Worth honest mention.
- 15 flows is *more* than a 4-day workshop can cover. Have to choose which 2-3
  to dissect; the rest are "this is what scaling looks like" backdrop.

### 4. gecog (study, Graphene ECoG)

**Tool inventory**

- `.claude/settings.json`: MCP triad **plus** `mcp__cogpy__*` (a third per-
  project MCP server is wired). No explicit pixi/ssh permissions; uses pixi
  via `pixi.toml`.
- Skills: none in `.projio/skills/`.

**Subsystem footprint**

| Subsystem | State | Signature artifact |
|---|---|---|
| indexio | active | standard |
| biblio | active | `bib/config/biblio.yml` |
| notio | active | `docs/log/{idea,issue,meeting,result,task}/` |
| codio | active | `code/lib/{cogpy,labpy}` as subdatasets |
| pipeio | active — **8 flows** | `brainstate`, `factor_analysis`, `preprocess_{ecephys,ieeg,motion}`, `sleep_spindle`, `spectrogram`, `travelling_wave` |
| figio | one registered spec | `docs/deliverables/reports/2026-05-02-mlclassifier-cohort-figs/figurespec.yaml` (the only first-party FigureSpec in any study project) — other figures still live ad-hoc under `<report>-figs/` |

**Conventions**

- BIDS: yes (`raw/`, `derivatives/`).
- Pipeline style: same `BidsPaths` + cross-flow `manifest.yml` pattern as
  pixecog. Each mod has its own `docs/<mod>/` directory (theory.md/spec.md
  facets) — strongest example of the mod-doc convention.
- Notebook backend: `notebooks/{explore,demo}/` per flow with `notebook.yml`.
- Pixi-managed.
- Tier layout: full `code/{lib,pipelines,utils}/`.

**Teaching-grade examples**

- **`brainstate.mlclassifier` mod evolution** is the strongest narrative in
  this dataset: ~10 task notes and ~7 result notes between Apr 29 and May 6
  document a real iteration arc — apply-mode → target-rescale → auto-rescale
  → two-stage → cohort sweep → emg-from-lfp ablation. The *log trail itself*
  is a teaching artifact: shows the agent-driven research loop from question
  to result to follow-up question. Workshop day 4 / handbook chapter on
  "iterating with the agent".
- **`factor_analysis` flow** (designmat → pca → match) — clean four-rule
  flow with a *cross-session aggregation rule* (`match`) that gathers PCA
  outputs from all sessions. Good demonstration of `expand()` / aggregate
  input function in a real pipeline.
- **`docs/deliverables/reports/2026-05-02-mlclassifier-cohort.md`** — recent,
  real cohort report bundled with figures. Workshop final-day rubric anchor.

**Friction**

- No project-local skills under `.projio/skills/` — depends entirely on
  ecosystem skills. May be the cleanest "default" project.
- One figio spec out of ~7 reports in `docs/deliverables/reports/`; the
  rest are ad-hoc `<report>-figs/` directories. The May-02 cohort
  FigureSpec is the only first-party figio asset across all five projects
  and is therefore a candidate teaching example.

### 5. msol (study, behavioral object-location)

**Tool inventory**

- `.projio/config.yml` declares `code.runner` indirectly via pixi env names:
  `default: analysis`, `docs: default`, `projio: default`, `datalad: datalad`.
  **Migrating off conda per 2026-04-19** comment in config — only project
  with this transition explicitly documented.
- `.claude/settings.json` not present in the read paths (didn't open it; not
  blocking — config + registry tell us most of what we need).

**Subsystem footprint**

| Subsystem | State | Signature artifact |
|---|---|---|
| indexio | active | standard |
| biblio | **`enabled: false`** in config — but `bib/` directory does exist | likely stale config flag |
| notio | **`enabled: false`** in config — but `docs/log/{idea,issue,meeting,result,task}/` is populated and recent (May 5) | likely stale config flag |
| codio | active (no explicit catalog read; subdataset role) | `code/lib/{database_io, ratcave}` — distinct from cogpy/labpy used by ECoG projects |
| pipeio | active — **3 flows** | `dlc_pose`, `exploration_analysis`, `process_video` |
| figio | dir absent | n/a |

**Conventions**

- BIDS: yes (`raw/`, `derivatives/`, `sourcedata/`, `participants.tsv` implied
  by study scaffolding).
- Pipeline style: same Snakemake / pipeio shape as pixecog/gecog.
- Notebook backend: `notebooks/` per flow with `notebook.yml`.
- Pixi-managed; explicit pixi-env mapping (only project with named pixi
  envs — `analysis`, `default`, `datalad`).

**Teaching-grade examples**

- **`exploration_analysis` flow** (eco_decompose / compute_di) — clean
  *behavioral* pipeline contrasting with the three ECoG projects'
  electrophysiology pipelines. Workshop benefit: shows that pipeio applies
  beyond electrophysiology.
- **`dlc_pose` flow** — DLC train/analyze for both rat and objects;
  authentic "ML-in-pipeline" example for workshop day 3.
- **`docs/deliverables/reports/msol-behavior-status-2026-04-28.md`** + the
  recent task `task-arash-20260505-...` chain showing manuscript figures
  being wired in from DI summary tables — useful narrative for handbook
  chapter on "from pipeline output to manuscript figure".

**Friction**

- `biblio` and `notio` `enabled: false` in `.projio/config.yml` while the
  on-disk evidence shows both are actively used → **honest gap to surface in
  the handbook**: subsystem-enable flags can lag actual usage and projio
  doesn't auto-detect that drift.
- Pixi migration in flight; some legacy conda references may remain.
- One *behavioral* study among three electrophysiology studies — the workshop
  can lean on this for diversity, but the handbook should not over-generalize
  conventions tuned to ECoG.

## Cross-project synthesis

**Universal conventions across all four study projects (cogpy, pixecog,
gecog, msol):**

- BIDS layout (`raw/` + `derivatives/<flow>/` + `sourcedata/`).
- DataLad subdatasets for `code/lib/` and `derivatives/<flow>/`.
- `docs/log/{idea,issue,task,result,meeting}/` notio layout with `index.md`.
- Snakemake (via snakebids or pipeio's `BidsPaths`).
- MkDocs site framework — cogpy is the lone Sphinx outlier.

**Universal MCP server set:** all four project `.mcp.json`s wire `projio`
(rooted at the project), `worklog`, and `sirocampus`. gecog adds `cogpy` as
a fourth MCP server.

**Divergences worth highlighting in the workshop:**

| Axis | projio | cogpy | pixecog | gecog | msol |
|---|---|---|---|---|---|
| Project kind | tool | library | study | study | study |
| Runner | conda (rag) | conda | **pixi** | pixi | **pixi (named envs)** |
| Pipeio | disabled | empty (legacy snakebids inside src/) | 15 flows | 8 flows | 3 flows |
| Code tier layout | n/a | `src/cogpy/<area>/` flat | `code/{lib,pipelines,utils,scripts}/` | `code/{lib,pipelines,utils}/` | `code/{lib,pipelines,utils}/` |
| Domain | meta | iEEG primitives | ECoG + Npx | Graphene ECoG | Behavior + DLC |
| Docs | MkDocs | Sphinx | MkDocs | MkDocs | MkDocs |
| Project skills | figio-guide, projio-setup | cogpy-dev | pixecog-flow-setup | none | none |
| Figio specs | 1 example (packages/figio) | 0 | 0 (figs in deliverables dirs) | 1 (May-02 mlclassifier cohort) | 0 |

**Patterns that recur (these are the load-bearing handbook concepts):**

1. **Cross-flow `manifest.yml` contract.** Every electrophysiology flow emits
   one and downstream flows consume it via `BidsPaths`. This is the actual
   integration glue between pipelines, not Snakemake's input/output alone.
2. **Mod-as-thin-orchestrator + script-per-rule.** All study projects keep
   `code/pipelines/<flow>/scripts/<rule>.py` as small wrappers around `cogpy`
   primitives — never the other way around.
3. **Subdataset code/lib** with `cogpy` (sometimes `labpy`, `labbox`,
   `database_io`, `ratcave`) — projects compose by mounting libraries
   in-tree, not by `pip install` alone.
4. **Notio result + task chain as a research log.** The gecog mlclassifier
   arc and the pixecog detection_qc → coupling_h1 arc are both navigable
   stories in `docs/log/`.
5. **Deliverables dir as the publication surface.** All study projects use
   `docs/deliverables/{reports,presentations,posters,figures}/` to stage
   shareable artifacts — separate from the working `docs/log/`.

**Patterns that are inconsistent (workshop should pick one and stick to it):**

- Figio adoption: only one first-party FigureSpec across all study projects
  (`gecog/.../2026-05-02-mlclassifier-cohort-figs/figurespec.yaml`); the rest
  are ad-hoc `<report>-figs/` dirs. That one spec is the natural template
  for a workshop figio dissection.
- Notebook subdir convention: `notebooks/{explore,demo}/` exists everywhere
  but `notebook.yml` content varies. Pick one example flow as canonical.
- Project skills: present in 3/5 projects, absent in 2/5. Workshop can
  introduce skills as "optional but recommended."

## Recommended teaching artifacts (shortlist)

Ranked by leverage (impact × concreteness × low explanatory friction).

| # | Artifact | Project | Demonstrates | Suits |
|---|---|---|---|---|
| 1 | `code/pipelines/lfp_extrema/Snakefile` (registry-extension + 7-output detection block) | pixecog | Config-driven Snakemake; non-trivial pipeio flow | Workshop **Day 1 PM** (Snakemake), Handbook ch. "config-driven pipelines" |
| 2 | `brainstate.mlclassifier` mod + result/task chain (Apr 29 – May 6) | gecog | Agent-driven research iteration loop end-to-end | Workshop **Day 2 PM** ("working with the agent"), Handbook ch. "the iterative loop" |
| 3 | `factor_analysis` flow (designmat → pca → match) | gecog | Cross-session aggregation rule; literature-driven flow design (Garcia-Cortadella 2024) | Workshop **Day 3 AM** (pipeio ecosystem), Handbook ch. "from paper to pipeline" |
| 4 | `manifest_assemble` flow + the cross-flow `BidsPaths` contract | pixecog | I/O contracts as composable infrastructure | Workshop **Day 3 AM**, Handbook ch. "contracts make pipelines composable" |
| 5 | `cogpy` primitive catalog + `subtract_template` quick-start | cogpy | Small operators → narrative composition | Handbook ch. "small operators"; could anchor a Day-1 hands-on |
| 6 | `exploration_analysis` flow (msol) | msol | Pipeio applies beyond electrophysiology — behavior + DLC | Workshop diversity slot; Handbook ch. "this generalizes" |
| 7 | The `docs/log/` notio layout + agent-activity.md (any study project; pixecog or gecog) | pixecog/gecog | Structured project memory; auditable agent trail | Workshop **Day 2 AM** intro; Handbook early ch. "project as queryable knowledge" |
| 8 | The `.projio/codio/mirrors/` + indexio catalog (projio itself) | projio | External knowledge layer via RAG | Handbook ch. "the codio + indexio knowledge layer" |
| 9 | TTL-cleaning ieeg → re-BIDS derivative pattern (`bids_dir_ieeg` switch in `lfp_extrema/config.yml`) | pixecog | Derivative-of-derivative; BIDS roots in series | Handbook ch. "BIDS in practice — when one root isn't enough" |
| 10 | `docs/deliverables/reports/2026-05-02-mlclassifier-cohort.md` + bundled figures | gecog | What a "good final deliverable" looks like | Workshop **Day 4** participant template + rubric anchor |

## Honest gaps (call these out in the handbook)

1. **Figio is under-adopted.** Only one first-party FigureSpec across all
   four study projects (gecog's May-02 cohort report); the rest of figure
   production is ad-hoc into `<report>-figs/`. Workshop can dissect that one
   spec as the canonical example, but the handbook should be honest that
   figio is mostly aspirational at this point.
2. **`enabled:` flags in `.projio/config.yml` drift from on-disk reality.**
   msol declares `biblio: false` and `notio: false` while clearly using both.
   projio doesn't auto-reconcile this. Workshop should advise periodic `projio
   sync` — handbook should mention the drift exists.
3. **Two snakemake idioms coexist.** cogpy uses `snakebids.generate_inputs`
   directly; the four study projects use `pipeio.adapters.bids.BidsPaths` on
   top of snakebids. Pick the latter for the workshop and explain the former
   exists as legacy.
4. **Pixi vs conda is mid-migration.** msol explicitly migrating off conda;
   pixecog and gecog already on pixi; cogpy and projio still on conda. Not
   a teaching obstacle but worth a workshop slide.
5. **Ad-hoc top-level files in active projects.** pixecog has
   `lpf_validation_sub01_ses04.py` and `__marimo__/` at repo root — even the
   most disciplined study has friction. The handbook chapter on tier layout
   should acknowledge this honestly rather than show only sanitized examples.
6. **Project-local skills are uneven.** 3/5 projects have at least one,
   2/5 have none. Skill authoring is real but not yet a baseline practice;
   workshop should introduce it as "optional advanced" not "expected."
7. **Single-author fragility.** Per the Deep Research frame: every project in
   this set has one author (Arash). The handbook + workshop are the docs +
   examples + community legs of the survival strategy — name this in the
   handbook's first chapter as motivation, not as deflection.
8. **Manuscript subsystem is absent across all five projects.** projio
   `manuscript_list` returns `[]`. The notio.manuscript subpackage is
   designed but not yet exercised on a real paper. Workshop day 3 should
   be cautious about teaching manuscript flow as if mature.

## Method note

- Used `mcp__worklog__worklog_project_context` for each project's snapshot.
- Used `mcp__worklog__worklog_read_file` to read configs / settings without
  cd'ing into other projects.
- Used `mcp__projio__codio_list`, `pipeio_flow_list`, `figio_figure_list`,
  `manuscript_list`, `corpus_list`, `present_list`, `indexio_sources_list`
  inside projio (these tools are scoped to the calling project).
- Fell back to filesystem reads for `code/pipelines/*/`,
  `.projio/pipeio/registry.yml`, and `docs/log/*/` listings on the four
  surveyed projects (registry files yielded the flow inventory directly).
- No source projects modified.
