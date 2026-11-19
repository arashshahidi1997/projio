# Study template defaults: Quarto site, analysis threads

**Status:** draft, decisions taken with the user on 2026-11-19. No code until the user approves this spec.
**Origin:** idea [[idea-arash-20260411-173908-283692]] (study profiles), triage handoff
[[handoff-arash-20261119-165657-000000]].
**Related specs:** [quarto-reports.md](quarto-reports.md), [deliverables.md](deliverables.md),
[layout-config.md](layout-config.md), [research-orchestration/design.md](research-orchestration/design.md) (questio,
superseded in part by this spec).

## 1. Decisions

| # | Question | Decision (the user, 2026-11-19) |
|---|----------|----------------------------------|
| D1 | Default site for `projio init --kind study` | Quarto website |
| D2 | mkdocs | Deprecated, removed later |
| D3 | When mkdocs can be removed | Only after a migration spec exists and pixecog, gecog, msol and cogpy have moved or chosen to pin an older projio. No date |
| D4 | How far the deprecation reaches now | Study projects only. Tool and generic defaults (mkdocstrings vs quartodoc) and projio's own docs get their own spec |
| D5 | questio (`plan/questions.yml`, `plan/milestones.yml`) | Replaced by analysis threads. questio tools and skills are deprecated for one release with pointers to the thread skills, then removed. `plan/` is no longer created |
| D6 | How much thread structure a new study gets | Docs plus skills: `docs/analysis/` pages and generic ecosystem skills ported from pixecog. Exploration code and outputs are a written convention, not created |
| D7 | Migration tooling for existing mkdocs projects | None yet; a later spec |

## 2. What exists today (survey, 2026-11-19)

**`projio init --kind study`** (`src/projio/init.py`, `_scaffold_study`) writes:

- `.projio/config.yml` with `layout.plan: plan` and `site.framework` from detection (falls back to `mkdocs`);
- `mkdocs.yml` (`STUDY_MKDOCS`): material theme; plugins `search`, `ezlinks`, `include-markdown` (no settings),
  `bibtex` on `.projio/render/compiled.bib`, `monorepo`, `mkdocs-jupyter`; a nav of `!include` sub-sites for
  Pipelines, Plan, Log and Infra;
- `docs/{log,plan,pipelines,manuscript,infra,deliverables,assets}/index.md` stubs and `docs/study-overview.md`;
- `code/{pipelines,lib,scripts,utils}/`;
- `.projio/render.yml`;
- `plan/questions.yml` and `plan/milestones.yml` (empty lists).

`SITE_FRAMEWORK_CHOICES` is `mkdocs`, `sphinx`, `vite`. There is no `quarto` framework.

**`projio sync`** keeps mkdocs in shape: `_sync_mkdocs_monorepo` adds `monorepo`, writes the sub-navs
`docs/{log,manuscript,pipelines,plan,<sec>}/mkdocs.yml` and the root `!include` lines; `_sync_questio_docs` regenerates
`docs/plan/` from `plan/questions.yml`; `_sync_deliverables_index` writes the deliverables indexes;
`_sync_quarto_config` creates `.projio/render/quarto.yml` (only `min_version`).

**Quarto today** is a report backend only: `report_init` / `report_build` (`src/projio/mcp/report.py`) render
`docs/deliverables/reports/<name>/report.qmd` with its own `_quarto.yml`, a min-version check and runner-aware command
resolution (`_resolve_quarto_cmd`). No project in `/storage2/arash/projects` or `/storage/share` has a Quarto website.

**Features that assume mkdocs:**

