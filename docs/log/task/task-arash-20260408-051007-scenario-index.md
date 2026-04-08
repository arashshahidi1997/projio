---
title: "Scenario book: create index page and update scenario-book.md as overview"
date: 2026-04-08
timestamp: 20260408-051007
status: done
result_note: /storage2/arash/worklog/workflow/captures/20260408-141838-598800/note.md
completed: 2026-04-08T14:18:40+02:00
actionable: true
source_note: "docs/specs/research-orchestration/scenario-book.md"
project_primary: projio
tags: [task, questio, scenario-book]
---

# Scenario book: create index page and update scenario-book.md as overview

## Goal

Restructure the scenario book: convert `scenario-book.md` into an overview/index page that links to individual scenario files in the `scenarios/` subdirectory. Add a coverage matrix showing which ecosystem components and loop patterns each scenario exercises.

## Context

The scenario book started as a single file with two scenarios (TTL removal and anomaly investigation). It's being expanded to 8 scenarios total, each in its own file under `docs/specs/research-orchestration/scenarios/`. The original file needs to become an index/overview that:
- Explains what the scenario book is and how to use it
- Lists all scenarios with one-line summaries
- Shows the coverage matrix (which tools/loops/subsystems each scenario exercises)
- Keeps the anti-patterns table from the original

## Prompt

**Step 1: Read all scenario files.**
- Read `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenario-book.md` (current content)
- List all files in `/storage2/arash/projects/projio/docs/specs/research-orchestration/scenarios/` to see what scenarios exist
- Read each scenario file's header to get titles and ecosystem coverage

**Step 2: Move the two existing scenarios from scenario-book.md into separate files.**

Move Scenario 1 (TTL characterization) to `scenarios/scenario-ttl-removal.md` and Scenario 2 (anomaly investigation) to `scenarios/scenario-anomaly-investigation.md`. Add mkdocs material admonitions to both (they were written before the admonition requirement):
- `!!! info "Behind the scenes"` for tool call blocks
- `!!! tip` for design insights
- `!!! warning "Human checkpoint"` for confirmation points

**Step 3: Rewrite scenario-book.md as the index/overview.**

Structure:
```markdown
# Scenario Book — Agentic Research Workflows

## What is this?

[1-2 paragraphs explaining the scenario book's purpose: demonstrate realistic
human-agent conversations using the projio ecosystem. Each scenario shows what
you'd actually type, what the agent does behind the scenes, and where human
judgment drives the process.]

## Scenarios

| # | Scenario | Primary pattern | Ecosystem focus |
|---|----------|----------------|-----------------|
| 1 | [TTL removal](scenarios/scenario-ttl-removal.md) | Orient → iterate | pipeio, questio |
| 2 | [Anomaly investigation](scenarios/scenario-anomaly-investigation.md) | Investigate | pipeio, questio |
| 3 | [Reproduce paper results](scenarios/scenario-reproduce-paper.md) | Ground → iterate | biblio, questio, pipeio |
| 4 | [Evaluate new method](scenarios/scenario-method-evaluation.md) | Ground → iterate → decide | biblio, codio, pipeio |
| 5 | [Cross-flow debugging](scenarios/scenario-cross-flow-debug.md) | Investigate (multi-flow) | pipeio |
| 6 | [Manuscript drafting](scenarios/scenario-manuscript-drafting.md) | Iterate (writing) | manuscripto, figio, biblio |
| 7 | [Unexpected finding](scenarios/scenario-unexpected-finding.md) | Iterate → investigate → extend | questio, biblio |
| 8 | [Research sprint](scenarios/scenario-research-sprint.md) | Scheduled orient → iterate | worklog, questio, pipeio |

## Ecosystem coverage matrix

[Table showing scenarios vs subsystems (biblio, codio, pipeio, figio, manuscripto,
questio, notio, worklog, indexio) with checkmarks]

## Loop pattern coverage

[Table showing scenarios vs loop patterns (orient, investigate, iterate,
ground, record, propose-review-confirm)]

## Anti-patterns

[Keep the anti-patterns table from the original scenario-book.md]

## Tool reference

[Keep the tool reference table from the original, expanded with tools from
new scenarios]
```

**Step 4: Commit** with message: "Restructure scenario book: index page with individual scenario files"

## Acceptance Criteria

- [ ] scenario-book.md is now an index/overview
- [ ] Original two scenarios moved to separate files with admonitions added
- [ ] Scenario table links to all 8 files
- [ ] Ecosystem coverage matrix present
- [ ] Loop pattern coverage present
- [ ] Anti-patterns and tool reference tables preserved
- [ ] All links are relative and correct
- [ ] Committed
