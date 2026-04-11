# Marimo Reactive Notebooks in pipeio

This guide shows how to add marimo reactive notebooks to a projio-managed project alongside the existing jupytext/Jupyter workflow.

**Full spec:** [pipeio notebook specification](../specs/pipeio/notebook.md)

## Prerequisites

Marimo must be installed in the conda environment where your project's compute libraries live — typically the same env your pipeline uses. For example, if your pipeline runs in `cogpy`:

```bash
conda run -n cogpy pip install marimo
```

Verify:

```bash
conda run -n cogpy marimo --version
```

Marimo is also needed in the `rag` env (where pipeio/MCP runs) for `pipeio_nb_validate` to work — it runs `marimo check`, which is static analysis only (no code execution, no compute dependencies needed). If your compute env has an incompatible Python/marimo combination, install a compatible marimo version there — `marimo<0.22` works with Python 3.11.

## What is marimo?

Marimo is a reactive notebook framework where each cell is a Python function decorated with `@app.cell`. Dependencies between cells are declared via function parameters, and marimo builds a DAG to guarantee correct execution order. Unlike Jupyter, there is no hidden state — if you redefine a variable, `marimo check` catches it.

Key differences from jupytext percent-format:

| | Percent-format (jupytext) | Marimo |
|--|---------------------------|--------|
| Cell syntax | `# %%` comment markers | `@app.cell` decorators |
| Dependencies | Implicit via kernel state | Explicit via function params |
| Human interface | `.ipynb` in Jupyter Lab | `.py` via `marimo edit` |
| Sync needed | Yes (`.py` <-> `.ipynb`) | No (single file) |
| Execution | papermill + Jupyter kernel | `marimo run` |
| Validation | AST syntax check | `marimo check` (DAG integrity) |

## Quick start

### 1. Create a marimo notebook via MCP

```
pipeio_nb_create(flow="preprocess_ieeg", name="interactive_explorer", kind="interactive")
```

The `kind="interactive"` automatically selects marimo format. The notebook is placed in the workspace directory (not `.src/`), because the `.py` IS the human interface:

```
notebooks/explore/
├── .src/investigate_noise.py       # percent-format (hidden)
├── investigate_noise.ipynb         # Jupyter (human-facing)
└── interactive_explorer.py         # marimo (human-facing)
```

### 2. Open in marimo editor

Run marimo from your project's compute environment (where cogpy / numpy / etc. are installed):

```bash
conda run -n cogpy marimo edit notebooks/explore/interactive_explorer.py
```

This opens a browser UI where you can edit cells, see outputs, and interact with reactive widgets (sliders, dropdowns).

### 3. Agent-driven editing with live feedback

This is the key workflow. In one terminal, start marimo with `--watch`:

```bash
conda run -n cogpy marimo edit notebooks/explore/interactive_explorer.py --watch
```

In another terminal, run Claude Code. When the agent edits the `.py` file, marimo detects the filesystem change and reloads — you see updated cells and re-executed plots live in your browser, without manual reload.

**The feedback loop:**
1. You tell Claude what to explore ("add a spectrogram view for channels 10-20")
2. Claude edits the `.py` file
3. Marimo auto-reloads — you see the spectrogram appear
4. You give feedback ("the colormap is wrong, use viridis, and the frequency axis should stop at 200 Hz")
5. Claude edits again — you see the fix instantly

No restarting kernels. No "run all cells." No screenshots. You're both working on the same file in real time.

**Important:** Launch marimo from the compute env (e.g. `cogpy`), not from `rag` — the notebook needs access to your project's data libraries (numpy, xarray, cogpy, etc.). The `pipeio_nb_watch` MCP tool is available but launches from the MCP server env; for full data access, use the manual `conda run` approach above.

### 4. Agent reads outputs with `nb_snapshot`

The agent can't see the browser, but it can read cell outputs:

```
pipeio_nb_snapshot(flow="preprocess_ieeg", name="interactive_explorer")
```

This runs `marimo export session`, executes all cells, and returns structured output:
- **Console**: stdout/stderr from print statements
- **Errors**: exception name, message, and traceback
- **Data**: text/plain and text/html cell outputs (truncated for size)
- **Images**: noted as `has_image: true` (binary data stripped)

This closes the feedback loop — the agent sees what the human sees. Use it after editing to verify results, or to inspect a notebook the human just ran.

### 5. Validate

```
pipeio_nb_validate(flow="preprocess_ieeg", name="interactive_explorer")
```

This runs `marimo check`, which catches:
- Variables defined in multiple cells (use `_` prefix for cell-local vars)
- Dependency cycles
- Undefined cell references

### 5. Publish

Set `publish_html: true` in `notebook.yml`, then:

```
pipeio_nb_publish(flow="preprocess_ieeg", name="interactive_explorer")
```

