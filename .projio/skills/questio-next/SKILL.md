---
name: questio-next
description: "Recommend highest-impact research work based on questio status and evidence gaps"
tools: [questio_status, questio_gap, pipeio_flow_status]
---

# Questio Next

Use this skill when the user asks "what should I work on next?" or when starting
a research session and needing to pick the highest-impact unblocked work.

## Workflow

### 1) Get current research state

```
questio_status()
```

Note the status of each question: `not_started`, `in_progress`, `blocked`,
`sufficient`. Focus on questions that are `in_progress` or `not_started`.

### 2) Identify evidence gaps per question

For each `in_progress` or `not_started` question:

```
questio_gap(question_id="<id>")
```

Collect:
- Unmet milestones (not `complete`)
- Dependency blockers (milestones that block others)
- Missing pipeline runs
- Confidence gaps (milestones with `preliminary` evidence but not `validated`)

### 3) Check pipeline readiness

For each flow referenced by unmet milestones:

```
pipeio_flow_status(flow="<flow_name>")
```

Determine which pipelines are ready to run, which need development, and which
are blocked on upstream flows.

### 4) Rank by impact

Score candidate work items by considering (in order of priority):

1. **Dependency depth** — milestones that unblock the most downstream
   milestones and questions rank highest. A preprocessing milestone that
   blocks 5 hypotheses outranks a leaf milestone that serves one.
2. **Pipeline readiness** — work where the pipeline is already built or
   nearly complete is cheaper to execute. Prefer finishing near-complete
   pipelines over starting new ones.
3. **Evidence proximity** — questions that already have substantial evidence
   (closer to sufficiency) may be worth completing before starting fresh
   questions. Finishing H2 at 80% is often better than starting H5 at 0%.
4. **Blocked vs unblocked** — only recommend work that is currently
   unblocked (all dependency milestones are complete).

### 5) Output recommendation

Present a ranked list (top 3) with:

```
## Recommended: <milestone description>

**Question:** <question_id> — <question text>
**Milestone:** <milestone_id>
**Why this ranks highest:**
- Unblocks: <N milestones, M questions>
- Pipeline: <flow_name> — <status>
- Current evidence: <N/M milestones complete for this question>

**Action:** <concrete next step — e.g., "run preprocess_ieeg for remaining
subjects" or "create validation notebook for SWR detection">
```

If all work is blocked, explain what is blocking progress and suggest
alternative actions (e.g., resolving a preprocessing issue, seeking external
data, or reviewing literature for alternative approaches).

## Hard rules

- Never recommend work that has unresolved dependency blockers without
  flagging them explicitly.
- Always check pipeline readiness before recommending execution work.
- If the project has no `plan/questions.yml`, tell the user to set up the
  questio data model first.
- Do not recommend manuscript writing unless explicitly asked — use the
  `questio-ready` workflow for that.
