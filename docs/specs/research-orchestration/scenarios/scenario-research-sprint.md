# Scenario: Multi-Day Scheduled Research Sprint

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- Milestone `ttl-removal-validated` is `complete` (Scenario 1 in the scenario book)
- Three preprocessing milestones are unblocked and `not_started`:
    - `ieeg-preprocessing-stable` (flow: `preprocess_ieeg`)
    - `ecephys-preprocessing-stable` (flow: `preprocess_ecephys`)
    - `brainstate-classification-validated` (flow: `brainstate`, depends on `ieeg-preprocessing-stable`)
- Each milestone requires: run pipeline → validate across subjects → record evidence
- The researcher has a week and wants to clear all three
- 5 subjects (sub-01 through sub-05), each with multiple sessions

**What the researcher wants:** Clear the preprocessing backlog in one week using scheduled background agents, with daily human review checkpoints.

---

## Day 1 Morning: Planning session

```
Human: I want to clear all preprocessing milestones this week. The TTL
       gate is open, three milestones are unblocked. Can you set up a
       sprint plan?
```

!!! info "Behind the scenes"
    ```
    → questio_status()
      Returns: 7 hypotheses, all blocked by preprocessing milestones
        ttl-removal-validated: complete ✓
        ieeg-preprocessing-stable: not_started (unblocked)
        ecephys-preprocessing-stable: not_started (unblocked)
        brainstate-classification-validated: not_started (blocked by ieeg)

    → questio_gap("H1")
      Returns: root blocker is ieeg-preprocessing-stable
               then swr-detection-validated (depends on ecephys + brainstate)

    → pipeio_flow_status("preprocess_ieeg")
      Returns: configured, remaining steps: rereferencing, filtering, epoching
               TTL removal complete for all subjects

    → pipeio_flow_status("preprocess_ecephys")
      Returns: configured, needs TTL removal + full preprocessing
               Independent of iEEG (shares only TTL config)

    → pipeio_flow_status("brainstate")
      Returns: configured, depends on preprocessed iEEG output
               Uses LFP features for NREM/REM/wake classification
    ```

```
Agent: **Sprint plan — preprocessing milestones:**

       **Dependency analysis:**
       ```
       ttl-removal-validated ✓
         ├→ ieeg-preprocessing-stable (Day 1-2)
         │    └→ brainstate-classification-validated (Day 3)
         └→ ecephys-preprocessing-stable (Day 1-2, parallel)
       ```

       **Proposed schedule:**

       | Day | Task | Flow | Dependencies |
       |-----|------|------|-------------|
       | Day 1 (Tue) | iEEG preprocessing | preprocess_ieeg | TTL done ✓ |
       | Day 1 (Tue) | ecephys preprocessing | preprocess_ecephys | TTL done ✓ |
       | Day 2 (Wed) | Review Day 1 results | — | ieeg + ecephys complete |
       | Day 2 (Wed) | Brainstate classification | brainstate | ieeg done |
       | Day 3 (Thu) | Review all results | — | all complete |
       | Day 3 (Thu) | Update milestones, plan next | — | human review |

       **Key constraint:** brainstate depends on ieeg, so it can't start
       until Day 2 at earliest. But ieeg and ecephys can run in parallel
       on Day 1.

       **Background agent approach:**
       - Each task runs as a scheduled background agent
       - Background agents: orient → run pipeline → assess → create notes → PROPOSE milestone update
       - Background agents do NOT auto-apply milestone changes
       - You review each morning and approve/reject

       Want me to set up the schedule?
```

!!! tip "Autonomy levels"
    Background agents can: run pipelines, read outputs, compare against literature, create observation and result notes, and **propose** milestone updates. They cannot: apply milestone updates, change pipeline configurations, or make decisions about scientific interpretation. The daily morning review is where the human exercises judgment over the agent's proposals.

```
Human: Set it up. Run ieeg and ecephys tonight — I want results by
       tomorrow morning.
```

---

## Day 1: Scheduling — setting up the sprint queue

