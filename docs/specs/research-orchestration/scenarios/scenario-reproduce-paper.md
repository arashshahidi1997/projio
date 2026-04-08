# Scenario: Reproduce Siapas & Wilson 1998 Coupling Results

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Milestone `spindle-detection-validated` is `not_started`
- Milestone `spindle-topography-mapped` is `not_started`
- Pipeline `spectrogram_burst` is configured but not yet run for spindle detection
- Pipeline `coupling_spindle_ripple` is configured but blocked by upstream milestones
- cogpy has spindle detection primitives and cross-correlogram tools
- H2 ("What are the cortical origins of ripple-driving spindles?") cites `@siapas_1998_CoordinatedInteractions`

**What the researcher wants:** Reproduce the core finding from Siapas & Wilson 1998 — coordinated interactions between hippocampal ripples and neocortical spindles — using pixecog's simultaneous Neuropixels + ECoG data. Use the paper as the blueprint for what to run, what to expect, and how to validate.

---

## Phase 1: Paper deep dive — "What did Siapas & Wilson actually show?"

```
Human: I want to reproduce the Siapas & Wilson 1998 results in our data.
       Their paper showed coordinated spindle-ripple interactions. What
       exactly did they find, and what would we need to do?
```

!!! info "Behind the scenes"
    ```
    → paper_context("@siapas_1998_CoordinatedInteractions")
      Returns: full-text extraction — abstract, methods, key figures, claims

    → biblio_enrich("@siapas_1998_CoordinatedInteractions")
      Returns: OpenAlex metadata — citation count, citing works, field impact

    → rag_query("Siapas Wilson 1998 spindle ripple coupling cross-correlogram")
      Returns: relevant chunks from indexed papers referencing this work
    ```

```
Agent: **Siapas & Wilson 1998 — key findings:**

       1. **Core claim:** hippocampal ripples and neocortical spindles are
          temporally correlated during slow-wave sleep. Cross-correlograms
          show a significant peak at ~100ms (spindles leading ripples).

       2. **Methods:**
          - Simultaneous hippocampal (CA1) and neocortical recordings in rats
          - Spindle detection: bandpass 10-16 Hz, amplitude threshold
          - Ripple detection: bandpass 100-300 Hz, amplitude threshold
          - Cross-correlogram between spindle peaks and ripple peaks
          - Statistical validation via shuffled controls

       3. **Expected values:**
          - Cross-correlogram peak at +50 to +150 ms (spindle → ripple)
          - Peak magnitude ~2-3x above baseline
          - Effect is specific to NREM sleep, absent during wake

       4. **What's reproducible with our setup:**
          - We have simultaneous Neuropixels (hippocampus) + ECoG (cortex) — ✓
          - We have NREM sleep periods identified via brainstate — needs validation
          - Spindle detection in ECoG — exists in spectrogram_burst but not yet run
          - Ripple detection in Neuropixels — exists in sharpwaveripple but not yet run
          - Cross-correlogram — cogpy has the tools

       **Citation impact:** 1200+ citations. The finding has been replicated
       extensively (Sirota 2003, Peyrache 2011, Maingret 2016) and is
       considered foundational for memory consolidation theory.

       Want me to check what we already have in place for reproducing this?
```

!!! tip "Why this matters"
    The agent didn't just return the paper abstract. It extracted the specific methods, expected values, and mapped them to the project's capabilities. This is **literature-first planning** — the paper becomes the specification for what to build and how to validate it.

---

## Phase 2: Map to hypotheses — "How does this connect to our research plan?"

```
Human: Yes. How does this map to our hypotheses?
```

!!! info "Behind the scenes"
    ```
    → questio_status()
      Returns: 7 hypotheses, all not_started. H2 directly cites this paper.

    → questio_gap("H2")
      Returns:
        H2: "What are the cortical origins of ripple-driving spindles?"
        milestones:
          spindle-detection-validated: not_started (flow: spectrogram_burst)
          spindle-topography-mapped: not_started (flow: spectrogram_burst)
        blockers: spindle-detection-validated depends on ieeg-preprocessing-stable
        root dependency: ttl-removal-validated (in_progress)
    ```

