# Build a Quarto-powered executable report

Goal: scaffold and render a deliverable report that re-executes against
current state — questio questions, recent result notes, pipeio flow
status, and labeled cells from your analysis notebooks.

For background on why reports are reactive while result notes are
atomic, see the [delegation model](../explanation/delegation-model.md)
and the [quarto-reports spec](../specs/quarto-reports.md).

## Prerequisites

- Quarto on `PATH` — install via `pixi global install quarto`, or
  ensure `~/.pixi/bin/pandoc` and `quarto` are reachable
- A projio workspace (`projio init` already run)
- Optional: at least one executed pipeio notebook to embed (Quarto's
  `{{< embed >}}` shortcode pulls labeled cells from `.ipynb` outputs)

## Scaffold

```python
# via the projio MCP server
report_init(name="weekly-2026-05-04", template="progress")
```

This writes `docs/deliverables/reports/weekly-2026-05-04/report.qmd`
with frontmatter pre-populated from current questio state, recent
`result` notes, and the pipeio flow registry. The three templates
(`progress`, `update`, `milestone`) differ only in their starter section
headings — pick by audience cadence, not by feature set.

The CLI equivalent is on the roadmap; for now use the MCP tool from
inside Claude Code or via `mcp__projio__report_init` from any MCP
client.

## Embed a notebook figure

Reports pull figures **directly from executed notebooks**, no figio
intermediate. The Quarto `embed` shortcode:

```markdown
## Spindle density across age

{{< embed ../../../code/pipelines/detect_swr/notebooks/spindle-analysis.ipynb#fig-spindle-density-age >}}

Across N=18 subjects, spindle density showed a significant negative
correlation (r=-0.42, p=0.003) with subject age during NREM sleep.
```

Three preconditions, all checked by `report_build`'s preflight:

- The notebook exists and is `.ipynb` (jupytext percent-format counts —
  pipeio executes those into `.ipynb` artifacts; pure marimo doesn't,
  see [fallback](#fallback-exported-figure-files))
- The notebook has been executed via `pipeio_nb_exec` so cell outputs
  are cached in the `.ipynb` JSON
- The cell has a label: add `#| label: fig-spindle-density-age` to the
  code chunk header

The embed pulls **cached cell output** — re-rendering the report does
not re-execute the notebook. Freshness is tied to when
`pipeio_nb_exec` last ran, which is the right coupling.

### Fallback: exported figure files

For marimo notebooks (Quarto can't embed those — `embed` requires
`.ipynb`) or for ad-hoc analyses without a pipeio flow, use
`pipeio_nb_extract` to write labeled figures to PNG/SVG, then embed
the file directly:

```markdown
![Spindle density by age](../figures/fig-spindle-density-age.png)
```

This loses the single-source-of-truth property (the file can drift from
notebook code) but preserves report portability — a six-month-old
report still renders even if the notebook is gone.

## Build

```python
report_build(name="weekly-2026-05-04", format="html")
```

Execution chain:

1. **Preflight** — verifies every `{{< embed >}}` target exists and
   resolves; checks every `![](path)` path; checks bibliography
   resolves (when the report cites anything)
2. **Runner resolution** — picks the Quarto binary via
   `code.envs.report` → `code.envs.default` → `PATH` → known fallback
   locations, mirroring the snakemake/pandoc resolution chain
3. **Version check** — `quarto --version` against
   `.projio/render/quarto.yml`'s `min_version` (defaults to 1.5)
4. **Render** — `quarto render report.qmd --to html` inside the
   project's compute env (`pixi run`/`conda run`, depending on
   `code.runner`)

Output lands at
`docs/deliverables/reports/weekly-2026-05-04/build/report.html`.
Open in any browser.

## Iterate

`_freeze/` and `_files/` are gitignored — `quarto render` re-uses cached
cell outputs across runs, so subsequent renders are sub-second. Edit
the `.qmd`, re-run `report_build`, refresh the browser.

If you want a fresh re-execution, delete `_freeze/<report-name>/` and
re-render.

## What reports do *not* do

Per the [delegation model](../explanation/delegation-model.md):

- **No analysis logic.** Reports embed cells; they don't re-implement
  analysis. If you find yourself writing pandas in a `.qmd`, that
  belongs in a notebook.
- **No figio integration.** Reports carry preliminary figures.
  Composed, publication-ready figures live in figio and flow into
  manuscripts and decks via a one-way promotion door.
- **No cross-project embeds yet.** Phase 2 of the spec sketches
  `report_import_notebook(from_project, ...)` — analogous to
  `present_section_import` for decks. Not landed.

## Empty bibliography

If your report has no citations (`@key` markers), the preflight may
still complain about a missing `compiled.bib`. The fix [is filed as a
known edge case](../log/issue/index.md) — the workaround until it
lands: drop the `bibliography:` line from the `.qmd` frontmatter, or
create an empty `compiled.bib`.

## Related

- [Quarto reports spec](../specs/quarto-reports.md) — design rationale,
  resolved decisions
- [Delegation model](../explanation/delegation-model.md) — why reports
  embed raw notebook outputs and not figio figures
- [Pipeio notebook lifecycle](../specs/pipeio/notebook.md) — how
  notebooks get executed and cached
