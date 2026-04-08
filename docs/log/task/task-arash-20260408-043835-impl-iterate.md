---
title: "Implement questio-iterate skill"
date: 2026-04-08
timestamp: 20260408-043835
status: done
actionable: true
source_note: "docs/specs/research-orchestration/loop-mechanisms.md"
project_primary: projio
tags: [task, questio, impl, skill]
---

# Implement questio-iterate skill

## Goal

Write the `questio-iterate` skill prompt that teaches the agent the iteration loop pattern — implement, run, evaluate, adjust based on human feedback.

## Context

The loop mechanisms spec at `docs/specs/research-orchestration/loop-mechanisms.md` (section 3) defines the iterate loop. This replaces the rejected standalone `questio-dispatch` — iteration is always within a human feedback loop, not fire-and-forget.

Key difference from investigate: investigate is reactive (something went wrong), iterate is proactive (improving toward a goal).

## Prompt

**Step 1: Read the specs.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md` section 3 (iterate loop)
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md` sections 8.2-8.3 (inner loop, sequences)
- Read existing skills for format reference

**Step 2: Write the skill prompt** at `/storage2/arash/projects/projio/docs/specs/research-orchestration/skills/questio-iterate.md`.

The skill should guide the agent through:

1. **Establish the goal**: What are we trying to achieve? Link to questio milestone and flow:
   - `questio_gap(question_id)` — what milestone are we working toward?
   - What does "success" look like? (from grounding: literature values, prior results, human-stated criteria)

2. **Ground before first iteration**:
   - `paper_context` — expected methods, values, pitfalls
   - `codio_discover` — existing implementations
   - `rag_query` — prior attempts at this analysis
   - Synthesize: approach, expected results, quality criteria

3. **Pre-flight check**:
   - `pipeio_flow_status(flow)` — is the flow ready?
   - For expensive runs: present what will execute (targets, estimated scope) and get human confirmation
   - For cheap runs (single notebook, single subject): proceed with note

4. **Execute**:
   - `pipeio_run(targets)` or `pipeio_nb_exec(notebook)` depending on scope
   - Monitor: `pipeio_run_status` for pipeline runs
   - On failure: enter investigate loop (reference questio-investigate skill)

5. **Evaluate**:
   - Read outputs: `pipeio_target_paths` → inspect files, `pipeio_nb_read` for notebook results
   - Compare against grounded expectations
   - Create observation note: what was run, what was produced, assessment
   - Present results to human with: key metrics, comparison to expectations, recommendation

6. **Human feedback gate**:
   - Wait for human response before next cycle
   - Possible feedback: "looks good" → record evidence, "adjust X" → modify and re-iterate, "investigate Y" → switch to investigate loop, "stop" → record current state and exit
   - The agent does NOT autonomously decide to iterate again — the human directs

7. **Record**:
   - Each iteration: observation note (lightweight, tags=[observation, iterate])
   - On success: result note via questio-record with full evidence schema
   - On exit (human says stop): observation note summarizing what was tried and current state
   - Propose milestone status update (propose-review-confirm, not auto-update)

8. **Convergence tracking**:
   - After 3+ iterations, the agent should summarize the trajectory: "iteration 1 gave X, iteration 2 gave Y, iteration 3 gave Z — the trend is [improving/plateauing/degrading]"
   - If plateauing or degrading after 3 iterations: suggest changing approach rather than continuing to tune

**Step 3: Commit** with message: "Add questio-iterate skill template"

## Acceptance Criteria

- [ ] Skill prompt at `docs/specs/research-orchestration/skills/questio-iterate.md`
- [ ] Human feedback gate is explicit — no autonomous re-iteration
- [ ] Dry-run/confirmation for expensive runs
- [ ] References questio-investigate for failure cases
- [ ] Convergence tracking after 3+ iterations
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `d63b4b31684a`
- session: `be6951d6-6bf8-4098-b8ae-20e0a01542ea`
- batch duration: 527.5s
