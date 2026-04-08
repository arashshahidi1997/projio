# Scenario: Unexpected Finding Leads to New Hypothesis

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Milestone `swr-detection-validated` is being worked on (iterate loop in progress)
- The agent has just finished running sharpwaveripple detection for sub-01 and is assessing results
- Detection rate looks fine (12.3/min, within literature range)
- The researcher is expecting a routine "looks good, run all subjects" report
- 7 hypotheses defined in questions.yml, none about ripple subtypes

**What the researcher wants:** Routine SWR validation. What they get: a discovery that changes the analysis plan.

---

## Phase 1: The surprise — "Wait, this doesn't look right"

The agent is in the middle of a routine iterate loop assessment for SWR detection. It reads the detection output for sub-01 and starts the standard checks.

!!! info "Behind the scenes"
    ```
    → pipeio_target_paths("sharpwaveripple", group="detect", member="sub-01")
      → reads detection output: event times, durations, amplitudes, frequencies

    → [standard assessment against literature expectations]
      Rate: 12.3/min — ✓ within range (10-15/min)
      Frequency: 142 Hz — ✓ within range (100-300 Hz)
      Mean duration: 62 ms — ✓ within range (30-100 ms)

    → [agent examines duration distribution more closely]
      Duration histogram is BIMODAL:
        Peak 1: 48 ± 8 ms (N = 412 events)
        Peak 2: 118 ± 22 ms (N = 186 events)
        Clear valley at ~80 ms
    ```

!!! warning "Surprise detected"
    A routine assessment would report "12.3/min, looks good" and move on. But the agent noticed the bimodal duration distribution — something that wasn't in the grounding expectations and wasn't part of the validation criteria. This is the moment where the agent earns its keep.

```
Agent: SWR detection for sub-01 looks good on the main metrics:
       - Rate: 12.3/min ✓
       - Frequency: 142 Hz ✓
       - Mean duration: 62 ms ✓

       **However, I notice something unexpected.** The ripple duration
       distribution is clearly bimodal:
       - Short ripples: 48 ± 8 ms (N=412, 69%)
       - Long ripples: 118 ± 22 ms (N=186, 31%)
       - Clear separation at ~80 ms

       This wasn't flagged during grounding. A unimodal distribution
       centered around 50-60 ms would be typical. The bimodality suggests
       two distinct event types.

       This could be:
       1. A detection artifact (long events are merged short events)
       2. A real distinction (ripple complexes vs single ripples)

       Want me to investigate, or should I proceed with the standard
       validation?
```

!!! tip "Why flagging matters"
    If the agent had silently continued — reporting only the aggregate rate and frequency — this finding would be buried. The bimodality might show up later in the coupling analysis as noise or as a confusing secondary peak. By flagging it now, during the detection validation phase, the researcher can decide whether to investigate or defer. Silent continuation would be the wrong call because: (1) it violates the iterate loop's assess step — assessment means looking at the data, not just checking boxes, and (2) the finding may affect downstream analyses (coupling patterns may differ between short and long ripples).

---

## Phase 2: Investigation — "Is this real?"

```
Human: Investigate. Is this a detection artifact or something real?
```

!!! info "Behind the scenes"
    ```
    → pipeio_mod_context("sharpwaveripple", "detect_swr")
      Returns: detection script uses bandpass 100-300 Hz, amplitude threshold
               3.5 SD, min duration 25ms, no max duration, merge_gap 15ms

    → [agent checks: could long events be merged short events?]
      Merge gap is 15ms. If two short ripples occur within 15ms, they merge.
      But: inspecting the long events, they show continuous oscillation
      (not two bursts with a gap). The 118ms events are single sustained
      oscillations, not merged pairs.

    → note_create(note_type="idea",
                  tags=["observation", "investigate"],
                  series="sharpwaveripple",
                  title="Investigation: long ripples are sustained oscillations, not merged events")
    ```

```
Agent: **Artifact check:** the long events are NOT merged short events.
       Inspecting the raw waveforms:
       - Short events (~48ms): 5-7 cycles, clean oscillation, sharp onset
       - Long events (~118ms): 12-15 cycles, sometimes with amplitude
         modulation, gradual onset

       These look like genuinely different event types, not detection
       artifacts. The merge gap (15ms) is too short to explain 118ms events.

       Let me check the literature — is this a known distinction?
```

---

## Phase 3: Literature grounding — "What does the field say?"

!!! info "Behind the scenes"
    ```
    → rag_query("ripple subtypes bimodal duration short long")
      Returns: sparse results — not well-covered in indexed papers

    → paper_context("@buzsaki_2015_HippocampalSharp")
      Returns: comprehensive SWR review. Mentions "ripple complexes" —
               prolonged ripple events associated with stronger memory reactivation

    → biblio_discover_authors("Fernandez-Ruiz")
      Returns: 8 papers, including Fernandez-Ruiz 2019 "Long-duration
               hippocampal sharp wave ripples improve memory"

    → biblio_ingest(dois=["10.1126/science.aax0758"])
      Returns: ingested @fernandez-ruiz_2019_LongDuration

    → paper_context("@fernandez-ruiz_2019_LongDuration")
      Returns: key finding — long-duration SWRs (>100ms) are associated
               with stronger replay and better memory consolidation.
               Duration bimodality is a feature, not noise.

    → biblio_graph_expand("@fernandez-ruiz_2019_LongDuration")
      Returns: 15 citing works, including:
               - Xu 2023: long ripples correlate with cortical activation patterns
               - Tang 2021: ripple duration predicts learning performance
    ```

