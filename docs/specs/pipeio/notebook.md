# pipeio: Notebook Lifecycle Specification

## Purpose

Research pipeline flows produce notebooks that serve two roles with distinct lifecycles:

1. **Exploratory** (`kind: investigate` or `explore`) — prototype analysis, test parameters, validate approaches before absorbing into mod scripts. End state: `status: archived` once code is promoted to Snakemake rules.
2. **Demo** (`kind: demo` or `validate`) — showcase mod outputs in narrative form, generate QC reports for publication. End state: `status: promoted` with `publish_html: true`, published to the project site.
3. **Interactive** (`kind: interactive`) — marimo-backed live exploration with reactive parameter tuning. Not intended for batch execution or promotion. Persists by design.

Both exploratory and demo types are linked to a flow mod via the `mod` field in `notebook.yml`.

## Multi-Backend Architecture

pipeio supports multiple notebook formats through a **backend abstraction** (`NotebookBackend` protocol). Each backend handles format-specific operations: detection, sync, execution, validation, export, cell splitting, and template generation. Higher-level lifecycle operations (audit, status, lab, scan) compose these primitives and remain format-agnostic.

### Supported backends

| Backend | Format | Source | Human UI | Execution | Validation |
|---------|--------|--------|----------|-----------|------------|
| `percent` | jupytext percent-format | `.py` with `# %%` markers | Jupyter Lab via `.ipynb` | papermill / nbconvert | AST syntax + import isolation |
| `marimo` | marimo reactive | `.py` with `@app.cell` | marimo editor (`--watch`) | `marimo run` | `marimo check` |

### Backend resolution

Format is resolved per-notebook: `entry.format > config.default_format > auto-detect`. Auto-detection checks marimo first (more specific `import marimo` + `marimo.App()` signature), then percent-format (`# %%`). Default fallback: `percent`.

### Key differences

- **Sync**: Percent-format needs bidirectional `.py` ↔ `.ipynb` sync. Marimo is single-file (sync is a no-op).
- **Execution**: Percent uses papermill on `.ipynb`. Marimo uses `marimo run` directly on `.py`.
- **Pairing**: Percent creates `.ipynb` and `.myst` pairs. Marimo has no paired outputs.
- **Kernels**: Percent uses Jupyter kernelspecs. Marimo uses its own runtime (kernel field ignored).
- **Export**: Percent uses nbconvert. Marimo uses `marimo export html/md/ipynb`.

pipeio manages the notebook lifecycle: scan, pair, sync (bidirectional), execute, audit, publish. `nb_audit` detects lifecycle mismatches (e.g., exploratory notebook still active after mod has scripts, demo notebook not set to publish).

## Notebook Directory Convention

Notebooks use a split layout that separates human-facing files from agent/build artifacts. Marimo notebooks live alongside `.ipynb` files in the workspace dir (the `.py` IS the human interface):

```
code/pipelines/{flow}/
└── notebooks/
    ├── notebook.yml                              # lifecycle config
    ├── explore/
    │   ├── investigate_noise.ipynb               # human-facing (Jupyter Lab)
    │   ├── interactive_explorer.py               # human-facing (marimo edit)
    │   ├── .src/                                 # agent territory (percent-format)
    │   │   └── investigate_noise.py              # source of truth
    │   └── .myst/                                # build artifacts (generated)
    │       └── investigate_noise.md
    └── demo/
        ├── demo_filter.ipynb
        ├── .src/
        │   └── demo_filter.py
        └── .myst/
            └── demo_filter.md
```

- **Workspace dir** (`explore/`, `demo/`) — human territory: `.ipynb` (Jupyter) and `.py` (marimo) files
- **`.src/`** — agent territory: `.py` percent-format files (source of truth for jupytext)
- **`.myst/`** — generated MyST markdown for docs pipeline

**Why marimo files are NOT in `.src/`:** The `.src/` convention exists because percent-format has two faces — the `.py` is the agent source and the `.ipynb` is the human interface. Marimo doesn't have this split: the `.py` IS both the agent file and the human file. Placing it in `.src/` would hide it from humans.

Legacy layouts (flat `notebooks/name.py` or subdirectory `notebooks/name/name.py`) are still supported. Use `pipeio nb migrate --yes` to convert to the `.src/` layout.

### Source of Truth

The `.py` file is always the source of truth for both formats. For percent-format, `.ipynb` and `.md` are generated/synced artifacts. For marimo, the `.py` is the only file.

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

  # Marimo-format notebook (reactive, single-file)
  # Note: marimo files live in the workspace dir (not .src/) because the .py
  # IS the human interface — no .ipynb pairing needed.
  - path: notebooks/explore/interactive_explorer.py
    format: marimo            # explicit format declaration
    kind: interactive         # live exploration, not batch-executable
    description: "Interactive ECoG signal explorer with reactive tuning"
    status: active
    publish_html: true        # exported via marimo export html
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
    kind: str = ""                # investigate | explore | demo | validate | interactive
    description: str = ""         # human-readable description
    status: str = "active"        # draft | active | stale | promoted | archived
    format: str = ""              # "" (auto-detect) | "percent" | "marimo"
    kernel: str = ""              # Jupyter kernelspec name (percent-only; ignored for marimo)
    mod: str = ""
    pair_ipynb: bool = False      # (percent-only) create .ipynb pairing
    pair_myst: bool = False       # (percent-only) create .md pairing
    publish_myst: bool = False
    publish_html: bool = False

class PublishConfig(BaseModel):
    format: str = "html"          # output format (html, markdown)
    docs_dir: str = ""
    prefix: str = "nb-"

class NotebookConfig(BaseModel):
    kernel: str = ""              # flow-level default kernel
    default_format: str = ""      # flow-level default format ("percent" | "marimo" | "")
    publish: PublishConfig = PublishConfig()
    entries: list[NotebookEntry] = []
```

### Format resolution

```
entry.format > config.default_format > auto-detect from file content
```

### Kernel resolution

```
entry.kernel > config.kernel > (no override)
```

For marimo-format notebooks, `resolve_kernel()` always returns empty string (marimo uses its own runtime).

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
