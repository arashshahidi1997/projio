---
name: biblio-batch-curate
description: >
  End-to-end bibliography curation: ingest DOIs, merge sources, fetch PDFs,
  validate, run docling extraction, compile final bib, and sync indexes.
  Handles async jobs (PDF fetch, docling) with polling. Use after bulk
  paper discovery or when bibliography needs a full refresh.
metadata:
  short-description: Ingest → fetch → validate → extract → compile → index
  tags: [bibliography, batch, curation, production]
  tooling:
    mcp:
      - server: projio
        tools:
          - biblio_ingest
          - biblio_merge
          - biblio_pdf_fetch_oa
          - biblio_pdf_fetch_oa_status
          - biblio_pdf_validate
          - biblio_docling_batch
          - biblio_docling_status
          - biblio_grobid
          - biblio_grobid_check
          - biblio_graph_expand
          - biblio_compile
          - biblio_library_quality
          - indexio_sources_sync
---

# Bibliography Batch Curation

Orchestrate the full bibliography pipeline from raw DOIs to indexed,
searchable papers with compiled BibTeX for manuscript rendering.

## When to use

- After bulk paper discovery (literature-discovery, graph expansion, author search)
- When onboarding a new batch of papers from Zotero export
- Periodic library refresh (new PDFs available, stale docling outputs)
- When `ecosystem_status()` flags bibliography staleness

Do NOT use for single-paper lookups — use `citekey_resolve` / `paper_context` directly.

## Inputs

- `DOIS` (optional): list of DOIs to ingest. If empty, skip step 1 and start from merge.
- `CITEKEYS` (optional): specific citekeys to process. If empty, process all pending.
- `TAGS` (optional): tags to apply to newly ingested papers.
- `MODE` (optional): `full` (default) or `refresh` (skip ingest, re-fetch/re-extract only).

## Workflow

### 1) Ingest new papers (skip if MODE=refresh)

```
biblio_ingest(dois=DOIS, tags=TAGS, status="unread")
```

Record the returned citekeys — these feed subsequent steps.

If any DOIs fail to resolve, report them and continue with successful ones.

### 2) Merge source bibliographies

```
biblio_merge()
```

This consolidates `bib/srcbib/*.bib` into `.projio/biblio/merged.bib`.
Check the returned stats: entry count, duplicates resolved, warnings.

### 3) Fetch PDFs via open-access cascade

For small batches (< 20 papers):
```
biblio_pdf_fetch_oa(citekeys=CITEKEYS)
```

For large batches (20+ papers), run in background:
```
biblio_pdf_fetch_oa(background=True, citekeys=CITEKEYS)
```

Poll until complete:
```
biblio_pdf_fetch_oa_status(job_id=<job_id>)
```

Report: how many PDFs fetched, from which sources (pool/OpenAlex/Unpaywall/EZProxy), how many missing.

### 4) Validate fetched PDFs

```
biblio_pdf_validate()
```

This detects HTML paywall pages saved as `.pdf` (magic bytes check).
If invalid PDFs found:
- Report the count and affected citekeys
- Ask user: fix now (`biblio_pdf_validate(fix=True)` deletes fakes for re-fetch) or skip?
- If fixed, re-run step 3 for affected citekeys only

### 5) Run docling extraction

```
biblio_docling_batch(concurrency=1)
```

This is always async — returns a `job_id`. Poll:
```
biblio_docling_status(job_id=<job_id>)
```

Keep concurrency at 1 on shared HPC. Report progress at each poll.

### 6) GROBID reference extraction (if available)

First check availability:
```
biblio_grobid_check()
```

If GROBID is running:
```
biblio_grobid(citekeys=CITEKEYS)
```

If GROBID is not available, skip this step and note it in the report.

### 7) Expand citation graph (optional)

If the user wants to discover related papers:
```
biblio_graph_expand(citekeys=CITEKEYS, direction="both", depth=1)
```

Report new DOIs found. Ask user whether to ingest them (loops back to step 1).

### 8) Compile final bibliography

```
biblio_compile()
```

This merges `merged.bib` + `modkey.bib` → `.projio/render/compiled.bib`.
Report entry count in compiled output.

### 9) Quality check

```
biblio_library_quality()
```

Report per-tier counts: noise, stubs, sparse entries.
Flag any newly ingested papers that are stubs or missing DOI/authors.

### 10) Sync indexes

```
indexio_sources_sync(build=True)
```

This registers new papers in the indexio config and rebuilds the search index.

## Decision gates

The workflow has two explicit gates where the agent MUST pause and report:

1. **After step 4 (PDF validation)**: if invalid PDFs found, get user decision before proceeding
2. **After step 7 (graph expansion)**: if new DOIs discovered, get user decision on whether to ingest

All other steps proceed automatically.

## Guardrails

- NEVER skip the PDF validation step — paywall HTML masquerading as PDF will cause docling failures.
- NEVER set `concurrency` > 2 for `biblio_docling_batch` on shared infrastructure.
- NEVER run `biblio_compile` before `biblio_merge` — compiled.bib depends on merged.bib.
- If `biblio_pdf_fetch_oa` returns 0 new PDFs, still proceed to docling (there may be pending unprocessed PDFs from prior runs).
- Do NOT run git commands during this workflow.

## Output format

Report:
1. Papers ingested (count, failed DOIs if any)
2. PDFs fetched (count by source: pool/OA/Unpaywall/EZProxy, missing count)
3. PDF validation (valid/invalid counts, action taken)
4. Docling extraction (processed/skipped/failed counts)
5. GROBID status (available/unavailable, refs extracted)
6. Compiled bibliography entry count
7. Quality summary (noise/stub/sparse counts)
8. Index rebuild status
9. Suggested next step
