# GROBID Citation Context Extraction

**Status:** Proposed
**Date:** 2026-04-05
**Prerequisites:** [Enrichment Pipeline](enrichment-pipeline.md), [Bib Architecture](bib-architecture.md)

## Motivation

Biblio uses GROBID for header extraction and reference parsing, producing a flat list of
references per paper. But GROBID's TEI output already contains **citation contexts** — the
inline `<ref type="bibr" target="#bN">` elements embedded within full-text paragraphs. The
surrounding text is the citation context. This data enables "paper X cites paper Y in
context C" relationships, far richer than simple citation edges.

The `ref_md.py` module already parses these inline refs for citation-key resolution (see
`extract_citation_clusters_from_body`), but discards the surrounding prose. This spec
proposes extracting and persisting that prose as structured citation contexts.

## GROBID TEI Structure for Inline Citations

GROBID's `processFulltextDocument` returns TEI XML with inline reference callouts in the
`<body>` element. Each callout is a `<ref>` element linking to a `<biblStruct>` in
`<listBibl>`:

```xml
<body>
  <div>
    <head>Introduction</head>
    <p>Sharp-wave ripples were shown to play a critical role in
    memory consolidation <ref type="bibr" target="#b12">(Buzsáki, 2015)</ref>,
    with subsequent work demonstrating their causal involvement
    <ref type="bibr" target="#b3">(Girardeau et al., 2009)</ref>.</p>
  </div>
</body>
<!-- ... -->
<listBibl>
  <biblStruct xml:id="b12">
    <analytic><title>Hippocampal sharp wave-ripple...</title></analytic>
    <!-- ... -->
  </biblStruct>
</listBibl>
```

Key structural facts:
- `target="#bN"` links to `xml:id="bN"` in `<listBibl>` (0-based index, display_num = N+1)
- Multiple consecutive `<ref>` elements form citation groups (e.g., `[1, 3-5]`)
- Refs appear inside `<p>` elements, sometimes within `<div>` with `<head>` section titles
- GROBID benchmarks show 78–96% F1-score for citation context resolution across corpora
- Sentence segmentation (OpenNLP or Pragmatic_Segmenter) can be enabled server-side via
  `grobid.yaml` config — when active, `<s>` elements wrap sentences within paragraphs

## Proposed Data Model

### Storage

Per-citekey file at `bib/derivatives/grobid/{citekey}/contexts.json`:

```json
{
  "citekey": "smith2024",
  "timestamp": "2026-04-05T12:00:00Z",
  "total_contexts": 47,
  "contexts": [
    {
      "bib_id": "b12",
      "cited_title": "Hippocampal sharp wave-ripple...",
      "cited_doi": "10.1126/science.1217230",
      "cited_citekey": "buzsaki2015",
      "section": "Introduction",
      "paragraph_index": 0,
      "sentence": "Sharp-wave ripples were shown to play a critical role in memory consolidation (Buzsáki, 2015), with subsequent work demonstrating their causal involvement.",
      "callout_text": "(Buzsáki, 2015)",
      "position": {
        "para_offset_start": 0,
        "para_offset_end": 156
      }
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `bib_id` | str | xml:id of the `<biblStruct>` target (e.g. "b12") |
| `cited_title` | str? | Title from the referenced `<biblStruct>` |
| `cited_doi` | str? | DOI from the referenced `<biblStruct>` |
| `cited_citekey` | str? | Local citekey if matched (via `match_biblstructs_to_corpus`) |
| `section` | str? | Nearest `<head>` ancestor text, or null |
| `paragraph_index` | int | 0-based paragraph index within the section |
| `sentence` | str | The sentence containing the citation (full paragraph if no sentence segmentation) |
| `callout_text` | str | The display text of the `<ref>` element(s) |
| `position` | dict | Character offsets within the paragraph for precise location |

### Corpus-Level Aggregation

A cross-paper index at `bib/derivatives/grobid/citation_contexts.json`:

```json
{
  "buzsaki2015": {
    "cited_by": [
      {
        "citing_citekey": "smith2024",
        "section": "Introduction",
        "sentence": "Sharp-wave ripples were shown to play a critical role in memory consolidation (Buzsáki, 2015)..."
      }
    ],
    "total_citations": 5
  }
}
```

This aggregation inverts the per-paper contexts: for each cited paper, list all contexts
where it is cited across the corpus. Only includes entries where `cited_citekey` is resolved.

## Implementation

### New Function: `extract_citation_contexts`

In `grobid.py`, add a TEI parser that extracts citation contexts from the full-text body:

```python
def extract_citation_contexts(tei_xml: str) -> list[dict[str, Any]]:
    """Extract citation contexts from TEI XML body.

    For each <ref type="bibr"> in the body, extract the containing
    sentence (or paragraph), the section heading, and the bib target.
    """
```

This reuses the existing TEI namespace constants and parsing infrastructure. The algorithm:

1. Walk `<body>//<div>` elements, tracking the current `<head>` (section title)
2. Within each `<p>`, iterate child elements looking for `<ref type="bibr">`
3. For each ref, extract the full paragraph text (via `itertext()`) and the ref's `target`
4. If sentence segmentation is present (`<s>` elements), use the containing `<s>` as context;
   otherwise use the full paragraph
