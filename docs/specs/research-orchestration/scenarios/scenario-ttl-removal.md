# Scenario: TTL Characterization and Removal — Notebook to Pipeline

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Milestone `ttl-removal-validated` is `in_progress` with empty evidence
- Pipeline `preprocess_ieeg` has TTL removal rule, script, and config
- cogpy library has TTL primitives (`cogpy.triggered.estimate_template`, `subtract_template`)
- Investigation notebooks exist but haven't been validated on all subjects
- 5 real subjects available (sub-01 through sub-05), plus sub-test

**What the researcher wants:** Characterize the TTL artifact, validate the removal approach, then run the full pipeline and record evidence.

---

## Phase 1: Orient — "Where are we?"

```
Human: I want to tackle TTL characterization and removal for pixecog.
       What's the current state?
```

!!! info "Behind the scenes"
    ```
    → questio_status()
      Returns: 7 questions, ttl-removal-validated is in_progress, 0 evidence,
      blocks ieeg-preprocessing-stable which blocks 5 hypotheses

    → questio_gap("H1")
      Returns: root blocker is ttl-removal-validated
      flow: preprocess_ieeg, status: in_progress, evidence: []

    → pipeio_flow_status("preprocess_ieeg")
      Returns: configured, ttl mod exists, test run completed for sub-test
    ```

```
Agent: Here's where things stand for TTL removal:

       **Milestone:** ttl-removal-validated — in_progress, no evidence recorded yet
       **Flow:** preprocess_ieeg — configured, ttl mod and rule exist
       **Test run:** sub-test has been processed (1 valid TTL event, QC metrics are zero
       due to minimal test data)
       **Blocking:** this milestone gates ieeg-preprocessing-stable, which gates
       SWR detection, spindle detection, and all 7 hypotheses

       There are investigation notebooks in notebooks/explore/ (investigate_ttl_artifact,
       ttl_artifact_removal) and a demo notebook (ttl_characterization_removal) that
       needs execution.

       **Recommended approach:**
       1. Start with characterization on one real subject (sub-01) to understand
          the artifact
       2. Validate removal on that subject
       3. Run across all subjects
       4. Record evidence for the milestone

       Want to start with sub-01 characterization?
```

!!! tip "Orient loop"
    The agent used the orient loop — `questio_status` → `questio_gap` → `pipeio_flow_status` — to survey the state and produce a prioritized recommendation. The human hasn't had to navigate any of this manually.

---

## Phase 2: Ground — literature and code context

```
Human: Yes, let's start. But first, what does the literature say about TTL
       artifacts and removal approaches?
```

!!! info "Behind the scenes"
    ```
    → paper_context("@sirota_2003")    — early reference for in-vivo electrophysiology
    → paper_context("@buzsaki_2012")   — large-scale recording methodology
    → codio_get("cogpy")               — check existing TTL code
    → rag_query("TTL artifact removal template subtraction")
    → skill_read("ttl_artifact_notebook")  — the design prompt for TTL work
    ```

```
Agent: **Literature context:**
       TTL artifacts at 120 Hz are common in simultaneous stimulation-recording
       setups. Standard approach: template subtraction with median template
       estimation (robust to neural signal contamination). Key QC metrics:
       artifact power reduction (>20 dB expected) and neural band distortion
       (<1 dB in 1-30 Hz).

       **Existing code (cogpy.triggered):**
       - estimate_template(epochs, method="median") — template estimation
       - subtract_template(signal, events, template, scaling) — removal
       - fit_scaling(signal, template) — per-event amplitude fitting
       - triggered_snr() — QC metric

       **Current config** (preprocess_ieeg/config.yml):
       - ttl_freq: 120 Hz, template_method: median
       - skip_s: 20 (exclude first 20s direct injection)
       - pre_ms: 12, post_ms: 12 (epoch window)
       - neural_band_hz: [1, 30]

       **Prior work:** the investigation notebooks exist but outputs haven't been
       reviewed against literature expectations. The test run on sub-test
       showed 0% artifact reduction (too few events in test data).

       Ready to run the characterization notebook on sub-01.
```

!!! tip "Literature-first grounding"
    The agent used `questio-ground` — literature, codio, rag query, and the TTL design prompt — to establish what "good" looks like before touching any data. This grounds all subsequent judgment.

---

