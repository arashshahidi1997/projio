---
name: analysis-log
description: >
  Record a finding and keep an analysis thread's state doc
  `docs/analysis/<thread>/index.md` current. RECORD: write the result note
  (dated, immutable evidence with runs and a hypothesis ID, no status) and add
  or update the finding ID that cites it. SEED: create a new thread's state doc
  from notes and git (and `docs/analysis/index.md` and `hypotheses.md` when the
  project has none). UPDATE: fold a session's results, decisions and open
  questions into an existing doc with stable IDs. Use when the user says
  "record this finding", "write a result note", "start / seed a thread for X",
  "update the analysis doc", at the end of an exploration, or at session wrap
  for a thread that advanced. The reader is analysis-orientation. Works with
  git and the docs folder only (no .projio, notio or projio needed).
metadata:
  short-description: Result notes and analysis-thread state docs (RECORD, SEED, UPDATE)
  tags: [analysis, threads, results, hypotheses, research]
  portable: true
---

# analysis-log: result notes and the thread state doc

How findings flow:

```
run (pipeline or exploration) ──► result note (dated, immutable, runs, no status)
                              ──► finding ID in docs/analysis/<thread>/index.md   ◄── the current claim
```

The state doc says *what we currently believe*; it cites result notes, figures and commits and never copies them.
Three modes: RECORD (a new finding), SEED (no doc yet), UPDATE (doc exists). RECORD usually runs with UPDATE. The
reader half is the `analysis-orientation` skill; read its "The model" section if the terms are new.

## Where things are

- **Analysis dir:** `layout.analysis` in `.projio/config.yml`, else `docs/analysis/`.
- **Notes:** notio when the project has it (`note_create`, `note_search` MCP tools, or the `notio` CLI); otherwise
  plain files under `docs/log/<type>/` (`analysis.log_dir` in `.projio/config.yml` overrides `docs/log`).
- **Templates** in this skill's folder (`.claude/skills/analysis-log/templates/` after `projio sync` or a copy):
  `state-doc.md` (a thread's `index.md`), `analysis-index.md` (`docs/analysis/index.md`), `hypotheses.md` (the
  registry), `result-note.md` (for projects without notio). Fill every `{{…}}` placeholder; the HTML comments are
  examples of the entry format and may stay until the first real entry replaces them.
- **Freshness helper:** `.claude/skills/analysis-orientation/threads.py thread <key>` lists the notes and commits
  since a doc's watermark (read-only).

## When a thread deserves a state doc

Only at a real handoff boundary: something a new person would need to "get up to speed on", with its own history,
current state, open decisions and outputs. A one-off diagnostic lives inside an existing thread. If unsure, ask
before seeding. The thread key is `snake_case`, shared by the note series, the doc folder and `code/explore/<key>/`
where the project has exploration code. The ID prefix is a short uppercase form of the key (`topography` → `TOPO`),
unique across the project's threads.

## The record contract (all modes)

- **IDs are stable and namespaced:** `<PREFIX>-R##` observed result · `-I##` interpretation · `-D##` analysis
  decision (ADR style) · `-O##` open question. Keep observation (R) apart from interpretation (I): a summary never
  turns "we observed X" into "X means Y".
- **I is never a to-do.** An I item is an explanatory claim beyond the observations (mark it *untested* when it is).
  **Suggested work is only ever an O item:** a question, a proposed test, or an analysis idea phrased as the
  question it would answer (a longer idea can live in an idea note linked from it). An untested I that needs a test
  gets an O item for that test.
- **Every finding cites evidence:** a result note `[[result-…]]` (preferred), plus a figure path or commit. No
  resolvable pointer → don't add the entry.
- **Orientation numbers only:** scoped and pointed ("~X % higher, subject 5 session 10, see [[result-…]]"). Numbers
  for a manuscript come from the project's results pipeline, not from the state doc.
