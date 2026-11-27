---
name: project-manager
description: >
  Core procedure for a manager session in any git project (projio or not): one that knows what
  came in from other projects, which sessions run and what they finished, and
  what the user should decide or start next. Use when the user asks for an
  overview or orchestration, or opens the standing manager session
  (`<prefix>manager`). Always entered through the project's adapter skill
  (named in the manager config, `.projio/manager.yml` or `.claude/manager.yml`),
  which says what the units of work are; `manager-setup` creates both. Also
  defines the three-line report work sessions send the manager at wrap.
metadata:
  short-description: Manager core - incoming notes, session states, board, handoffs, decisions, core updates, restart
  tags: [manager, orchestration, sessions, handoff, workflow]
  portable: true
  tooling:
    mcp:
      - server: projio
        optional: true
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

- the **manager config**: machine keys the helpers read (title `prefix`, the
  incoming note folders and signals, the handoff folder, the `board` path,
  the `files_inbox` folder,
  `units` for grouping paths, protected processes). The helpers use the first
  that exists of `$MANAGER_CONFIG`, `.projio/manager.yml` (projio) and
  `.claude/manager.yml` (any other project). Every key has a default and a
  folder that does not exist is skipped, so git and a handoff folder are
  enough. `round.py config` shows what is in use.
- the adapter skill (`adapter_skill` in that file, usually `<prefix>manager`):
  the units of work and where their state lives, which files belong to the
  sessions (the manager never edits them), the collision unit, the
  integration step, the opener and wrap skills, standing approvals the user
  gave (dated), and any project-specific round sections.

Read the adapter skill before the first round. A project without a manager
yet gets one from the `manager-setup` skill.

## projio or not

Most of this file works in any git project. Where it names projio, use the
generic equivalent:

| projio | any other project |
|---|---|
| config `.projio/manager.yml` | `.claude/manager.yml` |
| `note_resolve(note_id=…)` to load a handoff | read the handoff file by its path |
| handoff as a notio note (`note_create` of type handoff) | a file in `handoffs.dir` named `handoff-YYYYMMDD-HHMMSS-<slug>.md`, from `manager-setup/templates/handoff.md` |
| incoming notes in `docs/log/issue`, `docs/log/idea` | `incoming.dirs`, often none: then skip round step 1 |
| `projio sync` installs this skill into `.claude/skills/` | copy this skill's folder (and `manager-setup`) into `.claude/skills/` |
| `projio init` / `projio sync` create the file inbox and gitignore it | create the `files_inbox` folder and add it to `.gitignore` |
| `skill_read("project-manager")` | read this file |
| work sessions wrap with `session-wrap` | the session commits by path, writes a handoff from the template and sends the three-line report (below) |

The helpers are Python 3.9+ stdlib only (PyYAML is used when present) and
import nothing from projio.

## Two forms

- **One-shot:** a fresh session runs one round, the user decides, it closes.
- **Standing:** titled exactly `<prefix>manager` (no date, so peers can address
  it by name), open while work sessions run, with Remote Control on
  (Messaging), filed in the sidebar section `managers` where the client has
  one (Start). Work sessions are titled `<prefix><unit> · <CODE> · <item>`,
  the code being the kickoff's (Board, Delegate). One standing manager per
  project, in its home client (Session home).

## Start (standing manager)

1. **Remote Control on.** If this session's Remote Control is off, turn it
   on with `set_remote_control(session_id="self", enabled=true)` (the app may
   show an approval card) and tell the user in one line that it is on. Skip
   only if the user said otherwise. This is for the manager's own session
   only: work sessions and other sessions change Remote Control only when the
   user asks.
