# Scenario: Debugging a Cross-Flow Anomaly

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Milestone `spindle-detection-validated` is `complete`
- Milestone `swr-detection-validated` is `complete`
- Pipeline `coupling_spindle_ripple` has been run for all 5 subjects
- The cross-correlogram output is unexpectedly flat — no coupling peak
- All upstream milestones passed their individual validation
- The researcher expected a clear spindle-ripple coupling peak based on Siapas 1998, Sirota 2003, and Maingret 2016

**What the researcher wants:** Figure out why the coupling analysis shows no spindle-ripple interaction when all the literature — and this project's own validated detections — say it should be there.

---

## Phase 1: Symptom — "Something is wrong"

```
Human: The cross-correlogram between spindles and ripples is completely
       flat. No coupling peak at all. Sirota 2003 and Siapas 1998 both
       show clear spindle-ripple coupling. Something is wrong.
```

```
Agent: That's unexpected — both detection milestones passed with good
       metrics. Let me investigate systematically.
```

!!! danger "The trap"
    The instinct is to suspect the coupling code itself. But in cross-flow pipelines, the symptom is almost never where the cause is. The coupling analysis can be perfectly correct and still produce flat output if its *inputs* are wrong. The investigation must trace the full dependency chain.

---

## Phase 2: Reproduce and scope — "Is it real, and how widespread?"

!!! info "Behind the scenes"
    ```
    → pipeio_target_paths("coupling_spindle_ripple", group="correlogram")
      Returns: output paths for all 5 subjects

    → [reads cross-correlogram output for sub-01]
      Confirms: flat correlogram, no significant peak at any lag

    → [reads cross-correlogram outputs for sub-02 through sub-05]
      All flat — no coupling peak in any subject

    → note_create(note_type="idea",
                  tags=["observation", "investigate"],
                  series="coupling_spindle_ripple",
                  title="Investigate: flat cross-correlogram across all 5 subjects")
    ```

```
Agent: **Confirmed:** the cross-correlogram is flat for ALL 5 subjects.
       No significant coupling peak at any lag from -500ms to +500ms.

       **Scoping:** this is systemic (all subjects), not subject-specific.
       That rules out electrode issues or subject-level artifacts — this
       points to a pipeline or configuration problem.

       Starting systematic trace through the dependency chain:
       ```
       spectrogram_burst → spindle events ─┐
                                            ├→ coupling_spindle_ripple → correlogram
       sharpwaveripple → ripple events ─────┘
       ```

       Let me check the coupling code first, then trace upstream.
```

---

## Phase 3: Check coupling code — "Is the analysis itself correct?"

!!! info "Behind the scenes"
    ```
    → pipeio_mod_context("coupling_spindle_ripple", "cross_correlogram")
      Returns: script reads spindle event times from spectrogram_burst output,
               reads ripple event times from sharpwaveripple output,
               computes cross-correlogram with ±500ms window, 10ms bins,
               shuffled control (100 shuffles)

    → codio_get("cogpy")
      Returns: cogpy.coupling.cross_correlogram — well-tested function,
               used in other projects
    ```

```
Agent: **Coupling code inspection:**
       - Script reads spindle events from `spectrogram_burst` output ✓
       - Script reads ripple events from `sharpwaveripple` output ✓
       - Cross-correlogram: ±500ms window, 10ms bins, 100 shuffles ✓
       - cogpy.coupling.cross_correlogram is well-tested ✓

       The code looks correct. It's computing the right thing. If the
       inputs are correct, the output should show coupling.

       **The issue must be upstream.** Let me check the inputs.
```

!!! tip "Investigation pattern"
    The agent checked the most obvious suspect first (the coupling code) and ruled it out quickly. This is important — don't skip steps just because you have a hypothesis. Rule out the simple explanation before pursuing the complex one.

---

## Phase 4: Trace upstream — ripple detection

