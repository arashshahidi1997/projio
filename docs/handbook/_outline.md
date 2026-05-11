# Handbook outline (stack-axis)

Status: spec-only. No prose. Source survey:
[`docs/log/result/result-arash-20260508-stack-axis-survey.md`](../log/result/result-arash-20260508-stack-axis-survey.md).
Source idea: [`docs/log/idea/idea-arash-20260507-221835-382557.md`](../log/idea/idea-arash-20260507-221835-382557.md).
Workshop syllabus companion:
[`docs/log/result/result-arash-20260508-stack-axis-syllabus-spec.md`](../log/result/result-arash-20260508-stack-axis-syllabus-spec.md).

The handbook teaches the **stack itself**, organized along the
stack-component axis. projio enters as a layer that *knows about* the
prior stack, not as a self-justifying primitive. Agentic workflows are
last. The two-workspace contract, cross-link protocol, and
Quarto-multi-output decisions remain valid as defined in
[`result-arash-20260508-021908-627443.md`](../log/result/result-arash-20260508-021908-627443.md)
§A, §E, §F (no longer authoritative for chapter list).

---

## A. Chapter list

```
docs/handbook/
├── index.md                                  # landing + reading paths
├── 00-frame/
│   ├── why-this-stack.md
│   ├── why-interactivity.md
│   └── single-author-fragility.md
├── 10-bids/
│   ├── strict-raw-root.md
│   ├── derivatives-and-manifest.md
│   └── bids-beyond-electrophysiology.md
├── 20-datalad/
│   ├── superdataset-and-subdatasets.md
│   ├── siblings-and-ria.md
│   └── code-as-subdataset.md
├── 30-snakemake/
│   ├── rules-and-the-dag.md
│   ├── snakebids-wildcards.md
│   ├── config-driven-pipelines.md
│   └── three-idioms.md
├── 40-marimo/
│   ├── reactive-cells.md
│   ├── analysis-notebooks.md
│   └── handbook-explorables.md
├── 50-publication/
│   ├── mkdocs-for-the-site.md
│   ├── quarto-for-deliverables.md
│   └── two-surfaces-one-cross-link-protocol.md
├── 60-projio/
│   ├── 00-stack-aware-layer.md
│   ├── 10-notio.md
│   ├── 20-pipeio.md
│   ├── 30-biblio-indexio.md
│   ├── 40-figio-and-manuscript.md
│   └── 50-codio.md
├── 70-agentic/
│   ├── claude-code-and-mcp.md
│   ├── permissions-and-bounded-context.md
│   ├── skills.md
│   └── captures-tasks-queues.md
├── 80-orchestration/
│   ├── worklog-overview.md
│   ├── goals-and-critical-path.md
│   └── cross-project-dispatch.md
├── 90-future-directions/
│   ├── agent-hierarchies.md
│   └── live-agent-communication.md
├── 99-honest-gaps.md
├── references.md                             # handbook-wide bibliography
└── _outline.md                               # this file
```

`docs/blog/` co-resides on the same mkdocs-material site (per prior spec §B);
out of scope for this outline.

---

## B. Per-chapter sub-sections

Sub-sections listed only at the level needed to anchor stack axis. One
line each.

### 00-frame
- `why-this-stack.md` — the stack as a coherent open-science substrate; what each component contributes; what's missing and why projio fills it.
- `why-interactivity.md` — 7-paradigm taxonomy (from idea note) translated to research workflow; manipulable workflow as the gap.
- `single-author-fragility.md` — Quantomatic precedent; docs+examples+community as survival strategy; honest scope.

### 10-bids
- `strict-raw-root.md` — `participants.tsv` + `dataset_description.json` + `sub-XX/`; the directory layout *is* the API.
- `derivatives-and-manifest.md` — `derivatives/<flow>/`; `manifest.yml` as a projio convention layered on BIDS.
- `bids-beyond-electrophysiology.md` — BIDS for video / behavior; what generalizes, what doesn't.

### 20-datalad
- `superdataset-and-subdatasets.md` — git + git-annex; super/sub composition; `.gitmodules` reading.
- `siblings-and-ria.md` — RIA stores, GitHub/GitLab siblings, preview-first sibling helpers.
- `code-as-subdataset.md` — `code/lib/<name>/` mounting, pinned commits; subdataset-per-derivative as a deliberate choice.

