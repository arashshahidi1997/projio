---
name: projio-manager
description: >
  projio's manager: the adapter for the project-manager core. Use when the user
  asks for an overview of projio work (issues and ideas from other projects,
  sessions on the subsystems, what to integrate or release next), or opens the
  standing `projio-manager` session. Loads the core first.
metadata:
  short-description: projio adapter for the project-manager core
  tags: [manager, orchestration, adapter]
---

# projio-manager: the adapter

**Load the core first:** the `project-manager` skill (`skill_read("project-manager")`
or `.claude/skills/project-manager/SKILL.md`). This file only fills in what is
specific to projio. Machine keys are in `.projio/manager.yml`.

## Names

- Standing manager: `projio-manager`.
- Work sessions: `projio-<unit> · <item>`, for example `projio-biblio · docling slim`
  or `projio-core · skill sync drift`. Units are those in `.projio/manager.yml`.
- Opener: `projio-orient` plus the issue or idea notes by id
  (`note_resolve(note_id=…)`). Wrap: `session-wrap`, which ends with the
  three-line report to `projio-manager` when it runs.

## Board

`.scratch/projio-manager-board.md` (the default; `.scratch/` is gitignored).
Refresh with `round.py board`, open it with
`show_pane(pane="file", path=".scratch/projio-manager-board.md")`. Other
managers in Sync: pix-manager (gamma2), lit-manager and worklog-manager (laptop).

## Units of work and where their state lives

| Unit | State lives in |
|---|---|
| An issue, or a small batch of issues on one subsystem | the note in `docs/log/issue/` (`status:`, progress sections); the commits that cite it |
| An idea taken to a spec | the note in `docs/log/idea/`; the spec in `docs/specs/` |
| A package release | `packages/<pkg>` version (`__version__` or pyproject) against its newest tag; its CHANGELOG |
| A projio release | `pyproject.toml` version, `CHANGELOG.md` `## Unreleased`, the tags |
| A deliverable (talk, handbook, starter) | `docs/deliverables/<…>` and its handoff |

Status vocabulary for notes: open, partial, scheduled (active); done, resolved
(closed; both are in use).

**Incoming.** Notes from other projects land in `docs/log/issue/` and
`docs/log/idea/`. Few carry a `[from <project>]` title; most carry only a
`### Source context: <project>` line in the body. `incoming.py` reads both.
They often arrive uncommitted: committing the ones the user approves is a
manager write.

**How issue work is recorded.** A `feat:` or `fix:` commit, then
`docs(issue): resolve|progress on <timestamp> (…)` that edits the note
(status, `updated:`, a progress section). That commit message is the citation
`incoming.py` shows.

## What belongs to the sessions (the manager never edits)

- code under work in `src/projio/` and in `packages/<pkg>/`;
- a spec or a deliverable a session is writing;
- an issue note a session is resolving (the manager may set status only when
  the session has wrapped and its commits show the fix).

## Collision unit

One subdataset (`packages/<pkg>`) per session. In core, these files are
shared by most changes, so two sessions touching them need sequencing:
`src/projio/mcp/server.py`, `src/projio/init.py` (`_generate_claude_md`),
`CLAUDE.md`, `CHANGELOG.md`, `pyproject.toml`.

## Integration (only when the user asks)

1. Tests green: `PYTHONPATH=src python -m pytest tests -q` in core, and the
   package's own tests for a touched package.
2. Package work is committed inside its subdataset first; then the parent
   commits the pointer (`packages/<pkg>: <version or summary>`).
3. The uv tool env has every package editable, so code changes are live.
   Tell the user when a refresh is needed: new dependencies, entry points or
   a version bump need `uv pip install --python <projio uv env>/bin/python3
   --no-deps -e packages/<pkg>`; new MCP tools need the MCP servers restarted
   in the consumer sessions.
4. Tag or release only when the user asks (projio: `release: vX.Y.Z` bumps
   pyproject and CHANGELOG; RELEASE.md has build and upload).
5. Gaps in consumer projects' environments are reported to the user, not
   fixed from here.

## projio-specific round sections

After the core round, add:

- **Untagged releases:** per package, the version in the source against the
  newest tag (`git -C packages/<pkg> describe --tags --abbrev=0`); list those
  with a version ahead of their tag.
- **Open by sender:** the incoming list counted by sender, so the user sees
  where the load comes from.

## Not the manager's

Writing fixes, specs or tests; choosing which subsystem owns a feature (ask
the user); releasing without the user's word.
