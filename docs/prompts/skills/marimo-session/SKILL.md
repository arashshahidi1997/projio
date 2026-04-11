---
name: marimo-session
description: >
  Start or join a marimo interactive notebook session for real-time
  agent-human collaboration. The human sees live output in the browser
  via --watch; the agent edits the .py and reads outputs via nb_snapshot.
metadata:
  short-description: interactive marimo notebook session with live agent-human collaboration
  tags: [pipeio, notebook, marimo, interactive, exploration]
  tooling:
    mcp:
      - server: projio
        tools:
          - pipeio_nb_create
          - pipeio_nb_snapshot
          - pipeio_nb_validate
          - pipeio_nb_status
          - pipeio_flow_list
---

# Marimo Interactive Session

Use this skill for real-time agent-human collaboration on a marimo reactive
notebook. The human sees live plots and outputs in the browser; the agent
edits the `.py` file and reads cell outputs via `pipeio_nb_snapshot`.

**Guide:** `docs/tutorials/marimo-notebooks.md`

## When to use

- The user says `/marimo-session` or asks to "explore data interactively"
- You need to iterate on visualizations with live human feedback
- The user wants reactive parameter exploration (sliders, dropdowns)
- You need to see cell outputs (prints, errors, data) while editing a notebook
- A notebook already exists with `format: marimo` in `notebook.yml`

## Prerequisites

Marimo must be installed in the project's compute env (e.g. `cogpy`).
The agent env (`rag`) needs marimo for `nb_validate` only (static analysis).

## Workflow

### 1) Identify or create the notebook

Ask the user (or infer from context): which **flow** and which **notebook**?

```
pipeio_nb_status(flow="<flow>")
```

If no marimo notebook exists, create one:

```
pipeio_nb_create(flow="<flow>", name="<name>", kind="interactive", description="<purpose>")
```

`kind="interactive"` auto-selects marimo format and places the `.py` in the
workspace directory (not `.src/`).

### 2) Ask the human to launch marimo

Tell the user:

> Please launch marimo in your compute environment:
>
> ```
> conda run -n <env> marimo edit <path-to-notebook.py> --watch
> ```
>
> Once the browser opens, let me know and I'll start editing.

The `--watch` flag makes marimo auto-reload when the agent edits the file.
The human sees changes live without manual refresh.

**Important:** Marimo must run from the env where project compute libraries
are installed (e.g. `cogpy`), not from `rag`.

### 3) Edit-snapshot-iterate loop

This is the core collaboration pattern. Repeat until the exploration goal
is met:

**a) Edit the notebook**

Read the current state, then make targeted edits to the `.py` file.
Follow marimo cell rules:
- Cells are `@app.cell` decorated functions
- Function parameters = dependencies on other cells
- Return tuples = exported variables
- Prefix cell-local variables with `_` (no reuse across cells)
- Use `mo.ui.slider()`, `mo.ui.dropdown()` for reactive widgets
- Use `mo.md(f"...")` for markdown output
- Use `with app.setup:` for shared imports/constants

**b) Read outputs**

After editing, capture what the notebook produced:

```
pipeio_nb_snapshot(flow="<flow>", name="<name>")
```

This executes all cells and returns:
- `console`: stdout/stderr from print statements
- `error`: exception name, message, traceback (if cell failed)
- `output_text`: text/plain cell output
- `output_html`: text/html cell output (truncated)
- `has_image`: whether a plot was rendered (binary not included)

**c) Report to the human**

Summarize what you see in the snapshot:
- Which cells succeeded, which errored
- Key data values from prints or text output
- Whether plots rendered (you can see `has_image: true` but not the plot)
- Ask the human what they see in the browser for visual feedback

**d) Iterate**

Based on human feedback ("the PSD looks noisy above 200 Hz", "channel 14
is clearly bad"), make targeted edits and snapshot again.

### 4) Validate and wrap up

When the exploration goal is met:

```
pipeio_nb_validate(flow="<flow>", name="<name>")
```

Fix any structural issues (`marimo check` catches variable redefinition,
dependency cycles, etc.).

Optionally, offer to:
- Publish as HTML: set `publish_html: true` in `notebook.yml`, run `nb_publish`
- Capture findings as a result note: `note_create(note_type="result")`
- Start a report: use `/report` skill

## Editing guidelines

### Cell structure pattern

```python
@app.cell
def analysis(mo, data, threshold):     # dependencies as params
    _filtered = data[data > threshold]  # underscore = cell-local
    _mean = _filtered.mean()

    mo.md(f"""
    ## Filtered Results
    - Threshold: {threshold.value}
    - Count: {len(_filtered)}
    - Mean: {_mean:.3f}
    """)

    return (_filtered,)                 # export for downstream cells
```

### Adding reactive controls

```python
@app.cell
def controls(mo):
    slider = mo.ui.slider(start=0, stop=100, value=50, label="Threshold")
    dropdown = mo.ui.dropdown(options=["A", "B", "C"], label="Method")
    mo.md(f"## Parameters\n{slider}\n{dropdown}")
    return slider, dropdown
```

Downstream cells that depend on `slider` or `dropdown` auto-re-execute
when the user changes the widget in the browser.

### Adding plots

```python
@app.cell
def plot(mo, data, slider):
    import matplotlib.pyplot as plt

    _fig, _ax = plt.subplots(figsize=(10, 5))
    _ax.plot(data)
    _ax.axhline(slider.value, color="red", linestyle="--")
    _ax.set_title(f"Data with threshold = {slider.value}")
    plt.tight_layout()

    mo.md("## Signal Plot")
    return (plt,)           # export plt so downstream cells can use it
```

### Debugging with prints

Add explicit print statements for values you need to see via `nb_snapshot`:

```python
@app.cell
def debug(data):
    print(f"Shape: {data.shape}")
    print(f"Range: [{data.min():.2f}, {data.max():.2f}]")
    print(f"NaN count: {data.isna().sum()}")
    return ()
```

The agent sees these in `nb_snapshot` output under `console`.

## Hard rules

- Never edit the `.py` while the human has unsaved changes in marimo editor
  (unlikely with `--watch`, but check if the human mentions manual editing).
- Always run `pipeio_nb_validate` before declaring the session complete.
- Never assume what plots look like -- ask the human for visual feedback.
- Use `_` prefix for ALL cell-local variables (matplotlib axes, loop vars,
  temp arrays). Marimo enforces unique names across cells.
- Do not add cells that take more than 30 seconds to execute without warning
  the human first (long-running cells block the reactive UI).
- If `nb_snapshot` shows errors, fix them before asking the human for feedback
  -- they see the same errors in the browser.
- Keep the notebook focused. If the exploration grows beyond ~15 cells,
  suggest splitting into a second notebook or promoting code to a library.
