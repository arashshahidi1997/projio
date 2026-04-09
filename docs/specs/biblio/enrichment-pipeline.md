# Biblio Enrichment Pipeline Redesign

**Status:** Proposed
**Date:** 2026-04-03
**Prerequisites:** [OpenAlex API Audit](openalex-audit.md), [Concept/Topic Overlap Analysis](concept-topic-overlap.md)

## Motivation

Biblio's current OpenAlex integration resolves papers (DOI/title → OpenAlex ID) and expands
citation graphs, but discards most of the rich metadata OpenAlex returns. The resolver already
fetches `topics`, `authorships`, `open_access`, and `primary_location` via `DEFAULT_SELECT`,
yet only a fraction reaches biblio's data model. This spec designs an enrichment pipeline that
persists and surfaces the rest.

## Current Pipeline

```
srcbib/*.bib → biblio_merge → openalex_resolve (DOI/title → OpenAlex ID)
                                     ↓
                              graph_expand (references/citing)
                                     ↓
                              pdf_fetch → docling → grobid → RAG index
```

**Currently extracted per work:** `openalex_id`, `display_name`, `publication_year`,
`cited_by_count`, `authorships` (names only), `topics` (in `_work_to_minimal` but NOT
in `WorkRecord`), `referenced_works` (count only in resolve; full IDs in graph expand).

**Currently extracted per author:** `openalex_id`, `orcid`, `display_name`,
`affiliation` (first institution only), `works_count`, `cited_by_count`, `h_index`.

---

## Proposed Enrichment Additions

### 1. Topic Enrichment

**Priority:** Must-have (P1)

**What OpenAlex provides:**
- `primary_topic`: single topic with 4-level hierarchy (domain → field → subfield → topic) and confidence score
- `topics[]`: up to 3 topics, each with `id`, `display_name`, `score`, `subfield`, `field`, `domain`
- `keywords[]`: up to 5 AI-assigned keywords with similarity scores

**Where it would be stored:**

Per-citekey YAML in `bib/derivatives/openalex/{citekey}.yml`:

```yaml
citekey: smith2024
primary_topic:
  id: T12419
  name: "Analysis of Cardiac and Respiratory Sounds"
  score: 0.9997
  domain: "Health Sciences"
  field: "Medicine"
  subfield: "Pulmonary and Respiratory Medicine"
topics:
  - {id: T12419, name: "...", score: 0.9997, domain: "...", field: "...", subfield: "..."}
  - {id: T11636, name: "...", score: 0.85, domain: "...", field: "...", subfield: "..."}
keywords:
  - {keyword: "Cardiac Imaging", score: 0.56}
  - {keyword: "Clinical Decision Support", score: 0.52}
```

Cross-paper index at `bib/derivatives/openalex/_topic_index.yml`:

```yaml
# topic_id → list of citekeys
T12419: [smith2024, jones2023]
T11636: [smith2024, lee2025]
```

**Which MCP tools would expose it:**

| Tool | Change |
|------|--------|
| `library_get` | Include `topics` and `keywords` in response when available |
| `paper_context` | Include topic hierarchy in paper context output |
| New: `biblio_topic_search(topic, field, domain)` | Filter library by OpenAlex topic/field/domain |

**Data model changes:**

- `WorkRecord` dataclass: add `topics: list[dict] | None`, `keywords: list[dict] | None`, `type: str | None`, `is_retracted: bool`
- `_extract_work`: extract `topics`, `keywords`, `type`, `is_retracted` from API response

**Implementation notes:**

- The resolver already fetches `topics` via `DEFAULT_SELECT` — no new API calls needed
- `_work_to_minimal` already captures `topics` but `_extract_work` does not — fix this inconsistency
- Write topic YAML during resolution (not as a separate step) to avoid extra API calls
- The topic index can be rebuilt from per-citekey files (no API needed)

**Layering with existing systems** (per concept-topic-overlap.md):

1. Layer 0 (free): OpenAlex topics/keywords — this enrichment
2. Layer 1 (free): Autotag propagation tier — existing
3. Layer 2 (cheap): Autotag LLM tier — existing
4. Layer 3 (cheap): Concept extraction — existing

OpenAlex topics replace neither `concepts.py` nor `autotag.py` — they complement them at
the broad-domain level while LLM systems handle fine-grained extraction (datasets, metrics, techniques).

---

### 2. Author Model Enrichment

**Priority:** Must-have (P1 for affiliations/ORCID, P2 for topics/co-authors)

**What OpenAlex provides:**