```
Agent: **H2 is the direct match.** It asks "What are the cortical origins
       of ripple-driving spindles?" and cites @siapas_1998 as a foundation.

       **Hypothesis → paper mapping:**

       | Paper claim | H2 milestone | Status |
       |-------------|-------------|--------|
       | Spindles detected in cortex | spindle-detection-validated | not_started |
       | Spindle topography varies | spindle-topography-mapped | not_started |
       | Spindle-ripple coupling exists | (H3: spindle-amplitude-ripple-coupling) | not_started |

       **Dependency chain:**
       ```
       ttl-removal-validated (in_progress)
         → ieeg-preprocessing-stable
           → spindle-detection-validated    ← first target
             → spindle-topography-mapped    ← second target
       ```

       **Gap analysis:** the root blocker is ttl-removal-validated, which is
       in_progress. Assuming that clears (see Scenario 1 in the scenario book),
       the next steps for H2 are:
       1. Run spindle detection (spectrogram_burst flow)
       2. Validate detection rates against literature
       3. Map spindle topography across cortical contacts
       4. Then feed into coupling analysis (coupling_spindle_ripple)

       The paper's cross-correlogram analysis maps to step 4, but we need
       steps 1-3 first. Want me to check what code and pipelines exist?
```

!!! note
    The agent connected the 1998 paper to the project's formal hypothesis structure without the researcher needing to remember which hypothesis number maps to which paper. This is the value of structured `citations` fields in `questions.yml`.

---

## Phase 3: Audit existing capabilities — "What do we have, what's missing?"

```
Human: Yes, audit what we have for spindle detection and coupling.
```

!!! info "Behind the scenes"
    ```
    → codio_discover("spindle detection")
      Returns: cogpy.spectral.SpindleDetector — bandpass + threshold + duration criteria
               cogpy.spectral.spectrogram_burst — time-frequency burst detection

    → codio_get("cogpy")
      Returns: library profile — spectral module has spindle detection, triggered module
               has cross-correlogram tools, brainstate module has NREM classification

    → pipeio_flow_status("spectrogram_burst")
      Returns: configured, 3 mods (blob_detect, merge_events, summarize),
               scripts exist, config has freq_band: [10, 16] for spindle mode

    → pipeio_flow_status("coupling_spindle_ripple")
      Returns: configured, cross_correlogram mod exists, but expects upstream
               outputs from spectrogram_burst and sharpwaveripple
    ```

```
Agent: **Capability audit:**

       **Code (cogpy):**
       | Component | Status | Notes |
       |-----------|--------|-------|
       | SpindleDetector | ✓ exists | Bandpass 10-16 Hz, amplitude threshold, min duration |
       | spectrogram_burst | ✓ exists | Time-frequency method, configurable freq band |
       | cross_correlogram | ✓ exists | Pairwise event cross-correlation |
       | brainstate.classify | ✓ exists | NREM/REM/wake classification |

       **Pipelines:**
       | Flow | Status | What it does |
       |------|--------|-------------|
       | spectrogram_burst | configured | Spindle detection via TF bursts (freq_band: [10, 16]) |
       | sharpwaveripple | configured | Ripple detection (100-300 Hz) |
       | coupling_spindle_ripple | configured | Cross-correlogram between event types |

       **What's ready:**
       - Spindle detection code exists and the flow is configured
       - Ripple detection code exists and the flow is configured
       - Cross-correlogram code exists

       **What's missing:**
       - spindle-detection-validated milestone is not_started — the flow
         hasn't been run and validated yet
       - swr-detection-validated is not_started — same for ripples
       - coupling_spindle_ripple expects both upstream outputs to exist

       **Bottom line:** the code and pipeline infrastructure exist. What's
       needed is execution and validation — running the flows, checking
       outputs against Siapas 1998 expectations, and recording evidence.
```

!!! tip "Why this matters"
    The audit reveals that this is an **execution and validation** problem, not a **code development** problem. The agent saved the researcher from potentially writing code that already exists. This is the codio discovery pattern in action.

---

## Phase 4: Identify gaps and plan — "What's the execution plan?"

```
Human: So the code is there. What's the plan to actually reproduce the
       Siapas results?
```