### 30-snakemake
- `rules-and-the-dag.md` — input → output declaration; staleness; parallelism.
- `snakebids-wildcards.md` — `generate_inputs()`; subject/session/run wildcards; one rule chain end-to-end.
- `config-driven-pipelines.md` — registry-extension pattern; one config drives many outputs.
- `three-idioms.md` — snakebids alone vs snakebids + `BidsPaths` vs plain snakemake; pick one default; honest gap.

### 40-marimo
- `reactive-cells.md` — file-as-`.py`; reactive DAG; no hidden state; diff-friendly.
- `analysis-notebooks.md` — `notebooks/{explore,demo}/.src/` layout; `nb_watch`; `nb_snapshot`.
- `handbook-explorables.md` — `marimo export html-wasm`; embedding in mkdocs; constraints (no backend).

### 50-publication
- `mkdocs-for-the-site.md` — material theme; nav patching; plugin density (search/monorepo/ezlinks/bibtex).
- `quarto-for-deliverables.md` — `.qmd` reports; `.projio/render/quarto.yml`; per-deliverable rendering.
- `two-surfaces-one-cross-link-protocol.md` — handbook (mkdocs) + workshop (Quarto); cross-link via published URL.

### 60-projio
- `00-stack-aware-layer.md` — *the stack already does the work; projio makes it queryable*; `project_context()`, `runtime_conventions()`; six-subsystem map; `projio sync`.
- `10-notio.md` — `docs/log/{idea,task,result,…}/`; agent-activity trail; project memory as audit trail (pain solved: "why was this run produced?").
- `20-pipeio.md` — flow registry; `BidsPaths`; `manifest.yml` as cross-flow contract; ~50 MCP tools; `pipeio_target_paths` (pain solved: hand-constructed BIDS wildcards).
- `30-biblio-indexio.md` — citekey resolution; docling/grobid; corpus indexing; RAG (pain solved: claims drift from data).
- `40-figio-and-manuscript.md` — FigureSpec YAML; honest "mostly aspirational" note; manuscript subsystem listed but not taught as mature.
- `50-codio.md` — library catalog with `role: core/shared/external`; `codio_discover` (pain solved: agent reinvents primitives).

### 70-agentic
- `claude-code-and-mcp.md` — Claude Code as the editor; MCP server set; three-server baseline (projio + sirocampus + worklog).
- `permissions-and-bounded-context.md` — `.claude/settings.json`; allow-list shape; `mcp__<server>__*` in both `permissions.allow` and `allowedTools`.
- `skills.md` — SKILL.md format; ecosystem vs project-local; when to write one (graduated adoption — only 3/5 projects have any).
- `captures-tasks-queues.md` — `worklog_note → promote_to_task → schedule_queue`; model selection (haiku/sonnet/opus); auto-dispatch.

### 80-orchestration
- `worklog-overview.md` — registry, captures, queue, goals.
- `goals-and-critical-path.md` — goal definition, milestones, critical-path computation, weekly `focus()`.
- `cross-project-dispatch.md` — `run_prompt`, `worklog_note(..., auto_dispatch=True, project_id=...)`, `schedule_queue(after=...)` for chains.

### 99-honest-gaps
- One section per gap from survey §"Honest gaps" (8 gaps), each as: *gap* → *what the handbook does about it*. No new gaps introduced here.

---

## C. Per-chapter mapping (component → workshop session → canonical artifact → explorable)

`E` = planned marimo-WASM explorable (max 5 total — see §F).
`[example: TBD]` = survey lacks a canonical artifact; identify before drafting.

