# OpenAlex API Audit: biblio integration vs actual API capabilities

**Date:** 2026-04-03
**Scope:** Endpoint correctness, data model gaps, caching, rate limiting
**Sources:** biblio source code, indexed OpenAlex API docs + elastic-api source

---

## 1. Endpoint & Filter Audit

### Endpoints used

| biblio module | Endpoint | Correct? |
|---|---|---|
| `openalex_client.py` | `GET /works/doi:<doi>` | Yes |
| `openalex_client.py` | `GET /works/<id>` | Yes |
| `openalex_client.py` | `GET /works?search=` | Yes |
| `openalex_client.py` | `GET /works?filter=` | Yes |
| `openalex_client.py` | `GET /authors?search=` | Yes |
| `openalex_client.py` | `GET /authors/<id>` | Yes |
| `openalex_client.py` | `GET /authors?filter=` | Yes |
| `openalex_client.py` | `GET /institutions?search=` | Yes |
| `openalex_client.py` | `GET /institutions/<id>` | Yes |
| `author_search.py` | `GET /authors?filter=orcid:<orcid>` | Yes |
| `discovery.py` | `GET /works?filter=author.id:<id>` | Yes |
| `discovery.py` | `GET /works?filter=institutions.id:<id>` | Yes |
| `discovery.py` | `GET /authors?filter=last_known_institutions.id:<id>` | Yes |
| `graph.py` | `GET /works?filter=cites:<id>` | Yes |

**Verdict:** All endpoints and filter expressions are correct.

### Filter syntax

- Comma-separated AND filters: used correctly (`author.id:X,from_publication_date:Y`)
- The `cites:` filter for citation graph expansion: correct

### Missing useful query parameters

| Parameter | API support | biblio usage | Priority |
|---|---|---|---|
| `sort` | Yes (`field:asc\|desc`) | Used in `author_search.py` and `discovery.py` (`publication_year:desc`, `works_count:desc`) | Done |
| `group_by` | Yes (faceted aggregation) | **Not used** | P2 — useful for topic/year distributions |
| `sample` + `seed` | Yes (random sampling up to 10k) | **Not used** | P3 — useful for corpus sampling |
| `select` | Yes (field selection) | Used in `openalex_client.py` via `DEFAULT_SELECT` and in `discovery.py` per-request override | Done |
| `per-page` (max 200) | Yes | Used, but defaults to 25 in config | P1 — should default to 200 for bulk ops |
| OR filter (pipe `\|`) | Yes (up to 50 values) | **Not used** | P1 — batch DOI lookups would be 50x faster |
| `title.search` filter | Yes (title-only search) | **Not used** (uses generic `search=`) | P2 — more precise for title matching |

### Cursor pagination

**Implementation (in `author_search.py` and `discovery.py`):**
```python
cursor = "*"
while cursor:
    params = {"cursor": cursor, ...}
    data = client._get_json("works", params=params)
    meta = data.get("meta")
    next_cursor = meta.get("next_cursor")
    if next_cursor and next_cursor != cursor:
        cursor = next_cursor
    else:
        break
```

**API reality:**
- Initial request: `cursor=*`
- Subsequent: use `meta.next_cursor`
- Terminal: `next_cursor` is `null` when no more results

**Verdict:** Correct. The `next_cursor != cursor` guard is slightly defensive but harmless — the API returns `null` when exhausted, which the `if next_cursor` check catches. No bug here.

**Gap:** `search_works` and `filter_works` in `openalex_client.py` do NOT paginate — they return only the first page. This is fine for small result sets but means these methods silently truncate. The cursor-paginated paths in `author_search.py` and `discovery.py` work correctly.

### Rate limiting / polite pool

**Current state:**
- `mailto` parameter: supported via `OpenAlexClientConfig.email` → added as `params["mailto"]`
- Retry with exponential backoff: implemented (both with and without tenacity)
- No explicit rate limiter (requests/second throttle)

**API reality:**
- Without `mailto`: 1 req/sec, 100k/day
- With `mailto` (polite pool): 10 req/sec, 100k/day
- With API key (premium): higher limits

**Gap (P2):** No per-second rate limiter. For serial requests this is fine (network latency provides natural throttling), but if biblio ever adds concurrency, it could hit rate limits. Low priority since all current usage is serial.

