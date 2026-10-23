# Run tasks: the CLI and pixi

A projio project has no task runner of its own. Each job has one place:

| Job | Where | Example |
|-----|-------|---------|
| Environments | pixi (`pixi.toml`) | `pixi install`, `pixi run -e compute python ...` |
| The project's own tasks | pixi `[tasks]` | `pixi run test`, `pixi run fig`, `pixi run snakemake ...` |
| projio and notio operations | their CLIs | `projio sync`, `projio site serve`, `notio manuscript build paper --format pdf` |
| Agent workflows | skills (and MCP tools where a shell is not enough) | see [agent interface layers](../specs/agent-interface-layers.md) |

pixi tasks run in pixi's own cross-platform shell, so the same `pixi run`
works on Linux, macOS and Windows; they support dependencies between tasks
(`depends-on`), cached `inputs`/`outputs`, `cwd` and `env`. projio and notio
are on PATH from the global install (`uv tool install projio`), or run them
through the project env with `pixi run projio ...` when the project's
`pixi.toml` depends on projio.

## What can I do in this project?

```bash
projio tasks
```

prints the routine commands for this project: sync, status, the site, and
one group per manuscript and master document that exists, e.g.

```
projio sync                                     # synchronize project metadata, skills and indexes
projio site serve                               # serve the documentation site locally
notio manuscript build paper --format pdf       # manuscript 'paper' to PDF
```

`pixi task list` shows the project's own tasks; `projio --help` and
`notio --help` show everything else.

## Remotes, siblings and saving

Setting up DataLad siblings (GitHub, GitLab, RIA), checking credentials and
saving and pushing are procedures with decisions in them, not menu items:
the `projio-remotes` skill walks an agent (or you) through them with the
preview-first `projio sibling ...` commands.

## New and existing projects

- `projio init` scaffolds a `pixi.toml` (a package gets an editable install of
  itself and a `dev` feature with `test`, `build`, `check`) and no task file.
- A project that already has a `Makefile` keeps it: projio still regenerates
  `.projio/projio.mk` for it (`code.task_runner: make`, chosen automatically).
  That path is Unix/macOS only and is deprecated. To move off it, put the
  targets you use into pixi `[tasks]` (`save` and `push` become `datalad
  save` / `datalad push`, or the `projio-remotes` skill), then delete the
  `Makefile` and `.projio/projio.mk`.

## Why not make or go-task

`make` does not run on Windows without extra tooling. A generated go-task
menu was tried (2026-09/10): it held four aliases of `projio` commands, and
agents ran `pixi run` about 2,700 times against 37 `task` calls in the same
period. pixi already gives cross-platform tasks; the CLI is the menu.
