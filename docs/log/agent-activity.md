# Agent Activity Log

Recent agent session summaries for handoff context.

## 2026-03-26 00:38 | projio | opus | 1 steps

(no output)

Session: `n/a` | Task: `task-arash-20260325-213420-015848.md`

## 2026-03-28 18:04 | projio | opus | 1 steps

Please run the verification commands to confirm:

Session: `4cb2c2fb` | Task: `task-arash-20260328-174922-286397.md`

## 2026-03-28 19:50 | projio | opus | 1 steps

Tests: 70 passed, 1 pre-existing unrelated failure.

Session: `0ed4146e` | Task: `task-arash-20260328-193742-747938.md`

## 2026-03-28 20:07 | projio | sonnet | 1 steps

Users can now run:

Session: `510ff241` | Task: `task-arash-20260328-200549-976370.md`

## 2026-03-30 18:16 | projio | sonnet | 1 steps

- **Tests**: 234 passed
- **pipeio submodule**: saved (config_patch, nb_update, mod_context, rule_insert fixes)
- **projio root**: saved (MCP tools, roadmap notes, all subdatasets + docs)
- **Status**: clean, no uncommitted changes

Session: `5e0a9bde` | Task: `task-arash-20260330-175553-676358.md`

## 2026-03-30 18:35 | projio | sonnet | 1 steps

---

Session: `3bdfb3e7` | Task: `task-arash-20260330-175231-488273.md`

## 2026-03-30 19:12 | projio | sonnet | 1 steps

(no output)

Session: `n/a` | Task: `task-arash-20260330-175554-840850.md`

## 2026-03-31 00:11 | projio | opus | 1 steps

No datalad save needed since there are no new changes.

Session: `3dad73ad` | Task: `task-arash-20260330-175554-589019.md`

## 2026-03-31 03:36 | projio | opus | 1 steps

**Task 2:** Wrote comprehensive audit note (`idea-arash-20260331-033442-033443`) covering: current implementation analysis (4 run tools), datalad run semantics, new interface design, replacement strategy, 6 open questions with recommendations, and 4-phase migration plan.

Session: `dd9c6c81` | Task: `task-arash-20260330-175232-430442.md`

## 2026-03-31 03:43 | projio | opus | 1 steps

1. **config_patch YAML round-trip fidelity** — spurious formatting diffs from flow-style normalization (`issue-arash-20260331-034216-830892`)
2. **DAG edge resolution for `out_paths()` references** — DAG returns 0 edges for ecephys despite clear dependency chain (`issue-arash-20260331-034232-267346`)

Session: `eb2cd156` | Task: `task-arash-20260330-175554-840850.md`

## 2026-03-31 03:49 | projio | opus | 1 steps

Section 6 identifies 7 operations a future `pipeio_flow_migrate` tool could automate.

Session: `acfce680` | Task: `task-arash-20260330-180056-943959.md`

## 2026-03-31 17:26 | projio | opus | 1 steps

| File | Fixes |
|------|-------|
| **mcp-tools.md** | Added `pipeio_nb_update`, `pipeio_mod_context`, `pipeio_dag_export`, `pipeio_report` sections; fixed `nb_status`/`nb_sync`/`run_status`/`run` signatures; moved `config_init` to Config Authoring; restructured Adapters → DAG & Reporting + Logging; updated category table counts; added new entries to Agent Routing table |
| **registry.md** | Added `app_type: str = ""` to FlowEntry model; updated registry path to `.projio/pipeio/registry.yml` ...

Session: `fd48d498` | Task: `task-arash-20260331-145359-712330.md`

## 2026-03-31 18:11 | projio | opus | 1 steps

**Task 2 — Implementation** (`packages/notio/src/notio/manuscript/`):
- `schema.py` — `ManuscriptSpec` dataclass with `from_yaml()`, `from_dict()`, `to_dict()`, and `scaffold_spec()` for scaffolding
- `assembly.py` — `strip_frontmatter()`, `adjust_headings()`, `load_sections()`, `assemble()`, `write_assembled()`
- `render.py` — `find_pandoc()`, `build_pandoc_command()`, `render_single()`, `render()` — full pandoc pipeline
- `figures.py` — `resolve_figure_paths()`, `insert_figure_references()`...

