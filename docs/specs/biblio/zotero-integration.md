# Zotero Integration Spec

## Overview

Biblio complements Zotero (collection manager) and OpenAlex (metadata network) as an enrichment engine. This spec defines bidirectional integration between biblio and Zotero, replacing the current manual `.bib` export workflow with a live, incremental sync.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Zotero Library                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Items    │  │  PDFs    │  │  Tags    │  │  Notes   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │              │                │
└───────┼──────────────┼──────────────┼──────────────┼────────────────┘
        │              │              │              │
        ▼              ▼              ▲              ▲
┌───────────────────────────────────────────────────────────────┐
│                    biblio zotero sync                          │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Pull items  │  │ Pull PDFs   │  │ Push enrichments     │  │
│  │ → srcbib/   │  │ → articles/ │  │ ← tags, notes, IDs   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────▲───────────┘  │
│         │                │                     │              │
└─────────┼────────────────┼─────────────────────┼──────────────┘
          │                │                     │
          ▼                ▼                     │
┌──────────────────────────────────────────────────────────────┐
│                     biblio pipeline                            │
│  srcbib/*.bib → merge → compile → docling/grobid → indexio   │
│                                                    │          │
│  OpenAlex enrichment ──── autotag ──── summaries ──┘          │
└──────────────────────────────────────────────────────────────┘
```

## Authentication

Two modes, matching pyzotero:

| Mode | Use case | Config key | Notes |
|------|----------|------------|-------|
| **API key** (cloud) | Remote Zotero library | `zotero.api_key` | From zotero.org/settings/keys |
| **Local API** (Zotero 7) | Local client | `zotero.local: true` | Requires Zotero 7 with local API enabled; read-only |

Config location: `.projio/biblio/biblio.yml` under a new `zotero` section.

```yaml
zotero:
  library_id: "123456"        # Zotero user/group ID
  library_type: "user"        # "user" or "group"
  api_key: null               # Set via env BIBLIO_ZOTERO_API_KEY or config
  local: false                # Use Zotero 7 local API instead
  collection: null            # Sync a specific collection key (null = whole library)
  tags_filter: null           # Only sync items with these tags
  sync_state: ".projio/biblio/zotero_sync.yml"  # Version tracking
```

API key resolution order: `BIBLIO_ZOTERO_API_KEY` env var → `zotero.api_key` in biblio.yml → prompt.

## Phase 1: Zotero → biblio (pull)

### Command

```bash
biblio zotero pull [--collection KEY] [--tags TAG,...] [--since VERSION] [--dry-run]
```

MCP tool: `biblio_zotero_pull(collection=None, tags=None, dry_run=False)`

### Pull Flow

1. **Read sync state** from `.projio/biblio/zotero_sync.yml`:
   ```yaml
   last_version: 42
   last_sync: "2026-04-01T12:00:00Z"
   item_versions: { "ABC123": 42, "DEF456": 40 }
   ```

2. **Fetch changed items** using `zot.item_versions(since=last_version)` — returns only key→version pairs (tiny payload).

3. **Fetch full items** for changed keys. Use `format=bibtex` for direct BibTeX export, plus `format=json` for structured metadata (tags, collections, DOI, attachments).

4. **Write BibTeX** to `bib/srcbib/zotero.bib` (single file, full replace on each sync — Zotero is authoritative for this file).

5. **Fetch PDFs** for items with file attachments:
   - Use `zot.file(attachment_key)` to download binary content.
   - Store at `bib/articles/{citekey}/{citekey}.pdf` following existing convention.
   - Skip if PDF already exists and MD5 matches (use pdf_manifest.json).

6. **Sync library.yml metadata**:
   - Map Zotero tags → `library.yml` tags (union merge with existing).
   - Map Zotero collections → a `zotero_collections` field for reference.

7. **Update sync state** with new `last_version` and `item_versions`.

8. **Trigger downstream**: after pull, run `biblio_merge` → `biblio_compile` to update compiled.bib.

### Citekey Strategy

Zotero exports citekeys via Better BibTeX (if installed) or generates them from the BibTeX translator. Two modes:

| Mode | Behavior | Config |
|------|----------|--------|
| `zotero` (default) | Use citekeys from Zotero's BibTeX export as-is | `zotero.citekey_mode: "zotero"` |
| `biblio` | Re-assign citekeys using biblio's `assign_citekeys()` | `zotero.citekey_mode: "biblio"` |

When using `zotero` mode, store a `zotero_key → citekey` mapping in sync state for stable cross-references.

### Incremental Sync

Zotero's API provides version-based change tracking:

- `zot.item_versions(since=N)` returns items changed since version N.
- `zot.deleted(since=N)` returns items deleted since version N.
- On pull: fetch changed items, update local copies, remove deleted items from `zotero.bib`.
- First sync (no sync state): full pull of all items.

### Deleted Item Handling

When Zotero reports deleted items via `zot.deleted(since=last_version)`:

- Remove corresponding entries from `bib/srcbib/zotero.bib`.
- Do **not** delete PDFs or derivatives (they may be referenced elsewhere).
- Log deletions to `.projio/biblio/logs/runs/zotero_sync.jsonl`.
- Optionally mark as `archived` in library.yml instead of removing.

## Phase 2: biblio → Zotero (push back)

### Command

```bash
biblio zotero push [--citekeys KEY,...] [--what tags,notes,ids] [--dry-run]
```

MCP tool: `biblio_zotero_push(citekeys=None, what=["tags","notes","ids"], dry_run=False)`

### Push-back Targets

| Enrichment | Zotero field | Method | Conflict strategy |
|-----------|-------------|--------|-------------------|
| Autotag / concept tags | `tags[]` | `zot.add_tags(item, *tags)` | Union merge — never remove existing tags |
| LLM summaries | Child note item | `zot.create_items(note, parentid=item_key)` | Create new note; skip if identical note exists |
| Resolved DOI | `DOI` field | `zot.update_item(item)` | Only write if Zotero DOI is empty |
| OpenAlex ID | `extra` field | `zot.update_item(item)` | Append `OpenAlex: W1234` line if not present |
| Reading status | Tag: `#status:reading` | `zot.add_tags(item, tag)` | Prefix-namespaced tags to avoid collision |

### Conflict Handling

All push-back operations use **optimistic concurrency**:

1. Read item with current `version`.
2. Write with `last_modified=version`.
3. On 409 Conflict: re-read item, re-apply enrichment, retry once.
4. On second conflict: log and skip (human wins).

**Invariant**: biblio never overwrites human-edited fields. Tags are union-merged, DOI is write-if-empty, notes are append-only.

### Tag Namespacing

To distinguish biblio-generated tags from human tags in Zotero:

- Autotag output: `biblio:topic/neural-networks`
- Status tags: `biblio:status/reading`
- Concept tags: `biblio:concept/attention-mechanism`

Prefix `biblio:` prevents collision with user tags. Zotero displays these in the tag pane like any other tag.

## Architecture Decisions

### Dependency: pyzotero

Biblio depends on pyzotero directly as an optional dependency:

```toml
[project.optional-dependencies]
zotero = ["pyzotero>=1.6"]
```

Import guarded at module level:

```python
try:
    from pyzotero import zotero as pyzotero_client
    HAS_PYZOTERO = True
except ImportError:
    HAS_PYZOTERO = False
```

MCP tools and CLI commands raise a clear error if pyzotero is not installed.

### Sync State Location

`.projio/biblio/zotero_sync.yml` — colocated with other biblio state. Tracked by git (not gitignored) so collaborators share sync state. Contains:

```yaml
last_version: 42
last_sync: "2026-04-03T15:00:00Z"
library_id: "123456"
library_type: "user"
collection: null
item_map:
  ABC123:
    version: 42
    citekey: "smith_2024_AttentionMechanisms"
    has_pdf: true
  DEF456:
    version: 40
    citekey: "jones_2023_TransformerArchitecture"
    has_pdf: false
```

### Coexistence with srcbib Workflow

Zotero sync **coexists** with manual srcbib exports:

- Zotero-synced items go to `bib/srcbib/zotero.bib` (one dedicated file).
- Manual exports remain in other `bib/srcbib/*.bib` files.
- `biblio_merge` combines all srcbib files as before (last-wins dedup on citekey).
- Users can run both workflows simultaneously — Zotero for collection management, manual export for one-off additions.

Migration path: users who adopt Zotero sync can gradually move items from manual exports into their Zotero library, then delete the old export files.

### DataLad Interaction

When the project is a DataLad dataset:

- Synced PDFs land in `bib/articles/` which is typically annexed.
- After `zotero pull`, the user runs `datalad save` (or the MCP tool) to commit new PDFs to the annex.
- `zotero.bib` and `zotero_sync.yml` are regular git files (small text).
- Pool interaction: if `pool.path` is configured, PDFs are stored in the pool and symlinked locally (existing pool logic handles this).

### Pool Integration

Zotero sync targets the **project** (`bib/`), not the pool directly:

- Project is the unit of knowledge — Zotero collections map to projects.
- Pool sharing works via existing `sync_pool_symlinks()` — after pull, citekeys appear in the project, pool provides the physical PDFs if available.
- Multiple projects can sync different Zotero collections but share PDFs via pool.

Future consideration: a pool-level Zotero sync that pulls an entire library and distributes to projects by collection mapping.

## Module Layout

New module: `packages/biblio/src/biblio/zotero.py`

```
biblio/zotero.py
├── ZoteroClient          # Thin wrapper around pyzotero.Zotero
│   ├── __init__(config)  # Auth from config/env
│   ├── pull_items()      # Incremental item fetch
│   ├── pull_pdfs()       # Download attachments
│   ├── push_tags()       # Write tags back
│   ├── push_notes()      # Create child notes
│   └── push_ids()        # Update DOI/OpenAlex in extra field
├── SyncState             # Load/save zotero_sync.yml
│   ├── load()
│   ├── save()
│   └── diff(current_versions)  # Compute changed/deleted keys
├── pull()                # Orchestrator: fetch → write bib → fetch PDFs → update state
├── push()                # Orchestrator: read enrichments → write back → update state
└── item_to_bibtex()      # Zotero JSON → BibTeX entry (fallback if BibTeX export fails)
```

## CLI Surface

```
biblio zotero pull    [--collection KEY] [--tags TAG,...] [--dry-run]
biblio zotero push    [--citekeys KEY,...] [--what tags,notes,ids] [--dry-run]
biblio zotero status  # Show sync state, last sync time, item counts
biblio zotero init    # Interactive setup: library ID, API key, collection
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `biblio_zotero_pull` | Pull items and PDFs from Zotero (incremental) |
| `biblio_zotero_push` | Push enrichments back to Zotero |
| `biblio_zotero_status` | Show sync state and statistics |

## Implementation Plan

### Phase 1: Read-only pull (MVP)

1. Add `zotero` section to biblio config schema.
2. Implement `SyncState` (load/save YAML).
3. Implement `ZoteroClient.pull_items()` with incremental version tracking.
4. Write BibTeX to `bib/srcbib/zotero.bib`.
5. Implement PDF download via `zot.file()`.
6. CLI: `biblio zotero pull`, `biblio zotero status`, `biblio zotero init`.
7. MCP: `biblio_zotero_pull`, `biblio_zotero_status`.

**Dependencies**: pyzotero (optional), PyYAML (existing).

### Phase 2: Write-back

1. Implement tag push-back with `biblio:` namespace prefix.
2. Implement note creation for LLM summaries.
3. Implement DOI/OpenAlex ID write-back to extra field.
4. Conflict handling with optimistic concurrency.
5. CLI: `biblio zotero push`.
6. MCP: `biblio_zotero_push`.

**Dependencies**: Phase 1 complete, enrichment pipeline producing tags/summaries.

### Phase 3: Advanced

1. Collection-based filtering (sync specific Zotero collections).
2. Bidirectional tag sync (detect tag changes in Zotero, reflect in library.yml).
3. Zotero 7 local API support for read-only workflows.
4. Pool-level sync for shared lab libraries.

## Key References

- pyzotero source: `.projio/codio/mirrors/urschrei--pyzotero/`
- Zotero data model: `.projio/codio/mirrors/zotero--zotero-schema/schema.json`
- BibTeX translator: `.projio/codio/mirrors/zotero--translators/BibTeX.js`
- biblio discovery model: `packages/biblio/docs/explanation/discovery.md`
- biblio pool: `packages/biblio/src/biblio/pool.py`
- biblio ingest: `packages/biblio/src/biblio/ingest.py`
- bib architecture: `docs/specs/biblio/bib-architecture.md`
- enrichment pipeline: `docs/specs/biblio/enrichment-pipeline.md`
