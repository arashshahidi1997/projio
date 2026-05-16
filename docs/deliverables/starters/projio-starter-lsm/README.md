# projio-starter-lsm

> A 10-minute starter project. Adopt or adapt.
>
> Companion to the LSM Future Skills 2026 talk *"Treating your research
> workflow as a manipulable object"*.

This repository is the smallest plausible *stack-aware research project*:
a BIDS-shaped data root, DataLad versioning, one Snakemake rule, a
Marimo notebook, a Quarto report, and an MCP server (projio) that an
agent can navigate. Clone it, ask the agent one question, see what
"workflow-as-queryable-object" feels like from the inside.

## What's here

```
projio-starter-lsm/
├── .claude/                   # pre-permissioned tool surface
│   └── settings.json
├── .mcp.json                  # one MCP server (projio), one entry point
├── data/
│   └── raw/                   # BIDS-shaped placeholder
│       ├── dataset_description.json
│       ├── participants.tsv
│       └── sub-01/
│           └── eeg/
│               └── sub-01_task-rest_eeg.txt   # tiny synthetic signal
├── code/
│   └── pipelines/
│       └── demo/
│           ├── Snakefile      # one rule: raw → cleaned
│           └── scripts/
│               └── clean.py
├── notebooks/
│   └── explore.py             # marimo reactive notebook
├── docs/
│   ├── log/
│   │   ├── idea/
│   │   │   └── idea-example.md
│   │   └── result/            # agent-written outputs land here
│   └── deliverables/
│       └── report.qmd         # Quarto report scaffold
├── .projio/
│   └── config.yml             # minimal projio config
├── pyproject.toml             # pixi or pip env
└── README.md                  # this file
```

## Install (5 minutes)

```bash
# 0. Install pixi if you don't have it (one-time, system-wide)
curl -fsSL https://pixi.sh/install.sh | bash

# 1. Clone the starter (the scaffold is already in place — do NOT run `projio init`)
git clone github.com/arashshahidi1997/projio-starter-lsm
cd projio-starter-lsm

# 2. Set up the env (pinned projio version; see pyproject.toml)
pixi install

# 3. Sync (auto-discover code/lib, validate config — non-destructive)
pixi run projio sync
```

Then **open the directory in Claude Code**. Claude Code is Anthropic's
terminal CLI for agent-assisted editing; install instructions at
<https://docs.anthropic.com/claude-code>. (Not the same thing as the
chat interface at claude.ai.) The `.mcp.json` and `.claude/settings.json`
in this repo are pre-configured so the projio MCP server starts
automatically; the `pixi run` wrapper ensures it finds the right Python
even if your system shell points elsewhere.

The starter's `pyproject.toml` pins `projio==0.X.Y` so this README's
commands keep working under projio API drift. If you want the latest
projio, bump the pin yourself.

## Try one MCP query (2 minutes)

In Claude Code, ask:

> *"Summarise the idea in `docs/log/idea/` and propose one next step."*

The agent will:

1. Call `rag_query` (one of ~70 MCP tools projio exposes) against the
   notes corpus
2. Read `docs/log/idea/idea-example.md`
3. Reply with a one-paragraph summary and a follow-up

That's the smallest possible loop. Everything else is a generalisation.

## What's missing on purpose

This starter is **not** the four-day workshop in miniature. It's the
shortest path from `git clone` to "I see what the pattern is." The
following are deferred to the workshop or the handbook:

- Multi-agent dispatch (`schedule_queue(after=...)` chains or live SDK
  agents)
- Cross-project orchestration (worklog)
- The full notio note-type taxonomy (idea, task, result, meeting, …)
- figio composed figures and the manuscript subsystem
- Cohort-scale BIDS layouts and derivative chaining

If you want any of those, see [the handbook](https://arashshahidi1997.github.io/projio/handbook/)
or come to the workshop.

## Adapt to your own stack

The conventions in this starter — **receipts on disk, permissioned
tools, file-mediated handoff** — do not depend on projio. If you
already have:

- a different version-control story (plain git + git-annex; dvc; …),
- a different pipeline runner (nextflow, dagster, airflow, …),
- a different notebook tool (Jupyter; observable; …),
- a different MCP server (filesystem-MCP, git-MCP, your own),

then adopt the *layout* of this starter and swap the implementations.
The agent doesn't care which MCP server it's calling; it cares about
what the project's files say about its own state.

## How to contribute

This repo is a teaching artifact. If you build a variant — different
domain, different stack, different MCP server — please open an issue
linking your repo. A directory of "stack-aware starters in the wild"
is more useful to the community than any one author's implementation.

## License

CC0 / Public Domain. Copy freely.
