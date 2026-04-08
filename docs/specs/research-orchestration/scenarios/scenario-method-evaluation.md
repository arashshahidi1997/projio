# Scenario: Evaluating a New Detection Method from Recent Literature

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Milestone `spindle-detection-validated` is `complete` with evidence from Scenario 3 (reproduce paper)
- Pipeline `spectrogram_burst` is running with cogpy's `SpindleDetector` (bandpass 10-16 Hz, amplitude threshold)
- Detection rates are within literature range (7.9 ± 0.8 /min across 5 subjects)
- Researcher has just read Pedrosa et al. 2024 and wonders if their method is better

**What the researcher wants:** Decide whether to adopt a new spindle detection method from recent literature, or stick with the current approach. Make this decision systematically, with evidence, and record it so future agents don't re-evaluate without new information.

---

## Phase 1: Literature trigger — "Should we switch?"

```
Human: I just read Pedrosa 2024 and their spindle detection looks more
       sophisticated than ours — they use a wavelet-based approach with
       adaptive thresholding per channel. Should we switch?
```

!!! info "Behind the scenes"
    ```
    → paper_context("@pedrosa_2024_HippocampalRipples")
      Returns: full-text extraction — methods section describes wavelet-based
               spindle detection with channel-adaptive sigma thresholds,
               cross-validated against expert manual scoring

    → biblio_discover_authors("Pedrosa")
      Returns: 12 papers by J. Pedrosa, primarily on hippocampal oscillations
               and sleep physiology. 3 papers specifically on detection methods.

    → biblio_graph_expand("@pedrosa_2024_HippocampalRipples")
      Returns: 8 citing works (recent — paper is from 2024), 42 references.
               Two references are method comparison papers for spindle detection.
               One citing work (Martinez 2025) reports implementing the Pedrosa
               method and finding marginal improvement over bandpass methods.
    ```

```
Agent: **Pedrosa 2024 spindle detection method:**

       1. **Approach:** continuous wavelet transform (Morlet, σ=7) in 10-16 Hz,
          per-channel adaptive threshold set at the 95th percentile of
          wavelet power during NREM.

       2. **Claimed advantages:**
          - Adapts to per-channel amplitude differences (no global threshold)
          - Better temporal resolution than bandpass + Hilbert
          - Cross-validated against expert manual scoring (F1: 0.87 vs 0.79
            for bandpass method)

       3. **Reception:**
          - Martinez 2025 implemented it and found "marginal improvement in
            detection rate (+8%) but no significant difference in downstream
            coupling analysis" — the coupling results were equivalent.
          - No other independent replication yet (paper is recent).

       4. **Our current method (cogpy SpindleDetector):**
          - Bandpass 10-16 Hz + amplitude threshold (2.5 SD)
          - Already validated: 7.9 ± 0.8 /min, matches literature
          - Duration and frequency profiles match Siapas 1998

       **Key question:** is the improvement in detection F1 (0.87 vs 0.79)
       worth the migration cost? Martinez 2025 suggests the downstream
       coupling analysis is equivalent either way.

       Want me to do a head-to-head comparison on our data?
```

!!! tip "Why this matters"
    The agent didn't just summarize the new paper — it found an independent evaluation (Martinez 2025) via `biblio_graph_expand`. This citation network analysis transforms a "should we switch?" question from opinion into evidence. The agent is already framing the decision in terms of what matters: downstream coupling results, not just detection accuracy.

---

## Phase 2: Current method audit — "What exactly are we comparing against?"

```
Human: Yes, let's compare. But first make sure I understand what our
       current method actually does — I want a fair comparison.
```

!!! info "Behind the scenes"
    ```
    → codio_get("cogpy")
      Returns: spectral module — SpindleDetector class, spectrogram_burst function

    → codio_discover("spindle detection wavelet")
      Returns: cogpy.spectral.SpindleDetector (bandpass), cogpy.spectral.cwt_burst
               (wavelet-based burst detection — exists but not used in pipeline)

    → pipeio_mod_context("spectrogram_burst", "blob_detect")
      Returns: script uses SpindleDetector with config: freq_band=[10,16],
               threshold_sd=2.5, min_duration_s=0.5, merge_gap_s=0.1
    ```

```
Agent: **Current method (in pipeline):**
       - cogpy.spectral.SpindleDetector
       - Bandpass filter 10-16 Hz → Hilbert envelope → threshold at 2.5 SD
       - Merge gap: 0.1s, min duration: 0.5s, max duration: 2.0s
       - Global threshold (same SD cutoff across all channels)

       **Interesting finding:** cogpy already has `cwt_burst` — a wavelet-based
       burst detector that could implement the Pedrosa approach. It uses Morlet
       wavelets and supports per-channel adaptive thresholds. It's just not
       currently wired into the spectrogram_burst pipeline.

       **Comparison framework:**

       | Dimension | Current (bandpass) | Pedrosa (wavelet) |
       |-----------|-------------------|-------------------|
       | Temporal resolution | ~50ms (filter transition) | ~30ms (wavelet) |
       | Threshold | Global (2.5 SD) | Per-channel adaptive (95th pctl) |
       | Implementation | In pipeline, validated | In cogpy, not wired up |
       | Migration cost | None | Config change + revalidation |
       | Literature evidence | Standard method, widely used | F1=0.87 vs 0.79, one replication |

       Since `cwt_burst` already exists, the migration cost is actually low —
       it's a config change in the pipeline, not new code. Want to run both
       methods on one subject and compare?
```

