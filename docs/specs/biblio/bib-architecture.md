# Bibliography Architecture: Sources vs Artifacts

**Status:** Accepted
**Date:** 2026-04-02

## Motivation

Previously, `bib/` held both human-managed sources (Zotero exports, PDFs) and
generated artifacts (merged bibliography, pandoc-defaults, config files, logs).
This conflation caused:

- mkdocs parsing `.bib` artifacts as pages, triggering false warnings
- unclear ownership: which files are safe to edit vs auto-generated
- no clean separation between source data and build artifacts

## Design Decision

**All generated/shipped artifacts move to `.projio/`; `bib/` holds only
human-managed sources.**

## Layout

```
.projio/
  render.yml                    # config (human-edited)
  render/
    compiled.bib                # biblio_compile output — THE single bib for pandoc + mkdocs-bibtex
    pandoc-defaults.yaml        # generated from render.yml
    csl/                        # shipped by projio, copied during sync
      apa.csl
  filters/
    include.lua                 # shipped by projio (existing)
  biblio/
    merged.bib                  # biblio_merge output (intermediate)
    biblio.yml                  # biblio config (moved from bib/config/)
    library.yml                 # library ledger (moved from bib/config/)
    logs/                       # merge/quality/duplicate logs
      duplicate_bib_ids.txt
      low_quality_entries.txt
      runs/                     # run ledger (JSONL)
  pipeio/
    modkey.bib                  # pipeio_modkey_bib output (intermediate)
    registry.yml                # (existing)

bib/
  srcbib/           # Zotero exports (human-managed source .bib files)
  articles/         # PDFs (human-managed or fetched)
  config/           # legacy location — reads fall back here if .projio/biblio/ not found
  derivatives/      # docling, grobid, openalex outputs
```

## Compilation Pipeline

```
srcbib/*.bib  →  biblio_merge  →  .projio/biblio/merged.bib  ─┐
                                                                ├→  biblio_compile  →  .projio/render/compiled.bib
             pipeio_modkey_bib →  .projio/pipeio/modkey.bib  ─┘
```

Both pandoc (via `pandoc-defaults.yaml`) and mkdocs (via `bib_file` config)
point to `.projio/render/compiled.bib` as the single bibliography.

## render.yml Schema Extension

```yaml
# .projio/render.yml
pdf_engine: xelatex
bibliography: .projio/render/compiled.bib
csl: .projio/render/csl/apa.csl
bib_sources:
  - .projio/biblio/merged.bib
  - .projio/pipeio/modkey.bib
lua_filter: .projio/filters/include.lua
conda_env: ""
resource_path:
  - .
  - docs
  - docs/assets
  - bib
```

The `bib_sources` list declares the intermediate `.bib` files that
`biblio_compile` merges into `compiled.bib`. Missing sources are skipped
gracefully (e.g. pipeio may not be present in all projects).

## Migration Strategy

- **Backward compatibility:** if old paths exist (`bib/config/biblio.yml`,
  `bib/main.bib`) and new paths don't, read from old locations but write to new.
- **projio sync** handles migration: copies config files, updates paths, runs
  `biblio_merge → biblio_compile` with new output locations.
- The `bib/config/` directory remains readable but is no longer the write target.

## MCP Tool Changes

| Tool | Change |
|------|--------|
| `biblio_merge` | Output moves to `.projio/biblio/merged.bib` |
| `biblio_compile` | **New** — merges intermediates into `compiled.bib` |
| `pipeio_modkey_bib` | Output moves to `.projio/pipeio/modkey.bib` |
| `project_context` | Reports bib compilation status |

## Related Specs

- [Manuscript spec](../notio/manuscript.md) — manuscript build reads `compiled.bib`
- [Pipeio ontology](../pipeio/ontology.md) — modkey.bib generation
