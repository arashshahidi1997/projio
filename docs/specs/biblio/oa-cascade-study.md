# OA Cascade Study: Unpaywall/oadoi Internals vs biblio

Study of the Unpaywall backend (oadoi) to understand how OA resolution works and identify improvements for biblio's PDF fetch cascade.

## How Unpaywall Finds OA Copies

### Source Discovery Pipeline (oadoi `pub.py:find_open_locations`)

Unpaywall's `Pub.find_open_locations()` method checks **six source types** in sequence, accumulating all discovered locations into `open_locations`:

1. **Local lookup** (`ask_local_lookup`) — checks journal-level OA status via:
   - DOAJ (Directory of Open Access Journals) by ISSN match
   - Known OA publishers (PLoS, Hindawi, MDPI, SciELO, etc.)
   - Publisher+genre combos (e.g., Atlantis Press proceedings)
   - CrossRef license URLs (CC-BY, CC-BY-NC, etc.)
   - Manual journal overrides (hardcoded ISSNs with year thresholds)
   - DataCite DOI prefixes (700+ known open prefixes)
   - DOI fragment patterns (arxiv, figshare, dryad, zenodo, etc.)

2. **PubMed Central** (`ask_pmc`) — queries Europe PMC API for PMCID matches, determines version (published vs author manuscript)

3. **Green OA / Repository scraping** (`ask_green_locations`) — harvests OAI-PMH repository pages, scrapes for PDF links

4. **Publisher equivalent pages** (`ask_publisher_equivalent_pages`) — generates candidate URLs for known preprint servers (bioRxiv, medRxiv, Research Square, SciELO, Authorea, EarthArXiv) and scrapes them

5. **Hybrid scrape** (`ask_hybrid_scrape`) — checks publisher landing pages for openly accessible PDFs (bronze/hybrid OA)

6. **Semantic Scholar** (`ask_s2`) — queries S2 for additional copies

7. **Preprint/postprint cross-linking** (`ask_preprints`, `ask_postprints`) — follows CrossRef `has-preprint`/`is-preprint-of` relations to find related versions

8. **Manual overrides** (`ask_manual_overrides`) — human-curated corrections

### OA Status Classification (oadoi `open_location.py`)

Each location is classified into one of five statuses:

| Status | Meaning | How determined |
|--------|---------|----------------|
| **gold** | Published in a fully OA journal | Evidence starts with "oa journal" (DOAJ, publisher name, manual) |
| **green** | Repository copy | Evidence starts with "oa repository" |
| **hybrid** | OA article in subscription journal, with open license | Publisher-hosted, not gold/green, has open license |
| **bronze** | Free-to-read but no open license | Publisher-hosted, not gold/green/hybrid, no open license |
| **closed** | No OA copy found | No best_url available |

### Best OA Location Selection

The `best_oa_location` is the first element of `deduped_sorted_locations`, which applies:

1. **Filtering** — removes noncompliant copies (reported takedowns), validates PDF URLs against a database of known-bad URLs, excludes known-garbage endpoints
2. **Sorting** by `sort_score` (lower is better):
   - Publisher locations: -1000 base; +100 if evidence is manual/observed; -50 if has open license
   - Version: publishedVersion -600, acceptedVersion -400, submittedVersion -200
   - Has PDF URL: -100
   - DOI match in evidence: -10
   - Repository URL scoring: PMC -45, arxiv -40, .edu -30, citeseerx +10, ftp +60
3. **Deduplication** — merges bronze+hybrid publisher locations that point to the same content

**Key insight:** Unpaywall strongly prefers publisher versions with PDFs, then published versions from repositories, then accepted manuscripts.

## Biblio's Current Cascade vs Unpaywall

### Biblio's approach (`pdf_fetch_oa.py`)

Biblio walks a configurable source list (default: `pool → openalex → unpaywall → ezproxy`), **stopping at the first successful download**:

1. **Pool** — symlinks from shared PDF pools across projects
2. **OpenAlex** — uses `best_oa_location.pdf_url`, then `open_access.oa_url`, then `primary_location.pdf_url`
3. **Unpaywall** — direct API call: `best_oa_location.url_for_pdf`, then `best_oa_location.url`, then first `oa_locations[].url_for_pdf`
4. **EZProxy** — proxied DOI resolution for institutional access
5. **HTML fallback** — saves publisher landing page for docling extraction

### Key Differences

| Aspect | Unpaywall (oadoi) | biblio |
|--------|-------------------|--------|
| Sources checked | 8+ (DOAJ, PMC, repos, publisher scrape, S2, preprints) | 4 (pool, OpenAlex, Unpaywall API, EZProxy) |
| PDF validation | Database of known-bad URLs + header checks + `%PDF` magic + encrypted PDF detection + content-length < 128 rejection | Content-Type `text/html` rejection + `%PDF-` magic bytes |
| Location ranking | Sophisticated multi-factor scoring | Takes first available URL from OpenAlex record |
| URL fallback | Tries all `oa_locations[]`, not just best | Only tries `best_oa_location` fields, then `oa_url` |
| Version awareness | Tracks publishedVersion/acceptedVersion/submittedVersion | Not version-aware |
| License tracking | Full CC license classification | Not tracked |

## Is the Unpaywall API Call Redundant?

**Mostly yes, with important exceptions.**

OpenAlex incorporates Unpaywall data directly — their `best_oa_location` and `oa_locations` fields come from Unpaywall's database. However:

