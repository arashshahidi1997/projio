# pipeio: Notebook Lifecycle Specification

## Purpose

Research pipeline flows produce notebooks that serve two roles with distinct lifecycles:

1. **Exploratory** (`kind: investigate` or `explore`) — prototype analysis, test parameters, validate approaches before absorbing into mod scripts. End state: `status: archived` once code is promoted to Snakemake rules.
2. **Demo** (`kind: demo` or `validate`) — showcase mod outputs in narrative form, generate QC reports for publication. End state: `status: promoted` with `publish_html: true`, published to the project site.

Both types are linked to a flow mod via the `mod` field in `notebook.yml`.

pipeio manages the notebook lifecycle: scan, pair, sync (bidirectional), execute, audit, publish. `nb_audit` detects lifecycle mismatches (e.g., exploratory notebook still active after mod has scripts, demo notebook not set to publish).

## Notebook Directory Convention

Notebooks use a split layout that separates human-facing files from agent/build artifacts:

```
code/pipelines/preprocess/ieeg/
└── notebooks/
    ├── notebook.yml                              # lifecycle config
    ├── investigate_noise.ipynb                    # human-facing (Jupyter Lab)
    ├── explore_params.ipynb
    ├── .src/                                     # agent territory
    │   ├── investigate_noise.py                  # source of truth (percent-format)
    │   └── explore_params.py
    └── .myst/                                    # build artifacts (generated)
        ├── investigate_noise.md
        └── explore_params.md
```

- **`notebooks/`** — human territory: `.ipynb` files visible in Jupyter Lab
- **`.src/`** — agent territory: `.py` percent-format files (source of truth)
- **`.myst/`** — generated MyST markdown for docs pipeline

Legacy layouts (flat `notebooks/name.py` or subdirectory `notebooks/name/name.py`) are still supported. Use `pipeio nb migrate --yes` to convert to the `.src/` layout.

### Source of Truth

The `.py` file (percent format) is always the source of truth. The `.ipynb` and `.md` files are generated/synced artifacts.

### Notebook Header Convention

Notebook `.py` files carry structured docstring metadata:

```python
# ---
# Title: investigate_noise_characterization_demo.py
# Status: INVESTIGATION
# Objective: Prototype a compact cross-session noise-characterization demo
# Focus: PSD-first spectral characterization, spatial structure analysis
# Guardrails: Read-only, in-memory exploration only, flow-aware paths
# ---
```

## notebook.yml Schema

```yaml
kernel: cogpy                 # flow-level default kernel (Jupyter kernelspec name)

publish:
  docs_dir: /abs/path/to/docs/reports/.../notebooks   # where to publish
  prefix: nb-                                           # filename prefix for published copies

entries:
  - path: notebooks/investigate_noise_characterization_demo/investigate_noise_characterization_demo.py
    kind: investigate         # investigate | explore | demo | validate
    description: "Prototype noise characterization demo"
    status: active            # draft | active | stale | promoted | archived
    kernel: neuropy-env       # per-notebook override (takes precedence over flow kernel)
    pair_ipynb: true          # create .ipynb and pair with jupytext
    pair_myst: true           # create .md (MyST) and pair
    publish_myst: true        # copy .md to docs_dir after execution
    publish_html: false       # render HTML and copy to docs_dir
  - path: notebooks/investigate_noise_tfspace_demo/investigate_noise_tfspace_demo.py
    kind: investigate
    status: active
    pair_ipynb: true          # inherits kernel: cogpy from flow level
    pair_myst: true
    publish_myst: true
```

### Kernel Resolution

Kernels are resolved with entry-level taking precedence over flow-level:

```
entry.kernel > config.kernel > (no override)
```

When set, the kernel name is:
- Embedded in `.ipynb` metadata via `jupytext --set-kernel` during sync
- Passed to papermill via `-k` during execution
- Shown in `nb_status` and `nb_lab` manifest output

### NotebookConfig Pydantic Model

```python
class NotebookEntry(BaseModel):
    path: str
    kind: str = ""                # investigate | explore | demo | validate
    description: str = ""         # human-readable description
    status: str = "active"        # draft | active | stale | promoted | archived
    kernel: str = ""              # Jupyter kernelspec name (overrides flow default)
    pair_ipynb: bool = False
    pair_myst: bool = False
    publish_myst: bool = False
    publish_html: bool = False

class PublishConfig(BaseModel):
    format: str = "html"          # output format (html, markdown)
    docs_dir: str = ""
    prefix: str = "nb-"

class NotebookConfig(BaseModel):
    kernel: str = ""              # flow-level default kernel
    publish: PublishConfig = PublishConfig()
    entries: list[NotebookEntry] = []
```

