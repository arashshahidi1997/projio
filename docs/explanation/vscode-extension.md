# VS Code Extension

## Overview

Projio includes a local VS Code extension that provides IDE integration over the core projio system. The extension lives at `editors/vscode/` in the repository.

This is a **thin client** — it does not replicate projio logic in TypeScript. Core functionality (workspace management, indexing, bibliography, notes, code intelligence) remains in the Python package. The extension provides a UI layer and will eventually connect to the projio MCP server for richer interactions.

## Location in the repo

```
editors/
  vscode/
    package.json        # Extension manifest
    tsconfig.json       # TypeScript config
    src/
      extension.ts      # Activation, command registration
      workspace.ts      # Workspace detection heuristics
    .vscode/
      launch.json       # F5 launch config
      tasks.json        # Build tasks
```

The `editors/` top-level directory was chosen to keep the extension cleanly separated from the Python source (`src/`), ecosystem packages (`packages/`), and documentation (`docs/`). This convention also leaves room for other editor integrations in the future.

## Install dependencies

```bash
cd editors/vscode
npm install
```

## Build

```bash
npm run compile      # One-shot build
npm run watch        # Incremental rebuild on save
```

## Run locally

1. Open the `editors/vscode/` folder in VS Code.
2. Press **F5** (or Run → Start Debugging).
3. A new VS Code window opens as the Extension Development Host.
4. Open any folder in that window and use the Command Palette to run Projio commands.

## Current MVP commands

| Command | What it does |
|---------|-------------|
| **Projio: Hello** | Shows a greeting message. Smoke test for activation. |
| **Projio: Detect Workspace** | Checks whether the open folder contains `.projio/config.yml` and reports which subsystems (indexio, notio, codio, biblio) are present. |
| **Projio: Show Status** | Opens a document with workspace info (root path, config location, active subsystems). |

## Workspace detection

The extension detects a projio workspace by looking for `.projio/config.yml` in the workspace folder — the same marker the CLI uses. It also scans for known subsystem directories inside `.projio/` to report which components are active.

This matches the convention in `src/projio/config.py` where `get_project_config_path()` resolves to `<root>/.projio/config.yml`.

## Why a thin extension?

Projio's core value is in its Python ecosystem: semantic search (indexio), bibliography management (biblio), structured notes (notio), and code intelligence (codio). These are complex systems with their own dependencies (ChromaDB, embedding models, etc.) that don't belong in a TypeScript extension.

The extension should only handle:

- **UI concerns** — tree views, status bar items, webview panels
- **Process management** — launching/connecting to the MCP server
- **Workspace detection** — lightweight file-based heuristics
- **Command dispatch** — forwarding user actions to the core system

## What is intentionally out of scope (for now)

- Marketplace publishing (no `.vsixmanifest`, no PAT setup)
- Bundling with esbuild/webpack (not needed for local dev)
- Sidebar tree views
- MCP server connection
- Rich workspace inspection beyond file presence checks
- Any duplication of projio core logic

## Next steps

Likely directions for the extension:

- **Tree view / sidebar** — show workspace structure, subsystem status, recent notes
- **MCP integration** — launch or connect to the projio MCP server, forward tool calls
- **Richer workspace inspection** — parse `config.yml`, show project kind and enabled features
- **Workstream views** — surface corpus search results, bibliography entries, note timelines
- **Source attachment UI** — attach papers, code libraries, or data sources to the workspace
- **Init / attach / index commands** — run `projio init`, `projio attach`, corpus indexing from the palette
- **Status bar item** — persistent indicator showing projio workspace state
- **CodeLens / diagnostics** — inline markers for citekeys, library references, note links
