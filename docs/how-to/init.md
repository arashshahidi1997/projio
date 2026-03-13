# Initialize a Workspace

## Generic project

```bash
projio init .
```

Creates `.projio/config.yml`, `.projio/projio.mk`, `Makefile`, a managed `projio` section in `.gitignore`, and `docs/index.md`.

If no site framework is already present, `projio` defaults to MkDocs and also writes `mkdocs.yml`. If the repo already looks like a Sphinx or Vite/React frontend project, `projio` records that framework in `.projio/config.yml` instead of forcing MkDocs files into the repo.

## Tool project (Python package)

```bash
projio init . --kind tool
```

Additionally creates `pyproject.toml`, `src/<package>/__init__.py`, and `tests/`.

## Study project

```bash
projio init . --kind study
```

Lightweight scaffold with biblio and notio disabled by default.

## Overwrite existing files

```bash
projio init . --force
```

## Add VS Code site excludes

```bash
projio init . --vscode
```

Writes `.vscode/settings.json` with file, search, and watcher excludes for `site/`.

## Add a GitHub Pages workflow

```bash
projio init . --github-pages
```

Writes `.github/workflows/docs.yml` using the detected site framework:

- MkDocs uploads `site/`
- Sphinx uploads `docs/_build/html/`
- Vite uploads `site/`

## User-level defaults

Scaffold `~/.config/projio/config.yml` for cross-project defaults:

```bash
projio config init-user
```

User config is merged with project config, with project values taking precedence.
