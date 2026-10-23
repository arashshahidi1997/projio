# Agent interface layers: CLI, skills, MCP

**Status:** Proposed; the biblio group is implemented (2026-10-23): `paper_lookup`, `biblio_job`, 34 tools deprecated for one release
**Date:** 2026-10-23

## Motivation

Projio and its subsystems reach agents through four channels: each package's
CLI, skills (`SKILL.md`), the projio MCP server, and generated instructions
(`CLAUDE.md` routing tables, server instructions). They grew side by side, and
the MCP server grew fastest: one tool per CLI operation, for every subsystem.

Usage says most of that surface is not used. Claude Code transcripts on gamma2
(350 sessions, 2026-07-13 to 2026-10-23, every project) record 1379 calls to
projio-server tools:

| Group | Tools | Ever called | Calls | Schema size (tokens) |
|-------|------:|------------:|------:|---------------------:|
| notio | 14 | 10 | 536 | ~940 |
| datalad | 6 | 4 | 265 | ~520 |
| indexio | 8 | 7 | 185 | ~550 |
| biblio | 37 | 17 | 155 | ~3320 |
| codio | 10 | 1 | 72 | ~850 |
| pipeio | 58 | 17 | 62 | ~5780 |
| context | 8 | 5 | 50 | ~550 |
| questio | 4 | 2 | 43 | ~290 |
| manuscript | 19 | 3 | 5 | ~980 |
| present | 15 | 2 | 3 | ~1090 |
| figio | 6 | 1 | 2 | ~450 |
| site | 6 | 1 | 1 | ~260 |
| report | 2 | 0 | 0 | ~200 |
| **total** | **193** | **70** | **1379** | **~15 800** |

The 123 tools never called were all added in March or April 2026, so each was
available for the whole three-month window. Meanwhile the work that matters
most in biblio now (wiki, digests, quote checks) has no MCP tools at all and is
done through the CLI: about 95 `biblio wiki|digest|figures|fulltext` calls in
the same transcripts, driven by skills.

The cost of the unused surface:

- **Context.** Each server instance carries ~15 800 tokens of tool schemas and
  descriptions. Gamma2 projects run two instances (`projio` and
  `sirocampus`), so twice that. Claude Code defers schemas, which reduces the
  cost to a list of ~390 names plus tool-search noise; Codex, VS Code/Copilot
  and Cursor (see [multi-agent MCP config](multi-agent-mcp-config.md)) load
  tools eagerly, and some clients cap or warn on the number of tools.
- **Drift.** A tool that mirrors a CLI command goes stale when the command
  changes: `biblio_merge` still describes `biblio merge`, which became
  `biblio bibtex merge`; `paper_absent_refs` uses the matching that
  `biblio refs triage` replaced; `biblio_docling_batch` cannot pass `--keys`,
  so through MCP it still converts every pending paper in a shared copy.
- **Misrouting.** Generated instructions say "always use MCP tools instead of
  direct file manipulation" and map intents to MCP tools only, which sends
  agents away from the CLI that the skills and tests actually cover.

## Design decision

**The CLI (over the library) is where capabilities live. Skills say when and
how to use them. MCP is a small, typed interface admitted per tool for
reasons a shell cannot serve. Instructions route each intent to the layer that
serves it.**

### Layers

| Layer | Answers | Contains | Never contains |
|-------|---------|----------|----------------|
| Library | how | the implementation, tested | agent prose |
| CLI | what can be done | every capability, `--help`, dry runs, exit codes | logic absent from the library |
| Skills | when, in what order, what counts as done | procedure, judgment, hard rules; names CLI commands (and MCP tools where one is admitted) | reimplemented capability |
| MCP | typed access where a shell serves badly | thin adapters over library functions | logic of its own; one tool per CLI subcommand |
| Instructions | where to go for an intent | routing tables, pointers to skills | prohibitions on the CLI |
| Hooks | what must always happen | deterministic triggers (sync, index on save) | judgment |

### When a capability gets an MCP tool

A tool is admitted for at least one of these reasons, recorded with it:

- **R1 No shell.** The client cannot run commands (claude.ai, desktop chat,
  hosted agents), or the user wants the capability there.
- **R2 Cross-project.** The tool answers about a project other than the one
  the agent works in, through a server with a fixed root (`sirocampus`, the
  worklog hub, a citekey looked up in the lab pool).
- **R3 Long-running state.** A job or a server the agent starts and then
  polls, stops or attaches to: docling and OA-fetch batches, index builds,
  pipeline runs, marimo sessions. The tool returns a handle.
- **R4 Structured result.** The answer is a record the agent would otherwise
  parse out of large or irregular output (a paper's context, a flow's status).
- **R5 Permission boundary.** A narrow, auto-approvable action whose shell
  form would need a broad permission (`datalad_save` of the project, a
  read-only lookup).

A capability that a shell agent can run through the CLI, that has none of
these reasons, stays CLI-only. Usage is evidence, not the rule: a tool called
often without a reason (e.g. by habit, or because instructions said so) is
moved to the CLI; a tool with a reason and no calls is kept if the reason is
R1 for a client in use.

### How admitted tools are shaped

1. **Thin.** The tool calls the same library function the CLI calls. If the
   CLI has a flag the tool needs, the tool gets the same parameter (and the
   same name); a CLI change that the tool does not follow fails a test.
2. **Task-shaped, not operation-shaped.** One tool per task an agent has,
   e.g. `biblio_job(action=start|status|kill, kind=docling|oa_fetch, keys=…)`
   in place of six start and status variants; `paper_lookup(citekeys,
   fields=…)` in place of `citekey_resolve`, `paper_context` and
   `library_get`.
