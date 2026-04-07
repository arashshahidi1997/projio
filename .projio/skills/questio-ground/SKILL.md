---
name: questio-ground
description: "Gather literature, code, and project context before starting work on a milestone or question"
tools: [paper_context, codio_discover, rag_query, questio_status, questio_gap]
---

# Questio Ground

Use this skill before starting work on a specific milestone or question.
Grounding ensures the agent works from literature-backed expectations, reuses
existing code, and avoids repeating prior failed attempts.

## Inputs

- `TARGET` (required): a milestone ID (e.g., `swr-detection-validated`) or
  question ID (e.g., `H3`). If a question ID is given, ground the
  highest-priority unmet milestone for that question.

## Workflow

### 1) Resolve target

If `TARGET` is a question ID:
```
questio_gap(question_id="<TARGET>")
```
Pick the deepest unblocked milestone from the gap analysis.

If `TARGET` is a milestone ID, use it directly.

Call `questio_status()` to get the question context and locate the milestone's
parent question, associated pipelines, and any citations listed in
`questions.yml`.

### 2) Literature context

Extract relevant citekeys from the question's `citations` field in
`questions.yml`. For each key citation (up to 3-5 most relevant):

```
paper_context(citekey="<key>")
```

Extract:
- **Expected methods** — what techniques did the literature use?
- **Expected values** — what quantitative results should we expect?
  (e.g., "ripple rate 10-15/min during NREM", "spindle density 2-4/min")
- **Potential pitfalls** — what did authors warn about or what failed in
  their hands?
- **Quality criteria** — what thresholds or validation approaches are standard?

### 3) Code discovery

Extract keywords from the milestone description and search for existing
implementations:

```
codio_discover(query="<keywords from milestone>")
```

If results are found, inspect the most relevant:
```
codio_get(name="<library>")
```

Note:
- Reusable functions that can be called directly
- Patterns that can be adapted
- Utilities in `code/utils/` that handle I/O or common operations

### 4) Project knowledge search

Search for prior attempts, decisions, or observations related to this
milestone:

```
rag_query(query="<milestone description keywords>", corpus="docs")
```

Look for:
- Prior notebook attempts (successful or failed)
- Design decisions or constraints documented in notes
- Related result notes from adjacent milestones

### 5) Synthesize grounding brief

Output a structured brief:

```
## Grounding Brief: <milestone description>

**Question:** <question_id> — <question text>
**Milestone:** <milestone_id>
**Pipeline:** <flow_name>

### Expected Approach
Based on <citekey1>, <citekey2>:
- <recommended method/algorithm>
- <key parameters or settings>

### Expected Results
- <metric>: <expected range> (from <citekey>)
- <metric>: <expected range>

### Quality Criteria
- <criterion> (e.g., "detection rate within 1 SD of literature mean")
- <criterion> (e.g., "consistent across >= 80% of subjects")

### Available Code
- <library.function> — <what it does, how to use it>
- <utility> — <relevance>

### Prior Work in This Project
- <note/notebook reference> — <what was found>

### Potential Pitfalls
- <pitfall from literature>
- <pitfall from prior project attempts>

### Recommended Action
<concrete first step, e.g., "Create validation notebook using cogpy.detection.swr,
parameterize with threshold=3.5 SD, validate against sub-01 first">
```

## Hard rules

- Always check literature before recommending an approach — don't guess at
  expected values.
- If no relevant papers are cited in `questions.yml`, say so explicitly and
  suggest the user add citations before proceeding.
- If `codio_discover` finds an existing implementation, recommend reusing it
  rather than reimplementing. Only suggest new code if the existing solution
  is clearly inadequate.
- Never skip the project knowledge search — prior failed attempts are
  critical context.
- If the milestone is blocked by dependencies, report that instead of
  producing a grounding brief.
