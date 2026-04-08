# Loop Mechanisms — Investigate, Iterate, Orient

**Status:** draft
**Date:** 2026-04-08
**Extends:** [design.md](design.md) section 8 (Operational workflows)
**Origin:** idea-arash-20260408-035007-479946 (questio-dispatch), idea-arash-20260408-035035-245990 (auto-QC)

This spec defines three concrete loop mechanisms that operate within the inner/middle/outer loop framework established in `design.md` section 8. The existing loop framing (inner = notebook development, middle = milestone completion, outer = research cycle) remains valid — investigate, iterate, and orient are *patterns* that occur within those loops.

---

## 1. Design philosophy

### Agent-as-judge

The agent IS the validation and assessment layer. There are no pre-scripted validation notebooks that produce pass/fail verdicts. Instead, the agent reads pipeline outputs, compares against literature-grounded expectations, and makes a judgment call about quality and sufficiency.

This reverses the assumption in the original auto-QC idea (idea-arash-20260408-035035-245990), which proposed per-flow validation notebooks with structured QC schemas. The infrastructure for that pattern exists (pipeio_nb_exec, pipeio_nb_read), but the *judgment* is the agent's job, not a notebook's. Notebooks may be created during a loop as analytical tools, but they are agent-authored artifacts, not pre-scripted templates.

**Why this matters:** pre-scripted validation encodes domain knowledge in notebooks that become stale, rigid, and disconnected from evolving expectations. Agent-as-judge means the validation logic adapts to context — the agent consults current literature, compares against prior results, and applies project-specific criteria that evolve as understanding deepens.

### Skills encode investigation strategy, not judgment

Skill prompts teach the agent *where to look*, *what order to follow*, and *when to escalate*. They do not encode domain-specific logic like "SWR detection rate should be 10-15/min" — that comes from grounding (literature, prior results, human-set criteria). The skill is the investigation playbook; the domain knowledge comes from projio's knowledge layers.

### Lightweight mid-loop recording

Observations are captured *during* iteration, not just at the end. This prevents information loss when loops are long or interrupted, and builds an audit trail of the agent's reasoning. Observations use notio's existing `idea` note type with `tags: [observation]` — no new note types needed.

### Human-in-the-loop by default

Milestone status changes require human confirmation. The agent proposes, the human reviews and confirms. Full autonomy for milestone updates is a dial to turn later, not the default. This propose-review-confirm pattern applies to all consequential state changes.

---

## 2. Investigate loop

**Pattern:** human spots an issue or anomaly → agent digs in using projio tools → narrows cause → proposes explanation or fix → iterates if needed.

### 2.1 Entry conditions

- **Human-triggered:** user flags an issue ("these spectrograms look wrong", "sub-03 has no output", "detection rate is too low")
- **Gap-surfaced:** `questio_gap` reveals a blocker that needs diagnosis before work can proceed
- **Unexpected output:** pipeline completes but results are outside expected range (detected during iterate loop assessment)
- **Pipeline failure:** `pipeio_run` or `pipeio_nb_exec` fails with non-trivial errors

### 2.2 Tool composition

The investigate loop uses tools in a diagnostic sequence, narrowing from broad context to specific cause:

| Phase | Tools | Purpose |
|-------|-------|---------|
| **Locate** | `pipeio_target_paths(flow)`, `pipeio_flow_status(flow)` | Find where outputs should be, check flow state |
| **Inspect** | `pipeio_nb_read(flow, name)`, file reading, `pipeio_log_parse(flow)` | Read actual outputs, check logs for errors |
| **Compare** | `paper_context(citekey)`, `rag_query(query)` | Compare against expected values from literature and prior results |
| **Contextualize** | `questio_status()`, `note_search(query)` | Check if this issue was seen before, find related observations |
| **Diagnose** | `pipeio_mod_context(flow, mod)`, `codio_get(name)` | Read the code that produced the output, understand the logic |
| **Record** | `note_create(note_type="idea")` with `tags: [observation, investigate]` | Capture findings mid-loop |

### 2.3 Investigation strategy

The skill prompt teaches a general diagnostic pattern, not domain-specific logic:

