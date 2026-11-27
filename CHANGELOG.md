# Changelog

## Unreleased

### Changed
- **projio-workflow 0.6.0**: three manager changes in the `project-manager` core. Lean verify (decided 2026-11-27): every kickoff carries a `Verify:` line (files expected to change, tests); when a session reports done the manager runs `git show --stat` on its commits against that line and flags unexpected or missing files and a missing test run to the user; a read-only verify subagent in fresh context only when that check flags something, the kickoff touches files other sessions edit, or the user asks. Manager handoff by name (2026-11-24): managers are addressed by exact name only, no session ids in a board, kickoff or memory, Sync lists names; a retiring manager renames itself `<prefix>manager · retired <date>` and turns its Remote Control off, the new one sends `moved · <prefix>manager · <machine>` to the cross-project manager, a retired session forwards stray messages once. Session home (2026-11-26): at a laptop the standing manager runs in the desktop app with Remote Control on, Remote Control listeners only start sessions from the phone, one standing manager per project; phone-side and extra-machine sessions are the one case the board records an id. `session-wrap` reports to the manager by name with the commit shas and test run; the `round.py board` skeleton, `manager-setup` and its adapter template follow.
- **projio-workflow 0.5.0**: a manager board's `## Decisions waiting for you` uses one line per open question, the format worklog's cross-project hub parses (adopted 2026-11-24): `- **<question>?** · <option A> / <option B> (rec. A) · YYYY-MM-DD`, with the date first asked, the project first on cross-project boards, context in indented sub-bullets, settled items after a plain `Recent answers:` paragraph or struck through, waits under Waiting on others, deferred items kept with `parked` as an option. In the `project-manager` core (Board, Decisions, Decision drill, Hard rules), the `round.py board` skeleton and the `manager-setup` adapter template.

### Added
- **projio-workflow 0.4.0**: two analysis-thread skills (docs/specs/study-template-defaults.md §5.2, §5.3), ported from pixecog and portable (git and the docs folder only). `analysis-orientation` (read-only): THREAD (where a thread stands, from its state doc `docs/analysis/<thread>/index.md`, with the notes and commits since its `state_as_of` watermark), NEXT (open O items across threads, ranked) and OVERVIEW, with the stdlib helper `threads.py`. `analysis-log`: RECORD (result note plus finding ID), SEED (new state doc; `docs/analysis/index.md` and `hypotheses.md` when missing) and UPDATE, with templates for the state doc, the thread index, the hypothesis registry and a result note.

### Deprecated
- **notio.present (decks)**: deprecated (docs/specs/notio/slim.md §7, 2026-11-24) and removed after the next notio release. The 15 `present_*` MCP tools are opt-in: they load only when `.projio/packages.yml` has `present: {enabled: true}` or `PROJIO_MCP_TOOLS` names `present` (or a `present_*` tool). Their descriptions, the generated agent instructions, the `literature-presentation` and `progress-report-deck` skills and the presentio docs point to Quarto reveal.js and the `quarto-talks` skill. `toolset.OPT_IN` is the general switch for opt-in groups.

### Fixed
- **projio-workflow 0.3.1**: the file inbox is off (one warning line) when `files_inbox` equals, sits inside or contains an `incoming.dirs` folder, so committed incoming notes in a folder named `inbox/` are neither gitignored nor listed as downloads.

### Changed
- **projio-workflow 0.3.0**: the plugin is versioned on its own (a release is a version bump, `projio skills export`, a push), so a manager-core update ships without a projio release. The `project-manager` core gains a Core updates section: each project's manager applies an update in its own project, reloads and confirms in one line; the owning project ships and announces it. It also adds the file inbox: `files_inbox` in the manager config (default `inbox`), listed first by `round.py` with a proposed move per file (nothing moves without the user's word, never into another project); `projio init` and `projio sync` create the folder and add it to the managed .gitignore block. 0.3.0 also carries the manager starting kickoffs with `start_session`, the `managers` sidebar section and `.scratch/` as the board's home.

## 0.2.0 — 2026-11-19