## Phase 3: Iterate — notebook development

```
Human: Run the characterization notebook on sub-01. I want to see the
       spectral signature of the artifact first.
```

!!! info "Behind the scenes — iteration 1"
    ```
    → pipeio_nb_exec(flow="preprocess_ieeg",
                     name="investigate_ttl_artifact",
                     parameters={"subject": "sub-01", "session": "ses-04"})

    → pipeio_nb_read(flow="preprocess_ieeg",
                     name="investigate_ttl_artifact")
      Returns: notebook outputs — spectral plots, spatial maps, temporal structure

    → note_create(kind="idea", tags=["observation", "iterate"],
                  series="preprocess_ieeg",
                  title="Iteration 1: TTL artifact characterization sub-01")
    ```

```
Agent: Notebook executed for sub-01/ses-04. Key findings:

       **Spectral:** clear 120 Hz peak at ~35 dB above noise floor, with
       harmonics at 240 Hz and 360 Hz visible. Consistent with TTL injection.

       **Spatial:** artifact is strongest on contacts closest to the stimulation
       site (channels 55-65). Reference channel 59 shows highest artifact power
       (3.31 arbitrary units from prior test).

       **Temporal:** artifact is stable across the session after the first 20s
       (confirming skip_s=20 is appropriate).

       This matches literature expectations. The artifact is well-characterized
       and amenable to template subtraction.

       Next: run the removal notebook and check before/after spectra?
```

```
Human: Yes, run removal. But also check if there's distortion in the
       neural band (1-30 Hz) after removal.
```

!!! info "Behind the scenes — iteration 2"
    ```
    → pipeio_nb_exec(flow="preprocess_ieeg",
                     name="ttl_artifact_removal",
                     parameters={"subject": "sub-01", "session": "ses-04"})

    → pipeio_nb_read(flow="preprocess_ieeg",
                     name="ttl_artifact_removal")

    → note_create(kind="idea", tags=["observation", "iterate"],
                  series="preprocess_ieeg",
                  title="Iteration 2: TTL removal sub-01, checking neural distortion")
    ```

```
Agent: Removal results for sub-01/ses-04:

       **Artifact reduction:** 120 Hz peak reduced by 28 dB (literature
       expects >20 dB). Good.

       **Neural band distortion:** 1-30 Hz power changed by -0.3 dB
       (literature threshold: <1 dB). Acceptable.

       **Per-channel:** removal is consistent across channels. Reference
       channel 59 shows the largest improvement (32 dB reduction).

       **Cross-check against grounding:** artifact reduction exceeds the
       20 dB threshold from literature. Neural distortion is well below
       1 dB. Template method (median) appears to be working as expected.

       Sub-01 looks clean. Want to extend to remaining subjects, or
       adjust parameters first?
```

```
Human: The 28 dB reduction is good but I want to see sub-02 as well
       before running all subjects — sub-02 has different session types
       (pre, post, track).
```

!!! info "Behind the scenes — iteration 3"
    ```
    → pipeio_nb_exec(flow="preprocess_ieeg",
                     name="ttl_artifact_removal",
                     parameters={"subject": "sub-02", "session": "ses-02"})

    → pipeio_nb_read(...)

    → note_create(kind="idea", tags=["observation", "iterate"],
                  series="preprocess_ieeg",
                  title="Iteration 3: TTL removal sub-02/ses-02 (task-pre)")
    ```

```
Agent: Sub-02/ses-02 (task-pre) results:

       **Artifact reduction:** 24 dB. Lower than sub-01 (28 dB) but still
       above the 20 dB threshold.

       **Neural distortion:** -0.5 dB. Slightly higher than sub-01 but
       within threshold.

       **Note:** sub-02 has more TTL events (12 vs sub-01's 8), which
       gives a better template estimate. The lower reduction may be due
       to different electrode placement relative to stimulation site.

       **Trajectory:** 2 subjects tested, both pass QC thresholds.
       Consistent with literature expectations.

       Ready to run all 5 subjects via the pipeline?
```

!!! tip "Iterate loop"
    Three iterations of the iterate loop. Each cycle: execute → assess → report → human feedback. The agent captured observation notes at each step. The human directed each iteration — choosing which subject to test, asking for specific checks. The agent never autonomously re-iterated.

---

## Phase 4: Pipeline execution — full run