!!! example "Literature says..."
    The bimodality is a **known phenomenon** in the field. Fernandez-Ruiz et al. 2019 (Science) showed that long-duration SWRs (>100ms) are functionally distinct from short SWRs — they're associated with stronger hippocampal replay and better memory consolidation. Multiple subsequent papers have confirmed and extended this finding.

```
Agent: **Literature confirms this is real.**

       **Key paper:** Fernandez-Ruiz et al. 2019 (Science) —
       "Long-duration hippocampal sharp wave ripples improve memory"

       **What they found:**
       - SWR duration is bimodal (~50ms and ~100-120ms peaks)
       - Long SWRs show stronger replay content
       - Long SWRs predict behavioral memory performance
       - The distinction is not a detection artifact — it reflects
         different hippocampal network states

       **Subsequent work:**
       - Xu 2023: long ripples correlate with specific cortical activation
       - Tang 2021: ripple duration predicts learning performance in tasks

       **Relevance to pixecog:**
       Our bimodality (48ms vs 118ms) matches their distribution almost
       exactly. This means:
       1. Our detection is working correctly (we're seeing the real thing)
       2. Short and long ripples may have different cortical coupling patterns
       3. This could affect H1-H5 if we don't account for ripple subtype

       This is not just a validation detail — it's a potential new question.
       Should we explore further?
```

---

## Phase 4: New question formulation — "This changes things"

```
Human: This is interesting. If different ripple types couple differently
       with cortical oscillations, that could affect all our coupling
       hypotheses. Let's add an exploratory question.
```

```
Agent: **Proposed new question:**

       ```yaml
       Q8:
         text: "Do short and long ripples have distinct cortical coupling patterns?"
         type: exploratory
         prediction: >
           Long-duration ripples (>80ms) show stronger and more widespread
           cortical coupling than short ripples, particularly in association cortex
         pipelines: [sharpwaveripple, coupling_spindle_ripple]
         milestones:
           - ripple-subtype-classification
           - subtype-coupling-comparison
         manuscript_section: results/q8-ripple-subtypes
         status: not_started
         depends_on: []
         citations:
           - "@fernandez-ruiz_2019_LongDuration"
           - "@buzsaki_2015_HippocampalSharp"
       ```

       **Proposed new milestones:**

       ```yaml
       ripple-subtype-classification:
         description: "Classify ripples into short (<80ms) and long (>80ms) subtypes"
         flow: sharpwaveripple
         pipelines: [sharpwaveripple]
         depends_on: [swr-detection-validated]
         status: not_started
         evidence: []

       subtype-coupling-comparison:
         description: "Compare cortical coupling patterns between ripple subtypes"
         flow: coupling_spindle_ripple
         pipelines: [coupling_spindle_ripple]
         depends_on: [ripple-subtype-classification, spindle-detection-validated]
         status: not_started
         evidence: []
       ```

       **Impact on existing hypotheses:**
       - H1 (delta-ripple coupling): consider adding subtype as a variable
       - H3 (spindle amplitude → ripple probability): long ripples may have
         different coupling with spindle amplitude
       - H5 (ripple-band power propagation): long ripples may propagate
         more strongly

       This doesn't invalidate existing hypotheses — it adds a new
       dimension. Want me to update questions.yml and milestones.yml?
```

!!! note "Extending the data model"
    The new question follows the same schema as existing questions. It references existing pipelines (no new code needed — just a classification step and a conditional coupling analysis). The milestones slot into the existing dependency chain. The agent has designed Q8 to be minimally disruptive to the existing plan while capturing the new scientific direction.

!!! warning "Human checkpoint"
    Adding a new question to the research plan is a consequential decision. The agent proposes the exact YAML, explains the impact on existing hypotheses, and waits for confirmation. This is propose-review-confirm for data model changes.

```
Human: Add Q8 and the milestones. But mark Q8 as exploratory and don't
       let it block the existing hypothesis timeline. It's a bonus if
       we get to it.
```

---

## Phase 5: Update questio data model

!!! info "Behind the scenes"
    ```
    → [agent updates plan/questions.yml with Q8 as type: exploratory]

    → [agent updates plan/milestones.yml with ripple-subtype-classification
       and subtype-coupling-comparison]

    → questio_status()
      Returns: 8 questions (7 hypothesis + 1 exploratory), Q8 dependencies
               are satisfied by existing milestone chain

    → note_create(note_type="idea",
                  tags=["observation", "investigate"],
                  series="sharpwaveripple",
                  title="Cross-subject check: bimodality present in all 5 subjects")
    ```