---

## 2. Data Model Audit

### `_extract_work` (author_search.py)

| Field | Extracted? | Available in API? | Notes |
|---|---|---|---|
| `id` (OpenAlex ID) | Yes | Yes | |
| `doi` | Yes (from `ids.doi` or `doi`) | Yes | |
| `display_name` / title | Yes | Yes | |
| `publication_year` | Yes | Yes | |
| `cited_by_count` | Yes | Yes | |
| `journal` (from `primary_location.source`) | Yes | Yes | |
| `is_oa` (from `open_access.is_oa`) | Yes | Yes | |
| **`topics`** | No | Yes — up to 3 topics with 4-level hierarchy (topic/subfield/field/domain) | **P1** |
| **`keywords`** | No | Yes — up to 5 AI-assigned keywords with scores | **P2** |
| **`grants`** | No | Yes — funder ID + award ID (from Crossref) | **P2** |
| **`sustainable_development_goals`** | No | Yes — SDG tags with scores | **P3** |
| **`counts_by_year`** | No | Yes — citation counts per year (last 10 years) | **P2** |
| **`related_works`** | No | Yes — algorithmically computed related work IDs | **P2** |
| **`fwci`** | No | Yes — Field-Weighted Citation Impact | **P2** |
| **`citation_normalized_percentile`** | No | Yes — percentile + top 1%/10% flags | **P2** |
| **`type`** | No | Yes — article, book, dataset, etc. | **P1** |
| **`language`** | No | Yes — ISO 639-1 | **P2** |
| **`abstract_inverted_index`** | No | Yes — inverted index format | **P3** |
| `referenced_works` | No (only count via `_work_to_minimal`) | Yes — full list of IDs | Already used in `graph.py` |
| `locations` | No | Yes — all hosting locations | P3 |
| `is_retracted` | No | Yes | **P1** — should flag retracted papers |
| `biblio` (volume/issue/pages) | No | Yes | P3 |
| `mesh` | No | Yes (PubMed works only) | P3 |
| `indexed_in` | No | Yes — arxiv, crossref, doaj, pubmed | P3 |
| `corresponding_author_ids` | No | Yes | P3 |

### `_extract_author` (author_search.py)

| Field | Extracted? | Available in API? | Notes |
|---|---|---|---|
| `id` | Yes | Yes | |
| `orcid` | Yes | Yes | |
| `display_name` | Yes | Yes | |
| `last_known_institutions` (first only) | Yes | Yes (list) | Only takes first institution |
| `works_count` | Yes | Yes | |
| `cited_by_count` | Yes | Yes | |
| `h_index` (from `summary_stats`) | Yes | Yes | |
| **`counts_by_year`** | No | Yes — works + citations per year (10 years) | **P2** |
| **`affiliations`** | No | Yes — full affiliation history with years | **P1** |
| **`display_name_alternatives`** | No | Yes — name variants | P3 |
| **`topics`** | No | Yes — author-level topic distribution | **P2** |
| `i10_index` (from `summary_stats`) | No | Yes | P3 |
| `2yr_mean_citedness` (from `summary_stats`) | No | Yes | P3 |

### `_extract_institution` (discovery.py)

| Field | Extracted? | Available in API? | Notes |
|---|---|---|---|
| `id` | Yes | Yes | |
| `ror` | Yes | Yes | |
| `display_name` | Yes | Yes | |
| `country_code` | Yes | Yes | |
| `type` | Yes | Yes | |
| `works_count` | Yes | Yes | |
| `cited_by_count` | Yes | Yes | |
| **`lineage`** | No | Yes — parent institution chain | P3 |
| **`homepage_url`** | No | Yes | P3 |
| **`topics`** | No | Yes — institution-level topics | P3 |
| **`counts_by_year`** | No | Yes | P3 |

### `_work_to_minimal` (openalex_resolve.py)

This is used for the srcbib→OpenAlex resolution output. Currently extracts: `openalex_id`, `display_name`, `publication_year`, `cited_by_count`, `authorships`, `topics`, `referenced_works_count`.

**Gap:** Topics are captured here but not in `_extract_work`. Inconsistency.

---

## 3. Caching Audit

### Current implementation (`openalex_cache.py`)