Session: `f9189029` | Task: `task-arash-20260331-175617-644481.md`

## 2026-03-31 18:16 | projio | sonnet | 1 steps

---

Session: `df0484c9` | Task: `task-arash-20260328-011427-733990.md`

## 2026-03-31 18:43 | projio | opus | 1 steps

8. **Permissions** — No changes needed; existing `mcp__projio__*` wildcard already covers `mcp__projio__manuscript_*`.

Session: `7d5c004a` | Task: `task-arash-20260331-175739-980549.md`

## 2026-04-01 04:07 | projio | sonnet | 1 steps

**Task 3 — Agent safety** (`docs/explanation/agent-safety.md`):
- Expanded the granular read-only allowlist from 23 to 60 tools covering all new subsystems
- Updated write tools list in the description paragraph
- Corrected "no deletion" claim — clarified `pipeio_flow_deregister` and `pipeio_run_kill` behavior
- Updated `projio add claude` → `projio claude update-permissions`

Session: `4ff59117` | Task: `issue-arash-20260331-172245-820267.md`

## 2026-04-02 12:34 | projio | opus | 1 steps

**Task 3** — Master document support:
- Created `notio.manuscript.master` module with `find_master_files()`, `build_master()`, `generate_master_md()`
- Added `master_list`, `master_build`, `master_generate` MCP tools
- Added `notio manuscript master-list` and `notio manuscript master-build` CLI commands
- Master docs use the Lua filter for Pandoc transclusion and inherit render settings

Session: `29223ba5` | Task: `task-arash-20260402-122112-581688.md`

## 2026-04-02 22:19 | projio | opus | 1 steps

**Follow-up tasks scheduled:**
- P2 (`c4fc0e6c9f76`) — `manuscript_diff` + `manuscript_cite_suggest` — after this task
- P3 (`f7ef8596f3f6`) — `manuscript_journal_check` — after P2

Session: `30fa61ef` | Task: `task-arash-20260402-221203-017791.md`

## 2026-04-02 23:13 | projio | opus | 1 steps

**Task 6** — Updated `ecosystem_status()` to use new merged/compiled bib paths with staleness checking, updated CLAUDE.md MCP tool list to include `biblio_compile`, updated `manuscript_cmd.py` render defaults.

Session: `5770b78c` | Task: `task-arash-20260402-221336-068739.md`

## 2026-04-02 23:41 | projio | opus | 1 steps

**5. CLAUDE.md** — Added `manuscript_diff`, `manuscript_cite_suggest` to the manuscripto tool list.

Session: `2db48022` | Task: `task-arash-20260402-221637-400871.md`

## 2026-04-02 23:48 | projio | opus | 1 steps

**Phase 3 — Registration & docs**:
- Registered `manuscript_journal_check` tool in `server.py`
- Added to the tool list in `CLAUDE.md`

Session: `5c6bde77` | Task: `task-arash-20260402-221711-206073.md`

## 2026-04-03 06:01 | projio | opus | 1 steps

It looks like you sent an empty or accidental message. What would you like to work on?

Session: `cc8d54d3` | Task: `task-arash-20260403-053526-884621.md`

## 2026-04-03 19:34 | projio | opus | 1 steps