!!! info "Behind the scenes"
    ```
    → pipeio_target_paths("sharpwaveripple", group="detect", member="sub-01")
      → reads SWR detection output for sub-01

    → [inspects ripple events: count, rate, frequency, amplitude]
      Rate: 12.3/min — within expected range (10-15/min)
      Mean frequency: 142 Hz — within expected range (100-300 Hz)
      Duration: 45ms mean — within expected range (30-100ms)

    → note_create(note_type="idea",
                  tags=["observation", "investigate"],
                  series="coupling_spindle_ripple",
                  title="Investigation: ripple detection looks normal (12.3/min, 142 Hz)")
    ```

```
Agent: **Ripple detection check (sub-01):**

       | Metric | Observed | Expected | Status |
       |--------|----------|----------|--------|
       | Rate | 12.3/min | 10-15/min | ✓ normal |
       | Frequency | 142 Hz | 100-300 Hz | ✓ normal |
       | Duration | 45 ms | 30-100 ms | ✓ normal |

       Ripple detection looks fine. The events are physiologically plausible
       and match the validated milestone evidence.

       Moving to spindle detection.
```

---

## Phase 5: Trace upstream — spindle detection

!!! info "Behind the scenes"
    ```
    → pipeio_target_paths("spectrogram_burst", group="detect", member="sub-01")
      → reads spindle detection output for sub-01

    → [inspects spindle events: count, rate, frequency, amplitude]
      Rate: 25.1/min — UNUSUALLY HIGH (expected: 5-10/min)
      Mean frequency: 22.4 Hz — OUTSIDE expected spindle band (10-16 Hz)
      Duration: 0.3s mean — shorter than expected (0.5-2.0s)
    ```

```
Agent: **FOUND IT.**

       **Spindle detection check (sub-01):**

       | Metric | Observed | Expected | Status |
       |--------|----------|----------|--------|
       | Rate | **25.1/min** | 5-10/min | ✗ way too high |
       | Frequency | **22.4 Hz** | 10-16 Hz | ✗ wrong band |
       | Duration | **0.3 s** | 0.5-2.0 s | ✗ too short |

       This is not spindle detection — this is beta oscillation detection.
       25/min at 22 Hz with 0.3s duration is a textbook beta burst profile.

       Let me check the spectrogram_burst config.
```

!!! info "Behind the scenes"
    ```
    → pipeio_config_read("spectrogram_burst")
      Returns:
        blob_detect:
          freq_band: [15, 30]    ← THIS IS THE PROBLEM
          threshold_sd: 2.5
          min_duration_s: 0.3
          merge_gap_s: 0.1

    → note_create(note_type="idea",
                  tags=["observation", "investigate"],
                  series="coupling_spindle_ripple",
                  title="ROOT CAUSE: spectrogram_burst freq_band is [15,30] not [10,16]")
    ```

```
Agent: **Root cause identified.**

       The `spectrogram_burst` config has:
       ```yaml
       freq_band: [15, 30]   # ← BETA band, not spindle band
       ```

       It should be:
       ```yaml
       freq_band: [10, 16]   # ← spindle band (sigma)
       ```

       **What happened:** the frequency band is set to 15-30 Hz (beta range)
       instead of 10-16 Hz (spindle/sigma range). The pipeline is correctly
       detecting beta oscillations — but calling them "spindles."

       **Why the coupling is flat:** beta bursts have no temporal
       relationship with hippocampal ripples. Spindles do. The
       cross-correlogram is flat because there IS no coupling between
       beta events and ripples — which is the correct result for the
       wrong inputs.
```

!!! danger "The trap"
    The spindle-detection-validated milestone passed because the detection *rate* (25/min) wasn't checked against literature expectations at the time — or the validation was done with a different config that was later changed. This is why the agent-as-judge approach matters: pre-scripted validation might have caught this if it checked frequency, but the agent can catch it by reasoning about the full picture.

!!! warning "Human checkpoint"
    ```
    Human: How did this happen? The spindle validation used [10, 16].
    ```

