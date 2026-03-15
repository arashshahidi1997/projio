# Workspace Layout

Specification of the `.projio/` workspace directory structure.

## Directory tree

```
.projio/
├── projio.yml              # workspace identity
├── packages.yml            # component registry
├── config.yml              # project configuration
├── projio.mk               # shared Makefile targets
├── state/                  # persistent runtime state
│   └── servers.json        # running doc-server metadata
├── cache/                  # transient, rebuildable artifacts
│   └── index/              # embedding indexes (chroma, etc.)
├── site/                   # generated site artifacts
│   └── indexio_chat_hook.py
├── biblio/                 # biblio component state
├── notio/                  # notio component state
├── codio/                  # codio component state
│   ├── catalog.yml
│   └── profiles.yml
└── indexio/                # indexio component state
    └── config.yaml
```

## File and directory purposes

### `projio.yml`

Workspace identity and metadata. Created by `projio init`.

```yaml
workspace:
  name: my-project
  kind: generic          # generic | tool | study
  created: 2026-03-15
```

This file marks the directory as a projio workspace. Its presence is the canonical signal for workspace detection.

### `packages.yml`

Component registry. Tracks which packages are activated and where their state lives. See [Package Registry](#package-registry) below.

### `config.yml`

Project configuration. Merges with the user config at `~/.config/projio/config.yml` (project wins). Contains settings for projio and each subsystem.

This is the existing configuration file — unchanged from the current design. See [Configuration](configuration.md) for the full schema.

### `projio.mk`

Shared Makefile targets (`save`, `push`, `projio-init`, `site-build`, etc.). Always overwritten on `projio init` to stay current.

### `state/`

Persistent runtime state that is not configuration. Files here track processes and sessions.

| File | Purpose |
|------|---------|
| `servers.json` | Metadata for running doc servers (PID, port, framework) |

**Git policy**: should be in `.gitignore` — state is machine-local.

### `cache/`

Transient artifacts that can be regenerated. Embedding indexes, compiled assets, and temporary build outputs live here.

| Subdirectory | Purpose |
|--------------|---------|
| `index/` | ChromaDB or other embedding store directories |

**Git policy**: should be in `.gitignore` — cache is rebuildable.

### `site/`

Generated site artifacts. Currently holds the MkDocs chat hook script when chatbot integration is enabled.

**Git policy**: should be in `.gitignore`.

### `<package>/`

Component state directories. Each activated package gets a namespaced directory. The package owns the internal structure — projio only creates the directory and records the path in `packages.yml`.

Examples:

| Directory | Contents |
|-----------|----------|
| `biblio/` | Bibliography config, citekey caches |
| `notio/` | Templates, note indexes |
| `codio/` | `catalog.yml`, `profiles.yml`, curated notes |
| `indexio/` | `config.yaml`, corpus metadata |

## Package registry

The `packages.yml` file:

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

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `packages.<name>.enabled` | bool | Whether the component is active |
| `packages.<name>.path` | string | Relative path (from repo root) to the component directory. Present only when `enabled: true`. |

### Discovery rules

1. `projio add <package>` sets `enabled: true` and `path: .projio/<package>`
2. `projio remove <package>` sets `enabled: false` and removes `path`
3. `projio list` reads the registry and checks which packages are actually installed (importable)
4. The MCP server reads the registry at startup to decide which tool modules to load

### Package reads

A package determines its working directory by:

1. Checking for `.projio/packages.yml` in the project root
2. If present, reading its own entry and using the `path` value
3. If absent or the entry is missing, falling back to standalone detection

## `.gitignore` recommendations

Add to the project `.gitignore`:

```gitignore
# projio transient state
.projio/state/
.projio/cache/
.projio/site/
.projio/servers.json      # legacy location
```

The following should be tracked in git:

```
.projio/projio.yml        # workspace identity
.projio/packages.yml      # component registry
.projio/config.yml        # project configuration
.projio/<package>/        # package state (package decides what to track)
```

## Migration from current layout

The current layout stores some state at paths that differ from this specification:

| Current | Target |
|---------|--------|
| `.projio/servers.json` | `.projio/state/servers.json` |
| `.projio/index/` (chroma) | `.projio/cache/index/` |
| `.projio/site/` | `.projio/site/` (unchanged) |

A `projio migrate` command can handle relocation. Until then, both paths should be checked.
