---
title: "Stack-axis survey: BIDS / DataLad / Snakemake / Marimo / Quarto+MkDocs / projio / agentic across study projects"
date: 2026-05-08
timestamp: 20260508-stack-axis-survey
tags: [result, handbook, workshop, survey, stack-axis, agentic-workshop-2026-09]
source_task: docs/log/task/task-arash-20260508-160000-200001.md
source_note: docs/log/idea/idea-arash-20260507-221835-382557.md
supersedes: docs/log/result/result-arash-20260508-tool-use-survey.md
project_primary: projio
status: complete
---

## Purpose

Empirical input for the **handbook + 4-day workshop** on the open-science stack
(BIDS, DataLad, Snakemake, Marimo, Quarto/MkDocs) plus the projio + agentic
layer that wraps them. This survey slices **horizontally across the stack**:
for each component, "how does it show up in projio's project-aware system,
and how does its adoption vary across projio + the four study projects
(`cogpy`, `pixecog`, `gecog`, `msol`)?"

Read-only across all projects. Companion / superseded by the per-project
[tool-use survey](result-arash-20260508-tool-use-survey.md) — that one is
organized per-project on the analysis-substance axis; this one is organized
per-component on the stack axis.

Workshop-audience framing throughout: each component opens with a one-paragraph
operational definition that could appear verbatim in pre-workshop reading.

---

## Component 1 — BIDS

### What it does

BIDS (Brain Imaging Data Structure) is a filesystem convention for organizing
neuroscience datasets so that any tool, person, or script knows where to find
subjects, sessions, runs, modalities, and metadata without per-dataset
configuration. Workshop framing: *the directory layout is the API.* A
BIDS-valid `raw/` lets you point any analysis at `sub-01/ses-pre/...` without
inventing a project-specific path scheme each time.

### How projio is aware of it

- **`pipeio.adapters.bids.BidsPaths`** — pipeio's BIDS adapter (in
  `packages/pipeio/src/pipeio/adapters/bids.py`). Wraps a flow's input/output
  registries against a BIDS root and snakebids `generate_inputs()` output.
- **`raw/registry.yml` + per-flow `manifest.yml`** convention layered on top
  of BIDS to carry cross-flow contract information BIDS itself doesn't
  express (e.g. which channel labels are good after a calibration step).
- **`pipeio_target_paths(flow, group, member)`** — MCP tool that resolves
  output paths from BIDS wildcards without the agent having to construct
  paths by hand.

### Adoption across projects

| Project | Adopted? | How / signature artifact | Variation worth teaching |
|---|---|---|---|
| projio | n/a | tool repo, no dataset | — (workshop note: stack tools don't themselves consume BIDS) |
| cogpy | n/a | library repo, no dataset | snakebids appears in source code (`src/cogpy/workflows/preprocess/Snakefile`) without a real BIDS dataset |
| pixecog | yes (strict) | `raw/{participants.tsv, dataset_description.json, sub-01..05, sub-test, tasks.json, registry.yml}` + 18 derivative roots; `raw/sourcedata/` separate | 18 derivative roots + 3 manifest-emitting flows = densest BIDS in the cohort |
| gecog | yes (strict) | `raw/{participants.tsv, dataset_description.json, sub-01..12, sourcedata/, registry.yml, config.yml}` + 7 derivative roots | derivative root with no `dataset_description.json` but with `manifest.yml` — soft-form derivative re-rooting |
| msol | yes | `raw/{participants.tsv, participants.json, dataset_description.json, sub-01..06, cameras.{json,tsv}, task-*.json}` + 4 derivative roots | first BIDS adoption *outside electrophysiology* — behavior + DLC; demonstrates BIDS-for-video |

### Convergent patterns

- All three study projects use `raw/` as the strict BIDS root with
  `participants.tsv` + `dataset_description.json` + `sub-XX/`.
- All three keep `sourcedata/` outside the BIDS-validated tree (pixecog and
  msol use it as a symlink to a separate dataset directory).
- All three put per-flow output under `derivatives/<flow>/` rather than
  in-place rewrites of `raw/`.

### Divergent patterns

- **Derivative-root strictness**: pixecog and gecog keep `derivatives/<flow>/`
  *partial* BIDS — `manifest.yml` carries channel/event metadata but no
  `dataset_description.json` is emitted, so derivatives aren't independently
  BIDS-valid. msol doesn't use the manifest pattern at all (its derivatives
  are plain output dirs).
- **TTL-cleaning re-rooting**: pixecog re-roots `derivatives/preprocess_ieeg/`
  as if it were a new BIDS root for downstream flows (the
  `bids_dir_ieeg` config switch in `lfp_extrema/config.yml`). Neither gecog
  nor msol does this — pixecog is the one example of "derivative-of-derivative
  treated as a fresh BIDS root."
- **Subject scale**: msol 6 subjects, pixecog 5 subjects, gecog 12 subjects —
  meaningful for choosing a workshop dataset (gecog largest, msol smallest).

### Canonical teaching artifact

**`pixecog/raw/`** + the `derivatives/preprocess_ieeg/manifest.yml` chain.
Single concrete pair: a strict BIDS root + a non-trivial derivative root
that has its own `manifest.yml` consumed by downstream flows. Lets the
workshop teach (a) BIDS strictness in `raw/` and (b) the soft-form
derivative-rooting pattern as a deliberate departure from full BIDS in
the same artifact.

### Honest gap

Derivatives in pixecog/gecog are not BIDS-valid (no
`dataset_description.json` per derivative root). The workshop should be
explicit that the `manifest.yml` pattern is a *projio convention layered
on BIDS*, not BIDS itself, and that there is an unresolved question
about whether derivative roots should also emit `dataset_description.json`
to be tool-portable beyond projio.

