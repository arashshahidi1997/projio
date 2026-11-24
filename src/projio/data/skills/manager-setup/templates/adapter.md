---
name: {{prefix}}manager
description: >
  {{project}}'s manager: the adapter for the project-manager core. Use when the
  user asks for an overview of {{project}} work ({{purpose}}), or opens the
  standing `{{prefix}}manager` session. Loads the core first.
metadata:
  short-description: {{project}} adapter for the project-manager core
  tags: [manager, orchestration, adapter]
---

# {{prefix}}manager: the adapter

**Load the core first:** the `project-manager` skill
(`.claude/skills/project-manager/SKILL.md`). This file only fills in what is
specific to {{project}}; the core's rules are not repeated here. Machine keys
are in `{{config_path}}`.

## Names

- Standing manager: `{{prefix}}manager`.
- Work sessions: `{{prefix}}<unit> · <CODE> · <item>`, for example
  `{{prefix}}{{example_unit}} · {{example_code}} · {{example_item}}`; the code is
  the kickoff's on the board. Units are those in `{{config_path}}`.
- Messaging: the standing manager keeps Remote Control on (the core's Start
  and Messaging); other machines are reached by exact session name, by a
  `[from <project>]` note only when that fails.
- Opener: {{opener}}. Wrap: {{wrap}}, ending with the three-line report to
  `{{prefix}}manager`.
- Working copy: `{{repo}}`.
- Starting sessions: on the user's go for a kickoff, the manager starts it
  with `start_session` where the client has it (the core's Levels,
  Dispatcher): nested, fresh, the kickoff as the prompt, sharing `{{repo}}`
  with the "touch only your files, commit by path, switch no branch" line.
  Without the tool, the user pastes the kickoff.
- Sidebar: the manager files itself in the section `managers` (the core's
  Start).

## Board

`{{board_path}}` (gitignored). Refresh with `round.py board`, open it with
`show_pane(pane="file", path="{{board_path}}")`. Delegate opens with
**Recommended now** (the kickoffs to start next, in order, each with its
reason, then what to hold); keep it current every round. Other managers in Sync:
{{other_managers}}.

**Decisions.** On the board, one line per open question (the core's
Decisions): `- **<question>?** · <option A> / <option B> (rec. A) · YYYY-MM-DD`,
dated when first asked, context in sub-bullets, settled items after
`Recent answers:`. **Drill:** record each answer, dated, in
{{decision_place}}. Relay it to the session concerned.

## Units of work and where their state lives

| Unit | State lives in |
|---|---|
| {{unit_row}} | {{unit_state}} |

**Incoming.** {{incoming}}

## What belongs to the sessions (the manager never edits)

- {{session_owned}}

## Collision unit

{{collision}}

## Integration (only when the user asks)

1. {{integration}}

Push: {{push_rule}}.

## {{project}}-specific round sections

{{round_sections}}

## Not the manager's

{{not_managers}}
