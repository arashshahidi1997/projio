# OSF Integration Spec

Status: draft (2026-04-16)

## Overview

The [Open Science Framework](https://osf.io) (OSF, Center for Open Science) is a cloud-hosted project container offering free DataCite DOIs, immutable registrations, preprint hosting, ORCID-anchored contributors, and a *link-only* storage add-on model over GitHub, S3, Dataverse, Figshare, Zotero, Mendeley, and others. It has shallow metadata, imposes no project structure, and offers no code/pipeline/bibliography intelligence — but guarantees 50-year preservation and is the de-facto platform for preregistration in many fields.

Projio and OSF are **complementary, not competing**:

- **Projio** is the working environment — local-first, opinionated structure, deep per-subsystem metadata, agent-native via MCP.
- **OSF** is a publication / registration / archival façade — shallow metadata, cloud-hosted, DOI-minting, discoverable.

This spec defines how a projio repo becomes OSF-compatible without compromising its local-first, repo-as-knowledge design. The guiding principle mirrors OSF's own add-on philosophy: **link, don't copy**. The repo stays the source of truth; OSF becomes the discoverability / DOI / archive layer.

## Goals

1. One-command publication of a projio repo as an OSF project with a DOI.
2. Single metadata manifest that also feeds `CITATION.cff`, `codemeta.json`, and `datacite.yaml` — no duplication.
3. Map projio subsystems (manuscripts, pipelines, bibliography, code, data) to OSF components so OSF visitors see a navigable structure rather than a file dump.
4. First-class preregistration living in the repo (YAML answers → OSF registration schema).
5. Manuscript → preprint flow via notio + OSF Preprints.
6. Agent-facing `osf_*` MCP tools with preview-first semantics (matching the `datalad` module).

## Non-goals

- Re-implementing OSF storage locally.
- Making OSF the source of truth for code, data, or bibliography.
- Pushing every file in the repo. Uploads are explicit and curated.
- Running a custom OSF instance or upstreaming a projio add-on into OSF core.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       projio repository                         │
│  .projio/osf.yml          ← single source of truth metadata    │
│  .projio/osf-registration.yml                                   │
│  .projio/osf/state.json   ← mirror of remote state (generated) │
│                                                                 │
│   bib/      code/       manuscripts/     pipelines/    figs/   │
└────────────┬──────────────────────────────────────┬────────────┘
             │                                      │
             │ projio sync                          │ projio osf push
             ▼                                      ▼
  generated citation artifacts           ┌──────────────────────┐
  CITATION.cff                            │        OSF           │
  codemeta.json                           │  ┌────────────────┐  │
  datacite.yaml                           │  │ root project   │  │
                                          │  ├────────────────┤  │
                                          │  │ component:     │  │
                                          │  │   manuscript   │  │
                                          │  ├────────────────┤  │
                                          │  │ component:     │  │
                                          │  │   pipeline …   │  │
                                          │  ├────────────────┤  │
                                          │  │ component:     │  │
                                          │  │   code (link)  │  │
                                          │  ├────────────────┤  │
                                          │  │ component:     │  │
                                          │  │   data  (link) │  │
                                          │  └────────────────┘  │
                                          └──────────────────────┘
```

## The `.projio/osf.yml` manifest

Single human-edited file. Acts as the source of truth for all citation-related metadata in the repo. `projio sync` derives `CITATION.cff`, `codemeta.json`, and `datacite.yaml` from it.

```yaml
# .projio/osf.yml
title: "Example Study on Cortical Dynamics"
description: |
  Short abstract. Can be multi-line. Rendered into the OSF project
  description and DataCite metadata.

category: project         # one of OSF's ~15 categories
license: CC-BY-4.0        # SPDX ID
tags: [neuroscience, fmri, preregistration]

contributors:
  - name: "Arash Shahidi"
    orcid: 0000-0000-0000-0000
    role: [conceptualization, software, writing-original-draft]   # CRediT
    bibliographic: true
  - name: "Jane Co-Author"
    orcid: 0000-0000-0000-0001
    role: [investigation, writing-review-editing]

funders:
  - name: "Example Funding Agency"
    award_number: "EFA-1234"
    award_uri: "https://example.org/awards/EFA-1234"

related_identifiers:
  - identifier: "https://github.com/arash/example-study"
    type: url
    relation: IsSupplementTo

osf:
  project_id: null        # filled in on first push
  public: false
  include:
    - manuscripts/*/build/*.pdf
    - figs/**/*.svg
    - figs/**/*.pdf
    - .projio/render/compiled.bib
    - docs/site/
  exclude:
    - "**/*.tmp"
    - "**/__pycache__/**"

components:
  - kind: manuscript
    source: manuscripts/main
    title: "Manuscript: Example Study"
  - kind: pipeline
    source: pipelines/preprocessing
    title: "Pipeline: preprocessing"
  - kind: bibliography
    title: "Bibliography"
  - kind: code
    addon: github
    repo: arash/example-study
    title: "Code"
  - kind: data
    addon: s3
    bucket: example-study-data
    title: "Data"
```

The `components:` block drives the concept → OSF component mapping on push.

## Commands

All commands are preview-first: default dry-run prints the planned API calls and file list; `--yes` executes.

### `projio osf push`

1. Validate `.projio/osf.yml`.
2. Resolve the target project (create if `osf.project_id` is null).
3. Sync metadata (title, description, license, category, tags, contributors, funders, related identifiers) via v2 REST API.
4. For each entry in `components:`, create or update the matching component and apply its own metadata subset.
5. Walk `osf.include`/`osf.exclude` and upload changed files via [`osfclient`](https://github.com/osfclient/osfclient) to OSF Storage on the appropriate component.
6. For `addon: github` / `addon: s3` components, configure the OSF add-on to link the upstream service instead of uploading bytes.
7. Write the returned `project_id` back into `osf.yml` on first push.
8. Refresh `.projio/osf/state.json`.

### `projio osf pull`

Mirror remote OSF project state into `.projio/osf/state.json`: DOI, public/private flag, contributors, last-modified, registration list, preprint list. Enables agent queries like "is this project published, what's its DOI, who are the contributors" without hitting the API every time.

### `projio osf register`

1. Read `.projio/osf-registration.yml` (schema choice + answers).
2. Create a git tag `osf/reg/<timestamp>`.
3. Build a frozen file-hash manifest of the current tree.
4. Submit a registration draft to OSF's v2 API against the chosen schema (default: `OSF-Standard Pre-Data Collection`; supported: `AsPredicted`, `PreregChallenge`, `Secondary Data`).
5. Optionally apply an embargo (up to 4 years).
6. Return the registration DOI and store it under `related_identifiers`.

### `projio osf preprint <manuscript>`

1. Build the PDF via `manuscript_build` (notio + pandoc).
2. Upload to a chosen preprint server (PsyArXiv, SocArXiv, MetaArXiv, EarthArXiv, …; configurable per-manuscript).
3. Fill preprint metadata from notio frontmatter + `osf.yml`.
4. Return the preprint DOI and store it in the manuscript's frontmatter.

### `projio osf doi`

Quick accessor that prints the project DOI (and registration / preprint DOIs if present) from `.projio/osf/state.json`.

## Concept → OSF component mapping

| projio concept | OSF target | Mechanism |
|---|---|---|
| Repo root + README | Root project | Metadata from `osf.yml`; README uploaded |
| `manuscripts/<name>` | Component "Manuscript: …" | Built PDF + supplementary figures uploaded |
| `pipelines/<flow>` | Component "Pipeline: …" | `dag.svg` + `pipeline-docs.md` + rule list uploaded |
| `bib/` | Component "Bibliography" | `compiled.bib` + biblio summary uploaded |
| `code/` | Component "Code" | GitHub add-on link (no upload) |
| `data/` (DataLad) | Component "Data" | S3 add-on link to DataLad RIA/S3 sibling |
| `figs/` | Attached to the relevant manuscript component | SVG/PDF uploaded |
| Git tag + registration answers | Registration | `projio osf register` |
| Manuscript PDF | Preprint | `projio osf preprint` |

## MCP tools

Expose under `src/projio/mcp/osf.py`, registered in `src/projio/mcp/server.py`:

| Tool | Purpose |
|---|---|
| `osf_status` | Return `.projio/osf/state.json` contents; refresh if stale |
| `osf_push` | Preview or execute publication (respects `--yes`) |
| `osf_pull` | Refresh local mirror of remote state |
| `osf_register` | Preview or execute preregistration |
| `osf_preprint` | Preview or execute preprint upload |
| `osf_doi_get` | Return the project / registration / preprint DOIs |
| `osf_contributors_sync` | Two-way sync of contributor list with OSF |
| `osf_manifest_validate` | Schema-check `.projio/osf.yml` |

All mutating tools follow the preview-first pattern used by the `datalad` MCP module.

## Configuration

User config (`~/.config/projio/config.yml`):

```yaml
osf:
  token_env: OSF_TOKEN          # personal access token env var
  default_preprint_server: psyarxiv
  default_registration_schema: "OSF-Standard Pre-Data Collection"
```

Project config (`.projio/config.yml`) may override any of these.

## Derived artifacts (written by `projio sync`)

- `CITATION.cff` — GitHub citation widget + Zenodo ingestion.
- `codemeta.json` — CodeMeta 2.0 for code discovery.
- `datacite.yaml` — DataCite 4 metadata, used when minting DOIs outside OSF (e.g. Zenodo).

All three are regenerated from `.projio/osf.yml` and should not be edited by hand. Each carries a header comment: `# generated from .projio/osf.yml — do not edit`.

## Implementation phases

**Phase 1 — Manifest + citation artifacts (low effort, high value)**

- [ ] `.projio/osf.yml` schema + loader (`src/projio/osf/manifest.py`)
- [ ] `projio sync` generates `CITATION.cff`, `codemeta.json`, `datacite.yaml`
- [ ] `projio osf validate` (CLI) + `osf_manifest_validate` MCP tool
- [ ] Docs under `docs/how-to/osf-publish.md`

**Phase 2 — Push / pull**

- [ ] `projio osf push` using `osfclient` + direct v2 API calls for metadata
- [ ] `projio osf pull` → `.projio/osf/state.json`
- [ ] `osf_push`, `osf_pull`, `osf_status`, `osf_doi_get` MCP tools
- [ ] Preview-first semantics mirroring `datalad` module

**Phase 3 — Components mapping**

- [ ] `components:` block processing on push
- [ ] GitHub / S3 add-on linking instead of uploads for `code` / `data`
- [ ] Per-component metadata propagation

**Phase 4 — Registration + preprint**

- [ ] `.projio/osf-registration.yml` schema
- [ ] `projio osf register` with schema selection + embargo
- [ ] `projio osf preprint <manuscript>` via notio build
- [ ] `osf_register`, `osf_preprint` MCP tools

**Phase 5 — Exploratory (only if an institutional user asks)**

- [ ] OSF Storage as a DataLad sibling via WebDAV
- [ ] Custom OSF add-on surfacing a projio repo's `.projio/` index

## Open questions

1. **osfclient vs. direct v2 calls.** `osfclient` is mature for file ops but does not cover registrations, wikis, or metadata. Push = osfclient for uploads + direct `requests` for metadata/components/registrations.
2. **Preprint server defaults.** Should `default_preprint_server` be user-global or per-manuscript? Leaning per-manuscript in frontmatter with user-global fallback.
3. **Registration schema coverage.** Start with `OSF-Standard Pre-Data Collection`; add others on demand.
4. **DOI ownership.** OSF mints DataCite DOIs free; Zenodo does too. Should `projio osf` and a future `projio zenodo` share the same manifest? Yes — `osf.yml` is already shaped like a DataCite record for this reason. Consider renaming to `.projio/citation.yml` once Zenodo lands.
5. **Contributor sync direction.** One-way (projio → OSF) is safe; two-way risks overwriting OSF-side edits. Default one-way with explicit `osf_contributors_sync --pull`.

## Related specs

- [bib-architecture.md](biblio/bib-architecture.md) — bibliography structure that feeds the `bibliography` component.
- [deliverables.md](deliverables.md) — publishable outputs that become OSF components and preprints.
