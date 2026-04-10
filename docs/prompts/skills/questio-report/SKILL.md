---
name: questio-report
description: >
  Generate a supervisor-ready progress summary with milestones hit, key
  results, blockers, and next steps. Persists the report to
  docs/deliverables/reports/ for sharing and archival.
metadata:
  short-description: supervisor-ready research progress summary
  tags: [questio, report, research, progress, deliverables]
  tooling:
    mcp:
      - server: projio
        tools:
          - questio_status
          - questio_docs_collect
          - note_search
          - pipeio_flow_status
---

# Questio Report

Use this skill to generate a concise, supervisor-ready progress summary and
persist it to `docs/deliverables/reports/`. Suitable for weekly updates,
session wrap-ups, or on-demand status checks.

## Inputs

- `PERIOD` (optional): time window for recent activity. Default: `7d` (last
  7 days). Accepts: `1d`, `7d`, `14d`, `30d`.
- `AUDIENCE` (optional): who the report is for. Default: `supervisor`.
  Accepts: `supervisor`, `team`, `conference`, `public`.

## Workflow

### 1) Get overall research state

```
questio_status()
```

Capture:
- Total questions and their statuses
- Overall milestone completion (N/M complete)
- Questions with sufficient evidence
- Blocked questions and what blocks them

### 2) Find recent results

```
note_search(query="result", tags=["result"])
```

Filter to notes created within `PERIOD`. For each recent result note, extract:
- Question and milestone it supports
- Key metric and value
- Confidence level

### 3) Identify recently completed milestones

Compare current milestone statuses against what would have been true at the
start of `PERIOD`. Milestones that transitioned to `complete` during the period
are recent completions.

If this comparison is not feasible, list milestones marked `complete` whose
evidence notes fall within `PERIOD`.

### 4) Identify blockers

From `questio_status()`, list:
- Milestones with `blocked` status and what blocks them
- Questions where all remaining milestones are blocked
- Pipeline issues (check `pipeio_flow_status` for referenced flows if needed)

### 5) Determine next steps

Based on current state, list 2-3 concrete next actions. These should be the
same recommendations `questio-next` would produce, but abbreviated.

### 6) Assess timeline impact

If any milestones are behind their expected timeline (if timelines are tracked):
- Flag which milestones are delayed
- Note downstream impact (which questions are affected)
- Suggest whether reprioritization is needed

If no timelines are tracked, skip this section.

### 7) Format the report

Format the report body as clean markdown:

```markdown
# Research Progress Report

**Period:** <start_date> - <end_date>
**Project:** <project name>

## Progress

- **Milestones:** <N_complete>/<N_total> complete (<+delta> this period)
- **Questions:** <N_sufficient>/<N_total> with sufficient evidence
- **Recent completions:**
  - <milestone_id>: <description> (completed <date>)

## Key Results

| Date | Question | Milestone | Metric | Value | Confidence |
|------|----------|-----------|--------|-------|------------|
| <date> | <qid> | <mid> | <metric> | <value> | <conf> |

## Blockers

- <blocker description> — blocks <milestone_id> which blocks <question_id>

## Next Steps

1. <concrete action> — <rationale>
2. <concrete action> — <rationale>

## Timeline Impact

<assessment or "On track — no delays identified.">
```

### 8) Persist the report

Save the report to `docs/deliverables/reports/`. Create the directory if it
doesn't exist.

**Filename:** `report-YYYY-MM-DD.md` using today's date. If a report with
that filename already exists, append a sequence suffix:
`report-YYYY-MM-DD-2.md`.

**Frontmatter:** prepend YAML frontmatter to the report body:

```yaml
---
title: "Research Progress Report — <start_date> to <end_date>"
date: <today's date>
type: report
audience: <AUDIENCE input, default: supervisor>
period: "<start_date> to <end_date>"
questions: [<list of question IDs referenced in Key Results>]
tags: [report, <AUDIENCE>]
---
```

### 9) Regenerate deliverables index

```
questio_docs_collect()
```

This regenerates the index pages in `docs/deliverables/` so the new report
appears in the overview.

## Hard rules

- Keep the report concise — this is for a supervisor who wants a 2-minute read.
- Always include quantitative metrics in Key Results — no vague summaries.
- Blockers must name specific milestones and questions, not generic categories.
- If there are no recent results, say so explicitly — don't pad with filler.
- Do not include implementation details (code, notebook names, script paths)
  in the report — keep it at the research level.
- Always persist the report to `docs/deliverables/reports/` — do not output
  it only as ephemeral text.
- Always call `questio_docs_collect()` after persisting the report.
- If `plan/questions.yml` doesn't exist, tell the user the project doesn't
  have a questio data model set up yet.
