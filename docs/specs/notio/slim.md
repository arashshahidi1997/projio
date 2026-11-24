# Slim notio

**Status:** draft, for the user's review. Nothing here is implemented.
**Date:** 2026-11-23. Session `projio-notio · NSLIM · slim notio spec`.
**Origin:** the user chose (2026-11-23, relayed by worklog-manager): slim notio, spec first, no code. Earlier request:
issue [[issue-arash-20260326-162053-576639]] (slim the note types, add `series` and `refs`), mostly done since; this
spec supersedes what is left of it.
**Related:** [remote-integration.md](remote-integration.md), [manuscript.md](manuscript.md),
[../study-template-defaults.md](../study-template-defaults.md) (Quarto default),
[../figio-decision.md](../figio-decision.md) (a decision spec of the same kind).

**Where this spec lives, and why.** projio's `docs/specs/notio/` already holds the current notio specs (manuscript,
remote integration). `packages/notio/docs/specs/` holds the 2025 `makenotes` design notes (goals, non-goals,
critique, redesign) that describe the Makefile tool notio replaced. Most of what this spec changes sits outside the
notio package (projio sync and site builds, MCP wrappers, the manager skills, worklog), and a spec in the
superproject needs no submodule commit and pointer bump. The notio package docs get a short pointer to it when the
work starts.

## 1. What notio is after this

notio writes and reads project notes: Markdown files with YAML frontmatter under `docs/log/<type>/`, named by type,
owner and timestamp, created from templates, found by id, searched, and updated in their frontmatter. A CLI and MCP
tools do this for agents; any Markdown editor does it for people. Three things change: LLM calls happen only when a
project turns them on, the generated index pages leave git, and a lint replaces the triage sessions that cleaned up
half-written notes. Whether manuscript and present stay in notio is left for a later decision (§6).

| # | Topic | Proposal | Status |
|---|---|---|---|
| a | Core | keep layout, ids, templates, create/resolve/search/update, CLI, MCP | keep |
| b | LLM enrich | one project switch, `[llm] enabled = false` by default, gates every LLM call | proposed |
| c | Indexes | not written on note creation; gitignored; built by `notio toc`, `projio sync` and site builds | proposed |
| d | Lint | `notio lint` (CLI) and `note_lint` (MCP): stub, partial, title, frontmatter, stale, broken refs | proposed |
| e | manuscript, present | present deprecated now; manuscript retired after pixecog moves to Quarto | decided 2026-11-24 |
| f | Human side | a docs page: Obsidian, Foam, SilverBullet on the same files | proposed |
| g | `handoff` type | add to notio's default types, with a built-in template and a missing-template fallback | proposed |

## 2. Survey (2026-11-23)

**Code.** `packages/notio/src/notio`, about 7,100 lines in all:

- note core: `core.py` 598, `query.py` 243, `config.py` 145, `repo.py` 39
- around it: `cli.py` 586, `mcp/server.py` 669 + `mcp/common.py` 90, `llm.py` 484, `remote.py` 502 (GitHub/GitLab
  issues), `docs.py` 249 (log, manuscript and master nav), `diataxis.py` 261
- manuscript: about 1,000 lines in `manuscript/`
- present: about 1,800 lines in `present/` (marp and reveal.js renderers, schema, import)

Tests: 50 in `tests/test_notio.py`, 29 in `test_manuscript.py`, 4 in `test_mcp_fields.py`, 46 in `present/tests/`.

**Defaults.** Default types are already the slim five from the March issue: idea, issue, task, meeting, result. The
`series` and `refs` fields exist. Projects add types in `notio.toml`, which merges over the defaults (`config.py`
`load_config`). projio adds `handoff` there (commit 2363ae8); pixecog keeps daily, weekly, commit and others.

**Notes.** Counts exclude `index.md`:

| project | idea | issue | task | result | handoff | other |
|---|---|---|---|---|---|---|
| projio | 49 | 151 | 157 | 8 | 28 | commit 3, goal 1 |
| pixecog | 187 | 66 | 223 | 294 | 143 | meeting 36, daily 27, commit 18, agent-interaction 13, weekly 2 |

A rough heuristic (body under 15 words after removing headings, empty bullets and template placeholders = stub; half
or more of the sections empty = partial) finds:

- projio: 9 stub and 31 partial tasks, mostly untitled shells (`title: "task"`, every section `-`), and 2 stub ideas
- pixecog: 7 stub dailies, 5 stub and 5 partial meetings, 3 stub commits, 7 partial ideas, 3 partial tasks, 1 stub
  weekly

A second defect is more common. 98 projio notes (61 issues, 24 tasks, 13 ideas) have a title that runs onto the next
line: `title: "Feature request: …` followed by body text. Captures that go through worklog put the first lines of the
body into the title. The March issue is one of them.

**Index churn.** `create_note` rebuilds `docs/log/<type>/index.md` and `docs/log/index.md` on every note
(`core.py:281-282`).

- In projio, 29 commits touched log indexes this year, adding 3,478 and removing 1,232 lines.
- In pixecog, 55 commits added 6,822 and removed 1,097 lines.
- At the time of this survey both working trees have modified index files that no session owns:
  - projio: `handoff/index.md` and `issue/index.md`
  - pixecog: `handoff`, `idea` and `result`

  Each session that writes a note dirties shared files that another session then commits or trips over.

**LLM.** notio itself only calls an LLM when asked. `--enrich` on note commands works only with `--transcript`
(`cli.py:60-69`), and `notio links` and MCP `note_links` call `suggest_links`. The default backend is `claude -p`, and
the ollama fallback defaults to a lab host (`http://theta:11434`, `llm.py:37`). In practice enrichment is on because
worklog turns it on (§4).

## 3. (a) Keep

**What stays.**

- **Layout:** `docs/log/<type>/<type>-<owner>-<timestamp>.md`, YAML frontmatter, timestamp ids
  (`YYYYMMDD-HHMMSS-ffffff`). Event and period modes.
- **Config:** `notio.toml` or `[tool.notio]` in pyproject, merged over the defaults. Templates live in
  `template_root` (`.projio/notio/templates` in projio projects), and built-in templates fill a fresh workspace.
- **Operations:** create (`create_note`), resolve by id or prefix, list, latest, read, search, frontmatter update.
- **Remote:** promote a note to a platform issue, capture an issue as a note, pull its thread (`remote.py`).
- **CLI:** `notio <type>`, `notio note`, `notio toc`, `notio init`, `notio promote|capture|pull|remote-status`.
- **MCP:** `note_list`, `note_latest`, `note_read`, `note_resolve`, `note_search`, `note_update`, `note_create`,
  `note_types`, the remote tools, and projio's wrappers of them.

**What changes here.** Nothing in behavior, apart from the three changes below and the template fallback in §8.

**Done when:** the existing note tests pass unchanged, apart from the index assertions §5 moves.

## 4. (b) LLM enrich: opt-in, off by default

**Today.** worklog drives the LLM calls:

- Its capture path adds `--enrich` whenever a note has no body (`capture/note.py:232-236`). Voice ingest, `worklog
  note` text, task records and queued-note delivery all reach this.
- After every note it runs `notio links <path> --apply`, an LLM call through `suggest_links` (`capture/note.py:257`).
- Its own `--no-llm` flag only skips worklog's classifier and never reaches notio. Item W12 in worklog's backlog plans
  to carry it through the gamma2 queue, because each enrich costs one LLM call of about 25 s per note.

**What changes.** notio gets one project-level switch, read from `notio.toml` or pyproject. Every LLM call in notio
passes through it.

```toml
[llm]
enabled = false        # default; nothing in notio calls an LLM
backend = "claude"     # only read when enabled
```

- Override for one run: env `NOTIO_LLM_ENABLED=1` (or `0`). With this, a caller like worklog can turn enrichment on
  for voice captures only, without changing a project's config.
- When disabled, `--enrich` is accepted and does nothing beyond one line on stderr (`enrich skipped: llm disabled`).
  The note is written with the plain structure, so worklog's current command line keeps working.
- When disabled, `notio links` and MCP `note_links` return `{"skipped": "llm disabled"}` with exit 0 and leave the note
  unchanged.
- `notio llm` and `notio warmup` report the switch first.
- The ollama URL loses its lab-host default. Without `OLLAMA_URL` or `[ollama] url`, the ollama backend reports itself
  as unavailable.