```
Agent: Looking at the git history for the config file...

       The config was changed after the spindle validation. It looks like
       a subsequent analysis (beta burst exploration) modified freq_band
       to [15, 30] and the change wasn't reverted. The spindle detection
       milestone was validated with [10, 16], but the coupling analysis
       ran with the modified [15, 30].

       **This is a config drift issue** — the validated state and the
       current pipeline state diverged.

       **Proposed fix:**
       1. Restore freq_band to [10, 16]
       2. Re-run spectrogram_burst for all subjects
       3. Re-run coupling_spindle_ripple
       4. Check the cross-correlogram for the expected peak

       Shall I proceed?
```

---

## Phase 6: Root cause summary

```
Human: Yes, fix it. But first — is there a way to prevent this kind of
       config drift in the future?
```

```
Agent: **Root cause trace:**

       ```
       Symptom:  flat cross-correlogram (coupling_spindle_ripple)
       ↓ not the coupling code (verified correct)
       ↓ not the ripple detection (12.3/min, 142 Hz — normal)
       ↓ IS the spindle detection (25/min, 22 Hz — wrong band)
       Root:     spectrogram_burst config freq_band changed from [10,16]
                 to [15,30] after validation, not reverted
       ```

       **Prevention:** this is exactly what `pipeio_contracts_validate` is
       designed for — it checks that pipeline configs match their documented
       parameters. If the spindle detection milestone recorded the validated
       config parameters (freq_band: [10, 16]) in its evidence, a
       contracts check could detect the drift.

       For now, let me fix and re-run.
```

!!! tip "Investigation pattern"
    The full diagnostic trace: **symptom** (flat correlogram) → **rule out direct cause** (coupling code is correct) → **check input A** (ripples are fine) → **check input B** (spindles are wrong) → **trace to config** (frequency band changed). The key insight: always trace the dependency chain systematically. Don't assume the most proximal component is the broken one.

---

## Phase 7: Fix and re-run — iterate loop

!!! info "Behind the scenes"
    ```
    → pipeio_config_patch("spectrogram_burst",
                          registry_entry={"blob_detect": {"freq_band": [10, 16]}},
                          apply=True)

    → pipeio_run(flow="spectrogram_burst",
                 wildcards={"subject": "sub-*"})

    → pipeio_run_status(run_id)
      Returns: completed, 0 errors

    → [spot-check: reads sub-01 spindle detection output]
      Rate: 8.1/min ✓, Frequency: 12.8 Hz ✓, Duration: 0.8s ✓

    → pipeio_run(flow="coupling_spindle_ripple",
                 wildcards={"subject": "sub-*"})

    → pipeio_run_status(run_id)
      Returns: completed, 0 errors

    → pipeio_target_paths("coupling_spindle_ripple", group="correlogram", member="sub-01")
      → reads cross-correlogram output

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="coupling_spindle_ripple",
                  title="Fix verified: coupling peak present after freq_band correction")
    ```

```
Agent: **Fix verified.**

       **Spindle detection (sub-01 spot check):**
       - Rate: 8.1/min (was 25.1/min) ✓
       - Frequency: 12.8 Hz (was 22.4 Hz) ✓
       - Duration: 0.8s (was 0.3s) ✓

       **Cross-correlogram (sub-01):**
       - **Peak at +95 ms** (spindle leading ripple) ✓
       - Peak magnitude: z = 3.8 (well above shuffled baseline) ✓
       - Peak width (FWHM): 48 ms ✓

       **Comparison to literature:**

       | Metric | Our result | Siapas 1998 | Sirota 2003 |
       |--------|-----------|-------------|-------------|
       | Peak timing | +95 ms | +50-150 ms | +80-120 ms |
       | Significance | z=3.8 | p<0.01 | p<0.001 |

       The coupling is exactly where the literature says it should be.
       The fix worked. Want me to check all subjects and create a result note?
```

```
Human: Check all subjects, then record.
```

!!! info "Behind the scenes"
    ```
    → [reads cross-correlogram for all 5 subjects]

    → note_create(note_type="idea",
                  tags=["observation", "iterate"],
                  series="coupling_spindle_ripple",
                  title="Cross-subject coupling: all 5 subjects show peak at ~100ms")
    ```

