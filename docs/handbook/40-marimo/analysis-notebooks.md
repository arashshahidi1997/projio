# Analysis notebooks

!!! note "Sources & anchors"
    - **Stack component:** Marimo
    - **Canonical artifact:** `pixecog/code/pipelines/preprocess_ieeg/notebooks/` + `notebook.yml`
    - **Workshop session:** Day-2 AM session 1 (Marimo authoring)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

`notebooks/{explore,demo}/` layout; `nb_watch`; `nb_snapshot`.

## The notebook layout

Each flow directory in a projio project contains a `notebooks/` tree that
partitions notebooks by intent:

```
code/pipelines/<flow>/
└── notebooks/
    ├── notebook.yml        # registry: paths, kinds, formats, publish config
    ├── explore/            # marimo: live in the directory root
    │   └── <name>.py
    ├── demo/               # marimo: validated, publication-facing
    │   └── <name>.py
    └── explore/
        └── .src/           # jupytext: source .py with paired .ipynb/.myst.md
            └── <name>.py
```

The `explore/` bucket is for notebooks that are live analysis artifacts —
tools you run while developing a mod, checking preprocessing outputs, or
investigating a new detection approach. The `demo/` bucket is for notebooks
that have been validated to run end-to-end and are published to the docs site.
The distinction is about *trust*, not *content*: a demo notebook is one you
are confident will run correctly for a reader who didn't author it.

The format matters for placement. **Marimo notebooks** live directly inside
`notebooks/explore/` or `notebooks/demo/` — the `.py` file IS the notebook;
no separate source directory is needed. **Jupytext (percent-format) notebooks**
live inside `notebooks/explore/.src/` or `notebooks/demo/.src/` because their
source file pairs with a `.ipynb` or `.myst.md` companion and the split
prevents accidental confusion between source and derived file.

The `notebook.yml` registry file at the flow level records every notebook in
the flow, its kind, format, and publication settings:

```yaml
# pixecog/code/pipelines/preprocess_ieeg/notebook.yml (excerpt)
kernel: cogpy
entries:
- path: notebooks/explore/interactive_signal_explorer.py
  kind: interactive
  description: Reactive signal explorer with subject/session/channel selection
  status: active
  format: marimo
  pair_ipynb: false
  publish_html: false

- path: notebooks/explore/investigate_ttl_masking_characterization.py
  kind: investigate
  description: TTL masking proof-of-concept — per-row lag estimation, stability check
  status: active
  format: marimo
  publish_html: true
```

The `format: marimo` field tells pipeio's notebook tooling which backend to
use. When the field is empty (`format: ''`), pipeio auto-detects by reading
the first few lines of the file and checking for `import marimo`. The
`publish_html: true` entries get served on the docs site via the publish
pipeline.

## A concrete example: the interactive signal explorer

`pixecog/code/pipelines/preprocess_ieeg/notebooks/explore/interactive_signal_explorer.py`
is the clearest example of marimo's role in a real analysis flow. The notebook:

- Discovers available subjects at startup by reading the BIDS `raw/`
  directory tree (no hardcoded subject list)
- Presents dropdown controls for subject and session selection
- On any dropdown change, re-runs signal loading, PSD estimation, and
  spatial RMS computation automatically via the reactive DAG
- Displays time-domain waveforms, power spectral density, and a spatial
  channel map for the selected data slice

This is exactly the kind of notebook that would be dangerous in Jupyter:
several cells that each take 5–30 seconds to run, with state accumulated
across subject switches. In marimo, changing the subject dropdown re-runs
only the cells downstream of the subject selection, and re-runs them
automatically.

The notebook uses `cogpy.io.ieeg_io` for BIDS-iEEG loading and
`cogpy.spectral.psd` for multitaper PSD estimation — library functions
from `code/lib/cogpy` registered in codio as `role: core`. This is the
code-tier pattern in practice: the notebook composes library functions
(cogpy) with flow-specific configuration (which subjects, which preprocessing
derivatives to load).