!!! info "Behind the scenes"
    ```
    → worklog_note(project_id="pixecog",
                   text="## Prompt\n\nSprint task: iEEG preprocessing (preprocess_ieeg)\n\n1. Orient: call questio_status, pipeio_flow_status('preprocess_ieeg')\n2. Ground: check cogpy preprocessing functions, literature for QC thresholds\n3. Run pipeline for all 5 subjects (sub-01 through sub-05)\n4. Assess results:\n   - Check spectral content (no artifact residuals in 100+ Hz)\n   - Check signal amplitude (within physiological range)\n   - Check continuity (no gaps or dropouts)\n   - Compare SNR across subjects\n5. Create observation notes for each assessment step\n6. Create result note with cross-subject QC summary\n7. PROPOSE milestone update for ieeg-preprocessing-stable → complete\n   (do NOT auto-apply — wait for human review)\n\nQC thresholds from literature:\n- No residual TTL artifact (>20 dB reduction confirmed in prior milestone)\n- Signal amplitude: 50-500 μV range\n- No segments with >5% dropout\n- SNR > 3 dB in neural bands (1-100 Hz)",
                   kind="task",
                   auto_dispatch=True,
                   model="opus")
      Returns: queue_id="q-001"

    → worklog_note(project_id="pixecog",
                   text="## Prompt\n\nSprint task: ecephys preprocessing (preprocess_ecephys)\n\n1. Orient: call questio_status, pipeio_flow_status('preprocess_ecephys')\n2. Ground: check cogpy ecephys preprocessing, literature for Neuropixels QC\n3. Run pipeline for all 5 subjects\n4. Assess results:\n   - Check spike sorting quality metrics (if applicable)\n   - Check LFP quality in hippocampal channels\n   - Check electrode drift estimation\n   - Verify ripple-band (100-300 Hz) content present\n5. Create observation notes for assessment\n6. Create result note with cross-subject summary\n7. PROPOSE milestone update for ecephys-preprocessing-stable → complete\n\nQC thresholds:\n- LFP amplitude in hippocampal channels: 100-1000 μV\n- Ripple-band power present (spectral peak at 100-300 Hz during NREM)\n- Electrode drift < 50 μm over session",
                   kind="task",
                   auto_dispatch=True,
                   model="opus")
      Returns: queue_id="q-002"
    ```

!!! note "Scheduling pattern"
    Both tasks are dispatched immediately because they're independent (ieeg and ecephys don't depend on each other). The prompts are detailed — they include the full orient → ground → execute → assess → record pattern, with explicit QC thresholds and a clear instruction to PROPOSE but not auto-apply milestone updates.

    For the brainstate task, which depends on ieeg completion, we use `schedule_queue` with `after=` to create a dependency:

    ```
    → worklog_note(project_id="pixecog",
                   text="## Prompt\n\nSprint task: brainstate classification (brainstate flow)\n\nPREREQUISITE: ieeg-preprocessing-stable must be complete.\nCheck questio_status first — if the milestone is still not_started or\nthe human hasn't approved it yet, wait and report back.\n\n1. Orient: questio_status, pipeio_flow_status('brainstate')\n2. Ground: check literature for brain state classification criteria\n   - NREM: delta power dominant, spindle activity present\n   - REM: theta power dominant, low delta\n   - Wake: mixed frequency, high EMG\n3. Run brainstate pipeline for all 5 subjects\n4. Assess:\n   - State proportions (literature: ~50% NREM, ~10% REM, ~40% wake for sleep sessions)\n   - Transition rates (not too frequent — suggests noisy classification)\n   - Visual check: state hypnogram makes physiological sense\n5. Create observation notes and result note\n6. PROPOSE milestone update for brainstate-classification-validated",
                   kind="task")
      Returns: note_path for brainstate task

    → schedule_queue(task_path=note_path, after="q-001")
      Returns: queue_id="q-003", scheduled after q-001 (ieeg)
    ```

```
Agent: **Sprint queue set up:**

       | Queue ID | Task | Status | Dependencies |
       |----------|------|--------|-------------|
       | q-001 | iEEG preprocessing | running | none |
       | q-002 | ecephys preprocessing | running | none |
       | q-003 | brainstate classification | queued | after q-001 |

       Both ieeg and ecephys are running now. Brainstate will start
       automatically after ieeg completes (and after you've approved
       the milestone in your morning review).

       I'll have results for you tomorrow morning.
```