| Where | What |
|-------|------|
| `projio.init` | `STUDY_MKDOCS`, `DEFAULT_MKDOCS`, `MKDOCS ?=` in `projio.mk`, GitHub/GitLab Pages templates |
| `projio.site`, `mcp/site.py` | detection, build, serve; the docs chatbot hook is mkdocs-only |
| `projio.sync` | monorepo plugin and `!include` nav |
| notio (`notio.docs`, `mcp/notio.py`) | `docs/log/mkdocs.yml` sub-nav; `diataxis_init(mkdocs=True)` nav snippet |
| pipeio (`pipeio.docs`, `mcp/pipeio.py`) | `docs/pipelines/mkdocs.yml`, `pipeio_mkdocs_nav_patch` |
| manuscripto (`mcp/manuscripto.py`) | `docs/manuscript/mkdocs.yml` and per-section sub-navs |
| questio (`mcp/questio.py`) | `docs/plan/` pages and the deliverables sub-nav |
| `helpers/docs.py` | `mkdocs_init` |
| Content syntax | `[[wikilinks]]` (ezlinks) in every notio note; `{% include-markdown %}` in master files; `!!!` admonitions where authors used them |

**questio in use:** `plan/questions.yml` exists in cogpy, gecog, largescale-infraslow and msol. All four hold zero
questions and zero milestones. pixecog has no `plan/`.

**pixecog's analysis threads** (`pixecog/docs/infra/repo-architecture.md` §5.3, `scope.md` "Lifecycle: knowledge and
findings"):

- A thread is a key (`spindle`, `swr_so_coupling`, ...) shared by the note series (`series: <thread>`), exploration
  code (`code/explore/<thread>/`) and exploration outputs (`explore/<thread>/<sweep>/`).
- Each thread has one state doc, `docs/analysis/<thread>/index.md`: frontmatter (`thread`, `state_as_of`,
  `verification`), then the scientific question, current working model, established results, interpretations,
  analysis decisions, rejected approaches, open questions and next analyses. IDs are `R` (result), `I`
  (interpretation), `D` (decision) and `O` (open question), prefixed by the thread (`TOPO-R01`).
- `docs/analysis/index.md` lists the threads; `docs/analysis/hypotheses.md` is the hypothesis registry (H ids, status
  stated with the evidence it rests on, pointing at finding IDs, never holding a to-do).
- A result note is dated, immutable evidence: `series`, `hypothesis`, `runs`, `subjects`, `metric`, `value`, `figure`,
  `confidence`. A finding becomes citable when the state doc gets a finding ID that cites the note.
- New work is an O item in a state doc. The skills `px-analysis-orientation`, `px-analysis-log`,
  `px-analysis-checkpoints` and `px-promote` carry the procedure.

This is questio's model (question, milestone, evidence) kept as prose pages that a person and an agent both read, and
it is the one in daily use.

## 3. Default site: Quarto

### 3.1 Layout

A new study project gets a Quarto website rooted at `docs/`:

```
docs/
  _quarto.yml        # human-owned site config
  _projio.yml        # generated by projio sync (header says so); merged via metadata-files
  index.md
  analysis/          # §5
  log/  pipelines/  manuscript/  infra/  deliverables/  assets/
_site/               # build output (gitignored), site.output_dir
```

Rooting the project at `docs/` keeps page URLs free of a `docs/` prefix and keeps `code/` and data out of the render.
Files starting with `_` are not rendered, so `_projio.yml` and any `_template` folders stay out of the site.

### 3.2 `docs/_quarto.yml` (template)

```yaml
project:
  type: website
  output-dir: ../_site

metadata-files:
  - _projio.yml          # generated: sidebar, bibliography, CSL, filters. Remove this line to opt out.

website:
  title: "{name}"
  navbar:
    left:
      - href: index.md
        text: Home
      - analysis/index.md
      - log/index.md

format:
  html:
    toc: true
    from: markdown+wikilinks_title_after_pipe
```

The person owns this file; sync never edits it.

### 3.3 `docs/_projio.yml` (generated by sync)

Sync writes one fragment, the Quarto counterpart of the mkdocs sub-navs:

- **sidebar:** one section per subsystem that is present (Analysis, Pipelines, Manuscript, Deliverables, Log, plus any
  other `docs/<sec>/` with an index), each with `contents: <sec>/` so Quarto lists the folder itself. No per-note nav is
  generated.
- **bibliography and CSL** from `.projio/render.yml` (`bibliography`, `csl`), so `render.yml` stays the single source
  of truth for citation settings, as it is for pandoc.
- **filters:** `../.projio/filters/wikilink.lua` (§3.4) and `../.projio/filters/include.lua`.

