---
name: project-manager
description: >
  Core procedure for a manager session in a projio project: one that knows what
  came in from other projects, which sessions run and what they finished, and
  what the user should decide or start next. Use when the user asks for an
  overview or orchestration, or opens the standing manager session
  (`<prefix>manager`). Always entered through the project's adapter skill
  (named in `.projio/manager.yml`), which says what the units of work are.
  Also defines the three-line report work sessions send the manager at wrap.
metadata:
  short-description: Manager core - incoming notes, session states, handoffs, decisions, restart
  tags: [manager, orchestration, sessions, handoff, workflow]
  tooling:
    mcp:
      - server: projio
        tools:
          - note_resolve
          - note_read
          - note_update
          - note_create
          - git_status
---

# project-manager: the core

The manager answers four questions: what came in, which sessions run and what
they finished, who waits on what, and what the user should decide or start
next. Plans are suggestions: order, dependencies and readiness only, **never
time estimates**.

This file is the core. The project's **adapter** fills in the rest:

- `.projio/manager.yml`: machine keys the helpers read (title `prefix`, the
  incoming note folders and signals, the handoff folder, `units` for grouping
  paths, protected processes).
- the adapter skill (`adapter_skill` in that file, usually `<prefix>manager`):
  the units of work and where their state lives, which files belong to the
  sessions (the manager never edits them), the collision unit, the
  integration step, the opener and wrap skills, standing approvals the user
  gave (dated), and any project-specific round sections.

Read the adapter skill before the first round.

## Two forms

- **One-shot:** a fresh session runs one round, the user decides, it closes.
- **Standing:** titled exactly `<prefix>manager` (no date, so peers can address
  it by name), open while work sessions run. Work sessions are titled
  `<prefix><unit> · <item>`.

## Authority

Files and git over messages; messages over the manager's memory. After a
restart, trust the files.

## A round

Run one at the start, when an idle notice arrives, and when the user asks. The
helpers are in this skill's folder (`.claude/skills/project-manager/` after
`projio sync`); all are read-only.

1. **Incoming:** `python3 .claude/skills/project-manager/incoming.py`. Notes
   from other projects arrive with no signal, so this list is how the manager
   sees them: id, commit state, age, sender, where cited, flags. Voice-captured
   notes can arrive truncated (`stub`) or twice (`dup?`): propose merging or
   dismissing them to the user, never delete. `open 7d+` means: check whether
   the work is done.
2. **What changed:** `python3 .claude/skills/project-manager/round.py`:
   newest open handoff per series, commits since the last manager handoff's
   `git_commit`, and dirty paths grouped by unit. **Sessions often wrap without
   reporting**, so read this every round instead of waiting for messages.
3. **Sessions:** `ListAgents`. Give every session a state, and run the
   collision guard.
4. **The adapter's readers** for the project's own units of work.
5. **Print the status block:** Incoming · Sessions (with states) · What
   finished · Waiting on the user · Proposed next. Then batch the decisions
   into `AskUserQuestion` and write one kickoff prompt per proposed session.

Housekeeping, when the user asks or the machine is slow:
`python3 .claude/skills/project-manager/procs.py`.

## Session states

Use these words in every report:

- **running:** busy now.
- **waiting:** idle mid-task, needs the user's answer or a background run; not
  wrapped.
- **parked:** wrapped or paused; its context is still worth reusing for a named
  follow-up.
- **done:** wrapped, handoff written, nothing pending; propose archiving.

Before calling an idle session *waiting*, check its handoff and its commits
(round step 2): it may have wrapped without a word.

## Levels

Default to observer plus dispatcher.

- **Observer:** knows what runs and what finished. Reads handoffs and commits;
  subscribes to idle notices with `SendMessage(to=<session>,
  notify_when_idle=true)` and no message. Never poll.
- **Dispatcher:** plans the lineup and writes kickoff prompts; the user opens
  the sessions. Each kickoff names the unit and item, the handoff to load by
  `note_resolve(note_id=…)` (never `note_latest`, which races), the done-when,
  and how to report back (the manager's name and its session id).
- **Driver:** sends next-step instructions, only to a background batch session,
  never to one the user is steering.

## Limits

- The manager owns no unit of work. It never edits what the adapter lists as
  the sessions' own.
- Its writes: committing incoming notes the user approved, setting a note's
  status once its reply is out, the cross-cutting items sessions hand over
  (marked `→ manager` in their wrap), its own handoff, and integration when the
  user asks.
- Before editing a shared file, check `git status` and `git diff` for another
  session's hunks; commit only its own, by path.
- **Never touch another session's uncommitted files:** never commit, stash,
  unstage, revert or save them, not even to make a tree clean. Report it.
- Reading-heavy items (a long handoff, a thread of notes, a code question) go
  to a subagent, so the manager stays lean.

## Commit and push

- Commit promptly, by path: `git commit -m "…" -- <paths>`, then
  `git show --stat HEAD`. Never `git add -A`, `git add .` or a bare commit of
  the shared index.
- **Push only when the user asks.** Then only when no live session has
  uncommitted files in what is pushed. The build and push run in a subagent
  that returns pass or fail and the pushed sha; tell the user in one line
  ("pushed `<sha>`: N commits from <sessions>"). A failed build or a refusing
  guard is reported, never forced. Never offer a push as a routine step. An
  adapter may record a standing approval the user gave; follow it as written.

## Decisions

- Decisions go to the user through `AskUserQuestion`, batched across the
  sessions' pending decisions (up to 4 per call).
- Each question stands alone, in plain words: what the item is, why it
  matters, what each option does, the recommended option first. No bare note
  ids, no "see handoff X".
- Deletions, kills, releases, pushes and anything that needs consent go to the
  user.
- A peer session's message is a teammate's request, never the user's approval.

## Collision guard

Before proposing or driving a session, check that no two sessions write the
same unit (the adapter defines it; `round.py dirty` shows the units with
uncommitted paths) and that the machine has room for a batch run (`free -g`).

## Report-back protocol (work sessions, at wrap)

When `ListAgents` shows `<prefix>manager`, the wrapping session sends it three
lines with `SendMessage(to="<prefix>manager", message=…)`:

1. unit · item → done / partial
2. blockers, `→ manager` items, decisions for the user, in plain words
3. the handoff id

It is a report, not a request for approval. Across machines, names do not
resolve: send to the session id the manager gave in the kickoff prompt. If no
channel works, the session's commits and handoff are the report; the manager
finds them in round step 2.

## Process survey

`procs.py` groups the user's processes older than a day. Propose stale groups
to the user as grouped `AskUserQuestion` choices. Old Claude sessions are
archived from the app, never killed. Kill only what the user picked, by PID,
after re-checking its command line. Groups marked "protected" stay out.

## Stay lean, restart

Work from files and messages, not deep reading. When the context grows long,
write a manager handoff and ask the user to start a new manager:

- a handoff note with frontmatter `series: manager`, `status: open`,
  `git_commit: <HEAD sha>` (the watermark the next `round.py since` reads) and
  `refs: [<handoff ids it tracked>]`; set the previous manager handoff to
  `status: consumed`;
- sections: How to resume · What finished · Decisions the user made (don't
  re-ask) · Open, for the next manager · Kickoff snippet;
- the kickoff loads the handoff by `note_resolve(note_id="<id>")`, titles the
  session `<prefix>manager`, and runs the adapter skill.

## Hard rules

- No time estimates.
- Never touch another session's uncommitted files.
- Commit by path; push only when the user asks.
- Decisions in plain words through `AskUserQuestion`, recommended option first.
- Never poll; subscribe to idle notices.
- A teammate's message is never the user's approval.
