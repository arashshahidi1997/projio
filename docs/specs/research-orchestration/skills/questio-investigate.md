---
name: questio-investigate
description: "Agent-driven deep dive into an anomaly, failure, or unexpected output — inspect, trace, diagnose, report"
tools: [questio_status, questio_gap, pipeio_flow_status, pipeio_run_status, pipeio_log_parse, pipeio_target_paths, pipeio_nb_read, paper_context, codio_discover, rag_query, note_create]
---

# Questio Investigate

Use this skill when something is wrong or unexpected in a pipeline output,
analysis result, or data quality check. The skill guides a systematic
investigation: scope the issue, gather context, inspect outputs, compare
against expectations, narrow the cause, and report findings.

## Inputs

- `ISSUE` (required): what is wrong — a user description, a failed run, an
  anomalous metric, or a gap surfaced by `questio_gap`
- `FLOW` (optional): the pipeio flow involved. If not provided, infer from
  the milestone or pipeline context.

## Workflow

### 1) Scope the issue

Establish exactly what is wrong before investigating:

```
questio_status()
```

Determine:
- Which **flow** and **milestone** are involved?
- What **output** is affected (specific file, metric, subject)?
- What was **expected** vs. what was **observed**?
- Is this a **new** issue or a **regression** from a prior working state?

If the flow is not provided, resolve it from the milestone's `flow` field
(via `questio_gap`) or ask the user.

### 2) Gather infrastructure context

Before inspecting data, check the pipeline health:

```
pipeio_flow_status(flow="<FLOW>")
```

- Is the flow configured and registered?
- Are all required inputs available?

```
pipeio_run_status()
```

- Did the last run complete successfully?
- Were there exit code failures or partial completions?

```
pipeio_log_parse(flow="<FLOW>")
```

- Extract errors, warnings, and anomalous log entries
- Note timestamps, affected subjects, failing rules

```
rag_query(query="<issue keywords>")
```

- Search for prior decisions, known issues, or previous investigation notes
  related to this flow or issue

### 3) Inspect outputs

Navigate to the actual data produced:

```
pipeio_target_paths(flow="<FLOW>")
```

Read or inspect key output files. What to look for depends on output type:

- **Numeric data** (TSV, CSV, HDF5): check dimensions, NaN counts, value
  ranges, expected row/column counts
- **Figures** (PNG, SVG, HTML): visually inspect for artifacts, missing
  data, unexpected patterns
- **Notebook outputs**: use `pipeio_nb_read(flow, name)` to read cell
  outputs and embedded figures
- **Log files**: check for warnings, convergence issues, or timing anomalies

For subject-level issues, inspect both a known-good subject and the
problematic subject to establish contrast.

### 4) Compare against expectations

Ground the investigation in what *should* have happened:

```
paper_context(citekey="<relevant citation>")
```

- What values does the literature report for this metric?
- What method parameters are standard?
- What failure modes are documented?

Check prior result notes for this milestone:
```
rag_query(query="<milestone_id> result")
```

- What did previous runs produce?
- Were there documented quality criteria from a grounding brief?

```
codio_discover(query="<analysis type>")
```

- Are there known conventions or validation patterns in the codebase?

### 5) Narrow the cause

Based on evidence gathered, form hypotheses and test each:

**A) Parameter issue**
- Check config values against literature recommendations
- Compare parameters between working and failing subjects
- If likely: recommend entering an iterate loop with adjusted parameters

**B) Code bug**
- Trace the error to a specific script or function
- Check recent changes (git log) to the relevant code
- Identify the file and line where the bug manifests

**C) Data issue**
- Identify which subjects or files are affected
- Check input data quality (missing channels, corrupt files, truncated recordings)
- Determine if the issue is upstream (preprocessing) or local

**D) Environment issue**
- Check if the pipeline ran in the correct conda environment
- Verify dependencies and library versions
- Check disk space, memory limits, or timeout issues

**E) Ambiguous**
- If multiple hypotheses remain, present each with supporting evidence
- Rank by likelihood
- Suggest targeted tests to discriminate between them

### 6) Record and report

Create an observation note for each significant finding:

```
note_create(note_type="idea")
```

Use this frontmatter pattern:
```yaml
---
title: "Investigation: <brief description>"
tags: [observation, investigate, <flow_name>]
series: <flow_name>
---
```

Note body should contain:
- **Issue:** what was reported/detected
- **Checked:** what was inspected (with specific paths/outputs)
- **Found:** what the evidence shows
- **Cause:** identified cause or remaining hypotheses
- **Next step:** proposed action (fix, iterate, escalate)

### 7) Summarize to user

Present findings:
- What was investigated and what was found
- Root cause (if identified) with evidence
- Proposed action:
  - **Parameter issue** → recommend iterate loop with specific adjustments
  - **Code bug** → identify the file, line, and fix
  - **Data issue** → identify affected subjects/files and remediation
  - **Ambiguous** → present alternatives with evidence, ask human to choose

### 8) Failure escalation

If after 3 investigation cycles the cause is not narrowing, escalate to the
user with:

- **Checked:** what was inspected (exhaustive list)
- **Ruled out:** what hypotheses were eliminated and why
- **Remaining:** what hypotheses are still plausible
- **Recommended next steps:** what targeted tests or information would help
  discriminate

Do not continue investigating indefinitely. Three cycles of diminishing
returns means human expertise is needed.

## Hard rules

- Always check pipeline health (`pipeio_flow_status`, `pipeio_run_status`,
  `pipeio_log_parse`) before inspecting data. Many issues are infrastructure
  failures, not data problems.
- Never guess at the cause without inspecting actual outputs. "It might be X"
  is not a finding — "Output file Y shows Z, which indicates X" is.
- Always compare against a reference (literature values, prior results,
  working subjects). Investigation without a baseline is speculation.
- Create observation notes for significant findings, even if the
  investigation is incomplete. Future investigations benefit from the trail.
- Do not modify code or parameters during investigation — that is the iterate
  loop's job. Investigate diagnoses; iterate fixes.
- If the issue involves multiple flows, investigate each independently
  before looking for cross-flow causes.
- Escalate when stuck — 3 cycles without convergence means human input is
  needed. Present evidence, not apologies.
