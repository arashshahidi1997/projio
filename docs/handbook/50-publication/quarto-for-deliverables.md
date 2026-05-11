# Quarto for deliverables

!!! note "Sources & anchors"
    - **Stack component:** Quarto/MkDocs
    - **Canonical artifact:** `projio/.projio/render/quarto.yml` + one `docs/deliverables/reports/*.qmd`
    - **Workshop session:** Day-2 PM session 1 (publication frameworks)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

`.qmd` reports; `.projio/render/quarto.yml`; per-deliverable rendering.

## What Quarto solves that MkDocs does not

MkDocs builds a docs site. Quarto builds *deliverables* — the things you
hand to someone once, whether that means a progress report, a workshop
handout, or a set of slides. The decisive difference is not cosmetic.
Quarto can render a single `.qmd` source file to multiple output formats
simultaneously: a standalone HTML page, a PDF via LaTeX, a revealjs slide
deck, and an interactive executable notebook are all legal outputs from
the same source. MkDocs can do none of those.

The second difference is execution. A `.qmd` file can contain Python (or R)
code cells that are run during the render; their outputs — figures, tables,
printed values — are captured inline. MkDocs never runs code; it only
processes already-static Markdown. For a report that needs to re-run an
analysis and embed the results at build time, Quarto is the only option in
this stack.

The third difference is typographic. Quarto's LaTeX route produces
publication-quality PDFs with proper cross-reference numbering, bibliography
formatting, and figure captions. A MkDocs `print:` output is passable for
internal notes; it is not a submission-ready manuscript.

## `.qmd` file structure

A Quarto document is a plain Markdown file with YAML frontmatter that
declares the output format (or formats) and any rendering options. Executable
Python cells are annotated as `python` code fences with `{python}` as the
language tag. A minimal report looks like:

```qmd
---
title: "LFP extrema: pilot analysis"
author: "Arash Shahidi"
date: "2026-04-15"
format:
  html:
    embed-resources: true
    toc: true
  pdf:
    documentclass: article
bibliography: .projio/render/compiled.bib
csl: .projio/render/csl/apa.csl
---

## Overview

This report summarizes the pilot run of the `lfp_extrema` flow on subject 01.

```{python}
import pandas as pd
results = pd.read_csv("derivatives/lfp_extrema/sub-01/results.csv")
results.describe()
```
```

The `embed-resources: true` flag for HTML output bakes all assets
(images, CSS, JavaScript) into a single self-contained file. Without it,
the HTML output depends on a local directory of supporting files —
inconvenient for sharing. The PDF output needs no such flag; LaTeX handles
asset embedding natively.

The `bibliography` and `csl` keys point to `.projio/render/compiled.bib`
and a CSL style file — the same files used by the MkDocs bibtex plugin.
This is intentional: one bibliography source serves both the site and
the deliverables.

## `.projio/render/quarto.yml`

The projio convention for Quarto deliverables is a thin `quarto.yml` at
`.projio/render/quarto.yml` that acts as a runtime guard:

```yaml
# Projio Quarto defaults for docs/deliverables/reports/*.qmd.
# CSL + bibliography inherit from .projio/render.yml via report.qmd frontmatter;
# report_build enforces min_version as a runtime check.
min_version: "1.5"
```

This is intentionally minimal. The per-deliverable rendering configuration —
format, bibliography path, CSL, figure settings — lives in each `.qmd`
file's frontmatter, not in a shared defaults file. The rationale is that
deliverables diverge: a 5-minute revealjs deck needs different rendering
options than a 20-page technical report, and forcing both through a shared
defaults file produces friction rather than consistency.

What `quarto.yml` *does* guarantee is that `report_build` — the MCP tool
that drives `quarto render` — refuses to proceed if the installed Quarto
version is older than `min_version`. Quarto's `.qmd` format has changed
enough across minor versions (especially around the revealjs and Typst
backends) that a silent version mismatch produces wrong output without a
clear error message. The version guard surfaces the problem at build time.

## The multi-output decision for the workshop

The workshop itself — the 4-day course package that this handbook
accompanies — is the most direct application of Quarto's multi-output
capability. A single `.qmd` handout can render to:

- **HTML** for the course website (readable before, during, and after the
  session),
- **revealjs slides** for the instructor's projected view, and
- **PDF** for participants who prefer a printed reference.

This is not hypothetical. The `docs/deliverables/presentations/projio-5min/slides.qmd`
file demonstrates the pattern: YAML frontmatter declares `format: revealjs`
with `embed-resources: true`, and the file renders to a fully self-contained
slide deck with no external dependencies. A workshop handout using `format:
html` + `format: revealjs` + `format: pdf` in the same frontmatter block
produces all three from one source.

The practical constraint is that multi-output rendering takes longer and
requires all output backends to be installed (Quarto + TeX for PDF). For
iteration during writing, rendering only HTML (`quarto render handout.qmd
--to html`) is faster and sufficient. The full multi-output render is run
as a final build step, not during drafting.

## What projio contributes

Beyond the version guard, projio's role in Quarto rendering is
coordination, not execution. The `report_build` MCP tool:

1. Checks the `min_version` constraint from `.projio/render/quarto.yml`.
2. Resolves the path to the `.qmd` file from `docs/deliverables/`.
3. Calls `quarto render` with the appropriate target and format flags.
4. Reports the output path back to the agent.

The agent does not need to know where Quarto is installed or what
command-line flags `quarto render` accepts; `report_build` encapsulates
that. This is consistent with the broader projio pattern: the MCP tool
is the agent's interface; the underlying CLI tool is an implementation
detail.

## When Quarto is the right tool

Quarto is appropriate when:

- the output must be **handed off** (report, slides, book chapter) rather
  than browsed in a docs site,
- the content includes **executable cells** whose output needs to be captured
  at render time,
- **multi-format output** from one source is required (HTML + PDF + slides),
- or **LaTeX-quality typesetting** — cross-reference numbering, theorem
  environments, proper figure captions — is needed.

When none of those apply — the content is evergreen documentation that lives
on the site alongside the codebase — MkDocs is faster and requires fewer
dependencies. The two tools are complements, not competitors. See
[Two surfaces, one cross-link protocol](two-surfaces-one-cross-link-protocol.md)
for how the handoff between surfaces is managed.

## Further reading

- **[Quarto documentation](https://quarto.org/docs/)** — formats (`html`, `pdf`, `revealjs`, `docx`), YAML front-matter, and `_quarto.yml` project files.
- **[Quarto revealjs guide](https://quarto.org/docs/presentations/revealjs/)** — slide transitions, incremental lists, fragment animations, and code-block highlighting.
