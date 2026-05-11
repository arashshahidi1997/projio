# figio + manuscript

!!! note "Sources & anchors"
    - **Stack component:** projio
    - **Canonical artifact:** `gecog`'s `2026-05-02-mlclassifier-cohort-figs/figurespec.yaml` (1 first-party FigureSpec across the cohort)
    - **Workshop session:** Day-3 AM session 2 sidebar
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

FigureSpec YAML for composed multi-panel figures; an honest *mostly
aspirational* note about adoption; the manuscript subsystem listed but
not taught as mature.

## The intent

A paper figure is rarely a single rendered image. It is more often a
composition: several panels produced by different rules, each from a
different upstream pipeline output, arranged on a canvas with shared
typography, exported as both an editor-friendly SVG and a
publication-ready PDF. The status quo is a one-off Python script per
report that loads the panels, calls matplotlib with the right
spacing, and dumps a PDF. The script lives next to the report, gets
copied into the next report, drifts, and dies.

**figio** is projio's attempt at a declarative answer. A
*FigureSpec* is a YAML file that lists the panels, their data
sources, the layout, and the export targets. `figio_build(figure_id)`
reads the spec, dispatches the panel renderers, composes the SVG,
and writes the export bundle. The figure becomes a *first-class
deliverable* — versioned, reproducible, queryable — instead of a
side-effect of whichever report needed it last.

## The MCP surface

The figio tool set is small and orthogonal:

- `figio_figure_list()` enumerates the registered FigureSpecs.
- `figio_inspect(figure_id)` returns a spec's panels, dependencies,
  and current build state.
- `figio_build(figure_id)` runs the build.
- `figio_validate(figure_id)` checks the spec for missing inputs,
  unresolved panel references, and broken cross-links.
- `figio_edit_spec(figure_id, patch)` applies a structured patch to
  the YAML.
- `figio_query_output(figure_id, query)` introspects the rendered
  SVG (e.g. "what panel is at coordinate X?").

The pattern is familiar from pipeio: a registry of named entities,
addressed by id, queried and mutated through MCP rather than by
hand-editing files.

## The honest gap

The stack-axis survey records *one first-party FigureSpec across all
four study projects*: `gecog`'s May-02 mlclassifier cohort figure.
Everywhere else — pixecog, msol, cogpy — figures live in ad-hoc
`<report>-figs/` directories next to the reports that consume them,
built by hand-written Python scripts. figio is, in cohort terms,
**mostly aspirational**: the tool exists, the convention exists, the
MCP surface exists, but the cohort has not yet adopted it at scale.

The workshop introduces figio as a *direction* rather than as a
baseline practice. The single gecog FigureSpec is used as the
canonical teaching artifact precisely because there is only one — the
contrast between figio's expressed intent and the cohort's actual
state is itself instructive. See [Honest gaps](../99-honest-gaps.md)
§7 for the longer framing.

## When to reach for figio vs. an ad-hoc script

The graduated criterion the cohort agreed on:

- **One-off chapter illustrations, screenshot grids, architecture
  diagrams**: hand-author SVG / PNG under
  `docs/handbook/<chapter-dir>/_assets/`. Do not invoke figio for
  these. The asset-conventions table in
  [`_outline.md`](../_outline.md) §E codifies this.
- **One-off report-specific panels** that won't be reused: a plain
  Python script next to the report, producing a PNG or SVG. This is
  the *current* cohort practice; it is honest and pragmatic for a
  single use.
- **Cross-report, multi-panel composed figures** with shared
  typography and multiple export targets: this is what figio is
  *for*. Until a figure crosses the reuse threshold, the ad-hoc
  script is the right tool.

The graduated framing keeps figio from being a premature dependency:
it earns its complexity by being the right tool for the case where
the alternatives genuinely fail.

## The manuscript subsystem

The manuscript subsystem under `notio.manuscript` exposes a parallel
surface: `manuscript_init`, `manuscript_list`, `manuscript_assemble`,
`manuscript_build`, `manuscript_cite_check`, `manuscript_validate`,
`manuscript_figure_insert`, `manuscript_section_context`,
`manuscript_overview`. The conceptual model is that a manuscript is
an ordered set of section notes (`docs/notes/...` or
`docs/manuscripts/<name>/sections/`) assembled by pandoc into a
final document, with citations resolved against
[`compiled.bib`](30-biblio-indexio.md) and figures resolved against
the figio output bundle.

The honest cohort framing, from the stack-axis survey, is that
`manuscript_list` returns `[]` across the cohort — no project
currently uses the manuscript subsystem in earnest. The convention
is in place; the adoption is not. The workshop introduces
`manuscript_*` as a *listed* subsystem ("here is how it would fit
together with figio and biblio") but **does not teach it as mature**
and does not include manuscript drafting in any workshop session.

The forward-looking story is that figio + biblio + manuscript
together close the production pipeline: figures composed
declaratively, citations resolved from extracted PDF text, sections
assembled into pandoc. When the cohort adopts it, the chapter will
need a substantial rewrite. Until then this section is a placeholder
for what the layer *will* be, surfaced honestly so workshop
participants do not infer maturity that does not yet exist.

## What follows

The last subsystem chapter — [codio](50-codio.md) — closes the
six-subsystem map with the code-catalog story. The agentic chapters
that follow ([70-agentic](../70-agentic/claude-code-and-mcp.md))
return to the figio/manuscript story from a different angle: how an
agent given a FigureSpec and a target manuscript section *uses*
these subsystems together. The honest gaps for both figio and
manuscript are catalogued in [99-honest-gaps.md](../99-honest-gaps.md).

## Further reading

- **[Pandoc user manual](https://pandoc.org/MANUAL.html)** — `--citeproc`, `--bibliography`, Lua filter interface, and all output format options used by `manuscript_build`.
- **[Citation Style Language](https://citationstyles.org/)** — CSL spec; the APA, IEEE, Chicago, and Vancouver styles bundled by projio are drawn from this repository.