- **Three labels per R and I**, not a confidence score:
  `evidence: exploratory | single-session | multi-session | cohort-replicated | independently-validated` ·
  `record_status: candidate | active | superseded | invalidated` · `review: agent-extracted | human-reviewed`.
  (The `evidence` scale fits session-based data; a project may name its own levels in the doc's `labels:` block.)
  Decisions use `status: accepted | superseded` (+ `superseded_by:`).
- **Hypothesis link:** each finding names the hypothesis it bears on (an H id from `hypotheses.md`) or `—`.
- **Literature:** ground R, I and D entries in prior art by citekey; resolve each citekey against the project's
  bibliography and never invent one. Under an O item, a `Literature before (<date>)` sub-bullet when work starts
  (expected values and traps, from the hypothesis's **Literature** line in the registry) and a
  `Literature after (<date>)` one when it yields a result (our value vs the field's). When the O item closes into an
  R or I, carry the comparison into `Literature grounding`.
- **Promotion is asymmetric:** add `candidate` entries freely; `active` or `accepted` needs stated evidence
  criteria or the user's review. When unsure, leave `candidate` and say what would promote it.
- **Never rewrite history:** a wrong entry becomes `superseded` or `invalidated` with `superseded_by:`. A result note
  is never edited after the fact; a correction is a new note. Wording-only edits for plain language (numbers, runs
  and conclusions untouched) are allowed and recorded as a `Wording revised <date>` line.
- **Plain language:** a result note opens with 2-3 plain sentences (what was measured, on what, what came out).
  Each measure or method is defined in words the first time it appears; code names may follow in backticks. A
  finding ID is a pointer, never the explanation. Figures cited get titles, axes and legends in words.
- **Watermark**, kept current in the doc's frontmatter:
  ```yaml
  state_as_of: {date: <today>, git_commit: <short HEAD>, branch: <branch>,
                latest_note: <newest note id folded in>, series: [<key>, …]}
  verification: {synthesis: agent-extracted, human_reviewed: false}
  ```

**Doc skeleton** (state first, history at the bottom), as in `templates/state-doc.md`: Scientific question →
Current working model (2-4 lines) → Established results (R) → Interpretations (I) → Literature grounding → Analysis
decisions (D) → Rejected / superseded → Open questions (O) → Next analyses (priority order, no time estimates) →
Evidence index (notes, newest first).

## RECORD mode: the result note, then the finding ID

Record only stable, repeatable findings. A mid-loop hunch stays in chat or an idea note.

1. **Find the runs.** The run id(s) of the outputs the finding rests on, from the project's provenance records when
   it keeps them. No run record → cite the commit of the producing code and say so.
2. **Write the note.** With notio: `note_create(note_type="result", title=…, frontmatter=…, body=…)`. Without:
   copy `templates/result-note.md` to `docs/log/result/result-<user>-<stamp>.md` (stamp from
   `date +%Y%m%d-%H%M%S-%6N`, user from `git config user.name`, lowercase). Frontmatter:
   ```yaml
   series: <thread key>
   hypothesis: [H1]          # or []
   refs: [<handoff/idea ids>]
   runs: [<run id>, …]       # or [code <sha>] when there is no run record
   subjects: [...]           # what the data are: subjects, sessions, datasets
   figure: <path to the main figure>
   metric: "<what was measured>"
   value: "<headline number with its denominator>"
   ```
   No `status`, `question` or `milestone` field (the finding ID carries the status; an older notio template may still
   have the last two: leave them empty). Body: plain summary → Result → Interpretation → Caveats → Sources (producing
   code, output folder, runs). Numbers with denominators ("6 of 58 cells, subject 3 day 4"), not narrative.
3. **Add or update the finding ID** in the state doc (UPDATE below): the entry cites the new `[[result-…]]`, and the
   note goes into the Evidence index. If the thread has no doc yet, SEED first (with the user's OK).
4. If an exploratory notebook or script concluded with this finding and the project marks such headers, set it to
   concluded with the finding ID and note id.

## SEED mode (no doc yet)

1. **Confirm the thread boundary** with the user, the key and the ID prefix. Resolve the series (usually the key)
   and the thread's code and output paths.
2. **Project scaffold, if missing:** when the analysis dir has no `index.md` or `hypotheses.md`, create them from
   `templates/analysis-index.md` and `templates/hypotheses.md`. Never overwrite existing ones.
3. **Assemble the record:** notes in the series (latest result and handoff first; `note_search(series=<key>)` with
   notio, else `grep -rlE "^series:.*\b<key>\b" docs/log`), `git log` on the thread's paths, output figures and
   tables, agent memory (cache only).
4. **Write `docs/analysis/<key>/index.md`** from `templates/state-doc.md` with stable IDs, labels and pointers, and set
   the watermark. Everything synthesized without the user's sign-off is `review: agent-extracted`; be conservative
   on status. A fresh thread with no findings yet keeps the Scientific question, a one-line working model and its
   first O items.
5. **Register it:** add a row to `docs/analysis/index.md`, and add the thread to the owning-thread column of the
   hypotheses it bears on in `hypotheses.md` (status unchanged until a finding ID supports a change).

## UPDATE mode (doc exists)

1. **Diff against the watermark:** notes in the series newer than `state_as_of.latest_note` that the doc does not
   cite, new figures and tables, commits on the thread's paths since `state_as_of.git_commit`
   (`threads.py thread <key>` lists them).
2. **For each new or changed finding:** add an R, I, D or O entry (as `candidate`), or update an existing entry's
   labels and evidence. Supersede rather than edit away a prior claim. A resolved O item stays, marked
   `status: resolved → <ID>`, never deleted. Keep `Next analyses` in step with the open O items.
3. **Registry:** if a finding changes what a hypothesis rests on, update that hypothesis's status line and finding
   IDs in `hypotheses.md` (status from finding IDs only; new work stays an O item in the doc, never a to-do there).
4. **Bump the watermark.** Leave `human_reviewed: false` unless the user confirms a review.
5. **Keep it lean:** this is state, not a changelog; git and notes hold the timeline.

## Report

The result note id(s), the doc path, the IDs added, updated or superseded, and the new watermark. Two or three lines.

## Hard rules

- Writes only result notes, the thread's state doc, `docs/analysis/index.md` and `hypotheses.md`. Never another
  thread's state doc: a result that bears on another thread goes to that thread as an idea note
  (`[from <thread>] <target ID>: …`) for its next session to fold in.
- Never edit a result note after the fact (wording-only exception above); never delete an ID.
- No finding without a resolvable pointer; no invented citekeys; no time estimates.
- Commit by path when the project's session routine commits (`session-wrap`); this skill itself does not push.
