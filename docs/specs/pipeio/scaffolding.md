# pipeio: Scaffolding Specification

## Purpose

Scaffolding creates new flows and mods from templates, ensuring they follow the canonical directory structure and are properly integrated into the registry.

## Flow Scaffolding (`pipeio flow new`)

### Current State (pixecog)

The template lives at `code/pipelines/_template/flow/` and is applied via `cp -R` + `sed -i` to replace `__PIPE__` / `__FLOW__` placeholders.

### Template Structure

```
_template/flow/
├── Snakefile              # workflow entry point with __PIPE__/__FLOW__ vars
├── config.yml             # skeleton config with input/output dirs
├── Makefile               # notebook lifecycle targets
├── scripts/
│   └── example_step.py    # script template with mock snakemake object
├── notebooks/
│   ├── notebook.yml       # empty notebook config
│   └── explore_registry_bootstrap/
│       └── explore_registry_bootstrap.py   # bootstrap notebook
├── report/                # RST captions directory
└── _docs/
    └── README.md          # guidance on writing mod-level docs
```

### pipeio Implementation

```
$ pipeio flow new preprocess ecephys
```

1. **Copy template** — copy `_template/flow/` to `<pipelines_dir>/<pipe>/<flow>/`
2. **Variable substitution** — replace `__PIPE__` → `preprocess`, `__FLOW__` → `ecephys` in all files (Jinja2 or simple string replacement)
3. **Create output directory** — `mkdir -p derivatives/<pipe>/`
4. **Update registry** — add the new flow entry to `.pipeio/registry.yml`
5. **Create docs stubs** — scaffold `docs/explanation/pipelines/pipe-<pipe>/flow-<flow>/index.md`
6. **Post-scaffold report** — print what was created and next steps

### Options

```
pipeio flow new <pipe> <flow> [OPTIONS]

Options:
  --template PATH       Custom template directory (default: built-in)
  --pipelines-dir PATH  Override pipelines directory
  --no-registry         Skip registry update
  --no-docs             Skip docs stub creation
  --dry                 Show what would be created without creating it
```

### Template Variables

| Variable | Replacement |
|----------|-------------|
| `__PIPE__` | Pipe name (e.g., `preprocess`) |
| `__FLOW__` | Flow name (e.g., `ecephys`) |
| `__PIPE_FLOW_ID__` | `pipe-<pipe>_flow-<flow>` |
| `__DATE__` | Current date (ISO format) |

### Validation

Before scaffolding:

1. Target directory must not already exist
2. Pipe name and flow name must pass `slug_ok()` validation
3. Template directory must exist and contain at least `Snakefile` or `config.yml`

## Mod Scaffolding (Future)

```
$ pipeio mod new preprocess/ieeg atlas
```

Creates:

1. `scripts/atlas.py` — script template with rule prefix `atlas_`
2. `_docs/mod-atlas/` — mod documentation stub (Theory/Spec/Delta)
3. Updates `registry.yml` with the new mod entry

## Built-in Templates

pipeio ships with a minimal built-in template (`pipeio/templates/flow/`) covering:

- `Snakefile` — minimal Snakemake workflow skeleton
- `config.yml` — input/output/registry skeleton
- `notebooks/notebook.yml` — empty notebook config
- `scripts/example_step.py` — script template

Projects can override with their own templates via `--template` or by placing templates at `.pipeio/templates/flow/`.
