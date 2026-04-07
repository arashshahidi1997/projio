---
name: questio-record
description: "Guided result capture: create evidence note, update milestone, regenerate docs"
tools: [questio_status, note_create, questio_docs_collect]
---

# Questio Record

Use this skill after completing analysis work to capture the result as
structured evidence linked to the research plan. This skill creates a `result`
note, updates the milestone's evidence list, and regenerates plan docs.

## Workflow

### 1) Identify the result target

Ask the user (or infer from context):
- Which **question(s)** does this result relate to? (e.g., `H2`, `H3`)
- Which **milestone** does this evidence support? (e.g., `swr-detection-validated`)
- What is the key **metric** and its **value**? (e.g., `detection_rate: 12.3 ± 2.1/min`)
- What **confidence** level? (`preliminary`, `validated`, `final`)
- Which **subjects** were included? (e.g., `[sub-01, sub-02, sub-03]`)

### 2) Validate IDs exist

```
questio_status()
```

Verify that:
- The question ID(s) exist in `plan/questions.yml`
- The milestone ID exists in `plan/milestones.yml`

If an ID doesn't exist, tell the user and ask for correction. Do not create
result notes with invalid references.

### 3) Create the result note

```
note_create(note_type="result")
```

This creates a note file from the `result` template at `docs/log/result/`.
Edit the generated file to fill in the structured frontmatter:

```yaml
---
title: "<descriptive title>"
owner: "<user>"
series: "<question_id>"
question: "<question_id>"
milestone: "<milestone_id>"
subjects: [<subject list>]
metric: "<metric_name>"
value: "<metric_value>"
figure: "<path to figure if any>"
confidence: "<preliminary|validated|final>"
tags: [result, <question_id>, <milestone_id>]
---
```

Fill the note body with:
- **Context:** what was tested and why
- **Method:** brief description of the analysis approach
- **Result:** the key finding with quantitative details
- **Interpretation:** what this means for the question/milestone
- **Limitations:** caveats, edge cases, or subjects that failed

### 4) Update milestone evidence

Read `plan/milestones.yml` and add the result note's path or ID to the
milestone's `evidence` list. For example:

```yaml
swr-detection-validated:
  status: in_progress
  evidence:
    - result-arash-20260415-143022-123456  # existing
    - result-arash-20260416-091530-789012  # newly added
```

### 5) Assess milestone completion

After adding evidence, evaluate whether the milestone now has sufficient
evidence to be considered complete:

- Are all required subjects included?
- Is the confidence level `validated` or `final`?
- Do the metrics meet the quality criteria (from grounding brief or literature)?

If sufficient:
- Ask the user: "Milestone `<id>` now appears to have sufficient evidence.
  Should I update its status to `complete`?"
- If approved, update `status: complete` in `plan/milestones.yml`
- Check if this completion unblocks any downstream milestones

If not yet sufficient:
- Report what's still missing (e.g., "3/5 subjects validated, need remaining 2")

### 6) Regenerate plan docs

```
questio_docs_collect()
```

This updates `docs/plan/` pages to reflect the new evidence and any status
changes.

## Hard rules

- Never create a result note with a question or milestone ID that doesn't
  exist in the YAML files.
- Always ask for confirmation before changing a milestone status to `complete`.
- The result note must have a quantitative metric and value — qualitative-only
  results should use `confidence: preliminary`.
- Never modify `plan/questions.yml` — only `plan/milestones.yml` is updated
  by this skill (evidence list and status).
- Always call `questio_docs_collect()` at the end to keep rendered docs
  in sync.