3. **Bounded output.** Results are records with counts and paths, never full
   texts or logs; the CLI or a file read gives the rest.
4. **Reason in code.** Each registration carries its reasons
   (`@tool(..., reasons=("R3",))`); a test fails for a tool without one.
5. **Groups.** Tools belong to a group (the subsystem). A server instance
   exposes only the groups a project enables (`mcp.groups` in
   `.projio/config.yml`, default from the installed subsystems and the
   project kind; `PROJIO_MCP_GROUPS` per server entry). A pool server such as
   `sirocampus` exposes lookups only.

### Skill delivery

A skill reaches Claude Code as a native skill (`.claude/skills/<name>/SKILL.md`),
written by `projio sync` from its source (project, installed package, projio's
bundle). The agent sees the name and `description` of every skill and loads a
body only when it uses the skill, so the description must say what the skill
does and when to use it. The earlier delivery, a `.claude/commands/` wrapper
per skill that called `skill_read`, showed an HTML comment as the description
and made every use depend on someone typing the command: on gamma2 no biblio
skill was ever chosen by an agent. `agent_instructions` and `skill_read` stay
for agents that do not read `.claude/skills/` (R1). A package tests that the
commands its skills name exist (biblio: `tests/test_skills_commands.py`).

### Instructions

Generated routing tables (`CLAUDE.md`, server instructions, the codegen in
`config_gen.py`) map intent to the layer per this spec: the CLI command for
CLI-only work, the skill for a workflow, the MCP tool where one is admitted.
They drop the "always use MCP tools" rule. Per the existing convention, a
change to MCP tools updates three places: the worklog MCP server
instructions, worklog's `CLAUDE.md`, and projio's codegen.

### Removing a tool

1. Mark it deprecated: its description starts with "Deprecated: use `<cli
   command>`" for one release.
2. Remove the registration and the wrapper; keep the library function.
3. Update the generated instructions and `docs/reference/mcp-tools.md`.

A usage report (`projio mcp usage`, from the transcripts as above) makes the
next review a command instead of a script.

## Open questions

1. **R1 in practice.** Which clients without a shell use projio today
   (claude.ai, desktop chat, voice capture through worklog)? The answer sets
   how many read-heavy tools stay.
2. **Codex and Copilot.** They have shells; whether they should get the same
   small set or a larger one depends on how well they use skills
   (`agent_instructions` and `skill_read` serve skills over MCP for them).
3. **Transcripts elsewhere.** The data covers gamma2 only; laptop sessions
   may use other tools.

## Proposed changes per group

For review. "CLI" means the capability stays in the CLI (and library) and the
MCP tool goes. "Opt-in" means the group is off unless a project enables it.

| Group | Keep (reason) | Merge into | Move to CLI or remove |
|-------|---------------|------------|-----------------------|
| context | `project_context` (R4), `skill_read`, `agent_instructions` (R1: skills for clients without them) | | `projio_init` (`projio init`), `ecosystem_status` (`projio status`); `runtime_conventions`, `module_context`, `permissions_sync` need a CLI form first (`projio sync` covers permissions) |
| notio | `note_create`, `note_read`, `note_update`, `note_search`, `note_list`, `note_resolve` (R5, R4; 476 calls) | `note_latest`, `note_types` into `note_list` | `notio_reindex`, `notio_log_nav`, `note_promote`, `note_capture`, `note_pull`, `note_remote_status` |
| datalad | `datalad_save`, `datalad_push`, `datalad_status`, `datalad_pull` (R5) | `git_status` into `datalad_status` | `datalad_siblings` |
| indexio | `rag_query`, `rag_query_multi`, `corpus_list` (R4, R2); `indexio_build` + status (R3) | `indexio_build_status`, `indexio_status` into one job tool | `indexio_sources_list`, `indexio_sources_sync` |
| biblio | `paper_lookup` (R2, R4), `biblio_job` for docling and OA fetch (R3), `biblio_status` (R4), `biblio_ingest`, `biblio_compile` (render pipeline, R5) | `citekey_resolve`, `paper_context`, `library_get` into `paper_lookup`; `biblio_docling*`, `biblio_pdf_fetch_oa*` into `biblio_job` | the other 26, incl. `biblio_merge` (stale), `biblio_rag_sync` (RAG not trusted yet), discovery, Zotero, enrich, pool, graph |
| codio | `codio_func_doc` (R4; 72 calls in pixecog) | | the other 9 (opt-in if a project wants them) |
| pipeio (opt-in) | `pipeio_flow_status`, `pipeio_flow_list`, `pipeio_target_paths` (R4); `pipeio_run` job, `pipeio_nb_open` session (R3) | run status and kill into `pipeio_run`; `pipeio_nb_watch`/`snapshot` into the session tool | the other ~45 (CLI) |
| questio (opt-in) | `questio_status`, `questio_docs_collect` | | `questio_gap`, `questio_prior_art` |
| manuscript, present, report, figio, site | opt-in groups; in each, `*_build` (R3) and `*_status` (R4) | | the rest (CLI) |

Result: about 25 tools by default, down from 193, plus opt-in groups; the
`sirocampus` instance exposes `paper_lookup`, `rag_query` and `note_search`.

## Order of work

1. Agree on this spec and the table (user decision).
2. projio: groups and reasons in the registry, the test, `mcp.groups`;
   deprecation descriptions for the removed tools; regenerated instructions
   (three places).
3. Merged tools (`paper_lookup`, `biblio_job`, job tools for indexio and
   pipeio), each a thin adapter, with `keys` for docling.
4. Remove deprecated tools after one release; subsystem `mcp.py` modules
   keep only what the kept tools call.
