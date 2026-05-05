# Presentio Design Spec

**Status:** Draft
**Date:** 2026-04-13
**Package:** TBD — either `notio.present` (subpackage, mirrors `notio.manuscript`) or standalone `packages/presentio/`
**Working name:** presentio

## Motivation

Research presentations — journal clubs, conference talks, lab meetings,
progress reports, thesis defenses — are currently a gap in the projio
ecosystem. Today:

- [biblio/present.py](https://github.com/arashshahidi1997/biblio/blob/master/src/biblio/present.py) can
  generate a single-paper Marp deck via LLM from docling output. Useful
  seed, but one-shot and paper-scoped.
- Notio/manuscript owns the pandoc+citeproc+Lua filter stack used for
  papers, but has no notion of slides.
- Figio produces publication figures; they can't be consumed by a deck
  without manual path plumbing.
- Worklog holds the cross-project briefing data that a progress report
  would need; no path from it to a deck exists.
- Cross-project reuse (e.g. a pixecog talk that embeds projio ecosystem
  slides) is unsupported.

The goal is not to **generate decks in one shot**. The goal is to make
decks **iteratable artifacts** — first-class projio objects that agents
and humans co-edit slide-by-slide, assembled from the same knowledge
layers (papers, figures, notes, code, cross-project material) that the
rest of projio already exposes.

## Design Principles

1. **Decks are artifacts, not outputs.** Like manuscripts: a YAML spec +
   a section tree + a render pipeline. Agents iterate; they don't
   one-shot.
2. **Sections are notes.** Each slide (or slide group) is a markdown
   file with frontmatter, addressable through the existing notio
   infrastructure. Reuses templates, indexing, search.
3. **Reuse is by reference, not copy.** A slide from another project is
   pulled in via worklog-mediated path resolution, not duplicated.
   Frozen snapshots are opt-in.
4. **Multiple backends, one source.** The same deck source should build
   Marp, reveal.js, and pptx. Backend is per-deck, declared in the
   spec, dispatched at render time.
5. **Figures come from figio, citations from biblio.** No parallel
   infrastructure. `present_figure_insert` mirrors
   `manuscript_figure_insert`; citations resolve against the project's
   existing compiled.bib.
6. **The repo is the unit of knowledge.** Decks live in-repo,
   git-tracked, versioned. Google Slides is an *export target*, never a
   source format.
7. **Agent-first ergonomics.** Every operation has an MCP tool. Every
   iteration loop is a skill. No CLI-only features.

## Critical tensions (worth being explicit about)

These are the design decisions I'm *least* certain about. Calling them
out so the spec review can push back.

### 1. Subpackage vs standalone

Manuscript is a notio subpackage because sections *are* notes. Slides
are section-like too — same argument applies, and `notio.present` would
inherit note infrastructure for free. But presentations pull from a
**wider** surface (figio, biblio, worklog, cross-project) than
manuscripts typically do, and a standalone `presentio` package would be
more discoverable in the ecosystem table.

**Recommendation:** start as `notio.present` subpackage. Promote to
standalone only if it accretes enough surface to justify the split
(same rule biblio and figio earned).

### 2. Marp + reveal.js dual-backend tax

Supporting two renderers from day one sounds expensive. It isn't —
*reveal.js-via-pandoc is nearly free* because notio/manuscript already
owns the pandoc+citeproc+Lua filter stack. Marp is the separate
toolchain, and it's the one we already have partial code for. Refusing
one forces ergonomic compromises:

- Marp-only ⇒ weak citeproc, no reuse of render.yml, can't embed
  interactive figio HTML.
- Reveal-only ⇒ no pptx export path, heavier toolchain for simple
  lab-meeting decks, agent edits feel more indirect.

**Recommendation:** both, chosen per-deck via `format: marp|revealjs` in
the spec, same pattern as notebook.yml (jupytext vs marimo).

### 3. Slide granularity

Three options for how sections map to slides:

- **One file per slide** — maximal agent ergonomics (surgical edits,
  trivial reuse), but filesystem-heavy and order management becomes
  painful at >30 slides.
- **One file per section** (intro, methods, results...) — pandoc-style,
  matches how humans think about talks, but agent edits touch larger
  blobs.
- **Free-form with `---` separators inside files** — what Marp wants
  natively, but breaks reuse of individual slides.

**Recommendation:** one file per *section*, with `---` slide separators
*within* a section file. Section = the unit of semantic grouping and
reuse; slide = a rendering detail. Matches manuscript's mental model
(sections are the primary object) and still lets reveal.js/Marp split
at `---`.

### 4. Cross-project figure and citation resolution

If pixecog's deck imports a projio section that cites `@smith2024` and
uses figure `fig-architecture`:

- **Citations**: the imported section carries `@smith2024` as a literal
  string. pixecog's `compiled.bib` must contain that entry, or the
  import helper must copy it across (`biblio_ingest` on the imported
  citekeys). Cleanest: on import, walk the section, extract citekeys,
  auto-`biblio_ingest` in the target project.
- **Figures**: two options. (a) Rewrite figure paths to
  `{project}:{figure_id}` at import and resolve at render time via
  worklog. (b) Copy/symlink the figure files into the importing
  project. (a) is more projio-philosophical (reference, not copy) but
  brittle if the source project changes. (b) is safer but
  duplicates.

**Recommendation:** (a) with an explicit "freeze" operation that
converts to (b) when you want a stable snapshot for a talk you're about
to give. Default is reference; freezing is a deliberate act.

### 5. Google Slides integration

Tempting to support, but there's no round-trip path that preserves git
as source of truth. Any collaborative edit in the web UI is lost unless
manually mirrored back.

**Recommendation:** export-only. `present_build --format pptx` → user
uploads manually, or a thin `present_publish_gslides` that uses Drive
API to upload + return a link. No pull-back. Document loudly that
edits in Google Slides do not flow back.

## DeckSpec schema

```yaml
# docs/deliverables/presentations/<name>/deck.yml
name: projio-ecosystem-intro
title: "Projio: a project-centric research environment"
author: Arash Shahidi
date: 2026-04-24
venue: lab-meeting

format: marp  # or revealjs
theme: default
ratio: 16:9

# Bibliography and citation style inherited from .projio/render.yml by
# default. Override only if this deck needs a different style.
bibliography: null
csl: null

sections:
  - id: intro
    order: 10
    path: sections/intro.md
  - id: ecosystem
    order: 20
    path: sections/ecosystem.md
  - id: demo
    order: 30
    path: sections/demo.md
    # Import a section from another project via worklog
    import:
      from_project: pixecog
      deck: thesis-defense
      section: methods-overview
      mode: reference  # or: freeze
  - id: closing
    order: 40
    path: sections/closing.md

figures:
  - id: fig-architecture
    source: figio        # rendered by figio in this project
    figure: architecture
  - id: fig-pixecog-results
    source: worklog      # pulled from another project
    project: pixecog
    figure: main-results
    mode: reference

speaker_notes: true
outputs:
  - format: html
    path: build/deck.html
  - format: pdf
    path: build/deck.pdf
  - format: pptx
    path: build/deck.pptx
```

Section files are plain markdown with Marp/reveal-compatible `---`
separators between slides. Frontmatter on each section file carries
notio-compatible fields (`title`, `tags`, `created`) so notio indexing
and search work for free.

## MCP tool surface

Mirrors the manuscript surface closely.

| Tool | Purpose |
|------|---------|
| `present_init(name, format, template)` | Scaffold a new deck: deck.yml + sections/ |
| `present_list()` | List decks in the project |
| `present_status(name)` | Section count, missing figures/citations, last build |
| `present_section_context(name, section)` | Return section + resolved figures + citations |
| `present_section_import(name, from_project, source_deck, section, mode)` | Cross-project import |
| `present_figure_insert(name, figure_id, section)` | Route a figio figure into a section |
| `present_assemble(name)` | Concatenate sections → single intermediate markdown |
| `present_build(name, format?)` | Render via marp-cli or pandoc/revealjs; write outputs |
| `present_validate(name)` | Check refs resolve, figures exist, citations in bib, slide count sane |
| `present_diff(name, since)` | Diff against last build or a git ref |
| `present_cite_check(name)` | Like manuscript_cite_check — confirm all citekeys resolve |
| `present_freeze(name, section?)` | Convert `reference` imports to `freeze` (copy files in) |
| `present_overview(name)` | One-shot: spec + section list + outline headers |

Seed command: wrap existing `biblio present` as `present_seed_from_paper(name, citekey, template)` — pulls the existing LLM Marp output into a new deck as a starting section, rather than being the whole deck.

## Skills

Skills are where the "not one-shot" philosophy lives. Each one is an
iteration loop, not a button.

- **`literature-presentation`** — build an intro deck from a set of
  papers. Loop: `biblio_ingest` missing → `paper_context` each →
  outline proposal → human approves → draft one section at a time →
  `present_cite_check` → `present_build`.
- **`progress-report`** — build a status deck from worklog data. Loop:
  `list_projects` → `goal_milestones` → `list_sessions` for the
  window → classify into narrative buckets → draft sections → import
  any relevant figures from other projects → build.
- **`deck-import`** — pull a section from another project into the
  current deck. Loop: resolve source via `worklog_read_file` →
  extract citekeys → `biblio_ingest` into current project → copy or
  reference figures → write import block to deck.yml.
- **`conference-talk-rehearsal`** — structural review of an existing
  deck: slide count budget, timing estimate, speaker-notes coverage,
  citation density, figure legibility check via
  `figio_query_output`.
- **`journal-club-deck`** — thin wrapper around `present_seed_from_paper`
  with a post-seed iteration loop for slide refinement.

## Build pipeline

### Marp backend
1. `present_assemble` concatenates section files in order, prepends
   computed Marp frontmatter from deck.yml.
2. Citations pre-resolved: a preprocessing pass replaces `@key` with
   rendered form using biblio's citeproc (not Marp's job).