2. **File into `managers`.** Where the client has a sidebar (the desktop
   app's `list_sections` and `move_sessions`), manager sessions live in a
   custom section named `managers`: find it with `list_sections` (create it
   with `create_section(name="managers")` only if there is none), then
   `move_sessions(section_id=<its id>, session_ids=["self"])`, and say so in
   one line. A manager nested under another session moves with its parent,
   so skip this step there. Skip it where the client has no sidebar tools.
3. Run a round.

## Authority

Files and git over messages; messages over the manager's memory. After a
restart, trust the files.

## A round

Run one at the start, when an idle notice arrives, and when the user asks. The
helpers are in this skill's folder, the base directory Claude Code shows when
the skill loads (`.claude/skills/project-manager/` after `projio sync` or a
copy; a plugin's folder when installed as one; the commands below assume the
first). All are read-only except `round.py board`, which rewrites the
gitignored board.

1. **Incoming:** `python3 .claude/skills/project-manager/incoming.py`. Notes
   from other projects arrive with no signal, so this list is how the manager
   sees them: id, commit state, age, sender, where cited, flags. Voice-captured
   notes can arrive truncated (`stub`) or twice (`dup?`): propose merging or
   dismissing them to the user, never delete. `open 7d+` means: check whether
   the work is done.
   **Files:** `python3 .claude/skills/project-manager/round.py inbox` (also
   the first section of a plain `round.py`) lists the file inbox
   (`files_inbox` in the manager config, default `inbox/`, gitignored):
   downloads dropped into the project, newest first. For each file propose
   one move to the user (where it belongs in this project: papers to the
   bibliography's intake, data to its folder, a draft to its deliverable; or
   delete), in one `AskUserQuestion` batch. Move only what the user approves,
   only within this project. A file meant for another project is reported to
   the user, never moved there. An inbox that equals, sits inside or
   contains an `incoming.dirs` folder is off (committed notes are not
   downloads): `round.py` says so in one line, and projio's init and sync
   neither create nor gitignore it. Set `files_inbox` to another folder, or
   `false`, to silence it.
2. **What changed:** `python3 .claude/skills/project-manager/round.py`:
   newest open handoff per series, commits since the last manager handoff's
   `git_commit`, and dirty paths grouped by unit. **Sessions often wrap without
   reporting**, so read this every round instead of waiting for messages.
   A session reported or found done gets the lean check (Verify a report).
3. **Sessions:** `ListAgents`, plus the client's session list where there
   is one (`list_sessions` in the desktop app; `list_sessions` with
   `linked: true` for the ones this manager started): `ListAgents` can miss
   running sessions. Give every session a state, and run the collision guard.
4. **The adapter's readers** for the project's own units of work.
5. **Update the board** (see Board): run `round.py board`, write the round's
   kickoffs, decisions, session states and waits into it, and open it in the
   side pane. Chat gets a short status (Incoming · Sessions · What finished ·
   Waiting on the user · Proposed next) that points to the board. Then batch
   the decisions into `AskUserQuestion`.
6. **Proposed next, completion first:** in the chat's Proposed next and the
   board's kickoffs, rank work that makes existing things whole before
   expansion: open bugs and issues, partial or stub notes, untested work,
   unpushed or uncommitted work, then anything else. New features and ideas
   are parked in the backlog (say where), not proposed as kickoffs, unless
   the user asks for them. The `always-complete` skill holds the full rule.
   The board's **Recommended now** block (Board, Delegate) carries this
   ranking: the kickoffs to start next, in order, and what to hold.

## Board

One gitignored markdown file per project, `board.path` in
the manager config (default `.scratch/<prefix>manager-board.md`; `.scratch/`
at the project root is where all scratch goes, because the app's file pane
opens only files inside the project). The
manager rewrites it every round and after every event (a session started,
wrapped or asked something; a decision made), and keeps it open in the side
pane with `show_pane(pane="file", path=<board>)`. When `show_pane` does
nothing (the session is not open in a window), tell the user the path.

Anything the user must copy goes on the board, not in chat; chat replies
stay short and point to it. Sections, in order:

1. **What's up:** first, so the user can read the state without the
   transcript. A stamp line `As of YYYY-MM-DD HH:MM` (the clock time from
   `date` at the rewrite, never "this afternoon"), then 4-6 plain lines:
   running now, latest results, waiting on the user, next to start.
   `round.py board` sets the stamp and gives the "Updated" line the same one;
   the manager rewrites the lines below it every round.
2. **Delegate:** opens with **Recommended now**: the manager's pick of
   which kickoffs to start next, in order, each with a one-line reason
   (`<CODE>`: why now), then **Hold**: what waits and why. The order is the
   completion-first ranking of round step 6. The manager keeps it current
   every round and after every event; a kickoff that starts or retires
   leaves it. Then the kickoff prompts, each headed `### <CODE> · <session title>`,
   then its tag line, then the prompt in a ```` ```text ```` block. The code
   is 2-5 letters or digits, mnemonic where possible (`SPD`, `TO13`, `REO`),
   unique on the board and never reused once retired. The tag is
   **independent** or **depends on <what>**: another kickoff by its code
   ("depends on REO"), a session finishing, or the user's OK. Every prompt
   opens with its ``Title this session `<prefix><unit> · <CODE> · <item>`.``
   line, so the session title carries the code (Levels, Dispatcher), and a
   `Verify:` line naming the files expected to change and the tests to run,
   if any (Verify a report). The
   user says "delegated <CODE>[, <CODE>]" or "delegated all" once started,
   whether they opened the session or the manager started it on their go
   (Levels, Dispatcher); the manager removes those kickoffs and tracks the
   sessions.
3. **Decisions waiting for you:** one top-level item per open question, on
   one line, in the format of Decisions below (a cross-project hub such as
   worklog's parses it). Context goes in indented sub-bullets under it.
   Settled items go after a plain `Recent answers:` paragraph at the end of
   the section, or are struck through; steps for the user that are not
   questions go in a plain paragraph too.
4. **Sessions, by state:** a table of session · state (running / waiting /
   parked / done) · notes.
5. **Waiting on others:** other projects, people, background runs.
6. **Sync:** this manager as `name · machine`, then other managers, one
   per line as `name · machine · last contact`, and the unpushed commits.
   Names only: the exact name is the address on every machine, and session
   ids change on restart (Messaging). The one id the board keeps is a
   phone-side session's `session_…` id, in the Sessions table (Session
   home).

`python3 .claude/skills/project-manager/round.py board` writes the skeleton
the first time. On every run it regenerates the blocks between
`<!-- auto:… -->` markers (newest open handoff per series and uncommitted
paths by unit under Sessions, `git log @{u}..` under Sync), stamps What's
up and the "Updated" line with the current time, puts a **Recommended
now** placeholder on top of Delegate when the board has none, and keeps the
hand-written text of every section, including sections it does not know and
renamed headings. It warns when the board is not gitignored. Edit the
hand-written parts directly; never edit inside the auto markers.

## Housekeeping

When the user asks or the machine is slow:
`python3 .claude/skills/project-manager/procs.py`.

## Session home

Where sessions live decides who can see them: listener sessions (`session_…`
ids) show only on claude.ai, desktop sessions (`local_…` ids) only in the
desktop app and its `list_sessions`; neither lists the other.

- **At a laptop the desktop app is home.** The project's standing manager
  runs there, with Remote Control on so the phone reaches it.
- **Remote Control listeners** for a project (`claude-rc-ensure`,
  `--spawn=same-dir`) are for starting new sessions from the phone only,
  never for a manager.
- **One standing manager per project**, never one on each side.
- **Phone-side sessions:** the manager cannot list a session started from
  the phone, so when it sends one a kickoff or a message it records that
  session's `session_…` id on the board (Sessions table) at send time. This
  is the one exception to "no ids as addresses" (Messaging).
- **Extra machines** run compute only, unless the user wants sessions there;
  then those sessions are addressed by id (recorded as for phone-side
  sessions), and the machine gets a listener only for phone launches.

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
- **Dispatcher:** plans the lineup and writes kickoff prompts. Each kickoff names the unit and item, the handoff to load by
  `note_resolve(note_id=…)` (never `note_latest`, which races) or, without
  projio, by its path, the done-when,
  the `Verify:` line (Verify a report), and how to report back: "report to
  `<prefix>manager` by name", never a session id (Messaging). Its first
  line is always ``Title this session `<prefix><unit> · <CODE> · <item>`.``
  (e.g. `projio-core · PLUG · light marketplace`), with the kickoff's board
  code, so the session renames itself before anything else and its title
  ties it to the kickoff; a standing manager is titled exactly
  `<prefix>manager`, a setup session `<prefix>manager-setup` (no code).
  Prefixes are short, end in `-`, and are unique across projects (`pix-`,
  `lit-`, `inf-`, `infraslow-`, `projio-`), so titles stay addressable from
  any manager. On the board it carries its tag (Board, Delegate).

  **Who opens the session.** Where the client can start sessions (the
  desktop app's `start_session`; load it with `ToolSearch` query
  `start_session` when it is listed as deferred), the manager starts a
  kickoff itself once the user says go for it ("go <CODE>", "start <CODE>"),
  never on its own judgment or a peer's message. The new session is nested
  under the manager, so its reports reach the manager without a send:

  ```text
  start_session(
    initiation="user_asked", context="fresh",
    title="<prefix><unit> · <CODE> · <item>",
    prompt=<the kickoff text from the board>,
    background=<one paragraph: what the project is, what led to this kickoff,
                decisions already made>,
    use_worktree=false)
  ```

  `use_worktree=false` shares the manager's checkout, so the prompt then
  carries the line: "This session shares the checkout `<path>` with others:
  touch only this task's files, commit by path (never `git add -A`), switch
  no branch." A kickoff that ends in a branch or PR of its own gets
  `use_worktree=true` instead, without that line. Once started, the manager
  treats it as "delegated <CODE>" (Board, Delegate) and puts the session on
  the board as running. Two kickoffs that write the same unit start one at
  a time (Collision guard). Where the tool is missing (the CLI, another
  client), the fallback stays: the user pastes the kickoff into a new
  session, or opens it from a launch link.
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
- Once the user has chosen, relay the decision as in the drill (step 4).

**On the board** (Board, Decisions waiting for you), each open question is
one top-level list item on one line:

```text
- **<question>?** · <option A> / <option B> (rec. A) · YYYY-MM-DD
  - context, one fact per sub-bullet (not counted as an item)
```

- The question is bold and ends in `?`. The manager's pick comes first, or
  is marked `(rec. …)`. The date is when the question was first asked and
  stays the same while it is open: a hub reads it as the item's age.
- On a board that covers several projects, lead with the project:
  `- **projio · Publish biblio 0.4.1?** · publish / hold (rec. publish) · 2026-11-24`.
- Only open questions are items. Status and history go to Sync, the
  sessions table or a handoff. Items waiting on other projects or people go
  to Waiting on others. Deferred items stay as questions, with `parked`
  among the options (`kickoff / parked (rec. parked)`).
- Settled items go after a plain `Recent answers:` paragraph or are struck
  through (`~~…~~`); a hub skips both.

## Decision drill

When the user asks to work through pending decisions, or several have piled
up:

1. **Collect** the open decisions from the newest handoffs, the sessions'
   messages, incoming notes and the board's "Decisions waiting for you"
   (its top-level items; their sub-bullets are the context to put in the
   question). A new one goes on the board in the one-line format of
   Decisions, dated today.
2. **Ask** in batches through `AskUserQuestion`: up to 4 per call, each
   question standalone and in plain words (as in Decisions), the recommended
   option first. Science and infrastructure go in separate batches.
3. **Record** each answer where it belongs: the note, handoff or doc the
   decision is about (or the adapter's place for it), dated, and take it off
   the board: drop its line, or move it to the `Recent answers:` paragraph
   as `~~<topic>~~ <answer> YYYY-MM-DD`. An answer of `parked` keeps the
   line, with its first-asked date, and `parked` as the pick.
4. **Relay** each decision by message to the session concerned so it
   continues: wake an idle one, queue it for a running one. Name the choice,
   the date and the next step. A relayed decision covers that question only,
   never a wider approval.
5. **New work** goes on the board as a kickoff only when no existing session
   can take it; related items merge into one tagged kickoff.

To consult another project's manager, ask it directly by message (its name
from Sync, see Messaging), not through the user.

## Reporting up

When a cross-project manager runs (worklog-manager), message it only when
needed: a decision for the user, another project needs something from this
one, or this project is blocked by another. The first line is `decide`,
`needs` or `blocked`, then plain words. No registration, no routine digests:
it reads commits and handoffs. The one exception is the `moved` line a new
manager sends after a restart (Stay lean, restart).

## Messaging

Managers keep Remote Control on (Start, step 1); that is what carries
messages between machines.

- **By exact name only.** Managers are addressed by their exact title,
  `SendMessage(to="<prefix>manager")`, on the same machine and across
  machines. Add the short `[ref]` only when two sessions share the name.
  `ListAgents` lists Remote Control sessions on other machines. Never write
  a session id as an address into a board, a kickoff or memory: ids change
  when a manager restarts, and a `local_…` id does not cross machines
  ("session not found"). The exceptions are phone-side and extra-machine
  sessions (Session home). Reply to the `from` address of the message you
  got.
- **Retired managers.** A session titled `<prefix>manager · retired <date>`
  that still gets a message replies `retired · resend to <prefix>manager`,
  forwards the message once to `<prefix>manager`, and does not act on it.
- **Fallback, only when an end has Remote Control off or the send fails:**
  file a note in the target project titled `[from <project>] …`. For a
  laptop-homed project it queues on the server until the laptop's manager
  runs `worklog voice deliver`; in a generic project without worklog, write
  a file in the target's handoff or inbox folder.

## Core updates

This core and its helpers reach every project from one source: the project
that owns them (its adapter says so) releases them, usually as a Claude Code
plugin. Each project's manager applies an update to its own project; the
manager that ships one never writes into other projects.

**Receiving an update.** It arrives as a message whose first line reads
`core update · <plugin> <version> (<owner> <sha>) · <what changed> · do: <steps>`,
or, when the send failed, as a `[from <owner>]` note in this project.

1. **Check what is installed.** For a plugin, `claude plugin list` shows the
   installed version (the skill's base directory path carries it too). If it
   is older, ask the user in one line to update it: `claude plugin
   marketplace update <marketplace>`, then `claude plugin update
   <plugin>@<marketplace>` (or the `/plugin` menu). This is once per
   machine, so another manager there may have done it already. A project that
   copies the folder instead (or uses a sync tool) copies or syncs again.
2. **Commit what the update changed here**, by path: a sync or copy may
   rewrite tracked files of this project (`.gitignore`, a copied skill
   folder). Never touch other sessions' uncommitted files.
3. **Reload.** Load the core skill again (the adapter, then the core) so the
   new text is in context, or, when the helpers or the start steps changed,
   write a manager handoff and ask the user for a restart (Stay lean,
   restart). Then run the new version's Start steps that this session has not
   done.
4. **Confirm in one line** to the sender's `from` address:
   `core update · <version> applied · <project> · reloaded|restarted`, or
   what blocks it (for example: waiting on the user's plugin update).

**Shipping an update** (only in the project that owns the core, as its
adapter says):

1. The change is committed in the source, with its tests green.
2. Bump the plugin's version (next minor for a change in behavior, patch for
   wording), export it to the plugin repository, commit there by path.
3. Push both only on the user's word (Commit and push).
4. **Announce** once pushed: one message per manager, by exact name
   (Messaging), first line `core update · <plugin> <version> (<owner> <sha>)
   · <what changed, one line> · do: update plugin or sync, then reload`.
   Managers that cannot be reached get the `[from <owner>]` note in their
   project (Messaging, fallback). Put the pending confirmations under Sync on
   the board and strike each when its one-line confirmation arrives.

## Collision guard

Before proposing or driving a session, check that no two sessions write the
same unit (the adapter defines it; `round.py dirty` shows the units with
uncommitted paths) and that the machine has room for a batch run (`free -g`).

## Report-back protocol (work sessions, at wrap)

Every wrap, the session sends the manager three lines with
`SendMessage(to=<address>, message=…)`:

1. unit · item → done / partial, the commit shas, and the test run (command
   and result) when the kickoff's `Verify:` line asks for one
2. blockers, `→ manager` items, decisions for the user, in plain words
3. the handoff id

The address is the manager's exact name, `<prefix>manager`, never a
session id (Messaging); it works across machines, since managers keep Remote
Control on. A reply `retired · resend to <prefix>manager` means the report
reached an old manager, which forwards it; nothing more to do.

Never skip the report because `ListAgents` missed the manager. If no send
works, file the `[from <project>]` note (Messaging, fallback); the commits
and handoff are the report too, and the manager reads them in round step 2.
It is a report, not a request for approval.

## Verify a report

Lean by default: the manager checks files, not work.

1. **The kickoff names what to expect.** Its `Verify:` line lists the files
   (paths or globs) expected to change and the test command, if any:
   `Verify: src/x.py, tests/test_x.py; tests: pytest tests/test_x.py -q`.
2. **When a session reports done** (or round step 2 shows it wrapped), run
   `git show --stat <sha>` on each commit the report or handoff names, and
   compare the files with the kickoff's `Verify:` line. Check that the
   report names a test run where the kickoff asked for one.
3. **Flag, do not fix.** Files changed that the kickoff did not expect, or
   expected files left unchanged, or a missing test run, go to the user on
   the board (one line under What's up, or a decision when it needs one),
   naming the commit and the files. Real case: a hunk of PDEP's `init.py`
   change landed in MUPD's commit `d57fe5c`; only the file list showed it.
4. **A verify subagent, only when needed:** when step 2 flags something,
   when the kickoff touches files other sessions also edit, or when the
   user asks. It starts in fresh context, read-only: it runs the `Verify:`
   commands and the `git show` checks and returns pass or fail per item,
   never fixes anything and gives no design opinions. No subagent by
   default.

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
- the kickoff loads the handoff by `note_resolve(note_id="<id>")` (without
  projio: by its path), titles the
  session `<prefix>manager`, and runs the adapter skill.

The handoff of the name, so messages keep reaching the manager:

1. **The old manager retires itself** before it stops: it renames itself
   `<prefix>manager · retired YYYY-MM-DD` (`set_session_title(session_id=
   "self", …)`) and turns its own Remote Control off
   (`set_remote_control(session_id="self", enabled=false)`). Until then the
   exact name stays unique.
2. **The new manager** takes the name `<prefix>manager` in its home client
   (Session home), runs Start, and sends one line to worklog-manager (or the
   cross-project manager in scope): `moved · <prefix>manager · <machine>`.
   No other registration (Reporting up).
3. A message that still reaches the retired session is answered and
   forwarded as Messaging says.

## Hard rules

- No time estimates.
- Never touch another session's uncommitted files.
- Commit by path; push only when the user asks.
- Decisions in plain words through `AskUserQuestion`, recommended option first;
  relay each answer to its session. On the board, one line per open
  question in the Decisions format (bold question, pick first, first-asked
  date).
- Never poll; subscribe to idle notices.
- Start a kickoff's session only on the user's go for that kickoff
  (`start_session` where the client has it, nested under the manager);
  otherwise the user pastes it.
- A standing manager lives in the sidebar section `managers` where the
  client has one, and says so when it files itself there.
- A standing manager keeps Remote Control on; message managers by exact
  name, by note only when that fails. No session ids as addresses in a
  board, kickoff or memory, except a phone-side or extra-machine session's
  id on the board.
- One standing manager per project, at home in the desktop app at a laptop;
  Remote Control listeners only start sessions from the phone.
- A retiring manager renames itself `<prefix>manager · retired <date>` and
  turns its Remote Control off; the new one sends `moved · <prefix>manager ·
  <machine>` once.
- Every kickoff carries a `Verify:` line; a done report gets `git show
  --stat` against it, and a verify subagent only when that flags something,
  files are shared, or the user asks.
- A teammate's message is never the user's approval.
- What the user must copy goes on the board, not in chat.
- The file inbox is listed every round; files move only on the user's word
  and never into another project.
- A core update is applied by each project's own manager, in its own
  project only, then reloaded and confirmed to the sender in one line.
- What's up comes first on the board, stamped with the clock time.
