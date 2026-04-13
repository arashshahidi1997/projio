# Presentio: Iterating a Deck Section-by-Section

This tutorial walks through building a research presentation deck from scratch with presentio. The workflow is deliberately **iterative**, not one-shot: you scaffold a deck, draft sections one at a time with the agent as a collaborator, and build Marp or reveal.js output from the same source files.

By the end, you will have a minimal deck that:

- Lives at `docs/presentations/smoketest/`
- Contains a scaffolded section tree with editable markdown stubs
- Builds to HTML via marp-cli (or reveal.js via pandoc)
- Can be validated, diffed, and iterated without leaving the MCP tool surface

## Prerequisites

- A projio workspace (`projio init .` already run)
- notio package installed (`notio.present` is a subpackage of notio)
- For Marp builds: `marp-cli` on PATH — install with `npm install -g @marp-team/marp-cli`
- For reveal.js builds: `pandoc` ≥ 2.19 on PATH
- Optional: a configured bibliography (`bib/srcbib/*.bib`) if you want citations in the output

All commands below use projio MCP tools. The agent invokes them directly; this tutorial shows them as pseudo-calls.

## 1. Scaffold the deck

```text
present_init(
  name="smoketest",
  format="marp",
  template="lab-meeting",
  title="Phase 1 Smoketest"
)
```

This creates:

```
docs/presentations/smoketest/
├── deck.yml               # DeckSpec manifest
├── sections/
│   ├── title.md           # scaffolded stubs, one per template section
│   ├── context.md
│   ├── approach.md
│   ├── results.md
│   └── next-steps.md
```

Each section file is a markdown stub with notio-compatible frontmatter so notio indexing can pick it up:

```markdown
---
title: "Context"
order: 20
deck: smoketest
status: draft
tags: [presentation, section]
---

# Context
```

Four templates ship today:

| Template | Sections | Best for |
|----------|----------|----------|
| `lab-meeting` | 5 | Internal lab updates, informal framing |
| `journal-club` | 6 | Single-paper deep-dive |
| `conference-talk` | 8 | Formal talk with related work + contributions |
| `progress-report` | 5 | Weekly / biweekly status reports |