!!! note
    The codio discovery revealed that the wavelet method is already implemented in cogpy but unused. This changes the cost-benefit calculus entirely — "should we switch?" becomes much cheaper when the code already exists.

---

## Phase 3: Benchmark design — "How do we compare fairly?"

```
Human: Yes. Run both on sub-01, compare detection rates, temporal
       precision, and whether it changes the coupling result.
```

```
Agent: **Benchmark plan:**

       1. **Method A (current):** SpindleDetector, bandpass 10-16 Hz, 2.5 SD
          — already has results for sub-01

       2. **Method B (Pedrosa):** cwt_burst, Morlet wavelet, per-channel
          adaptive threshold at 95th percentile NREM power

       3. **Comparison metrics:**
          - Detection rate (/min)
          - Event overlap: what fraction of events are detected by both methods
          - Duration distribution comparison
          - **Downstream test:** run cross-correlogram (coupling_spindle_ripple)
            with each method's events → compare coupling peak timing and magnitude

       The downstream test is the real arbiter — if coupling results are
       equivalent, the detection difference doesn't matter for our hypotheses.

       Running now.
```

!!! warning "Human checkpoint"
    The researcher approved the benchmark plan. The agent identified the right success criterion — not detection accuracy in isolation, but impact on the downstream coupling analysis that actually matters for H2.

---

## Phase 4: Benchmark execution — head-to-head comparison

!!! info "Behind the scenes"
    ```
    → pipeio_nb_create(flow="spectrogram_burst",
                       name="benchmark_spindle_methods",
                       kind="investigate",
                       mod="blob_detect")

    → [agent writes benchmark notebook: runs both methods on sub-01/ses-04,
       computes overlap, generates comparison plots]

    → pipeio_nb_exec(flow="spectrogram_burst",
                     name="benchmark_spindle_methods",
                     parameters={"subject": "sub-01", "session": "ses-04"})

    → pipeio_nb_read(flow="spectrogram_burst",
                     name="benchmark_spindle_methods")

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="spectrogram_burst",
                  title="Iteration 1: spindle method benchmark sub-01")
    ```

```
Agent: **Benchmark results — sub-01/ses-04:**

       | Metric | Method A (bandpass) | Method B (wavelet) |
       |--------|--------------------|--------------------|
       | Detection rate | 8.1/min | 8.9/min |
       | Mean duration | 0.8 s | 0.7 s |
       | Mean frequency | 12.8 Hz | 12.6 Hz |
       | Events > 2s | 0.5% | 0.3% |

       **Overlap analysis:**
       - 82% of Method A events have a matching Method B event (±100ms)
       - 75% of Method B events have a matching Method A event
       - Method B detects ~10% more events (mostly low-amplitude spindles
         that fall below Method A's global threshold)

       The extra events from Method B are concentrated on channels with
       lower overall amplitude — exactly where the per-channel adaptive
       threshold helps. But are these real spindles or noise?

       Let me check the downstream coupling before concluding.
```

!!! info "Behind the scenes"
    ```
    → [agent extends the benchmark notebook: runs cross-correlogram
       using Method A events and Method B events separately]

    → pipeio_nb_exec(flow="spectrogram_burst",
                     name="benchmark_spindle_methods",
                     parameters={"subject": "sub-01", "session": "ses-04",
                                 "run_coupling": true})

    → pipeio_nb_read(...)

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="spectrogram_burst",
                  title="Iteration 2: coupling comparison between methods")
    ```

```
Agent: **Coupling comparison — the decisive test:**

       | Coupling metric | Method A | Method B |
       |-----------------|---------|---------|
       | Peak timing | +92 ms | +88 ms |
       | Peak magnitude (z-score) | 3.8 | 3.6 |
       | Peak width (FWHM) | 45 ms | 52 ms |
       | Significance (p-value) | <0.001 | <0.001 |

       **Key finding:** the coupling results are nearly identical. The peak
       timing, magnitude, and significance are within noise of each other.

       This matches Martinez 2025's finding: "marginal improvement in
       detection rate but no significant difference in downstream coupling."

       The extra events detected by Method B (low-amplitude spindles on
       quiet channels) don't contribute to the coupling signal — they may
       be real spindles, but they're not the ones that drive ripples.
```

!!! example "What the agent sees"
    The cross-correlogram peaks are indistinguishable between methods. The 10% increase in detection rate from Method B doesn't translate to a measurably different coupling result. The decisive metric — the one that matters for H2 — is equivalent.

```
Human: So the coupling is the same. What's your recommendation?
```

---

## Phase 5: Decision — "Switch or stay?"

