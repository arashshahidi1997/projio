# Quickstart

This tutorial shows the smallest practical `projio` workflow for a fresh project.

## Install

```bash
pip install projio
```

To install with all ecosystem packages:

```bash
pip install "projio[all]"
```

## Initialize a workspace

From your project root:

```bash
projio init .
```

This creates:

- `.projio/config.yml`
- `Makefile`
- `mkdocs.yml`
- `docs/index.md`

## Choose a project kind

For a Python package project:

```bash
projio init . --kind tool
```

This additionally creates a `pyproject.toml`, `src/<package>/`, and `tests/` scaffold.

For a lightweight study project:

```bash
projio init . --kind study
```

## Check project status

```bash
projio status -C .
```

## Set up user defaults

Scaffold a user-level config file for cross-project defaults:

```bash
projio config init-user
```

This writes `~/.config/projio/config.yml`.

## Start the MCP server

```bash
projio mcp -C .
```

This starts a FastMCP stdio server exposing all enabled tools for the current project.

## Build the docs site

```bash
projio site build -C .
projio site serve -C .
```

To enable the `indexio` chatbot in a MkDocs site preview, add this to `.projio/config.yml`:

```yaml
site:
  chatbot:
    enabled: true
```