---

## Component 2 — DataLad

### What it does

DataLad versions data and code together by combining git (for small text and
metadata) with git-annex (for large files), and by structuring repositories
as **superdatasets** with **subdatasets** mounted at chosen paths. Workshop
framing: *git for everything, including the multi-gigabyte files and the
upstream library you depend on.* Subdatasets let you pin a known commit of
`code/lib/cogpy` inside a study, and **siblings** let you push the same
dataset to GitHub *and* a RIA store *and* a GitLab pages target with one
command.

### How projio is aware of it

- **`mcp__projio__datalad_*` tools**: `datalad_save`, `datalad_status`,
  `datalad_push`, `datalad_pull`, `datalad_siblings`. Wrap CLI invocations
  in the `labpy` conda env per the runtime convention.
- **Sibling helpers** in `src/projio/helpers/` for GitHub, GitLab, and RIA
  sibling provisioning. All preview-first (require `--yes` to execute).
- **`projio sync`** auto-discovers `code/lib/<name>/` subdatasets and
  registers them in codio with `role=core`.
- **`pipeio_flow_new`** scaffolds a flow whose `derivatives/<flow>/` is
  expected to be registered as its own subdataset (the convention is
  enforced socially, not yet automatically).

### Adoption across projects

| Project | Adopted? | How / signature artifact | Variation worth teaching |
|---|---|---|---|
| projio | yes (composition) | 6 ecosystem subdatasets under `packages/{biblio,notio,indexio,codio,pipeio,figio}` + 13 read-only mirrors under `.projio/codio/mirrors/` | only project where subdatasets are the *product*, not just inputs |
| cogpy | minimal | no `.gitmodules`; `.datalad/config` only carries dataset id `493104a7-...` | a library, used as a subdataset by others — shows the upstream side of the relationship |
| pixecog | maximal | `.gitmodules` lists ~25 entries: `raw`, 14 `derivatives/*`, `bib`, `code/ECoGandNpix`, 3 `code/lib/*`, 2 `.projio/codio/mirrors/sirotalab--*` | densest subdataset graph in the cohort; RIA URLs split across `/storage/share/` (ecosystem libs) and `/storage2/ria-store/` (study-specific) |
| gecog | medium | 9 entries: `raw`, 5 `derivatives/*`, `code/lib/{cogpy,labpy}` (no labbox) | clean RIA layout (`/storage2/ria-store/alias/gecog-*` for everything) |
| msol | minimal | **only one entry**: `code/lib/ratcave` (an external GitHub remote, not a RIA alias); no `raw`/`derivatives` registered as subdatasets | the outlier — DataLad initialized but most of the directory tree is not currently treated as subdatasets |

### Convergent patterns

- Every project has a `.datalad/config` with a dataset id (DataLad-initialized).
- Every study project's `code/lib/` mounts subdatasets for the cogpy +
  labpy + (sometimes) labbox + (msol-only) ratcave/database_io libraries.
- RIA store is the canonical sibling pattern when a sibling is registered
  (`/storage2/ria-store/alias/<project>-<component>` or
  `/storage/share/git/ria-store/alias/<lib>`).

### Divergent patterns

- **Subdataset coverage**: pixecog and gecog register every flow's
  `derivatives/<flow>/` as a subdataset; msol does not. Workshop has to
  pick one and call out the other as "this is the convention, msol is
  midway through adopting it."
- **Aliased entries** in pixecog's `.gitmodules` (`derivatives/spectrogram`
  and `derivatives/spectrogram_burst` both pointing at `pixecog-spectrogram`;
  `manifest` and `manifest_assemble` both at `pixecog-manifest`) — evidence
  of in-flight rename, worth flagging but not worth teaching.
- **External GitHub subdataset** is unique to msol (`code/lib/ratcave` →
  github.com/ratcave/ratcave.git) — the rest use RIA aliases throughout.

### Canonical teaching artifact

**`gecog/.gitmodules`** — 9 entries, every URL `/storage2/ria-store/alias/gecog-*`,
clean separation of `raw/`, per-flow `derivatives/*`, and `code/lib/*`. The
cleanest demonstration of "DataLad as a coherent subdataset graph" without
the rename-aliasing noise pixecog carries.

### Honest gap

Sibling provisioning is preview-first in projio's helpers (good), but the
*subdataset-per-derivative* convention is enforced socially. msol shows
the consequence: a study can be DataLad-initialized but not actually use
DataLad for the bulk of its content. The workshop and handbook should
teach the convention as a deliberate choice the user has to make at
flow-creation time, not as an automatic projio behavior.

---

## Component 3 — Snakemake

### What it does

Snakemake is a Python-based pipeline framework that turns a graph of input
→ output dependencies into a DAG of jobs that can be parallelized,
re-run on staleness, and described declaratively in a `Snakefile`.
Workshop framing: *write down what each step needs and what it produces;
Snakemake figures out the rest.* The `snakebids` extension parameterizes
rules over BIDS subject/session/run wildcards.

### How projio is aware of it

- **`packages/pipeio/`** — projio's pipeline subsystem. `pipeio.adapters.bids.BidsPaths`
  layers projio's per-flow registry/manifest convention on top of snakebids.
- **`.projio/pipeio/registry.yml`** — generated by `pipeio_registry_scan`,
  enumerates flows and their `app_type` (currently always `snakemake`).
- **MCP tools**: `pipeio_flow_list`, `pipeio_flow_status`, `pipeio_flow_new`,
  `pipeio_run`, `pipeio_dag_export`, `pipeio_flow_report`, `pipeio_mod_*`,
  `pipeio_rule_*`. ~50 tools total addressing flows by name (no path).
