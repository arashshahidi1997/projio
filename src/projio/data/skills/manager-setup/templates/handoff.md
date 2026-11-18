---
title: "{{title}}"
date: {{date}}
timestamp: {{timestamp}}
series: "{{series}}"
status: open
git_commit: "{{git_commit}}"
refs: []
---

<!-- File name: handoff-{{timestamp}}-<slug>.md in the handoffs folder (handoffs.dir in the manager config).
     status: open | consumed. When writing a new handoff in a series, set the previous one to consumed.
     A manager handoff has series: manager and git_commit: <HEAD sha>, the watermark `round.py since` reads.
     A work session's handoff has series: <unit> and these sections instead: What shipped · Uncommitted /
     in flight · Parked or broken · Next steps · Kickoff prompt. -->

**How to resume (one paste):** the kickoff snippet at the end.

## What finished
-

## Decisions the user made (don't re-ask)
-

## Open, for the next manager
1.

## Kickoff snippet
```text
Title this session `{{prefix}}manager`. Read the handoff {{handoffs_dir}}/handoff-{{timestamp}}-<slug>.md, then load the {{prefix}}manager skill (it loads the project-manager core) and run a round. Stay open as observer and dispatcher; decisions to me through AskUserQuestion; commit by path; {{push_rule}}.
```
