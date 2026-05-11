# Handbook explorables

!!! note "Sources & anchors"
    - **Stack component:** Marimo
    - **Canonical artifact:** [example: TBD] — this chapter *creates* the first explorable (E1); no existing examples in the surveyed projects
    - **Workshop session:** Day-2 AM session 1 (preview, not hands-on)
    - **Outline:** [`_outline.md`](../_outline.md) §B §F

!!! warning "Honest gap"
    The marimo-WASM explorable format described in this chapter has **zero
    implemented examples** across all surveyed projects as of this writing.
    This chapter describes the pattern and plans the first explorable; the
    pattern is validated once the first bundle ships. See
    [99-honest-gaps.md](../99-honest-gaps.md) §4.

## Frame

`marimo export html-wasm`; embedding in mkdocs; constraints (no backend).

## The WASM export

Marimo notebooks serve a dual purpose. In the analysis workflow described in
[analysis-notebooks.md](analysis-notebooks.md), they are interactive tools
requiring a Python process to execute cells. The second role is entirely
different: a **static HTML bundle** that runs Python in the browser via
WebAssembly, with no server, no kernel, and no installation required from
the reader.

The command:

```bash
marimo export html-wasm notebooks/explore/my_notebook.py \
  -o docs/handbook/00-frame/_explorables/e1-task-graph/index.html
```

produces a self-contained `index.html` that bundles the marimo runtime, a
Pyodide-based Python interpreter, and the notebook source. A reader opens
the file in any modern browser and gets a fully reactive marimo notebook:
sliders slide, dropdowns update, cells re-run, all without leaving the page.

The output goes under `docs/handbook/<chapter-dir>/_explorables/<slug>/` per
the asset convention in [_outline.md](../_outline.md) §E.

## Embedding in mkdocs-material

The simplest embedding is a raw `<iframe>` in the chapter markdown:

```html
<iframe
  src="./_explorables/e1-task-graph/index.html"
  width="100%"
  height="600px"
  style="border: 1px solid #e0e0e0; border-radius: 4px;"
  title="E1 — Task-graph trace explorable">
</iframe>
```

mkdocs-material passes raw HTML blocks through unchanged when the
`markdown_extensions` list includes `md_in_html`. No plugin is required for
this embedding pattern. The explorable file is part of the docs source tree
(`docs/`) and is copied into the site output by the mkdocs build; no
separate deployment step.

## Constraints

WASM-exported notebooks operate under different constraints than server-backed
marimo notebooks. Understanding these constraints shapes what an explorable
can do.

**No Python backend.** All code runs client-side in Pyodide. There is no
`subprocess`, no `pathlib.Path` pointing at `/storage2/arash/projects/pixecog`,
no access to the host file system. Any data that a notebook displays must be
fetched from a URL (using `pyodide.http.open_url` or the standard `urllib`
via Pyodide's fetch bridge) or embedded directly in the notebook as a literal.

**Package availability.** Only packages that are available in Pyodide's
package registry (or installable via `micropip` at runtime) work in the
WASM context. `numpy`, `pandas`, `matplotlib`, `scipy`, and `altair` are
available. `cogpy`, `labbox`, or any package with compiled C/Fortran
extensions that lack WASM wheels are not. Explorables must be designed around
pure-Python or pre-Pyodide packages.

**Bundle size.** The initial bundle includes the marimo WASM runtime
(~2 MB) and the notebook source. Packages are fetched from a CDN at first
run. A notebook that imports `numpy` and `pandas` will trigger a ~20 MB
download on first open; subsequent opens use the browser cache. For handbook
use, keep imports minimal and lean toward `altair` (data-driven declarative
charts) over `matplotlib` (heavier) where possible. The practical cap for
acceptable cold-start time is approximately 5 MB of non-cached payload.

**No file I/O.** Reading local files (`open()`, `Path.read_text()`) fails in
the WASM context. Data must either be embedded in the notebook as a
dictionary literal or fetched from a URL. For handbook explorables that
illustrate schema or structure (rather than visualizing a dataset), embed
small synthetic examples directly. For explorables that visualize real data,
pre-export the data to a JSON or CSV file and fetch it from the published
docs URL.

## The five planned explorables

The handbook caps marimo-WASM explorables at five total (see
[_outline.md](../_outline.md) §F). Each explorable is budgeted at small (S)
or medium (M) implementation effort and lives in its host chapter:

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| **E1** | `00-frame/why-interactivity` | Task-graph trace | <!-- TODO: E1 --> planned |
| **E2** | `30-snakemake/config-driven-pipelines` | DAG explorable | <!-- TODO: E2 --> planned |
| **E3** | `60-projio/20-pipeio` | `pipeio_target_paths` interactive | <!-- TODO: E3 --> planned |
| **E4** | `70-agentic/permissions-and-bounded-context` | Permission-scope diagram | <!-- TODO: E4 --> planned |
| **E5** | `80-orchestration/goals-and-critical-path` | Goal critical-path render | <!-- TODO: E5 --> planned |

E1 and E2 are the first candidates to implement because they reuse this
session's own `idea → task → result` chain (E1) and an existing pipeline
artifact from `pixecog/code/pipelines/lfp_extrema/` (E2). Both are pure
data-visualization notebooks — no file I/O, no compiled dependencies.

<!-- TODO: E1 -->

## How to build an explorable

The workflow is:

1. **Write the notebook as a normal marimo `.py` file.** Design it around the
   WASM constraints from the start: no `pathlib` reads, no subprocess calls,
   data embedded or fetched by URL.
2. **Test it in the marimo editor** (`marimo edit notebook.py`) to verify
   the reactive logic works.
3. **Test it in a WASM-like environment** by running
   `marimo export html-wasm notebook.py -o /tmp/test.html` and opening the
   output in a browser. This is the only reliable way to catch Pyodide
   compatibility issues before publishing.
4. **Export to the chapter asset path** and commit the `index.html` to the
   docs source tree.
5. **Embed via `<iframe>`** in the chapter markdown.

Because explorable notebooks are not project-flow notebooks, they live outside
the `notebooks/` tree. The suggested location is
`docs/handbook/<chapter-dir>/_explorables/<slug>/notebook.py` for the source
and `index.html` for the built bundle. The source `.py` is kept in the repo
so the explorable can be rebuilt as marimo versions advance.

## This chapter exists before the pattern is validated

There is a deliberate sequencing honesty here: this chapter describes a
pattern that is not yet validated in any of the five surveyed projects. The
stack-axis survey (component 4, honest gap §4) notes that "marimo's second
role (handbook explorables via `marimo export html-wasm`) has zero examples
in any surveyed project." Writing this chapter before the first explorable
ships is intentional — the chapter frames the capability and the constraints
so that the workshop's Day-2 AM session can introduce the *possibility* of
explorables without promising a live demo that does not yet exist.

The first explorable (E1) is a separate implementation task
(`task-arash-20260507-222051-589638.md`). When it lands, this chapter will
update from "planned" to a concrete example with a live embed. Until then,
the constraint analysis and embedding instructions above are the chapter's
primary contribution.

## Further reading

- **[Marimo §WASM export](https://docs.marimo.io/guides/exporting.html)** — `marimo export html-wasm`; bundle size limits, supported PyPI packages, and embedding options.
- **[Pyodide](https://pyodide.org/)** — Python in WebAssembly; the runtime that powers Marimo's browser-side execution and its package availability constraints.