The fragment carries a generated-file header (docs convention: human and generated docs co-locate in `docs/`, headers
mark generated files).

### 3.4 Content compatibility

- **Wikilinks.** notio notes link with `[[note-id]]` and `[[note-id|text]]`. Pandoc's `wikilinks_title_after_pipe`
  extension parses these into links; a new bundled filter `src/projio/data/filters/wikilink.lua`, copied to
  `.projio/filters/` by sync like `include.lua`, resolves each target to the relative path of the file with that stem
  under `docs/`. An unresolved target renders as plain text and logs a warning.
- **Transclusion.** `include.lua` already handles `{% include-markdown %}` and `--8<--` for pandoc; the site uses the
  same filter, so master files render the same on the site and in PDF. New content may use Quarto's
  `{{< include >}}`.
- **Callouts.** New templates and skills write Quarto callouts (`::: {.callout-note}`). Existing `!!!` admonitions are a
  migration concern (§7).
- **Notebooks.** `.ipynb` files render natively (not executed by default), which replaces `mkdocs-jupyter`.

### 3.5 Reports inside the site

In a project with a Quarto site, `docs/deliverables/reports/<name>/` is inside the website project. A report's
`_quarto.yml` then acts as directory metadata (format, execution), and the report renders as a site page. `report_build`
keeps its interface and resolves the output path from the project's output dir instead of `build/`. Projects without a
Quarto site keep today's behavior (each report its own project). See §8, V1.

### 3.6 Tooling

- `SITE_FRAMEWORK_CHOICES` gains `quarto`. Detection order: explicit `site.framework`, then `docs/_quarto.yml` or a root
  `_quarto.yml` with `project.type: website`, then mkdocs, sphinx, vite. Nested report `_quarto.yml` files are not
  looked at, so existing projects are not misdetected.
- `site_build` runs `quarto render docs`; `site_serve` runs `quarto preview docs --host <h> --port <p> --no-browser`.
  The quarto command comes from the runner chain `report.py` already has (`_resolve_quarto_cmd`, moved to
  `projio.runners` so both use it).
- `projio.mk` gains `QUARTO ?= quarto`; the docs targets dispatch on `site.framework`.
- `.gitignore` block: `_site/`, `docs/.quarto/`, and the freeze dirs already listed for reports.
- GitHub and GitLab Pages templates get a Quarto variant (`quarto-dev/quarto-actions/setup`, or a Quarto image).
- The docs chatbot (`site.chatbot`) stays mkdocs-only for now (§6).

## 4. mkdocs: deprecated

- **Init.** `--kind study` defaults to Quarto. `--site mkdocs` still works for study projects and prints a one-line
  deprecation notice. Tool and generic kinds are unchanged (D4).
- **Sync.** The mkdocs steps keep running on projects that have `mkdocs.yml`, unchanged, with a one-line notice per run.
  No new mkdocs features are added.
- **Subsystem sub-navs** (notio log, pipeio pipelines, manuscript, plan, deliverables) are written only when
  `site.framework` is `mkdocs`. Their index pages are plain markdown and are written for every framework.
- **mkdocs-only tools** (`pipeio_mkdocs_nav_patch`, notio `diataxis_init(mkdocs=True)`, `helpers.docs.mkdocs_init`)
  say "deprecated (mkdocs)" in their descriptions and keep working.