**What stays.** The `--enrich` flag, the enrich prompts, `suggest_links`, both backends, and the config keys
`backend`, `claude_model`, `claude_timeout`, `[ollama]`.

**Effect on worklog.** In projects that leave the switch off, worklog's delivery path makes no LLM calls, so W12
becomes moot. Its open question becomes a worklog decision instead: set `NOTIO_LLM_ENABLED=1` for `telegram-voice`
captures, where structuring a transcript is worth a call, or accept plain notes. Drop the unconditional
`notio links --apply`, or keep it, since it is now a cheap no-op.

**Done when:**

- A test with `_call_llm` patched to raise shows that `notio idea --transcript x --enrich` and `notio links` in a fresh
  workspace make no LLM call, and that the env override turns enrichment back on.
- `packages/notio/docs/reference/configuration.md` documents the switch.
- worklog-manager is told that W12 can close, or narrow to the voice-only override.

## 5. (c) Generated indexes leave git

**Today.** Four things write or need the index pages:

- `create_note` writes the type index and the root index on every note.
- `notio toc`, projio's `notio_reindex` and notio's own reindex tool rebuild them.
- `notio.docs.log_nav` (called by `projio sync` and `notio_log_nav`) writes `docs/log/mkdocs.yml` from the index pages.
  It lists only those pages and skips a type folder without one.
- questio's generated plan index links `../log/result/index.md` (`src/projio/mcp/questio.py:359`).

**What changes.**

1. `create_note` stops building indexes. A config key keeps the old behavior for projects that want it:
   `[indexes] build = "on-demand"` (default) or `"on-create"`.
2. The generated files are gitignored through projio's managed `.gitignore` block (`# >>> projio >>>`):
   `docs/log/**/index.md` and `docs/log/mkdocs.yml`. They are untracked once with `git rm --cached`, the same way
   `projio git untrack` does it, in one commit per project. A non-projio notio project adds the two lines itself.
   `notio init` prints them.
3. They are built on demand by:
   - `notio toc --all` and the MCP reindex tools (unchanged)
   - `log_nav`, which builds any missing index before it writes the nav
   - `projio sync` when `docs/log/` exists (it already calls `log_nav`)
   - `site_build` and `site_serve`, before mkdocs or Quarto run, so the questio link and the Log nav resolve
4. `projio init` stops writing the stub `docs/log/index.md`. The root index is generated like the others.
5. For Quarto study sites (the default since 2026-11-19), one option is a static listing page per type,
   `docs/log/<type>/index.qmd` with a Quarto `listing:` over `*.md`. It is written once and committed, Quarto renders
   it, and nothing has to be generated. This spec suggests it as the Quarto path, and the
   `projio-site · Quarto` work decides it. mkdocs sites keep the generated pages.

**What stays.** The index page format (`build_type_index`, `toc_keys`, `toc_groupby`, note cards) and the commands
that build them.

**Done when:**

- Creating a note changes exactly one file in git.
- projio and pixecog no longer track any `docs/log/**/index.md`, and their docs builds (`site_build`) still show the
  Log section with every type.
- notio's tests that assert an index after `create_note` (`tests/test_notio.py:129-138, 209-214, 355, 536-539`) assert
  it after `toc` instead, and a new test asserts that `create_note` writes no index.
- projio's `tests/test_mcp_notio.py` still passes. Its tests that mention `index.md` (`test_sync.py`, `test_init.py`,
  `test_site.py`, `test_regression.py`) have been checked for log-index assumptions.

## 6. (d) A lint for stub and partial notes

Triage sessions read notes one by one to find shells, half-filled notes and stale issues. A lint finds them
mechanically and leaves the decisions to the person or the manager.

**What changes.** `notio lint [--type T] [--json] [--strict] [--fix]` and MCP `note_lint(note_type="", fix=False)`
(projio wrapper too). It reads only the files. Each finding has a path, a rule and a one-line message:

| rule | finding | basis |
|---|---|---|
| `stub` | body has no content beyond the template | sections and placeholders from the note type's template |
| `partial` | half or more of the template's sections are empty | same |
| `title` | title missing, equal to the type name or default, or running past the closing quote onto the next line | frontmatter |
| `frontmatter` | unparsable block, duplicate keys (seen: `status` twice), required key missing (`timestamp`) | frontmatter |
| `status` | status not in the type's known set (issue: open/closed/…; task: pending/done/…) | per-type list in config, optional |
| `stale` | open issue or pending task older than N days (default 60) | `timestamp`, `status` |
| `ref` | `refs` entry or `[[wikilink]]` naming a note id that does not resolve | `resolve_note` |