- **Structure:** `{root}/doi/{hash[:2]}/{hash}.json`, `{root}/work/{hash[:2]}/{hash}.json`, `{root}/search/{hash[:2]}/{hash}.json`
- **Key generation:** SHA1 of normalized DOI / work ID / lowercased query
- **Atomic writes:** Yes — writes to `.tmp` then renames
- **TTL/invalidation:** None — cache entries never expire
- **Force refresh:** Supported via `force` parameter

### API best practices (from tutorials + docs)

The OpenAlex docs recommend:
1. Cache responses to avoid hitting the 100k/day limit
2. Use `select` to reduce response size (already done)
3. Use `mailto` for polite pool access (already done)

### Gaps

| Issue | Severity | Notes |
|---|---|---|
| **No TTL** | P2 | OpenAlex data updates regularly. Cached data can go stale. Consider optional max-age parameter |
| **No cache for author/institution lookups** | P2 | Only DOI, work ID, and search queries are cached. Author and institution fetches go directly through the client with no caching |
| **No cache size management** | P3 | No pruning or size limits. For large corpora, cache can grow unbounded |
| **Search cache is query-exact** | P3 | "machine learning" and "Machine Learning" would be different cache keys due to `.lower()`, but slight variations still miss. This is acceptable |

---

## 4. Priority Summary

### P1 — Should fix soon

1. **Batch DOI lookups via OR filter (pipe `|`)** — Up to 50 DOIs per request. Would dramatically speed up `openalex_resolve.py` which currently does one request per DOI
2. **Extract `type` field** — Needed to distinguish articles from books, datasets, preprints
3. **Extract `is_retracted` field** — Critical for library quality; retracted papers should be flagged
4. **Extract `topics` in `_extract_work`** — Already in `_work_to_minimal` but missing from the `WorkRecord` dataclass used by discovery/author tools
5. **Default `per_page` to 200 for bulk operations** — Current default of 25 means 8x more API calls than necessary
6. **Extract full `affiliations` history for authors** — Only first `last_known_institution` is captured; the API provides a complete history with years

### P2 — Nice to have

7. **Add `group_by` support** — For analytics: publication trends by year, topic distributions, OA status breakdowns
8. **Extract `keywords`** — AI-assigned keywords with scores, up to 5 per work
9. **Extract `grants`/funders** — Available from Crossref metadata
10. **Extract `counts_by_year`** — Citation trends over time for both works and authors
11. **Extract `related_works`** — Algorithm-computed related papers (useful for graph expansion beyond citations)
12. **Extract `fwci` and `citation_normalized_percentile`** — Impact metrics
13. **Extract `language`** — Useful for filtering non-English papers
14. **Add optional TTL to cache** — Prevent stale data for actively updated entities
15. **Cache author/institution lookups** — Currently uncached
16. **Use `title.search` filter** — More precise than generic `search=` for title matching in resolution
17. **Add per-second rate limiter** — Defensive measure for future concurrency

### P3 — Low priority / niche

18. **`sample` + `seed` support** — Random corpus sampling
19. **SDG tags** — Useful for specific research domains
20. **`abstract_inverted_index`** — Full abstract text reconstruction
21. **`locations`** — All hosting locations beyond primary
22. **`biblio` (volume/issue/pages)** — Already in BibTeX; low incremental value
23. **`mesh` tags** — Only for PubMed works
24. **Institution `lineage`** — Parent organization chains
25. **Author `display_name_alternatives`** — Name variants

---

## 5. Correctness Issues

No outright bugs found. The implementation is solid on the endpoints it uses. Specific observations:

1. **DOI encoding:** `get_work_by_doi` uses `quote(doi_norm, safe='')` which is correct — OpenAlex expects URL-encoded DOIs in the path
2. **ID normalization:** Consistently strips URL prefixes to get short IDs (`W...`, `A...`, `I...`) — correct
3. **Author truncation:** OpenAlex truncates authorships to 100 in list responses (documented limitation). biblio doesn't account for this — the `is_authors_truncated` flag is not checked. Low impact since most papers have <100 authors
4. **The `author.id` filter vs `authorships.author.id`:** biblio uses `author.id` which is a valid alias (confirmed in API source). The canonical form is `authorships.author.id` but both work
5. **The `institutions.id` filter vs `authorships.institutions.id`:** Same situation — `institutions.id` is an alias that works
