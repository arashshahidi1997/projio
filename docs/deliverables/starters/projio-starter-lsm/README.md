# projio-starter-lsm

> A 10-minute starter project. Adopt or adapt.
>
> Companion to the LSM Future Skills 2026 talk *"Open-science conventions as
> agent infrastructure"*.

This repository is the smallest plausible *stack-aware research project*:
a BIDS-shaped data root, one Snakemake rule, a Marimo notebook, a Quarto
report, and an MCP server (projio) that an agent can navigate. Clone it, ask
the agent one question, and see what "workflow-as-queryable-object" feels
like from the inside.

## What's here

```
projio-starter-lsm/
├── .claude/
│   └── settings.json           # pre-permissioned tool surface
├── .mcp.json                   # one MCP server (projio), one entry point
├── .gitignore
├── pixi.toml                   # pinned projio + compute env (pixi)
├── .projio/
│   ├── config.yml              # minimal projio config
│   └── indexio/
│       └── config.yaml         # notes-corpus search index config
├── data/
│   └── raw/                    # BIDS-shaped
│       ├── dataset_description.json
│       ├── participants.tsv
│       ├── make_synthetic_eeg.py           # regenerates the signal below
│       └── sub-01/
│           └── eeg/
│               ├── sub-01_task-rest_eeg.txt    # tiny synthetic signal
│               └── sub-01_task-rest_eeg.json   # BIDS sidecar (sampling rate)
├── code/
│   └── pipelines/
│       └── demo/
│           ├── Snakefile       # one rule: raw → cleaned
│           └── scripts/
│               └── clean.py
├── notebooks/
│   └── explore.py              # marimo reactive notebook
├── docs/
│   ├── log/
│   │   ├── idea/
│   │   │   └── idea-example.md
│   │   └── result/             # agent-written outputs land here
│   └── deliverables/
│       └── report.qmd          # Quarto report scaffold
└── README.md                   # this file
```

Running the demo pipeline writes cleaned output to `data/derivatives/demo/`
(generated, gitignored).

## Install (5 minutes)

```bash
# 0. Install pixi if you don't have it (one-time, system-wide)
curl -fsSL https://pixi.sh/install.sh | bash

# 1. Clone the starter (the scaffold is already in place; do NOT run `projio init`)
git clone github.com/arashshahidi1997/projio-starter-lsm
cd projio-starter-lsm

# 2. Set up the env (pinned projio version; see pixi.toml)
pixi install

# 3. Sync: validate config and install the render filters (non-destructive)
pixi run projio sync
```

Step 3 is non-destructive and needs no network: it validates the projio config
and installs the citation and include filters. Semantic search over your notes
(`rag_query`) is an optional add-on; see "Semantic search over your notes" below.

Then **open the directory in Claude Code**. Claude Code is Anthropic's terminal
CLI for agent-assisted editing; install instructions at
<https://docs.anthropic.com/claude-code>. (Not the same thing as the chat
interface at claude.ai.) The `.mcp.json` and `.claude/settings.json` in this
repo are pre-configured so the projio MCP server starts automatically; the
`pixi run` wrapper ensures it finds the right Python even if your system shell
points elsewhere.

The starter's `pixi.toml` pins `projio==0.1.2` so this README's commands keep
working under projio API drift. If you want the latest projio, bump the pin
yourself.

## Try one MCP query (2 minutes)

In Claude Code, ask:

> *"Summarise the idea in `docs/log/idea/` and propose one next step."*

The agent will:

1. Read the idea note in `docs/log/idea/`, then `clean.py` and the raw signal,
   using the project's layout to find them.
2. Notice that the idea proposes a **1 Hz** high-pass while `clean.py` applies
   **0.5 Hz**, surface that as a decision for you, pick a burst threshold, and
   propose writing a result note in `docs/log/result/`.

That's the smallest possible loop: a claim on disk, an agent that reads the
project's own files to check it, and a receipt written back. Everything else is
a generalisation.

Want to run the rest of the loop by hand?

```bash
pixi run snakemake -s code/pipelines/demo/Snakefile --cores 1   # raw → cleaned
pixi run marimo edit notebooks/explore.py                        # explore
pixi run quarto render docs/deliverables/report.qmd              # report
```

## Semantic search over your notes (optional)

`rag_query` is a projio MCP tool for semantic recall across many notes. It needs
an embedding backend and a built index, which this minimal starter leaves out to
stay quick to install. To turn it on:

```bash
pixi add --pypi sentence-transformers                        # embedding backend (pulls torch; a larger download)
pixi run indexio build --config .projio/indexio/config.yaml  # build the notes index
```

After that, `rag_query(query, corpus="notes")` returns real hits over
`docs/log/`. With a single idea note the agent barely needs it; the payoff shows
up once a project has dozens of notes.

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

The conventions in this starter (**receipts on disk, permissioned
tools, file-mediated handoff**) do not depend on projio. If you
already have:

- a different version-control story (plain git + git-annex; dvc; …),
- a different pipeline runner (nextflow, dagster, airflow, …),
- a different notebook tool (Jupyter; observable; …),
- a different MCP server (filesystem-MCP, git-MCP, your own),

then adopt the *layout* of this starter and swap the implementations.
The agent doesn't care which MCP server it's calling; it cares about
what the project's files say about its own state.

## How to contribute

This repo is a teaching artifact. If you build a variant (different
domain, different stack, different MCP server), please open an issue
linking your repo. A directory of "stack-aware starters in the wild"
is more useful to the community than any one author's implementation.

## License

CC0 / Public Domain. Copy freely.
