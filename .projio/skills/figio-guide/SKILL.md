---
name: figio-guide
description: "How to use figio MCP tools to build, validate, and manage reproducible scientific figures"
tools: [figio_figure_list, figio_inspect, figio_build, figio_validate, figio_edit_spec, figio_query_output]
---

# Figio Guide

Figio is a declarative build orchestrator for reproducible scientific figures.
It coordinates plotting libraries (Matplotlib, generic scripts) through a YAML
manifest (FigureSpec) that describes panels, layout, annotations, and style,
then assembles them into a single validated SVG suitable for journal submission.

Figio is an **orchestration system**, not a rendering engine. Panels are opaque
-- figio positions, composes, and validates them.

## Core concepts

**FigureSpec** — a YAML file declaring panels, layout, annotations, style, and
a target profile. This is the single source of truth; every build produces the
same output.

**Panel** — a Python script with a `make_figure()` function that returns a
Matplotlib `Figure`, or a generic script that produces an SVG file. Figio
renders it and captures the SVG.

**Target profile** — journal-specific constraints (width, min font, DPI). Built-in
profiles: `nature_single_column`, `nature_double_column`, `science_single`,
`science_double`, `pnas_single`, `pnas_double`, `elife`, `plos_one`,
`cell_single`, `cell_double`, `ieee_single`, `ieee_double`, `default`.

**Composition** — figio places panels in a grid, applies constraints
(`equal_height`, `equal_width`, `align_ylabels`, `align_xlabels`), adds
annotations (panel labels, captions, arrows, callouts, brackets), and
exports to SVG/PDF/PNG.

## MCP tool workflow

### 1. Discover figures

```
figio_figure_list()
```

Returns all `*.figurespec.yaml` and `figurespec.yaml` files in the project.

### 2. Inspect before changing

```
figio_inspect(figure_id="fig1")
```

Returns panels, layout, constraints, annotations, style, and resolved target.
Always inspect before editing.

### 3. Edit a spec

```
figio_edit_spec(figure_id="fig1", patch={"style": {"font_size_pt": 7}})
```

Applies an RFC 7396 JSON merge-patch. The patch is validated before saving.

Common patches:
- Change target: `{"target": "nature_single_column"}`
- Add a panel: `{"panels": {"new_panel": {"generator": "matplotlib", "source": "panels/new.py"}}}`
- Change layout: `{"layout": {"cols": 3}}`
- Add constraint: `{"layout": {"constraints": [{"equal_height": ["a", "b"]}]}}`
- Adjust style: `{"style": {"panel_gap_mm": 5, "font_size_pt": 7}}`

### 4. Build

```
figio_build(figure_id="fig1")
```

Renders panels, composes SVG, exports formats. Returns output paths, validation
checks, cached panels, and timing. Use `force=True` to bypass cache.

To rebuild only specific panels:
```
figio_build(figure_id="fig1", panels="panel_a,panel_b")
```

### 5. Validate

```
figio_validate(figure_id="fig1")
```

Checks against the target profile. Override with:
```
figio_validate(figure_id="fig1", target="nature_single_column")
```

Checks: figure width, max height, panel overflow, min font size, DPI/PNG
dimensions, colorblind palette safety.

### 6. Query build output

```
figio_query_output(figure_id="fig1", query="dimensions")
```

Returns structured data from the last build (bounding boxes, panel positions).

## FigureSpec YAML format

```yaml
id: fig1
target: nature_double_column

panels:
  panel_a:
    generator: matplotlib      # or: script
    source: panels/plot_a.py   # relative to spec file
    inputs: [data/input.csv]   # for cache invalidation

layout:
  type: grid
  rows: 1
  cols: 2
  constraints:
    - equal_height: [panel_a, panel_b]

annotations:
  - type: panel_label
    target: panel_a
    text: A
  - type: caption
    text: "Figure 1. Description."

style:
  font_family: Helvetica
  font_size_pt: 8
  panel_gap_mm: 3
  line_weight: 0.5
```

Supports both flat format (above) and wrapped format (`figure: { ... }`).

## Panel scripts

Matplotlib panels expose a `make_figure()` function:

```python
def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(4, 3))
    # ... plot ...
    return fig
```

Script panels (`generator: script`) run as subprocesses with `--output PATH`
and must produce a valid SVG at that path.

## Connection to manuscripts

Figures are inserted into manuscripts via:
- `manuscript_figure_insert(name, section, figure_id)` — adds a figure reference
- `manuscript_figure_build_all(name)` — batch-builds all referenced figures

The typical workflow: create figures with figio, reference them in manuscript
sections, then build the manuscript.

## Caching

Figio caches panel SVGs keyed by SHA-256 of source + inputs + style. Changed
source or data triggers a rebuild; unchanged panels are skipped. Use
`figio_build(force=True)` to bypass.

## Hard rules

- Always `figio_inspect` before `figio_edit_spec` to understand current state.
- Always `figio_validate` after `figio_build` to check journal compliance.
- Panel scripts must not call `plt.show()` or `fig.savefig()` — figio handles
  SVG capture internally.
- List data dependencies in `inputs` so the cache invalidates correctly.
- Use built-in target profiles when possible; define inline profiles only when
  no built-in matches the journal.
