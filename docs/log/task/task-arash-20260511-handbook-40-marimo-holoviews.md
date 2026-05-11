---
title: "Patch 40-marimo: add holoviews + xarray pairing section"
date: 2026-05-11
timestamp: 20260511-handbook-40-marimo-holoviews
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260511-184846-a05bd7/note.md
completed: 2026-05-11T18:48:54+02:00
actionable: true
prompt: ""
source_note: docs/handbook/_outline.md
project_primary: projio
priority: medium
due: ""
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [handbook, writing, stack-axis, agentic-workshop-2026-09, chapter-40-marimo, patch]
model_hint: sonnet
---

## Task

Add a section on **HoloViews + xarray** as the recommended exploration stack
paired with Marimo. The handbook draft of `40-marimo/analysis-notebooks.md`
landed without this content; this patch task inserts it.

User context (2026-05-11): *"I recommend holoviews to students. This pairs
well with marimo for exploration. xarray for multidimensional data pairs
well with holoviews. It's a great combo for exploration and usable via
marimo."*

## Where to add

`docs/handbook/40-marimo/analysis-notebooks.md`

Insert a new H2 section titled **"Pairing: HoloViews + xarray"** (~300–500
words). Position it after the existing sub-chapter content but before any
trailing references/cross-link section. Preserve the existing admonition
block at the top.

## Beats to cover

- **Why xarray:** N-dim labeled arrays for neuroscience data (channels × time × trials × subjects); BIDS data often loads naturally into xarray; named dimensions survive across rule chains.
- **Why HoloViews:** declarative plotting; same API across matplotlib / bokeh / plotly backends; one-line `.hvplot()` accessor on xarray DataArrays/Datasets; widget-driven exploration without per-plot boilerplate.
- **Why Marimo for both:** reactive cells mean changing one xarray slice or HoloViews param re-renders downstream; no manual figure regeneration; the trio (xarray → hvplot → reactive cell) collapses the explore-iterate loop.
- **Concrete pattern:** one short code-block example showing the loop — load BIDS data as xarray, slice via a Marimo `mo.ui` widget, render via `.hvplot.image()` or `.hvplot.line()`, watch downstream cells react.
- **Honest scope:** HoloViews is recommendation, not in projio's enforced stack; for static publication figures, fall back to matplotlib/figio (cross-link to `60-projio/40-figio-and-manuscript.md`).
- **Recommend to students explicitly** (Arash's phrasing): position this as the *exploration* stack the workshop teaches students to reach for, distinct from the *publication* stack.

## Hard rules

- **Edit only `40-marimo/analysis-notebooks.md`.** Do not touch other chapter files.
- **Preserve the existing admonition block** ("Sources & anchors") at the top.
- **No new explorables.** Do not add `<!-- TODO: Ex -->` markers.
- **Code-block example must be runnable in principle** but does not need to execute (workshop dataset isn't frozen yet); use realistic BIDS-shaped xarray.
- Build validation: `conda run -n rag python -m mkdocs build --strict` should still pass after the edit (ignore pre-existing INFO-level notio link warnings).

## Acceptance

- New H2 section "Pairing: HoloViews + xarray" inserted in `40-marimo/analysis-notebooks.md`
- 300–500 words, all six beats covered
- One short code-block example present
- Existing chapter content preserved (admonition + prior prose unchanged)
- Strict build passes
