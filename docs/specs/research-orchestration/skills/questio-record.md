---
name: questio-record
description: "Guided evidence and observation capture — result notes for milestones, observation notes for mid-loop findings"
tools: [questio_status, questio_gap, note_create, note_update, questio_docs_collect]
---

# Questio Record

Use this skill to capture research findings. It handles two modes:

- **Mode A (Result note):** structured evidence that advances a milestone —
  created when you have a definitive finding with metrics.
- **Mode B (Observation note):** lightweight mid-loop capture during
  investigate or iterate loops — created to record what was checked, found,
  or tried.

## Choosing the right mode

| Signal | Mode |
|--------|------|
| "I found something definitive that advances a milestone" | **A — Result** |
| "The iteration produced results meeting quality criteria" | **A — Result** |
| "I found something interesting during investigation" | **B — Observation** |
| "I want to record what I tried and what happened" | **B — Observation** |
| "Intermediate finding, not yet conclusive" | **B — Observation** |
| "Pipeline failed — here's what I found" | **B — Observation** |

**Rule of thumb:** if it has a quantitative metric and confidence level that
could be cited as evidence for a milestone, it's a result note. Everything
else is an observation note.

---

## Mode A: Result note (milestone evidence)

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
- The question ID(s) exist in `docs/plan/questions.yml`
- The milestone ID exists in `docs/plan/milestones.yml`

If an ID doesn't exist, tell the user and ask for correction. Do not create
result notes with invalid references.

### 3) Create the result note

```
note_create(note_type="result", title="<descriptive title>")
```

Edit the generated file to fill in the structured frontmatter:

```yaml
---
title: "<descriptive title>"
owner: "<user>"
series: "<flow_name>"
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

**Qualitative evidence** is also valid — use `metric: qualitative` with a
free-text `value`:
```yaml
metric: qualitative
value: "Spectrograms show clean signal after TTL removal, no residual artifacts visible"
confidence: preliminary
```

### 4) Update milestone evidence

Read `docs/plan/milestones.yml` and add the result note's filename (stem) to
the milestone's `evidence` list:

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
- If approved, update `status: complete` in `docs/plan/milestones.yml`
- Check if this completion unblocks any downstream milestones

If not yet sufficient:
- Report what's still missing (e.g., "3/5 subjects validated, need remaining 2")

### 6) Regenerate plan docs

```
questio_docs_collect()
```

---

## Mode B: Observation note (mid-loop capture)

### 1) Determine context

Identify from the current conversation:
- Which **loop** is active? (`investigate`, `iterate`, or general)
- Which **flow** is involved?
- What **iteration number** is this? (if in an iterate loop)

### 2) Create the observation note

```
note_create(note_type="idea", title="<brief description>")
```

Edit the frontmatter to tag it as an observation:

```yaml
---
title: "<Investigation: ... | Iteration N: ... | Observation: ...>"
tags: [observation, <loop_type>, <flow_name>]
series: <flow_name>
---
```

Tag conventions:
- `observation` — always present, marks this as a mid-loop capture
- Loop type: `investigate` or `iterate` — which loop produced this
- Flow name: the pipeio flow involved (e.g., `sharpwaveripple`)

Title conventions:
- Investigation: `"Investigation: SWR detection rate anomaly in sub-03"`
- Iteration: `"Iteration 2: SWR detection with threshold=3.0 SD"`
- General: `"Observation: preprocessing artifacts in channel HPC-R1"`

### 3) Fill the note body

Use this template:

```markdown
## Checked
- <what was inspected — specific files, outputs, metrics>

## Found
- <what the evidence shows — specific values, patterns, anomalies>

## Interpretation
- <what this means — cause identified, hypothesis formed, or uncertainty>

## Next step
- <proposed action — fix, iterate, escalate, or continue investigating>
```

Keep it concise. Observation notes are breadcrumbs, not full reports.

### 4) Do NOT update milestones

Observation notes are **not** milestone evidence. They inform future result
notes but do not appear in milestone `evidence` lists and do not trigger
milestone status changes.

Do not call `questio_docs_collect()` for observation notes — the plan docs
don't reference them.

---

## Hard rules

- Never create a result note with a question or milestone ID that doesn't
  exist in the YAML files.
- Always ask for confirmation before changing a milestone status to `complete`.
- Result notes must have a `metric` and `value` — qualitative-only results
  use `metric: qualitative` with `confidence: preliminary`.
- Never modify `docs/plan/questions.yml` — only `docs/plan/milestones.yml`
  is updated by this skill (evidence list and status).
- Always call `questio_docs_collect()` after creating a result note.
- Never call `questio_docs_collect()` after creating an observation note.
- Observation notes go in `docs/log/idea/` (standard notio location).
  Result notes go in `docs/log/result/`.
- Observation notes always have `tags: [observation, ...]`.
  Result notes always have `tags: [result, ...]`.
- Do not add observation notes to milestone evidence lists.
- Tag every observation note with the loop type (`investigate` or `iterate`)
  so future searches can reconstruct the investigation trail.