```
Agent: **Execution plan — reproducing Siapas & Wilson 1998:**

       **Assumptions:** ttl-removal-validated and ieeg-preprocessing-stable
       are complete (or will be by the time we get to this).

       **Step 1: Spindle detection** (spectrogram_burst flow)
       - Run for one subject first (sub-01) to validate
       - Check: detection rate (literature: 5-10 spindles/min during NREM)
       - Check: frequency content (should peak at 10-16 Hz)
       - Check: duration (0.5-2s expected)
       - If metrics match literature → run for all subjects

       **Step 2: Ripple detection** (sharpwaveripple flow)
       - Run for same subject (sub-01)
       - Check: detection rate (literature: 10-15 ripples/min during NREM)
       - Check: frequency content (100-300 Hz)
       - If metrics match → run for all subjects

       **Step 3: Cross-correlogram** (coupling_spindle_ripple flow)
       - Run for sub-01 first
       - Check: peak at +50 to +150 ms (spindle leading ripple)
       - Check: peak magnitude ~2-3x above shuffled baseline
       - Check: effect specific to NREM (control: compute during wake)

       **Step 4: Cross-subject validation**
       - Run coupling for all subjects
       - Check consistency: peak timing and magnitude across subjects
       - Compare against Siapas 1998 Figure 2 values

       **Step 5: Record**
       - Result notes for spindle-detection-validated, swr-detection-validated
       - Result note for the coupling analysis
       - Milestone updates for H2

       We need to start with Step 1. Ready to run spindle detection on sub-01?
```

!!! warning "Human checkpoint"
    The agent presented a full plan but waited for approval before executing. The plan is grounded in the paper's specific methods and expected values — not generic "run the pipeline" instructions. Each step has concrete validation criteria derived from Phase 1.

```
Human: The plan looks good. But let's focus on spindle detection first —
       that's the piece I'm least confident about. Start with sub-01.
```

---

## Phase 5: Execute first step — iterate loop for spindle detection

```
Agent: Starting spindle detection iterate loop for sub-01.
```

!!! info "Behind the scenes"
    ```
    → pipeio_config_read("spectrogram_burst")
      Returns: freq_band: [10, 16], threshold_sd: 2.5, min_duration_s: 0.5,
               max_duration_s: 2.0, brainstate_filter: "NREM"

    → pipeio_run(flow="spectrogram_burst",
                 wildcards={"subject": "sub-01", "session": "ses-04"})

    → pipeio_run_status(run_id)
      Returns: completed, 0 errors

    → pipeio_target_paths("spectrogram_burst", group="detect", member="sub-01")
      → reads spindle detection output: event times, durations, amplitudes

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="spectrogram_burst",
                  title="Iteration 1: spindle detection sub-01, initial parameters")
    ```

```
Agent: **Iteration 1 results — sub-01/ses-04:**

       | Metric | Observed | Literature (Siapas 1998) | Status |
       |--------|----------|-------------------------|--------|
       | Detection rate | 7.2/min | 5-10/min | ✓ within range |
       | Mean frequency | 12.8 Hz | 10-16 Hz | ✓ within range |
       | Mean duration | 0.9 s | 0.5-2.0 s | ✓ within range |
       | Amplitude (median) | 42 μV | varies by setup | — |

       Detection looks reasonable on first pass. The rate of 7.2/min is
       consistent with Siapas 1998 and subsequent replication studies.

       One thing to check: the duration distribution has a long tail
       (some events >3s). These may be merged events rather than single
       spindles. Want me to inspect the merge criteria, or are you
       satisfied with these parameters?
```

```
Human: Check the long-duration events — if they're merged spindles,
       we should tighten the max_duration or adjust the merge gap.
```

!!! info "Behind the scenes"
    ```
    → pipeio_mod_context("spectrogram_burst", "merge_events")
      Returns: merge_gap_s: 0.3 — events within 300ms are merged

    → [reads the event list, filters for duration > 2.0s]
      Found: 12 events with duration > 2.0s (out of 180 total)
      Inspection: these show two distinct spindle bursts separated by ~200ms,
      merged into a single event

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="spectrogram_burst",
                  title="Iteration 1b: long events are merged spindles, merge_gap too wide")
    ```

