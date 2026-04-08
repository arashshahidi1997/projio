---
title: "Implement questio-investigate skill"
date: 2026-04-08
timestamp: 20260408-043834
status: done
actionable: true
source_note: "docs/specs/research-orchestration/loop-mechanisms.md"
project_primary: projio
tags: [task, questio, impl, skill]
---

# Implement questio-investigate skill

## Goal

Write the `questio-investigate` skill prompt that teaches the agent the investigation loop pattern.

## Context

The loop mechanisms spec at `docs/specs/research-orchestration/loop-mechanisms.md` (section 2) defines the investigate loop. This task implements it as a skill prompt.

Key design principle: the skill teaches *investigation strategy* (where to look, what order, when to escalate), NOT domain-specific judgment. The agent reasons over tool outputs to make assessment calls.

## Prompt

**Step 1: Read the specs.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md` section 2 (investigate loop)
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md` section 8.1 (action components) for the tool inventory
- Read existing skills for format reference: check `.projio/skills/` in projio or pixecog for examples

**Step 2: Determine skill location.**
- Skills live at `.projio/skills/questio-investigate.md` in the project repo (not in projio source)
- For now, create a reference/template skill at `/storage2/arash/projects/projio/docs/specs/research-orchestration/skills/questio-investigate.md`
- This will be the canonical template that projects copy to their `.projio/skills/`

**Step 3: Write the skill prompt.**

The skill should guide the agent through:

1. **Scope the issue**: What specifically is wrong? What flow/milestone/output is involved? Use `questio_status` and user description to scope.

2. **Gather context**: Before investigating outputs, ground yourself:
   - `pipeio_flow_status(flow)` — is the flow configured and healthy?
   - `pipeio_run_status(flow)` — did the last run succeed? Check exit codes and logs
   - `pipeio_log_parse(flow)` — extract errors or warnings
   - `rag_query` — search for prior decisions or known issues related to this flow

3. **Inspect outputs**: Navigate to the actual data:
   - `pipeio_target_paths(flow)` — where are outputs?
   - Read/inspect key output files (the skill should teach which file types matter for different flow kinds)
   - `pipeio_nb_read` — if there are analysis notebooks, read their outputs

4. **Compare against expectations**:
   - `paper_context` with relevant citations from questions.yml — what does literature say?
   - Check prior result notes for this milestone — what did previous runs produce?
   - `codio_discover` — are there known issues or conventions for this analysis type?

5. **Narrow the cause**: Based on evidence, form hypotheses about what's wrong. Test each:
   - If it's a parameter issue → suggest iterate loop
   - If it's a code bug → identify the file and line
   - If it's a data issue → identify which subjects/files are affected
   - If it's ambiguous → present alternatives to the human

6. **Record and report**:
   - Create observation notes (`note_create`, kind=idea, tags=[observation, investigate]) for each significant finding
   - Summarize: what was investigated, what was found, proposed action
   - If cause is clear: propose a fix (code change, parameter adjustment, rerun)
   - If cause is unclear: escalate with the evidence gathered, not just "I don't know"

7. **Failure escalation**: If after 3 investigation cycles the cause isn't narrowing, escalate to human with:
   - What was checked
   - What was ruled out
   - Remaining hypotheses
   - Recommended next steps

**Step 4: Commit** with message: "Add questio-investigate skill template"

## Acceptance Criteria

- [ ] Skill prompt exists at `docs/specs/research-orchestration/skills/questio-investigate.md`
- [ ] Covers all 7 investigation steps
- [ ] References concrete MCP tool names
- [ ] Includes failure escalation criteria
- [ ] Does NOT encode domain-specific judgment — teaches strategy only
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `d63b4b31684a`
- session: `be6951d6-6bf8-4098-b8ae-20e0a01542ea`
- batch duration: 527.5s