## Authoring with nb_watch

The standard workflow for authoring a marimo notebook while keeping the agent
in the loop is `nb_watch`:

```python
# MCP tool call
pipeio_nb_watch(flow="preprocess_ieeg", name="interactive_signal_explorer")
```

This launches `marimo edit --watch` pointed at the notebook file. The marimo
editor opens in the browser; the file-watcher reloads the running session
whenever the `.py` file changes. When an agent edits the `.py` file directly
(using the `Edit` tool), the marimo session picks up the change without
requiring a restart. The human sees the updated notebook in the browser in
real time; the agent sees feedback via `nb_snapshot`.

This is the collaboration pattern: the agent edits the source file, the human
watches the live session in the browser, and neither party has to restart a
kernel or re-run cells manually. The reactive DAG handles propagation
automatically.

## Capturing outputs with nb_snapshot

The agent cannot see a marimo session directly. `pipeio_nb_snapshot` bridges
that gap:

```python
# MCP tool call
pipeio_nb_snapshot(flow="preprocess_ieeg", name="investigate_ttl_masking_characterization")
```

This executes the notebook non-interactively (`marimo run`) and returns the
text output of each cell. For diagnostic notebooks — the kind that compute a
summary table, print a report, or emit a figure to disk — `nb_snapshot` gives
the agent a complete view of what the notebook produced. It is the agent's
"eyes" into a notebook run: the same information a human sees after execution,
accessible via a single MCP tool call rather than via screenshot or manual
inspection.

`nb_snapshot` complements `nb_watch`: watch for interactive authoring where a
human is present, snapshot for autonomous execution where the agent needs to
verify outputs or extract figures for further processing (see also
`pipeio_nb_extract` for pulling figures out of an executed notebook).

## The notebook lifecycle

pipeio tracks notebooks across a lifecycle managed via `notebook.yml`:

| Status | Meaning |
|--------|---------|
| `draft` | Scaffolded, not yet meaningful content |
| `active` | Used, maintained, re-runnable |
| `archived` | Superseded; kept for reference but not maintained |

The `kind` field further qualifies purpose: `investigate` (exploratory, may
have hardcoded paths or side effects), `interactive` (reactive UI, requires
a running marimo session), `demo` (validated pipeline walkthrough),
`validate` (correctness check for a specific mod). These are social contracts
rather than enforced constraints, but they are the vocabulary `pipeio_nb_status`
and `pipeio_nb_audit` use to report on a flow's notebook health.

To check notebook sync state — whether the `.py` and any paired `.ipynb` file
are consistent — use `pipeio_nb_diff(flow, name)`. To sync them:
`pipeio_nb_sync(flow, name, direction="py2nb")`. Marimo notebooks set
`pair_ipynb: false` in `notebook.yml` and skip this step entirely: there is
no `.ipynb` to keep in sync because marimo doesn't produce one.

## One discipline to adopt

The survey found one friction point worth naming: pixecog's `__marimo__/session/`
cache directory leaked into the repository root and was not gitignored. This is
easy to miss because marimo's default cache location is a hidden directory in
the working directory where `marimo edit` was launched. Add this to `.gitignore`
if it isn't there already:

```
__marimo__/
```

The pipeio scaffold now includes this in the generated `.gitignore`, but
existing projects that predated the scaffold may need to add it manually.

## Pairing: HoloViews + xarray

The exploration stack recommended to workshop students is: **xarray** for
multidimensional data, **HoloViews** (via `hvplot`) for declarative plotting,
and **Marimo** as the reactive shell that ties them together. Each piece
addresses a distinct pain point; the trio collapses what would otherwise be
a slow manual loop — load, slice, re-plot, compare — into a single reactive
cell chain.

### Why xarray