```
Agent: **Finding:** the 12 long-duration events (>2s) are pairs of spindles
       merged because the merge gap is 0.3s. Two distinct bursts separated
       by ~200ms get treated as one event.

       **Options:**
       1. Reduce merge_gap from 0.3s to 0.1s — would split these pairs
       2. Keep merge_gap but cap max_duration at 2.0s — would discard them
       3. Leave as-is — 12/180 events (6.7%) is a small fraction

       Siapas 1998 doesn't report merge criteria explicitly, but the
       duration histogram in their Figure 1 shows no events beyond 2s.
       I'd recommend option 1 — reducing the merge gap preserves the
       events while matching the paper's implicit criteria.
```

!!! warning "Human checkpoint"
    The agent identified a concrete parameter issue, proposed three options with trade-offs, and grounded the recommendation in the paper's own data. The human makes the call.

```
Human: Option 1. Reduce merge_gap to 0.1s and re-run.
```

!!! info "Behind the scenes"
    ```
    → pipeio_config_patch("spectrogram_burst",
                          registry_entry={"merge_events": {"merge_gap_s": 0.1}},
                          apply=True)

    → pipeio_run(flow="spectrogram_burst",
                 wildcards={"subject": "sub-01", "session": "ses-04"})

    → pipeio_target_paths("spectrogram_burst", group="detect", member="sub-01")

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="spectrogram_burst",
                  title="Iteration 2: merge_gap=0.1s, long events resolved")
    ```

```
Agent: **Iteration 2 results — sub-01/ses-04, merge_gap=0.1s:**

       | Metric | Iteration 1 | Iteration 2 | Literature |
       |--------|-------------|-------------|------------|
       | Detection rate | 7.2/min | 8.1/min | 5-10/min ✓ |
       | Mean duration | 0.9 s | 0.8 s | 0.5-2.0 s ✓ |
       | Events > 2s | 12 (6.7%) | 1 (0.5%) | ~0% ✓ |
       | Max duration | 3.4 s | 2.1 s | ~2.0 s ✓ |

       The merge gap fix resolved the long-duration events. Detection rate
       increased slightly (split events now counted separately) — still
       within literature range.

       Duration distribution now matches the shape in Siapas 1998 Figure 1.
       Sub-01 looks good. Extend to remaining subjects?
```

```
Human: Run for all subjects. If they all look similar, we can move to
       the coupling analysis.
```

---

## Phase 6: Record and plan forward

!!! info "Behind the scenes"
    ```
    → pipeio_run(flow="spectrogram_burst",
                 wildcards={"subject": "sub-*"})

    → [monitors via pipeio_run_status — all subjects complete]

    → [reads detection outputs for all subjects, compiles cross-subject summary]

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="spectrogram_burst",
                  title="Assessment: spindle detection across all 5 subjects")
    ```

```
Agent: **Cross-subject spindle detection results:**

       | Subject | Rate (/min) | Mean freq (Hz) | Mean dur (s) | Events > 2s |
       |---------|-------------|----------------|--------------|-------------|
       | sub-01  | 8.1         | 12.8           | 0.8          | 0.5%        |
       | sub-02  | 6.9         | 13.1           | 0.9          | 0.3%        |
       | sub-03  | 7.5         | 12.5           | 0.7          | 0.8%        |
       | sub-04  | 9.2         | 12.9           | 0.8          | 0.2%        |
       | sub-05  | 7.8         | 13.3           | 0.9          | 0.4%        |
       | **Mean** | **7.9 ± 0.8** | **12.9 ± 0.3** | **0.8 ± 0.1** | **0.4%** |

       All subjects are within literature range (5-10/min, 10-16 Hz, 0.5-2s).
       Cross-subject consistency is good (low variance).

       **Recommendation:** spindle detection is validated. I propose:
       1. Create a result note for spindle-detection-validated
       2. Update milestone status to complete
       3. Next session: run coupling analysis (Step 3 of our plan)

       Confirm?
```

```
Human: Confirmed. Record the result and update the milestone.
```