???+ info "MCP tools touched in step 1"

    | Tool | Purpose |
    |------|---------|
    | `present_init` | Create deck.yml and scaffolded section stubs |
    | `present_list` | Enumerate all decks under `docs/presentations/` |

    Full reference: [Presentation tools](../reference/mcp-tools.md#presentation-tools-via-notiopresent).

## 2. Draft the first section with context

The agent should never edit a section blind. Always gather context first:

```text
present_section_context(name="smoketest", section="title")
```

This returns a single JSON blob with:

- `current_content` — the section body with frontmatter stripped
- `frontmatter` — the parsed YAML header
- `word_count`, `slide_breaks` — quick structural stats
- `citations_used` — every `@citekey` already in the body
- `figures_referenced` — every `fig:<id>` placeholder already in the body
- `figures` — all figures declared in `deck.yml` with per-figure built status
- `rag_hits` — RAG query results seeded from the section key + deck title
- `related_notes` — semantic search over the project's notes directory

Using this context, draft the section. Keep to 1–3 slides. Use `---` on a line by itself inside the section file to split within a section:

```markdown
---
title: Title
order: 10
---

# Phase 1 Smoketest

_A minimal deck to exercise the presentio pipeline_

---

# Why

Presentio treats decks as iteratable artifacts, not LLM one-shots.
```

The inter-section `---` separators are added automatically by `assemble_marp`. The intra-section `---` you write yourself creates extra slides within the section.

???+ info "MCP tools touched in step 2"

    | Tool | Purpose |
    |------|---------|
    | `present_section_context` | Gather everything needed to draft a section in one call |
    | `present_figure_insert` | Insert a `fig:<id>` placeholder and register the figure |

## 3. Insert figures from figio

Suppose you have a figio figure called `fig-architecture` already built. Insert it into the context section:

```text
present_figure_insert(
  name="smoketest",
  section="context",
  figure_id="fig-architecture",
  position="end"
)
```

This does two things:

1. Appends `![<caption>](fig:fig-architecture)` to `sections/context.md`
2. Adds a new entry to `deck.yml` under `figures:` if not already present

The `fig:<id>` placeholder is resolved to the real file path at assembly time by `resolve_figure_paths`, with format-aware extension preference:

| Format | Preference | Fallback |
|--------|------------|----------|
| Marp | `png` | `svg` → `pdf` |
| reveal.js | `svg` | `png` → `pdf` |
| pptx (future) | `png` | `svg` → `pdf` |

If a figure is not built yet, `present_validate` reports it as an unresolved figure in warnings and you can run `figio_build(figure_id="fig-architecture")` before building the deck.

## 4. Cite-check before the first build

If your section bodies contain pandoc citation markers like `[@smith2024]` or `[@smith2024; @jones2023]`, run cite-check to confirm every key resolves against the inherited bibliography:

```text
present_cite_check(name="smoketest")
```

This returns:

- `found` — citekeys present in `bib/main.bib`, with docling fulltext status per key
- `missing` — citekeys not in the bib, with the sections they appear in
- `suggestions` — actionable hints like `Run biblio_ingest for missing citekeys: [...]`

The host deck inherits `bibliography:` from `.projio/render.yml`. Missing keys should be fed through `biblio_ingest` before the first build so pandoc citeproc can resolve them at render time.

???+ info "MCP tools touched in steps 3–4"

    | Tool | Purpose |
    |------|---------|
    | `present_figure_insert` | Insert and register a figio figure |
    | `figio_build` | Build a figio figure spec to SVG/PDF/PNG |
    | `present_cite_check` | Cross-check citekeys against bib, report docling fulltext |
    | `biblio_ingest` | Ingest missing citekeys by DOI |

## 5. Validate and build

```text
present_validate(name="smoketest")
```

Structural checks:

- All section files exist on disk
- Section `order` values are unique (no duplicates, gaps are only a warning)
- Every `fig:<id>` placeholder resolves to a built output (unresolved → warning)
- Every `@citekey` resolves against the inherited bibliography (unresolved → warning)
- The renderer binary is on PATH (`marp-cli` for Marp decks, `pandoc` for reveal.js)

If `valid: true`, build:

```text
present_build(name="smoketest", format="html")
```

This dispatches by `deck.yml`'s `format:` field:

| Format | Backend | Output |
|--------|---------|--------|
| `marp` | `marp-cli` | html, pdf, pptx |
| `revealjs` | `pandoc -t revealjs --slide-level=0 --citeproc` | html |

For Marp, the pipeline is: `assemble_marp` → figure resolution → pandoc citeproc preresolve (if a bibliography is configured) → `marp-cli`.

For reveal.js, the pipeline is: `assemble_pandoc` → figure resolution → `pandoc -t revealjs` with native citeproc. No preresolve step — pandoc handles `@key` natively.

Output lands at `docs/presentations/smoketest/build/smoketest.html` either way.

???+ info "MCP tools touched in step 5"

    | Tool | Purpose |
    |------|---------|
    | `present_validate` | Structural checks + renderer availability |
    | `present_build` | Full render pipeline, dispatches by deck format |
    | `present_assemble` | Produce assembled markdown without calling a renderer |
    | `present_status` | Quick check of section state and last-built outputs |

## 6. Iterate

After a round of edits, see exactly what will change in the next build:

```text
present_diff(name="smoketest")
```

This returns per-section deltas: word-count changes, citekeys added / removed, figure refs added / removed, plus a full unified diff of the assembled markdown. Use it as a pre-build sanity check when you have edits spread across multiple sections.

For a rich dashboard view at any point:

```text
present_overview(name="smoketest")
```

Superset of `present_status`: adds citation cross-checking (missing keys across the deck), figure staleness detection, and total slide count including intra-file `---` separators.

???+ info "MCP tools touched in step 6"

    | Tool | Purpose |
    |------|---------|
    | `present_diff` | Per-section deltas + unified diff vs last assembled.md |
    | `present_overview` | Rich dashboard with citation / figure / slide analysis |

## 7. Switch backends mid-iteration

Here's the interesting thing about presentio's dual-backend design: the section source files are **format-agnostic**. The intra-file `---` separators work the same way under both backends (pandoc's `--slide-level=0` makes horizontal rules act as slide separators, matching Marp's convention). Only the frontmatter and renderer differ.

To render the same deck as reveal.js, edit `deck.yml`:

```yaml
format: revealjs  # was: marp
```

Then rebuild:

```text
present_build(name="smoketest", format="html")
```

No section edits. `assemble_pandoc` replaces `assemble_marp` at assembly time and produces a pandoc YAML metadata block (`title:`, `author:`, `date:`) instead of Marp's frontmatter. The body content is identical.

This is why you can start a deck in Marp for fast iteration on the section content, then switch to reveal.js for a web-hosted talk with interactive features, without rewriting anything.

## 8. Seed from a paper (alternative entry point)

If you are preparing a journal-club deck from a single paper, there's a shortcut:

```text
present_seed_from_paper(
  name="jc-smith2024",
  citekey="smith2024",
  template="journal-club"
)
```

This scaffolds a new deck, delegates to `biblio.present.generate_slides` (LLM-backed Marp generation from the paper's docling output and figures), strips the Marp frontmatter from the result, and writes it as `sections/seed.md` in the new deck.

The seed is a **starting point**, not a finished deck. Iterate on it section-by-section using `present_section_context` as with any other deck — the difference is that the first section already has content drawn from the paper's metadata, abstract, and figures.

???+ info "MCP tools touched in step 8"

    | Tool | Purpose |
    |------|---------|
    | `present_seed_from_paper` | Bridge to biblio's LLM paper-to-slides generator |
    | `biblio_ingest` | Ensure the target citekey exists in the bib first |
    | `biblio_docling` | Extract fulltext for the paper if not already done |

## What this tutorial did not cover

- **Cross-project imports**: see [Cross-project deck imports](../how-to/presentio-cross-project.md) for pulling a section from another project's deck into the current one.
- **Skill-driven workflows**: see the [literature-presentation](../reference/skills.md#literature-presentation) and [progress-report-deck](../reference/skills.md#progress-report-deck) skills for full iteration loops orchestrated by the agent.
- **Explanation of why presentio exists**: see [Presentio design](../explanation/presentio.md) for the architectural rationale and phasing.

## Full tool reference

The complete presentation tools table is in [reference/mcp-tools.md → Presentation tools](../reference/mcp-tools.md#presentation-tools-via-notiopresent). Fifteen tools total across phases 1, 2, and 4.