```
Human: Yes, run the full pipeline for all subjects.
```

!!! info "Behind the scenes"
    ```
    → pipeio_flow_status("preprocess_ieeg")
      Returns: configured, all dependencies met

    → pipeio_target_paths("preprocess_ieeg", mod="ttl")
      Returns: target paths for all subjects/sessions
    ```

!!! warning "Human checkpoint"
    ```
    Agent: This will run TTL removal for all 5 subjects across their sessions:
           - sub-01: 4 sessions
           - sub-02: 5 sessions
           - sub-03, sub-04, sub-05: [N sessions each]

           Total: ~[N] jobs. Based on the notebook runs, each takes about
           2-3 minutes. Full run estimate: ~30-45 minutes.

           Proceed?
    ```

```
Human: Go ahead.
```

!!! info "Behind the scenes"
    ```
    → pipeio_run(flow="preprocess_ieeg", targets="ttl_removal/sub-*")

    → [monitors via pipeio_run_status periodically]

    → note_create(kind="idea", tags=["observation", "iterate"],
                  series="preprocess_ieeg",
                  title="Pipeline run: TTL removal all subjects initiated")
    ```

```
Agent: Pipeline running. I'll check status and report when complete.

       [... time passes ...]

       Pipeline complete. All 5 subjects processed. Let me inspect the results.
```

!!! tip "Propose-review-confirm"
    Dry-run/confirmation pattern — the agent showed what would execute and got explicit confirmation before committing compute. This is the propose-review-confirm pattern for expensive operations.

---

## Phase 5: Assess — agent-as-judge

!!! info "Behind the scenes"
    ```
    → pipeio_target_paths("preprocess_ieeg", mod="ttl")
      → reads QC JSON logs for each subject/session

    → paper_context — re-checks literature thresholds

    → note_create(kind="idea", tags=["observation", "iterate"],
                  series="preprocess_ieeg",
                  title="Assessment: TTL removal across all 5 subjects")
    ```

```
Agent: **Cross-subject results:**

       | Subject | Sessions | Artifact reduction (dB) | Neural distortion (dB) | Pass? |
       |---------|----------|------------------------|----------------------|-------|
       | sub-01  | 4        | 28.1 ± 1.2             | -0.3 ± 0.1          | Yes   |
       | sub-02  | 5        | 24.3 ± 2.0             | -0.5 ± 0.2          | Yes   |
       | sub-03  | 3        | 26.7 ± 1.5             | -0.2 ± 0.1          | Yes   |
       | sub-04  | 4        | 25.9 ± 1.8             | -0.4 ± 0.2          | Yes   |
       | sub-05  | 3        | 27.2 ± 1.1             | -0.3 ± 0.1          | Yes   |

       **Summary:** all subjects pass both QC thresholds:
       - Artifact reduction: 25.4 ± 2.1 dB (threshold: >20 dB) ✓
       - Neural distortion: -0.3 ± 0.2 dB (threshold: <1 dB) ✓

       Cross-subject consistency is good (low variance).
       Results are consistent with literature expectations.

       I recommend creating a result note and marking the
       ttl-removal-validated milestone as complete. Want me to proceed?
```

!!! tip "Agent-as-judge"
    This is agent-as-judge in action. No pre-scripted validation notebook — the agent read the QC logs, compared against literature thresholds established during grounding, and made an assessment. The assessment is presented to the human, not silently acted on.

---

## Phase 6: Record — evidence capture

```
Human: Yes, record it.
```

!!! info "Behind the scenes"
    ```
    → note_create(note_type="result",
                  title="TTL removal validated across all subjects",
                  series="preprocess_ieeg",
                  question=["H1", "H2", "H3", "H4", "H5", "H6", "H7"],
                  milestone="ttl-removal-validated",
                  subjects=["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
                  metric="artifact_reduction_db",
                  value="25.4 ± 2.1 dB (all subjects > 20 dB threshold)",
                  confidence="validated")
    ```

!!! warning "Human checkpoint"
    ```
    Agent: Result note created: result-arash-20260408-XXXXXX.md

           Milestone update proposal:
           - ttl-removal-validated: in_progress → complete
           - Evidence: [result-arash-20260408-XXXXXX]

           This unblocks ieeg-preprocessing-stable (next milestone in chain).
           Confirm the milestone update?
    ```