**Key findings:**
- **No bugs** — all endpoints, filters, and cursor pagination are correct
- **6 P1 gaps**: batch DOI lookups via OR filter (50x speedup), missing `type`/`is_retracted`/`topics` extraction in `WorkRecord`, default `per_page` should be 200 for bulk ops, only first author affiliation captured
- **11 P2 gaps**: `group_by` support, `keywords`/`grants`/`counts_by_year`/`related_works`/`fwci` extraction, cache TTL, author/institution cache, rate limiter
- **8 P3 gaps**: `sample`/`s...

Session: `6803550f` | Task: `task-arash-20260403-193018-521162.md`

## 2026-04-03 19:37 | projio | opus | 1 steps

**Recommendation:** Layer them — OpenAlex topics as free baseline (layer 0), autotag propagation (layer 1), autotag LLM (layer 2), concept extraction (layer 3). Biblio already fetches `topics` from OpenAlex in the resolver, so Phase 1 requires no new API calls.

Session: `8d0b7222` | Task: `task-arash-20260403-193053-418834.md`

## 2026-04-03 19:40 | projio | opus | 1 steps

Key design decision: enrichment happens during resolution (same API call), not as a separate pipeline step — the data is already in the response, just being discarded.

Session: `d57d2682` | Task: `task-arash-20260403-193124-041896.md`

## 2026-04-03 20:20 | projio | opus | 1 steps

- **Data flow diagram** (Zotero ↔ biblio ↔ OpenAlex)
- **Authentication** — API key (cloud) and local API (Zotero 7), config model under `zotero:` section in biblio.yml
- **Phase 1 (pull)** — Incremental version-based sync, BibTeX to `srcbib/zotero.bib`, PDF download, sync state in `zotero_sync.yml`, citekey strategy (Zotero vs biblio mode)
- **Phase 2 (push-back)** — Tags with `biblio:` namespace, child notes for summaries, DOI/OpenAlex ID write-back, optimistic concurrency conflict handling...

Session: `9428acf7` | Task: `task-arash-20260403-201627-821230.md`

## 2026-04-03 21:04 | projio | opus | 1 steps

5. **`packages/biblio/src/biblio/cli.py`** — Added `biblio pool promote` CLI subcommand with `--citekeys` and `--all-local` options

Session: `1fc76032` | Task: `task-arash-20260403-210000-819864.md`

## 2026-04-03 21:12 | projio | opus | 1 steps

### Files modified
- **`packages/biblio/pyproject.toml`** — Added `zotero = ["pyzotero>=1.6"]` optional dep
- **`packages/biblio/src/biblio/cli.py`** — Added `biblio zotero pull` and `biblio zotero status` subcommands
- **`packages/biblio/src/biblio/mcp.py`** — Added `zotero_pull()` and `zotero_status()` MCP wrappers
- **`src/projio/mcp/biblio.py`** — Added `biblio_zotero_pull()` and `biblio_zotero_status()` tool functions
- **`src/projio/mcp/server.py`** — Registered `biblio_zotero_pull` and...

Session: `e7558a52` | Task: `task-arash-20260403-210018-484102.md`

## 2026-04-03 21:17 | projio | opus | 1 steps

Key design decisions matching the spec:
- **Tag namespacing**: All pushed tags use `biblio:` prefix (`biblio:status/reading`, `biblio:topic/...`, `biblio:concept/...`, `biblio:tag/...`)
- **Optimistic concurrency**: Compares stored vs current Zotero item version; skips conflicts unless `--force`
- **Union merge for tags**: Only adds new tags, never removes existing ones
- **DOI write-if-empty**: Only writes DOI if Zotero's DOI field is blank
- **OpenAlex ID in extra field**: Appends line if n...

Session: `21f69514` | Task: `task-arash-20260403-210031-898352.md`

## 2026-04-03 21:20 | projio | opus | 1 steps

Done. Added DOI and OpenAlex ("OA") outbound links to each paper row in `packages/biblio/frontend/src/components/CorpusTab.jsx` (lines 315–340). The links appear in the citekey column next to the existing open/network buttons, matching the style used in PaperTab.jsx.

Session: `efc546db` | Task: `task-arash-20260403-210053-391568.md`

## 2026-04-04 01:56 | projio | opus | 1 steps

All new fields are propagated through MCP return dicts. The `get_author_works_by_position` select string was also updated to include the new fields.

Session: `ed6dcb96` | Task: `task-arash-20260404-015001-691920.md`

## 2026-04-04 02:24 | projio | opus | 1 steps

**Modified files:**
- `packages/biblio/src/biblio/openalex/openalex_client.py` — Added `keywords` and `counts_by_year` to `DEFAULT_SELECT`
- `packages/biblio/src/biblio/openalex/openalex_resolve.py` — Extended `_work_to_minimal` with `primary_topic`, `keywords`, `type`, `is_retracted`, `counts_by_year`
- `packages/biblio/src/biblio/autotag.py` — LLM tier now loads OpenAlex enrichment and injects it as context in the classification prompt
- `packages/biblio/src/biblio/mcp.py` — Added `enrich()...

Session: `302dbc10` | Task: `task-arash-20260404-015003-191891.md`
