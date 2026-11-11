---
name: literature-audit
description: >
  Audit a project's bibliography coverage for a topic: search every available
  corpus (project + shared/ecosystem), triage which held papers are relevant,
  and find what's missing — from cross-corpus gaps and from the citation graph.
  Produces a have / one-import-away / fetch-needed map and hands the fetch list
  to biblio-batch-curate. Use when checking literature coverage for an analysis,
  manuscript section, or new topic — not for grounding a single implementation
  idea (use literature-discovery for that).
metadata:
  short-description: Coverage audit — relevant held papers + missing (cross-corpus + citation gaps)
  tags: [bibliography, audit, gap-analysis, literature, coverage]
  tooling:
    mcp:
      - server: projio
        tools:
          - corpus_list
          - rag_query
          - rag_query_multi
          - paper_lookup
          - biblio_crossref_resolve
          - biblio_ingest
          - note_create
      - server: sirocampus
        tools:
          - corpus_list
          - rag_query
---

# Literature Audit

Given a **topic** (usually tied to an active analysis, detector, or manuscript
section), answer two questions with evidence:

1. **What do we already hold that's relevant?** — triage the current library.
2. **What's missing?** — from (a) a shared/ecosystem library and (b) the
   citation graph of the relevant papers.

Output is a three-bucket coverage map — **have** / **one-import-away** (in a
shared corpus, not here) / **fetch-needed** (in neither, surfaced by citations)
— and the fetch list is handed to `biblio-batch-curate`.

This is the coverage counterpart to `literature-discovery` (which grounds one
analysis *idea* in methods/parameters). Use this when the question is "do we
have the literature for X, and what are we missing," not "what method should I
implement."

## When to use

- Checking coverage before writing a manuscript section / introduction.
- After building an analysis: does the bib support and contextualize it, and
  what's missing.
- Onboarding a new topic; sanity-checking a reference list for gaps.

Do NOT use for: single-paper lookups (`paper_lookup`), bulk DOI ingest
(`biblio-batch-curate`), or method/parameter grounding (`literature-discovery`).

## Inputs

- `TOPIC` (required): the subject to audit (e.g. "cortical delta / DOWN-state detection").
- `SEED_CITEKEYS` (optional): known-central papers to anchor the citation-graph gap.
- `ANALYSIS` (optional): the specific analysis/detector to rank relevance against.
- `SHARED_CORPORA` (optional): shared/ecosystem MCP servers to also search
  (for example sirocampus, the lab's shared library).

## Workflow

### 1) Enumerate corpora — never assume names

Corpus names are NOT uniform across projects/servers (`bib` in one project,
`biblio` on sirocampus, `papers` elsewhere). Discover them, don't hardcode:

```
corpus_list()                    # project (projio)
sirocampus: corpus_list()        # shared, if reachable
```

Pick the literature corpus on each (the one holding paper chunks).

### 2) Multi-angle search of every corpus

For each corpus, run 3–5 complementary queries (definition, method, mechanism,
application angle) so one search framing doesn't miss papers:

```
rag_query_multi(corpus=<project_lit>, queries=[...])
sirocampus: rag_query(corpus=<shared_lit>, query=...)   # repeat per angle
```

Collect the union of surfaced source paths / citekeys per corpus.

### 3) Triage relevance — the **have** bucket

For each project-corpus hit, judge relevance to TOPIC/ANALYSIS and group it
(definition & methods / mechanism / application / adjacent). Confirm each exists:
`paper_lookup(refs=[...])`. This is the **have** bucket.

### 4) Cross-corpus gap — the **one-import-away** bucket

Papers surfaced by a SHARED corpus but NOT in the project library. Dedup by
DOI / title / author-year — **citekeys differ across libraries** (a shared
`el-kanbiDistinctionSlowWaves2022` may be the local `elkanbi_2022_Distinction`).
For each candidate, confirm it is genuinely absent locally (`paper_lookup` by
DOI or "Author Year Title", or grep the merged bib by title) before listing it. These are
**one-import-away** — the shared corpus already holds the PDF/docling.

### 5) Citation-graph gap — the **fetch-needed** bucket

From SEED_CITEKEYS (or the top relevant held papers):

```
biblio refs triage <seed>                          # one paper's references not held here (GROBID)
biblio graph expand --keys <seed> [<seed> ...]     # multi-seed OpenAlex reference set
```

(biblio CLI commands; run `biblio refs triage --help` and
`biblio graph expand --help` for the options in this version.)

Also read the reference-list snippets RAG already surfaced — foundational papers
a detector "should" cite often appear inside *other* papers' methods sections.
Keep items relevant to TOPIC and absent from BOTH libraries. These are
**fetch-needed**.

### 6) Rank + write the audit note

Rank every bucket by relevance to the ANALYSIS (methodological twins first).

```
note_create(note_type="task", title="Lit audit: <TOPIC>")
```

Structure:

```markdown
# Literature audit: <TOPIC>

## Have (relevant, already in library)
| Citekey | Why relevant | Group |

## One import away (in <shared corpus>, not here)
| Title / author-year | Why relevant | Shared citekey | DOI |

## Fetch-needed (in neither; from citations)
| Title / author-year | Why relevant | DOI (if known) | Seen cited in |

## Recommendation
Top N to add, ranked by relevance to <ANALYSIS>. Fetch list (DOIs) → biblio-batch-curate.
```

### 7) Hand off the fetch list (optional)

If the user approves, resolve + ingest, then hand to curation:

```
biblio_crossref_resolve(dois=[...])   # verify DOIs resolve to the intended papers
biblio_ingest(dois=[...], tags=[...]) # then run /biblio-batch-curate
```

For **one-import-away** papers whose PDFs live in a shared corpus, reuse that PDF
(copy into `bib/articles/<citekey>/<citekey>.pdf`) to skip the flaky OA fetch,
then merge → docling → compile → index.

## Guardrails

- **Discover corpora first** (`corpus_list`) — do not hardcode a corpus name; a
  wrong name returns empty and reads as "no coverage" when there is plenty.
- **Never invent citekeys or DOIs** — only use keys returned by RAG/resolve, and
  verify DOIs with `biblio_crossref_resolve` before ingest.
- **Verify a "gap" is real** — a paper may already be present under a different
  citekey; check `paper_lookup` / grep the merged bib by title before listing
  it as missing.
- **Summarize relevance in your own words** — the audit is a map, not a source
  of quotes; for claims backed by verbatim, checked quotes use `literature-sourcing`.
- **Shared corpora may be absent** in headless/cron runs (they are interactive
  MCP connectors). If unreachable, note it and audit the project corpus +
  citation graph only — do not fail.
- Do not run `biblio_citekey_normalize` (renames cited keys and does not dedup).

## Output format

Report:

1. Corpora searched (names + chunk counts) and queries run.
2. Counts per bucket: have / one-import-away / fetch-needed.
3. Path to the audit note.
4. Ranked top-N recommendation + the fetch-list DOIs.
5. Suggested next step (usually `/biblio-batch-curate` on the fetch list).

## Related

- `literature-discovery` — grounds one analysis idea in methods/parameters (prospective).
- `biblio-batch-curate` — ingest → PDF → validate → docling → compile → index (the fetch stage this feeds).
- `rag-query` — single-corpus semantic search primitive.
- `literature-sourcing` — back a specific claim with verbatim quotes checked against the full text.
