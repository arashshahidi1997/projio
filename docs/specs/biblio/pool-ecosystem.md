# Pool Ecosystem: Multi-Project Bibliography Architecture

**Status:** Accepted
**Date:** 2026-04-03

## Motivation

Biblio is **project-centric and MCP-first** — the bibliography lives in the
repo, versioned alongside code and manuscripts, queryable by agents through
structured tools.

But research doesn't happen in one repo. A researcher works across multiple
projects, reads broadly, and collaborates in a lab. Papers, PDFs, and
enrichments need to flow between these contexts without duplication.

This spec defines how biblio's pool system, Zotero integration, OpenAlex
discovery, and DataLad transport work together across the multi-project
research ecosystem.

## Identity: Where Biblio Sits

```
Zotero                    biblio                     OpenAlex
─────────                 ──────                     ────────
Person-centric            Project-centric            Corpus-centric
GUI-first                 MCP-first                  API-first
Sync across devices       Versioned in repo          Global metadata

Collection manager        Enrichment engine          Metadata network
├─ Manual organization    ├─ PDF → full text          ├─ Citation graph
├─ PDF storage            │  (docling, GROBID)        ├─ Author/institution
├─ Citation plugins       ├─ Semantic search (RAG)    ├─ Topics/concepts
└─ Device sync            ├─ LLM analysis             ├─ OA locations
                          ├─ Reference graph           └─ Trends
                          └─ Manuscript pipeline
```

Biblio does not replace Zotero or OpenAlex. It bridges them into the project,
making their data agent-accessible and project-local.

## Three-Layer Pool Architecture

### Layers

| Layer | Example | Contains | Owned by |
|-------|---------|----------|----------|
| **Project** | pixecog `bib/` | Papers cited in this manuscript/analysis | The project |
| **Personal pool** | `arash-bib` | Everything Arash reads across all projects | A person |
| **Lab pool** | sirocampus `bib/` | Core literature, lab output, shared references | The lab |

### Resolution cascade

When biblio needs a PDF or derivative (docling, grobid, openalex), it checks
each layer in order:

```
project local → personal pool → lab pool
```

Configured in the project's `bib/config/biblio.yml`:

```yaml
pool:
  path: /storage2/arash/pools/arash-bib
  search:
    - /storage2/arash/pools/arash-bib       # personal first
    - /storage2/shared/sirocampus/bib       # then lab
```

### What lives where

```
pixecog (project)               arash-bib (personal pool)        sirocampus (lab pool)
─────────────────               ─────────────────────────        ────────────────────
bib/                            bib/                             bib/
  srcbib/                         srcbib/                          srcbib/
    project-refs.bib                zotero-personal.bib              zotero-group.bib
  articles/                       articles/                        articles/
    smith2024/ → symlink            smith2024/smith2024.pdf          jones2023/jones2023.pdf
    jones2023/ → symlink            doe2022/doe2022.pdf              sirota2019/sirota2019.pdf
  derivatives/                    derivatives/                     derivatives/
    (project-specific only)         docling/smith2024/...            docling/jones2023/...
                                    grobid/smith2024/...             grobid/sirota2019/...
.projio/
  biblio/
    library.yml  (project tags)
    merged.bib
```

### Resolution example

```
Agent in pixecog calls paper_context("smith2024")

1. PDF lookup:
   pixecog/bib/articles/smith2024/  →  symlink exists → resolves to arash-bib

2. Docling lookup (resolve_docling_outputs):
   pixecog/bib/derivatives/docling/smith2024/  →  missing
   arash-bib/bib/derivatives/docling/smith2024/  →  found! use pool copy

3. GROBID lookup (resolve_grobid_outputs):
   same cascade → found in arash-bib

4. Library metadata:
   pixecog/.projio/biblio/library.yml  →  project-specific tags, status, priority

Agent gets unified context. Doesn't know or care about pool resolution.
```

## Topology

```
                          ┌─────────────────────┐
                          │    Zotero Cloud      │
                          │                      │
                          │  Personal library    │
                          │  Group library (lab) │
                          └───┬─────────────┬────┘
                              │             │
                         API (personal) API (group)
                              │             │
                              ▼             ▼
┌──────────────┐    ┌─────────────────┐   ┌─────────────────────┐
│ Local laptop │    │  Personal pool  │   │   sirocampus        │
│              │    │  (arash-bib)    │   │   (lab pool/hub)    │
│ Zotero GUI   │    │                 │   │                     │
│              │    │  bib/           │   │  bib/               │
│ DL clone  ───┼───►│    srcbib/      │   │    srcbib/          │
│ of pools  ───┼───►│    articles/    │   │    articles/        │
│ & projects   │    │    derivatives/ │   │    derivatives/     │
└──────────────┘    └────────┬────────┘   └──────────┬──────────┘
                             │ pool.search[0]        │ pool.search[1]
                             │                       │
                      ┌──────┴───────────────────────┴──────┐
                      │                                     │
                ┌─────▼──────┐                      ┌───────▼────┐
                │  pixecog   │                      │  other     │
                │  bib/      │                      │  project   │
                │   articles/│ ← symlinks to pools  │  bib/      │
                │   library  │ ← project-specific   └────────────┘
                └────────────┘
```

