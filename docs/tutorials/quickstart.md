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
- `.projio/projio.mk`
- `Makefile`
- `.gitignore` with a managed `projio` section
- `docs/index.md`

If no site stack is detected, `projio` also writes `mkdocs.yml`.

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

To print clickable repo and Pages URLs from your current git remotes:

```bash
projio url -C .
make url
```

## Set up user defaults

Scaffold a user-level config file for cross-project defaults:

```bash
projio config init-user
```

This writes `~/.config/projio/config.yml`.

## Optional VS Code setup

```bash
projio init . --vscode
```

This adds `.vscode/settings.json` excludes for `site/` so ripgrep-backed search and file watching do not degrade after a site build.

## Optional GitHub Pages setup

```bash
projio init . --github-pages
```

This adds `.github/workflows/docs.yml` for GitHub Pages deployment of the detected site framework.

## Start the MCP server

```bash
projio mcp -C .
```

This starts a FastMCP stdio server exposing all enabled tools for the current project.

## Set up agent permissions

```bash
projio add claude
```

This scaffolds `.claude/settings.json` with pre-approved permissions for all projio MCP tools (`mcp__projio__*`). The server is scoped to your project via `PROJIO_ROOT`, so writes stay within the repo. See [Agent Safety & Permissions](../explanation/agent-safety.md) for granular options.

## Build the docs site

```bash
projio site build -C .
projio site serve -C .
```

`projio site` explicitly supports MkDocs, Sphinx, and Vite-based React frontends.

To enable the `indexio` chatbot in a MkDocs site preview, add this to `.projio/config.yml`:

```yaml
site:
  chatbot:
    enabled: true
```
