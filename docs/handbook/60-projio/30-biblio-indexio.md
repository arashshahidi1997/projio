# biblio + indexio: literature and retrieval

!!! note "Sources & anchors"
    - **Stack component:** projio
    - **Canonical artifact:** projio's own corpus (1.3k docs + 75k codelib chunks)
    - **Workshop session:** Day-3 AM session 2
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Citekey resolution; docling/grobid for PDF extraction; corpus indexing,
chunking, embedding; RAG. The pain biblio + indexio solve is *claims
drift from data*.

## The pain

By the time a manuscript draft is being assembled, the author has read
fifty papers, cited twenty, and paraphrased the rest from memory. Two
weeks later a co-author asks "where did you get that number for the
ripple frequency?" The author opens Zotero, searches for "ripple
frequency", scrolls through hits, opens three PDFs, ctrl-F-s through
each, and tries to reconstruct the citation. By the third paragraph
of the manuscript, the claim has drifted: the paraphrase no longer
matches the source figure caption, the page reference is wrong, or
the cited paper turns out to have made the opposite claim with
different terminology.

The fix is mechanical, not editorial: keep a *queryable* corpus of
the project's literature — full text, sectioned, embedded — and
resolve every citekey to extracted source text at write time. biblio
and indexio together supply that corpus.

## biblio — bibliography management

biblio is the literature subsystem. It manages the project's
bibliography as a set of human-edited source `.bib` files in
`bib/srcbib/` plus a set of generated artifacts in `.projio/biblio/`
and `.projio/render/`.

The compilation pipeline is:

```
bib/srcbib/*.bib                         (Zotero export, human-managed)
    → biblio_merge
        → .projio/biblio/merged.bib       (deduplicated, single file)
    → biblio_compile
        → .projio/render/compiled.bib     (final bib used by pandoc and mkdocs-bibtex)
```

The MCP surface separates roles. Ingestion: `biblio_ingest(dois=[...])`
takes a list of DOIs, queries Crossref / OpenAlex, and creates new
.bib entries with normalized citekeys. PDF acquisition:
`biblio_pdf_fetch_oa(force, citekeys)` runs the open-access cascade
(Unpaywall → OpenAlex OA URL → direct publisher when available) and
drops PDFs under `bib/articles/`. Full-text extraction:
`biblio_docling(citekey)` runs docling on a PDF and produces a
structured `.json` and `.md` representation under `bib/derivatives/docling/`.
Reference graph: `biblio_grobid(citekey)` extracts the paper's own
reference list, and `biblio_graph_expand(citekeys)` walks the graph
to find related work that should also be in the library.

## Citekey resolution

Every cited paper has a canonical citekey (e.g. `buzsaki2024oscillations`).
`citekey_resolve(citekeys)` returns the full bibliographic record for
each. `paper_context(citekey)` returns the full docling extraction —
sectioned body text, figure captions, table contents — as structured
data the agent or human can quote from directly. `paper_absent_refs(citekey)`
lists the citekeys this paper references that are *not yet in the
library*, so an automated curation pass can pull them in.

The Zotero integration closes the loop with the lab's existing
workflow. `biblio_zotero_pull` ingests the latest export from the
researcher's personal Zotero collection; `biblio_zotero_push` reflects
biblio-side enrichments (added DOIs, normalized author names) back to
Zotero. The pattern from the [biblio identity memo](../99-honest-gaps.md)
is that biblio is *project-centric and MCP-first*, complementing Zotero
(person-centric, GUI-first) and OpenAlex (corpus-centric).

## indexio — corpus indexing and RAG

indexio is the retrieval subsystem. It takes a set of *sources* —
glob patterns, single files, or paths — and produces an embedded
Chroma index suitable for semantic search. The interface is two MCP
tools: `indexio_sources_list()` and `indexio_build()` to manage the
index, and `rag_query(query, corpus=...)` and
`rag_query_multi(queries=[...], corpus=...)` to query it.

