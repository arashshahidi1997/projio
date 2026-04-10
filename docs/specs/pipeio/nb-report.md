# pipeio: Notebook Report Specification

## Problem

Explore notebooks accumulate many cells — imports, data loading, reshaping, intermediate debugging — mixed with the actual findings: figures, metrics, interpretations. Reading through a 500+ line notebook to find the key results is slow, especially for sharing with collaborators or preparing meeting notes.

There is no structured way to extract findings from a notebook and turn them into a permanent, citable record of results. Agents that execute notebooks (`pipeio_nb_exec`) have no follow-up step to interpret what the notebook produced.

## Design Principles

### Agent-written = human-written

The report narrative is produced by agent judgment — interpreting figures, summarizing methods, drawing conclusions. This is not a deterministic build artifact. Reports are treated as **source files**: git-tracked, never overwritten by build tools, editable by humans after creation.

### Flow-local, published via docs_collect

Reports are flow-specific deliverables. They live in the flow's `docs/` directory (source of truth) and reach the site through the existing `docs_collect` pipeline. No new collector is needed — `DocsCollector` already copies `{flow}/docs/` recursively and preserves subdirectory structure.

### Two-phase separation

The workflow separates **extraction** (deterministic, reproducible from the notebook) from **report writing** (agent judgment, non-reproducible). The MCP tool handles extraction; the slash command orchestrates the agent to write the report.

## Flow Directory Layout

```
code/pipelines/{flow}/
└── docs/
    ├── overview.md                          # existing flow overview
    ├── {mod}/                               # existing mod facet docs
    │   ├── theory.md
    │   └── spec.md
    └── reports/                             # NEW — notebook reports
        ├── investigate_noise.md             # agent-written report (git-tracked)
        ├── investigate_noise/               # extracted figures (git-tracked)
        │   ├── output_3_0.png
        │   └── output_7_1.png
        └── explore_params.md
```

Each report is a pair: `{name}.md` (narrative) + `{name}/` (figure assets). The markdown references figures via relative paths: `![caption](investigate_noise/output_3_0.png)`.

### Publication path

```
{flow}/docs/reports/{name}.md          →  docs/pipelines/{flow}/reports/{name}.md
{flow}/docs/reports/{name}/*.png       →  docs/pipelines/{flow}/reports/{name}/*.png
```