- `--fix` is limited to mechanical repairs: it rebuilds a broken title from its first line or first heading and drops
  duplicate keys, keeping the last. It never deletes a note or changes a status.
- Without `--strict` the exit code is 0. With it, any finding exits 1, so a project can use the lint as a hook.
- The manager round and session-wrap use it:
  - The manager round runs `notio lint --json` (or `note_lint`) and shows one line of counts per rule.
  - session-wrap lints the notes this session wrote.
  - A person or a dispatched session acts on a finding by filling the note, closing it, or deleting it by hand.

**What stays.** Notes are never changed without `--fix`, and deletions stay manual.

**Done when:**

- `notio lint` on projio reports the 9 stub tasks and the 98 broken titles counted in §2. Small differences are fine
  where the heuristic and the template-based rule disagree; the report says which.
- `--fix` repairs the titles in a test fixture and changes nothing else.
- The project-manager adapter and session-wrap skills name the lint, while the core helpers stay stdlib-only. They
  call the CLI if it is there and skip it otherwise.

## 7. (e) manuscript and present: options only

**Today.**

- `notio.manuscript` (about 1,000 lines, 29 tests) and `notio.present` (about 1,800 lines, 46 tests) are subpackages.
- In notio they are used by the `notio manuscript` CLI and by `docs.py` (`manuscript_nav`, `master_nav`).
- In projio, `mcp/manuscripto.py`, `mcp/presentio.py`, `manuscript_cmd.py`, `sync.py` and `init.py` import them.
- Render config already lives in projio (`render.py`, `.projio/render.yml`).
- The 2026-03 design kept manuscript inside notio on purpose: sections are ordered notes.

**Options.** This spec chooses none of them.

1. **Stay as subpackages.** No change. notio's docs describe the notes core first and the two subpackages after it.
   Cheapest. notio stays the package with the most unrelated code.
2. **Optional extras.** They stay in the notio repository, behind `notio[manuscript]` and `notio[present]`, and import
   nothing at notio import time. The notes core installs without pandoc-related code paths. No consumer moves.
3. **Own package.** A new package (`manuscripto`, matching the MCP module names) takes both, or one each. notio
   becomes notes only. projio's imports move, and the release adds one more package to publish and pin.
4. **Into projio.** They sit next to `render.py`, which already owns the pandoc settings. notio becomes notes only.
   projio grows, and a non-projio user of manuscripts loses the small dependency.

**Inputs for the decision:**

- whether pixecog's first manuscript (the figio trial in [../figio-decision.md](../figio-decision.md)) uses
  `notio.manuscript` or Quarto directly
- how much of present the `quarto-talks` path replaces

**Done when:** the user picks an option in a later session. Until then, nothing in (a) to (d) depends on the choice.

**Decision (2026-11-24, the user, via projio-manager).** Quarto is the default for study sites, talks and
manuscripts (see [../study-template-defaults.md](../study-template-defaults.md)). It covers what `present` and
`manuscript` render, so notio does not wrap Quarto or scaffold Quarto files: `quarto create`, Quarto's own templates
and the agent writing `_quarto.yml` do that.

- **present: deprecated now.** No new work. Its MCP tools (`present_*`) become opt-in, as figio's did, and their
  descriptions say deprecated and point to Quarto reveal.js and the `quarto-talks` skill. The subpackage is removed
  after one notio release. Evidence: the recent decks are `.qmd` (pixecog `intro-2026-05-02`, the LSM talk), and
  no project builds through `notio.present` today.
- **manuscript: retired after pixecog's cutover.** pixecog's manuscript builds both ways side by side
  (`docs/manuscript/pixecog/_quarto.yml`, "coexists ... while the transition is in progress"); the Quarto path
  needs two pre-render scripts (sections to includes, stats sidecars to `{{< meta >}}`). Once pixecog drops the
  pandoc path, `notio.manuscript` is retired and those scripts become a projio "Quarto manuscript" template.
