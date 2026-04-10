# Deliverables Convention

**Status:** draft
**Date:** 2026-04-09

## 1. Problem

Research projects produce shareable artifacts beyond manuscripts: progress reports for supervisors, slide decks for lab meetings, posters for conferences. These deliverables currently lack a standard location, naming convention, or tooling integration:

- **Reports** — questio-report generates ephemeral text with no persistence
- **Presentations** — placed ad-hoc (e.g., `docs/assets/presentations/` in pixecog)
- **Posters** — no convention at all

All three share a pattern: they aggregate internal data (plan, results, figures, citations) into polished artifacts for external audiences. They are distinct from notes (atomic knowledge records in `docs/log/`) and manuscripts (journal-targeted long-form writing in `docs/manuscript/`).

## 2. Design Principles

1. **Deliverables are not notes.** Notes are atomic, internally-referenced knowledge records. Deliverables are assembled artifacts for external consumption. Mixing them in `docs/log/` would pollute note searches and blur the note type taxonomy.
2. **Deliverables are not manuscripts.** Manuscripts target journal publication with formal structure (sections, citations, peer review). Deliverables are shorter-lived, audience-specific, and may use different formats (slides, poster layout, summary markdown).
3. **Convention over tooling.** The directory layout and frontmatter schema are the convention. Tooling (index generation, skill-based creation) builds on top but is optional.
4. **Graceful degradation.** Projects without `docs/deliverables/` are unaffected. Tools skip deliverables indexing when the directory is absent.

## 3. Directory Layout

```
docs/deliverables/
  index.md                              # auto-generated overview (by questio_docs_collect)
  mkdocs.yml                            # sub-nav for MkDocs monorepo plugin
  reports/
    index.md                            # auto-generated report list
    report-YYYY-MM-DD.md                # one file per report
  presentations/
    index.md                            # auto-generated presentation list
    YYYY-MM-event-slug/                 # one directory per deck
      slides.md                         # slide content (markdown, or pointer to .pptx/.pdf)
      assets/                           # deck-specific images, diagrams
  posters/
    index.md                            # auto-generated poster list
    YYYY-MM-event-slug/                 # one directory per poster
      poster.md                         # poster content or build spec
      assets/                           # poster-specific panels, figures
```

### Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Report | `report-YYYY-MM-DD.md` | `report-2026-04-09.md` |
| Presentation | `YYYY-MM-event-slug/` | `2026-04-tdmn-project-overview/` |
| Poster | `YYYY-MM-event-slug/` | `2026-06-fens-swr-detection/` |

Reports are single files (markdown). Presentations and posters are directories because they typically include supporting assets (images, exported figures, build artifacts).

## 4. Frontmatter Schema

All deliverable files use YAML frontmatter for indexing and cross-referencing:

```yaml
---
title: "Weekly Progress Report"
date: 2026-04-09
type: report              # report | presentation | poster
audience: supervisor      # supervisor | team | conference | public
event: ""                 # conference/meeting name (presentations, posters)
period: ""                # time window covered (reports: "2026-04-03 to 2026-04-09")
questions: []             # questio question IDs referenced (e.g., [H1, H3])
tags: []                  # free-form tags
---
```

### Field Reference

| Field | Required | Types | Description |
|-------|----------|-------|-------------|
| `title` | yes | all | Human-readable title |
| `date` | yes | all | Creation or presentation date |
| `type` | yes | all | One of: `report`, `presentation`, `poster` |
| `audience` | yes | all | Target audience category |
| `event` | no | presentation, poster | Conference, workshop, or meeting name |
| `period` | no | report | Time window the report covers |
| `questions` | no | all | Questio question IDs this deliverable references |
| `tags` | no | all | Free-form tags for search |

## 5. Relationship to Existing Layers

```
docs/plan/           ──→  docs/deliverables/reports/     (progress aggregation)
docs/log/result/     ──→  docs/deliverables/reports/     (evidence summarization)
docs/log/result/     ──→  docs/deliverables/presentations/ (key results in slides)
figio figures        ──→  docs/deliverables/presentations/ (embedded figures)
figio figures        ──→  docs/deliverables/posters/       (panel composition)
biblio citations     ──→  docs/deliverables/posters/       (reference panels)
docs/manuscript/     ───  docs/deliverables/               (separate: different audience, lifecycle)
```

### How Each Type Is Produced

| Deliverable | Primary Skill | Data Sources | Output |
|-------------|--------------|--------------|--------|
| Report | `questio-report` | questio_status, result notes, pipeline status | `reports/report-YYYY-MM-DD.md` |
| Presentation | (manual or project-level skill) | results, figures, plan status | `presentations/YYYY-MM-slug/slides.md` |
| Poster | (manual or project-level skill) | results, figures, citations | `posters/YYYY-MM-slug/poster.md` |

## 6. Indexing

`questio_docs_collect()` generates index pages when `docs/deliverables/` exists:

- `docs/deliverables/index.md` — overview with counts and recent deliverables across all types
- `docs/deliverables/reports/index.md` — chronological report list with period and audience
- `docs/deliverables/presentations/index.md` — presentation list with event and date
- `docs/deliverables/posters/index.md` — poster list with event and date
- `docs/deliverables/mkdocs.yml` — sub-nav for MkDocs monorepo `!include`

Index pages are auto-generated and should not be hand-edited. They are regenerated on every `questio_docs_collect()` call.

## 7. MkDocs Integration

Study projects wire deliverables into their MkDocs nav via the monorepo plugin:

```yaml
# in project root mkdocs.yml
nav:
  # ...
  - Deliverables: '!include ./docs/deliverables/mkdocs.yml'
```

The generated `docs/deliverables/mkdocs.yml` follows the same pattern as `docs/log/mkdocs.yml`:

```yaml
site_name: deliverables
docs_dir: .
nav:
  - Overview: index.md
  - Reports: reports/index.md
  - Presentations: presentations/index.md
  - Posters: posters/index.md
```

## 8. Future: Figio Poster Composition

Figio's multi-panel composition model (FigureSpec YAML → panel rendering → SVG composition → PDF export) maps naturally to conference poster layout. A poster could be defined as a FigureSpec with:

- Large canvas dimensions (A0, A1)
- Grid/mosaic layout for content panels
- Text block panels for title, methods, conclusions
- Figure panels referencing existing figio outputs
- Annotation layer for logos, affiliations, QR codes

This is future work — tracked as an idea note. The current convention supports manual poster creation; figio integration would automate the build step.