3. Figure paths rewritten to absolute or resolved via worklog for
   cross-project references.
4. `marp-cli` invoked for html/pdf/pptx.

### Reveal.js backend
1. Assembly identical.
2. Pandoc invoked with `-t revealjs`, inheriting `.projio/render.yml`:
   same CSL, same compiled.bib, same Lua filter.
3. Output is a standalone html bundle, servable via `site_serve`.

### pptx export
- From Marp: `marp-cli --pptx` (native).
- From revealjs: not worth supporting directly. If pptx is needed,
  declare `format: marp` for that deck.

## Figio integration

`present_figure_insert` is a thin wrapper that:
1. Calls `figio_build(figure_id)` if the figure isn't current.
2. Resolves the output path (SVG preferred for reveal, PNG for pptx).
3. Writes the figure block into the target section with appropriate
   syntax for the deck's format.
4. Records the mapping in deck.yml `figures:` for later re-resolution.

Cross-project figures use the same tool with a `project=` argument;
resolution goes through worklog.

## Biblio integration

- Citations in section files use standard pandoc `@key` syntax, same
  as manuscripts.
- `present_cite_check` walks all section files, extracts citekeys,
  resolves each via `citekey_resolve`.
- Marp backend runs a pre-render citeproc pass (since Marp itself has
  no citation support).