1. **Reproduce:** confirm the issue exists by reading the relevant outputs. Don't trust secondhand descriptions — verify.
2. **Scope:** is this one subject, all subjects, one metric, all metrics? Narrowing scope is the first diagnostic step.
3. **Compare:** check against literature expectations (from grounding) and prior results in the project. Is this genuinely anomalous, or expected variation?
4. **Trace upstream:** if outputs are wrong, check inputs. Use `pipeio_target_paths` to find upstream outputs and inspect them.
5. **Check code:** read the relevant script or notebook via `pipeio_mod_context` or `pipeio_nb_read`. Look for parameter mismatches, edge cases, or bugs.
6. **Search prior knowledge:** use `rag_query` and `note_search` to check if this issue was encountered before. Prior observations may contain the diagnosis.
7. **Form hypothesis:** based on evidence gathered, propose a cause. If multiple causes are plausible, list them ranked by likelihood.
8. **Propose action:** recommend a fix, a parameter change, or further investigation. If the cause is clear, propose the specific change. If not, propose a targeted experiment to discriminate between hypotheses.

### 2.4 Recording

Mid-loop observations use lightweight notes:

```yaml
---
title: "Observation: sub-03 missing TTL events in first 100s"
tags: [observation, investigate]
series: preprocess_ieeg
---

Inspected pipeio_target_paths for sub-03. Output file exists but TTL events
are absent in the first 100 seconds. Upstream raw data shows TTL markers are
present. Suspect the filter cutoff is too aggressive for this subject's
signal characteristics.

Next: check filter parameters in ttl_removal mod config.
```

Observations accumulate during the loop and are referenced when creating a final result note or when escalating to the human.

### 2.5 Exit conditions

- **Cause identified, fix proposed:** the agent has a clear diagnosis and a concrete recommendation. Present to the human with evidence.
- **Cause identified, fix applied:** for low-risk fixes (parameter adjustment, re-run), the agent may fix and re-run within the iterate loop. Human confirmation required for code changes.
- **Escalation:** the investigation hits a dead end or the cause requires scientific judgment. The agent creates a summary observation note with all evidence gathered and presents findings to the human.

### 2.6 Failure modes

| Situation | Agent action |
|-----------|-------------|
| Investigation hits a dead end | Escalate with summary: "I checked X, Y, Z. None explain the issue. Here's what I know." |
| Outputs are ambiguous (could be correct or wrong) | Present alternatives: "This could be normal variation (literature says X) or a real issue (because Y). Your call." |
| Issue is environment/infrastructure, not science | Flag differently: "This is a compute/storage issue, not a scientific one. The job timed out / disk is full / dependency is missing." |
| Issue spans multiple flows | Trace to the root flow, investigate there first. Create observation notes linking the downstream effects. |
| Human provides additional context mid-investigation | Incorporate and adjust. Don't restart — continue from current position with new information. |

---

## 3. Iterate loop

**Pattern:** human has an idea about parameters or approach → agent implements → runs → evaluates → human gives feedback → agent adjusts.

This replaces the standalone `questio-dispatch` concept (idea-arash-20260408-035007-479946). Dispatch is not a separate skill — it's one step within the iterate loop. The iterate loop adds the crucial evaluate-and-feedback cycle that dispatch lacked.

### 3.1 Entry conditions

- **Human-directed:** user proposes a change ("try threshold=3.0 instead of 3.5", "add a bandpass filter before detection", "run this for neuropixels too")
- **Questio-next suggested:** `questio-next` identifies a pipeline ready to run or a parameter to tune
- **Agent-identified:** during assessment, the agent identifies a parameter that could improve results
- **Post-investigation:** an investigate loop identified the cause, and now the fix needs to be applied and tested

### 3.2 Cycle structure

Each iteration follows a fixed cycle:

```
modify → execute → assess → report → [receive feedback] → next cycle
```

**Modify:** change configuration, notebook code, script parameters, or pipeline settings. Use `pipeio_config_patch`, direct file edits, or `pipeio_nb_sync` as appropriate.

**Execute:** run the analysis. Use `pipeio_run(flow)` for full pipeline runs or `pipeio_nb_exec(flow, name)` for notebook-based analysis. For expensive runs, a dry-run or single-subject test precedes the full execution.