Neuroscience data is intrinsically N-dimensional: channels × time × trials ×
subjects, with named coordinates attached to each axis. Plain NumPy arrays
lose this structure the moment you slice them. `xarray.DataArray` keeps named
dimensions and coordinates alive through arithmetic, reductions, and
broadcasting, so `da.sel(channel="LFP-03", time=slice(0, 2))` reads like the
selection it represents, not like an index arithmetic puzzle.

BIDS-shaped data loads naturally into xarray. Tools like MNE-Python and
`mne-bids` expose data as `(channels, time)` arrays with associated metadata;
`xr.DataArray` with `dims=["channel", "time"]` and `coords={"channel": ch_names,
"time": times}` carries that metadata forward. A Snakemake rule that writes an
xarray `Dataset` to a NetCDF file (`ds.to_netcdf(output[0])`) makes the
output self-describing — downstream rules load it back with `xr.open_dataset`
and the dimension names are still there.

### Why HoloViews

HoloViews provides a declarative plotting layer that operates on labeled data:
one `.hvplot()` call on an xarray `DataArray` produces an interactive figure
with axes labeled from the dimension names, a colorbar drawn from the
coordinate values, and an automatic time slider if the data is three-dimensional.
The same API works across matplotlib, bokeh, and plotly backends — you select
the backend once per session, not per plot.

The practical payoff for exploration: you do not write `plt.xlabel(...)`,
`plt.colorbar(...)`, or `for subj in subjects: ax.plot(...)`. You write:

```python
import xarray as xr
import hvplot.xarray  # registers .hvplot on xarray objects

# load a channels × time DataArray from a derivatives NetCDF
da = xr.open_dataarray("derivatives/preprocess_ieeg/sub-01/ses-pre/sub-01_ses-pre_lfp.nc")

# one-line interactive line plot; HoloViews infers axes from dims
da.hvplot.line(x="time", by="channel", width=800, height=300)
```

### Why Marimo closes the loop

Reactive cells mean that changing one xarray slice or one HoloViews parameter
re-renders every downstream cell automatically. A subject-selection dropdown,
a channel multi-select, and a time-range slider each become a Marimo `mo.ui`
widget; the HoloViews plot cell takes those widget values as arguments and
re-runs whenever any of them changes:

```python
@app.cell
def controls(mo):
    subject = mo.ui.dropdown(options=subjects, label="Subject")
    channel = mo.ui.multiselect(options=ch_names, label="Channels")
    return subject, channel

@app.cell
def plot(subject, channel, da):
    # re-runs automatically when subject or channel changes
    return da.sel(subject=subject.value, channel=channel.value).hvplot.line(
        x="time", width=800, height=300
    )
```

No manual `plt.show()`, no cell re-runs, no stale figure from three iterations
ago. The trio — xarray labeled data, HoloViews declarative rendering, Marimo
reactive DAG — collapses the explore-iterate loop that is otherwise the slowest
part of analysis development.

### Honest scope

HoloViews is a workshop recommendation, not part of projio's enforced stack.
Projects can use any plotting library; the codio catalog already lists bokeh,
panel, and holoviews as external mirrors in `cogpy`. For **static publication
figures** — panels that will appear in a manuscript or a composed figio figure —
fall back to matplotlib and the [figio + manuscript pipeline](../60-projio/40-figio-and-manuscript.md).
HoloViews is optimized for interactive exploration; matplotlib is optimized for
precise layout control and vector export. Use each where it fits.

## Further reading

- **[xarray](https://docs.xarray.dev/)** — `DataArray`, `Dataset`, `.sel()`/`.isel()` coordinate selection, and groupby operations on labelled N-D arrays.
- **[HoloViews](https://holoviews.org/)** — declarative multi-dimensional plotting; the `.hvplot` accessor that bridges xarray and interactive bokeh/panel renderers.
- **[MNE-Python](https://mne.tools/)** — EEG/iEEG processing; `read_raw_*`, epochs, and time-frequency representations.
