# Changelog

## Unreleased

<!-- Detailed change descriptions live in docs/log/commit/ notes.
     CHANGELOG stays condensed — one line per feature, grouped by subsystem. -->

### Added

**pipeio** (notebooks + pipelines)
- `pipeio_nb_report` tool + `/report` skill — extract notebook results into flow-local reports with figures
- `pipeio_nb_move` tool — move a notebook between flows (files + registry update)
- `commit` note type in notio — structured change records with subsystem, commit_hash, files_created/modified fields

**biblio** (literature)
- 5 new MCP tools: `biblio_openalex_resolve`, `biblio_status`, `biblio_crossref_resolve`, `biblio_graph_promote`, `biblio_extract`
- `questio_prior_art` tool — aggregates paper relevance per research question
- `questio_gap` now includes literature expectations from `biblio_extract`

**notio** (notes + platform)
- Remote platform integration — bidirectional bridge with GitHub/GitLab issues (`promote`, `capture`, `pull`, `remote-status`)
- Card feed styling for note indexes with collapsible closed groups

**projio** (core)
- Multi-agent MCP config — `projio add codex` / `projio add copilot` alongside `projio add claude`
- `projio config help` — configuration reference
- `projio-setup` skill — guided ecosystem setup
- `projio sync --index` + `--install-hooks` — incremental index rebuild, post-commit hook
- Deliverables convention — `docs/deliverables/` with questio indexing
- ezlinks + bibtex mkdocs plugins auto-configured by sync
- Index staleness reported in `ecosystem_status()`

### Changed
- Questio YAML sources moved from `docs/plan/` to `plan/` at project root
- Conda env rename: `rag` → `projio`
- Cross-platform compatibility — removed hardcoded lab paths, Windows support
- README and docs/index.md rewritten for PyPI publication

### Fixed
- `pipeio_nb_exec` output placed in `.src/` instead of workspace `.ipynb`
- Citekey diacritic mangling (Molle → molle, not mlle)
- Silent zero returns in biblio pipeline when `resolved.jsonl` missing
- 7 questio link/index/cycle/load fixes (docs_collect, result filenames, dangling refs, _find_roots)
- `projio.mk` env resolution fallback chain (`projio` ↔ `docs`)

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
