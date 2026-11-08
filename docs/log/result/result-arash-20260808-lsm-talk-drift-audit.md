---
title: "LSM talk drift audit — slides, flyer, starter repo vs current projio (2026-08-08)"
date: 2026-08-08
tags: [result, lsm, agentic-workshop-2026-09, drift-audit, starter, session-checkpoint]
source_task: docs/log/task/task-arash-20260511-lsm-future-skills-ai-breakout.md
goal: agentic-workshop-2026-09
project_primary: projio
status: done
---

## What this note is

A read-only audit of the LSM Future Skills 2026 talk materials against the
current projio codebase, run 6 weeks before delivery (talk is 2026-09-22).
The prep task scheduled this drift check for 2026-09-15; it is done early.
Scope: `slides.qmd`, `proposal-flyer.qmd`, the `projio-starter-lsm` skeleton,
and the `idea-example.md` inside it. No files were modified except this note.

Bottom line: the **slides and flyer hold up well** (only one hard tool
reference in the slides, `rag_query`, and it is still correct). The **starter
repo does not work as advertised** — it is still the 4-file skeleton the
2026-05-27 status note flagged as unbuilt, so the README's "git clone → run
one MCP query" flow fails at every step. The single biggest risk to the talk
is not tool-name drift (there is almost none); it is that the promised
clone-and-try artifact is empty.

## Headline: the feared drift did not happen

The May risk register (risk 7) worried that `pipeio_target_paths`,
`schedule_queue`, and `note_search` might be renamed by September. They were
not. All three still exist and are registered:

- `rag_query` — `src/projio/mcp/server.py:13`, signature `rag_query(query, corpus="", k=8)`
- `note_search` — `server.py:500`, signature `note_search(query, k=5, corpus="notes")`
- `pipeio_target_paths` — `server.py:1617`
- `schedule_queue` (worklog) — still present as `mcp__worklog__schedule_queue`

`projio init`, `projio sync`, and `projio mcp` / `mcp-config` CLI subcommands
all still exist (`src/projio/cli.py:15, 249, 266, 269`). The MCP server module
`projio.mcp.server` is resolvable and has a `__main__` entry point.

So the tool surface is stable. The drift that matters is (a) a slide-vs-README
contradiction, (b) a frontmatter field-name mismatch in the quoted result
note, (c) one stale count, one stale title, and (d) the un-built starter.

## Reference cross-check (every projio-specific reference)

### slides.qmd

| Reference | Location | Current state | Verdict |
|---|---|---|---|
| `rag_query("burst threshold", corpus="notes")` | slide "wait — is this projio?" (l.200) | Tool registered; `corpus` kwarg valid | OK, no drift |
| `projio init` | slide "adopt or adapt" (l.301) | Valid CLI subcommand | CONFLICT — README says do NOT run it, and slide omits the required `pixi install` (see D-1) |
| Result-note frontmatter: `source_task`, `source_idea`, `project_primary`, `tags`, `status` | slide "a result note an agent wrote" (l.153-161) | `source_task`/`project_primary`/`tags`/`status` are current; `source_idea` is legacy (3 uses repo-wide vs 176 for `source_note`) | PARTIAL DRIFT — see D-2 |
| "Opus for synthesis, Haiku for triage" | slide "what works" | Conceptual, no code ref | OK |
| Live-open files: `result-arash-20260508-stack-axis-survey.md`, its `source_task` and cited idea note | speaker notes, slide "a result note…" | All three files exist on disk | OK (but the real note uses `source_note`, not `source_idea` — see D-2) |

### proposal-flyer.qmd

Names BIDS, DataLad, Snakemake, Marimo (HoloViews/Bokeh), Quarto, revealjs,
MkDocs, OpenAlex, docling, GROBID, GitHub/GitLab Pages. It names **no MCP
tools, no CLI commands, and no config keys**. Every named concept maps to a
live subsystem (biblio = docling/grobid/openalex; pipeio = Snakemake; notio =
manuscripts; `site.py` = Pages publish). Diagram and logo assets are present
(`proposal-diagram.png`, `logos/`). **No drift.** The handbook and source URLs
are external and were not fetched, but both are plausible and unchanged.

### projio-starter-lsm/README.md