- **Runner auto-detection** (`pixi.toml` present → `pixi run snakemake`,
  else `conda run -n <env> snakemake`).

### Adoption across projects

| Project | Adopted? | How / signature artifact | Variation worth teaching |
|---|---|---|---|
| projio | disabled | `subsystems.pipeio.enabled: false`; `flows: {}` | tool repo deliberately does not run pipelines on itself |
| cogpy | legacy | `src/cogpy/workflows/preprocess/Snakefile` — pure snakebids (`from snakebids import bids, generate_inputs`), no pipeio adapter | shows the "before-pipeio" world; predates the project's adoption of `code/pipelines/<flow>/` layout |
| pixecog | extensive | 16 flows in `code/pipelines/`, all `app_type: snakemake`; example Snakefile uses snakebids `set_bids_spec("v0_0_0")` *and* `BidsPaths(in_reg, root, inputs)` | most flows of the cohort; canonical example of snakebids + pipeio compose |
| gecog | medium | 8 flows in `code/pipelines/`; same snakebids + BidsPaths pattern | cleanest single-domain set (factor analysis + sleep spindle + travelling wave) |
| msol | minimal | 3 flows in `code/pipelines/`; **plain snakemake** — `glob_wildcards()` against flat path templates, no snakebids and no BidsPaths | demonstrates a working pipeline without the BIDS-aware adapters — useful for "Snakemake without ceremony" pedagogy |

### Convergent patterns

- Every project that runs pipelines puts them under `code/pipelines/<flow>/`
  with a `Snakefile`, `config.yml`, `scripts/`, and `notebooks/`.
- Every flow output goes under `derivatives/<flow>/` (BIDS-aligned).
- Every study project's Makefile resolves `SNAKEMAKE` through pixi or
  conda env wrapping; none invoke `snakemake` bare.

### Divergent patterns

- **snakebids vs plain snakemake**: cogpy = pure snakebids; pixecog + gecog
  = snakebids + pipeio's `BidsPaths`; msol = plain snakemake. Three
  styles in the same workflow ecosystem.
- **Cross-flow contract**: pixecog + gecog use `manifest.yml` written by
  upstream flows and read via `BidsPaths(safe_load(...manifest.yml), ...)`
  by downstream flows. cogpy is single-flow; msol's three flows do not
  cross-feed via manifests.
- **Flow scale**: pixecog 16 ≫ gecog 8 ≫ msol 3.

### Canonical teaching artifact

**`pixecog/code/pipelines/lfp_extrema/Snakefile` + `config.yml`** —
the registry-extension pattern (the Snakefile programmatically extends
`config['registry']` with one group per detection-tuple, then fans out
seven outputs per slow-wave detection). One artifact that shows
config-driven Snakemake, snakebids wildcards, the `BidsPaths` adapter,
and cross-flow `manifest.yml` consumption all at once.

### Honest gap

Three Snakemake styles coexist in one ecosystem (snakebids alone,
snakebids + BidsPaths, plain snakemake). The workshop should pick the
**snakebids + BidsPaths** style as the default and explicitly position
the others as predecessor (cogpy) and minimal-ceremony (msol) variants.
Trying to teach all three styles in 4 days would dilute the message.

---

## Component 4 — Marimo

### What it does

Marimo is a Python notebook format where the file *is* a `.py` file (no
JSON), cells form a reactive DAG (changing one cell automatically re-runs
its dependents), and the notebook can run as a script, as a server, or as
a static HTML/WASM bundle. Workshop framing: *Jupyter-style narrative,
diff-friendly storage, and reactive-spreadsheet semantics — with no
hidden state.* Marimo plays two distinct roles: (a) per-flow exploratory
notebooks, and (b) handbook explorables exported via `marimo export
html-wasm`.

### How projio is aware of it

