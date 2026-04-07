---
name: questio-session
description: "Structure a full research session: orient, plan, ground, execute, record, report"
tools: [questio_status, questio_gap, pipeio_flow_status, paper_context, codio_discover, rag_query, note_create, questio_docs_collect, note_search]
---

# Questio Session

Use this skill to structure a complete research session from orientation to
reporting. This is the outermost workflow — it composes the logic of
`questio-next`, `questio-ground`, `questio-record`, and `questio-report` into
a single guided session.

## Workflow

### Phase 1: Orient

```
questio_status()
```

Summarize the current state for the user:
- How many questions, what statuses
- Overall milestone completion
- Any blockers or recently completed work
- What changed since the last session (if detectable from recent result notes)

Present this as a brief paragraph, not a full report.

### Phase 2: Plan

Apply the `questio-next` logic:

1. Call `questio_gap()` for each `in_progress` or `not_started` question
2. Check pipeline readiness via `pipeio_flow_status()`
3. Rank by: dependency depth > pipeline readiness > evidence proximity

Present the top 2-3 recommendations and ask the user which to pursue:

```
Based on the current state, I recommend:

1. **<milestone>** — <rationale> (unblocks N downstream)
2. **<milestone>** — <rationale>
3. **<milestone>** — <rationale>

Which would you like to work on, or do you have a different priority?
```

**Wait for user approval before proceeding.**

### Phase 3: Ground

Once the user selects a milestone, apply the `questio-ground` logic:

1. Extract citations from the parent question in `questions.yml`
2. Call `paper_context()` for key papers (up to 3-5)
3. Call `codio_discover()` with milestone keywords
4. Call `rag_query()` to find prior project knowledge

Present the grounding brief:
- Expected approach and methods
- Expected results and quality criteria
- Available code to reuse
- Potential pitfalls

Ask: "Ready to proceed with this approach, or would you like to adjust?"

**Wait for user approval before proceeding.**

### Phase 4: Execute

This phase is user-driven. The agent assists with the actual work:
- Creating or updating notebooks (`pipeio_nb_create`, `pipeio_nb_exec`)
- Running pipelines (`pipeio_run`)
- Inspecting results (`pipeio_nb_read`, `pipeio_run_status`)
- Iterating on code based on results

The session skill does not prescribe what happens here — it depends on the
milestone. The agent should use the grounding brief to guide quality
assessments during execution.

### Phase 5: Record

After the user indicates work is complete (or at a natural stopping point),
apply the `questio-record` logic:

1. Identify which question(s) and milestone the work relates to
2. Create a `result` note via `note_create(note_type="result")`
3. Fill in structured frontmatter (question, milestone, metric, value,
   confidence, subjects)
4. Update `plan/milestones.yml` evidence list
5. If milestone appears complete, ask about status update
6. Call `questio_docs_collect()` to regenerate plan docs

### Phase 6: Close

Apply the `questio-report` logic scoped to this session:

1. Call `questio_status()` for updated state
2. Summarize what was accomplished:
   - Milestones advanced or completed
   - Evidence recorded
   - Confidence levels achieved
3. Note what remains for the next session
4. If any surprising results were found, flag them for human review

Present as a brief session summary:

```
## Session Summary

**Worked on:** <milestone_id> — <description>
**Result:** <key finding with metric>
**Milestone status:** <updated status>
**Next session:** <what to work on next>
```

## Hard rules

- Always wait for user approval at Phase 2 (plan) and Phase 3 (ground)
  checkpoints before proceeding.
- Do not skip grounding — even if the user says "just run it," the
  literature and code check takes seconds and prevents wasted effort.
- If the user wants to skip recording (Phase 5), remind them that
  unrecorded results are invisible to future sessions. Accept if they
  insist, but note it.
- The session does not need to complete all phases in one sitting. If the
  user stops mid-session, that's fine — summarize progress so far.
- If `plan/questions.yml` doesn't exist, orient the user to set up the
  questio data model before running a full session.
- Never auto-execute pipelines or notebooks without user awareness —
  always confirm before running compute-intensive operations.
