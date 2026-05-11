# Claude Code and MCP

!!! note "Sources & anchors"
    - **Stack component:** Agentic
    - **Canonical artifact:** `pixecog/.mcp.json` + `gecog/.mcp.json`
    - **Workshop session:** Day-3 PM session 1 (agent setup)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## The editor and the protocol

Claude Code is a terminal-based coding agent that edits files, runs shell
commands, and answers questions about the repository it is launched inside.
It is the editor in the agentic layer of this stack — the place where a
researcher pairs with a model on a real working tree, not a chat window
detached from code.

The Model Context Protocol (MCP) is the wire format that lets Claude Code
talk to *project-aware servers*. An MCP server is an ordinary process that
exposes a set of named tools over JSON-RPC; Claude Code lists those tools
and calls them on the agent's behalf. From the agent's point of view, an
MCP tool looks identical to a built-in one — `rag_query(...)` is no
different from `Read(...)`.

The architectural consequence: **the agent's knowledge of a project comes
from MCP tools, not from in-context retrieval.** When a Claude Code session
starts in a projio-aware repo, the agent does not need to be told what
notes exist, which papers have been ingested, or how flows are registered.
It calls `project_context()`, `note_list()`, `pipeio_flow_list()`, and
similar tools. Each returns structured output curated for that project.

## The `.mcp.json` server set

A project's MCP server set is declared in `.mcp.json` at the repo root. The
canonical artifact for the workshop is `pixecog/.mcp.json`:

```json
{
  "mcpServers": {
    "projio": {
      "command": "/storage/share/python/environments/Anaconda3/envs/rag/bin/python",
      "args": ["-m", "projio.mcp.server"],
      "env": { "PROJIO_ROOT": "/storage2/arash/projects/pixecog" }
    },
    "sirocampus": {
      "command": "/storage/share/python/environments/Anaconda3/envs/rag/bin/python",
      "args": ["-m", "projio.mcp.server"],
      "env": { "PROJIO_ROOT": "/storage/share/sirocampus" }
    },
    "worklog": {
      "command": "/storage/share/python/environments/Anaconda3/envs/rag/bin/python",
      "args": ["-m", "worklog.mcp_server"]
    }
  }
}
```

Each entry declares a server name (the prefix the agent uses to call its
tools, e.g. `mcp__projio__rag_query`), a Python interpreter, and an
optional environment block. The `projio` and `sirocampus` entries both run
`python -m projio.mcp.server` but with different `PROJIO_ROOT` values —
**the same server binary, two different roots.** That is how the agent
queries two projects in one session: each MCP server is rooted at a
different repository.

## The three-server baseline

Every projio-managed project in the cohort wires the same three servers:

| Server | What it exposes | Roughly how many tools |
|---|---|---|
| **`projio`** (rooted at this repo) | code, notes, papers, figures, pipelines, sites for the current project | ~150 |
| **`sirocampus`** (rooted at the lab-shared dataset) | shared notes, libraries, papers across the lab | same surface, different root |
| **`worklog`** | cross-project registry, captures, queue, goals — covered in [`80-orchestration/`](../80-orchestration/worklog-overview.md) | ~40 |

This is the **three-server baseline.** A new projio project starts with
exactly these three. The `projio` server is the project's own knowledge
layer; `sirocampus` is the lab-shared layer (same software, lab-shared
data); `worklog` is the orchestration layer.

`projio init` scaffolds `.mcp.json` with this baseline. The agent does not
configure it — the repository configures the agent.

## The fourth server: when to add one

`gecog/.mcp.json` is the cohort's only example of a fourth MCP server:

```json
"cogpy": {
  "command": "/storage/share/python/environments/Anaconda3/envs/rag/bin/python",
  "args": ["-m", "projio.mcp.server"],
  "env": { "PROJIO_ROOT": "/storage2/arash/projects/cogpy" }
}
```

The gecog session is editing analysis code that depends heavily on cogpy
as a library. Wiring `cogpy` as a fourth server gives the agent direct
access to cogpy's notes, codio catalog, and module documentation — without
needing to leave the gecog session or paste cogpy code into context.

The pattern generalises: **add a fourth server when a dependency project
is consulted often enough that round-tripping through `Read(/storage2/...)`
becomes friction.** A library you import is not a candidate; a library
whose internals you regularly read, whose notes you regularly cite, and
whose codio catalog you regularly query is.

## What an MCP tool returns

MCP tools are not thin wrappers over `Read`. They are *structured queries*
that return curated output:

- `project_context()` → a summary of the current project: kind, runtime
  conventions, code tier layout, pipeio flows, active code library catalog.
- `note_list(kind="task")` → a list of task notes with frontmatter, ordered
  by recency, with status and assigned model.
- `pipeio_flow_status("preprocess_ieeg")` → the flow's mods, recent rule
  invocations, log paths, and manifest state.
- `rag_query("how do we handle TTL artifacts?")` → ranked passages with
  citations into the project's indexed corpus (code, papers, notes).

The agent never reads the underlying YAML or markdown — the MCP tool does
the parsing and returns the question-shaped answer. That keeps the
agent's context window populated with conclusions, not source text.

## Why this is qualitatively different

A Claude Code session without MCP can edit files and run shell commands,
but it has no project-shaped index. To find a citation it greps; to run a
flow it reads the Makefile; to know what notes exist it walks directories.
Each of those is a token-expensive workaround.

A Claude Code session with the three-server baseline starts every
conversation with structured access to: every note in the project; every
ingested paper with its docling extracts; every registered pipeline flow
and its current run state; every figure spec; every code library in the
project's codio catalog; and the cross-project task queue. **The agent
asks a question, the project answers it.** The handbook reader should
expect this to feel different from "AI in the editor" — it is closer to
"the project explains itself to a collaborator."

The remaining three chapters of this section cover what bounds that
collaborator: permissions ([`permissions-and-bounded-context.md`](permissions-and-bounded-context.md)),
discoverable workflows ([`skills.md`](skills.md)), and how observations
flow into dispatched work ([`captures-tasks-queues.md`](captures-tasks-queues.md)).

## Further reading

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — installation, `.mcp.json` configuration, CLAUDE.md memory hierarchy, and the tool-permission model.
- **[Model Context Protocol](https://modelcontextprotocol.io/)** — the JSON-RPC wire format; reference for writing a new MCP server from scratch.