- **`pipeio_nb_*` MCP tools** treat marimo as a first-class notebook
  backend alongside jupytext percent-format. `pipeio_nb_create` is
  kind-aware (`investigate`/`explore` vs `demo`/`validate`);
  `pipeio_nb_watch` launches `marimo edit --watch` for live editing;
  `pipeio_nb_snapshot` executes a marimo notebook and reads cell
  outputs (the agent's "eyes" into a notebook); `pipeio_nb_validate`
  runs `marimo check`.
- **`format:` field in `notebook.yml`** selects the backend per notebook.
  Auto-detected when empty (which is currently the case in *every*
  surveyed `notebook.yml`).
- **`marimo-pair` skill** (user-level, not project-local) launches and
  monitors a marimo session and is allow-listed in pixecog's and msol's
  `.claude/settings.json` via the `discover-servers.sh` and
  `execute-code.sh` Bash patterns.

### Adoption across projects

| Project | Adopted? | How / signature artifact | Variation worth teaching |
|---|---|---|---|
| projio | n/a | 12 `import marimo` matches inside `packages/pipeio/` source/tests + 2 docs (`docs/specs/pipeio/notebook.md`, `docs/tutorials/marimo-notebooks.md`); no project-level notebooks | tool reference for the backend |
| cogpy | absent | 0 marimo matches | library repo — does not run notebooks |
| pixecog | extensive | 7 marimo `.py` notebooks under `code/pipelines/{calibrate_ieeg_notch, spectrogram_burst, calibrate_ieeg, preprocess_ecephys}/notebooks/explore/`; 15 `notebook.yml` files; `__marimo__/session/` cache dir at repo root | only project with real marimo authoring; the cache dir leaking into repo root is friction |
| gecog | minimal | 2 explore notebooks (`code/pipelines/travelling_wave/notebooks/explore/{kw_spectrum.py, flow_and_patterns.py}`); 7 `notebook.yml` files | one flow has marimo notebooks, the rest are placeholders |
| msol | absent (notebooks empty) | 3 `notebook.yml` files but the `.src/explore_*.py` paths point to placeholder marimo files; one calibration script (`code/scripts/calibration/calibrate_arena_corners.py`) imports marimo | adopted scaffolding without populating notebooks |

### Convergent patterns

- Every project that has flows uses the `notebooks/{explore,demo}/.src/`
  layout per the `feedback_notebook_layout.md` convention (split source
  vs MyST views; no per-notebook subdirs).
- Every `notebook.yml` is auto-detect (`format: ''`).
- Marimo enters projects via pipeio's notebook tooling — none of the
  projects use `marimo edit` independently of the projio convention.

### Divergent patterns

- **Real adoption** is concentrated in pixecog (7 notebooks across 4
  flows). Other projects have the scaffolding but mostly empty .src files.
- **Cache discipline**: only pixecog leaks `__marimo__/session/` into the
  repo root — should be in `.gitignore`.

### Canonical teaching artifact

**`pixecog/code/pipelines/spectrogram_burst/notebooks/`** — `notebook.yml`
+ a real marimo `.py` notebook in `explore/.src/`. Single concrete
example of (a) the kind-aware notebook layout, (b) a real exploration
notebook checked into the repo, (c) `pipeio_nb_*` discovery.

### Honest gap

Marimo is real on disk in only one project. The workshop can teach
authoring in pixecog, but the second role for marimo (handbook
explorables via `marimo export html-wasm`) has **zero examples** in
the surveyed projects. That is a deliberate handbook target rather
than a current artifact: handbook chapter 1 can include the first
real explorable as part of writing the chapter.

---

## Component 5 — Quarto / MkDocs

### What it does

Both are static-site generators that turn markdown/Quarto-markdown into
HTML, but with different defaults: **MkDocs (with the Material theme)** is
optimized for documentation sites with navigation, search, and MkDocs
plugins (bibtex, monorepo, ezlinks); **Quarto** unifies markdown +
executable code + multiple output formats (website, book, revealjs slides,
PDF) under one source. Workshop framing: *MkDocs for the handbook (a
docs site), Quarto for the workshop (a multi-output course package
where the same source feeds website + book + slides + executable
notebooks).*

### How projio is aware of it

- **`site.framework`** in `.projio/config.yml` (`mkdocs` | `sphinx`) plus
  `output_dir`. **No `quarto` value yet** in the framework enum — Quarto
  enters via `.projio/render/quarto.yml` for individual deliverables.
- **MCP tools**: `site_build`, `site_serve`, `site_deploy`, `site_list`,
  `site_detect`. These dispatch to MkDocs or Sphinx based on `site.framework`.
- **`pipeio_mkdocs_nav_patch`** — patches `mkdocs.yml` nav from collected
  flow docs. No equivalent for Quarto navigation yet.
- **`docs/specs/quarto-reports.md`** + `.projio/render/quarto.yml` — the
  Quarto-for-deliverables convention (per-report `.qmd` files rendered
  to HTML/PDF, separate from the site nav).

### Adoption across projects

| Project | MkDocs | Sphinx | Quarto | Variation worth teaching |
|---|---|---|---|---|
| projio | yes (`theme.name: material`) | no | yes (deliverables only — `.projio/render/quarto.yml`) | only project with both MkDocs and Quarto in the same repo |
| cogpy | yes (material) | **yes** (`docs/build/html`, `Makefile` uses `sphinx-build`) | no | only project on Sphinx (legacy, kept) |
| pixecog | yes (material) | no | no | mkdocs.yml + Makefile splits `serve` and `serve_live` (mike-style versioning) |
| gecog | yes (material) | no | no | minimal mkdocs.yml; Makefile defers to `.projio/projio.mk` |
| msol | yes (material) | no | no | most plugin-rich mkdocs (search + monorepo + ezlinks + bibtex) |

### Convergent patterns

- mkdocs-material is the universal documentation framework across all 5
  projects.
- All study projects' Makefiles include `.projio/projio.mk` for the
  generated docs targets.

### Divergent patterns

- **Sphinx outlier**: cogpy alone runs Sphinx (its API docs were
  pre-existing when it joined the projio ecosystem). Workshop honest
  framing: projio doesn't impose a docs framework.
- **Quarto split**: projio uses Quarto **only for deliverables**
  (`.qmd` reports) under `docs/deliverables/reports/`, not for the
  site itself. The workshop introduces Quarto as the *workshop's
  own* publication framework, not as a projio convention to push
  into other projects.
- **Plugin density**: msol's mkdocs.yml has 4 plugins (search, monorepo,
  ezlinks, bibtex); gecog's is minimal. Worth teaching that
  mkdocs-material is a bare framework — projects choose how much to
  decorate.

### Canonical teaching artifact

**`projio/.projio/render/quarto.yml`** + one `docs/deliverables/reports/*.qmd`
report. Single artifact that shows the projio Quarto-for-deliverables
convention. For MkDocs, **`pixecog/mkdocs.yml`** is the strongest
example — material theme, real navigation, Makefile-wired build.

### Honest gap

The handbook (mkdocs-material) and the workshop (Quarto project) are
**different surfaces with different generators**, and projio has no
convention for cross-linking from one to the other yet. The
*architecture decision* in the source idea note (handbook in projio,
workshop in `teaching/agentic-workshop/`) sidesteps this by separation —
worth surfacing as a deliberate design choice in chapter 1, not as an
unsolved problem.

---

## Component 6 — projio

### What it does