```
Agent: Updated:
       - questions.yml: Q8 added as exploratory
       - milestones.yml: 2 new milestones added

       Before we move on, let me quickly check if the bimodality is
       consistent across subjects...

       **Cross-subject bimodality check:**

       | Subject | Short peak (ms) | Long peak (ms) | % long | Bimodal? |
       |---------|----------------|----------------|--------|----------|
       | sub-01  | 48 ± 8         | 118 ± 22       | 31%    | Yes ✓    |
       | sub-02  | 51 ± 9         | 112 ± 18       | 28%    | Yes ✓    |
       | sub-03  | 45 ± 7         | 125 ± 25       | 33%    | Yes ✓    |
       | sub-04  | 50 ± 10        | 109 ± 20       | 26%    | Yes ✓    |
       | sub-05  | 47 ± 8         | 121 ± 21       | 30%    | Yes ✓    |

       Bimodality is present in all 5 subjects with consistent parameters.
       The ~30% long-ripple fraction matches Fernandez-Ruiz 2019 (~25-35%).

       This strengthens the case for Q8 — the phenomenon is robust.
```

---

## Phase 6: Record and plan — capturing the discovery

!!! info "Behind the scenes"
    ```
    → note_create(note_type="idea",
                  tags=["observation", "investigate", "discovery"],
                  series="sharpwaveripple",
                  title="Discovery: bimodal ripple duration distribution, consistent with Fernandez-Ruiz 2019")

    → note_create(note_type="idea",
                  tags=["decision"],
                  series="sharpwaveripple",
                  title="Decision: add Q8 (ripple subtypes) as exploratory question")

    → worklog_note(project_id="pixecog",
                   text="Exploratory analysis for Q8 (ripple subtypes): classify
                         ripples into short (<80ms) and long (>80ms) based on
                         duration bimodality. Run coupling analysis separately
                         for each subtype. Compare coupling peak timing and
                         magnitude. Reference: Fernandez-Ruiz 2019.
                         Priority: exploratory — do after main hypothesis milestones.",
                   kind="task")
    ```

```
Agent: **Recorded:**

       1. **Discovery note:** bimodal ripple duration distribution, literature
          grounding (Fernandez-Ruiz 2019), cross-subject validation
       2. **Decision note:** Q8 added as exploratory, rationale, impact
          on existing hypotheses
       3. **Worklog task:** exploratory analysis scheduled (low priority,
          after main hypothesis milestones)

       **Back to the original task:** SWR detection validation for sub-01
       was the starting point. The detection is working correctly — the
       bimodality is real, not an artifact. The standard validation can
       proceed.

       | Metric | sub-01 | Expected | Status |
       |--------|--------|----------|--------|
       | Rate | 12.3/min | 10-15/min | ✓ |
       | Frequency | 142 Hz | 100-300 Hz | ✓ |
       | Duration (short) | 48 ± 8 ms | 30-100 ms | ✓ |
       | Duration (long) | 118 ± 22 ms | 100-150 ms (Fernandez-Ruiz) | ✓ |

       Want to continue the standard validation — run all subjects?
```

```
Human: Yes, continue. The Q8 exploration can wait.
```

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **pipeio** | `pipeio_target_paths`, `pipeio_mod_context` | Read detection outputs, check for merge artifacts |
| **biblio** | `paper_context`, `biblio_discover_authors`, `biblio_ingest`, `biblio_graph_expand`, `rag_query` | Literature grounding for ripple subtypes |
| **questio** | `questio_status` | Verify updated question/milestone structure |
| **notio** | `note_create` (observation × 3, decision × 1) | Discovery capture and decision recording |
| **worklog** | `worklog_note` | Schedule exploratory follow-up as low-priority task |
| **codio** | (implicit) | Verify cogpy can handle duration-based classification |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1. Surprise | Iterate (assess step) | Agent flags unexpected pattern during routine assessment |
| 2. Investigation | Investigate | Check for artifact → inspect waveforms → confirm real |
| 3. Literature | Investigate (grounding) | `paper_context` → `biblio_discover_authors` → `biblio_graph_expand` |
| 4. Formulation | (extension) | New question + milestones proposed |
| 5. Update | (data model) | Propose-review-confirm for questio YAML changes |
| 6. Record + resume | (post-loop) | Discovery and decision notes, then resume original loop |

## Key insight

**The agent's most valuable contribution isn't running pipelines — it's noticing things a human might miss during routine validation and connecting them to literature.** A human running the same detection pipeline might glance at "12.3/min, looks good" and move on. The agent examined the full distribution, spotted the bimodality, checked whether it was an artifact, grounded it in literature, and helped the researcher decide what to do about it.

This is the scenario that demonstrates the **iterate → surprise → investigate → extend questio** transition. The agent didn't panic (investigate immediately), didn't ignore (continue silently), and didn't act unilaterally (add Q8 without asking). It flagged, proposed, and let the human decide — the propose-review-confirm pattern applied to scientific discovery, not just milestone updates.