A *source* in indexio is identified by id, has a glob or path, lands
in a named *corpus*, and carries optional metadata. The default
corpus for a project is `docs`; biblio outputs land in a `biblio`
corpus; codio mirrors land in a `codelib` corpus. Multiple corpora
keep retrieval focused: a query about RIPPLE detection should not get
chunks of the snakemake source code.

`biblio_rag_sync()` is the bridge: it walks `bib/derivatives/docling/`,
registers each extracted paper as a source under the `biblio`
corpus, and triggers an incremental index rebuild. `codio_rag_sync()`
does the same for code mirrors. The two syncs together populate the
retrieval surface; `rag_query("how does snakebids handle missing
sessions?", corpus="codelib")` searches code, `rag_query("typical
ripple frequency band", corpus="biblio")` searches papers.

## projio's own corpus as the canonical example

projio (the tool repo, dogfooding its own ecosystem) maintains *two*
corpora indexed under `.projio/indexio/`:

- a **docs** corpus indexing this handbook, the workshop syllabus,
  the survey, the specs, and the agent-activity log — currently ~1.3k
  chunks across the markdown tree.
- a **codelib** corpus indexing the ~14 external code mirrors under
  `.projio/codio/mirrors/*/` (snakemake, openalex-elastic-api,
  openalex-docs, openalex-api-tutorials, …) at ~75k chunks total.

The `.projio/indexio/config.yaml` declares each source explicitly:

```yaml
sources:
- id: docs
  corpus: docs
  glob: docs/**/*.md
- id: codio-notes
  corpus: codelib
  glob: docs/reference/codelib/libraries/**/*.md
- id: codio-src-snakemake
  corpus: codelib
  glob: .projio/codio/mirrors/snakemake--snakemake/**/*.{py,ipynb,md}
  metadata:
    library: snakemake
    kind: external_mirror
```

`rag_query("how does snakemake report job IDs?",
corpus="codelib")` searches the entire mirrored snakemake source and
returns the relevant code chunks plus surrounding context. The same
query against the `docs` corpus would search the handbook and the
specs. Splitting corpora at index-build time keeps queries cheap and
focused.

## Putting them together — the manuscript story

The closing pattern for this chapter: a manuscript author drafting a
methods section calls `paper_context("buzsaki2024oscillations")` to
get the extracted source text, quotes the relevant passage directly,
inserts the `[@buzsaki2024oscillations]` citekey, and runs
`manuscript_cite_check` on the assembled draft. The cite check
verifies that every cited key resolves in `compiled.bib`, every key
in the bib is referenced (or marked as background reading), and every
quotation is traceable to the extracted text. The author is still
the one writing the prose, but the *evidence* is now machine-resolvable
all the way back to the source PDF. (Note: `manuscript_cite_suggest`
and the broader manuscript subsystem are uneven across projects — see
[figio + manuscript](40-figio-and-manuscript.md) for the honest
framing.)

The pain of "claims drift from data" does not disappear, but the
mechanical part of the fix — find the source, paraphrase faithfully,
attach the citekey — is now a tool call rather than a manual hunt.

## What is honest about this layer

The cohort use of biblio and indexio is uneven. Three of the four
study projects have populated `bib/` directories and run docling
extraction periodically; one (msol) has `biblio.enabled: false` while
still carrying a populated `bib/` — the [enabled-flag drift](../99-honest-gaps.md)
the handbook documents. indexio is enabled across all five projects
but only projio itself currently maintains the two-corpus pattern at
scale; the study projects index `docs` and rely on the ecosystem
codelib corpus for code retrieval.

## Further reading

- **[Docling](https://docling-project.github.io/docling/)** — PDF text extraction; table, figure, and structured reference extraction that `biblio_docling` wraps.
- **[GROBID](https://github.com/kermitt2/grobid)** — ML tool for structured reference and header extraction from PDFs; powers `biblio_grobid`.
- **[OpenAlex API](https://docs.openalex.org/)** — open scholarly metadata API; powers DOI resolution and citation-graph expansion in biblio.
