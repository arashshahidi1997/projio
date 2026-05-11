# Permissions and bounded context

!!! note "Sources & anchors"
    - **Stack component:** Agentic
    - **Canonical artifact:** `pixecog/.claude/settings.json` (multi-host SSH + pixi + marimo-pair)
    - **Workshop session:** Day-3 PM session 1 (agent setup)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## The agent is a collaborator with bounded permissions

A Claude Code session is not a sandbox. When the agent calls `Edit`, files
are written. When it calls `Bash`, commands run with the user's privileges.
The agent's default posture is therefore to ask before acting; the project
overrides that default with an explicit allow-list of operations that may
proceed without confirmation. **The allow-list is a contract: the
researcher tells the agent, in writing, what it may do quietly.**

That contract lives in `.claude/settings.json` at the repo root. Editing
it is editing the project's risk surface — adding a `Bash(rm:*)` line is
not a productivity tweak.

## The shape of `.claude/settings.json`

Two top-level keys do the work. `permissions.allow` is a list of *patterns*
that pre-approve operations; `allowedTools` is a flat list of *tools* that
the agent may call without per-call confirmation. Most patterns appear in
both — a quirk of the surface that is worth taking seriously (see [Hard
rule: list each MCP wildcard twice](#hard-rule-list-each-mcp-wildcard-twice)
below).

The canonical artifact is `pixecog/.claude/settings.json`. Three slices
of it teach the format:

### Slice 1: tool wildcards

```json
"permissions": {
  "allow": [
    "mcp__projio__*",
    "mcp__worklog__*",
    "mcp__sirocampus__*",
    "Read",
    "Glob",
    "Grep",
    "Edit(/storage2/arash/projects/pixecog/**)",
    "Write(/storage2/arash/projects/pixecog/**)"
  ]
}
```

Read-class tools (`Read`, `Glob`, `Grep`) are pre-approved without scoping
— the agent may read freely. `Edit` and `Write` are *scoped to the
project's own tree* with a glob; an edit outside `/storage2/arash/projects/pixecog/`
will trigger a confirmation prompt. The three `mcp__<server>__*` wildcards
pre-approve every tool from each MCP server.

### Slice 2: explicit Bash command patterns

```json
"Bash(git:*)",
"Bash(python:*)",
"Bash(conda:*)",
"Bash(pytest:*)",
"Bash(make:*)",
"Bash(pixi search *)",
"Bash(ssh gamma1 uptime)",
"Bash(ssh gamma2 uptime)",
"Bash(ssh gamma3 uptime)",
"Bash(ssh gamma4 uptime)",
"Bash(ssh gpu uptime)",
"Bash(ssh spikesort uptime)",
"Bash(bash /home/arash/.claude/skills/marimo-pair/scripts/discover-servers.sh*)"
```

The pattern is `Bash(<command-prefix>)`. `Bash(git:*)` allows `git status`,
`git diff`, `git log` — every git subcommand. `Bash(pixi search *)`
allows `pixi search numpy` but not `pixi install`; the literal space and
glob is narrower than `Bash(pixi:*)` would be. The multi-host SSH lines
allow exactly the `uptime` probe on each compute host — useful for
checking host availability without granting arbitrary remote shell access.

This slice is **the canonical "multi-host SSH + pixi + marimo-pair"
surface** in the survey. It mirrors the project's compute layout:
`gamma1..4` for general compute, `gpu`/`spikesort` for specialised
hardware, `beta`/`theta` for additional nodes. The marimo-pair entry
allows the discovery script that finds running marimo servers across
those hosts.

### Slice 3: extra read scopes

```json
"Read(/storage2/arash/projects/pixecog/.projio/codio/mirrors/sirotalab--spikeinterface_srlab/**)",
"Read(/storage2/arash/projects/pixecog/code/lib/cogpy/**)",
"Read(/storage2/arash/projects/pixecog/code/lib/labbox/**)",
"Read(/storage2/arash/projects/pixecog/code/lib/labpy/**)",
"Read(/storage2/arash/**)",
"Read(/storage/share/sirocampus/**)"
```

These extend `Read` beyond the project root: into the codio-mirrored copy
of the lab's SpikeInterface fork, into each `code/lib/{name}/`
subdataset, and into the lab-shared `sirocampus` tree at
`/storage/share/sirocampus/`. The wildcard `Read(/storage2/arash/**)`
broadens the scope further to the user's whole project area — useful for
cross-project reads when the `sirocampus` MCP server doesn't expose what
the agent needs.

These three slices — tool wildcards, explicit Bash patterns, extra read
scopes — are the **three axes of bounded context**. Pick patterns from
each axis that match the project's compute layout, dependency tree, and
risk tolerance.

## Hard rule: list each MCP wildcard twice

From the `feedback_mcp_permissions.md` convention: MCP wildcards must
appear in **both** `permissions.allow` and `allowedTools`. Listing them
only in `permissions.allow` will still surface a confirmation prompt for
every tool call — the auto-approval path requires both lists to agree.

`pixecog/.claude/settings.json` follows the rule, as does every other
project in the cohort:

```json
{
  "permissions": {
    "allow": ["mcp__projio__*", "mcp__worklog__*", "..."]
  },
  "allowedTools": ["mcp__projio__*", "mcp__worklog__*", "..."]
}
```

This duplication is mechanical and a frequent source of confusion. The
workshop introduces it as a setup quirk to internalise, not a design
principle to defend.

## Cohort divergence: Bash shape mirrors the project's compute

The survey records that the *MCP wildcards* are universal — every project
pre-approves `mcp__projio__*`, `mcp__sirocampus__*`, `mcp__worklog__*` —
but the Bash shape varies:

| Project | Distinctive Bash patterns | Why |
|---|---|---|
| **projio** | `git/python/pip/pytest/make` baseline | library-style maintenance |
| **cogpy** | + `mypy/ruff/black/isort/tox/nox/coverage` | typing/lint stack |
| **pixecog** | + `pixi search *`, `ssh gamma{1..4} uptime`, multi-host SSH probes, marimo-pair discovery | multi-host research compute |
| **gecog** | minimal Bash baseline | minimal — cleanest "default" |
| **msol** | + `pixi run -e analysis marimo *`, `pixi install *`, marimo-pair scripts | pixi + marimo workflow |

The pattern is **the Bash allow-list mirrors the project's compute
layout.** A library repo (cogpy) allow-lists its quality-gate tooling;
a multi-host study project (pixecog) allow-lists the hosts and discovery
scripts it uses; a single-host pixi project (msol) allow-lists its pixi
environment commands.

When you scaffold a new project, start from the gecog baseline (minimal)
and add patterns *as they prove necessary in the session log*. Do not
pre-populate operations you have not yet performed manually.

## What the allow-list does not protect against

The allow-list is an *approval gate*, not a *security boundary*. A Bash
pattern of `Bash(python:*)` allows the agent to run `python script.py`
with anything `script.py` contains — including shell-outs to other
commands. The pattern catches the literal command shape; it does not
sandbox what that command does.

This means two things in practice:

1. **`Edit`/`Write` scoping does real work.** The glob-scoped `Edit` and
   `Write` patterns prevent the agent from quietly writing outside the
   project. Keep them scoped tightly; broaden them only when a specific
   workflow requires it (e.g. editing a sibling project, in which case
   prefer adding it as a fourth MCP server — see
   [`claude-code-and-mcp.md`](claude-code-and-mcp.md)).

2. **Bash patterns gate *intent*, not *effect*.** Reviewing the session
   transcript matters. The allow-list shape determines *what the agent
   may try without asking*; the audit trail in `docs/log/` is what tells
   you afterward whether it should have.

## additionalDirectories and defaultMode

The pixecog settings include two more keys:

```json
"additionalDirectories": ["/tmp"],
"defaultMode": "auto"
```

`additionalDirectories` extends the agent's filesystem awareness beyond
the project root — `/tmp` is added so the agent may use temp files
without prompts. `defaultMode: "auto"` selects the auto-approval
behaviour: pre-approved patterns proceed silently; unrecognised
operations surface a confirmation prompt. `defaultMode: "ask"` would
force a prompt for everything except pre-approved patterns; `bypassPermissions`
would skip prompts entirely (do not use this in research projects).

The workshop default is `auto` with a tightly-scoped allow-list. That is
the contract: *the agent may do exactly what we already permitted, and
must ask for anything else.*

<!-- TODO: E4 — Permission-scope diagram: toggle MCP servers / Bash
patterns / Read globs → highlighted slice of project surface the agent
can touch. See _outline.md §F #E4. -->

## Honest gap: hooks

`.claude/settings.json` supports a `hooks` key for cross-cutting
automation — running a command on `Stop`, on `PreToolUse`, on `UserPromptSubmit`.
**No project in the cohort currently defines hooks.** Permissions are
per-project; pre-commit-style cross-cutting policy is absent.

The handbook introduces hooks as **graduated adoption** rather than
baseline practice. A project that has stabilised its allow-list and
wants to enforce a lint pass before every `Edit`, or capture every `Stop`
event into the worklog, can add hooks — but the baseline is hooks-free.
See [`99-honest-gaps.md`](../99-honest-gaps.md) for the broader
cross-cutting gap context.

## Further reading

- **[Claude Code settings reference](https://docs.anthropic.com/en/docs/claude-code/settings)** — `permissions.allow`, `allowedTools`, `additionalDirectories`, `defaultMode`, and hook configuration.
