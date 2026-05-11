---
title: "Handbook references: populate references.md + add Further reading per chapter"
date: 2026-05-11
timestamp: 20260511-handbook-references
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260511-190231-905cdb/note.md
completed: 2026-05-11T19:02:33+02:00
actionable: true
prompt: ""
source_note: docs/handbook/references.md
project_primary: projio
priority: medium
due: ""
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [handbook, writing, stack-axis, agentic-workshop-2026-09, references]
model_hint: sonnet
---

## Task

Populate the handbook references in two places:

1. **Per-chapter `## Further reading` section** appended to each of the 33
   chapter-body files (the prose drafts that landed earlier today),
   listing 3–5 external references the chapter cites or that a reader
   would follow next.

2. **Handbook-wide `references.md`** — flesh out the existing stub at
   `docs/handbook/references.md` with the full inspirations bibliography
   AND a per-chapter aggregation index pointing readers to each
   chapter's Further reading.

User directive (2026-05-11): *"add references for the whole handbook
and/or per chapter. for instance goodresearch.dev was an important
inspiration to me."*

## Inputs

- All 33 chapter-body files under `docs/handbook/{00-frame,10-bids,20-datalad,30-snakemake,40-marimo,50-publication,60-projio,70-agentic,80-orchestration}/*.md` plus `99-honest-gaps.md`
- Existing `docs/handbook/references.md` stub (has the inspirations list already; needs the per-chapter aggregation populated)
- Idea note inspirations table: [`docs/log/idea/idea-arash-20260507-221835-382557.md`](../idea/idea-arash-20260507-221835-382557.md) §"Inspirations / reading list"
- 2 chapters from the new `90-future-directions/` may not yet have prose at the time this runs — handle gracefully (skip if `## TBD` still present)

## Per-chapter Further reading section

For each chapter file, append at the very end (after all existing content) a section:

```markdown
## Further reading

- [Title](https://url) — brief one-line reason it's relevant.
- ...
```

Selection criteria for each chapter:
- **Tools/libraries the chapter introduces:** primary docs URL (e.g. BIDS spec; DataLad handbook; Snakemake docs; Marimo docs; HoloViews; Quarto; mkdocs-material).
- **Solo-author / handbook influences relevant to that chapter:** e.g. Wickham for tooling-as-prose chapters (40-marimo, 50-publication); goodresearch.dev for `00-frame/` chapters; Ciechanowski for explorables chapter (`40-marimo/handbook-explorables.md`); Willison for note-to-blog cadence (`80-orchestration/`); etc.
- **Standards / specs:** BIDS spec; CFF citation file format; CITATION.cff; Snakemake catalog.
- **Original papers / posts** where one exists and is well-known (e.g. Karpathy "Recipe for Training Neural Networks" for the agentic chapters; Andy Matuschak's evergreen-notes essay for notio).
- **Honest scope:** Choose 3–5 per chapter — not exhaustive bibliography. Prefer authoritative URLs (project homepages, official docs, primary essays) over secondary sources.

Specific high-priority entries (must appear where applicable):
- **goodresearch.dev** (Mineault) — must appear in `00-frame/why-this-stack.md` Further reading (per user emphasis: "an important inspiration to me")
- **Deep Research PDF** (`reference/research/Interactive Mathematics Beyond the Static Page.pdf`) — already cited in `00-frame/why-interactivity.md`; also link from `00-frame/single-author-fragility.md`
- **Claude Agents SDK** — appears in `70-agentic/captures-tasks-queues.md` and forward-references the future-directions chapter
- **xarray + HoloViews docs** — must appear in `40-marimo/analysis-notebooks.md` Further reading (the separate `task-arash-20260511-handbook-40-marimo-holoviews.md` patch adds them in prose; ensure they also appear in Further reading)
- **NeuroPySeminar archive at `teaching/NeuroPySeminar/`** — appears in the foundation chapters as port source acknowledgment (10-bids, 20-datalad, 30-snakemake)

## References.md aggregation

After per-chapter sections land, replace the placeholder section in
`docs/handbook/references.md`:

```markdown
## Per-chapter further reading

> **Status:** populated by chapter prose. ...
```

with a real **per-chapter index** that mirrors each chapter's Further
reading list — one H3 per chapter directory, bulleted aggregation under
each. Format:

```markdown
## Per-chapter further reading

### 00-frame
- [Title](url) — relevance (also linked from `00-frame/why-this-stack.md`)
- ...

### 10-bids
- ...
```

Top of `references.md` (the existing inspirations list under
"Inspirations (handbook-wide)") stays as-is unless you can add 1–2
high-value inspirations not already listed. Keep the **goodresearch.dev
primary** framing.

## Hard rules

- **Append-only to chapter bodies.** Do not touch the admonition blocks or existing prose. Add Further reading at the end as a new H2.
- **No fabricated URLs.** Only link to real, well-known project pages or documents. If unsure, omit rather than invent.
- **Per-chapter sections must be present in every chapter file** (33 chapter files + 99-honest-gaps + 2 future-directions = 36 total). If a chapter has no relevant external references (rare), include 2–3 stack-component or cross-link entries instead.
- **References.md per-chapter index** mirrors each chapter's Further reading section verbatim (no extra entries, no missing ones).
- Build validation: `conda run -n rag python -m mkdocs build --strict` should pass after edits. Treat any new ERROR-level warnings as blockers; INFO/WARNING pre-existing notio link warnings stay.

## Acceptance

- All 33 + 99-honest-gaps + 2 future-directions chapter files have a `## Further reading` section appended
- Each section has 3–5 entries with one-line relevance notes
- `goodresearch.dev` appears in `00-frame/why-this-stack.md` Further reading
- HoloViews + xarray docs appear in `40-marimo/analysis-notebooks.md` Further reading
- `references.md` per-chapter aggregation section is populated and mirrors per-chapter content
- Strict build passes