- **Removal** waits for D3. This spec sets no date.
- **Issue 20260402-121445** (sync ensures `include-markdown` with pixecog's settings) is not worth doing: it is mkdocs
  work, the one project that needs the settings (pixecog) already carries them in its own `mkdocs.yml`, and gecog has
  the plugin without settings and builds. Recommend closing it as superseded by this spec.

## 5. Analysis threads replace questio

### 5.1 What a new study project gets

```
docs/analysis/
  index.md         # thread table: thread, what it covers, hypotheses
  hypotheses.md    # hypothesis registry: H ids, status with its evidence base, finding IDs
```

Thread state docs (`docs/analysis/<thread>/index.md`) are created by the `analysis-log` skill (SEED mode) when the first
thread starts, from a template that ships with the skill. Init creates no thread.

`layout.plan: plan` is replaced by `layout.analysis: docs/analysis`. Without `.projio` (a generic project) the skills
default to `docs/analysis/`.

### 5.2 Conventions (written in the skills and the study overview page)

- **Thread key** (`snake_case`) is shared by the note series (`series: <thread>`), the state doc folder and, where the
  project has exploration code, `code/explore/<thread>/`. Exploration outputs, their storage and provenance are the
  project's choice; pixecog's `explore/` subdataset is one example, not a default (D6).
- **State doc**: frontmatter `thread`, `title`, `state_as_of` (`date`, `git_commit`, `latest_note`), `verification`
  (`synthesis`, `human_reviewed`); sections Scientific question, Current working model, Established results,
  Interpretations, Analysis decisions, Rejected approaches, Open questions, Next analyses, Evidence index.
  IDs `<KEY>-R01`, `-I`, `-D`, `-O`.
- **Hypothesis registry**: a status always names what it rests on; status comes from finding IDs only; new work is an O
  item in a state doc, never a to-do in the registry.
- **Result note**: the notio `result` template drops `question` and `milestone` and gains `hypothesis: []` and
  `runs: []`; `series` is the thread key. A result note has no status; the finding ID in the state doc carries it.

### 5.3 Skills

Two ecosystem skills, generalized from pixecog's and marked `metadata.portable: true` (they need only git and the docs
folder):

