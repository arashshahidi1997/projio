---
name: literature-presentation
description: >
  Build a presentation deck that frames a scientific article's background —
  motivation, prior work, methods landscape, open questions — using the
  projio bibliography and presentio tools. The goal is an iteration loop,
  not one-shot generation: scaffold → outline → draft slides one at a
  time with human review → cite-check → build.
metadata:
  short-description: Build a literature-background deck slide-by-slide
  tags: [presentio, presentation, literature, iteration]
  tooling:
    mcp:
      - server: projio
        tools:
          - present_init
          - present_list
          - present_status
          - present_overview
          - present_section_context
          - present_figure_insert
          - present_cite_check
          - present_validate
          - present_assemble
          - present_build
          - present_diff
          - present_seed_from_paper
          - rag_query
          - rag_query_multi
          - citekey_resolve
          - paper_context
          - biblio_docling
          - biblio_ingest
          - figio_figure_list
          - figio_build
---

# Literature Presentation

Build a presentation deck that grounds an article in its literature
context. Work section-by-section with human review at each stage —
presentio decks are **iteratable artifacts**, not LLM one-shots.

## When to use

- You are preparing an introduction/background talk for a paper or
  thesis chapter.
- You want to frame the current work against prior art and open
  questions.
- You already have a shortlist of papers, or are about to assemble one
  via `literature-discovery`.

Do NOT use for progress reports (use `progress-report`) or for a single
paper journal club (use `present_seed_from_paper` directly).

## Inputs

- `TOPIC` (required): the scientific topic or question the deck frames
- `DECK_NAME` (required): short slug for the deck (e.g.
  `intro-gnn-brain`)
- `SEED_CITEKEYS` (optional): papers you already know should anchor
  the background narrative
- `VENUE` (optional): target audience (e.g. `lab-meeting`,
  `conference-talk`, `thesis-intro`)

## Workflow

### 1) Broad lit RAG

Start with a wide sweep to discover papers, methods, and framings.

```
rag_query(query=TOPIC, corpus="papers", k=10)
rag_query_multi(queries=[TOPIC, "<specific method>", "<open question>"], corpus="papers", k=5)
```

Extract candidate citekeys. Resolve them to confirm they are ingested:

```
citekey_resolve(citekeys=[...])
```

For any not in the library:

```
biblio_ingest(dois=[...])
```

### 2) Scaffold the deck

```
present_init(name=DECK_NAME, format="marp", template="conference-talk")
```

(Use `journal-club` for a single-paper deep-dive, `lab-meeting` for an
internal framing talk, `conference-talk` for a full talk with related
work + contributions.)

The scaffold creates `docs/presentations/<DECK_NAME>/` with
`deck.yml`, `sections/*.md` stubs, and an empty `figures/` tree.

### 3) Propose the outline to the human

**Do not draft any slide yet.** First, read the stub sections:

```
present_list()
present_status(name=DECK_NAME)
```

Then propose a narrative outline that covers the background arc:

- **Framing:** why the topic matters now
- **Prior-art map:** 3–5 clusters of existing work, each anchored by
  1–2 citekeys
- **Gap:** what's missing that the article addresses
- **Bridge:** how the article's contribution fits the gap

Present the outline as text. **Ask the human to accept, reject, or
reshape it** before drafting any slide. Capture the agreed outline in
the deck spec as section titles or as a plan note.

### 4) Draft sections one at a time

For each section in order, gather context:

```
present_section_context(name=DECK_NAME, section="<key>")
```

This returns the current body, citations already in-section, figures
referenced, RAG hits, and related notes — everything you need to
draft.

Draft **one section**. Keep it to 1–3 slides (use `---` on a line by
itself to split within a section file). Use pandoc citation syntax:
`[@smith2024]` or `[@smith2024; @jones2023]`.

**After drafting each section, stop. Show the human the change and
ask for approval before moving to the next.** This is the iteration
loop — do not batch.

### 5) Insert figures

If a prior-art slide needs a schematic or result figure that figio
can render:

```
figio_figure_list()                        # find candidates
figio_build(figure_id="<id>")              # ensure it's built
present_figure_insert(name=DECK_NAME, section="<key>", figure_id="<id>")
```

The figure is registered in `deck.yml` and a `fig:<id>` placeholder
is written into the section file. Real paths are resolved at build
time.

### 6) Cite-check

Before the first build:

```
present_cite_check(name=DECK_NAME)
```

Fix any `missing` citekeys via `biblio_ingest`. The tool reports which
cited papers lack docling fulltext — run `biblio_docling` on those so
RAG can surface quotes during later iteration.

### 7) Validate and build

```
present_validate(name=DECK_NAME)
present_build(name=DECK_NAME, format="html")
```

Open the HTML locally. If something looks wrong, iterate on the
affected section and rebuild. Use:

```
present_diff(name=DECK_NAME)
```

to see exactly what changed since the last build.

### 8) Capture a plan note when done

Create a plan/progress note linking the deck to the article it
introduces, with the final outline and the key references. This
keeps the deck discoverable after the talk.

## Hard rules

- **Never draft more than one section before human review.** The
  whole point of presentio is iteration — batch drafting defeats the
  workflow.
- **Never invent citekeys.** Every `@key` must resolve via
  `citekey_resolve`. If missing, `biblio_ingest` it first.
- **Do not run `present_seed_from_paper`** as the primary entry point
  for a literature deck — that tool is a single-paper LLM seed, not
  a multi-paper narrative builder. Use it only to bootstrap one
  section from one anchor paper, then iterate.
- **Prefer figio figures over inline images.** Registered figures
  survive deck edits and cross-project imports (phase 4).
- **Marp-cli must be installed** for `present_build` to succeed.
  Install with `npm install -g @marp-team/marp-cli`. Without it,
  `present_assemble` still works for structure inspection.