## Transport: How Papers Move

### Two paths

| Path | Mechanism | Best for |
|------|-----------|----------|
| **API path** | pyzotero → Zotero Web API | Incremental sync, write-back, metadata |
| **DataLad path** | datalad save + push | Bulk PDFs, offline, versioning, collaboration |

Both paths coexist. DataLad tracks `bib/` regardless of how files got there.

### Path A: Zotero API (live sync)

biblio on the remote server talks to Zotero cloud directly.

```bash
# Pull from personal Zotero → personal pool
biblio zotero pull --collection "Oscillations" --target pool

# Pull from group Zotero → lab pool
biblio zotero pull --group 12345 --collection "Core" --target lab-pool

# After enrichment, write tags back
biblio zotero push-tags --source pixecog
```

**Strengths:** Real-time, bidirectional, no manual export
**Weaknesses:** Needs cloud sync, API key, slower for bulk PDFs

### Path B: DataLad (bulk transport)

User works locally, commits to DataLad, pushes to remote.

```bash
# On laptop — export from Zotero
zotero-export → ~/arash-bib/bib/srcbib/export-2026-04.bib
cp PDFs → ~/arash-bib/bib/articles/

# Commit and push
cd ~/arash-bib
datalad save -m "Zotero April export"
datalad push --to origin

# On remote — biblio picks it up
biblio merge && biblio compile
```

**Strengths:** Offline, bulk-efficient (annex only transfers new PDFs), versioned
**Weaknesses:** One-directional, manual export step

### DataLad structure

| Dataset | Role | Annexed content |
|---------|------|-----------------|
| **sirocampus** | Lab pool/hub | `bib/articles/**/*.pdf`, `bib/derivatives/` |
| **arash-bib** | Personal pool | Same structure |
| **pixecog** | Project | `bib/articles/` gitignored (symlinks to pool) |

Projects don't annex PDFs directly — they symlink to pools. This avoids
duplicating large files across datasets.

## Scenarios

### 1. "Add my reading list to the project"

```
Zotero personal library
  │ biblio zotero pull --collection "Reading List" --target pool
  ▼
arash-bib (personal pool)
  │ new entries in srcbib/, PDFs in articles/
  │ biblio merge
  ▼
pixecog
  │ biblio pool sync  →  symlinks created
  │ papers now available to agents via paper_context, rag_query
  ▼
Agent enriches: docling → grobid → autotag → summarize
  │ enrichments stored in project library.yml
  ▼
biblio zotero push-tags
  │ tags flow back to Zotero
  ▼
Arash sees enriched tags in Zotero GUI on any device
```

### 2. "Dump my whole Zotero collection"

```
Laptop: Zotero export → arash-bib/bib/srcbib/
Laptop: cp PDFs → arash-bib/bib/articles/
Laptop: datalad save && datalad push
  │
  ▼ (DataLad, git-annex transfers only new PDFs)
Remote: arash-bib now has full collection
  │ biblio merge && biblio compile
  ▼
Any project: biblio pool sync → symlinks to arash-bib
```

### 3. "Agent discovers papers via OpenAlex"

```
Agent in pixecog:
  biblio_discover_authors("Buzsáki")
  biblio_author_papers(id, position="last", since_year=2022)
  biblio_ingest(selected_dois)
  │
  ▼
pixecog/bib/imports/new-papers.bib  +  PDF fetched via OA cascade
  │ biblio merge && biblio compile
  ▼
Papers live in project. Optionally promote to pool:
  biblio pool promote --citekeys buzsaki2023,buzsaki2024
  │
  ▼
arash-bib (or sirocampus) now has them too
  │ biblio zotero push --new
  ▼
Papers appear in Zotero
```

### 4. "Collaborator adds papers"

```
Collaborator on their laptop:
  cd ~/sirocampus
  cp paper.bib bib/srcbib/
  cp paper.pdf bib/articles/newpaper/newpaper.pdf
  datalad save -m "Add new paper"
  datalad push --to origin
  │
  ▼ (arrives on shared server)
sirocampus (lab pool): new paper available
  │
  ▼ (next time any project runs biblio merge)
All linked projects can access it via pool cascade
```