### Added
- **Skills as Claude Code skills**: `projio sync` writes every discovered skill into `.claude/skills/<name>/` with its description (a generated, read-only copy); `projio sync --check` reports drift and lints skill text; skills read env and run commands from the project; per-project `skills.disabled`; `projio skills usage` reports skill use from transcripts.
- **Package skills**: skills shipped by installed packages are discovered (the `projio.skills` entry point, e.g. biblio's).
- **Plugin marketplace**: the portable skills are shared as the `projio-workflow` plugin, versioned with projio, and exported as the light `projio-plugins` marketplace.
- **New ecosystem skills**: `project-manager` (core, with `incoming`, `round` and `procs` helpers and the manager board), `manager-setup` (any git project), `always-complete`, `literature-audit`, `projio-remotes`; `session-wrap` commits by path and reports to a running manager.
- **pixi as the environment runner** (`code.runner: pixi | conda | none`, auto-detected); conda kept as legacy compatibility.
- **CLI-first tasks**: `projio tasks`; no generated Makefile or Taskfile.
- **MCP**: `PROJIO_MCP_TOOLS` selects a reduced tool set per server entry; `pipeio_nb_open` (headless marimo server); existing projio/worklog server entries are pointed at the current runtime.
- **biblio group per the agent-interface spec**: `paper_lookup` and `biblio_job`; 34 biblio tools deprecated for one release (their descriptions name the replacement).
- `questio: {enabled: false}` turns off questio's plan pages; deliverables indexes are their own sync step.

### Changed
- Extras floors raised to the current releases: `indexio>=0.1.2`, `biblio-tools>=0.4.1`, `notio>=0.2.0`, `codio-tools>=0.2.0`, `pipeio>=0.2.0` (`projio[all]` installed packages months old).
- `fastmcp>=2.0,<4` (tested on fastmcp 3; fastmcp 4 is untested).

### Fixed
- `projio sync` refreshes the managed `.gitignore` block, and root-only entries are anchored.
- `projio sync`: multi-file pandoc defaults handled and render errors no longer abort sync; mkdocs `!include` only for sub-sites that exist.
- `corpus_list` counts without fetching all metadata.
- `note_create` / `note_update` accept YAML or dict fields (dates kept as strings) and return the note id.
- `pipeio_nb_publish` runs marimo in the project env.

## 0.1.3 — 2026-08-16

<!-- Detailed change descriptions live in docs/log/commit/ notes.
     CHANGELOG stays condensed — one line per feature, grouped by subsystem. -->

### Added

**pipeio** (notebooks + pipelines)
- Multi-backend notebook system — `NotebookBackend` protocol supporting jupytext percent-format and marimo reactive notebooks side by side, per-notebook `format:` field in `notebook.yml`
- `pipeio_nb_validate` tool — structural validation (percent: AST + import isolation; marimo: `marimo check`)
- `pipeio_nb_watch` tool — launch `marimo edit --watch` for live human oversight of agent edits
- `pipeio_nb_snapshot` tool — execute marimo notebook and return cell outputs (prints, errors, data) — agent's "eyes" for the `--watch` workflow
- `kind: interactive` notebook kind — marimo-only, persists by design, not promoted to scripts
- Marimo notebooks placed in workspace dir (not `.src/`) — the `.py` IS the human interface
- `pipeio_nb_create` accepts `format` param; `kind="interactive"` auto-selects marimo
- `pipeio_nb_extract` tool + `pipeio-nb-extract` skill — extract notebook results into flow-local reports with figures (renamed from `pipeio_nb_report` / `pipeio-report`; see [commit note](docs/log/commit/commit-arash-20260413-153016-000000.md))
- Size pre-flight in `pipeio_flow_report` — sums resolved target bytes before invoking `snakemake --report`, refuses above `max_embed_mb=200` with top-offenders list, warns above `warn_embed_mb=50`; motivated by pixecog `preprocess_motion` producing an 856 MB HTML from 640 MB of dense trajectory SVGs
- `pipeio_nb_move` tool — move a notebook between flows (files + registry update)
- `commit` note type in notio — structured change records with subsystem, commit_hash, files_created/modified fields
- `pipeio_flow_audit` tool + `pipeline-docs.md` spec — canonical flow documentation convention (`docs/index.md` section template, per-mod facet dirs, flow-root `CHANGELOG.md`), read-only compliance check, `ChangelogCollector` in `docs_collect`, richer `flow_new` scaffold. Pixecog migrated 0/8 → 7/8 compliant. See [commit note](docs/log/commit/commit-arash-20260413-175852-000000.md)
- **Delegation model** ([docs/explanation/delegation-model.md](docs/explanation/delegation-model.md)) — explicit engineering-vs-science boundary: pipeio flows own engineering (flows, DAGs, CHANGELOG), notio `result` notes own individual findings, `docs/deliverables/` owns narrative artifacts, questio binds them to research questions. Flow pages link to (not embed) results/deliverables. New frontmatter fields: `source_flow` (on results), `source_flows` (on deliverables). Updates to ecosystem.md, pipeio/overview.md, pipeline-docs.md, deliverables.md, notio result template.

**biblio** (literature)
- 5 new MCP tools: `biblio_openalex_resolve`, `biblio_status`, `biblio_crossref_resolve`, `biblio_graph_promote`, `biblio_extract`
- `questio_prior_art` tool — aggregates paper relevance per research question
- `questio_gap` now includes literature expectations from `biblio_extract`
- Reports index gains a GDoc column linking to a report's Google Doc when its front matter carries a `gdoc` field

**notio** (notes + platform)
- Remote platform integration — bidirectional bridge with GitHub/GitLab issues (`promote`, `capture`, `pull`, `remote-status`)
- Card feed styling for note indexes with collapsible closed groups
- `note_search` corpus fallback — searches `docs` (or all corpora) when the `notes` corpus is absent from the indexio config, reporting the substitution

**projio** (core)
- Multi-agent MCP config — `projio add codex` / `projio add copilot` alongside `projio add claude`
- `projio config help` — configuration reference
- `projio-setup` skill — guided ecosystem setup
- `projio sync --index` + `--install-hooks` — incremental index rebuild, post-commit hook
- Deliverables convention — `docs/deliverables/` with questio indexing
- ezlinks + bibtex mkdocs plugins auto-configured by sync
- Index staleness reported in `ecosystem_status()`
- `session-wrap` skill — end-of-session boundary: classify the tree, verify, commit coherent units, write a handoff note + kickoff prompt, update memory. `projio skill new --from-ecosystem <skill>` forks a bundled skill into `.projio/skills/` for per-project tailoring
- `projio-orient` skill — read-only workspace tour that surveys active subsystems and existing work, then suggests next actions (onboarding companion to `projio-setup`)
- Named render profiles — `.projio/render.yml` profiles (note/report/manuscript) each emit `pandoc-defaults-<name>.yaml`; `projio render run <file>` renders a doc with its front-matter-selected profile (`render: <profile>`)

### Changed
- **pipeio BREAKING rename** — `pipeio_report` → `pipeio_flow_report`, `pipeio_nb_report` → `pipeio_nb_extract`, skill `pipeio-report` → `pipeio-nb-extract`, slash-command `/pipeio-report` → `/pipeio-nb-extract`. Motivation: two tools that both sounded like "make a report" did completely different things (snakemake HTML report vs. notebook figure extraction). No backward-compat aliases — callers must update. See [commit note](docs/log/commit/commit-arash-20260413-153016-000000.md) for full change table.
- `agent_instructions()` routing table (`src/projio/init.py`) — added 8 previously missing pipeio tool rows (`pipeio_flow_new`, `_flow_fork`, `_flow_deregister`, `_mod_resolve`, `_nb_validate`, `_nb_watch`, `_nb_snapshot`, `_nb_extract`)
- Questio YAML sources moved from `docs/plan/` to `plan/` at project root
- Conda env rename: `rag` → `projio`
- Cross-platform compatibility — removed hardcoded lab paths, Windows support
- README and docs/index.md rewritten for PyPI publication
- Datalad-per-derivative relaxed to opt-in — a flow's `derivatives/<flow>/` is a plain directory by default; make it a subdataset only when the project versions derivatives and the outputs are stable (was framed as mandatory in the flow-create skill/guide, ontology spec, and handbook)
- `projio.mk` uses bare uv-tool commands — `PROJIO ?= projio`, `NOTIO ?= notio` (was `$(PYTHON) -m projio`); only MKDOCS still needs a configured Python

### Fixed
- `pipeio_nb_exec` output placed in `.src/` instead of workspace `.ipynb`
- Citekey diacritic mangling (Molle → molle, not mlle)
- Silent zero returns in biblio pipeline when `resolved.jsonl` missing
- 7 questio link/index/cycle/load fixes (docs_collect, result filenames, dangling refs, _find_roots)
- `projio.mk` env resolution fallback chain (`projio` ↔ `docs`)
- Render custom output paths — `_dump_yaml` creates parent dirs, so writing pandoc defaults to a path outside `.projio/render/` no longer errors

## 0.1.1 — 2026-04-08

### Added
- **Questio research orchestration layer** — hypothesis-to-evidence-to-manuscript reasoning for agentic research workflows
  - `questio_status` MCP tool — research state overview (questions, milestone completion %, evidence counts, blockers)
  - `questio_gap` MCP tool — per-question evidence gap analysis with dependency resolution and actionable recommendations
  - `questio_docs_collect` MCP tool — auto-generates `docs/plan/` pages (questions table, milestones tracker, mermaid roadmap, evidence index)
  - Data model convention: `docs/plan/questions.yml` (research question registry) and `docs/plan/milestones.yml` (dependency-aware milestone tracker)
  - 5 skills: `questio-session` (full research session), `questio-next` (prioritization), `questio-ground` (literature/code grounding), `questio-record` (structured evidence capture), `questio-report` (supervisor summary)
  - Design spec: `docs/specs/research-orchestration/design.md`
- **`result` note type in notio** — dedicated note type for structured evidence records with `question`, `milestone`, `metric`, `value`, `confidence` frontmatter fields; own directory (`docs/log/result/`), template, and index
- **Questio documentation** — explanation doc (`docs/explanation/questio.md`) and setup tutorial (`docs/tutorials/questio-setup.md`)
- **`biblio_compile` MCP tool** — merges intermediate `.bib` files (merged.bib + modkey.bib) into `.projio/render/compiled.bib`, the single bibliography consumed by pandoc and mkdocs-bibtex
- **`bib_sources` field in render.yml** — declares inputs to `biblio_compile` (default: `.projio/biblio/merged.bib`, `.projio/pipeio/modkey.bib`)
- **CSL files shipped as package data** — apa, chicago-author-date, elsevier-harvard, ieee, nature, vancouver; copied to `.projio/render/csl/` during `projio sync`
- **`bib/README.md` scaffold template** — auto-generated overview of bib layout, pipeline flow, and CLI/MCP commands
- **`projio sync` step 9: PandocCiter** — auto-syncs `.vscode/settings.json` PandocCiter.DefaultBibs and pandocCiter.csl from render.yml; only touches PandocCiter keys, leaves other settings untouched
- **`load_active_citekeys(cfg)`** — new canonical API for listing active citekeys, reads from merged bib instead of a separate citekeys.md file
- **mkdocs-monorepo-plugin** integration — pipeio owns `docs/pipelines/mkdocs.yml`, root mkdocs.yml includes via `!include`
- `projio sync` step 8: auto-configures monorepo plugin + `!include` in project mkdocs.yml when pipeio is present
- `mkdocs-monorepo-plugin>=1.1` added to `docs` and `dev` extras in pyproject.toml
- snakemake added to codio registry as external reference mirror

### Changed
- **Bib architecture: sources vs artifacts separation** — `bib/` now holds only human-managed source data (srcbib/, articles/, derivatives/); all generated artifacts moved under `.projio/`
  - `biblio_merge` output: `bib/main.bib` → `.projio/biblio/merged.bib`
  - Merge/quality/fetch logs: `bib/logs/` → `.projio/biblio/logs/`
  - Biblio config: `bib/config/biblio.yml` → `.projio/biblio/biblio.yml`
  - Compiled bibliography: `.projio/render/compiled.bib` (new)
  - Pandoc defaults: `bib/pandoc-defaults.yaml` → `.projio/render/pandoc-defaults.yaml`
  - CSL styles: `bib/csl/` → `.projio/render/csl/` (shipped by projio)
- **Citekeys derived from bib** — `citekeys.md` eliminated; active citekeys are now derived from the merged bibliography. `--all` flags on docling/grobid/batch commands read from the bib directly. `biblio citekeys` simplified to a flat list command.
- **Biblio scaffold restructured** — config files (biblio.yml, tag_vocab.yml) now scaffold to `.projio/biblio/`; `bib/.gitignore` only created when `bib/` is a git subdataset
- **Render defaults updated** — `bibliography` defaults to `.projio/render/compiled.bib`, `csl` to `.projio/render/csl/apa.csl`
- **Root .gitignore** — replaced stale `bib/logs/` entry with `.projio/biblio/logs/`
- `pipeio_mkdocs_nav_patch` simplified — writes sub-mkdocs.yml instead of fragile YAML patching of root mkdocs.yml
- CLAUDE.md updated with `pipeio_target_paths`, `pipeio_dag_export` SVG auto-write, tool count corrected to 51
- **projio gitignore block** expanded — covers all generated artefacts across subsystems: indexio jobs, codio mirrors, render outputs, pipeio state (`.snakemake/`, `*.ipynb`, `runs.json`), docs/pipelines nav, biblio logs, filters

### Removed
- **`citekeys.md`** — scaffold template, config key, and all `load_citekeys_md` / `add_citekeys_md` / `remove_citekeys_md` usage in batch/site/grobid/ingest/graph/pool modules replaced by `load_active_citekeys(cfg)`
- `bib/Makefile` scaffold template (superseded by biblio MCP tools)
- `bib/config/rag.yaml` scaffold template (belongs to indexio)