| Field | Description | Priority |
|-------|-------------|----------|
| `affiliations[]` | Full affiliation history with institution ID, display name, and year ranges | P1 |
| `orcid` | Already extracted | Done |
| `topics[]` | Author-level topic distribution (aggregated from their works) | P2 |
| `counts_by_year[]` | Works + citations per year for last 10 years | P2 |
| `display_name_alternatives` | Name variants | P3 |
| `i10_index`, `2yr_mean_citedness` | Additional summary stats | P3 |

**Where it would be stored:**

Extend `AuthorRecord` dataclass:

```python
@dataclass(frozen=True)
class AuthorRecord:
    openalex_id: str
    orcid: str | None
    display_name: str
    affiliation: str | None              # current (last known) — keep for backward compat
    affiliations: tuple[dict, ...] | None  # NEW: full history [{institution_id, name, years}]
    works_count: int
    cited_by_count: int
    h_index: int | None
    topics: tuple[dict, ...] | None       # NEW: author-level topic profile
    counts_by_year: tuple[dict, ...] | None  # NEW: {year, works_count, cited_by_count}
```

Per-author cache in `bib/derivatives/openalex/authors/{author_id}.yml` for expensive
lookups (co-author networks, full affiliation timelines).

**Which MCP tools would expose it:**

| Tool | Change |
|------|--------|
| `biblio_discover_authors` | Return enriched `AuthorRecord` with affiliations and topics |
| `biblio_author_papers` | Already works; no change needed |
| New: `biblio_author_network(author_id, depth=1)` | Co-author graph: fetch author's works, extract unique co-authors, return network | P2 |

**Implementation notes:**

- `_extract_author` currently only takes `last_known_institutions[0]` — extend to capture full `affiliations` list
- Author-level `topics` come from `GET /authors/{id}` which is already called — just not extracted
- Co-author network is computed client-side from `authorships` on author works — no new endpoint needed, but potentially many API calls for prolific authors. Cache aggressively.

---

### 3. Citation Trend Enrichment

**Priority:** P2 (nice-to-have)

**What OpenAlex provides:**

Per work:
```json
"counts_by_year": [
  {"year": 2025, "cited_by_count": 12},
  {"year": 2024, "cited_by_count": 45},
  {"year": 2023, "cited_by_count": 38},
  ...
]
```

Per author: same structure but with `works_count` + `cited_by_count` per year.

Field-Weighted Citation Impact (FWCI): single float, normalized to 1.0 = world average for the field/year.

Citation normalized percentile: percentile rank + `is_in_top_1_percent` / `is_in_top_10_percent` flags.

**Where it would be stored:**

Extend per-citekey OpenAlex YAML (`bib/derivatives/openalex/{citekey}.yml`):

```yaml
citekey: smith2024
# ... topics, keywords (from §1) ...
citation_metrics:
  fwci: 2.34
  percentile: 92.5
  top_1_percent: false
  top_10_percent: true
counts_by_year:
  - {year: 2025, cited_by_count: 12}
  - {year: 2024, cited_by_count: 45}
```

**Which MCP tools would expose it:**

| Tool | Change |
|------|--------|
| `library_get` | Include `fwci`, `percentile`, `counts_by_year` when available |
| `paper_context` | Show citation trajectory |
| New: `biblio_library_quality` enhancements | Add "rising papers" / "declining papers" analysis based on year-over-year trend |

**Implementation notes:**

- `counts_by_year` is NOT in `DEFAULT_SELECT` — add it. Response size increase is modest (~100 bytes/work).
- FWCI and percentile are also not in `DEFAULT_SELECT` — add `fwci` and `citation_normalized_percentile`.
- Trend analysis (rising/declining) is computed locally: compare last 2 years' citation counts. No extra API calls.

---

### 4. Funder/Grant Enrichment

**Priority:** P3 (nice-to-have, useful for grant reporting)

**What OpenAlex provides:**

```json
"grants": [
  {
    "funder": "https://openalex.org/F1234",
    "funder_display_name": "National Institutes of Health",
    "award_id": "R01-GM-123456"
  }
]
```

Sourced from Crossref metadata — coverage varies by publisher.

**Where it would be stored:**

Extend per-citekey OpenAlex YAML:

```yaml
citekey: smith2024
# ... topics, keywords, citation_metrics ...
grants:
  - {funder_id: F1234, funder_name: "National Institutes of Health", award_id: "R01-GM-123456"}
```

Cross-paper index at `bib/derivatives/openalex/_funder_index.yml`:

```yaml
F1234:  # NIH
  name: "National Institutes of Health"
  citekeys: [smith2024, jones2023]
F5678:  # DFG
  name: "Deutsche Forschungsgemeinschaft"
  citekeys: [mueller2024]
```

**Which MCP tools would expose it:**

| Tool | Change |
|------|--------|
| `library_get` | Include `grants` when available |
| New: `biblio_funder_papers(funder_name)` | List papers funded by a given funder | P3 |

**Implementation notes:**

- `grants` is NOT in `DEFAULT_SELECT` — add it. Increases response size slightly.
- Coverage is incomplete (depends on publisher depositing grant info with Crossref), so the tool should document this limitation.
- Most useful for grant progress reports: "list all papers from this project funded by DFG grant XY".

---

## Proposed Pipeline (After Redesign)

```
srcbib/*.bib → biblio_merge → openalex_resolve ──┐
                                                   │
         ┌─────── enrichment (same API call) ◄─────┘
         │
         ├→ persist topics/keywords        → bib/derivatives/openalex/{citekey}.yml
         ├→ persist citation metrics       → bib/derivatives/openalex/{citekey}.yml
         ├→ persist grants                 → bib/derivatives/openalex/{citekey}.yml
         ├→ flag retracted papers          → library.yml status update
         ├→ build topic index              → bib/derivatives/openalex/_topic_index.yml
         ├→ build funder index             → bib/derivatives/openalex/_funder_index.yml
         │
         ├→ graph_expand (references/citing)
         ├→ pdf_fetch → docling → grobid
         ├→ autotag (Layer 1: propagation, Layer 2: LLM)
         ├→ concept extraction (Layer 3)
         └→ RAG index rebuild
```

Key insight: **enrichment happens during resolution, not as a separate step.** The OpenAlex
API already returns all needed fields — we just need to persist them instead of discarding.

---

## `DEFAULT_SELECT` Changes

Current:
```python
DEFAULT_SELECT = (
    "id", "doi", "display_name", "publication_year", "cited_by_count",
    "authorships", "topics", "referenced_works", "ids",
    "open_access", "best_oa_location", "primary_location",
)
```

Proposed additions:
```python
DEFAULT_SELECT = (
    # existing
    "id", "doi", "display_name", "publication_year", "cited_by_count",
    "authorships", "topics", "referenced_works", "ids",
    "open_access", "best_oa_location", "primary_location",
    # P1 additions
    "keywords", "type", "is_retracted",
    # P2 additions
    "counts_by_year", "fwci", "citation_normalized_percentile",
    # P3 additions
    "grants",
)
```

---

## Implementation Phases

### Phase 1: Topic + Work Type + Retraction Flag (P1)

1. Add `keywords`, `type`, `is_retracted` to `DEFAULT_SELECT`
2. Extend `WorkRecord` with `topics`, `keywords`, `type`, `is_retracted`
3. Fix `_extract_work` to extract topics/keywords (matching `_work_to_minimal`)
4. Write per-citekey OpenAlex YAML during resolution
5. Build `_topic_index.yml` after resolution completes
6. Extend `library_get` and `paper_context` to include topic data
7. Auto-flag retracted papers in `library.yml` (status or tag)

### Phase 2: Author Model + Citation Trends (P1–P2)

1. Add `counts_by_year`, `fwci`, `citation_normalized_percentile` to `DEFAULT_SELECT`
2. Extend `AuthorRecord` with `affiliations`, `topics`, `counts_by_year`
3. Extend `_extract_author` to capture full affiliation history
4. Write citation metrics to per-citekey OpenAlex YAML
5. Add rising/declining paper analysis to `biblio_library_quality`
6. Cache author lookups (currently uncached)

### Phase 3: Grants + Indexes + New Tools (P2–P3)

1. Add `grants` to `DEFAULT_SELECT`
2. Write grant data to per-citekey YAML
3. Build `_funder_index.yml`
4. Implement `biblio_topic_search` MCP tool
5. Implement `biblio_author_network` MCP tool (P2)
6. Implement `biblio_funder_papers` MCP tool (P3)

---

## Related Specs

- [Bibliography Architecture](bib-architecture.md) — sources vs artifacts separation
- [Concept/Topic Overlap Analysis](concept-topic-overlap.md) — layering strategy for OpenAlex topics + LLM extraction
- [OpenAlex API Audit](openalex-audit.md) — field-level gap analysis
- Discovery Model — design philosophy for external data integration (see `packages/biblio/docs/explanation/discovery.md`)
