# Initialize a Workspace

## Generic project

```bash
projio init .
```

Creates `.projio/config.yml`, `Makefile`, `mkdocs.yml`, and `docs/index.md`.

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

## User-level defaults

Scaffold `~/.config/projio/config.yml` for cross-project defaults:

```bash
projio config init-user
```

User config is merged with project config, with project values taking precedence.