---

## Day 1 Evening: Background agents at work

!!! info "Behind the scenes"
    The background agent for q-001 (iEEG preprocessing) runs autonomously:

    ```
    [Background agent — q-001]

    → questio_status()
    → pipeio_flow_status("preprocess_ieeg")
    → codio_get("cogpy")    # preprocessing functions
    → rag_query("iEEG preprocessing quality metrics")

    → pipeio_run(flow="preprocess_ieeg", wildcards={"subject": "sub-*"})
    → pipeio_run_status(run_id)    # monitors until completion

    → pipeio_target_paths("preprocess_ieeg", group="preprocessed")
    → [reads QC metrics for each subject/session]

    → note_create(note_type="idea", tags=["observation", "iterate"],
                  series="preprocess_ieeg",
                  title="Sprint assessment: iEEG preprocessing 5/5 subjects complete")

    → note_create(note_type="result",
                  title="iEEG preprocessing validated — all subjects pass QC",
                  series="preprocess_ieeg",
                  milestone="ieeg-preprocessing-stable",
                  subjects=["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
                  metric="signal_quality",
                  value="SNR 8.2 ± 1.3 dB, no artifact residuals, no dropouts",
                  confidence="validated")

    → [DOES NOT update milestone — creates proposal in result note]
    ```

    The background agent for q-002 (ecephys) runs similarly but encounters an issue with sub-04:

    ```
    [Background agent — q-002]

    → pipeio_run(flow="preprocess_ecephys", wildcards={"subject": "sub-*"})
      sub-01: complete ✓
      sub-02: complete ✓
      sub-03: complete ✓
      sub-04: FAILED — electrode drift exceeded 100 μm threshold
      sub-05: complete ✓

    → note_create(note_type="idea", tags=["observation", "investigate"],
                  series="preprocess_ecephys",
                  title="Sprint issue: sub-04 ecephys failed — electrode drift 112 μm")

    → [agent investigates: reads drift estimation log, checks if drift
       correction can rescue the data]

    → note_create(note_type="idea", tags=["observation", "investigate"],
                  series="preprocess_ecephys",
                  title="Investigation: sub-04 drift appears to be post-probe insertion settling, first 30 min affected")

    → note_create(note_type="result",
                  title="Ecephys preprocessing: 4/5 subjects pass, sub-04 excluded (drift)",
                  series="preprocess_ecephys",
                  milestone="ecephys-preprocessing-stable",
                  subjects=["sub-01", "sub-02", "sub-03", "sub-05"],
                  metric="lfp_quality",
                  value="LFP SNR 6.8 ± 0.9 dB, ripple-band present, 4/5 subjects",
                  confidence="validated_with_caveats")
    ```

---

## Day 2 Morning: Review — "What happened overnight?"

```
Human: Good morning. What happened with the preprocessing sprint?
```

!!! info "Behind the scenes"
    ```
    → list_queue(status="all")
      Returns:
        q-001: completed (iEEG preprocessing)
        q-002: completed (ecephys preprocessing)
        q-003: queued (brainstate — waiting for ieeg milestone approval)

    → questio_status()
      Returns: ieeg-preprocessing-stable still not_started (pending human approval)
               ecephys-preprocessing-stable still not_started (pending human approval)

    → note_search(query="sprint assessment preprocessing")
      Returns: result notes and observation notes from overnight agents
    ```

!!! example "Morning report"
    ```
    Agent: **Sprint status — Day 2 morning:**

           ## Completed overnight

           **iEEG preprocessing (q-001): SUCCESS**
           - All 5 subjects processed
           - QC: SNR 8.2 ± 1.3 dB, no artifact residuals, no dropouts
           - Result note created: result-arash-20260409-001
           - **Milestone proposal:** ieeg-preprocessing-stable → complete
           - Pending your approval

           **Ecephys preprocessing (q-002): PARTIAL SUCCESS**
           - 4/5 subjects processed successfully
           - sub-04 FAILED: electrode drift of 112 μm (threshold: 50 μm)
           - Background agent investigated: drift is concentrated in first
             30 minutes (post-insertion settling). Later portions may be usable.
           - Result note: result-arash-20260409-002 (4/5 subjects, with caveat)
           - **Milestone proposal:** ecephys-preprocessing-stable → complete
             (with sub-04 excluded)

           ## Queued

           **Brainstate classification (q-003):** waiting for your approval
           of ieeg-preprocessing-stable before starting

           ## Actions needed
           1. Review iEEG result note → approve milestone?
           2. Decide on sub-04: exclude, attempt drift correction, or defer?
           3. Approve ecephys milestone (4/5)?
    ```

