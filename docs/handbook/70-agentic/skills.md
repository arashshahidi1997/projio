# Skills

!!! note "Sources & anchors"
    - **Stack component:** Agentic
    - **Canonical artifact:** `.projio/skills/` listings across cohort; `pixecog/.projio/skills/pixecog-flow-setup/`
    - **Workshop session:** Day-3 PM session 1 sidebar
    - **Outline:** [`_outline.md`](../_outline.md) §B

## What a skill is

A skill is a markdown file named `SKILL.md` with a YAML frontmatter
header. It is discoverable, slash-invokable, and read on demand by the
agent through the `skill_read(name)` MCP tool. The frontmatter declares
the skill's name and what MCP tools it expects to use; the body is a
prompt — a procedural template the agent follows when the skill is
invoked.

A skill is not code that runs. It is a *workflow checklist* that the
agent reads at the moment it needs it. The leverage comes from
discoverability: `agent_instructions()` lists every skill available in
the current project, ecosystem skills and project-local skills together,
so the agent knows what graded workflows the repository has codified.

## Two locations, project overrides ecosystem

| Location | What lives there |
|---|---|
| `src/projio/data/skills/<name>/SKILL.md` (in the projio package) | **ecosystem skills** — bundled with projio, available in every projio-managed project |
| `<repo>/.projio/skills/<name>/SKILL.md` | **project-local skills** — only available in this project; same-name skills override the ecosystem version |

Override semantics matter. A project that has its own version of
`pipeio-flow-create` (e.g. with project-specific path conventions) places
it at `.projio/skills/pipeio-flow-create/SKILL.md` and the ecosystem copy
is shadowed for that project. The agent does not see two skills with the
same name; it sees the project's version.

## The SKILL.md format

`pixecog/.projio/skills/pixecog-flow-setup/SKILL.md` is the canonical
project-local artifact:

```yaml
---
name: pixecog-flow-setup
description: >
  Project-specific conventions for creating pipeline flows in pixecog.
  Layers pixecog patterns (cogpy env, raw layout, datalad subdatasets,
  labpy/cogpy imports, BidsPaths adapter) on top of the generic
  pipeio-flow-create skill.
metadata:
  short-description: Pixecog-specific flow creation guide
  tags: [pipeline, pipeio, pixecog, authoring]
tooling:
  mcp:
    - server: projio
      tools:
        - pipeio_flow_list
        - pipeio_flow_new
        - pipeio_mod_context
        - pipeio_config_read
        - pipeio_run
        - codio_get
    - server: sirocampus
      tools:
        - codio_func_doc
        - codio_get
---
# Pixecog Flow Setup
Use this skill when creating a new pipeline flow in the pixecog project.
This skill layers pixecog-specific conventions on top of the generic
`pipeio-flow-create` skill.
```

The frontmatter is a structured signature. `description` is what
`agent_instructions()` shows when the agent surveys what's available;
`tags` aid retrieval; `tooling.mcp` lists the MCP tools the skill body
will invoke (a hint, not a requirement, but it makes skill-shaped
permissions audits easier).

The body is plain markdown. Section headings (When to use, Workflow,
Hard rules) are conventional. The body cites other skills by name —
`pixecog-flow-setup` layers on `pipeio-flow-create`, so its body says so
and instructs the agent to read the upstream skill first via
`skill_read("pipeio-flow-create")`.

## Cohort adoption: graduated, not baseline

The survey records that skill authoring is real but not yet universal:

| Project | Project-local skills (`.projio/skills/`) | User-level skills (`.claude/skills/`) |
|---|---|---|
| projio | `figio-guide`, `projio-setup` (2) | `gitnexus` (1) |
| cogpy | `cogpy-dev` (1) | none |
| **pixecog** | `pixecog-flow-setup` (1) | none |
| **gecog** | 0 | none |
| **msol** | 0 | none |

Three of five projects have any project-local skills; two have none.
That is the honest cohort state, and the workshop frames skills
accordingly: **skills are graduated adoption.** A project does not need
skills to participate in the agentic layer; it adds skills *when a
workflow has been performed manually enough times that codifying it
saves the next session.*

The full set of bundled ecosystem skills (≈25, including
`figio-guide`, `pipeio-guide`, `marimo-session`, `pipeio-nb-extract`,
`questio-*` (7), `biblio-batch-curate`, `codelib-discovery`,
`mcp-tool-scaffold`, `rag-query`, `idea-capture`) is available to every
projio-managed project automatically. They cover the cross-cutting
agentic workflows — figure building, pipeline authoring, literature
curation, idea capture. Project-local skills exist to layer
project-specific conventions on top.

## When to write a project-local skill

Three signals justify a skill:

1. **You have done the workflow manually more than twice and would do
   it the same way again.** Skills codify repeated procedure. The first
   pass is exploration; the second pass is confirming the procedure;
   the third pass is when writing it down pays off.

2. **A new collaborator (human or agent) would need a checklist to do
   it correctly.** The skill body is the checklist. If you find
   yourself writing the same instructions into three task notes —
   "remember to update the manifest, regenerate the docs, sync the
   subdataset" — that is the skill talking.

3. **An ecosystem skill is *almost* right but misses project-specific
   conventions.** `pipeio-flow-create` is the generic skill for new
   pipeline flows; `pixecog-flow-setup` layers on it because pixecog
   has its own cogpy env, raw layout, and BidsPaths import that the
   generic skill cannot know about. The layering pattern is canonical:
   the project skill says "do the generic skill, then add these
   project-specific steps."

## When *not* to write a skill

- The workflow is one-shot — you will not run it again. A note is
  enough; a skill would be ceremonial.
- The workflow is *already an MCP tool*. Wrapping a single tool call in
  a skill adds indirection without leverage. Skills are for sequences,
  contracts, and conventions — not for renaming individual tools.
- The workflow is captured in code (a Makefile target, a script). The
  agent can call that target; a skill that just says "run `make foo`"
  is a wrapper around a wrapper.

## Discovery and invocation

The agent finds skills through `agent_instructions()`, which returns
ecosystem + project skills together. Each appears as a line: name,
short description, where it lives. The agent reads a skill's body
through `skill_read(name)` — this is the actual fetch; the body is
only loaded into context when the skill is about to be used.

For a human user, every skill is also exposed as a Claude Code slash
command: `pixecog-flow-setup` becomes `/pixecog-flow-setup`. Typing that
in a session causes the agent to read the skill's body and follow it.
The slash-command surface and the MCP discovery surface are the same
set; **`/foo` and `skill_read("foo")` resolve to the same SKILL.md.**

`permissions_sync()` reconciles project skill listings — when you add a
new skill to `.projio/skills/`, run `permissions_sync` (or the wrapper
`projio sync`) to regenerate the indexes that `agent_instructions()`
consults. Skills are not auto-discovered every session; they are
indexed at sync time.

## Honest gap

Skills are present in 3/5 projects; gecog and msol have none. The
handbook treats skills as a graduated practice — useful when the
threshold conditions (§"When to write a project-local skill") are met,
unnecessary otherwise. Workshop participants are not asked to author a
skill on Day 3; they are shown the format and pointed at
`agent_instructions()` so they can read what already exists. See
[`99-honest-gaps.md`](../99-honest-gaps.md) for the broader cohort
unevenness in agentic adoption.

## Further reading

- **[Claude Code §Memory and context](https://docs.anthropic.com/en/docs/claude-code/memory)** — the CLAUDE.md memory hierarchy that skills plug into; project-level vs user-level instructions.