```
Agent: **Cross-subject coupling results:**

       | Subject | Peak (ms) | Magnitude (z) | Significant? |
       |---------|-----------|---------------|-------------|
       | sub-01  | +95       | 3.8           | Yes (p<0.001) |
       | sub-02  | +82       | 3.2           | Yes (p<0.001) |
       | sub-03  | +108      | 2.9           | Yes (p<0.01) |
       | sub-04  | +91       | 3.5           | Yes (p<0.001) |
       | sub-05  | +99       | 3.1           | Yes (p<0.001) |
       | **Mean** | **+95 ± 9** | **3.3 ± 0.3** | **All significant** |

       Consistent coupling peak across all subjects at +95 ± 9 ms,
       matching Siapas 1998 (+50-150ms) and Sirota 2003 (+80-120ms).
```

---

## Phase 8: Record — investigation trail and result

!!! info "Behind the scenes"
    ```
    → note_create(note_type="idea",
                  tags=["observation", "investigate", "decision"],
                  series="coupling_spindle_ripple",
                  title="Decision: spindle freq_band corrected from [15,30] to [10,16]")

    → note_create(note_type="result",
                  title="Spindle-ripple coupling validated — peak at +95ms matches literature",
                  series="coupling_spindle_ripple",
                  question=["H2", "H3"],
                  milestone="delta-ripple-coupling",
                  subjects=["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
                  metric="coupling_peak_lag_ms",
                  value="+95 ± 9 ms (all subjects significant, p<0.001)",
                  confidence="validated")
    ```

```
Agent: **Recorded:**

       1. **Investigation trail** (4 observation notes):
          - Flat correlogram confirmed across all subjects
          - Ripple detection verified normal
          - Root cause: freq_band [15,30] instead of [10,16]
          - Fix verified: coupling peak at +95ms after correction

       2. **Decision note:** freq_band corrected, with root cause analysis
          and prevention recommendation (contracts validation)

       3. **Result note:** spindle-ripple coupling validated with
          cross-subject metrics

       The investigation trace is fully documented. Any future agent
       encountering a flat correlogram will find the observation notes
       explaining that freq_band misconfiguration was the cause.
```

!!! warning "Human checkpoint"
    ```
    Human: Update the coupling milestone and let's move on.
    ```

    ```
    → [updates plan/milestones.yml: delta-ripple-coupling → complete,
       evidence: [result-arash-20260408-XXXXXX]]
    ```

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **pipeio** | `pipeio_target_paths`, `pipeio_mod_context`, `pipeio_config_read`, `pipeio_config_patch`, `pipeio_run`, `pipeio_run_status`, `pipeio_contracts_validate` (recommended) | Trace outputs, inspect code, read/fix config, re-run |
| **codio** | `codio_get` | Verify coupling code is well-tested |
| **biblio** | (implicit) | Literature values for expected coupling peak |
| **notio** | `note_create` (observation × 4, decision × 1, result × 1) | Investigation trail and formal evidence |
| **questio** | (milestone update) | Record coupling validation |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1-2. Reproduce and scope | Investigate | Confirm symptom, determine scope (all subjects = systemic) |
| 3. Check coupling code | Investigate | Rule out direct cause |
| 4. Trace ripples | Investigate | Check input A — normal |
| 5. Trace spindles | Investigate | Check input B — **anomalous** → trace to config |
| 6. Root cause | Investigate | Config drift identified |
| 7. Fix and re-run | Iterate | Config patch → re-run → verify coupling peak |
| 8. Record | (post-loop) | Investigation trail + result note + milestone |

## Key insight

**Cross-flow debugging requires tracing the full dependency chain — the symptom is never where the cause is.** The flat correlogram was in `coupling_spindle_ripple`, but the bug was in `spectrogram_burst`'s config. The agent systematically eliminated suspects: coupling code → ripple detection → spindle detection → config. Without this discipline, the researcher might have spent hours debugging the coupling code or doubting the coupling hypothesis — when the real issue was a frequency band that drifted after validation.

This scenario also demonstrates the **investigate → iterate transition**: once the root cause was found (investigate loop complete), the agent entered the iterate loop to apply the fix, re-run, and verify. The two loops compose naturally.
