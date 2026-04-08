---
title: "Spec: reconcile design.md section 8 with agent-as-judge loop philosophy"
date: 2026-04-08
timestamp: 20260408-043832
status: done
actionable: true
source_note: "docs/specs/research-orchestration/design.md"
project_primary: projio
tags: [task, questio, spec]
---

# Spec: reconcile design.md section 8 with agent-as-judge loop philosophy

## Goal

Update section 8 of the questio design spec to reflect the agent-as-judge philosophy. The current spec assumes pre-scripted validation notebooks and rigid QC schemas. The updated version should position the agent (Claude Code) as the assessment layer, with skills teaching investigation strategy rather than encoding domain-specific validation logic.

## Context

The current design.md section 8 has good structural framing (inner/middle/outer loops, action components, automation levels) but makes assumptions that we've since rejected:

1. **Section 8.2 inner loop** references "validation notebooks" as the assessment mechanism — but the agent should assess directly using tool outputs, not pre-scripted notebooks
2. **Sequence B (validation sweep)** describes running `validate_*` notebooks per subject — this is the artificial pattern we're replacing
3. **Section 8.5 automation levels** says inner loop is "fully automatable" — true, but the automation is agent reasoning over outputs, not notebook execution
4. The `questio-validate` skill in section 6.2 is described as "run validation notebook across subjects" — should be reframed as agent-driven assessment

The loop-mechanisms.md spec (task-arash-20260408-043830) defines the new patterns. This task makes design.md consistent with that spec.

## Prompt

Update `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md` sections 8 and 6.2 to reflect the agent-as-judge philosophy.

**Step 1: Read the full design spec** and the loop mechanisms spec (if it exists at `docs/specs/research-orchestration/loop-mechanisms.md`, otherwise read task-arash-20260408-043830 for the intended design).

**Step 2: Update section 8.2 (inner loop).**

Change the inner loop description from "agent iterates on a notebook" to "agent iterates on an analysis, using notebooks as one tool among many." The key change:
- Remove the assumption that validation = running a specific notebook
- The agent reads pipeline outputs (pipeio_target_paths, file inspection), compares against expectations (biblio context, prior results), and makes a judgment call
- Notebooks may be created/executed as part of this, but they're agent-authored during the loop, not pre-scripted templates
- Keep the SWR detection example but reframe it: the agent creates the validation analysis as part of the loop, it doesn't execute a pre-existing template

**Step 3: Update section 8.3 Sequence B (validation sweep).**

Rewrite to reflect agent-driven assessment:
- Instead of "for subject in subjects: run validate_* notebook", describe the agent inspecting outputs per subject using available tools
- The agent uses pipeio_nb_read, pipeio_target_paths, and direct file reading to assess outputs
- It compares against expectations set during grounding (literature values from paper_context)
- It creates observation notes for each assessment, then a final result note if satisfactory

**Step 4: Update section 6.2 skill table.**

- Reframe `questio-validate` from "run validation notebook" to "agent-driven assessment of pipeline output against grounded expectations"
- Add `questio-investigate` skill: "human-triggered deep dive into an anomaly or issue"
- Add note that `questio-iterate` replaces the standalone dispatch pattern — it's the execute-and-evaluate cycle within a human feedback loop
- Update `questio-ground` description to mention it feeds investigation context, not just pre-work context

**Step 5: Update section 8.5 automation levels.**

Adjust the table to reflect that:
- Inner loop automation depends on agent judgment quality, not notebook scripting
- The "human role" for inner loop should include "review agent's assessment rationale" not just "set quality criteria upfront"
- Add the propose-review-confirm pattern as the default for milestone updates

**Step 6: Add a forward reference** from section 8 to the loop-mechanisms.md spec for the detailed investigate/iterate/orient patterns.

**Step 7: Commit** with message: "Reconcile questio design spec section 8 with agent-as-judge loop philosophy"

## Acceptance Criteria

- [ ] Section 8.2 inner loop no longer assumes pre-scripted validation notebooks
- [ ] Sequence B rewritten for agent-driven assessment
- [ ] Skill table updated with questio-investigate, questio-iterate reframing
- [ ] Automation levels reflect agent-as-judge model
- [ ] Forward reference to loop-mechanisms.md added
- [ ] No structural breakage to other sections
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `08b012e5b5c7`
- session: `f5d805ae-69f7-4207-809b-3ee4b88ea1bb`
- batch duration: 425.8s
