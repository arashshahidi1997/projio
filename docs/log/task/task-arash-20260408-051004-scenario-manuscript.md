---
title: "Scenario book: drafting manuscript results from accumulated evidence"
date: 2026-04-08
timestamp: 20260408-051004
status: done
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: drafting manuscript results from accumulated evidence

## Goal

Write a scenario showing a researcher who has accumulated enough evidence for hypothesis H2 (spindle topography) and now wants to draft the results section with publication-quality figures.

## Context

This scenario exercises the **evidence-to-manuscript workflow**: questio-ready check → evidence collection → figure design with figio → manuscript section drafting with manuscripto. It's the payoff phase — where all the careful evidence recording finally produces a manuscript section.

The scenario should be written at `docs/specs/research-orchestration/scenarios/scenario-manuscript-drafting.md`.

**Pixecog context:**
- H2: "What are the cortical origins of ripple-driving spindles?" — milestones: spindle-detection-validated, spindle-topography-mapped
- Manuscript section: `results/h2-spindle-origins`
- Existing manuscript structure at `docs/manuscript/pixecog/` with intro, methods, placeholder results
- Methods section (10.5 KB) describes 5 rats, ECoG 512 contacts, Neuropixels 212 contacts
- Figures needed: spindle topography heatmaps, detection rate distributions, spatial maps
- figio can produce FigureSpec YAML → panel rendering → SVG composition → PDF/PNG
- manuscripto: `manuscript_section_context`, `manuscript_assemble`, `manuscript_build`, `manuscript_cite_check`
- biblio: `manuscript_cite_suggest` for finding missing citations

## Prompt

Write the scenario at `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/scenario-manuscript-drafting.md`.

**Step 1: Read context.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` for format
- Read pixecog's manuscript structure if accessible
- Read the figio design spec if it exists (check `/storage2/arash/projects/projio/docs/specs/figio/`)

**Step 2: Write the scenario.**

Structure:
1. **Header** with starting state: H2 milestones are complete, evidence is recorded, manuscript section is a placeholder
2. **Phase 1: Readiness check** — researcher says "H2 should have enough evidence now. Can we draft the results?" Agent calls `questio_status("H2")` — confirms both milestones complete with validated evidence. Calls `questio_gap("H2")` — no gaps. Uses the `questio-ready` skill pattern: "H2 has sufficient evidence, manuscript section results/h2-spindle-origins is draftable."
3. **Phase 2: Evidence collection** — Agent gathers all result notes for H2: `note_search(tags=["result"], series="spectrogram_burst")`. Retrieves 3-4 result notes with metrics, figures, and observations. Presents a structured evidence summary to the researcher.
4. **Phase 3: Figure design** — Researcher says "I need a figure showing the spindle topography across the cortical surface." Agent uses `figio_figure_list` to check existing specs, then proposes a FigureSpec YAML for a multi-panel figure: (A) mean spindle rate per contact, (B) spindle amplitude heatmap, (C) example waveforms from key regions. Uses `figio_edit_spec` and `figio_build` to create the figure. Iterate on layout based on human feedback.
5. **Phase 4: Section drafting** — Agent uses `manuscript_section_context("results/h2-spindle-origins")` to get the template and surrounding context. Drafts the results section, weaving evidence from result notes into scientific prose. Uses `manuscript_cite_check` to verify all claims have citations, `manuscript_cite_suggest` for any gaps.
6. **Phase 5: Build and review** — `manuscript_assemble` to compile the full manuscript, `manuscript_build` to render PDF. Researcher reviews, gives feedback on prose ("too much detail on methods here, that belongs in the Methods section"). Agent iterates.
7. **Phase 6: Polish** — `manuscript_journal_check` to verify formatting against target journal requirements. Final commit.

Use mkdocs material admonitions:
- `!!! info "Behind the scenes"` for tool calls
- `!!! tip "Evidence trail"` for showing how result notes feed into prose
- `!!! example "Generated figure"` for figio output descriptions
- `!!! warning "Human checkpoint"` for prose quality review
- `!!! note "Citation management"` for biblio/cite_check details

End with: ecosystem coverage (questio + figio + manuscripto + biblio — the full publication pipeline), loop patterns, key insight (answer: the manuscript writes itself when evidence is properly structured — questio-record's structured frontmatter directly feeds manuscript drafting).

**Step 3: Commit** with message: "Add scenario: drafting manuscript results from accumulated evidence"

## Acceptance Criteria

- [ ] File at `docs/specs/research-orchestration/scenarios/scenario-manuscript-drafting.md`
- [ ] Exercises questio (readiness), figio (figures), manuscripto (drafting/building), biblio (citations)
- [ ] Shows the evidence → figure → prose → build pipeline
- [ ] Iterate loop for figure design and prose refinement
- [ ] Uses mkdocs material admonitions
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `140acc720c2b`
- session: `49cfe4a4-561d-4bb8-8fb6-d01b2ac17020`
- batch duration: 801.3s