| Reference | Location | Current state | Verdict |
|---|---|---|---|
| `pixi install` | Install step 2 | Needs `pyproject.toml` or `pixi.toml`; neither exists | BREAKS — see D-3 |
| `pixi run projio sync` | Install step 3 | CLI valid, but `.projio/config.yml` missing → sync is a graceful no-op ("skipped: no .projio/config.yml") | DEGRADED — see D-4 |
| `.mcp.json` → `pixi run python -m projio.mcp.server`, `PROJIO_ROOT=${PWD}` | `.mcp.json` | Module valid; but `pixi run` needs a pixi env with projio+extras installed, which does not exist → **server never launches** | BREAKS — see D-3 |
| `rag_query` "against the notes corpus" | "Try one MCP query" step 1 | Needs a built indexio Chroma store + a `notes` corpus; starter ships no index, no `infra/indexio/config.yaml`. `indexio` is an optional extra (`pyproject.toml:39`). rag_query/note_search error or return empty; agent falls back to plain Read | BREAKS the headline claim — see D-5 |
| "one of ~70 MCP tools" | "Try one MCP query" step 1 | Actual count is 192 registered tools (`grep -c @server.tool server.py`) | STALE COUNT — see D-8 |
| `.claude/settings.json` with `mcp__projio__*` in `permissions.allow` and `allowedTools` | `.claude/settings.json` | Matches current convention (wildcard must be in both) | OK, no drift |
| Talk title "Treating your research workflow as a manipulable object" | README blockquote (l.6) | Superseded 2026-05-26 by "Open-science conventions as agent infrastructure" | STALE TITLE — see D-7 |
| Directory tree (data/, code/pipelines/demo/, notebooks/explore.py, docs/deliverables/report.qmd, .projio/config.yml, pyproject.toml) | "What's here" | Only `.claude/`, `docs/log/idea/idea-example.md`, `.mcp.json`, `README.md` exist | SKELETON — see D-6 |
| Deferred features: `schedule_queue(after=...)`, worklog, notio taxonomy, figio, manuscript | "What's missing on purpose" | All still exist | OK, correctly scoped |

### projio-starter-lsm/docs/log/idea/idea-example.md

| Reference | Current state | Verdict |
|---|---|---|
| `data/raw/sub-01/eeg/sub-01_task-rest_eeg.txt` (+ `.json`), `participants.tsv` | Do not exist | BREAKS — see D-6 |
| `code/pipelines/demo/scripts/clean.py` | Does not exist | BREAKS — the note explicitly demands the agent read this file |
| `data/derivatives/demo/sub-01/`, `pixi run snakemake --cores 1` | No Snakefile, no pixi env | BREAKS — see D-6 |
| Frontmatter is `title/date/tags` only; filename `idea-example.md` not in notio `idea-arash-YYYYMMDD-HHMMSS-NNNNNN.md` form | Cosmetic; does not model the `source_task`/`source_note` receipt convention the slides sell | LOW — see D-9 |

## Drift findings (detail)

Ordered worst-first. "BREAKS LIVE" = will visibly fail if run in front of the
room or by an audience member who clones the repo.