1. **Staleness gap** — OpenAlex snapshots Unpaywall data periodically. For recently-published papers, a direct Unpaywall API call may have fresher data.

2. **URL freshness** — OpenAlex caches the URL at ingest time. If a repository URL changes (common with institutional repos), Unpaywall's live check may catch the new URL while OpenAlex still has the old one.

3. **In practice** — for biblio's use case (downloading PDFs for a curated bibliography), the OpenAlex data is almost always sufficient. The Unpaywall step rarely yields a URL that OpenAlex doesn't already have.

**Recommendation:** Keep the Unpaywall step but make it smarter:
- Skip Unpaywall if OpenAlex already yielded a successful PDF download
- Only call Unpaywall as a fallback when the OpenAlex URL fails or is absent
- This is already how the cascade works — no change needed on ordering

## Recommended Improvements

### Priority 1: Better PDF validation

**Problem:** biblio only checks Content-Type header and `%PDF-` magic bytes. This misses:
- Encrypted PDFs that can't be processed (oadoi detects `/Encrypt \d+ \d+ [A-Za-z]+`)
- Very small files (< 128 bytes) that are error pages served as `application/pdf`
- Known-bad publisher URLs that consistently serve paywall pages

**Fix:** Enhance `_download()` in `pdf_fetch_oa.py`:

```python
# After downloading, add these checks:
# 1. Minimum file size (reject < 1KB as likely error pages)
# 2. Encrypted PDF detection
# 3. Content-Type: application/pdf but actually HTML (some servers lie)
```

Specific additions to `_download()`:
- Check file size after download; reject files under 1KB
- After confirming `%PDF-` header, scan first 4KB for `/Encrypt` pattern
- Check `Content-Disposition` header for additional PDF confirmation (like oadoi does)

### Priority 2: Try all OpenAlex OA locations, not just best

**Problem:** `_oa_pdf_url()` only checks `best_oa_location`, then `open_access.oa_url`, then `primary_location`. If the best URL is dead but a secondary location works, biblio misses it.

**Fix:** After the best URL fails, iterate through `oa_locations[]`:

```python
def _oa_pdf_url_candidates(record: dict) -> list[str]:
    """Return all candidate PDF URLs from an OpenAlex record, best first."""
    urls = []
    # Best OA location
    boa = record.get("best_oa_location") or {}
    for key in ("pdf_url", "url_for_pdf", "url"):
        if url := boa.get(key):
            urls.append(str(url))
    # open_access.oa_url
    if url := (record.get("open_access") or {}).get("oa_url"):
        urls.append(str(url))
    # primary_location
    if url := (record.get("primary_location") or {}).get("pdf_url"):
        urls.append(str(url))
    # All other oa_locations
    for loc in record.get("oa_locations") or []:
        for key in ("pdf_url", "url_for_pdf", "url"):
            if url := (loc or {}).get(key):
                urls.append(str(url))
    # Deduplicate preserving order
    seen = set()
    return [u for u in urls if u not in seen and not seen.add(u)]
```

Then in the cascade, try each URL before moving to the next source.

### Priority 3: Unpaywall location iteration

**Problem:** `best_pdf_url()` in `unpaywall.py` already iterates `oa_locations[]` for `url_for_pdf`, but falls back to `best_oa_location.url` (which may be a landing page, not a PDF) before trying other locations' direct PDF URLs.

**Fix:** Reorder fallback priority:
1. `best_oa_location.url_for_pdf`
2. All `oa_locations[].url_for_pdf` (not just first)
3. `best_oa_location.url` (landing page fallback, last resort)

### Priority 4: Content-Type validation for application/pdf responses

**Problem:** Some publishers serve HTML login/paywall pages with `Content-Type: application/pdf`. Biblio's `_download()` only rejects `text/html` content types.

**Fix:** After downloading, if Content-Type claims `application/pdf` but file doesn't start with `%PDF-`, treat it as a paywall page (already handled by magic bytes check — but add logging for diagnosis).

### Priority 5: Additional OA sources (low priority)

Sources that biblio currently misses but could add:
- **PubMed Central direct** — for biomedical papers, PMC often has copies that aren't in the OpenAlex `oa_locations` (rare but possible)
- **CORE** — aggregates 200M+ OA articles from repositories worldwide
- **BASE (Bielefeld Academic Search Engine)** — another large repository aggregator

These are low priority because OpenAlex already incorporates most of their data. Only worth adding if we find systematic gaps.

### Not recommended: Configurable cascade per paper type

The issue suggested per-paper-type cascade ordering. This adds complexity without clear benefit — the current cascade order (pool → openalex → unpaywall → ezproxy) is sensible for all paper types. The main gap is not ordering but thoroughness within each step.

## Summary

| Finding | Impact | Action |
|---------|--------|--------|
| Unpaywall call is largely redundant with OpenAlex | Low | Keep as fallback, no change needed |
| PDF validation is too simple | **High** | Add size check, encrypted PDF detection |
| Only tries best OA URL from OpenAlex | **High** | Iterate all `oa_locations[]` |
| Unpaywall fallback order suboptimal | Medium | Prefer all `url_for_pdf` before any `url` |
| Missing Content-Length check | Medium | Reject tiny responses |
| Additional OA sources (CORE, BASE, PMC direct) | Low | Not needed given OpenAlex coverage |