```
Human: iEEG looks clean — approve the milestone. For sub-04 ecephys,
       skip it for now. I know that probe had issues during insertion.
       Approve ecephys with 4 subjects.
```

!!! warning "Human checkpoint"
    The morning review is the essential human-in-the-loop checkpoint. The background agents did the work and proposed the outcomes, but the human makes the final call. This is especially important for sub-04 — the agent correctly flagged the issue and investigated, but the decision to exclude a subject is scientific judgment that belongs to the human.

!!! info "Behind the scenes"
    ```
    → [updates plan/milestones.yml:
       ieeg-preprocessing-stable → complete, evidence: [result-arash-20260409-001]
       ecephys-preprocessing-stable → complete, evidence: [result-arash-20260409-002]]

    → note_create(note_type="idea", tags=["decision"],
                  series="preprocess_ecephys",
                  title="Decision: exclude sub-04 from ecephys — known probe insertion issues")
    ```

```
Agent: Milestones updated:
       - ieeg-preprocessing-stable: **complete** ✓
       - ecephys-preprocessing-stable: **complete** (4/5 subjects) ✓

       Decision note created for sub-04 exclusion.

       Brainstate task (q-003) is now unblocked — starting automatically.
```

---

## Day 2 Evening: Brainstate runs

!!! info "Behind the scenes"
    ```
    [Background agent — q-003, triggered by ieeg milestone approval]

    → questio_status()
      Confirms: ieeg-preprocessing-stable is complete

    → pipeio_run(flow="brainstate", wildcards={"subject": "sub-*"})
      All 5 subjects processed (brainstate uses iEEG, not ecephys —
      sub-04 is fine here)

    → [assesses state proportions, transition rates, hypnogram quality]

    → note_create(note_type="result",
                  title="Brainstate classification validated — physiological state proportions",
                  series="brainstate",
                  milestone="brainstate-classification-validated",
                  subjects=["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
                  metric="state_proportions",
                  value="NREM 52±4%, REM 8±2%, wake 40±5% (sleep sessions)",
                  confidence="validated")
    ```

---

## Day 3 Morning: Course correction

```
Human: How did brainstate go?
```

!!! info "Behind the scenes"
    ```
    → list_queue(status="all")
      Returns: q-003 completed

    → note_search(query="sprint brainstate result")
    ```

!!! example "Morning report"
    ```
    Agent: **Brainstate classification (q-003): SUCCESS**

           - All 5 subjects classified (uses iEEG, sub-04 is fine here)
           - State proportions (sleep sessions):
             NREM: 52 ± 4%, REM: 8 ± 2%, Wake: 40 ± 5%
           - Literature expects: ~50% NREM, ~10% REM, ~40% wake ✓
           - Transition rates: 2.3 ± 0.4 /min — reasonable, not noisy ✓
           - Hypnograms show physiologically plausible patterns ✓

           **Milestone proposal:** brainstate-classification-validated → complete
    ```

```
Human: Approve it.
```

!!! info "Behind the scenes"
    ```
    → [updates plan/milestones.yml:
       brainstate-classification-validated → complete,
       evidence: [result-arash-20260409-003]]
    ```

---

## Day 3: Sprint review — "Where do we stand?"

```
Human: All three milestones are done. What does this unblock?
```

!!! info "Behind the scenes"
    ```
    → questio_status()
      Returns: updated milestone chain — event detection milestones now unblocked

    → questio_gap("H1")
      Returns:
        Next blockers:
          swr-detection-validated: not_started (unblocked — depends on ecephys ✓ + brainstate ✓)
          spindle-detection-validated: not_started (unblocked — depends on ieeg ✓)
          cortical-event-detection: not_started (unblocked — depends on ieeg ✓)
    ```

