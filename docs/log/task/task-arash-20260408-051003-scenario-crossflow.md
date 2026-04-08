---
title: "Scenario book: debugging a cross-flow anomaly"
date: 2026-04-08
timestamp: 20260408-051003
status: done
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: debugging a cross-flow anomaly

## Goal

Write a scenario showing a researcher discovering that a downstream analysis (coupling_spindle_ripple) produces nonsensical results because of an upstream issue, and the agent tracing the problem across flow boundaries.

## Context

This scenario exercises the **investigate loop across multiple flows** — the hardest debugging pattern in pipeline-based research. The symptom appears in one flow but the cause is in another. This is where the agent's ability to navigate the full pipeio flow graph and cross-reference outputs is most valuable.

The scenario should be written at `docs/specs/research-orchestration/scenarios/scenario-cross-flow-debug.md`.

**Pixecog context:**
- Flow dependency chain: `preprocess_ieeg` → `sharpwaveripple` → `coupling_spindle_ripple`
- Also: `preprocess_ieeg` → `spectrogram_burst` → `coupling_spindle_ripple`
- coupling_spindle_ripple takes inputs from both SWR and spindle detection
- scripts in coupling: `cross_correlogram.py`, `spatial_coupling.py`, `report.py`
- The cross-correlogram should show a peak at ~100ms lag (spindle leads ripple) per literature
- Plausible failure: spectrogram_burst config has wrong frequency band → spindles are actually detecting beta oscillations → coupling results are meaningless
- pipeio tools: `pipeio_cross_flow`, `pipeio_log_parse`, `pipeio_mod_context`, `pipeio_target_paths`

## Prompt

Write the scenario at `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/scenario-cross-flow-debug.md`.

**Step 1: Read context.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` for format
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md` (section 2, investigate loop)
- Read pixecog flow configs if accessible

**Step 2: Write the scenario.**

Structure:
1. **Header** with starting state: coupling_spindle_ripple has been run, results look wrong
2. **Phase 1: Symptom** — researcher says "The cross-correlogram is flat — no coupling peak. But Sirota 2003 and Siapas 1998 both show clear spindle-ripple coupling. Something is wrong." Agent enters investigate loop.
3. **Phase 2: Reproduce and scope** — Agent reads coupling outputs (`pipeio_target_paths("coupling_spindle_ripple")`), confirms flat correlogram. Checks: is it all subjects or just some? All subjects → systemic issue, not subject-specific.
4. **Phase 3: Check coupling code** — Agent reads `pipeio_mod_context("coupling_spindle_ripple", "cross_correlogram")`. Code looks correct — it's computing cross-correlogram between spindle events and ripple events. The issue is upstream.
5. **Phase 4: Trace upstream — ripple detection** — Agent checks `pipeio_target_paths("sharpwaveripple")`, reads SWR detection output. Detection rates look reasonable (12/min). Ripple detection seems fine.
6. **Phase 5: Trace upstream — spindle detection** — Agent checks `pipeio_target_paths("spectrogram_burst")`, reads spindle detection output. Detection rate is 25/min — unusually high for spindles (literature: 5-10/min during NREM). The agent checks the spectrogram_burst config: **frequency band is set to 15-30 Hz instead of 10-16 Hz** → it's detecting beta oscillations, not spindles.
7. **Phase 6: Root cause and fix** — Agent presents: "The spectrogram_burst config has freq_band: [15, 30] which captures beta, not spindles. Should be [10, 16]. This explains the flat coupling — beta events have no temporal relationship with ripples." Creates observation notes tracing the full investigation.
8. **Phase 7: Fix and re-run** — Human confirms the fix. Agent updates config, enters iterate loop: re-run spindle detection → re-run coupling → check correlogram. Now shows expected peak at ~100ms.
9. **Phase 8: Record** — Observation notes from investigation, result notes after fix confirmed. Decision note: "Spindle frequency band corrected from [15,30] to [10,16]."

Use mkdocs material admonitions:
- `!!! danger "The trap"` — for the moment where the wrong flow is initially suspected
- `!!! info "Behind the scenes"` for tool calls
- `!!! tip "Investigation pattern"` for explaining the diagnostic strategy
- `!!! warning "Human checkpoint"` before applying the fix

End with: ecosystem coverage, loop patterns (investigate → iterate transition), and key insight (answer: cross-flow debugging requires tracing the full dependency chain — the symptom is never where the cause is).

**Step 3: Commit** with message: "Add scenario: debugging a cross-flow anomaly"

## Acceptance Criteria

- [ ] File at `docs/specs/research-orchestration/scenarios/scenario-cross-flow-debug.md`
- [ ] Shows full investigate loop: reproduce → scope → check downstream → trace upstream → root cause
- [ ] Transitions from investigate to iterate (fix and re-run)
- [ ] Uses pipeio cross-flow tools realistically
- [ ] Root cause is in a different flow than the symptom
- [ ] Uses mkdocs material admonitions
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `140acc720c2b`
- session: `49cfe4a4-561d-4bb8-8fb6-d01b2ac17020`
- batch duration: 801.3s
