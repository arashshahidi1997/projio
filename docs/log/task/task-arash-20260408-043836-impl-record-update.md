---
title: "Update questio-record for mid-loop observation capture"
date: 2026-04-08
timestamp: 20260408-043836
status: done
actionable: true
source_note: "docs/specs/research-orchestration/loop-mechanisms.md"
project_primary: projio
tags: [task, questio, impl, skill]
---

# Update questio-record for mid-loop observation capture

## Goal

Extend questio-record to support lightweight mid-loop observation notes in addition to full result notes. Update the skill prompt and verify note_create supports the observation pattern.

## Context

The loop mechanisms spec defines two recording granularities:
- **Result notes**: formal evidence for milestones (existing questio-record)
- **Observation notes**: lightweight mid-loop findings during investigate/iterate (new)

Observation notes use existing notio infrastructure (kind=idea, tags=[observation]) — no new note type needed. But questio-record's skill prompt needs to distinguish between "record a result" and "capture an observation" and guide the agent to use the right one.

## Prompt

**Step 1: Read the specs.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/loop-mechanisms.md` section 5 (cross-cutting, recording granularity)
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/design.md` section 5.3 (result note schema)
- Read the existing questio-record skill if it exists, or the skill description in design.md section 6.2
- Read notio note_create tool signature to understand what fields are available

**Step 2: Write or update the questio-record skill prompt.**

Location: `/storage2/arash/projects/projio/docs/specs/research-orchestration/skills/questio-record.md`

The skill should handle two modes:

**Mode A: Result note (milestone evidence)**
- Full structured frontmatter: question, milestone, metric, value, confidence, subjects, figure
- Created when the agent has a definitive finding to record
- Goes in `docs/log/result/` directory
- Gets added to milestone evidence list (propose to human first)
- Follows the schema in design.md section 5.3

**Mode B: Observation note (mid-loop capture)**
- Lightweight: kind=idea, tags=[observation, <loop-type>], series=<flow-name>
- Created during investigate/iterate loops to capture intermediate findings
- Goes in `docs/log/idea/` (standard notio location)
- NOT added to milestone evidence — observations inform result notes, they aren't evidence themselves
- Template: what was checked, what was found, what it means, next step

The skill should guide the agent to choose the right mode:
- "I found something definitive that advances a milestone" → result note
- "I found something interesting during investigation" → observation note
- "I want to record what I tried and what happened" → observation note
- "The iteration produced results meeting quality criteria" → result note

**Step 3: Verify note_create supports observation pattern.**
- Check that `note_create` (or `mcp__projio__note_create`) accepts kind=idea and arbitrary tags
- If tags=[observation] needs special handling, document it

**Step 4: Commit** with message: "Add questio-record skill with observation and result note modes"

## Acceptance Criteria

- [ ] Skill prompt at `docs/specs/research-orchestration/skills/questio-record.md`
- [ ] Two modes documented: result note and observation note
- [ ] Clear decision criteria for which mode to use
- [ ] Observation notes explicitly excluded from milestone evidence
- [ ] Compatible with existing notio note_create
- [ ] Committed


## Batch Result

- status: done
- batch queue_id: `d63b4b31684a`
- session: `be6951d6-6bf8-4098-b8ae-20e0a01542ea`
- batch duration: 527.5s
