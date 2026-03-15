# Workspace Architecture

This document describes the workspace layout strategy for the projio ecosystem — how projio manages a shared workspace root while preserving package autonomy.

## Motivation

Projio orchestrates four subsystems (biblio, notio, codio, indexio), each capable of running standalone. Without coordination, each package creates its own hidden directory at the repository root:

```
repo/
├── .projio/
├── .biblio/          # hypothetical standalone
├── .notio/
├── .codio/
├── .indexio/
```

This causes hidden-folder sprawl, fragments the user's mental model, and makes cross-package integration harder. The workspace architecture addresses this by introducing a single shared root.

## Core concepts

### Package

A Python distribution or CLI tool that provides domain-specific functionality:

- **biblio** — bibliography management
- **notio** — structured notes
- **codio** — code intelligence
- **indexio** — corpus indexing and search

A package owns its schemas, commands, data structures, and lifecycle. Projio does not manage package internals.

### Workspace component

A package's instantiated project state within a projio-managed workspace. When biblio is activated in a project, its workspace component lives at `.projio/biblio/`. The component is an instance of the package, scoped to a particular project.

### Workspace root

The `.projio/` directory at the repository root. Projio owns this directory and its top-level structure. Packages write their project-local state into namespaced subdirectories within it.

## Target layout

```
repo/
└── .projio/
    ├── projio.yml          # workspace metadata
    ├── packages.yml        # component registry
    ├── config.yml          # project configuration (existing)
    ├── projio.mk           # shared Makefile targets (existing)
    ├── state/              # projio-managed state (servers.json, etc.)
    ├── cache/              # transient artifacts (indexes, embeddings)
    ├── biblio/             # biblio component state
    ├── notio/              # notio component state
    ├── codio/              # codio component state
    └── indexio/            # indexio component state
```

## Workspace containment

Projio owns the workspace topology. All project-local state lives under `.projio/`. This means:

- One hidden directory instead of many
- A single `.gitignore` entry covers transient state
- Cross-package tools can discover each other through the registry
- Users see a unified workspace, not separate tools

## Modular activation

`projio init` creates the base workspace — it does **not** initialize every package. Components are added explicitly:

```bash
projio init                    # creates .projio/ with base files
projio add biblio              # activates biblio component
projio add notio               # activates notio component
```

This reflects an intentional design: users install only what they need. The `packages.yml` registry tracks which components are active.

### Init profiles

For convenience, named profiles bundle common component sets:

```bash
projio init --profile research    # notio + biblio + indexio
projio init --profile full        # all four packages
```

The default `projio init` (no profile) creates only the base workspace.

## Standalone vs managed mode

Packages must support two operational modes:

### Standalone mode

The package manages its own root directory. Used when the package is installed without projio.

```
repo/
├── .codio/
│   ├── catalog.yml
│   └── profiles.yml
```

The package detects its root by looking for its own markers (e.g., `.codio/catalog.yml`).

### Managed mode

The package stores state under `.projio/<package>/`. Used when the package is activated as a projio workspace component.

```
repo/
└── .projio/
    └── codio/
        ├── catalog.yml
        └── profiles.yml
```

The package detects managed mode by checking for `.projio/packages.yml` and reading its configured path from the registry.

### Resolution order

When a package resolves its working directory:

1. **Explicit argument** — if the user passes `--root` or a path, use it
2. **Managed mode** — if `.projio/packages.yml` exists and lists the package with a path, use that path
3. **Standalone mode** — if the package's own marker exists (e.g., `.codio/`), use it
4. **Fallback** — `.git` or `pyproject.toml` as generic project root

## Package registration

The `packages.yml` file tracks activated components:

```yaml
packages:
  biblio:
    enabled: true
    path: .projio/biblio
  notio:
    enabled: true
    path: .projio/notio
  codio:
    enabled: false
  indexio:
    enabled: true
    path: .projio/indexio
```

Projio reads this file to:

- List active components (`projio list`)
- Route MCP tool registration to installed packages
- Provide cross-package discovery (e.g., codio can find the indexio index path)

Packages read this file to resolve their working directory in managed mode.

## Design principles

### Projio manages topology, not logic

Projio controls where packages store state. It does not manage what they store or how they process it. Schemas, commands, and data formats remain package-owned.

### Graceful degradation

Missing packages are not errors. If biblio is not installed, its MCP tools are not registered and `projio list` shows it as unavailable. The workspace continues to function.

### No mandatory coupling

A package should never import projio. The only shared contract is the filesystem layout and the `packages.yml` schema. Packages read a path and operate on it — they do not need to know about projio internals.

### Migration path

Existing projects using standalone package directories (`.codio/`, `.indexio/`, etc.) continue to work. The managed layout is opt-in via `projio add`. A future `projio migrate` command can move standalone state into the managed workspace.