`DocsCollector` handles this via its existing `rglob("*")` traversal. Reports are not mod facet dirs (they don't contain `theory.md`/`spec.md`/`delta.md`), so they pass through with their original relative paths. The published copies get the standard `_copy_with_header` source-path comment.

### Why not `docs/log/result/`

Result notes in `docs/log/result/` are project-wide, timestamped event records (like ideas or issues). Notebook reports are flow-specific, notebook-specific, and evolve with the notebook. A result note *may* cross-reference a flow report, but they serve different purposes:

| Aspect | Result note (`docs/log/result/`) | Notebook report (`{flow}/docs/reports/`) |
|--------|----------------------------------|------------------------------------------|
| Scope | Project-wide finding | Single notebook's outputs |
| Identity | Timestamped event | Named after notebook |
| Lifecycle | Append-only log | Updated when notebook re-runs |
| Ownership | Notio | Pipeio |
| Published via | Notio index builder | `docs_collect` |

A common pattern: run `/report` to produce the flow-local report, then capture the key finding as a result note that references it.

## MCP Tool: `pipeio_nb_report(flow, name)`

### Purpose

Extract figures, markdown narrative, and text outputs from an executed notebook. Save figures to the flow's `docs/reports/{name}/` directory. Return a structured payload for the agent to write a report from.

### Signature

```python
def mcp_nb_report(
    root: Path,
    flow: str,
    name: str,
    *,
    overwrite: bool = False,
    tags_only: bool = False,
) -> dict[str, Any]:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `flow` | `str` | Flow name |
| `name` | `str` | Notebook name (without extension) |
| `overwrite` | `bool` | Re-extract figures even if `docs/reports/{name}/` exists. Default `False` |
| `tags_only` | `bool` | Only extract cells tagged with `# REPORT:` marker. Default `False` |

### Behavior

The tool dispatches to format-specific backends via the notebook backend system.

#### Percent-format (default)

1. **Locate the executed notebook.** Resolve `.py` → `.ipynb` via `backend.output_paths()`. Error if the `.ipynb` has no cell outputs (never executed).

2. **Extract via nbconvert.** Use `MarkdownExporter` + `ExtractOutputPreprocessor` (already installed, no new deps).

3. **Save figures.** Write extracted PNGs to `{flow}/docs/reports/{name}/`. Skip if directory exists and `overwrite=False`.

4. **Parse and classify cells.** Walk the `.ipynb` JSON and classify:
   - **markdown_cells**: narrative text (what is being computed, why)
   - **figures**: `[{path, cell_index, mime, alt_text}]` — paths relative to `docs/reports/`
   - **text_outputs**: `[{cell_index, content}]` — print statements with metrics, tables
   - **html_outputs**: `[{cell_index, widget_lib, html_length}]` — interactive widget outputs (holoviews, bokeh, plotly, ipywidgets) that cannot be extracted as static images

5. **Apply tag filter (if `tags_only=True`).** Only include cells where:
   - Markdown cells start with `# REPORT:` (prefix stripped from output)
   - Code cells have a `# REPORT` comment in the first 3 lines

6. **Return structured payload** (see below).

#### Marimo format

1. **Export to markdown** via `marimo export md`.
2. **Extract embedded figures** (base64 data URIs) from the markdown output.
3. **Save figures** to `{flow}/docs/reports/{name}/`.
4. **Return structured payload** with `format: "marimo"`.

Tag filtering (`tags_only`) is not supported for marimo.

### Interactive widget outputs (holoviews, bokeh, plotly)

Notebooks using holoviews, bokeh, or plotly render interactive HTML widgets in Jupyter. These **cannot be extracted as static images** by nbconvert — they produce `text/html` MIME outputs, not `image/png`.

When the tool detects these, it returns:
- `html_outputs`: list of `{cell_index, widget_lib, html_length}` for each widget
- `html_outputs_hint`: human-readable guidance on how to add static alternatives

**Workarounds for authors:**
- **holoviews**: `hv.save(plot, 'output.png', backend='matplotlib')`
- **bokeh**: `export_png(plot, filename='output.png')`
- **plotly**: `fig.write_image('output.png')`
- Add matplotlib summary plots alongside interactive widgets
- Tag the static alternatives with `# REPORT` for inclusion

### Return Value

```python
{
    "flow": "preprocess_ieeg",
    "notebook": "investigate_noise",
    "format": "percent",  # or "marimo"
    "notebook_path": "code/pipelines/preprocess_ieeg/notebooks/explore/investigate_noise.ipynb",
    "figures_dir": "code/pipelines/preprocess_ieeg/docs/reports/investigate_noise",
    "figures_extracted": 5,
    "figures_skipped": 0,       # when overwrite=False and dir exists
    "markdown_cells": [
        {"cell_index": 0, "content": "# Noise Characterization\n\nWe compute PSD..."},
        {"cell_index": 4, "content": "## Spatial structure\n\nCorrelation across..."},
    ],
    "figures": [
        {"cell_index": 3, "path": "investigate_noise/output_3_0.png", "alt_text": ""},
        {"cell_index": 7, "path": "investigate_noise/output_7_1.png", "alt_text": ""},
    ],
    "text_outputs": [
        {"cell_index": 5, "content": "Mean SNR: 12.3 dB\nMedian: 11.8 dB"},
        {"cell_index": 9, "content": "Channels rejected: 4/128 (3.1%)"},
    ],
    "execution_metadata": {
        "kernel": "cogpy",
        "executed_at": "2026-04-10T11:30:00",
        "cell_count": 32,
        "tagged_cells": null,     # or count if tags_only
    },
    # Present only when interactive widgets are detected (percent-format):
    "html_outputs": [
        {"cell_index": 6, "widget_lib": "holoviews", "html_length": 45230},
        {"cell_index": 8, "widget_lib": "bokeh", "html_length": 12800},
    ],
    "html_outputs_hint": "2 interactive widget output(s) detected (bokeh, holoviews). ...",
}
```

### Idempotency

- Figures: only re-extracted when `overwrite=True` or the directory doesn't exist yet.
- Report `.md`: never touched by this tool. Writing the report is the agent's job.
- Re-running after notebook re-execution: use `overwrite=True` to refresh figures, then update the report markdown.

### Error Cases

| Condition | Behavior |
|-----------|----------|
| Notebook not found | Error with resolution details |
| Notebook has no outputs (percent) | Error: "notebook has not been executed — run pipeio_nb_exec first" |
| Marimo export fails | Error with stderr from `marimo export` |
| nbconvert not available (percent) | Error: "nbconvert required — install via pip install nbconvert" |
| Figures dir exists, `overwrite=False` | Skip extraction, return payload with `figures_skipped` count |
| All outputs are HTML widgets | `figures` empty, `html_outputs` populated, `html_outputs_hint` explains |

## Slash Command: `/report`

### Purpose

Orchestrate the agent to produce a curated, human-readable report from a notebook's extracted outputs. The skill calls `pipeio_nb_report`, then guides the agent to write a narrative markdown file.

### Skill Definition

```yaml
# .projio/skills/pipeio-report/SKILL.md
name: pipeio-report
trigger: /report
description: Extract notebook results and write a flow-local report
```

### Skill Prompt (summary)

1. Ask the user which flow and notebook to report on (or infer from context).
2. Call `pipeio_nb_report(flow, name)` to extract figures and outputs.
3. Write `{flow}/docs/reports/{name}.md` with this structure:

```markdown
---
notebook: investigate_noise
flow: preprocess_ieeg
date: 2026-04-10
kernel: cogpy
tags: [report]
---

# Noise Characterization — investigate_noise

## Summary

<!-- 2-3 sentence overview of what the notebook investigates and key findings -->

## Method

<!-- Concise description of each analysis step — the math/logic, not the code.
     Reference mod theory docs where applicable. -->

## Results

### Power Spectral Density

![PSD across channels showing 50 Hz line noise peak](investigate_noise/output_3_0.png)

<!-- Interpretation: what does this figure show? What is notable? -->

### Spatial Correlation

![Channel correlation matrix with 4 outlier channels highlighted](investigate_noise/output_7_1.png)

<!-- Interpretation -->

## Key Metrics

| Metric | Value |
|--------|-------|
| Mean SNR | 12.3 dB |
| Channels rejected | 4/128 (3.1%) |

## Conclusions

<!-- What did we learn? What should happen next? -->

## References

- Mod theory: [filter/theory.md](../filter/theory.md)
- Source notebook: `notebooks/explore/investigate_noise.ipynb`
```

4. The agent selects which figures to include and writes captions + interpretations.
5. Not all extracted figures need to appear — the agent curates.

### Behavior on Re-run

If `{flow}/docs/reports/{name}.md` already exists, the skill should:
1. Call `pipeio_nb_report(flow, name, overwrite=True)` to refresh figures.
2. Read the existing report.
3. Ask the user whether to update the existing report or create a fresh one.

## Cell Tagging (Optional Enhancement)

Notebook authors can tag cells for report inclusion using comment markers:

**Markdown cells:**
```markdown
# REPORT: Power Spectral Density

We compute the PSD using Welch's method...
```

**Code cells:**
```python
# REPORT
fig, ax = plt.subplots()
ax.plot(freqs, psd)
ax.set_title("PSD across channels")
plt.show()
```

When `tags_only=True`, `pipeio_nb_report` filters to tagged cells only. This produces a curated subset — useful for long notebooks where the author knows which cells matter.

Tags are a convention, not a requirement. Without tags, the tool extracts everything and the agent curates during report writing.

## Integration with Existing Tools

### docs_collect

No changes needed. `DocsCollector` already handles `{flow}/docs/reports/` through its `rglob` traversal. Reports are not mod facet dirs, so they pass through with original paths. The `_copy_with_header` adds the standard source-path comment to published copies.

### publish.yml

Optional gating via a new `reports` key:

```yaml
# {flow}/publish.yml
dag: true
report: true       # existing: Snakemake HTML report
scripts: true
reports: true       # NEW: notebook reports (default: true)
```

When `reports: false`, `DocsCollector` skips the `reports/` subdirectory. Default is `true` — reports are published unless explicitly suppressed.

### nb_audit

`pipeio_nb_audit` can flag notebooks that have been executed but lack a report:

```
investigate_noise: executed, no report (docs/reports/investigate_noise.md missing)
```

This is informational, not an error — not every notebook needs a report.

### Result notes

The `/report` skill may optionally prompt the user to also capture a result note (`note_create(type="result")`) that cross-references the flow report. The result note's `figure` field can point to the report, and `refs` can link the flow report path. This bridges flow-local reports with the project-wide result log.

## Implementation Plan

| Step | Component | Change |
|------|-----------|--------|
| 1 | `pipeio/mcp.py` | New `mcp_nb_report` function |
| 2 | `projio/mcp/pipeio.py` | Register `pipeio_nb_report` tool |
| 3 | `.projio/skills/pipeio-report/SKILL.md` | New `/report` skill |
| 4 | `pipeio/docs.py` | Add `reports` filtering to `DocsCollector` (gated by `publish.yml`) |
| 5 | `pipeio/docs.py` | Add `reports` field to `PublishConfig` (default `True`) |
| 6 | `pipeio/notebook/analyze.py` | Cell tag detection helpers |
| 7 | ontology.md | Document report convention in flow directory layout |

Steps 1-3 deliver the core feature. Steps 4-5 add publish gating. Step 6 adds tag filtering. Step 7 updates the canonical spec.

## Non-Goals

- **Auto-generating the report narrative.** The tool extracts raw material; the agent (or human) writes the interpretation. `pipeio_nb_report` is an extractor, not a summarizer.
- **Replacing Snakemake reports.** `pipeio_report` generates provenance-rich HTML from Snakemake metadata. `pipeio_nb_report` extracts findings from notebook cell outputs. Different tools for different purposes.
- **Notebook-to-documentation conversion.** This is not nbconvert-to-docs. The report is a curated, interpreted subset of notebook outputs — not a full notebook rendering.
- **Version-stamped reports.** Reports evolve with notebooks. Git history provides versioning. No dated copies or report archives.
- **Cross-flow report aggregation.** Each report is scoped to one notebook in one flow. Project-wide synthesis belongs in result notes or manuscript sections.