**Assess:** read outputs using `pipeio_target_paths` + file inspection, `pipeio_nb_read`, `pipeio_run_status`, `pipeio_log_parse`. Compare against expectations from grounding. The agent makes a judgment call — this is the agent-as-judge principle in action.

**Report:** present findings to the human. Include: what was changed, what the results look like, how they compare to expectations, and the agent's assessment (satisfactory / needs adjustment / unexpected).

**Receive feedback:** the human directs the next cycle: continue iterating, change approach, accept results, or stop.

### 3.3 Convergence criteria

The iterate loop converges when any of:

- **Human says stop:** the human accepts the results or redirects to different work
- **Metrics stabilize:** successive iterations produce negligibly different results (agent detects this and reports)
- **Quality criteria met:** results meet the expectations established during grounding (literature values, statistical thresholds, cross-subject consistency)
- **Resource limit:** after N iterations (configurable, default 5), the agent escalates: "I've iterated N times. Here's the trajectory. Should I continue or try a different approach?"

### 3.4 Parameter tracking

Each iteration cycle produces a lightweight observation note:

```yaml
---
title: "Iteration 3: threshold=3.0, detection_rate=14.2/min"
tags: [observation, iterate]
series: sharpwaveripple
---

**Changed:** detection threshold from 3.5 SD to 3.0 SD
**Result:** detection rate increased from 10.1/min to 14.2/min (literature: 10-15/min)
**Assessment:** within expected range. Cross-subject consistency improved (SD: 2.1 → 1.8).
**Recommendation:** accept this threshold. Ready to validate across remaining subjects.
```

These notes provide a parameter sweep audit trail. When the iterate loop converges, the final result note references the iteration observations.

### 3.5 Dry-run and confirmation

For expensive pipeline runs (full dataset, multi-subject, long compute):

1. **Preview:** agent describes what will be executed, estimated scope (N subjects, approximate duration if known)
2. **Confirm:** human approves before `pipeio_run` is called
3. **Monitor:** agent checks `pipeio_run_status` and reports progress at natural checkpoints

Single-subject test runs or notebook executions do not require confirmation unless the human has requested it.

### 3.6 Failure modes

| Situation | Agent action |
|-----------|-------------|
| Pipeline fails | Check `pipeio_log_parse(flow)`. If the error is clear, fix and re-run. If not, enter investigate loop. |
| Results degrade (worse than previous iteration) | Report the regression. Propose reverting the change. Do not silently iterate further. |
| Human redirects mid-loop | Capture current state in an observation note (what was tried, where things stand). Pivot to the new direction. |
| Iteration produces surprising results | Do not silently continue. Flag the surprise, provide literature context, and let the human decide whether to pursue or investigate. |
| Environment or resource failure | Flag as infrastructure issue (see investigate loop failure modes). Do not retry indefinitely — max 2 retries for transient failures. |

---

## 4. Orient loop

**Pattern:** agent surveys project state → surfaces what needs attention → feeds into investigate or iterate.

Orient is the entry point for the other two loops. It answers "what should I be doing?" by combining questio status with pipeline state.

### 4.1 Trigger

- **Session start:** whenever a research session begins (manually via `questio-session` or scheduled via worklog)
- **Scheduled agent run:** periodic orientation as part of automated monitoring
- **Human asks:** "what's next?", "what needs attention?", "where are we?"

### 4.2 Tool composition

```
questio_status()          → research state: questions, milestones, evidence
    ↓
questio_gap(question_id)  → per-question: unmet milestones, blockers, confidence gaps
    ↓
pipeio_flow_status(flow)  → per-flow: is the pipeline configured, ready, or broken?
```

For each actionable milestone returned by `questio_gap`, the agent checks whether the linked flow is ready via `pipeio_flow_status`. This requires the milestone→flow structured link (see section 4.4).

### 4.3 Output

Orient produces a prioritized list of actionable items, each tagged with a recommended loop type:

```
## Orientation Summary

### Ready to iterate
1. **ttl-removal-validated** (flow: preprocess_ieeg) — pipeline configured,
   dry-run passes. Run for remaining subjects.
2. **swr-detection-validated** (flow: sharpwaveripple) — notebook exists,
   needs parameter tuning.

### Needs investigation
3. **preprocessing-stable** — ecephys pipeline has errors in last run.
   Check pipeio_log_parse for details.

### Blocked
4. **delta-ripple-coupling** — blocked by swr-detection-validated
   and delta-event-detection (both incomplete).
```

Items tagged "iterate" feed directly into the iterate loop. Items tagged "investigate" feed into the investigate loop. Blocked items are reported but not actionable until dependencies resolve.

### 4.4 The milestone→flow structured link

Orient depends on resolving from questio milestones to pipeio flows. This is the critical infrastructure piece that connects research planning to pipeline execution.

**Current state:** milestones have a `pipelines` field (list of flow names as strings). This works but is ambiguous when a milestone spans multiple flows — which flow should the agent check first?

**Required change:** milestones should have a `flow` field — the *primary* pipeio flow for this milestone. This enables direct resolution: `questio_gap` returns the `flow` field → agent calls `pipeio_flow_status(flow)` → no NLU, no guessing.

```yaml
ttl-removal-validated:
  description: "TTL artifact removal validated for iEEG and neuropixels"
  flow: preprocess_ieeg           # primary flow (structured link)
  pipelines: [preprocess_ieeg]    # retained for milestones spanning multiple flows
  depends_on: []
  status: in_progress
  evidence: []
```

- `flow` is the primary link used by orient and dispatch logic
- `pipelines` is retained for milestones that genuinely span multiple flows (e.g., `preprocessing-stable` needs both `preprocess_ieeg` and `preprocess_ecephys`)
- When `flow` is set, the agent resolves directly without NLU
- When `flow` is absent but `pipelines` has exactly one entry, treat that as the flow
- `questio_gap` should return the `flow` field in its structured output

### 4.5 Connection to other loops

```
                orient
               /      \
         investigate    iterate
              ↑    ↘   ↗    ↓
              └── (findings feed back) ──┘
                        ↓
                     record
```

- Orient produces entry conditions for investigate and iterate
- Investigate may conclude with a fix that enters the iterate loop
- Iterate may surface anomalies that enter the investigate loop
- Both loops produce observations and results that feed back into orient (via updated questio state)

---

## 5. Cross-cutting concerns

### 5.1 Failure mode taxonomy

All three loops share a common failure vocabulary. When something goes wrong, the agent classifies the failure and acts accordingly:

| Mode | Meaning | Agent action | Escalation |
|------|---------|-------------|------------|
| `retry` | Transient failure (timeout, resource contention, network) | Re-run with same parameters, max 2 attempts | → `investigate` after 2 failures |
| `investigate` | Unexpected output (wrong values, empty files, partial results) | Enter investigate loop, gather evidence | → `escalate` if cause not found |
| `escalate` | Needs human judgment (ambiguous results, scientific interpretation) | Create observation note, present findings, ask human | Terminal — human decides |
| `skip` | Blocked by external dependency (missing data, upstream incomplete) | Record blocker, move to next unblocked item | Re-check when dependency resolves |
| `abort` | Unrecoverable (corrupted data, infrastructure failure) | Stop loop, create detailed observation note, alert human | Terminal — requires human intervention |

Each mode has a max-iterations or timeout before escalating to the next level: `retry` → `investigate` → `escalate`. This prevents infinite loops and ensures humans are informed when automation cannot resolve an issue.

### 5.2 Recording granularity

Three levels of recording serve different purposes:

| Record type | Note type | When created | Purpose |
|-------------|-----------|-------------|---------|
| **Observation** | `idea` with `tags: [observation]` | During any loop iteration | Capture mid-loop findings, parameter changes, intermediate results |
| **Result** | `result` | At loop convergence | Structured evidence for milestone completion |
| **Decision** | `idea` with `tags: [decision]` | When human redirects or makes a judgment call | Audit trail of human direction changes |

Observations are *inputs to* result notes, not evidence themselves. They do not appear in milestone `evidence` lists. They are referenced in result note bodies as context for how the conclusion was reached.

### 5.3 Propose-review-confirm pattern

For all consequential state changes, the agent follows propose-review-confirm:

1. **Propose:** agent states what it wants to change and why ("Milestone `swr-detection-validated` appears to have sufficient evidence: 5/5 subjects validated, metrics within literature range. I recommend updating status to `complete`.")
2. **Review:** human examines the proposal, possibly asking for more detail or checking the evidence
3. **Confirm:** human approves or rejects. Agent acts only after confirmation.

This pattern applies to:
- Milestone status changes (especially → `complete`)
- Evidence sufficiency judgments
- Pipeline re-runs after parameter changes
- Code modifications to scripts or configurations

It does NOT apply to:
- Creating observation notes (lightweight, always allowed)
- Reading outputs and inspecting state (read-only, always allowed)
- Creating result notes (capturing evidence is always safe; the milestone update is what needs confirmation)

### 5.4 Relationship to design.md section 8

This spec extends section 8 of `design.md`. The relationship:

| design.md concept | This spec | Relationship |
|-------------------|-----------|-------------|
| Inner loop (notebook development) | Iterate loop | Iterate generalizes the inner loop beyond notebooks — any modify→execute→assess cycle |
| Middle loop (milestone completion) | Orient + iterate | Orient picks the milestone; iterate works on it |
| Outer loop (research cycle) | Orient | Orient is the entry point that drives the outer loop |
| Sequence B (validation sweep) | Investigate + agent-as-judge | Agent inspects outputs directly rather than running pre-scripted validation notebooks |
| Sequence C (pipeline-to-evidence) | Iterate → record | The iterate loop subsumes pipeline-to-evidence as the execute→assess→record cycle |
| Section 8.4 (human checkpoints) | Propose-review-confirm | Formalized as a named pattern with explicit scope |
| Section 8.5 (automation levels) | Section 1 philosophy | Agent-as-judge reframes what "automation" means — it's agent judgment quality, not notebook scripting |

The inner/middle/outer loop framing remains valid as a timescale model. Investigate, iterate, and orient are *behavioral patterns* that occur within those timescale loops.

---

## 6. Skill mapping

### 6.1 New skills

| Skill | Loop | Description |
|-------|------|-------------|
| `questio-investigate` | Investigate | Investigation loop skill prompt. Teaches the diagnostic strategy (section 2.3). Entry: human flags an issue or agent detects anomaly. |
| `questio-iterate` | Iterate | Iteration loop skill prompt. Teaches the modify→execute→assess→report cycle (section 3.2). Replaces the rejected standalone `questio-dispatch` — dispatch is one step within iterate, not a separate skill. |

### 6.2 Existing skills with orient folded in

Orient does not need a standalone skill. Its logic is already distributed across:

- `questio-session` — Phase 1 (Orient) and Phase 2 (Plan) implement the orient loop
- `questio-next` — the ranking and recommendation logic IS orient's output

The orient pattern (section 4) codifies what these skills already do and adds the milestone→flow resolution as a concrete mechanism.

### 6.3 Updates to existing skills

| Skill | Update needed |
|-------|---------------|
| `questio-record` | Add support for mid-loop use: creating observation notes (not just result notes). Add guidance for referencing prior observations when creating the final result note. |
| `questio-ground` | Extend to feed investigation context, not just pre-work context. Add a "diagnostic grounding" mode: when entering investigate, ground on what the expected output should look like so the agent can compare against actual. |
| `questio-session` | Phase 4 (Execute) should reference the iterate loop pattern. The session skill should recognize when investigation is needed (unexpected results) and switch to investigate mode. |
| `questio-next` | Should return the `flow` field from milestones in its recommendations, enabling direct dispatch without NLU. |

### 6.4 Skills NOT created (and why)

| Rejected skill | Reason |
|----------------|--------|
| `questio-dispatch` | Subsumed by iterate loop. Dispatch is execute-without-evaluate — the iterate loop adds the essential evaluate-and-feedback cycle. |
| `questio-validate` | Subsumed by agent-as-judge philosophy. Validation is not a separate action — it's the assess step within the iterate loop. The agent reads outputs and judges, rather than running a pre-scripted validation notebook. |
| `questio-orient` (standalone) | Already covered by questio-session Phase 1 and questio-next. No need for a third skill that duplicates this logic. |