### 5. "What did the agent tag my papers with?"

```
Agent in pixecog:
  biblio_autotag(citekeys)  →  tags in library.yml
  biblio_concepts(citekey)  →  concepts in derivatives/

biblio zotero push-tags --source pixecog
  │ reads library.yml tags + concept categories
  │ writes to Zotero item tags via API
  ▼
Zotero shows: "method:place-cells", "domain:hippocampus", etc.
Visible on all devices via Zotero sync
```

### 6. "I'm on a plane, want to add papers"

```
Laptop (offline):
  Drop .bib + PDFs into local DataLad clone of arash-bib
  datalad save -m "Papers from conference"
  (push later when online)

When online:
  datalad push --to origin
  │
  ▼
Remote pool updated. Projects pick up on next merge.
```

## Enrichment Sharing

Enrichments are computed once and shared via the pool cascade:

| Enrichment | Stored in | Shared via pool? | Project-specific? |
|------------|-----------|------------------|--------------------|
| PDF | `bib/articles/` | Yes (symlinked) | No |
| Docling (full text) | `bib/derivatives/docling/` | Yes | No |
| GROBID (header, refs) | `bib/derivatives/grobid/` | Yes | No |
| OpenAlex (metadata) | `bib/derivatives/openalex/` | Yes | No |
| LLM summary | `bib/derivatives/summaries/` | Could be | Sometimes |
| Concepts | `bib/derivatives/concepts/` | Could be | Sometimes |
| Autotag | `bib/derivatives/autotag/` | Could be | Sometimes |
| Library metadata | `.projio/biblio/library.yml` | No | Yes (tags, status, priority) |
| RAG index | `.cache/indexio/` | No | Yes (project-scoped search) |
| Manuscript refs | `docs/manuscript/` | No | Yes |

Rule: **factual derivatives** (text extraction, metadata resolution) are
pool-shared. **Interpretive derivatives** (summaries, tags, reading status)
are project-local because different projects may interpret the same paper
differently.

## Agent Perspective

An agent working in any project sees a unified MCP interface. The pool
architecture is invisible:

```python
# Agent doesn't know where the PDF lives
paper_context("sirota2023")     # → resolves via cascade

# Agent doesn't know which pool has the docling output
rag_query("theta oscillations") # → searches project index (built from pool data)

# Agent ingests to the project, not the pool
biblio_ingest(["10.1234/new"])  # → project-local

# Agent can discover externally
biblio_discover_authors("Sirota")           # → OpenAlex
biblio_author_papers(id, position="last")   # → OpenAlex
```

The pool architecture is a deployment concern, not an agent concern.

## Configuration

### Project config (`bib/config/biblio.yml`)

```yaml
pool:
  path: /storage2/arash/pools/arash-bib
  search:
    - /storage2/arash/pools/arash-bib
    - /storage2/shared/sirocampus/bib

zotero:
  api_key_env: ZOTERO_API_KEY        # or inline
  library_type: user                  # user | group
  library_id: "12345"
  sync_target: pool                   # pool | local
```

### Pool config (`arash-bib/bib/config/biblio.yml`)

```yaml
pool:
  is_pool: true
  pdf_pattern: "{citekey}/{citekey}.pdf"

zotero:
  api_key_env: ZOTERO_API_KEY
  library_type: user
  library_id: "12345"
  auto_collections:
    - name: "Core Reading"
      query: "status:reading OR status:cited"
```

### Lab pool config (`sirocampus/bib/config/biblio.yml`)

```yaml
pool:
  is_pool: true
  lab_pool: true

zotero:
  library_type: group
  group_id: "67890"
  api_key_env: ZOTERO_LAB_API_KEY
```

## Implementation Phases

### Phase 1: Pool promote + cross-pool resolve (current gaps)

- `biblio pool promote` — move project-local papers to a pool
- Verify cross-pool derivative resolution works end-to-end
- Document the pool setup workflow

### Phase 2: Zotero read (pull)

- `biblio zotero pull` — pull items + PDFs from Zotero via pyzotero
- Collection/tag filtering
- Incremental sync (track last sync version)
- Dependency: pyzotero as optional dependency

### Phase 3: Zotero write (push-back)

- `biblio zotero push-tags` — write enriched tags back to Zotero
- `biblio zotero push --new` — push newly ingested papers to Zotero
- Conflict detection (item modified in Zotero since last sync)

### Phase 4: Pool-level features

- Pool-level RAG index (shared search across all pool papers)
- Cross-project tag aggregation in pool
- Pool health dashboard (coverage, enrichment status)
