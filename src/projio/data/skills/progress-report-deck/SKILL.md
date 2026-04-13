---
name: progress-report-deck
description: >
  Build a recurring progress-report presentation (weekly, monthly,
  milestone) by orchestrating across projects via worklog and drafting
  the deck in presentio. Worklog supplies the cross-project briefing
  data (projects, goals, sessions, captures); presentio owns the deck
  artifact itself. The loop is human-in-the-loop: propose outline from
  worklog data → human approves → draft sections one at a time.
metadata:
  short-description: Worklog-sourced progress deck, iterated section-by-section
  tags: [presentio, progress-report, worklog, cross-project]
  tooling:
    mcp:
      - server: projio
        tools:
          - present_init
          - present_status
          - present_overview
          - present_section_context
          - present_figure_insert
          - present_validate
          - present_assemble
          - present_build
          - present_diff
      - server: worklog
        tools:
          - list_projects
          - get_project
          - worklog_project_context
          - worklog_search
          - goal_list
          - goal_milestones
          - list_sessions
          - list_captures
          - list_notes
---

# Progress Report Deck

Assemble a progress-report deck from worklog data. The deck lives in
one specific project (usually your active "writing" project or a
dedicated `reports/` project) but draws material from **all** projects
via worklog's cross-project index.

## When to use

- Weekly or biweekly progress report to a PI or committee
- Monthly research group update
- Thesis committee milestone report
- Any recurring meeting where the narrative is "what happened across
  my projects since the last report"

Do NOT use for literature-background decks (use
`literature-presentation`) or for one-off talks that aren't rooted in
project activity data.

## Inputs

- `DECK_NAME` (required): short slug, usually dated
  (e.g. `progress-2026-05-05`)
- `HOST_PROJECT` (required): which project's
  `docs/presentations/` the deck lives in
- `WINDOW` (optional): date range for activity ("last 2 weeks",
  "since 2026-04-01"). Default: the span since the most recent
  progress-report deck.
- `FOCUS_PROJECTS` (optional): subset of projects to emphasise;
  default is all projects in worklog

## Workflow

### 1) Gather cross-project briefing

Start in worklog — it has the cross-project view.

```
list_projects(status="active")
```

For each project that should appear in the report:

```
worklog_project_context(project_id=<id>)
goal_milestones(project_id=<id>)
list_sessions(project=<id>, since=<WINDOW start>)
list_notes(project=<id>)
```

Collect:
- Current goals and their milestone state
- Recent sessions (time spent, what happened)
- Any notes, captures, or issues created in the window
- Recent commits / significant changes — via
  `worklog_project_context` which surfaces git activity

### 2) Classify into narrative buckets

Do not propose slides yet. First bucket the material into:

- **Done** — shipped work, closed milestones, merged changes
- **In flight** — active work in progress, with current state
- **Blockers** — things stuck, open questions, decisions needed
- **Next** — what's planned for the next window
- **Side-findings** — anything discovered or decided along the way

This classification is the backbone of the narrative. A progress report
is almost always some permutation of these five buckets.

### 3) Scaffold the deck in the host project

Switch PROJIO_ROOT context (or the agent's project) to `HOST_PROJECT`
and:

```
present_init(name=DECK_NAME, format="marp", template="progress-report")
```

This creates the scaffold with sections: `title`, `summary`,
`progress`, `blockers`, `next-steps`.

### 4) Propose the outline from worklog data

Summarise the bucketed material as an outline. Typical layout:

1. **Title** — date, author, reporting period
2. **Summary** — one-slide TL;DR (3–5 bullets)
3. **Progress** — one slide per major milestone moved forward
4. **Blockers** — one slide per blocker with ask
5. **Next** — planned window

Show this outline to the human. **Ask them to cut, reorder, or add
before drafting any slide.** A 15-minute report is 6–10 slides, not
20.

### 5) Draft one section at a time

For each section:

```
present_section_context(name=DECK_NAME, section=<key>)
```

Draft that section's slides from the bucketed worklog data. Keep to
1–2 slides per section; progress reports live or die by brevity.

**Stop after each section for human review** before moving on. Do not
batch.

### 6) Pull cross-project figures (phase-4 ready)

Phase 1 supports figio figures from the host project only. When
phase 4 cross-project imports land, this step also pulls figures from
other projects via `present_section_import`. For now, if you need a
figure from another project, either:

- Build it locally via figio and `present_figure_insert`, or
- Screenshot and inline as a regular markdown image, or
- Reference the source project via `worklog_read_file` and copy the
  asset explicitly

### 7) Cite-check, validate, build

Same as any other deck:

```
present_cite_check(name=DECK_NAME)
present_validate(name=DECK_NAME)
present_build(name=DECK_NAME, format="pdf")
```

### 8) Follow-ups

After the report, log any decisions or action items from the meeting
in worklog as notes or captures — they become source material for
*next* week's progress report.

## Hard rules

- **Never batch-draft sections.** One section, human review, next
  section. This is the core presentio loop.
- **Never invent activity.** If worklog doesn't have a session, a
  milestone, or a note about a piece of work, do not put it on a
  slide — ask the human for the source instead.
- **Keep it under 10 slides** unless the human explicitly asks for
  more. A progress report is a narrative, not a dump.
- **Worklog is the source of truth.** Do not grep project repos
  directly — use `worklog_project_context`, `list_sessions`, etc.
  The entire point of worklog is that it has the index.
- **The host project's bibliography is what gets cited.** If you want
  to cite a paper that's only in another project's library, ingest
  it into the host project first via `biblio_ingest`.
