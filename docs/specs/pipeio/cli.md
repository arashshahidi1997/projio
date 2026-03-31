# pipeio: CLI Specification

## Entry Point

```
pipeio [-h] {init,flow,nb,registry,contracts,docs} ...
```

Installed via `pip install pipeio`, entry point `pipeio = "pipeio.cli:main"`.

## Commands

### `pipeio init`

Scaffold `.pipeio/` in the current project.

```
pipeio init [--pipelines-dir PATH] [--root PATH]
```

Creates:

```
.pipeio/
├── registry.yml          # empty pipeline registry
└── templates/
    └── flow/             # default flow template
```

If `.projio/config.yml` exists, adds a `pipeio:` section.

### `pipeio flow`

Flow management and navigation.

```
pipeio flow list [--pipe PIPE]                    # list all flows
pipeio flow new <pipe> <flow> [--template PATH]   # scaffold a new flow
pipeio flow ids                                    # print flow names (for shell completion)
pipeio flow path <flow>                            # print absolute code_path for a flow
pipeio flow config <flow>                          # print absolute config_path for a flow
pipeio flow deriv <flow>                           # print absolute output_dir (derivative directory)
pipeio flow smk <flow> [smk_args...]               # run snakemake in flow's context
pipeio flow status <flow>                          # show flow status (config, outputs, mods)
pipeio flow targets <flow> [options]               # resolve output paths for registry entries
    --group <name>, -g                             # filter by registry group
    --member <name>, -m                            # filter by registry member
    --entity <key=value>, -e                       # entity filters (repeatable)
    --expand, -x                                   # glob for all matching paths
pipeio flow run <flow> [targets] [options]         # launch snakemake in screen session
    --cores <n>, -c                                # number of cores
    --dryrun, -n                                   # dry run
    --filter <key=value>, -f                       # wildcard filter (repeatable)
pipeio flow log <flow> [--lines <n>]               # tail latest run log (default 40 lines)
pipeio flow mods <flow>                            # list mods and their rules
```

### `pf` — Shell Flow Navigator

The `pf` helper (`packages/pipeio/bin/pf.sh`) provides quick flow navigation, similar to `wg` for projects. Source it in your shell profile.

```bash
pf                          # list all flows
pf <flow>                   # cd to flow's code directory
pf <flow> smk [args]        # run snakemake in flow context
pf <flow> deriv             # cd to flow's derivative directory
pf <flow> path              # print flow code_path
pf <flow> config            # print flow config_path
pf <flow> status            # show flow status
pf <flow> targets [opts]    # resolve output paths
pf <flow> run [opts]        # launch snakemake in screen session
pf <flow> log [--lines N]   # tail latest run log
pf <flow> mods              # list mods and rules
```

Includes bash/zsh completion for flow names via `pipeio flow ids`.

### `pipeio nb`

Notebook lifecycle management. Requires `pipeio[notebook]`.

```
pipeio nb pair     [--config PATH] [--entry NAME]
pipeio nb sync     [--config PATH] [--entry NAME] [--dry]
pipeio nb exec     [--config PATH] [--entry NAME] [--timeout SECS]
pipeio nb publish  [--config PATH] [--entry NAME] [--format FORMAT]
pipeio nb status   [--config PATH]
pipeio nb new      --mode MODE NAME [--flow PIPE/FLOW]
```

Default config: `notebooks/notebook.yml` relative to CWD.

### `pipeio registry`

Pipeline registry management.

```
pipeio registry scan [--pipelines-dir PATH] [--output PATH]
pipeio registry validate [--registry PATH]
```

### `pipeio contracts`

Pipeline I/O validation.

```
pipeio contracts validate
```

### `pipeio docs`

Pipeline documentation.

```
pipeio docs collect       # collect flow docs + notebooks → docs/pipelines/
pipeio docs nav           # generate MkDocs nav fragment
```

## Common Options

| Option | Description |
|--------|-------------|
| `--root PATH` | Project root (default: auto-detect via `.projio/` or `.git`) |
| `--dry` | Dry run — show what would happen without executing |
| `--verbose` | Verbose output |
| `--quiet` | Suppress non-error output |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error / not implemented |
| 2 | Validation failure (contracts, registry) |

## Auto-Detection

When `--root` is not specified, pipeio walks up from CWD looking for:

1. `.pipeio/` directory
2. `.projio/config.yml` with a `pipeio:` section
3. `.git` directory (last resort)

When inside a flow directory (e.g., `code/pipelines/preprocess/ieeg/`), pipeio auto-detects the current pipe and flow from the path structure.
