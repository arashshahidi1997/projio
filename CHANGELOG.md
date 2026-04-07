# Changelog

## Unreleased

### Added
- **mkdocs-monorepo-plugin** integration — pipeio owns `docs/pipelines/mkdocs.yml`, root mkdocs.yml includes via `!include`
- `projio sync` step 8: auto-configures monorepo plugin + `!include` in project mkdocs.yml when pipeio is present
- `mkdocs-monorepo-plugin>=1.1` added to `docs` and `dev` extras in pyproject.toml
- snakemake added to codio registry as external reference mirror

### Changed
- `pipeio_mkdocs_nav_patch` simplified — writes sub-mkdocs.yml instead of fragile YAML patching of root mkdocs.yml
- CLAUDE.md updated with `pipeio_target_paths`, `pipeio_dag_export` SVG auto-write, tool count corrected to 51
- **projio gitignore block** expanded — covers all generated artefacts across subsystems: indexio jobs, codio mirrors, render outputs, pipeio state (`.snakemake/`, `*.ipynb`, `runs.json`), docs/pipelines nav, biblio logs, filters
