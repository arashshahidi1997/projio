---
name: pipeio-report
description: >
  Extract notebook results via pipeio_nb_report and write a curated
  flow-local report with figures, metrics, and interpretation.
metadata:
  short-description: extract notebook results and write a flow-local report
  tags: [pipeio, notebook, report, results]
  tooling:
    mcp:
      - server: projio
        tools:
          - pipeio_nb_report
          - pipeio_flow_list
          - pipeio_nb_status
          - note_create
---

# Pipeio Report

Use this skill to extract findings from an executed notebook and write a
curated report that lives in the flow's `docs/reports/` directory.

## When to use

- After running `pipeio_nb_exec` to execute an exploratory notebook
- When you need to summarize notebook findings for collaborators
- When preparing results for meeting notes or manuscript sections
- When the user says `/report`

## Format support

The tool works with both notebook formats via the backend system:

- **Percent-format** (default): Extracts from the paired `.ipynb` via
  nbconvert. Full cell classification, tag filtering, HTML widget detection.
- **Marimo**: Exports to markdown via `marimo export md`, then extracts
  embedded figures. Tag filtering (`tags_only`) is not supported for marimo.

## Workflow

### 1) Identify the target

Ask the user (or infer from conversation context):
- Which **flow**?
- Which **notebook**?

If unclear, use `pipeio_flow_list()` and `pipeio_nb_status()` to discover
available flows and notebooks.

### 2) Extract notebook outputs

```
pipeio_nb_report(flow="<flow>", name="<notebook>")
```

This extracts:
- **markdown_cells**: narrative text from the notebook
- **figures**: extracted PNGs saved to `{flow}/docs/reports/{name}/`
- **text_outputs**: printed metrics and tables
- **execution_metadata**: kernel, timestamp, cell count

If the notebook has not been executed, the tool will error. Ask the user
to run `pipeio_nb_exec` first.

If figures already exist and the notebook was re-executed, use:
```
pipeio_nb_report(flow="<flow>", name="<notebook>", overwrite=True)
```

For long notebooks where the author tagged important cells with `# REPORT:`:
```
pipeio_nb_report(flow="<flow>", name="<notebook>", tags_only=True)
```

### 3) Check for existing report

Read `{flow}/docs/reports/{name}.md` if it exists.

- If it exists, ask the user: "A report already exists. Update it with
  new results, or start fresh?"
- If starting fresh, proceed to step 4.
- If updating, read the existing report and revise relevant sections
  (new figures, updated metrics, revised conclusions).

### 4) Write the report

Create `{flow}/docs/reports/{name}.md` with this structure:

```markdown
---
notebook: <notebook_name>
flow: <flow_name>
format: <percent or marimo>
date: <today>
kernel: <kernel from extraction, empty for marimo>
tags: [report]
---

# <Descriptive Title> -- <notebook_name>

## Summary

<!-- 2-3 sentence overview: what was investigated, key finding -->

## Method

<!-- Concise description of each analysis step.
     Describe the math/logic, not the code.
     Reference mod theory docs where applicable:
     see [filter theory](../filter/theory.md) -->

## Results

### <Result Section Title>

![Descriptive caption](investigate_noise/output_3_0.png)

<!-- Interpretation: what does this figure show? What is notable?
     What was expected vs observed? -->

### <Another Result>

![Caption](investigate_noise/output_7_1.png)

<!-- Interpretation -->

## Key Metrics

| Metric | Value |
|--------|-------|
| <metric_name> | <value> |

## Conclusions

<!-- What did we learn? Does this confirm or refute the hypothesis?
     What should happen next? -->

## References

- Source notebook: `notebooks/explore/<name>.ipynb` (or `<name>.py` for marimo)
- Related mod docs: [<mod>/theory.md](../<mod>/theory.md)
```

### Handling interactive widget outputs (holoviews, bokeh, plotly)

If the extraction returns `html_outputs`, these are interactive widgets
that render in Jupyter but cannot be extracted as static images. The
`html_outputs_hint` field explains the issue.

**What to do:**
- Report to the user which cells produced widget-only outputs
- Suggest adding static summary plots alongside the widgets:
  - **holoviews**: `hv.save(plot, 'output.png', backend='matplotlib')`
  - **bokeh**: `export_png(plot, filename='output.png')`
  - **plotly**: `fig.write_image('output.png')`
- If static alternatives already exist in other cells, use those
- If no static figures are available, describe the findings from
  `text_outputs` (printed metrics) and note that the interactive
  visualizations are available in the source notebook

### Writing guidelines

- **Curate, don't dump.** Not every figure needs to appear. Select the
  figures that tell the story. Omit redundant or debugging plots.
- **Describe the science, not the code.** "We computed the power spectral
  density using Welch's method with 2-second Hanning windows" -- not
  "We called scipy.signal.welch with nperseg=2000".
- **Add figure captions.** Every figure must have a descriptive alt text
  in the markdown image reference. The caption should say what the figure
  shows, not just name it.
- **Interpret, don't just describe.** "Channels 3 and 7 show anomalously
  high low-frequency power, consistent with electrode drift" -- not
  "The plot shows the PSD."
- **Highlight key metrics.** Pull quantitative results into the Key Metrics
  table even if they also appear in the text.
- **Cross-reference mod docs.** If the notebook tests a mod's output,
  link to the mod's theory.md or spec.md.
- **Use relative paths** for figure references: `{name}/output_3_0.png`
  (relative to the report file's location in `docs/reports/`).

### 5) Optionally capture a result note

If the report reveals a finding that advances a research milestone, ask:

> "This report contains findings that could be recorded as a project-level
> result note. Would you like me to create one?"

If yes, create a result note via `note_create(note_type="result")` that
cross-references the flow report:

```yaml
refs:
  - source: "code/pipelines/<flow>/docs/reports/<name>.md"
    type: flow-report
```

This bridges flow-local reports with the project-wide result log.

## Hard rules

- Never overwrite an existing report without asking the user first.
- Never run this skill on a notebook that hasn't been executed.
- Always include figure captions (alt text) -- never bare `![](path.png)`.
- Reports are git-tracked source files, not build artifacts.
- Report figures live in `{flow}/docs/reports/{name}/`, not in any
  shared assets directory.
- The report file lives at `{flow}/docs/reports/{name}.md`, matching
  the notebook name.
- Do not include code cells in the report unless the user explicitly asks.
- Do not include all figures -- curate the most informative subset.
