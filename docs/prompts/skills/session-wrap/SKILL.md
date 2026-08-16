---
name: session-wrap
description: >
  End-of-session routine for any projio project: commit this session's coherent
  code/docs (without sweeping in other sessions' WIP or regenerated derivative
  data), run the right verification gates, write a handoff note plus a
  ready-to-paste kickoff prompt, and update cross-session memory so the next
  fresh agent resumes in one paste. Use when finishing a work session or when the
  user says "wrap up / prepare for next session / commit and hand off".
metadata:
  short-description: Clean session boundary, commit, handoff note, kickoff prompt
  tags: [session, handoff, commit, workflow]
  tooling:
    mcp:
      - server: projio
        tools:
          - git_status
          - datalad_status
          - note_types
          - note_create
          - note_read
          - note_resolve
          - note_latest
          - project_context
          - ecosystem_status
---

# session-wrap — clean session boundary + handoff

Goal: leave the repo and the next agent in a state where work resumes in **one
paste**. Follow the steps in order, but use judgment. This is not fully
mechanical, and the specifics (datalad vs plain git, which paths are yours, which
verify gates matter) depend on the project.

This is the generic ecosystem version. A project with unusual structure (a daemon
that mutates the tree, an MCP rooted at a different repo, a bespoke handoff
mechanism) should fork this into a tailored local copy:

```
projio skill new session-wrap --from-ecosystem session-wrap
```

That drops an editable copy under `.projio/skills/session-wrap/` which overrides
this one; edit it to encode the project's quirks.

## 0. Read the ground truth first

```
project_context()        # project kind, enabled packages, code tiers, config paths
git_status()             # branch + dirty/untracked paths (projio MCP, repo-rooted)
datalad_status()         # is this a datalad dataset? any subdatasets? (empty/err → plain git)
```

`datalad_status` tells you which world you are in. If it reports a dataset with
subdatasets, treat `derivatives/*` (or other subdatasets) as **data that lives in
its own dataset, not the parent git**. If it is a plain git repo, there is no
parent `datalad save` and no subdataset data to keep out of your commits.

## 1. Assess the working tree — separate yours from everyone else's

The tree is almost always dirty from prior or concurrent work. Classify EVERY
dirty or untracked path into one of:

- **This session's code/docs** → commit to the repo (step 3).
- **This session's derivative / data outputs** (parquet, NWB, figures, large
  binaries under `derivatives/*` or a data dir) → if they live in a datalad
  subdataset, they do NOT belong in the parent git; leave them, or
  `datalad_save(dataset=<subdataset path>)` **inside that subdataset** only if the
  user wants them persisted. Never `git add` a subdataset's data into the parent.
  In a plain repo, do not blob large regenerated outputs into git history either.
- **Owner / other-session WIP** (`.projio/` internals, a `*.lock` you did not
  change, unrelated `code/pipelines/*`, subdataset pointer bumps, other `docs/`)
  → **DO NOT touch.**

`git diff <file>` anything ambiguous before staging. If you reverted or disrupted
another session's file, say so loudly in the handoff.

## 2. Verify (capture the state the handoff will quote)

Run only the gates relevant to what changed. Use the project's own runner (check
`project_context()` / `runtime_conventions()` for the env; often `pixi run …` or
`conda run -n <env> …`):

- **Python edits** (`code/utils`, `code/lib`, pipeline scripts) → run the test
  suite or the targeted module, plus a fast `python -m py_compile <edited files>`
  syntax gate.
- **Config / Snakefile edits** → `yaml.safe_load` the config, and where cheap a
  `pipeio_run(flow=…, dryrun=True)` (never invoke `snakemake` / `conda run`
  manually).
- **Algorithm / detector edits** → a quick equivalence or smoke check on
  synthetic or one real input, with actual numbers to quote (not "ran without
  error").
- **Docs / mkdocs / bib / notebooks touched** → build the site (`site_build()` or
  `make build`) so it is healthy; never leave or push a broken site.

Record pass counts, dry-run OK, and key numbers. Note any long background runs
still in flight (the poll command and how to check).

## 3. Commit your coherent units

- Stage **explicit paths only — NEVER `git add -A` / `git add .`**. A blanket add
  scoops up other sessions' WIP and any subdataset data.
- One commit per coherent change (e.g. one per flow or feature), with clear
  conventional-commit subjects. End every commit body with:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- Commit on the current branch. **Do not push** unless the user asks. If you do
  push and docs changed, build the site first (CI often copies the built site
  from the working tree).
- Datalad projects: persist derivative data via `datalad_save` inside the
  subdataset only if asked; the parent commit should reference code/docs, not
  regenerated outputs.

## 4. Write the handoff note

Discover the right note type first — do not assume one exists:

```
note_types()             # which note types does THIS project define?
```

Prefer a dedicated **handoff** type if the project has one. Otherwise fall back to
the closest available (`agent-interaction`, `result`, or a flat file under the log
dir). Create it:

```
note_create(note_type="<handoff|agent-interaction|...>", title=…, owner=…,
            frontmatter='{"branch":…, "status":"hold|mergeable"}', body=…)
```

`note_create` returns the note's path/id — **capture it**. The kickoff prompt must
point at THIS note by id, not "the latest": other sessions can post concurrently,
so `note_latest(...)` is racy. Required sections in the body:

- **How to resume** — branch, and whether a restart is needed for new MCPs/tools.
- **What shipped this session** — commit list (newest first) + the verify state.
- **⚠️ Uncommitted / in flight** — owner and other-session WIP (don't touch); long
  background runs still going (IDs + poll command); data outputs not persisted.
- **What's parked/broken** — with the *diagnosis* (how you know), not just
  "broken".
- **New tooling/capabilities** (skills, MCP tools, config entries) + restart needs.
- **Prioritized next steps.**
- **A minimal kickoff snippet** — one or two lines: read this note by its specific
  path/id (`note_read` / `note_resolve(note_id="<this note's timestamp>")`, NOT
  `note_latest`) + "continue from Prioritized next steps" + the branch. Do NOT
  restate the note's content in the snippet; the note carries the detail, the
  snippet is just a pointer.

## 5. Update cross-session memory (if you keep it)

If this project maintains cross-session memory files (Claude Code memory under
`~/.claude/projects/<slug>/memory/`), append a dated update to the relevant
`project_*.md` (current state + pointer to the new handoff note) and keep the
`MEMORY.md` index line current. Memory is for durable facts and behaviors;
research findings belong in notio result/idea notes, not memory.

## 6. Report

State: the commits made, the handoff note path (from `note_create`), that memory
was updated, and any background runs left polling. **End by surfacing the minimal
kickoff snippet itself** (the literal one or two lines pointing at this handoff's
path/id) in a copy-paste block, so the user drops it straight into a fresh
session with no scrolling back to find it.

## Guardrails

- **NEVER `git add -A` / `git add .`** — explicit paths only.
- **Never `git add` subdataset data into the parent** — datalad projects only.
- **Point the kickoff at this note by id**, never `note_latest` (racy).
- **Do not push** unless asked; if you push with docs changes, build the site
  first.
- **Do not touch owner / other-session WIP** — classify it and leave it.