| Chapter | Stack component | Workshop session | Canonical artifact (from stack-axis survey) | E |
|---|---|---|---|---|
| 00-frame/why-this-stack | meta | Day-1 AM kickoff | survey §"Universal patterns" (9 items) | — |
| 00-frame/why-interactivity | meta | Day-1 AM kickoff (10 min) | idea note §"Conceptual frame" 7-paradigm table | **E1** |
| 00-frame/single-author-fragility | meta | Day-1 AM kickoff (5 min) | survey §"Honest gaps" cross-cutting #8 | — |
| 10-bids/strict-raw-root | BIDS | Day-1 AM | `pixecog/raw/` (survey component 1, canonical artifact) | — |
| 10-bids/derivatives-and-manifest | BIDS | Day-1 AM (continues) | `pixecog/derivatives/preprocess_ieeg/manifest.yml` (survey component 1) | — |
| 10-bids/bids-beyond-electrophysiology | BIDS | Day-1 AM sidebar | `msol/raw/` (survey component 1, msol row — first BIDS-for-video) | — |
| 20-datalad/superdataset-and-subdatasets | DataLad | Day-1 AM | `gecog/.gitmodules` (survey component 2, canonical artifact) | — |
| 20-datalad/siblings-and-ria | DataLad | Day-1 AM | survey component 2 §"Convergent patterns" RIA layout | — |
| 20-datalad/code-as-subdataset | DataLad | Day-1 AM | `pixecog/.gitmodules` `code/lib/{cogpy,labbox,labpy}` rows (survey component 2, divergent patterns) | — |
| 30-snakemake/rules-and-the-dag | Snakemake | Day-1 PM | `cogpy/src/cogpy/workflows/preprocess/Snakefile` (survey component 3, cogpy row — pure snakebids) | — |
| 30-snakemake/snakebids-wildcards | Snakemake | Day-1 PM | same artifact (cogpy Snakefile) | — |
| 30-snakemake/config-driven-pipelines | Snakemake | Day-1 PM (advanced) | `pixecog/code/pipelines/lfp_extrema/Snakefile` + `config.yml` (survey component 3, canonical artifact) | **E2** |
| 30-snakemake/three-idioms | Snakemake | Day-1 PM closing | survey component 3 §"Honest gap" (three idioms table) | — |
| 40-marimo/reactive-cells | Marimo | Day-2 AM | `pixecog/code/pipelines/spectrogram_burst/notebooks/explore/.src/*.py` (survey component 4, canonical artifact) | — |
| 40-marimo/analysis-notebooks | Marimo | Day-2 AM | same artifact + survey component 4 §"Convergent patterns" (`notebooks/{explore,demo}/.src/`) | — |
| 40-marimo/handbook-explorables | Marimo | Day-2 AM (preview) | `[example: TBD]` — survey component 4 §"Honest gap" notes zero existing examples; this chapter *creates* the first explorable | — |
| 50-publication/mkdocs-for-the-site | Quarto/MkDocs | Day-2 PM (pre-projio framing) | `pixecog/mkdocs.yml` (survey component 5, canonical artifact) | — |
| 50-publication/quarto-for-deliverables | Quarto/MkDocs | Day-2 PM | `projio/.projio/render/quarto.yml` + one `docs/deliverables/reports/*.qmd` (survey component 5, canonical artifact) | — |
| 50-publication/two-surfaces-one-cross-link-protocol | Quarto/MkDocs | Day-2 PM (transition into projio) | survey component 5 §"Honest gap"; prior-spec §F | — |
| 60-projio/00-stack-aware-layer | projio | Day-2 PM (projio enters) | `pixecog/.projio/config.yml` + `pixecog/.projio/pipeio/registry.yml` (survey component 6, canonical artifact) | — |
| 60-projio/10-notio | projio | Day-2 PM | survey component 6 §"Convergent patterns" `docs/log/{idea,task,result,meeting}/` (every study project) | — |
| 60-projio/20-pipeio | projio | Day-3 AM | `pixecog/code/pipelines/lfp_extrema/` end-to-end + `manifest_assemble` (survey component 6, graded-intro stage 2) | **E3** |
| 60-projio/30-biblio-indexio | projio | Day-3 AM | survey component 6 graded-intro stage 3; projio's own corpus (1.3k+75k chunks) | — |
| 60-projio/40-figio-and-manuscript | projio | Day-3 AM | `gecog` first-party FigureSpec (survey component 6, divergent patterns); honest "1 across cohort" framing | — |
| 60-projio/50-codio | projio | Day-3 AM | `cogpy` ~40 external mirrors + `code/lib/*` `role: core` (survey component 6, graded-intro stage 5) | — |
| 70-agentic/claude-code-and-mcp | Agentic | Day-3 PM | `pixecog/.mcp.json` + `gecog/.mcp.json` (survey component 7, `.mcp.json` table — gecog's 4-server unique case) | — |
| 70-agentic/permissions-and-bounded-context | Agentic | Day-3 PM | `pixecog/.claude/settings.json` (survey component 7, canonical artifact — multi-host SSH + pixi + marimo-pair) | **E4** |
| 70-agentic/skills | Agentic | Day-3 PM | `.projio/skills/` listings across cohort (survey component 7 §"Skills"); `pixecog/.projio/skills/pixecog-flow-setup/` | — |
| 70-agentic/captures-tasks-queues | Agentic | Day-3 PM | `gecog brainstate.mlclassifier` arc OR this very session's `idea → task → result` chain (survey component 7 §"Captures → tasks pattern") | — |
| 80-orchestration/worklog-overview | Orchestration | Day-3 PM closing | `[example: TBD]` — survey doesn't inventory worklog state; placeholder until worklog dashboard artifact exported | — |
| 80-orchestration/goals-and-critical-path | Orchestration | Day-3 PM | `[example: TBD]` — same; goal-arash-20260507-221912-674817 is one example to anonymize | **E5** |
| 80-orchestration/cross-project-dispatch | Orchestration | Day-3 PM | survey component 7 §"Captures → tasks pattern" + this session's chain | — |
| 99-honest-gaps | meta | Day-1 closing + Day-3 closing | survey §"Honest gaps" (8 items, verbatim mapping) | — |

---

## D. Cross-link policy

Verbatim from prior spec §F (still valid):

- **Workshop handouts → handbook**: link via the published URL
  (`https://projio.<domain>/handbook/...`). Keeps the workshop dataset
  detachable.
- **Handbook chapters → source artifacts**: cite via repo-relative paths
  (e.g. `pixecog/code/pipelines/lfp_extrema/Snakefile`) and mention the
  *project name* explicitly. Sole-author handbook → personal lab context
  is fine.
- **Handbook chapters → existing Diátaxis trees** (`tutorials/`,
  `how-to/`, `reference/`, `explanation/`): link out, do not absorb.
  E.g. `60-projio/40-figio-and-manuscript.md` →
  `how-to/build-a-report.md`.
- **Worklog framing**: keep lab/public-facing handbook copy free of
  personal-hub framing per `feedback_worklog_personal.md`. Worklog
  enters chapter `80-orchestration/` as cross-project dispatch
  infrastructure, not as Arash's daily hub.

---

## E. Asset conventions

| Asset type | Where | How | Don't |
|---|---|---|---|
| Static figures (architecture diagrams, screenshots) | `docs/handbook/<chapter-dir>/_assets/` | hand-authored SVG/PNG; alt text required | rebuild from figio just to ship a static diagram |
| **figio** FigureSpec | `figures/<id>/spec.yml` (project root); embed via `figio_build → SVG` referenced from chapter | reserved for composed multi-panel figures that will appear in manuscripts/decks | don't use figio for one-off chapter illustrations |
| **Marimo-WASM explorables** | exported to `docs/handbook/<chapter-dir>/_explorables/<slug>/index.html` via `marimo export html-wasm` | embed via raw `<iframe>` or mkdocs plugin; max 5 total in handbook (see §F) | don't depend on a backend |
| **Code blocks** | inline | language-tagged; one canonical example per concept | don't paste whole Snakefiles when an excerpt + repo-relative link suffices |
| **Cross-references** | inline | repo-relative path + project name (e.g. `pixecog/.gitmodules`) | don't link to local working copies (`/storage2/arash/...`) |
| **Naming** | chapters numbered `NN-slug.md`; sub-chapters `NN-projio/MM-slug.md` | leading two-digit prefix preserves order in mkdocs nav | no prose in `_outline.md` or `_assets/` filenames |
| **Section-axis purity** | every chapter named after a stack component | — | no chapter named after a substantive analysis (no "ECoG preprocessing", "spike sorting") |

---

## F. Marimo-WASM explorable shortlist (max 5)

| # | Chapter | Title (working) | What it shows | Cost | Reuses survey artifact? |
|---|---|---|---|---|---|
| **E1** | 00-frame/why-interactivity | Task-graph trace | The 7-paradigm taxonomy applied to a research session: notes → tasks → dispatched runs → outputs (the chapter-1 task-graph from the idea note) | S | reuses this session's `idea → task → result` chain |
| **E2** | 30-snakemake/config-driven-pipelines | DAG explorable | `pixecog/code/pipelines/lfp_extrema/Snakefile` rendered as an interactive DAG; toggle config entries → DAG re-fans-out | S | direct |
| **E3** | 60-projio/20-pipeio | `pipeio_target_paths` interactive | Pick (flow, group, member) wildcards → resolved BIDS path; teaches the registry → manifest → path resolution | M | direct (`pixecog/.projio/pipeio/registry.yml`) |
| **E4** | 70-agentic/permissions-and-bounded-context | Permission-scope diagram | Toggle MCP servers / Bash patterns / Read globs → highlighted slice of project surface area the agent can touch | S | direct (`pixecog/.claude/settings.json`) |
| **E5** | 80-orchestration/goals-and-critical-path | Goal critical-path render | Render a goal's milestone graph + critical path; click a milestone → its captures and dispatched tasks | M | partial — synthetic goal anonymized from `goal-arash-20260507-221912-674817.md` |

Total: 5. Cost mix: 3×S + 2×M. Three explorables (E1, E2, E4) are
buildable today from existing repo state; E3 needs a small wrapper over
`pipeio_target_paths`; E5 needs a minimal critical-path renderer.

Hard rule: **5 is the cap.** Adding a 6th means dropping one.

---

## G. Handbook ↔ workshop mapping table

Granularity: handbook *chapter* (file) ↔ workshop *session* (half-day or
named slot). Workshop sessions are defined fully in
`result-arash-20260508-stack-axis-syllabus-spec.md`; this table is the
contract.

| Handbook chapter | Workshop session(s) |
|---|---|
| 00-frame/* | Day-1 AM kickoff (15–20 min total) |
| 10-bids/strict-raw-root + derivatives-and-manifest | Day-1 AM session 1 (BIDS) |
| 10-bids/bids-beyond-electrophysiology | Day-1 AM session 1 sidebar |
| 20-datalad/* | Day-1 AM session 2 (DataLad) |
| 30-snakemake/rules-and-the-dag + snakebids-wildcards | Day-1 PM session 1 (Snakemake basics) |
| 30-snakemake/config-driven-pipelines | Day-1 PM session 2 (advanced rule chain) |
| 30-snakemake/three-idioms | Day-1 PM closing |
| 40-marimo/reactive-cells + analysis-notebooks | Day-2 AM session 1 (Marimo authoring) |
| 40-marimo/handbook-explorables | Day-2 AM session 1 (preview, not hands-on) |
| 50-publication/mkdocs-for-the-site + quarto-for-deliverables | Day-2 PM session 1 (publication frameworks) |
| 50-publication/two-surfaces-one-cross-link-protocol | Day-2 PM session 2 transition |
| 60-projio/00-stack-aware-layer | Day-2 PM session 2 (projio enters) |
| 60-projio/10-notio | Day-2 PM session 2 |
| 60-projio/20-pipeio | Day-3 AM session 1 |
| 60-projio/30-biblio-indexio | Day-3 AM session 2 |
| 60-projio/40-figio-and-manuscript | Day-3 AM session 2 |
| 60-projio/50-codio | Day-3 AM session 2 |
| 70-agentic/claude-code-and-mcp + permissions-and-bounded-context | Day-3 PM session 1 (agent setup) |
| 70-agentic/skills | Day-3 PM session 1 sidebar |
| 70-agentic/captures-tasks-queues | Day-3 PM session 2 (iteration loop) |
| 80-orchestration/* | Day-3 PM closing |
| 99-honest-gaps | Day-1 closing (BIDS/DataLad/Snakemake gaps) + Day-3 closing (projio + agentic gaps) |
| (Day 4) | Participant presentations — handbook chapters serve as reference, not primary source |

Inverse mapping (workshop → handbook) is maintained in the syllabus
spec; this table is the projio-side contract.

---

## H. What this outline deliberately omits

- Per-chapter prose, learning objectives in chapter form, code examples.
  Chapter 1 prose is a separate task
  (`task-arash-20260507-222028-504938.md`).
- Per-exercise marimo cell breakdowns (workshop-side; depends on dataset
  in `shared/datasets/`).
- Workshop announcement, dates, capacity, rubric specifics — see
  syllabus spec and idea note §"Open questions deferred".
- Manuscript subsystem deep dive (mention only; subsystem returns `[]`
  across cohort per survey component 6).