| Skill | From | Modes |
|-------|------|-------|
| `analysis-orientation` | `px-analysis-orientation` | THREAD (where a thread stands, from its state doc, with deltas since `state_as_of`); NEXT (open O items across threads, ranked); OVERVIEW. Runs the project's status command first if it names one (`analysis.status_cmd`, optional) |
| `analysis-log` | `px-analysis-log` | RECORD (result note plus finding ID); SEED (new thread state doc from notes and git); UPDATE (fold a session's results, decisions and O items into the doc) |

pixecog-specific parts (dstatus, lit-studio consultation, the explore subdataset, cohort rules) stay in pixecog's own
skills, which keep working. `px-analysis-checkpoints` and `px-promote` are not ported now (D6).

### 5.4 questio mapped onto threads

| questio | Thread replacement |
|---------|--------------------|
| `plan/questions.yml` question | `hypotheses.md` entry and the thread's Scientific question |
| `plan/milestones.yml` milestone | O items and Next analyses in a state doc |
| result note `question`, `milestone` | result note `series`, `hypothesis`, and the finding ID that cites it |
| `questio_status` | `analysis-orientation` THREAD / OVERVIEW |
| `questio_gap` | open O items; literature before/after notes under an O item |
| `questio_prior_art` | `literature-audit`, `literature-discovery` |
| `questio_docs_collect` (plan pages) | none; state docs are the pages |
| `deliverables_docs_collect` | stays; moves out of `mcp/questio.py` into its own module |
| skills `questio-ground`, `-next`, `-record`, `-session` | `analysis-orientation`, `analysis-log`, `session-wrap` |
| skill `questio-report` | `report_init` / `report_build` |
| skills `questio-investigate`, `-iterate` | kept, renamed `analysis-investigate`, `analysis-iterate`, with questio tool calls replaced by state-doc reads |

### 5.5 Deprecation of questio

One release, following the biblio pattern: each questio tool's description names its replacement; `questio-*` skill
names stay as stubs that point at the new skills; `agent_instructions` and the generated CLAUDE.md drop questio rows.
Sync keeps `_sync_questio_docs` for projects with a non-empty `plan/` during that release. Then the questio tools,
skills and sync step are removed. `plan/` folders in existing projects are never deleted by projio.

## 6. Existing projects: nothing forced

- mkdocs projects (pixecog, gecog, msol, cogpy) keep building with today's sync. The only change they see is the
  deprecation notice.
- Empty `plan/` folders (cogpy, gecog, largescale-infraslow, msol) stay until a person removes them; sync ignores an
  empty plan.
- pixecog keeps its `px-*` skills and may adopt the ecosystem skills when it chooses.
- A project without `.projio` (generic layout) can use the thread skills and a Quarto site; nothing in this spec requires
  `.projio` or the study kind.
- `projio init --kind study` on an existing folder never overwrites (`_write_if_needed`) and keeps the detected
  framework: where `mkdocs.yml` exists it stays mkdocs. Quarto is the default only where no site config exists, or with
  an explicit `--site quarto`.

## 7. Out of scope

- Migration of existing mkdocs projects to Quarto (tooling or guide): a later spec (D7). It covers `!!!` admonitions,
  mkdocs-only plugins, nav ordering, Pages CI and the chatbot.
- Defaults for tool and generic kinds, and projio's own docs site (D4).
- The docs chatbot on a Quarto site.
- Exploration storage and provenance (`explore/`, run manifests); porting `px-analysis-checkpoints` and `px-promote`.
- Marimo notebooks on the site.
- An MCP tool for threads. Skills first; a `thread_list`-style tool only if the skills need one.
- Removing mkdocs code (D3).

## 8. To verify during implementation

- **V1** A report folder with its own `_quarto.yml` inside a `docs/` website project: does `quarto render` of one
  `report.qmd` behave as directory metadata and write into `../_site`, and do `{{< embed >}}` paths into
  `code/pipelines/` (outside the project dir) still resolve? If not, exclude `deliverables/reports/` from the site render
  and keep reports as separate renders linked from the site.
- **V2** `metadata-files` merges `website.sidebar`, `bibliography`, `csl` and `filters` from `_projio.yml`
  (quartodoc's `_sidebar.yml` relies on the sidebar part).
- **V3** `include.lua` runs unchanged as a Quarto filter (Quarto's markdown reader and `{%` text).
- **V4** Render time on a site with thousands of notio notes (pixecog's `docs/log/` size), for the later migration
  spec.

## 9. Follow-up kickoffs (for the manager; none started)

1. **projio-site · Quarto site framework.** §3.3, §3.4, §3.6, and the framework-aware sub-nav skip in §4: `quarto` in
   `site.py` (detect, build, serve), quarto command resolution shared with `report.py`, `wikilink.lua`, sync writes
   `docs/_projio.yml`, `projio.mk` and Pages templates, gitignore. Start with V1 to V3 on a scratch project. Done when a
   scratch study site builds with wikilinks, citations and a report page, and the tests cover detection and the
   fragment.
2. **projio-init · study template defaults.** After kickoff 1. §3.1, §3.2, §4 init notice, §5.1: Quarto default for
   `--kind study`, `docs/analysis/` pages, no `plan/`, `layout.analysis`, result template fields (notio), sirota profile
   `site` block (drop `mkdocs.site_dir`). Done when `projio init --kind study` on an empty folder builds with
   `site_build` and the init tests cover it.
3. **projio-skills · analysis thread skills.** Independent of 1 and 2. §5.2, §5.3: `analysis-orientation` and
   `analysis-log` with the state-doc and registry templates, ported from pixecog's skills (read-only there), portable,
   copied to `docs/prompts/skills/`. Done when both run on pixecog's thread docs read-only and on a fresh
   `docs/analysis/`.
4. **projio-questio · deprecate questio.** After 3. §5.4, §5.5: tool descriptions, skill stubs and renames,
   `agent_instructions` and CLAUDE.md codegen (and the worklog instruction copies), `deliverables_docs_collect` moved
   out, docs. Done when no default-path instruction mentions questio and the stubs point at the new skills.
5. **Close issue 20260402-121445** as superseded by this spec (§4). A note edit for the manager.

Later, not now: the mkdocs-to-Quarto migration spec (D7); tool and generic kind defaults (D4).

## 10. Acceptance

- A fresh `projio init --kind study` has `docs/_quarto.yml`, no `mkdocs.yml`, no `plan/`, and `docs/analysis/` with
  `index.md` and `hypotheses.md`; `site_build` renders it.
- `projio sync` on pixecog, gecog, msol and cogpy changes nothing beyond printing the mkdocs notice.
- The thread skills work in a project without `.projio`.
- No questio tool or skill appears in default agent instructions after the deprecation release.