projio is the **project-aware layer** that knows about BIDS conventions,
DataLad subdatasets, Snakemake flows, marimo notebooks, and the docs
framework — and exposes that knowledge through MCP tools so a Claude
Code agent can query "what flows are registered?", "what does this
mod produce?", "where does this paper live?", "what notes did the
agent write last week?", without inventing a path scheme. Workshop
framing: *the stack already does the work; projio makes the stack
queryable.*

### How projio is aware of itself

projio's six subsystems each manage a knowledge domain:

| Subsystem | Domain | Awareness |
|---|---|---|
| **indexio** | retrieval | corpus indexing, chunking, embedding, RAG |
| **biblio** | literature | bibliography, citekey resolution, paper context, docling/grobid |
| **notio** | notes + manuscripts | structured notes, manuscript assembly |
| **codio** | code intelligence | library registry with `role: core/shared/external` |
| **pipeio** | pipelines | flow/mod/rule/notebook/config tooling |
| **figio** | figures | declarative figure orchestration (FigureSpec YAML) |

### Adoption across projects

| Project | indexio | biblio | notio | codio | pipeio | figio | Variation |
|---|---|---|---|---|---|---|---|
| projio | active (2 corpora, 1.3k+75k chunks) | active | active | active (1 first-party + 14 mirrors) | **disabled** (`enabled: false`) | minimal (1 example) | tool repo — pipeio off intentionally |
| cogpy | active | active (full `bib/`) | active (10 log subdirs) | active (~40 external mirrors) | not enabled | absent | strongest codio external-mirror catalog |
| pixecog | active | active | active (9 log subdirs) | active (cogpy/labbox/labpy as `code/lib/*`) | active (16 flows) | dir-only, figs ad-hoc | most flows; densest subsystem usage |
| gecog | active | active | active (5 log subdirs) | active (cogpy/labpy as `code/lib/*`) | active (8 flows) | **1 first-party FigureSpec** | only first-party FigureSpec in the cohort |
| msol | active | **`enabled: false`** (drift) | **`enabled: false`** (drift) | active (database_io/ratcave) | active (3 flows) | absent | only project with two subsystems flagged off |

### Convergent patterns

- All study projects use `code/{lib,pipelines,utils}/` per the code-tiers
  spec.
- All study projects keep `docs/log/{idea,issue,task,result,meeting}/`
  with `index.md` (notio).
- All study projects have `bib/` populated (even msol where biblio is
  flagged off in config).

### Divergent patterns

- **`enabled:` flag drift**: msol declares biblio + notio off while
  using both. projio doesn't auto-reconcile.
