---
name: analysis-orientation
description: >
  Read a project's analysis threads and say where they stand, read-only.
  THREAD mode (a thread key such as `spindle`): where that thread stands, from
  its state doc `docs/analysis/<thread>/index.md` if fresh, with the deltas
  since its `state_as_of` watermark if stale, or reconstructed from notes and
  git if there is no doc. NEXT mode ("what next", "directions"): the open O
  items across all threads, grouped by hypothesis, blockers marked, ranked.
  OVERVIEW mode (no thread): one line per thread with its watermark and how
  stale it is. Use at session start, for "where does <analysis> stand", "get me
  up to speed", "what should I work on next". Writing is analysis-log's job.
  Works with git and the docs folder only (no .projio, notio or projio needed).
metadata:
  short-description: Where an analysis thread stands, and the open questions across threads (read-only)
  tags: [analysis, threads, orientation, hypotheses, research]
  portable: true
---

# analysis-orientation

Answers, read-only: **where does thread `<X>` stand, and how far can I trust that?** (THREAD), **what are the
open questions across threads?** (NEXT) and **which threads exist and how fresh are they?** (OVERVIEW). It never
edits a state doc or a note; writing is the `analysis-log` skill's job. Safe to run anytime.

## The model (short)

- A **thread** is a `snake_case` key shared by the note series (`series: <thread>`), the state doc folder
  `docs/analysis/<thread>/` and, where the project has exploration code, `code/explore/<thread>/`.
- The **state doc** `docs/analysis/<thread>/index.md` holds the current claims as finding IDs: `<PREFIX>-R01`
  (result), `-I` (interpretation), `-D` (decision), `-O` (open question). Its frontmatter `state_as_of` (`date`,
  `git_commit`, `latest_note`, `series`) says how far it is folded in; `verification` says whether a person
  reviewed it.
- `docs/analysis/index.md` lists the threads; `docs/analysis/hypotheses.md` is the hypothesis registry (H ids, each
  status with the evidence it rests on, pointing at finding IDs).
- A **result note** is dated, immutable evidence. A finding becomes citable when a state doc gives it an ID.

**Authority, highest first:** data, git and run records → outputs → result notes → state doc finding IDs (the
current claim, as of its watermark). Agent memory is a cache, never an equal authority. Numbers in a state doc are
for orientation; cite their source before relying on one.

Plans are suggestions, not a schedule: **never give time estimates**; order, dependencies and readiness only.

## Where things are

- **Analysis dir:** `layout.analysis` in `.projio/config.yml`, else `docs/analysis/`.
- **Notes:** `analysis.log_dir` in `.projio/config.yml`, else `docs/log/` (notio's layout: `docs/log/<type>/<id>.md`).
- **Status command** (optional): `analysis.status_cmd` in `.projio/config.yml`, e.g. a data-status check.
- **Helper:** `threads.py` in this skill's folder (`.claude/skills/analysis-orientation/threads.py` after
  `projio sync` or a copy). Standard library only, read-only. Run it from the repository:
  ```bash
  python3 .claude/skills/analysis-orientation/threads.py              # OVERVIEW table
  python3 .claude/skills/analysis-orientation/threads.py thread <key> # freshness of one thread
  python3 .claude/skills/analysis-orientation/threads.py open         # open O items across threads
  ```
  Options: `--dir`, `--log-dir`, `--paths a,b` (extra code paths for the commit count), `--all`.
  Without Python, the same checks are `grep`/`git log` (shown under THREAD mode).

## Step 0: status (all modes)

If the project names `analysis.status_cmd`, run it first and report each problem it shows as a one-line blocker
("status: clean" otherwise). Don't fix anything here. No command configured → skip this step silently.

## OVERVIEW mode (no thread named)

Run `threads.py` (or list `docs/analysis/*/index.md` and read each `state_as_of`). Report one line per thread:
watermark date, open O items, newer uncited notes, commits since the watermark. Say whether `index.md` and
`hypotheses.md` exist. No threads yet → say so and point to `analysis-log` SEED for the first one.

