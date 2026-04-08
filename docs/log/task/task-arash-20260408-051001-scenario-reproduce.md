---
title: "Scenario book: reproduce Siapas & Wilson 1998 coupling results"
date: 2026-04-08
timestamp: 20260408-051001
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260408-141417-096dd0/note.md
completed: 2026-04-08T14:14:18+02:00
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: reproduce Siapas & Wilson 1998 coupling results

## Goal

Write a scenario showing a researcher using projio to plan and execute reproduction of results from a classic paper (Siapas & Wilson 1998 — hippocampal-cortical spindle-ripple coupling) in their own dataset.

## Context

This scenario exercises the **biblio-heavy planning workflow**: the researcher starts from a paper, extracts the key claims and methods, maps them to their own hypotheses and pipelines, identifies gaps, and executes. It demonstrates how biblio, questio, codio, and pipeio compose for literature-driven research.

The scenario should be written at `docs/specs/research-orchestration/scenarios/scenario-reproduce-paper.md`.

**Pixecog context (use this for realistic details):**
- The paper `@siapas_1998` is cited in H2 ("What are the cortical origins of ripple-driving spindles?") in `plan/questions.yml`
- H2 milestones: `spindle-detection-validated`, `spindle-topography-mapped`
- Relevant flows: `spectrogram_burst` (spindle detection), `sharpwaveripple` (ripple detection), `coupling_spindle_ripple`
- cogpy has: `SpindleDetector`, `RippleDetector`, cross-correlogram tools
- The paper's key finding: temporal correlation between hippocampal ripples and cortical spindles, suggesting a hippocampo-cortical dialogue during sleep
- Pixecog has ECoG (512 contacts) + Neuropixels (212 contacts) simultaneous recordings — richer than the original paper's single-tetrode + EEG setup
- bib/srcbib/ contains the citation; PDFs may or may not be fetched

## Prompt

Write the scenario at `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/scenario-reproduce-paper.md`.

**Step 1: Read for context and format.**
- Read the existing scenario book: `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` — follow the same conversation format (Human:/Agent: blocks with tool calls shown behind the scenes)
- Read the loop mechanisms spec: `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md`
- Read pixecog's questions.yml: `/storage2/arash/projects/pixecog/plan/questions.yml` — for H2 details
- Read pixecog's milestones.yml: `/storage2/arash/projects/pixecog/plan/milestones.yml`

**Step 2: Write the scenario.**

Structure:
1. **Header** with title, metadata, starting state, what the researcher wants
2. **Phase 1: Paper deep dive** — researcher says "I want to reproduce Siapas & Wilson 1998 results in our data." Agent uses `paper_context("@siapas_1998")`, `biblio_enrich`, potentially `biblio_pdf_fetch` if PDF is missing, then `biblio_docling` to extract methods details. Agent synthesizes: key claims, methods used, expected values, what's reproducible with pixecog's setup.
3. **Phase 2: Map to hypotheses** — Agent calls `questio_status`, identifies H2 maps to this paper. Checks `questio_gap("H2")` — what milestones are needed. Shows the researcher how the paper's claims map to their hypothesis structure.
4. **Phase 3: Audit existing capabilities** — Agent calls `codio_discover("spindle detection")`, `codio_get("cogpy")`, `pipeio_flow_status("spectrogram_burst")`, `pipeio_flow_status("coupling_spindle_ripple")`. Reports: what code exists, what flows are configured, what's missing.
5. **Phase 4: Identify gaps and plan** — Agent synthesizes: "The paper uses cross-correlogram analysis. cogpy has cross_correlogram tools. But the coupling_spindle_ripple flow expects spindle detection output that doesn't exist yet (spindle-detection-validated is not_started). We need to run spectrogram_burst first." Creates an execution plan.
6. **Phase 5: Execute first step** — Enter iterate loop for spindle detection. Run for one subject, assess, human gives feedback. Show 1-2 iterations.
7. **Phase 6: Record and plan forward** — Record observation notes, show what the next session would tackle.

Use mkdocs material admonitions throughout:
- `!!! info "Behind the scenes"` — for tool calls
- `!!! tip "Why this matters"` — for explaining design decisions
- `!!! warning "Human checkpoint"` — for moments requiring human judgment
- `!!! example "What the agent sees"` — for tool output summaries
- `!!! note` — for general explanations

Include at the end:
- **Ecosystem coverage** table showing which projio subsystems were used
- **Loop patterns** used in the scenario
- **Key insight** — what this scenario demonstrates that others don't (answer: literature-first planning, where the paper drives the agenda)

**Step 3: Ensure the file has proper mkdocs frontmatter** if needed (or just a markdown title).

**Step 4: Commit** with message: "Add scenario: reproduce Siapas & Wilson 1998 coupling results"

## Acceptance Criteria

- [ ] File at `docs/specs/research-orchestration/scenarios/scenario-reproduce-paper.md`
- [ ] Realistic conversation format matching scenario-book.md style
- [ ] Uses actual pixecog details (citekeys, flow names, cogpy modules, milestone names)
- [ ] Exercises biblio, questio, codio, pipeio in a natural flow
- [ ] Uses mkdocs material admonitions
- [ ] Shows both orient and iterate loop patterns
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `140acc720c2b`
- session: `49cfe4a4-561d-4bb8-8fb6-d01b2ac17020`
- batch duration: 801.3s