!!! example "Morning report"
    ```
    Agent: **Sprint review — preprocessing complete:**

           ## Milestones cleared this week

           | Milestone | Status | Subjects | Evidence |
           |-----------|--------|----------|----------|
           | ieeg-preprocessing-stable | complete ✓ | 5/5 | result-001 |
           | ecephys-preprocessing-stable | complete ✓ | 4/5 (sub-04 excluded) | result-002 |
           | brainstate-classification-validated | complete ✓ | 5/5 | result-003 |

           ## Caveats

           - sub-04 excluded from ecephys due to electrode drift (112 μm).
             This means sub-04 will have no hippocampal Neuropixels data
             for ripple detection. All other analyses (iEEG, brainstate,
             spindle detection) include sub-04.

           ## Now unblocked

           | Milestone | Flow | Can start now? |
           |-----------|------|---------------|
           | swr-detection-validated | sharpwaveripple | ✓ yes |
           | spindle-detection-validated | spectrogram_burst | ✓ yes |
           | cortical-event-detection | spectrogram_burst | ✓ yes |

           ## What this means for hypotheses

           All 7 hypotheses were blocked by preprocessing. Now:
           - H1-H7 are blocked only by event detection milestones
           - Event detection is the new critical path
           - Three detection milestones can run in parallel

           **Recommended next sprint:** event detection week
           - Day 1: spindle detection + SWR detection (parallel)
           - Day 2: cortical event detection
           - Day 3: review and validate all three
           - Day 4: start coupling analyses (first hypothesis tests)

           Want to schedule the next sprint?
    ```

```
Human: Not yet — let me review the full evidence trail first. But good
       work this week. The preprocessing backlog is clear.
```

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **questio** | `questio_status`, `questio_gap` | Sprint planning, daily status, unblocked milestone identification |
| **pipeio** | `pipeio_flow_status`, `pipeio_run`, `pipeio_run_status`, `pipeio_target_paths` | Pipeline execution and monitoring |
| **notio** | `note_create` (observations, results, decisions) | Evidence capture by background agents |
| **worklog** | `worklog_note`, `schedule_queue`, `list_queue` | Task dispatch, dependency scheduling, queue monitoring |
| **codio** | (implicit, used by background agents) | Code discovery for preprocessing functions |
| **biblio** | (implicit, used by background agents) | Literature QC thresholds for assessment |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| Day 1 AM: Planning | Orient | `questio_status` → `questio_gap` → dependency analysis → schedule |
| Day 1: Scheduling | (worklog) | `worklog_note` (parallel) + `schedule_queue` (with `after=` dependency) |
| Day 1 PM: Background | Iterate | Background agents: orient → run → assess → record → propose |
| Day 2 AM: Review | Orient | `list_queue` → read result notes → human approves/rejects |
| Day 2: Course correction | (decision) | sub-04 excluded, decision note created |
| Day 3: Sprint review | Orient | Full status check, unblocked milestone identification |

!!! danger "Course correction"
    The sub-04 failure demonstrates why daily review is essential. The background agent correctly identified the issue, investigated it, and created observation notes — but the decision to exclude a subject has scientific implications (reduced statistical power for ecephys analyses) that require human judgment. An autonomous agent might have tried to fix the drift, re-run with different parameters, or silently excluded the subject. The daily review prevents all three failure modes.

## Key insight

**Autonomous research sprints work when background agents PROPOSE and humans APPROVE.** The daily morning review is the essential human-in-the-loop checkpoint that prevents autonomous drift. Background agents do the heavy lifting (pipeline execution, QC assessment, evidence recording), but every consequential decision — milestone completion, subject exclusion, parameter changes — passes through the human.

The scheduling pattern (`schedule_queue` with `after=` dependencies) ensures that work proceeds in the right order without the human needing to manually trigger each step. The queue acts as a lightweight project management layer: the human sets the plan, the agents execute, and the morning review is where course corrections happen.

This is the scenario that demonstrates the **worklog + questio + pipeio triad**: worklog manages the schedule and task dispatch, questio tracks the scientific state and milestones, and pipeio executes the pipelines. Together, they turn a week-long preprocessing campaign into a series of "review and approve" morning sessions instead of "sit at the computer and babysit pipelines" all-day sessions.
