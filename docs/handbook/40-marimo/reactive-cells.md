# Reactive cells

!!! note "Sources & anchors"
    - **Stack component:** Marimo
    - **Canonical artifact:** `pixecog/code/pipelines/preprocess_ieeg/notebooks/explore/interactive_signal_explorer.py`
    - **Workshop session:** Day-2 AM session 1 (Marimo authoring)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

File-as-`.py`; reactive DAG; no hidden state; diff-friendly.

## The notebook format problem

Every notebook format is a bet about what the unit of analysis should be.
Jupyter's bet was the cell-as-output-block: run code interactively, accumulate
outputs inline, export to `.ipynb` (a JSON blob that records every output
alongside the code). That bet paid off for exploration and won wide adoption.
It also introduced a failure mode that every researcher who has touched a
Jupyter notebook for longer than a month has encountered: **hidden state**. You
run cells out of order during exploration, modify a variable in one cell, and
the later cell that depended on the old value still shows output from two runs
ago. The notebook looks consistent because the outputs are there; it isn't,
because the outputs no longer reflect the current code path. Restarting and
re-running fixes this, but it's a manual discipline — one that research
practice erodes under deadline pressure.

Marimo's bet is different: **the notebook is a reactive DAG**. The file is a
`.py` file. Each cell is a Python function annotated by `@app.cell`. The cell's
return values are its outputs; other cells that reference those names are its
dependents. When a cell changes — when you edit its code, when a UI element
fires, when an upstream value propagates — marimo re-runs all and only the
downstream cells. You cannot run cells out of order because there is no
"order" to violate: execution order is determined by the dependency graph,
not by the sequence in which cells appear in the file.

## The file

A marimo notebook starts with:

```python
import marimo

__generated_with = "0.23.1"
app = marimo.App(width="full")
```

Then cells, each a function decorated with `@app.cell`:

```python
@app.cell
def controls(mo):
    subject_dd = mo.ui.dropdown(options=subjects, label="Subject")
    session_dd = mo.ui.dropdown(options=[], label="Session")
    return subject_dd, session_dd

@app.cell
def signal_view(subject_dd, session_dd, mo):
    # re-runs automatically when subject_dd or session_dd change
    fig = plot_signals(subject_dd.value, session_dd.value)
    return mo.ui.plotly(fig)
```

The dependency between `controls` and `signal_view` is inferred from the
function signatures: `signal_view` takes `subject_dd` and `session_dd` as
arguments, so marimo knows to re-run `signal_view` whenever those change. No
hidden state, no import-order bugs, no mysterious stale outputs.

From `pixecog/code/pipelines/preprocess_ieeg/notebooks/explore/interactive_signal_explorer.py`:

```python
app = marimo.App(width="full")

with app.setup:
    from pathlib import Path
    import numpy as np
    PROJECT_ROOT = Path("/storage2/arash/projects/pixecog")
    subjects = sorted(
        p.name for p in (PROJECT_ROOT / "raw").iterdir()
        if p.is_dir() and p.name.startswith("sub-") and p.name != "sub-test"
    )
```

The `app.setup` block runs once at startup; the `@app.cell` functions form the
reactive graph on top. The subject list is populated from the BIDS `raw/`
directory at load time; changing the subject dropdown re-runs signal loading
and all downstream display cells automatically.

## No hidden state

The practical consequence for research: when you hand a marimo notebook to a
collaborator, they get a notebook that either runs — end to end, top to bottom,
producing the outputs you see — or fails visibly. There is no
"run-cells-6-and-12-in-the-right-order" tribal knowledge. The reactive DAG
enforces a contract: outputs are a deterministic function of inputs. This is
the property that makes marimo notebooks trustworthy as research artifacts
rather than as interactive scratchpads.

This also matters for pipeline integration. A marimo notebook can be executed
as a plain Python script (`python notebook.py`) because the `app` object,
when run from the command line, simply executes cells in dependency order.
No Jupyter server, no kernel management. The same file that you open in the
marimo editor for interactive exploration can be invoked from a Snakemake rule
without modification.

## Diff-friendly storage

The `.py` format makes a practical difference for a DataLad-versioned project.
Jupyter's `.ipynb` files serialize cell outputs as base64-encoded blobs
embedded in JSON. A one-line code change produces a diff that is hundreds of
lines long because the outputs change. Notebooks are effectively untrackable
in practice — people commit them with outputs stripped, or commit them with
outputs included and give up on meaningful diffs.

Marimo notebooks produce diffs that read like code diffs. A changed cell shows
exactly which function body changed. A new dependency shows as a new function
argument. The DataLad `datalad diff` and `git log` views remain legible; the
change history of the notebook is the change history of the analysis.

## Why Marimo over Jupyter for this workshop

The workshop teaches Marimo for three concrete reasons grounded in the stack:

1. **Pipeline integration**: marimo notebooks run as scripts and are invoked
   by pipeio's `pipeio_nb_exec(flow, name)` without a Jupyter kernel. The same
   format spans interactive and batch execution.

2. **Agent collaboration**: `pipeio_nb_watch(flow, name)` launches `marimo
   edit --watch` so a human can observe a live marimo session while an agent
   edits the underlying `.py` file. `pipeio_nb_snapshot(flow, name)` executes
   the notebook and returns cell outputs — the agent's only window into what a
   notebook produces. Neither tool has a Jupyter equivalent in the projio stack.

3. **Site publishing**: marimo notebooks export to self-contained HTML/WASM
   bundles via `marimo export html-wasm`, enabling handbook explorables that
   run in any browser without a server. That capability is what makes
   [chapter E1–E5](handbook-explorables.md) possible.

Jupyter remains the right tool when the ecosystem demands it (existing
workflows, packages that import `IPython`-specific display objects, published
`.ipynb` archives). For new work inside a projio-managed project, Marimo is
the default — the `pipeio_nb_create` scaffolding produces marimo-format files
by default when `format: marimo` is set in `notebook.yml`.

## Further reading

- **[Marimo documentation](https://docs.marimo.io/)** — installation, the reactive execution model, UI element API (`mo.ui.*`), and the `.py` file format.
- **[Marimo GitHub](https://github.com/marimo-team/marimo)** — source and issues; design-decision blog posts explain the reactive model's constraints.
