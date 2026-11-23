---
name: manager-setup
description: >
  Set up a standing manager session for a project, projio or not: ask the
  title prefix and what the manager is for, survey the repo read-only, write
  the manager config and the `<prefix>manager` adapter skill from templates,
  install the project-manager core, create the board with the first kickoff and
  write the first manager handoff. Use when the user asks to "set up a manager"
  for a project, or opens a session titled `<prefix>manager-setup`. Works with
  git and a handoff folder only (no .projio, notio or projio needed).
metadata:
  short-description: Set up the project-manager adapter, board and first kickoff in any project
  tags: [manager, orchestration, setup, adapter]
  portable: true
---

# manager-setup

Creates a project's manager from the `project-manager` core, so every manager
is set up the same way instead of from a hand-written kickoff. Read the core
(`project-manager` skill) first: this skill writes its adapter and does not
repeat its rules.

The session is titled `<prefix>manager-setup`; when the prefix is not known
yet, title it once step 1 settles it.

Templates are in this skill's folder (the base directory Claude Code shows on
load; `.claude/skills/manager-setup/` after `projio sync` or a copy):
`templates/manager.yml`, `templates/adapter.md`, `templates/handoff.md`. Fill
every `{{…}}` placeholder; a placeholder with nothing to say becomes a short
"none" line, never stays in the file.

## When to use

