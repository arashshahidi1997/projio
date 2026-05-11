# MkDocs for the site

!!! note "Sources & anchors"
    - **Stack component:** Quarto/MkDocs
    - **Canonical artifact:** `pixecog/mkdocs.yml`
    - **Workshop session:** Day-2 PM session 1 (publication frameworks)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Material theme; nav patching; plugin density (search/monorepo/ezlinks/bibtex).

## The right tool for the right surface

MkDocs is a static-site generator that turns a directory of Markdown files
into a navigable documentation site. The [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
theme is the standard choice across every project in this stack — projio,
cogpy, pixecog, gecog, and msol all declare `theme.name: material` in their
`mkdocs.yml`. That uniformity is not accidental: Material gives you search,
code highlighting, dark mode, admonitions, and tabbed navigation with no
configuration, and it has a plugin ecosystem that fills the remaining gaps
(bibliography, cross-repo inclusion, wiki-style links) without requiring a
custom build step.

The alternative in the stack is Quarto — covered in the [next
chapter](quarto-for-deliverables.md). The choice is straightforward once you
know what each tool optimizes for. MkDocs is the right tool when:

- the content is **evergreen documentation** that evolves with the codebase
  rather than delivered in one batch,
- contributors need to find things by navigation and search, not linear
  reading,
- the output is a **single HTML surface** — no PDF, no slides, no
  executable-cell rendering.

When any of those conditions fail — when you need multi-format output, or
executable Quarto cells, or book-style typesetting — Quarto takes over.

## Plugin layer

A bare `mkdocs.yml` with `theme.name: material` is functional but austere.
The plugin layer is where projects differentiate. The minimal working set
for a projio-managed research site is four plugins:

```yaml
plugins:
  - search
  - monorepo
  - ezlinks
  - bibtex:
      bib_file: .projio/render/compiled.bib
```

`search` is Material's built-in full-text index. `monorepo` enables the
`!include` directive in `nav:` so the top-level `mkdocs.yml` can delegate
a sub-tree to a child `mkdocs.yml` without copying nav entries — this is
how the handbook nav is wired into projio's main site
(`nav: - Handbook: '!include ./docs/handbook/mkdocs.yml'`).
`ezlinks` resolves wiki-style `[[page name]]` links to file paths, so
chapter cross-references survive folder moves without a find-and-replace.
`bibtex` renders citation keys against `.projio/render/compiled.bib` — the
file produced by `biblio_compile` — and inserts the bibliography inline.

Projects grow from this baseline as needed. `pixecog/mkdocs.yml` adds
`include-markdown` (for transclusion of file excerpts), `git-revision-date-localized`
(per-page last-modified timestamps), and `mkdocs-jupyter` (rendered notebooks).
msol's `mkdocs.yml` stays at the four-plugin minimum. Both are valid; the
plugin list is a surface for project-specific decisions, not a projio
convention.

## Nav patching and the monorepo plugin

The projio handbook you are reading is an example of `monorepo` at work.
The root `mkdocs.yml` delegates the handbook section to
`docs/handbook/mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Handbook: '!include ./docs/handbook/mkdocs.yml'
  - Tutorials: ...
```

`docs/handbook/mkdocs.yml` lists every chapter file once, under its own
`nav:` key. Any new chapter added to `docs/handbook/mkdocs.yml` appears
automatically in the published site; the root `mkdocs.yml` does not need
to change. For pipeline-generated docs — module-level reference pages
produced by `pipeio_docs_collect` — the `pipeio_mkdocs_nav_patch` MCP
tool patches `docs/handbook/mkdocs.yml` (or a project's equivalent) so
the agent does not have to manage nav entries by hand.

## The canonical example: `pixecog/mkdocs.yml`

`pixecog/mkdocs.yml` is the strongest reference in the cohort. The
relevant section:

```yaml
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - toc.integrate
    - content.code.copy

plugins:
  - ezlinks:
      wikilinks: true
  - include-markdown:
      recursive: true
  - bibtex:
      bib_file: .projio/render/compiled.bib
      csl_file: .projio/render/csl/apa.csl
  - git-revision-date-localized:
      enable_creation_date: true
      type: datetime
  - monorepo
  - search
  - mkdocs-jupyter
```

Three things worth noting. First, `wikilinks: true` in the ezlinks plugin
means `[[strict-raw-root]]` resolves to `10-bids/strict-raw-root.md`
without an explicit path — convenient once a project has enough internal
cross-links to make spelling out paths tedious. Second, the `csl_file`
key routes citation formatting through APA; the other bundled styles
(ieee, chicago-author-date, vancouver) are in `.projio/render/csl/`
after a `projio sync`. Third, `mkdocs-jupyter` is pixecog-specific —
it renders `.ipynb` files inline. Projects that use only Marimo notebooks
(`.py` files) do not need it.

## What is not in `mkdocs.yml`

MkDocs is deliberately not wired to run pipeline scripts, render Quarto
cells, or manage bibliography compilation. Those concerns live upstream:
`biblio_compile` produces `compiled.bib` before `mkdocs build` runs;
`pipeio_docs_collect` produces module reference pages before the nav is
patched; `figio_build` produces SVG figures before they are embedded.
The MkDocs build step is the last mile, not the production system.

If you find yourself writing a custom MkDocs plugin to run a computation
during the build, that computation belongs in a Snakemake rule or a
projio MCP tool instead. MkDocs builds should be reproducible from a cold
clone without a running database, kernel, or agent.

## Further reading

- **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** — theme reference; navigation, admonitions, search, social cards, and the full plugin list.
- **[MkDocs documentation](https://www.mkdocs.org/)** — `nav:` structure, `mkdocs.yml`, custom hooks, and deployment to GitHub Pages.