!!! info "Behind the scenes"
    ```
    → note_create(note_type="result",
                  title="Spindle detection validated — rates and properties match Siapas 1998",
                  series="spectrogram_burst",
                  question=["H2"],
                  milestone="spindle-detection-validated",
                  subjects=["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
                  metric="spindle_rate_per_min",
                  value="7.9 ± 0.8 /min (literature: 5-10/min)",
                  confidence="validated")

    → [updates plan/milestones.yml: spindle-detection-validated → complete,
       evidence: [result-arash-20260408-XXXXXX]]

    → questio_gap("H2")
      Returns: spindle-detection-validated: complete ✓
               spindle-topography-mapped: not_started (next target)
               upstream for coupling: swr-detection-validated still not_started
    ```

```
Agent: Result note created and milestone updated.

       **Updated state for H2:**
       - spindle-detection-validated: **complete** ✓
       - spindle-topography-mapped: not_started (unblocked — ready to tackle)
       - coupling analysis: blocked by swr-detection-validated

       **Next session options:**
       1. Map spindle topography (Step 2 toward H2 — can run now)
       2. Run and validate SWR detection (unblocks coupling analysis)
       3. Both — topography is independent of SWR, can run in parallel

       The Siapas 1998 reproduction needs both spindle topography AND
       coupling. Coupling requires SWR detection first. I'd recommend
       option 3 — run topography analysis and SWR detection in parallel.
```

!!! warning "Human checkpoint"
    The agent proposed the next steps grounded in the paper's requirements and the project's dependency chain. The researcher decides the priority for the next session.

```
Human: Good plan. Let's schedule SWR detection as a background task and
       pick up topography mapping next time I'm online.
```

!!! info "Behind the scenes"
    ```
    → worklog_note(project_id="pixecog",
                   text="Run SWR detection validation (sharpwaveripple flow).
                         Same pattern as spindle detection: run sub-01 first,
                         check detection rate (literature: 10-15/min during NREM),
                         check frequency (100-300 Hz), check duration.
                         If sub-01 passes, run all subjects. Create result note
                         and propose milestone update for swr-detection-validated.
                         Reference: Siapas & Wilson 1998 methods.",
                   kind="issue",
                   auto_dispatch=True,
                   model="opus")
    ```

```
Agent: SWR detection dispatched as background task. It will follow the
       same iterate pattern and propose a milestone update when complete.

       **Session summary:**
       - Reproduced Siapas 1998 spindle detection approach
       - Validated across all 5 subjects (7.9 ± 0.8 /min)
       - Fixed merge_gap parameter (0.3s → 0.1s) based on paper's duration profile
       - spindle-detection-validated milestone: complete
       - Next: spindle topography + SWR detection → coupling analysis
```

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **biblio** | `paper_context`, `biblio_enrich`, `rag_query` | Extract paper methods, expected values, citation impact |
| **questio** | `questio_status`, `questio_gap` | Map paper claims to hypotheses and milestones |
| **codio** | `codio_discover`, `codio_get` | Audit existing spindle detection code |
| **pipeio** | `pipeio_flow_status`, `pipeio_config_read`, `pipeio_config_patch`, `pipeio_run`, `pipeio_target_paths`, `pipeio_mod_context` | Configure, run, and inspect pipeline outputs |
| **notio** | `note_create` (observation × 4, result × 1) | Mid-loop capture and formal evidence |
| **worklog** | `worklog_note` | Schedule background SWR detection task |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1. Paper deep dive | (pre-loop) | Literature extraction → method specification |
| 2. Map to hypotheses | Orient | `questio_status` → `questio_gap` → dependency analysis |
| 3. Audit capabilities | Orient | `codio_discover` → `pipeio_flow_status` → gap identification |
| 4. Plan | (planning) | Paper methods → execution plan with validation criteria |
| 5. Execute | Iterate | 2 cycles: run → assess → adjust merge_gap → re-run → validate |
| 6. Record | (post-loop) | Result note + propose-review-confirm for milestone |

## Key insight

**Literature-first planning.** Unlike Scenario 1 (TTL removal), where the researcher already knew what to do and needed execution support, this scenario starts from a paper. The paper drives everything: what to build, what parameters to expect, what counts as success, and how to validate. The agent's role is to bridge the gap between "I read this paper" and "here's what our data shows" — extracting methods from literature, mapping them to project infrastructure, and grounding every assessment in the paper's reported values.

This is the scenario that demonstrates why biblio and questio need to work together: the paper provides the specification, questio tracks the execution, and the agent connects the two.
