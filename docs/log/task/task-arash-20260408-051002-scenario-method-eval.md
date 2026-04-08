---
title: "Scenario book: evaluating a new detection method from recent literature"
date: 2026-04-08
timestamp: 20260408-051002
status: done
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: evaluating a new detection method from recent literature

## Goal

Write a scenario showing a researcher discovering a new paper with a better spindle detection algorithm, evaluating whether to adopt it, benchmarking against their current approach, and making a recorded decision.

## Context

This scenario exercises the **method evaluation workflow**: literature discovery → code audit → benchmark → decision. It's a common real-world pattern — a new paper comes out, and you need to decide whether it's worth changing your approach.

The scenario should be written at `docs/specs/research-orchestration/scenarios/scenario-method-evaluation.md`.

**Pixecog context:**
- Current spindle detection: cogpy has `SpindleDetector` class in `cogpy.detect`
- Relevant flow: `spectrogram_burst` with scripts for spectrogram computation and blob detection
- H2 and H3 both depend on spindle detection quality
- Milestone: `spindle-detection-validated` is not_started
- The researcher reads Pedrosa 2024 (`@pedrosa_2024`, cited in H2 and H4) which describes an improved spindle detection approach
- biblio can discover related papers via `biblio_discover_authors`, `biblio_graph_expand`

## Prompt

Write the scenario at `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/scenario-method-evaluation.md`.

**Step 1: Read context.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` for format
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md`
- Read pixecog's questions.yml and milestones.yml for hypothesis/milestone details

**Step 2: Write the scenario.**

Structure:
1. **Header** with starting state and researcher's goal
2. **Phase 1: Literature trigger** — researcher says "I just read Pedrosa 2024 and their spindle detection looks better than ours. Should we switch?" Agent uses `paper_context("@pedrosa_2024")` to extract their method details. Then `biblio_discover_authors("Pedrosa")` and `biblio_graph_expand("@pedrosa_2024")` to find related work and validate the method's reception.
3. **Phase 2: Current method audit** — Agent uses `codio_get("cogpy")` and `codio_discover("spindle detection")` to understand the current SpindleDetector implementation. `pipeio_mod_context("spectrogram_burst", "blob_detect")` to see how it's used in the pipeline. Presents a comparison: current approach vs paper's approach.
4. **Phase 3: Benchmark design** — Agent proposes a benchmark: run both methods on one subject, compare detection rates, temporal precision, and false positive rates. Uses the iterate loop. Human approves the plan.
5. **Phase 4: Benchmark execution** — 2-3 iterate cycles: run current method → run new method (implemented in a notebook) → compare metrics. Agent presents side-by-side comparison. Use `paper_context` to check against literature-reported values.
6. **Phase 5: Decision** — Agent presents findings. Human decides (e.g., "the new method is marginally better but not worth the migration cost" or "yes, let's adopt it"). Agent creates a decision note with rationale.
7. **Phase 6: Record** — Decision note captures: what was compared, metrics, rationale, implications for milestones. If adopting: create issues for code migration. If not: record why, so future agents don't re-evaluate.

Use mkdocs material admonitions:
- `!!! info "Behind the scenes"` for tool calls
- `!!! tip "Why this matters"` for design insights
- `!!! warning "Human checkpoint"` for judgment calls
- `!!! note "Decision recording"` for explaining why decisions are captured

End with ecosystem coverage, loop patterns, and key insight (answer: method evaluation as a first-class workflow — the decision to NOT change is as valuable as the decision to change).

**Step 3: Commit** with message: "Add scenario: evaluating a new detection method from literature"

## Acceptance Criteria

- [ ] File at `docs/specs/research-orchestration/scenarios/scenario-method-evaluation.md`
- [ ] Exercises biblio (discovery, enrichment, graph expand), codio, pipeio, questio
- [ ] Shows the iterate loop used for benchmarking
- [ ] Decision recording is explicit — captures the "why" regardless of outcome
- [ ] Uses mkdocs material admonitions
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `140acc720c2b`
- session: `49cfe4a4-561d-4bb8-8fb6-d01b2ac17020`
- batch duration: 801.3s
