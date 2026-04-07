# Study: biblio-glutton for bibliographic reference matching

**Status:** study complete
**Date:** 2026-04-05

## Context

biblio resolves unmatched GROBID references to DOIs via CrossRef title search
(`crossref.py:resolve_doi_by_title`). biblio-glutton is a purpose-built
high-performance matching service by the GROBID author (Patrice Lopez) that
could replace or augment this.

## What biblio-glutton does

biblio-glutton is a self-hosted bibliographic matching and lookup framework:

- **Matching service** — from a raw citation string and/or structured metadata
  (title, first author, journal, volume, page, year), returns the disambiguated
  record with DOI and aggregated metadata.
- **Lookup service** — from strong identifiers (DOI, PMID, PMC, PII, ISTEX ID,
  HAL ID), returns aggregated metadata.
- **OA resolver** — integrates Unpaywall for Open Access PDF links.
- **Daily sync** — incremental CrossRef updates keep the local database current.

### Architecture

Two-tier storage:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LMDB | Embedded key-value | Fast identifier lookups (DOI→metadata, PMID↔DOI mappings) |
| Elasticsearch 7.x | Full-text index | Blocking/candidate retrieval for fuzzy matching |

Data sources: CrossRef (~147M records), PubMed/PMC ID mappings (34M PMIDs),
Unpaywall OA links, ISTEX, HAL, optionally DBLP.

Total storage: **~300 GB** on SSD.

### Matching algorithm

1. **Blocking** — Elasticsearch text search retrieves top-4 candidates using
   title, first author, journal, volume, first page as query fields.
2. **Pairwise ranking** — Ratcliff-Obershelp string similarity on each metadata
   field (title, author, journal, year), averaged across available fields.
3. **Threshold** — match accepted at ≥0.70 combined similarity.
4. **GROBID integration** — optionally parses raw citation strings via GROBID to
   extract structured metadata before matching (controlled by `parseReference`
   parameter).

### REST API

```
# Strong-ID lookup
GET /service/lookup?doi=<DOI>
GET /service/lookup?pmid=<PMID>

# Metadata matching
GET /service/lookup?atitle=<TITLE>&firstAuthor=<AUTHOR>
GET /service/lookup?jtitle=<JOURNAL>&volume=<VOL>&firstPage=<PAGE>

# Raw citation matching (most relevant for biblio)
GET /service/lookup?biblio=<RAW_CITATION_STRING>
POST /service/lookup/biblio   (Content-Type: text/plain)

# OA resolution
GET /service/oa?doi=<DOI>

# Combined (all parameters can be mixed)
GET /service/lookup?biblio=<RAW>&atitle=<TITLE>&firstAuthor=<AUTHOR>&year=<YYYY>
```

Parameters: `doi`, `pmid`, `pmc`, `pii`, `istexid`, `halid`, `atitle`,
`firstAuthor`, `jtitle`, `volume`, `firstPage`, `issue`, `year`, `biblio`,
`parseReference` (bool).

### Benchmarked performance

On 17,015 PubMed Central references:

| System | Precision | Recall | F1 |
|--------|-----------|--------|----|
| biblio-glutton (CRF) | 97.33% | 95.52% | 96.42% |
| biblio-glutton (BiLSTM-CRF) | 97.34% | 95.83% | 96.58% |
| CrossRef REST API | 97.19% | 94.26% | 95.69% |

**Throughput:**

| Operation | Speed |
|-----------|-------|
| DOI lookup (LMDB) | ~6,270 req/s |
| Metadata matching (1 ES node) | ~6.5 req/s |
| Metadata matching (2 ES nodes) | ~12.6 req/s |
| Per-reference latency | ~67 ms |

## How biblio currently resolves references

### Current flow

```
GROBID PDF → TEI XML → references.json {title, authors, year, doi, venue}
    ↓
Local matching (grobid.match_grobid_references)
    ├── DOI exact match against corpus
    └── Normalized title fuzzy match against corpus
    ↓
Absent refs = unmatched references
    ↓
CrossRef title resolution (crossref.resolve_doi_by_title)
    │  Query: query.bibliographic={title}, rows=5
    │  Scoring: SequenceMatcher similarity (case-insensitive)
    │  Accept: similarity ≥ 0.85 (or ≥ 0.70 with prefix match)
    ↓
Accepted → cache + OpenAlex enrichment → bibliography
Rejected → remains in absent_refs
```

### Limitations

1. **Title-only matching** — only sends the title to CrossRef, ignoring author,
   year, journal, volume, page metadata that GROBID already extracted.
2. **No raw citation matching** — doesn't leverage the original citation string.
3. **CrossRef API rate limits** — polite pool is 50 req/s with token, much less
   without; no local caching of the full CrossRef database.