- A project has sessions to coordinate and no `<prefix>manager` yet.
- An existing manager drifted from the core (redo steps 3-5 against its
  current files, keep the user's dated decisions).

## Workflow

1. **Ask** (one `AskUserQuestion` batch, recommended option first):
   - the **prefix**: short, ends in `-`, unique across projects. List the ones
     already in use to pick from: the core names `pix-`, `lit-`, `inf-`,
     `infraslow-`, `projio-`; add titles ending in `manager` from `ListAgents`
     and the client's session list (`list_sessions`), and the other projects'
     configs if a cross-project registry is at hand. Propose one derived from
     the repo name.
   - **what the manager is for**: the kinds of work it tracks (issues from
     other projects, analysis runs, releases, a paper…). This becomes the
     adapter's description, so it must say when to use it.
   - the **working copy**: which clone of the repo sessions work in (when
     there are several, e.g. a shared and a personal one).
   - **push rules**: push only when the user asks (default), or a standing
     approval the user states now (record it dated in the adapter).
   Then title the session `<prefix>manager-setup`.

2. **Detect the layout and survey, read-only.**
   - Layout: **projio** when `.projio/` exists (config `.projio/manager.yml`,
     adapter in `.projio/skills/<prefix>manager/`, installed by `projio sync`);
     else **generic** (config `.claude/manager.yml`, adapter in
     `.claude/skills/<prefix>manager/`). Whether the `projio` command is on
     PATH decides only how the core is installed (step 5).
   - Units: top-level folders, `git log --name-only` of recent commits (which
     paths change together), subrepos or subdatasets (`git submodule status`).
     A unit is what one session owns at a time.
   - Notes: folders where other projects drop notes (`docs/log/issue`,
     `docs/log/idea` in projio; an `inbox/` or `issues/` folder elsewhere),
     and how they name their sender (a `[from <project>]` title, a body line).
     None is a fine answer.
   - Handoffs: an existing handoff folder; else propose `docs/handoffs` (a
     projio project uses `docs/log/handoff` and notio's handoff type).
   - Opener and wrap: the skills sessions start and end with (`projio-orient`
     and `session-wrap` in projio; in a generic project, the handoff by path
     to open and the core's report-back protocol to close).
   - Protected processes: run the core's `procs.py` (read-only) and note
     long-lived servers that must never be proposed for a kill.
   Show the user the proposed units, folders and protected processes, and
   adjust before writing.

3. **Write the config** from `templates/manager.yml` to the layout's path.
   Leave out keys that equal the defaults only when the file stays clear;
   keep `prefix`, `adapter_skill`, `handoffs.dir`, `board.path`, `units`.
   Create the handoff folder if missing (with a `.gitkeep`).

4. **Write the adapter skill** `<prefix>manager` from `templates/adapter.md`,
   sections in this order: Names · Board · Units of work · What belongs to the
   sessions · Collision unit · Integration · project-specific round sections ·
   Not the manager's. Only what is specific to this project: **no copies of
   core rules** (states, levels, commit and push, decisions, report-back). The
   frontmatter `description` says when to use it.

5. **Gitignore the board and install the core.**
   - Add the board's folder (`.scratch/`) to `.gitignore` unless
     `git check-ignore -q <board>` already passes. In projio, `projio sync`
     puts `/.scratch/` in the `# >>> projio >>>` block; never edit that block
     by hand (sync rewrites it). `.scratch/` is the recommended home for all
     scratch (drafts, reports, viewable outputs), since the Claude app's file
     pane opens only files inside the project; it is never required.
   - projio layout with `projio` on PATH: `projio sync` (copies the core,
     this skill and the adapter into `.claude/skills/`). It also copies other
     skills; tell the user if other sessions have uncommitted skills.
   - Otherwise: copy the core's folder next to this one,
     `cp -r <this skill's folder>/../project-manager .claude/skills/` (and
     this skill's folder, so the project can redo the setup). The helpers are
     stdlib Python 3.9+; PyYAML is optional.
   - Check: `python3 .claude/skills/project-manager/round.py config` names
     the config, the layout, the folders found and "gitignored" for the board.

6. **Create the board and the first kickoff.**
   `python3 .claude/skills/project-manager/round.py board`, then under
   Delegate add the kickoff that starts the standing manager, coded (e.g.
   `MGR`), tagged **independent**, its prompt in a ```` ```text ```` block
   whose first line is ``Title this session `<prefix>manager`.`` (the
   standing manager's title carries no code), then: turn this session's
   Remote Control on if it is off (`set_remote_control(session_id="self",
   enabled=true)`; the app may show an approval card) and say so in one line,
   unless the user said otherwise; read the first manager handoff (step 7) by
   path (or `note_resolve` in projio), load the `<prefix>manager` skill, run a
   round, stay open as observer and dispatcher, the push rule. Write Delegate's **Recommended now** block
   (`MGR`: start the standing manager) and fill What's up and Sync (this
   setup session's id).

7. **Write the first manager handoff** from `templates/handoff.md` (in
   projio: a notio note of type handoff) with `series: manager`,
   `status: open`, `git_commit: <HEAD sha after step 8's commit>`. What
   finished: the setup. Decisions the user made: prefix, purpose, working
   copy, push rule (dated). Open: whatever the survey found for the first
   round. The kickoff snippet matches the board's.

8. **Commit by path**: the config, the adapter skill, the handoff folder,
   `.gitignore`, and (generic) the copied skill folders if the project keeps
   `.claude/skills/` in git. `git commit -m "…" -- <paths>`; amend nothing
   another session wrote. Then set the handoff's `git_commit`, commit it.
   No push unless the user's push rule says so.

9. **Report**: the board path (open it with `show_pane`), the kickoff code to
   start, and anything left for the user.

## Packaging (for projects without projio)

`project-manager` and `manager-setup` are plain folders: copy both into a
project's `.claude/skills/` (or `~/.claude/skills/` for every project). The
helpers import nothing from projio. To ship them as a Claude Code plugin, a
repo with `.claude-plugin/plugin.json` and the two folders under `skills/`
works; the helpers are then run from the plugin's folder, the base directory
Claude Code shows when the skill loads.

## Hard rules

- Survey read-only; write only the files in steps 3-8.
- Never touch another session's uncommitted files; commit by path.
- No core rules in the adapter: it names the project's specifics and points
  to the core.
- Every kickoff's first line is ``Title this session `<…>`.``; a work
  session's title carries the kickoff code, `<prefix><unit> · <CODE> · <item>`.
- The standing manager keeps Remote Control on and messages other machines
  by exact session name (the core's Messaging); a `[from <project>]` note
  only when an end has Remote Control off or the send fails.
- Push only by the push rule the user gave.