- **The project glue lives in projio, not notio:** compiled bibliography and CSL from `render.yml`, stats sidecars,
  pipeio figure paths, the wikilink filter, site templates (the Quarto site work). A few hundred lines of templates
  and scripts.
- **The `manuscript_*` MCP tools** are checked for real use first. Those that read the text (`cite_check`,
  `journal_check`, `section_context`, `diff`) can be pointed at a Quarto project; unused ones go with the
  subpackage.

notio after this is the notes core of §3 to §6 and §8.

## 8. (g) The `handoff` type

**Today.**

- session-wrap and the project manager treat a handoff as standard in every project. In projio they create it with
  `note_create(note_type="handoff")`, elsewhere as a file in the handoff folder.
- Only projio defines the type, in its own `notio.toml`. sirocampus has notio with idea, issue, task, meeting and
  result. Its templates folder holds no `handoff.md`, so manager-setup step 7 fell back to the file template
  (`docs/log/handoff/handoff-20261123-174000-setup.md`, reported by siro-manager-setup).
- The fallback leaves the handoff invisible to `note_resolve`, `note_list`, and the lint.

**Decision proposed: add `handoff` to notio's default types.**

```toml
[types.handoff]
mode = "event"
template = "handoff.md"
filename = "handoff-{owner}-{timestamp}.md"
toc_keys = ["title", "status", "branch"]
toc_groupby = "series"
```

- A built-in `handoff.md` joins `DEFAULT_TEMPLATES`. Its frontmatter carries `title`, `date`, `timestamp`, `series`,
  `status: open`, `branch`, `git_commit`, `refs`. Its body holds both section sets that manager-setup's template
  describes:
  - manager: What finished, Decisions, Open, Kickoff snippet
  - work session: What shipped, Uncommitted / in flight, Parked or broken, Next steps, Kickoff prompt

  One section set is deleted when the note is written.
- New, and needed for sirocampus: when a project's `template_root` lacks a type's template, `create_note` uses the
  built-in one instead of raising `FileNotFoundError`. sirocampus then gets handoff notes on its next notio upgrade
  with no config change.
- projio's own `[types.handoff]` in `notio.toml` becomes redundant and can be removed after the release. Its values
  are the same.

**Why this rather than documenting the file fallback.** Three projects already write handoffs (projio 28, pixecog
143, sirocampus 1), and the skills that write them ship with projio. A file fallback as the projio default would keep
two ways to write the same note and leave handoffs outside notio's resolve, search and lint. The March issue wanted
fewer types. A handoff has its own lifecycle (open, consumed, one open per series) and a reader (`round.py`) that
depends on it, which is the test that issue applied.

**Filenames.** notio names a handoff `handoff-<owner>-<timestamp>.md`. The file fallback for projects without notio
stays `handoff-<timestamp>-<slug>.md`. `round.py` orders handoffs by their frontmatter `timestamp` (`handoff_rows`),
so both forms can share a folder, as they now do in sirocampus.

**What manager-setup step 7 should then read:**

> 7. **Write the first manager handoff** with `series: manager`, `status: open`, `git_commit: <HEAD sha after step
> 8's commit>`. If the project has notio and `note_types()` (or `notio note --help`) lists `handoff`, create it with
> `note_create(note_type="handoff", …)`; otherwise write a file in `handoffs.dir` from `templates/handoff.md`, named
> `handoff-<timestamp>-<slug>.md`. What finished: the setup. Decisions the user made: prefix, purpose, working copy,
> push rule (dated). Open: whatever the survey found for the first round. The kickoff snippet matches the board's.

The check is on the type, not on "in projio". The step still works on an older notio and outside projio.
session-wrap's table row for handoffs gets the same wording.

**Done when:**

- A fresh `notio init` workspace lists `handoff` in `note_types()`.
- `note_create(note_type="handoff")` works in a workspace whose templates folder lacks `handoff.md`.
- manager-setup step 7 and session-wrap read as above.
- sirocampus creates a handoff through notio after upgrading.

## 9. (f) The human side: any editor on the same files

**What changes.** A notio docs page, `docs/how-to/editors.md`, linked from the README, states that people use any
Markdown editor on the same files, and covers three:

- **Obsidian:** open the repository (or `docs/log`) as a vault. Note ids are filenames, so `[[idea-arash-…]]` links
  resolve. Obsidian's template plugin uses `{{title}}`, while notio's templates use `${title}`. Create notes with
  `notio <type>`, or copy a template and fill the variables by hand.
- **Foam (VS Code):** wikilinks and backlinks work on the same ids. notio's predecessor used `.foam/templates`, and
  the page says how to point Foam at notio's templates or to use the CLI instead.
- **SilverBullet:** serve the repository folder. Frontmatter becomes queryable attributes, so a query over
  `status: open` issues works without notio.

The page also gives the rules a person keeps:

- the filename pattern and timestamp id
- frontmatter as YAML, with `title` on one line
- generated `index.md` files are not edited (they are gitignored after §5)
- `notio lint` checks the result

**What stays.** Nothing here adds editor plugins or syncs editor state.

**Done when:** the page exists and is in the notio docs nav. The user has opened one project in at least one of the
three editors and confirmed the links and frontmatter work. That last check is manual.

## 10. Effect on consumers

| Consumer | Reads | Effect | Change needed |
|---|---|---|---|
| worklog capture and delivery (`capture/note.py`, `pipeline.py`, `cli.py:3958`) | runs `notio … --enrich`, then `notio links --apply` | with §4 both are no-ops unless the target project enables the LLM | none required; W12 becomes moot; optional env override for voice |
| worklog promote paths (`cli.py:3200-3219`, `mcp_server.py:905-912`) | `--enrich` when no prompt | same | none required |
| worklog docs site (`mkdocs.yml:56`, 17 committed `docs/log/**/index.md`) | its own `docs/log/mkdocs.yml`; it links no other project's log index pages | once worklog upgrades notio its indexes stop updating on note creation | worklog builds them before mkdocs (`notio toc --all`, log nav), or sets `[indexes] build = "on-create"`; worklog's call |
| worklog `_note_forward_host` (`cli.py:3326-3333`) | rationale: one writer because indexes regenerate on every note | rationale weakens | none; worth a note to worklog-manager |
| project-manager core (`incoming.py`, `round.py`, `_common.py`) | globs `docs/log/<dir>/*.md`, skips `index.md`; never reads the index | none; gitignored indexes add no untracked noise | none |
| manager-setup step 7, session-wrap handoff row | handoff via notio type or file | §8 | reword as in §8 |
| manager-setup step 8 | commits "the handoff folder" | no index file in it after §5 | none |
| `projio sync` (`sync.py:495-499, 537`) | calls `log_nav`, adds the Log nav include | `log_nav` builds missing indexes first | small change in notio `log_nav` |
| `projio init` (`init.py:1396-1400`, managed `.gitignore` block) | writes a stub `docs/log/index.md` | stub removed; gitignore lines added | yes |
| `site_build`, `site_serve` | mkdocs nav includes `docs/log/mkdocs.yml` | must build indexes before the docs tool runs | yes |
| questio plan index (`mcp/questio.py:359`) | links `../log/result/index.md` | resolves because site build builds it | none beyond the site build |
| projio MCP `notio_reindex`, `notio_log_nav` | write the indexes and nav | unchanged; they become the main way to build | instructions table (`init.py:1978`) unchanged |
| projio MCP `note_*` wrappers | no LLM, skip `index.md` | none | add `note_lint` wrapper (§6) |
| projio, pixecog repositories | tracked indexes, modified in working trees today | one untrack commit each | yes, per project |

## 11. Order of work and what is left out

**Order of work.** Each step is complete on its own:

1. §4 switch and §8 type and template fallback, in one notio release with tests. manager-setup and session-wrap
   wording changes ship with projio.
2. §5 indexes: notio (`create_note`, `log_nav`), then projio (`.gitignore` block, init, site build), then the untrack
   commits in projio and pixecog.
3. §6 lint, then the manager and session-wrap mentions.
4. §9 docs page.
5. §7 when the user takes it up.

**Left out (parked here).**

- slimming the built-in template set further
- `diataxis.py` (doc scaffolding unrelated to notes; a candidate for the same treatment as §7)
- the `remote.py` platform integration, unchanged
- a status vocabulary per type beyond the optional lint rule

**Changelog note.** The index change alters what a note commit contains, so the notio release notes say so.