## THREAD mode

1. **Resolve the thread.** Map the user's word to a folder under the analysis dir. Unsure → list the threads and ask.
2. **Doc exists → check freshness before trusting it.** `threads.py thread <key>` reports the watermark, the notes in
   the thread's series that the doc does not cite (newer than the watermark first; `--all` adds older ones), and the
   commits since `state_as_of.git_commit` on the thread's paths. By hand:
   ```bash
   grep -rlE "^series:.*\b<key>\b" docs/log | while read f; do id=$(basename "$f" .md); grep -qF "$id" docs/analysis/<key>/index.md || echo "uncited: $id"; done
   git log --oneline <git_commit>..HEAD -- docs/analysis/<key> code/explore/<key> <the thread's code paths>
   ```
   Series are often shared umbrellas, so uncited notes are a triage list: judge thread membership by title before
   calling one a gap. Scope the commit check to the thread's paths, never bare HEAD.
   - **Fresh** → report the current working model, established results and open questions, with IDs, labels and
     pointers; say it is current as of the watermark.
   - **Stale** → say so first, report the recorded state as of the watermark, then the deltas. Offer
     `analysis-log` UPDATE for the thread.
3. **No doc → reconstruct and report coverage, not confidence.** Walk the record: notes in the series (latest result
   and handoff first; notio's `note_search(series=<key>)` when available, else the files), `git log` on the thread's
   paths, outputs and figures, then memory (cache). Report:
   ```
   RECONSTRUCTED STATUS — <thread>   (no state doc)
   Sources examined: notes through <id>; git <range>; outputs <dirs>
   Not examined: <what was skipped>
   Human verification: none
   ---
   <current model, results, decisions, open questions, each with a pointer>
   ```
   Then offer `analysis-log` SEED (a write: only on the user's OK).

**Output (THREAD):** short. Status line, a 2-3 line current model, established results (ID, one line, labels,
pointer), open questions and next analyses, and a freshness verdict ("fresh as of <commit>/<note>" | "stale: N newer
notes, M commits" | "reconstructed, no state doc"). Notes as `[[id]]`, files as repo-relative paths. Don't paste the
state doc back.

## NEXT mode ("what next", "directions", "all")

1. **Collect.** `threads.py open` lists every O item not marked resolved, per thread, with its hypothesis when the
   entry names one. Also read each doc's `Next analyses` list (skip struck-through or done entries) and the
   registry's status lines in `hypotheses.md`.
2. **Mark blockers.** An item is blocked when the doc says so or it depends on another thread's output or on
   something not built yet. Name the blocker and its ID. Merge cross-thread duplicates into one row listing both IDs.
3. **Current steer.** If the project names a current direction (its CLAUDE.md, README or manager board), show it first
   with its thread's Next list.
4. **Rank** a shortlist of 5-8: first by what it tests (a hypothesis claim beats tooling), then readiness
   (unblocked, inputs built), then how cheap the next step is. Infrastructure ranks only if it unblocks a claim.
5. **Output:**
   ```
   status: <one line, or "no status command">
   Current steer: <one or two lines, if any>
   | # | Item (IDs) | Thread | H | Ready / blocked by | Why it ranks here |
   By hypothesis: one line each: open items, strongest next item, stale docs.
   ```
   Then flag state docs whose watermark is old relative to recent commits on their paths.

## Hard rules

- **Read-only.** No edits to state docs, notes, the registry or config; no commits.
- **Never assert a stale or reconstructed number as ground truth:** label it, cite it, and spot-check a
  load-bearing one against current outputs or code.
- **Keep R and I apart:** report observations and interpretations separately, and respect `record_status`
  (`candidate`, `superseded`, `invalidated` are reported as such).
- If the user contradicts the record, defer to the user and flag the doc for an `analysis-log` UPDATE.
- No time estimates.