## Lifecycle Stages

### 1. Pair (`pipeio nb pair`)

Create paired formats according to `notebook.yml`:

- If `pair_ipynb: true` and `.ipynb` doesn't exist → create it with `jupytext --to notebook`
- Set pairing formats with `jupytext --set-formats ipynb,py`
- If `pair_myst: true` → additionally set formats to `ipynb,py,md:myst`

**Idempotent**: skips if pairing already exists.

### 2. Sync (`pipeio nb sync`)

Synchronize content between paired formats using "newer wins" logic:

- Compare modification times of `.py`, `.ipynb`, `.md`
- Sync newer → older with `jupytext --sync`
- Directional: `.py` → `.ipynb` preserves ipynb outputs; `.ipynb` → `.py` strips outputs

**Safety**: never overwrites newer content with older. Dry-run mode (`--dry`) shows what would happen.

### 3. Execute (`pipeio nb exec`)

Execute all registered `.ipynb` notebooks in place:

- `jupyter nbconvert --to notebook --execute --inplace <path>`
- Respects timeout settings (configurable, default 600s)
- Reports success/failure per notebook
- Can target a single entry: `pipeio nb exec --entry <name>`

### 4. Publish (`pipeio nb publish`)

Copy executed notebooks to the documentation directory:

- If `publish_myst: true` → copy `.md` to `docs_dir/` with prefix
- If `publish_html: true` → render `.ipynb` to HTML, copy to `docs_dir/`
- Can also publish `.ipynb` directly for embedding

**Path construction**: `{docs_dir}/{prefix}{notebook_name}.{ext}`

### 5. Status (`pipeio nb status`)

Show sync and publication state:

```
$ pipeio nb status
Flow: preprocess/ieeg (2 entries)

  investigate_noise_characterization_demo
    .py   2026-03-20 14:30  (source)
    .ipynb 2026-03-20 14:28  ⚠ out of sync (py is newer)
    .md   2026-03-20 14:28  ⚠ out of sync
    published: no

  investigate_noise_tfspace_demo
    .py   2026-03-19 10:00  (source)
    .ipynb 2026-03-19 10:00  ✓ synced
    .md   2026-03-19 10:00  ✓ synced
    published: yes (2026-03-19)
```

## Full Pipeline Shortcut

`pipeio nb publish` (without sub-stage) runs the full pipeline:

```
pair → sync → exec → publish
```

Equivalent to the pixecog Makefile target `nb-publish`.

## CLI Commands

```
pipeio nb pair     [--force]
pipeio nb sync     [--direction py2nb|nb2py] [--force]
pipeio nb diff
pipeio nb exec
pipeio nb publish
pipeio nb status
pipeio nb lab      [--pipe PIPE] [--flow FLOW] [--sync] [--refresh]
pipeio nb scan     [--register]
pipeio nb migrate  [--yes]
pipeio nb new      --mode explore|demo [--flow PIPE/FLOW] NAME
```

## `pipeio nb new`

Scaffold a new notebook:

- `--mode explore` — minimal bootstrap, no publish defaults, structured docstring header
- `--mode demo` — publish-ready, wired to pipeline outputs, auto-registered in `notebook.yml`

Creates `notebooks/<name>/<name>.py` with the standard header and PipelineContext bootstrap code.

## Reference: pixecog Makefile Targets

The current implementation these specs replace:

| Make target | pipeio equivalent | Lines of bash |
|-------------|-------------------|---------------|
| `nb-list` | `pipeio nb status` | 3 |
| `nb-pair` | `pipeio nb pair` | 45 |
| `nb-status` | `pipeio nb sync --dry` | 30 |
| `nb-sync` | `pipeio nb sync` | 50 |
| `nb-exec-all` | `pipeio nb exec` | 25 |
| `nb-publish-myst` | `pipeio nb publish --format myst` | 40 |
| `nb-publish-html` | `pipeio nb publish --format html` | 35 |
| `nb-publish-ipynb` | `pipeio nb publish --format ipynb` | 30 |
| `nb-publish` | `pipeio nb publish` | 15 (orchestration) |

Total: ~350 lines of bash → Python CLI with proper error handling, progress reporting, and dry-run support.