4. **SequenceMatcher scoring** — decent but not purpose-built for bibliographic
   matching; doesn't weight fields differently.
5. **No instrumentation** — no logging of success/failure rates, similarity
   distributions, or rejection reasons.
6. **Silent failures** — all exceptions caught silently in `ingest.py`.
7. **No feedback to graph** — absent references resolved via CrossRef are not
   automatically fed into graph expansion.

## Comparison

| Dimension | biblio (CrossRef API) | biblio-glutton |
|-----------|-----------------------|----------------|
| Matching input | Title only | Title + author + journal + volume + page + year + raw string |
| Scoring | SequenceMatcher (title) | Ratcliff-Obershelp (multi-field average) |
| Threshold | 0.85 (strict) | 0.70 (more permissive, compensated by multi-field) |
| Recall (benchmark) | 94.26% | 95.52–95.83% |
| Precision (benchmark) | 97.19% | 97.33–97.34% |
| Throughput | Rate-limited (~50 req/s max) | ~6.5–12.6 req/s local (unlimited) |
| Latency | Network-dependent | ~67 ms local |
| Data freshness | Always current | Daily sync (configurable) |
| Deployment | None (SaaS) | Java + Elasticsearch + ~300 GB storage |
| OA resolution | Separate (Unpaywall API) | Built-in |
| ID mappings | None | DOI↔PMID↔PMC↔PII↔ISTEX |

## Integration options

### Option A: Replace CrossRef calls with biblio-glutton

**Change:** `crossref.py` calls glutton `/service/lookup?atitle=...&firstAuthor=...`
instead of CrossRef API.

- Pros: Better recall (+1.3%), multi-field matching, no rate limits, OA links included.
- Cons: Requires deploying and maintaining glutton (Java + ES + 300 GB).
- Effort: Small code change, large infra setup.

### Option B: Glutton as fallback after CrossRef miss

**Change:** When `resolve_doi_by_title` returns low similarity, retry via glutton
with full metadata (title + author + year + journal).

- Pros: Incremental improvement, CrossRef handles the easy cases, glutton catches
  the hard ones. No infra required if glutton not available (graceful degradation).
- Cons: Two resolution paths to maintain.
- Effort: Medium.

### Option C: Glutton for bulk resolution of all GROBID references

**Change:** After GROBID extraction, POST all raw citation strings to glutton
in batch.

- Pros: Highest accuracy (raw string + GROBID re-parsing), fastest for bulk.
- Cons: Requires glutton always running. Raw citation strings not currently
  preserved in biblio's `references.json` (only parsed fields).
- Effort: Medium — need to also extract raw citation strings from TEI XML.

### Option D: Improve current CrossRef matching (no glutton)

**Change:** Send more metadata fields to CrossRef API, add instrumentation.

- Pros: Zero new infrastructure. CrossRef `query.bibliographic` already accepts
  combined title+author+year strings.
- Cons: Still rate-limited, still single-scoring-method.
- Effort: Small.

## Recommendation

**Short term: Option D** — improve the existing CrossRef resolution by:
1. Sending `title + firstAuthor + year` to `query.bibliographic` (CrossRef
   supports combined strings).
2. Adding instrumentation to track resolution success rates.
3. Logging rejection reasons for analysis.

**Medium term: Option B** — add glutton as an optional fallback, configured via
`biblio.yml`. Only activate when a glutton endpoint is configured. This lets
power users deploy glutton for better recall while keeping zero-infra as default.

**Not recommended now: Options A/C** — the 300 GB infrastructure cost is hard to
justify until we have instrumentation showing that CrossRef misses are a
significant problem. Option D will provide that data.

## Deployment notes (for future reference)

```bash
# Build glutton
./gradlew clean build

# Load CrossRef data (~300 GB)
./gradlew crossref
./gradlew crossref gap_crossref  # fill gap to today

# Load mappings
./gradlew pmid
./gradlew unpaywall

# Index into Elasticsearch
cd indexing && node main -dump <crossref_dump> index

# Start server
./gradlew server  # default port 8080
```

Configuration: `config/glutton.yml` — set ES host, data paths, server port.
Health check: `curl localhost:8080/service/data`.

## Key references

- Mirror: `.projio/codio/mirrors/kermitt2--biblio-glutton/`
- API docs: `.projio/codio/mirrors/kermitt2--biblio-glutton/doc/API.md`
- Benchmarks: `.projio/codio/mirrors/kermitt2--biblio-glutton/doc/Benchmarking.md`
- Current resolver: `packages/biblio/src/biblio/crossref.py`
- GROBID refs: `packages/biblio/src/biblio/grobid.py`
- Graph expansion: `packages/biblio/src/biblio/graph.py`
- Ingest enrichment: `packages/biblio/src/biblio/ingest.py` (lines 335–375, 537–627)