```
Agent: **Recommendation: stay with Method A (bandpass).**

       **Reasoning:**
       1. Coupling results are equivalent — the metric that matters for
          H2-H7 is unchanged
       2. Method A is already validated across all 5 subjects with
          documented evidence (spindle-detection-validated milestone)
       3. Switching to Method B would require:
          - Rewiring the pipeline config
          - Revalidating across all 5 subjects
          - Updating the result note and re-confirming the milestone
       4. The improvement (10% more detections) is real but doesn't
          impact downstream analysis
       5. Martinez 2025 reached the same conclusion independently

       **Exception:** if we later find that coupling analysis on specific
       channels is weak (e.g., low-amplitude cortical regions), Method B's
       per-channel adaptive threshold could help. We should revisit if
       spindle-topography-mapped reveals dead spots.

       Want me to record this decision?
```

!!! warning "Human checkpoint"
    The agent presented a clear recommendation with reasoning. The decision to NOT change is as important as the decision to change — and it needs to be recorded so that future agents (or the researcher in 6 months) don't re-run this evaluation.

```
Human: Agreed. Record the decision. And note the exception about
       revisiting for the topography analysis.
```

---

## Phase 6: Record — capturing the decision

!!! info "Behind the scenes"
    ```
    → note_create(note_type="idea",
                  tags=["decision", "method-evaluation"],
                  series="spectrogram_burst",
                  title="Decision: retain bandpass spindle detection over wavelet (Pedrosa 2024)")
    ```

    Note body:
    ```markdown
    ## Decision

    **Retain current bandpass method (SpindleDetector)** over wavelet-based
    method (Pedrosa 2024) for spindle detection in spectrogram_burst pipeline.

    ## Evidence

    - Head-to-head benchmark on sub-01/ses-04
    - Detection rate: 8.1/min (bandpass) vs 8.9/min (wavelet) — +10%
    - Coupling peak timing: 92ms vs 88ms — equivalent
    - Coupling peak magnitude: z=3.8 vs z=3.6 — equivalent
    - Martinez 2025 independently found equivalent coupling results

    ## Rationale

    The 10% detection improvement does not translate to measurably different
    coupling results. The current method is already validated across 5 subjects
    with documented evidence. Migration cost (revalidation, pipeline reconfig)
    is not justified by equivalent downstream results.

    ## Revisit conditions

    - If spindle-topography-mapped reveals dead spots on low-amplitude channels
    - If coupling analysis on specific cortical regions shows weak signal
    - If a new paper demonstrates coupling-relevant improvements (not just
      detection accuracy)

    ## References

    - @pedrosa_2024_HippocampalRipples — source method
    - Martinez 2025 — independent evaluation, same conclusion
    - result-arash-20260408-XXXXXX — spindle-detection-validated evidence
    ```

```
Agent: Decision note created: idea-arash-20260408-XXXXXX.md

       This note captures:
       - What was compared and the metrics
       - Why we're staying with the current method
       - When to revisit (specific conditions, not "maybe later")
       - Literature references supporting the decision

       Any future agent encountering "should we use Pedrosa's method?"
       will find this note via rag_query or note_search and see both
       the benchmark data and the reasoning.
```

!!! note "Decision recording"
    The decision note serves two purposes: (1) it prevents future re-evaluation without new evidence — the revisit conditions are explicit, and (2) it documents the negative result, which is scientifically valuable. "We tested X and it didn't help because Y" is information that would otherwise be lost.

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **biblio** | `paper_context`, `biblio_discover_authors`, `biblio_graph_expand` | Extract new method, find independent evaluations, assess reception |
| **codio** | `codio_get`, `codio_discover` | Discover that wavelet method already exists in cogpy |
| **pipeio** | `pipeio_mod_context`, `pipeio_nb_create`, `pipeio_nb_exec`, `pipeio_nb_read` | Benchmark notebook creation and execution |
| **notio** | `note_create` (observation × 2, decision × 1) | Mid-loop capture and decision recording |
| **questio** | (implicit) | H2 milestone context — what downstream analysis matters |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1. Literature trigger | (pre-loop) | Paper extraction + citation graph analysis |
| 2. Current method audit | Orient | Code discovery + pipeline inspection |
| 3. Benchmark design | (planning) | Define comparison metrics with downstream focus |
| 4. Benchmark execution | Iterate | 2 cycles: detection comparison → coupling comparison |
| 5. Decision | (judgment) | Agent recommends, human confirms |
| 6. Record | (post-loop) | Decision note with revisit conditions |

## Key insight

**Method evaluation as a first-class workflow.** The decision to NOT change is as valuable as the decision to change — perhaps more so, because it prevents future re-evaluation without new evidence. The scenario demonstrates that the right comparison metric is not detection accuracy in isolation, but impact on the downstream analysis that matters for the research questions. The agent's contribution is identifying the right comparison (coupling results, not just detection rates) and finding independent evidence (Martinez 2025) through citation graph expansion.

This is the scenario that justifies biblio's `graph_expand` tool: finding that one independent evaluation paper transformed the decision from "we should probably test this" to "others have tested it and the conclusion is clear."
