# Shared Code Library with Codio + Indexio

This tutorial walks through setting up a shared, cloned mirror of external reference repositories that multiple projects can browse and query via RAG. By the end you will have a searchable code library indexed for semantic search.

## Prerequisites

- Full ecosystem installed (`pip install "projio[all]"`)
- MCP server connected (see [Ecosystem Overview](ecosystem-overview.md))
- A shared storage location accessible to your projects (e.g. `/storage/share/codelib/`)

## Why

- Reference implementations live in dozens of external repos. Cloning them into a shared location means any project can look up algorithms, patterns, and APIs without leaving the editor.
- Indexio's RAG turns the clones into a searchable knowledge base — ask "how does neurodsp implement burst detection?" and get the actual source code.
- Shared storage avoids duplicating clones across projects.

## Architecture

```
/storage/share/codelib/              # shared clone directory
  neurodsp-tools--neurodsp/          # shallow clones, named <owner>--<repo>
  fooof-tools--fooof/
  ...

project-a/.projio/
  config.yml                         # mirrors_dir: /storage/share/codelib
  codio/
    catalog.yml                      # library metadata (name, URL, license)
    profiles.yml                     # triage (tier, decision, capabilities)
    repos.yml                        # clone state (storage: managed, local_path)
  indexio/
    config.yaml                      # codelib source glob
    index/                           # project-local vector index
```

Each project has its own catalog, profiles, and index. The clones on disk are shared.

## Step 1: Configure the shared clone directory

In `.projio/config.yml`:

```yaml
codio:
  mirrors_dir: /storage/share/codelib
```

Create the directory if it doesn't exist:

```bash
mkdir -p /storage/share/codelib
```

## Step 2: Add repos to the catalog and clone

Via MCP:

```
codio_add_urls(
  urls=["https://github.com/org/repo", ...],
  clone=True,
  shallow=True
)
```

This does three things per URL:

- Adds (or updates) the catalog entry with metadata fetched from GitHub/GitLab
- Shallow-clones the repo to `/storage/share/codelib/<owner>--<repo>`
- Updates `repos.yml` with `storage: managed` and the `local_path`

!!! note "Clone behavior"
    - `shallow=True` uses `git clone --depth 1` — saves disk for large repos.
    - The clone uses the remote's default branch (no `-b` flag), so repos using `master` or `main` both work.
    - GitLab URLs work too — hosting is auto-detected.
    - If a repo URL has changed (e.g., `nbara/meegkit` renamed to `nbara/python-meegkit`), add the new URL and remove the stale catalog entry manually.

## Step 3: Triage the catalog

Edit `profiles.yml` to set priority, runtime_import, and decision_default per library:

| Tier | Priority | Clone? | Use case |
|------|----------|--------|----------|
| 1 | `tier1` | Yes | Core domain libs — borrow algorithms, wrap APIs |
| 2 | `tier2` | No | Large frameworks — use via pip, don't clone |
| 3 | `tier3` | No | Reference only — MATLAB, notebooks, cookbooks |

Key profile fields:

- `runtime_import`: `pip_only` (installed dep), `reference_only` (code reference, not imported)
- `decision_default`: `wrap` (thin adapter), `new` (rewrite for your data model), `direct` (use as-is)

## Step 4: Add the codelib source to indexio

In `.projio/indexio/config.yaml`, add:

```yaml
sources:
  - id: "codelib"
    corpus: "codelib"
    glob: "/storage/share/codelib/**/*.py"
```

Absolute globs are supported — indexio resolves them from the filesystem root.

## Step 5: Build the index

Via MCP:

```
indexio_build(sources=["codelib"])
```

Partial rebuild — only indexes the codelib source, leaves other sources untouched.

## Step 6: Query

```
rag_query(query="multitaper spectral estimation", corpus="codelib", k=5)
```

Returns ranked code chunks from the indexed repos.

## Adding the library to another project

For a second project that wants to use the same shared library:

### Point mirrors_dir at the shared location

In the new project's `.projio/config.yml`:

```yaml
codio:
  mirrors_dir: /storage/share/codelib
```

### Copy or create catalog + profiles

Three options, from least to most shared:

**Option A — Independent catalog.** Create the project's own `catalog.yml` and `profiles.yml`. Run `codio_add_urls` with the same URLs (use `clone=True` — it's idempotent, skips cloning if the directory already exists).

**Option B — Shared catalog via absolute path.** Point at a central catalog:

```yaml
codio:
  mirrors_dir: /storage/share/codelib
  catalog_path: /storage/share/codelib/catalog.yml
  profiles_path: /storage/share/codelib/profiles.yml
```

**Option C — Symlink.** Symlink `.projio/codio/` to a shared directory. Simple but couples the projects tightly.

!!! tip "Recommendation"
    **Option A** for most cases. Each project should own its triage decisions (tier/priority may differ by project). The clones themselves are shared; the metadata is cheap to duplicate.

### Add the indexio source and build

Same as the first project — add the codelib source glob to `.projio/indexio/config.yaml` and run `indexio_build(sources=["codelib"])`. Each project maintains its own vector index but reads from the same code on disk.

## Maintenance

**Adding repos:** `codio_add_urls(urls=[...], clone=True, shallow=True)` from any project. The clone lands in the shared directory; other projects pick it up on their next index rebuild.

**Updating clones:** Currently manual — `git -C /storage/share/codelib/<owner>--<repo> pull`. A `codio_sync` tool would be a natural addition.

**Removing repos:** Delete the clone directory, remove the entry from `catalog.yml`, `profiles.yml`, and `repos.yml`, then rebuild the index.

**Re-indexing after changes:** `indexio_build(sources=["codelib"])`.

## Gotchas

- **Absolute paths in config:** `mirrors_dir`, `catalog_path`, etc. must be handled with the `_resolve()` helper in `codio/config.py` — absolute paths should not be prepended with `project_root`.
- **Repo renames:** GitHub doesn't always redirect clone URLs for renamed repos. Verify URLs before adding. The error surfaces as `could not read Username for 'https://github.com'`.
- **GitLab repos:** Work fine — pass the GitLab URL directly. Hosting is auto-detected but GitHub metadata fetching is skipped for non-GitHub URLs.
- **Branch detection:** Clones use the remote's default branch. The actual branch is detected post-clone via `git symbolic-ref` and recorded in `repos.yml`.
- **indexio absolute globs:** Supported — paths outside the project root are stored as absolute in chunk metadata.
- **MCP server caching:** After reinstalling codio, restart the MCP server (VS Code: reload window or `/mcp`).

## What's next

- [Agent Orchestration](agent-orchestration.md) — multi-tool session combining all ecosystem components
- [Grand Routine](grand-routine.md) — the full idea-to-deployment research workflow
