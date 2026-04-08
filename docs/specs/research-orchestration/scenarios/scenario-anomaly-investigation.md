# Scenario: Investigating an Anomaly Mid-Pipeline

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Same as end of TTL removal scenario — `ttl-removal-validated` is complete
- SWR detection pipeline is running on all subjects
- Sub-03 shows unexpected results during detection stage

**What the researcher wants:** Understand why sub-03's SWR detection rate is anomalously low and decide on a fix.

---

## Phase 1: Reproduce and scope

```
Human: The SWR detection rate for sub-03 is way too low — 2/min when
       literature says 10-15/min. What's going on?
```

!!! info "Behind the scenes"
    ```
    → questio_status() — confirms swr-detection is in_progress
    → pipeio_target_paths("sharpwaveripple") — locates sub-03 outputs
    → reads sub-03 detection output — confirms 2.1 events/min
    → reads sub-01 and sub-02 for comparison — 12.3/min and 11.8/min (normal)

    → note_create(kind="idea", tags=["observation", "investigate"],
                  title="Investigate: sub-03 SWR rate anomaly (2.1/min vs expected 10-15)")
    ```

```
Agent: Confirmed: sub-03 SWR detection rate is 2.1/min (sub-01: 12.3, sub-02: 11.8).

       **Scoping:** the issue is sub-03 only. Other subjects are in normal range.

       **Checking upstream:** let me verify the preprocessing output for sub-03.
```

---

## Phase 2: Check upstream

!!! info "Behind the scenes"
    ```
    → pipeio_target_paths("preprocess_ieeg", mod="ttl") — reads sub-03 QC log
    → reads the preprocessed signal for sub-03 — checks spectral content

    → note_create(kind="idea", tags=["observation", "investigate"],
                  title="Investigation: sub-03 preprocessing looks clean, issue is downstream")
    ```

```
Agent: **Upstream check:** TTL removal QC for sub-03 looks normal (26.7 dB reduction,
       -0.2 dB distortion). Preprocessed signal is clean.

       **Narrowing:** the issue is not preprocessing — it's in the detection stage.
       Let me check the detection parameters and sub-03's signal characteristics.
```

!!! tip "Diagnostic strategy"
    The agent follows the investigate loop: reproduce → scope (sub-03 only) → check upstream (preprocessing is clean) → trace downstream. Each step narrows the search space.

---

## Phase 3: Root cause analysis

!!! info "Behind the scenes"
    ```
    → pipeio_mod_context("sharpwaveripple", mod="detect_swr")
    → reads sub-03 raw signal characteristics (amplitude, noise floor)
    → paper_context("@sirota_2003") — ripple amplitude expectations

    → note_create(kind="idea", tags=["observation", "investigate"],
                  title="Root cause: sub-03 has lower amplitude ripples, threshold too high")
    ```

```
Agent: **Root cause identified:** sub-03 has lower overall signal amplitude
       compared to other subjects (likely electrode placement). The detection
       threshold (3.5 SD) is appropriate for sub-01 and sub-02 but too
       aggressive for sub-03.

       **Evidence:**
       - sub-03 mean ripple amplitude: 85 μV (sub-01: 145 μV, sub-02: 130 μV)
       - At 3.5 SD threshold, sub-03 misses ripples in the 80-100 μV range
       - Literature reports ripple amplitudes vary 2-3x across recording sites

       **Options:**
       1. Lower threshold to 3.0 SD for sub-03 (per-subject tuning)
       2. Use adaptive thresholding based on local noise floor
       3. Accept lower detection rate for sub-03 as a biological difference

       Which approach do you prefer?
```

---

## Phase 4: Decision and record

```
Human: Option 2 — adaptive thresholding. But let's iterate on that in a
       separate session. Record what we found.
```

!!! info "Behind the scenes"
    ```
    → note_create(kind="idea", tags=["observation", "investigate", "decision"],
                  title="Decision: use adaptive thresholding for SWR detection")
      Body: sub-03 has lower amplitude ripples due to electrode placement.
            Fixed threshold misses events. Human chose adaptive thresholding.
            To be implemented in next session.
    ```

```
Agent: Recorded. Three observation notes from this investigation, plus the
       decision to use adaptive thresholding. This will feed into the
       iterate loop when you're ready to implement it.
```

!!! tip "Investigation without pre-scripted notebooks"
    Pure investigate loop. The agent followed the diagnostic strategy: reproduce → scope (sub-03 only) → check upstream (preprocessing is clean) → trace to the detection stage → identify root cause (amplitude difference + threshold sensitivity) → present options → human decides. No pre-scripted notebook — the agent reasoned over tool outputs.

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **questio** | `questio_status` | Confirm milestone is in progress |
| **pipeio** | `pipeio_target_paths`, `pipeio_mod_context` | Locate outputs, inspect detection code and config |
| **biblio** | `paper_context` | Literature expectations for ripple amplitudes |
| **notio** | `note_create` (observation × 3, decision × 1) | Investigation trail and decision recording |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1. Reproduce and scope | Investigate | Confirm symptom, determine scope (sub-03 only) |
| 2. Check upstream | Investigate | Rule out preprocessing as cause |
| 3. Root cause | Investigate | Compare signal characteristics + literature → identify threshold sensitivity |
| 4. Decision | (human) | Human picks adaptive thresholding, defers implementation |

## Recording trail produced

| Note | Type | Content |
|------|------|---------|
| observation-1 | idea [observation, investigate] | SWR rate anomaly: 2.1/min vs expected 10-15 |
| observation-2 | idea [observation, investigate] | Preprocessing clean, issue is downstream |
| observation-3 | idea [observation, investigate] | Root cause: lower amplitude ripples + fixed threshold |
| decision-1 | idea [observation, investigate, decision] | Use adaptive thresholding (to implement next session) |

## Key insight

This scenario shows the **investigate loop** in isolation — a focused diagnostic workflow without any pipeline execution or milestone advancement. The agent narrows the problem systematically, presents options with evidence, and the human makes the engineering decision. The investigation trail is preserved in notes so the next session can pick up where this one left off.