```
Human: Confirmed.
```

!!! info "Behind the scenes"
    ```
    → updates plan/milestones.yml: ttl-removal-validated status → complete,
      evidence → [result-arash-20260408-XXXXXX]

    → questio_gap("H1")
      Returns: ttl-removal-validated: complete. Next blocker:
      ieeg-preprocessing-stable (needs remaining preprocessing steps)
    ```

```
Agent: Milestone updated. ttl-removal-validated is now complete.

       Next in the chain: ieeg-preprocessing-stable depends on this
       plus ecephys preprocessing. The TTL gate is cleared — detection
       pipelines (SWR, spindle) are one step closer to being unblocked.

       Want to continue with the next milestone, or stop here?
```

!!! tip "Propose-review-confirm for milestones"
    The agent created the result note, proposed the status change, and waited for human confirmation. The result note references all 5 iteration observations as context.

---

## Phase 7 (optional): Schedule downstream work

```
Human: Let's stop here for now. But schedule the ecephys TTL removal
       as a background task — same approach, same thresholds.
```

!!! info "Behind the scenes"
    ```
    → worklog_note(project_id="pixecog",
                   text="Run TTL removal for preprocess_ecephys flow.
                         Same approach as preprocess_ieeg: template subtraction,
                         median method, QC thresholds: >20 dB artifact reduction,
                         <1 dB neural distortion. Run for all subjects, create
                         result note and propose milestone update.",
                   kind="issue",
                   auto_dispatch=True,
                   model="opus")
    ```

```
Agent: Dispatched as a background task. It will run the ecephys TTL removal,
       assess results against the same thresholds, and propose a milestone
       update for ecephys-preprocessing-stable when done. You'll get a
       notification when it completes.
```

!!! tip "Worklog dispatch"
    The human chose to schedule follow-on work via worklog. The background agent will follow the same iterate loop pattern autonomously, but with the propose-review-confirm pattern — it will create observations and a result note, then propose (not auto-apply) the milestone update.

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **questio** | `questio_status`, `questio_gap` | Orient loop — map milestone state and blocking chains |
| **pipeio** | `pipeio_flow_status`, `pipeio_nb_exec`, `pipeio_nb_read`, `pipeio_target_paths`, `pipeio_run`, `pipeio_run_status` | Pipeline inspection, notebook execution, full pipeline run |
| **codio** | `codio_get` | Discover existing TTL removal code in cogpy |
| **biblio** | `paper_context` | Literature context for QC thresholds |
| **notio** | `note_create` (observation × 5, result × 1) | Mid-loop capture and formal evidence |
| **indexio** | `rag_query` | Semantic search for artifact removal approaches |
| **worklog** | `worklog_note` | Dispatch downstream ecephys task |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1. Orient | Orient | `questio_status` → `questio_gap` → `pipeio_flow_status` → prioritized recommendation |
| 2. Ground | (pre-loop) | Literature + codio + rag → established expectations and quality criteria |
| 3. Notebook iteration | Iterate | 3 cycles: execute notebook → assess → report → human feedback → adjust |
| 4. Pipeline run | Iterate | Dry-run/confirm → execute → monitor |
| 5. Assessment | Iterate (assess step) | Agent reads QC logs, compares to literature, presents judgment |
| 6. Record | (post-loop) | Result note + propose-review-confirm for milestone |
| 7. Schedule | (worklog) | Dispatch downstream work as background task |

## Recording trail produced

| Note | Type | Content |
|------|------|---------|
| observation-1 | idea [observation, iterate] | Iteration 1: TTL characterization sub-01 |
| observation-2 | idea [observation, iterate] | Iteration 2: TTL removal sub-01, neural distortion check |
| observation-3 | idea [observation, iterate] | Iteration 3: TTL removal sub-02 cross-session |
| observation-4 | idea [observation, iterate] | Pipeline run initiated |
| observation-5 | idea [observation, iterate] | Cross-subject assessment |
| result-1 | result | TTL removal validated — formal milestone evidence |

## Key insight

This scenario demonstrates the **full milestone lifecycle** — from orient through grounding, iterative validation, pipeline execution, assessment, and evidence capture. The agent never auto-advances; every transition is human-directed. The recording trail makes the journey reproducible: anyone can trace *why* the milestone was marked complete by reading the observation and result notes.