- Reveal backend gets citeproc for free via pandoc.
- On cross-project import, the import helper auto-runs `biblio_ingest`
  in the target project for any citekey present in the imported
  section but missing from the target's compiled.bib.

## Worklog integration

Decks don't need a new worklog surface. They use what exists:

- `worklog_read_file(project, path)` — fetch section files across
  projects.
- `worklog_search(query)` — find material for content.
- `list_projects`, `get_project`, `goal_milestones`, `list_sessions` —
  source data for progress reports.

The `progress-report` skill is the glue; no new worklog tools required
for v1.

## Filesystem layout

```
docs/deliverables/presentations/
  <name>/
    deck.yml
    sections/
      intro.md
      ecosystem.md
      demo.md
      closing.md
    figures/           # local figure refs or frozen copies
    build/
      deck.html
      deck.pdf
      deck.pptx
```

Build artifacts gitignored. `deck.yml` + `sections/` + `figures/` (when
frozen) are tracked.

## Out of scope (v1)

- Google Slides round-trip. Export-only, or not at all.
- Timing / rehearsal analytics beyond static slide-count estimates.
- Auto-layout optimization (slide-overflow detection is future work).
- Multi-author concurrent editing (git handles it; no locking).
- Slide-level branching for variant decks (short/long versions). Use
  conditional sections or separate deck.yml files.

## Open questions

1. **Where does `biblio present` live after presentio exists?** Retire
   it, or keep as a thin `present_seed_from_paper` backend?
   *Leaning retire, re-expose through presentio.*
2. **Do we need a presentio registry** (like codio's catalog) for
   cross-project deck discovery, or is `worklog_search` enough?
   *Leaning worklog_search — registries should earn their keep.*
3. **Should section files be under `notes/` proper** (so notio
   indexing picks them up without extra config) or under
   `docs/deliverables/presentations/<name>/sections/` (so they're co-located with
   the deck)? *Leaning co-located; notio can be told to index the
   additional directory via config.*
4. **Reveal.js plugin surface** — chalkboard, highlight, math. How
   much does deck.yml expose vs. what goes in a project-level
   `.projio/present.yml` analogous to render.yml?
5. **Speaker notes as separate files vs. HTML comments inline** — HTML
   comments are simpler; separate files survive format changes better.

## Phased implementation

**Phase 1 — minimal artifact + Marp build**
- DeckSpec schema, loader, validator.
- `present_init`, `present_list`, `present_status`,
  `present_assemble`, `present_build` (Marp only).
- Retire `biblio present` → reimplement as `present_seed_from_paper`.
- One skill: `journal-club-deck`.

**Phase 2 — iteration ergonomics**
- `present_section_context`, `present_figure_insert`,
  `present_cite_check`, `present_validate`, `present_diff`.
- Skill: `literature-presentation`.

**Phase 3 — reveal.js backend**
- Pandoc-based render path reusing render.yml.
- `site_serve` integration to preview decks on mkdocs.

**Phase 4 — cross-project**
- `present_section_import`, `present_freeze`.
- Worklog-mediated figure resolution.
- Skill: `deck-import`, `progress-report`.

**Phase 5 — polish**
- pptx export, rehearsal skill, validator heuristics, speaker-notes
  coverage checks.

## Success criteria

- An agent can produce a 10-slide journal-club deck from a citekey
  with ≤5 iterations (seed → refine outline → refine 3 key slides →
  build).
- A progress report deck can be generated from worklog data with the
  human reviewing outline + one slide at a time, no one-shot
  generation.
- A projio ecosystem section from the projio repo can be imported
  into a pixecog talk with one `present_section_import` call, citations
  auto-resolve, figures render at build time.
- Both Marp and reveal.js builds succeed from the same section source
  for a representative deck.