### D-1 (HIGH, BREAKS LIVE, effort S) — slides say `projio init`; README says do NOT
`slides.qmd:301` tells the audience to `git clone … && cd && projio init`.
`README.md:55` says "the scaffold is already in place — **do NOT run
`projio init`**" and instead prescribes `pixi install` then `pixi run projio
sync`. These are contradictory instructions for the same repo. The slide also
omits the `pixi install` step entirely, so a viewer following the slide would
call a system `projio` that may not be installed. Pick one story. Given the
starter is a pre-scaffolded repo, the README's "no init" path is correct; the
slide CTA should match it (e.g. `pixi install` then the agent prompt), or drop
the code block and just show the clone URL + the one prompt.

### D-2 (MEDIUM, live-credibility, effort S) — quoted result note uses a field that isn't in the real file
The "a result note an agent wrote" slide shows `source_idea:` and `status:
done`. The actual note the slide is drawn from
(`docs/log/result/result-arash-20260508-stack-axis-survey.md`) uses
`source_note:` (not `source_idea:`) and `status: complete`. Repo-wide,
`source_note` has 176 uses and is the field notio scaffolds
(`packages/notio/src/notio/core.py:72`); `source_idea` has only 3 (all older
notes). The speaker notes instruct opening the real file live and pointing at
`source_idea` — which will not be there. Fix: either change the slide to
`source_note` (matches the file you will open), or open one of the 3 notes that
genuinely has `source_idea` (e.g. `result-arash-20260508-handbook-workshop-roadmap.md`).
Also reconcile `done` vs `complete`.

### D-3 (HIGH, BREAKS LIVE, effort M) — starter has no env, so `pixi install` and the MCP server both fail
`README.md` steps 2-3 and `.mcp.json` all assume a working pixi environment
with projio (plus the `indexio`/`notio` extras) installed. There is no
`pyproject.toml` and no `pixi.toml`, so `pixi install` has nothing to resolve
and `pixi run …` cannot start the MCP server. Result: an audience member who
clones and follows the README never gets a running projio server. This is the
single most important fix. Needs a `pyproject.toml` with `[tool.pixi]` (or a
`pixi.toml`) pinning `projio[indexio,notio]==0.X.Y` and the compute deps
(numpy, snakemake, marimo).

### D-4 (MEDIUM, degraded, effort S) — `projio sync` is a no-op without `.projio/config.yml`
`sync.py` degrades gracefully: with no `.projio/config.yml` it returns
"skipped" for each step (`sync.py:128`). So README step 3 runs but does nothing
("auto-discover code/lib, validate config" has no config and no `code/lib` to
discover). Ship a minimal `.projio/config.yml` (the README's own tree lists it)
so sync has something to validate.

### D-5 (HIGH, BREAKS LIVE, effort M) — the promised `rag_query` returns nothing
The README's "Try one MCP query" claims step 1 is "Call `rag_query` against
the notes corpus". `rag_query` (and `note_search`) query a prebuilt Chroma
store via `infra/indexio/config.yaml`. The starter ships no index, no indexio
config, and `indexio` is an optional extra. With nothing indexed, the call
errors or returns empty and the agent silently falls back to reading the file
directly — so the demo "works" but not for the reason the README states, and if
the presenter shows the tool call it will be empty. Either (a) add an indexio
config + a build step (`projio sync --index` or `indexio_build`) to the setup,
or (b) rewrite the README so step 1 is an honest `note_search`/Read that
matches what actually happens on a fresh clone.

### D-6 (HIGH, BREAKS LIVE, effort L) — the starter is still the 4-file skeleton
Confirmed unchanged since the 2026-05-27 status note (build-out was due
2026-09-08). Present: `.claude/settings.json`, `.mcp.json`, `README.md`,
`docs/log/idea/idea-example.md`. **Missing** (all promised by the README tree
and/or referenced by `idea-example.md`):

- `pyproject.toml` (env + projio pin) — blocks D-3
- `.projio/config.yml` — blocks D-4
- `data/raw/dataset_description.json`
- `data/raw/participants.tsv`
- `data/raw/sub-01/eeg/sub-01_task-rest_eeg.txt` (the synthetic signal)
- (optional) `data/raw/sub-01/eeg/sub-01_task-rest_eeg.json` (sidecar)
- `code/pipelines/demo/Snakefile`
- `code/pipelines/demo/scripts/clean.py`
- `notebooks/explore.py` (marimo)
- `docs/deliverables/report.qmd`
- `docs/log/result/` (empty dir with `.gitkeep`)
- (recommended) `infra/indexio/config.yaml` + a built index, if D-5 is fixed the index-building way

`idea-example.md` is the sharpest failure: it instructs the agent to read
`clean.py` and the EEG signal and to flag a filter-cutoff inconsistency between
the idea and the script — none of which exist, so the one scripted demo cannot
run. Effort L because it is a real (if tiny) BIDS + DataLad + Snakemake +
Marimo build-out, not a text edit.

### D-7 (MEDIUM, cosmetic-but-visible, effort S) — README cites the old talk title
`README.md:5-6` calls itself the companion to *"Treating your research
workflow as a manipulable object"*. That title was superseded on 2026-05-26 by
*"Open-science conventions as agent infrastructure"* (per the prep task note).
Every person who clones the repo sees the stale title. One-line fix.

### D-8 (LOW, cosmetic, effort S) — "~70 MCP tools" is now ~190
`README.md` says "one of ~70 MCP tools projio exposes". Actual count is 192
`@server.tool` registrations. Change to "~190" or soften to "one of the many
MCP tools projio exposes" so it does not date again.

### D-9 (LOW, teaching-quality, effort S) — `idea-example.md` does not model the receipt convention
Its frontmatter is `title/date/tags` only and its filename is not in notio's
timestamped form. The whole talk sells `source_task`/`source_note` receipts;
the one example note in the starter shows none. When D-6 is built, give this
note (and the result note the demo writes) proper `source_note`/`source_task`
frontmatter so the artifact matches the slides.

## Dated prep punch-list → 2026-09-22

Grouped by whether the item can break the talk. Effort: S ≈ <30 min,
M ≈ 1-3 h, L ≈ half-day+.

### Must-fix before the talk (break-live)

| # | Fix | Where | Prio | Effort | By |
|---|---|---|---|---|---|
| 1 | Build out the starter repo (all D-6 files) so `git clone → set up → one query` actually runs end to end | `docs/deliverables/starters/projio-starter-lsm/` | HIGH | L | 2026-09-08 |
| 2 | Add `pyproject.toml`/`pixi.toml` pinning `projio[indexio,notio]==0.X.Y` + compute deps; verify `pixi install` then MCP server launches on a clean clone | starter root, `.mcp.json` | HIGH | M | 2026-09-08 |
| 3 | Decide the `rag_query` story: either ship an indexio config + build step, or rewrite README step 1 to match a fresh-clone reality (Read / `note_search`) | `README.md` "Try one MCP query"; `infra/indexio/config.yaml` | HIGH | M | 2026-09-08 |
| 4 | Reconcile slide CTA with README: drop or fix `projio init` on `slides.qmd:301`; make the on-screen steps match the README's pixi path | `slides.qmd:301` (adopt or adapt); cross-ref `README.md:55` | HIGH | S | 2026-09-15 |
| 5 | Populate `.projio/config.yml` so `projio sync` is not a no-op | starter `.projio/config.yml` | MED | S | 2026-09-08 |
| 6 | End-to-end rehearsal on a fresh clone (fresh VM or clean dir) running exactly the README steps + the one prompt; fix whatever breaks | whole starter | HIGH | M | 2026-09-20 |

### Should-fix (credibility / correctness, will not hard-crash)

| # | Fix | Where | Prio | Effort | By |
|---|---|---|---|---|---|
| 7 | Fix the quoted result-note frontmatter: `source_idea`→`source_note` (or open a note that actually has `source_idea`); `status: done`→`complete` to match the file you open | `slides.qmd` "a result note an agent wrote" (l.153-161) | MED | S | 2026-09-15 |
| 8 | Update the stale talk title in the README blockquote | `README.md:5-6` | MED | S | 2026-09-15 |
| 9 | Give `idea-example.md` (and the demo's result note) proper notio receipt frontmatter so the example matches the slides' claim | starter `docs/log/idea/idea-example.md` | LOW | S | 2026-09-08 |

### Cosmetic

| # | Fix | Where | Prio | Effort | By |
|---|---|---|---|---|---|
| 10 | "~70 MCP tools" → "~190" or soften | `README.md` "Try one MCP query" | LOW | S | 2026-09-15 |
| 11 | Rename `idea-example.md` to the timestamped notio form (optional; keeps note_search/reindex consistent) | starter | LOW | S | 2026-09-15 |

## What is genuinely fine (do not spend time here)

- The slides' one hard tool reference (`rag_query`) is correct.
- The flyer has zero tool/CLI/config references and needs no drift work.
- `note_search`, `pipeio_target_paths`, `schedule_queue` all survived — the
  May rename fear did not materialize.
- `.claude/settings.json` permission shape (wildcard in both `permissions.allow`
  and `allowedTools`) still matches the current convention.
- The files the presenter opens live (stack-axis survey note + its cited
  task/idea notes) all exist.

## One-line recommendation

Treat the starter repo, not the slides, as the at-risk deliverable. The talk's
credibility rests on "you can clone this and it works"; right now you cannot.
The 2026-09-08 build-out (items 1-3, 5) is the critical path; everything else is
S-effort text edits that can land in the 2026-09-15 pass.