This runs `marimo export html` to produce a standalone HTML file.

## Writing marimo cells

### Cell structure

```python
import marimo

app = marimo.App(width="medium")

@app.cell
def setup():
    import numpy as np
    return (np,)             # tuple of exports

@app.cell
def compute(np):             # np = dependency on setup's export
    x = np.array([1, 2, 3])
    return (x,)

@app.cell
def display(mo, x):
    mo.md(f"Result: **{x.sum()}**")
```

### Key rules

1. **Function parameters declare dependencies.** If `compute` needs `np`, list it as a parameter.
2. **Return tuples declare exports.** `return (x,)` makes `x` available to downstream cells.
3. **Variables must be unique across cells.** Use `_` prefix for cell-local variables (`_fig`, `_ax`, `_i`).
4. **`mo` is the marimo module** — pass it as a parameter to use `mo.md()`, `mo.ui.slider()`, etc.

### Reactive UI widgets

```python
@app.cell
def controls(mo):
    slider = mo.ui.slider(start=0, stop=100, value=50, label="Threshold")
    dropdown = mo.ui.dropdown(options=["A", "B", "C"], label="Method")
    mo.md(f"## Controls\n{slider}\n{dropdown}")
    return slider, dropdown

@app.cell
def filtered(slider, dropdown, data):
    # This cell re-runs automatically when slider or dropdown changes
    result = data[data > slider.value]
    ...
```

### Shared setup with `app.setup`

For imports and constants used across all cells, use `with app.setup:` — these names are available everywhere without passing them as parameters:

```python
with app.setup:
    from pathlib import Path
    import numpy as np
    PROJECT_ROOT = Path("/path/to/project")
```

## notebook.yml configuration

```yaml
kernel: cogpy                      # flow-level default (percent-only)
entries:
  # Percent-format — traditional Jupyter workflow
  - path: notebooks/explore/.src/investigate_noise.py
    kind: investigate
    mod: filter
    status: active
    pair_ipynb: true

  # Marimo — reactive, single-file
  - path: notebooks/explore/interactive_explorer.py
    format: marimo
    kind: interactive
    description: "Reactive signal explorer"
    status: active
    publish_html: true
```

Key fields for marimo entries:
- `format: marimo` — explicit format declaration (or auto-detected from file content)
- `kind: interactive` — signals this notebook persists by design (not promoted to scripts)
- `pair_ipynb` / `pair_myst` — not needed (ignored for marimo)
- `kernel` — not needed (marimo uses its own runtime)

## Layout convention

Marimo notebooks live in the workspace directory directly — NOT in `.src/`:

```
notebooks/explore/
├── .src/                          # percent-format only (hidden)
│   └── investigate_noise.py
├── investigate_noise.ipynb        # human opens in Jupyter Lab
└── interactive_explorer.py        # human opens with: marimo edit <this>
```

**Why?** The `.src/` convention exists because percent-format notebooks have two files: the `.py` (agent source, hidden) and the `.ipynb` (human interface, visible). Marimo has only one file — the `.py` IS the human interface. Hiding it in `.src/` would force humans to dig into a hidden directory.

## MCP tool behavior by format

| Tool | Percent | Marimo |
|------|---------|--------|
| `nb_create` | Places in `.src/` | Places in workspace dir |
| `nb_sync` | Bidirectional `.py` <-> `.ipynb` | No-op (single file) |
| `nb_exec` | papermill on `.ipynb` | `marimo run` on `.py` |
| `nb_validate` | AST + import isolation | `marimo check` |
| `nb_publish` | nbconvert HTML | `marimo export html` |
| `nb_lab` | Creates symlinks to `.ipynb` | Skipped (no `.ipynb`) |
| `nb_watch` | Error (use `nb_lab`) | `marimo edit --watch` |
| `nb_snapshot` | N/A (use `nb_exec` + ipynb) | `marimo export session` — agent reads outputs |
| `nb_audit` | Checks pairing, sync, kernel | Checks format, skips pairing |

## Choosing between formats

Use **percent-format** when:
- You need a specific Jupyter kernel (cogpy, neuropy-env)
- You need parameterized batch execution via papermill/RunCard
- The notebook will be promoted to a pipeline script (`nb_promote`)
- You want Jupyter Lab's full ecosystem (extensions, widgets)

Use **marimo** when:
- You want **live agent-human collaboration** — marimo's `--watch` mode gives you real-time visual feedback as Claude edits the notebook, no kernel restarts or manual reruns
- You want reactive parameter exploration (sliders auto-update plots)
- Reproducibility is critical (DAG execution eliminates hidden state)
- You want structural validation (`marimo check`) as a first-class step
- The notebook is a persistent exploration tool, not a pipeline prototype