- **figio adoption**: 1 first-party FigureSpec across all 5 projects
  (gecog's May-02 cohort). Most figures are ad-hoc `<report>-figs/`.
- **Code tier presence**: cogpy is `src/cogpy/<area>/` flat (no
  `code/lib/`) — it's a library, not a study; the tier convention
  doesn't apply.

### Graded introduction sequence (workshop)

The handbook + workshop introduce projio **gradually**: BIDS + DataLad +
Snakemake + Marimo + Quarto first (workshop day 1 + early day 2), then
projio enters as the layer that *knows* about those conventions. Each
stage motivated by the pain it solves in the prior stage.

| Stage | What's added | Workshop session that introduces it | Stack-awareness payoff |
|---|---|---|---|
| 0 | BIDS root + DataLad super/subdatasets + one snakebids flow + marimo explore notebook + mkdocs site, no projio | Day 1 (full day) | Establish the bare stack works without projio. Pain that motivates next stage: 12 derivatives dirs and no record of which Snakemake config produced each. |
| 1 | `projio sync` + `.projio/config.yml` + `notio` (`docs/log/` + indexes) | Day 2 AM | Project memory: dated tasks/results/ideas under `docs/log/`, navigable via MCP `note_search`. Pain solved: "why was this run produced and by whom?" Pain remaining: cross-flow paths still hand-constructed. |
| 2 | `pipeio` flow registry + `BidsPaths` adapter + `manifest.yml` contract | Day 2 PM | One MCP tool call (`pipeio_flow_list`, `pipeio_target_paths`) returns flow inventory and resolved BIDS output paths. Pain solved: agents and humans stop hand-constructing BIDS wildcards. Pain remaining: paper claims drift from data. |
| 3 | `biblio` + `indexio` (paper ingest, docling extraction, RAG) | Day 3 AM | Citekey-based references resolvable via MCP; full-text search across project corpus. Pain solved: claims back-link to extracted paper text. Pain remaining: figures still ad-hoc per report. |
| 4 | `figio` FigureSpec + `manuscript` subsystem | Day 3 PM | Composable figure specs (one panel-per-rule), auditable `manuscript_cite_check`. Pain solved: one figure spec → multiple outputs (PDF/PNG/SVG). |
| 5 | `codio` library catalog with `role: core` + `agent_instructions()` discovery | Day 3 PM (continues) | Agent-discoverable code reuse — "what library can do XYZ?" → MCP `codio_discover`. Pain solved: agent doesn't reinvent primitives. |

The point of the gradient: each subsystem **earns its complexity** by
solving a problem the previous stage exposed. A workshop participant who
stops at stage 1 still has a working project; each later stage is
additive, not foundational.

### Canonical teaching artifact

**`pixecog/.projio/pipeio/registry.yml`** (16 flows) + `pixecog/.projio/config.yml`
+ the `code/pipelines/lfp_extrema/` flow. Together they show: how
projio discovers flows (registry.yml), how it configures itself
(`.projio/config.yml`), and what a real flow looks like under the
convention.

### Honest gap

`subsystems.<name>.enabled` flags can lag actual on-disk usage, and
projio doesn't auto-detect that drift (msol is the running example).
Likewise figio is mostly aspirational across all five projects: one
first-party FigureSpec exists. The handbook should be honest about
both — the *convention* exists; *uniform adoption* does not.

---

## Component 7 — Agentic on top

### What it does

The "agentic on top" layer is the set of conventions and configurations
that let a Claude Code agent operate on a projio-aware project: which
MCP servers it talks to, which Bash commands and read paths are
pre-approved (`.claude/settings.json`), which prompt-based skills are
discoverable (`.projio/skills/`), and how captures/notes flow into
dispatched tasks (worklog). Workshop framing: *the agent is a
collaborator with bounded permissions, structured context, and routed
work — not an opaque chatbot.*

### How projio is aware of it

- `projio init` scaffolds `.claude/settings.json` (with `mcp__projio__*`
  pre-approved) + `.mcp.json` (projio + worklog + sirocampus baseline).
  Both files gitignored via the `# >>> projio >>>` block.
- **`agent_instructions()` MCP tool** discovers skills from
  `src/projio/data/skills/` (ecosystem) + `.projio/skills/<name>/SKILL.md`
  (project-local; project overrides ecosystem).
- **`skill_read(name)`** returns a skill body — Claude Code surfaces these
  as slash commands.
- **`permissions_sync()`** reconciles project skill listings.

### Agentic-on-top inventory

#### `.claude/settings.json` permission shape

| Project | MCP servers pre-approved | Distinctive Bash | Distinctive Read paths |
|---|---|---|---|
| projio | `mcp__projio__*`, `mcp__sirocampus__*`, `mcp__worklog__*` | `git/python/pip/pytest/make` baseline | `/storage2/arash/**`, 14 `.projio/codio/mirrors/*` |
| cogpy | `mcp__projio__*`, `mcp__sirocampus__*`, `mcp__worklog__*` | typing/lint stack: `mypy/ruff/black/isort/tox/nox/coverage/jupyter/ipython` | `/storage/share/codelib/*` (~17 lab-shared mirrors) |
| pixecog | `mcp__projio__*`, `mcp__sirocampus__*`, `mcp__worklog__*` + `WebSearch` | `pixi search *`, `ssh gamma{1..4} uptime`, `ssh gpu/spikesort/beta/theta uptime`, `bash /home/arash/.claude/skills/marimo-pair/scripts/discover-servers.sh*` | three subdataset trees `code/lib/{cogpy,labbox,labpy}` |
| gecog | `mcp__projio__*`, `mcp__sirocampus__*`, `mcp__worklog__*` **+ `mcp__cogpy__*`** | minimal Bash baseline | `code/lib/{cogpy,labpy}` |
| msol | `mcp__projio__*`, `mcp__sirocampus__*`, `mcp__worklog__*` | `pixi run -e analysis marimo *`, `pixi run marimo *`, `pixi search *`, `pixi install *`, marimo-pair scripts | `code/lib/{database_io,ratcave}` |

Tool wildcards (`mcp__projio__*`) are universal. Explicit Bash command
patterns vary by project domain (typing stack for cogpy, multi-host SSH
for pixecog, pixi+marimo for msol).

#### `.mcp.json` server set

| Project | projio MCP rooted at | Other servers | Notable |
|---|---|---|---|
| projio | this repo | sirocampus + worklog | three-server baseline |
| cogpy | this repo | sirocampus + worklog | baseline |
| pixecog | this repo | sirocampus + worklog | baseline |
| gecog | this repo | **cogpy** + sirocampus + worklog | unique fourth server (`cogpy` MCP exposes the cogpy library's projio tools as a sibling project) |
| msol | this repo | sirocampus + worklog | baseline |

All servers run `python -m projio.mcp.server` via `/storage/share/python/environments/Anaconda3/envs/rag/bin/python` — a single env hosts every MCP server in the ecosystem.

#### Skills

- **Project-local** (`.projio/skills/<name>/`):
  - projio: `figio-guide`, `projio-setup` (2)
  - cogpy: `cogpy-dev` (1)
  - pixecog: `pixecog-flow-setup` (1)
  - gecog: 0
  - msol: 0
- **User-level** (`.claude/skills/`):
  - projio: `gitnexus` (1)
  - everywhere else: directory does not exist
- **Ecosystem skills** (always available via `agent_instructions()`):
  ~25 skills from `src/projio/data/skills/` — `figio-guide`,
  `pipeio-guide`, `marimo-session`, `marimo-pair`, `pipeio-nb-extract`,
  `progress-report-deck`, `literature-presentation`, `idea-capture`,
  `questio-*` (7), `biblio-batch-curate`, `codelib-discovery`,
  `mcp-tool-scaffold`, `rag-query`, etc.

#### Captures → tasks pattern (worklog)

Across projects: notes captured via `worklog_note(text, project_id)`
land in `docs/log/idea/` or `docs/log/issue/` per kind. Tasks promoted
via `promote_to_task(source)` land in `docs/log/task/<task>.md` with
`status: scheduled`, then are dispatched via `worklog_note(...,
auto_dispatch=True, model="opus|sonnet")` or `schedule_queue(after=...)`
for dependency-based chains.

This very session is itself a teaching artifact: the source idea note
(`docs/log/idea/idea-arash-20260507-221835-382557.md`) → three task
notes (`task-arash-20260508-160000-200001.md` etc.) → this result note
all live in projio's `docs/log/` and trace a real planning loop.

#### Hooks

**No `hooks` key** in any of the five projects' `.claude/settings.json`.
Permissions are per-project; cross-cutting automation (Stop / PreToolUse)
is currently absent across the cohort. The workshop and handbook can
introduce hooks as "advanced" rather than as baseline practice.

#### Routing (model + host)

- Model selection follows the worklog-MCP convention: opus for
  synthesis (multi-package, architectural), sonnet for execution
  (single-module, clear scope), haiku for triage (trivial/typo).
  `auto_dispatch=True` defaults to opus.
- Host routing is encoded only in pixecog's `.claude/settings.json`
  via the `ssh gamma{1..4}/gpu/spikesort/beta/theta uptime` allow-list —
  that's where multi-host work happens. The other projects don't expose
  cross-host SSH in their permission set.

### Adoption summary table

| Project | hooks | project skills | extra MCP servers | distinctive permission shape |
|---|---|---|---|---|
| projio | none | 2 + user-level `gitnexus` | none beyond baseline | mirror Read globs |
| cogpy | none | 1 (`cogpy-dev`) | none beyond baseline | typing/lint Bash |
| pixecog | none | 1 (`pixecog-flow-setup`) | none beyond baseline | multi-host SSH + pixi + marimo-pair |
| gecog | none | 0 | **cogpy MCP** | minimal — cleanest "default" project |
| msol | none | 0 | none beyond baseline | pixi-env-named marimo Bash |

### Convergent patterns

- Three-server MCP baseline (projio + worklog + sirocampus) is
  universal.
- `mcp__<server>__*` wildcards must appear in **both**
  `permissions.allow` and `allowedTools` for auto-approval (per the
  user's `feedback_mcp_permissions.md` memory). Every surveyed project
  follows this.
- Read access to `/storage2/arash/**` and `/storage/share/sirocampus/**`
  is universal — the cross-project read substrate.

### Divergent patterns

- **Project-local skills**: present in 3/5 projects, absent in 2/5
  (gecog, msol). Skill authoring is real but not yet baseline.
- **Bash permission shape** mirrors project domain: cogpy = library
  hygiene; pixecog = multi-host research compute; msol = pixi+marimo
  workflow; gecog = minimal.
- **Fourth MCP server**: gecog uniquely wires `cogpy` as a per-project
  MCP server, exposing the cogpy library's projio tools alongside its
  own — the only example of a non-baseline projio MCP server in the
  cohort.

### Canonical teaching artifact

**`pixecog/.claude/settings.json` + `pixecog/.mcp.json` + the
`docs/log/idea/ → docs/log/task/ → docs/log/result/` chain for any
recent multi-step initiative**. One bundle that shows: tool wildcards,
explicit Bash command patterns for multi-host SSH, marimo-pair script
allow-listing, and the captured-to-dispatched-to-result flow as
auditable artifacts.

### Honest gap

Hooks are unused (zero across the cohort). Project-local skills are
present in only 3/5 projects. The "agent operates with bounded
permissions and structured context" pattern is real but not uniformly
adopted. Workshop should introduce skills + hooks as **graduated
adoption** rather than as baseline.

---

## Universal patterns across the stack

These hold across every component that's adopted by a project:

1. **The repository is the unit of knowledge** — everything (data,
   code, papers, notes, deliverables, configs, agent settings) lives
   in or alongside one git/datalad superdataset. No separate "knowledge
   base" elsewhere.

2. **Conventions over configuration** — BIDS for data, DataLad for
   versioning, `code/{lib,pipelines,utils}/` for code, `docs/log/{idea,
   task,result,...}/` for notio, `derivatives/<flow>/` for outputs,
   `.projio/` for tool state. Each tool surfaces its own conventions
   so that an agent or a new collaborator can navigate a project they
   have never seen.

3. **MCP wildcards in both permission slots** — every project's
   `.claude/settings.json` lists `mcp__<server>__*` in both
   `permissions.allow` and `allowedTools`. This is non-obvious from
   Claude Code defaults and is enforced socially.

4. **Subsystem-disable as a config flag, not a deletion** — turning
   off `pipeio` (projio) or `biblio`/`notio` (msol) in
   `.projio/config.yml` prevents the subsystem from being invoked but
   leaves the on-disk state alone. Drift between flag and state is
   possible.

5. **Snakemake outputs land under `derivatives/<flow>/` and are
   registered as DataLad subdatasets** (in pixecog and gecog —
   the convention msol is mid-adopting).

6. **Cross-flow contract is `manifest.yml` + `BidsPaths`** in the
   electrophysiology projects — Snakemake's input/output alone is
   not the integration glue.

7. **Three MCP servers minimum**: projio (rooted at the project) +
   sirocampus + worklog. All run from one shared `rag` conda env.

8. **`projio sync` is the periodic reconciliation step** — auto-detects
   `code/lib/*/`, generates `.projio/projio.mk`, copies CSL/Lua
   filters, regenerates skill index. Without it, drift accumulates.

9. **Notes are the audit trail** — `docs/log/{idea,task,result,...}/`
   with daily/weekly indexes captures the *why* of every dispatched
   task and every produced result. The chain itself is navigable
   knowledge, not a side-effect of work.

---

## Recommended teaching artifacts (one per component, 7 total)

Ranked by leverage (impact × concreteness × low explanatory friction)
within each component. Each entry maps to a specific workshop session
and a specific handbook chapter.

| # | Component | Artifact | Project | Anchors |
|---|---|---|---|---|
| 1 | BIDS | `pixecog/raw/` (strict BIDS) + `pixecog/derivatives/preprocess_ieeg/manifest.yml` (soft-form derivative root) | pixecog | Workshop **Day 1 AM**; Handbook ch. "BIDS in practice" |
| 2 | DataLad | `gecog/.gitmodules` (9 entries, single-RIA-store layout) | gecog | Workshop **Day 1 AM**; Handbook ch. "DataLad as a coherent subdataset graph" |
| 3 | Snakemake | `pixecog/code/pipelines/lfp_extrema/Snakefile` + `config.yml` (registry-extension pattern) | pixecog | Workshop **Day 1 PM**; Handbook ch. "config-driven pipelines" |
| 4 | Marimo | `pixecog/code/pipelines/spectrogram_burst/notebooks/` (real `.src/explore_*.py` + `notebook.yml`) | pixecog | Workshop **Day 2 AM**; Handbook ch. "reactive notebooks for analysis and explorables" |
| 5 | Quarto / MkDocs | `projio/.projio/render/quarto.yml` + `pixecog/mkdocs.yml` (the two surfaces) | projio + pixecog | Workshop **pre-workshop setup** (build the site once on day 0); Handbook ch. "publication framework" |
| 6 | projio | `pixecog/.projio/pipeio/registry.yml` (16 flows) + `pixecog/.projio/config.yml` + `pixecog/code/pipelines/lfp_extrema/` | pixecog | Workshop **Day 2 PM** + **Day 3 AM**; Handbook chs. "the project as a queryable knowledge environment" + "the pipeio subsystem" |
| 7 | Agentic on top | `pixecog/.claude/settings.json` + `pixecog/.mcp.json` + a recent `docs/log/idea → task → result` chain (gecog mlclassifier or pixecog detection_qc) | pixecog (settings) + gecog (chain) | Workshop **Day 2 AM** intro + **Day 3 PM**; Handbook ch. "the iterative loop" |

Notes on the shortlist:

- **pixecog dominates** the artifact list (5 of 7 entries) because it
  has the densest stack adoption — the strongest single project to
  dissect for a workshop.
- **gecog provides the agentic chain** because the `brainstate.mlclassifier`
  arc (Apr 29 – May 6) is the cleanest, most narrative `idea → task → result`
  loop in any project's `docs/log/`.
- **msol provides domain diversity** for the "this generalizes beyond
  electrophysiology" slot in workshop day 1, but is not the canonical
  artifact for any single component (it under-adopts DataLad subdatasets
  and Marimo, doesn't use snakebids/BidsPaths).
- **cogpy provides the legacy snakebids reference** (`src/cogpy/workflows/preprocess/Snakefile`)
  but is not on the canonical list — workshop introduces it as
  "before-pipeio" backdrop, not as the artifact to dissect.

---

## Honest gaps

Consolidated from the seven component-level gaps, plus one cross-cutting
gap. State each as a sentence, then a sentence on what the handbook /
workshop should do about it.

1. **Derivative roots aren't BIDS-valid** (no per-derivative
   `dataset_description.json`). The workshop teaches `manifest.yml` as a
   *projio convention layered on BIDS*, not as BIDS itself. Open question
   for a future projio convention iteration: should `pipeio_flow_new`
   emit a derivative `dataset_description.json`?

2. **Subdataset-per-derivative is socially enforced**, not automatic.
   msol shows the consequence: a study can be DataLad-initialized
   while most of the directory tree is not actually subdatasetted. The
   handbook chapter on DataLad should teach the convention as a
   *deliberate choice at flow-creation time*, with `pipeio_flow_new`
   prompting the user to register the subdataset.

3. **Three Snakemake idioms coexist** (snakebids alone in cogpy,
   snakebids + BidsPaths in pixecog/gecog, plain snakemake in msol).
   The workshop picks **snakebids + BidsPaths** as default and labels
   the others as legacy / minimal-ceremony variants — no attempt to
   teach all three.

4. **Marimo's second role (handbook explorables) has zero examples
   yet** in any surveyed project. The first explorable is a deliberate
   handbook target, not an existing artifact to dissect. Plan the first
   explorable into chapter 1's writing schedule, not into pre-workshop
   reading.

5. **Quarto and MkDocs don't cross-link** between the handbook surface
   and the workshop surface. The architecture decision in the source
   note (handbook in projio, workshop in `teaching/agentic-workshop/`)
   sidesteps this by separation, but the user-facing path between the
   two surfaces is currently "navigate the URL bar." Worth surfacing as
   a deliberate choice in chapter 1, not as an unsolved problem.

6. **`subsystems.<name>.enabled` flags drift from on-disk reality**
   (msol has biblio + notio off while using both). projio doesn't
   auto-reconcile. The workshop advises periodic `projio sync`; the
   handbook should mention the drift exists.

7. **Hooks are unused** across all 5 projects' `.claude/settings.json`,
   and project-local skills are present in only 3/5. The "agent
   operates with bounded permissions and structured context" pattern
   is real but not uniformly adopted. Introduce skills + hooks as
   *graduated* adoption rather than baseline.

8. **Cross-cutting**: every project in this set has **one author**
   (Arash). The single-author fragility named in the source idea
   note (Quantomatic precedent) applies to every component of the
   stack as projio uses it. The handbook + workshop are the
   docs + examples + community legs of the survival strategy. Name
   this as motivation in chapter 1, not as deflection.

---

## Method

- Read the prior `result-arash-20260508-tool-use-survey.md` once for
  paths and tool names; framed new prose around the seven stack
  components, not subsystems.
- Used `mcp__worklog__worklog_read_file` to read each project's
  `.claude/settings.json`, `.mcp.json`, `.projio/config.yml`, `pixi.toml`,
  `Makefile`, `.gitmodules`, `.datalad/config`, `.projio/pipeio/registry.yml`,
  one example `Snakefile` per project, and one example `notebook.yml` per
  project.
- Used a general-purpose agent in parallel to gather counts, file
  inventories, and the marimo / `__marimo__` cache scan across all
  five projects.
- Cross-checked findings against the prior tool-use survey for paths
  and adoption counts; this survey is internally consistent with that
  survey but reframes the same evidence on the stack axis.
- No source projects modified.