5. Resolve `target="#bN"` to the corresponding `<biblStruct>` for title/DOI metadata

### Integration with `run_grobid_for_key`

Extend `run_grobid_for_key` to also write `contexts.json` alongside existing outputs:

```python
# In run_grobid_for_key, after writing references.json:
contexts = extract_citation_contexts(tei_xml)
# Match bib_ids to local citekeys
biblstructs = parse_tei_biblstructs(tei_xml)  # from ref_md.py
bib_id_to_citekey = match_biblstructs_to_corpus(cfg, biblstructs)
for ctx in contexts:
    ctx["cited_citekey"] = bib_id_to_citekey.get(ctx["bib_id"])
contexts_path = outdir / "contexts.json"
contexts_path.write_text(json.dumps({"citekey": key, ...}, indent=2))
```

Update `GrobidOutputs` dataclass to include `contexts_path`.

### Corpus Aggregation Function

```python
def aggregate_citation_contexts(cfg: BiblioConfig) -> Path:
    """Build inverted citation context index across all papers."""
```

Walks all `bib/derivatives/grobid/*/contexts.json`, groups by `cited_citekey`, writes
`citation_contexts.json`.

### Relationship to Existing Code

| Module | Current Role | Change |
|--------|-------------|--------|
| `grobid.py` | TEI parsing, reference extraction, GROBID submission | Add `extract_citation_contexts`, extend `GrobidOutputs` and `run_grobid_for_key` |
| `ref_md.py` | Citation cluster extraction for markdown resolution | No change — continues to use `extract_citation_clusters_from_body` for its purpose |
| `graph.py` | OpenAlex-based citation graph expansion | No change — operates on OpenAlex data, not GROBID TEI |
| `grobid.match_grobid_references` | Flat citekey→citekey edges from references.json | Unchanged — citation contexts are a parallel enrichment, not a replacement |

## MCP Tools

### `biblio_citation_contexts(citekey)`

Returns citation contexts for a single paper (as citing paper). Reads from
`bib/derivatives/grobid/{citekey}/contexts.json`.

**Use cases:**
- "How does smith2024 cite buzsaki2015?" → filter contexts by `cited_citekey`
- "What papers does smith2024 cite in its Methods section?" → filter by `section`

### `biblio_cited_by_contexts(citekey)`

Returns all citation contexts where a paper is cited across the corpus. Reads from
the aggregated `citation_contexts.json`.

**Use cases:**
- "How is buzsaki2015 cited across the corpus?" → all citing sentences
- Manuscript writing: generate citation sentences based on how peers cite the same paper

## RAG Integration

Citation contexts are high-value RAG chunks. Each context record maps to a chunk:

```
source: grobid-context
citekey: smith2024
cited_citekey: buzsaki2015
section: Introduction
text: "Sharp-wave ripples were shown to play a critical role in memory consolidation (Buzsáki, 2015)..."
```

Add a `grobid-context` source type to `biblio_rag_sync` that indexes citation context
sentences. This enables queries like "what do papers say about sharp-wave ripples" to
surface the exact citing sentences.

## Priority Assessment

### Must-have (P1)

- **`extract_citation_contexts`** — the core parser; data is already in the TEI XML that
  biblio produces, just not extracted
- **`contexts.json` per citekey** — persist alongside existing GROBID outputs
- **`biblio_citation_contexts` MCP tool** — query interface for agents

### Should-have (P2)

- **Corpus-level aggregation** (`citation_contexts.json`) — inverted index for "cited-by"
  queries
- **`biblio_cited_by_contexts` MCP tool** — surfaces the aggregated data
- **RAG indexing** of citation context sentences

### Nice-to-have (P3)

- **Citation intent classification** — categorize contexts as "background", "method use",
  "result comparison", "contradiction" (would require an LLM or scite-style model)
- **biblio-glutton integration** — use biblio-glutton for higher-quality matching of
  unresolved GROBID references to DOIs (replaces or augments CrossRef title matching)
- **Section-level citation density** — statistics on which sections cite which papers most

## biblio-glutton

[biblio-glutton](https://github.com/kermitt2/biblio-glutton) is a high-performance
bibliographic matching service from the GROBID ecosystem. It matches raw bibliographic
strings against CrossRef, PubMed, and other sources using fuzzy matching.

**Relevance to biblio:**
- Could replace `resolve_doi_by_title` in `openalex_resolve.py` for unresolved references
- GROBID's `consolidateCitations=1` already uses a similar matching approach server-side;
  biblio-glutton would provide the same capability for post-hoc matching
- Most valuable for papers where GROBID extracts references without DOIs — biblio-glutton
  can resolve these to DOIs for corpus matching

**Recommendation:** Defer biblio-glutton integration to P3. The current DOI + title
matching in `match_grobid_references` covers the primary use case. biblio-glutton adds
value mainly for edge cases (malformed references, missing DOIs) that don't block the
citation context feature.
