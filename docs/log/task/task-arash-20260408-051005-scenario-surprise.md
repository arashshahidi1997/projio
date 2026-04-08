---
title: "Scenario book: unexpected finding leads to new hypothesis"
date: 2026-04-08
timestamp: 20260408-051005
status: done
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: unexpected finding leads to new hypothesis

## Goal

Write a scenario showing an unexpected result during routine analysis that leads the researcher to formulate a new exploratory question, extending the questio data model.

## Context

This scenario exercises the **discovery workflow** — the most scientifically valuable but hardest to automate. The agent detects something anomalous during an iterate loop, flags it (rather than silently continuing), and helps the researcher develop it into a new research question.

The scenario should be written at `docs/specs/research-orchestration/scenarios/scenario-unexpected-finding.md`.

**Pixecog context:**
- During SWR detection validation (sharpwaveripple flow), the agent notices a bimodal distribution of ripple durations — short ripples (~50ms) and long ripples (~120ms)
- Literature (Buzsaki 2015, Fernandez-Ruiz 2019) distinguishes "single ripples" from "ripple complexes" but pixecog's current detection treats them uniformly
- This could have implications for H1 (delta-ripple coupling) — do short and long ripples have different cortical correlates?
- This is NOT in the current questions.yml — it's a genuinely new observation
- cogpy's RippleDetector outputs duration as a feature but it's not currently used for classification
- The existing H1-H7 all treat ripples as a monolithic category

## Prompt

Write the scenario at `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/scenario-unexpected-finding.md`.

**Step 1: Read context.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` for format
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md`
- Read pixecog's questions.yml for current hypothesis structure

**Step 2: Write the scenario.**

Structure:
1. **Header** with starting state: agent is in the middle of an iterate loop for SWR detection validation (mid-Scenario 1, so to speak)
2. **Phase 1: The surprise** — during routine SWR validation, the agent reads detection output and notices the duration histogram is clearly bimodal. Instead of silently recording "detection rate: 12.3/min, looks good" and moving on, the agent flags it: "I notice the ripple duration distribution is bimodal (peaks at ~50ms and ~120ms). This wasn't expected from the grounding phase. Want me to investigate?"
3. **Phase 2: Investigation** — researcher says "yes, investigate." Agent enters investigate loop: checks literature (`paper_context` for ripple subtypes), checks if this is known in the field (`rag_query("ripple subtypes bimodal duration")`), checks if it's a detection artifact (inspects waveforms for short vs long events), checks cross-subject consistency.
4. **Phase 3: Literature grounding** — Agent finds that ripple complexes vs single ripples is a known distinction in literature. `biblio_discover_authors("Fernandez-Ruiz")` finds relevant papers. `biblio_graph_expand` discovers more recent work on ripple subtypes. Agent synthesizes: "This is a real phenomenon, not an artifact. Literature suggests short and long ripples may have different functions."
5. **Phase 4: New question formulation** — Researcher says "This is interesting. It could mean that different ripple types couple differently with cortical oscillations. Let's add an exploratory question." Agent helps formulate a new question:
   ```yaml
   Q8:
     text: "Do short and long ripples have distinct cortical coupling patterns?"
     type: exploratory
     pipelines: [sharpwaveripple, coupling_spindle_ripple]
     milestones: [ripple-subtype-classification, subtype-coupling-analysis]
   ```
6. **Phase 5: Update questio data model** — Agent updates `plan/questions.yml` with Q8, adds new milestones to `plan/milestones.yml`, proposes that this could modify the analysis plan for H1 (add ripple subtype as a variable). Uses propose-review-confirm.
7. **Phase 6: Record and plan** — Create observation notes documenting the discovery, a decision note recording the new question, and schedule follow-up analysis as worklog tasks.

Use mkdocs material admonitions:
- `!!! warning "Surprise detected"` for the moment the agent flags the anomaly
- `!!! info "Behind the scenes"` for tool calls
- `!!! tip "Why flagging matters"` for explaining why silent continuation would be wrong
- `!!! example "Literature says..."` for biblio findings
- `!!! note "Extending the data model"` for the questio update

End with: ecosystem coverage (questio extension, biblio discovery, notio recording), loop patterns (iterate → surprise → investigate → extend questio), key insight (answer: the agent's most valuable contribution isn't running pipelines — it's noticing things a human might miss during routine validation and connecting them to literature).

**Step 3: Commit** with message: "Add scenario: unexpected finding leads to new hypothesis"

## Acceptance Criteria

- [ ] File at `docs/specs/research-orchestration/scenarios/scenario-unexpected-finding.md`
- [ ] Shows the iterate → surprise → investigate transition
- [ ] Agent flags the anomaly rather than silently continuing
- [ ] Literature grounding confirms it's a real phenomenon
- [ ] New question added to questio data model
- [ ] Uses mkdocs material admonitions
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `140acc720c2b`
- session: `49cfe4a4-561d-4bb8-8fb6-d01b2ac17020`
- batch duration: 801.3s
