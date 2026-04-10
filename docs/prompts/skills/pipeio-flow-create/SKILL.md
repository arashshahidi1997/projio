---
name: pipeio-flow-create
description: >
  Guide agent through creating a new pipeline flow end-to-end: survey existing
  patterns, scaffold, write config and Snakefile, create scripts, set up datalad
  subdataset, and verify with dry-run.
metadata:
  short-description: Create a new pipeline flow step-by-step
  tags: [pipeline, pipeio, authoring]
  tooling:
    mcp:
      - server: projio
        tools:
          - pipeio_flow_list
          - pipeio_flow_status
          - pipeio_flow_new
          - pipeio_registry_scan
          - pipeio_mod_list
          - pipeio_mod_context
          - pipeio_mod_create
          - pipeio_script_create
          - pipeio_config_read
          - pipeio_config_init
          - pipeio_config_patch
          - pipeio_rule_stub
          - pipeio_rule_insert
          - pipeio_nb_create
          - pipeio_run
          - pipeio_registry_validate
          - pipeio_contracts_validate
          - codio_get
          - codio_discover
          - project_context
---

# pipeio Flow Create

Use this skill when the user wants to create a new pipeline flow from scratch.
Walks through the full lifecycle: survey → scaffold → config → Snakefile →
scripts → datalad → verify.

## Inputs

- `FLOW_NAME` (required): underscore-separated flow name (e.g., `preprocess_motion`)
- `DESCRIPTION` (optional): what this flow does
- `INPUT_SOURCE` (optional): where inputs come from (`raw` or a derivative flow name)

## Pre-flight: read pipeio-guide

```
skill_read("pipeio-guide")
```

Read the full pipeio ontology reference before proceeding. It defines directory
layout, config conventions, and MCP tool workflows.

## Step 1 — Survey existing flows

```
project_context()
pipeio_flow_list()
```

For each existing flow relevant to the new one:
```
pipeio_mod_list(flow=<name>)
pipeio_config_read(flow=<name>)
```

**Goal:** Learn the project's patterns — config structure, Snakefile style,
script conventions, registry groups. The new flow must be consistent with
existing flows.

Read at least one Snakefile and one script from an existing flow to extract
concrete patterns. Note:
- How `configfile` and `safe_load` override are used
- How `BidsPaths` adapter is instantiated
- How `in_paths` / `out_paths` helpers are called
- Script docstring format and snakemake mock pattern
- Which libraries are imported (check `codio_discover` for core libs)

## Step 2 — Scaffold

```
pipeio_flow_new(flow=FLOW_NAME)
```

This creates the directory structure under `code/pipelines/{FLOW_NAME}/`.
It is idempotent — safe to call on existing flows (fills gaps, never overwrites).

**Immediately after scaffolding:**

```
pipeio_registry_scan()
```

This registers the new flow in the pipeio registry. Without this step, no
other pipeio tool can find the flow.

### Hard rules

- **Do NOT overwrite scaffolded files** — `Makefile`, `notebook.yml`, and
  `publish.yml` are created by `flow_new` with correct defaults. Only edit
  `config.yml`, `Snakefile`, and `scripts/`.
- **Do NOT remove `configfile: "config.yml"`** — flows run from their own
  directory, so the relative path is correct.

## Step 3 — Write config.yml

The config defines inputs, outputs, and processing parameters.

### Template

```yaml
# -------------------------
# Pipeline inputs
# -------------------------
input_dir: "<raw or derivatives/upstream_flow>"
input_manifest: "<input_dir>/registry.yml or manifest.yml"

pybids_inputs:
  <input_name>:
    filters:
      suffix: '<suffix>'
      extension: '<ext>'
      datatype: '<datatype>'
    wildcards:
    - subject
    - session
    - task

# -------------------------
# Pipeline outputs
# -------------------------
output_dir: "derivatives/<FLOW_NAME>"
output_manifest: "derivatives/<FLOW_NAME>/manifest.yml"

registry:
  <group_name>:
    base_input: "<input_name>"
    bids:
      root: "<group_name>"
      datatype: "<datatype>"
    members:
      <member>: {suffix: "<suffix>", extension: "<ext>"}

# -------------------------
# Processing parameters
# -------------------------
<parameter_section>:
  <key>: <value>
```

### Conventions

- `input_manifest` / `output_manifest` — never `input_registry` / `output_registry`
- If reading from raw data: `input_dir: "raw"`, `input_manifest: "raw/registry.yml"`
- If reading from upstream flow: `input_dir: "derivatives/<upstream>"`,
  `input_manifest: "derivatives/<upstream>/manifest.yml"`
- Registry groups: each has `base_input` (pybids_inputs key), `bids` (root + datatype),
  and `members` (dict of member name → BIDS entities)
- Use YAML anchors (`&name`, `*name`) for repeated member sets
- Processing parameters at the end, grouped by section

Use `pipeio_config_init` or write manually, then `pipeio_config_patch` to add
registry groups incrementally.

## Step 4 — Write Snakefile

### Standard pattern

```python
from snakemake.utils import min_version
min_version("6.0")
from snakebids import generate_inputs, bids, set_bids_spec
set_bids_spec("v0_0_0")

from pathlib import Path
from yaml import safe_load
from sutil.repo_root import repo_abs

configfile: "config.yml"

# Override config with explicit load (runs from project root)
pipelinepath = repo_abs("code/pipelines/<FLOW_NAME>")
with open(pipelinepath / "config.yml", "r") as f:
    config = safe_load(f)

from pipeio.adapters.bids import BidsPaths

# Generate inputs from BIDS directory
inputs = generate_inputs(
    repo_abs(config["input_dir"]),
    config["pybids_inputs"],
)

# Load input registry and create path helpers
in_reg = safe_load(repo_abs(config["input_manifest"]).read_text())
in_paths = BidsPaths(in_reg, repo_abs(config["input_dir"]), inputs)
out_paths = BidsPaths(config["registry"], repo_abs(config["output_dir"]), inputs)

# --- Rules ---

rule all:
    input:
        inputs["<input_name>"].expand(
            out_paths("<group>", "<member>"),
        )

rule <rule_name>:
    input:
        <name>=in_paths("<group>", "<member>"),
    output:
        <name>=out_paths("<group>", "<member>"),
    params:
        <param>=config["<section>"]["<key>"],
    script:
        "scripts/<script_name>.py"

rule registry:
    """Write output manifest for downstream flows."""
    run:
        import yaml
        from pathlib import Path
        out = Path(repo_abs(config["output_manifest"]))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml.safe_dump(config["registry"], sort_keys=False))
```

### Key patterns

- **`configfile` + `safe_load` override**: Keep both. `configfile` is for Snakemake's
  internal config resolution. `safe_load` override ensures correct paths when
  Snakemake runs from the project root.
- **`BidsPaths` adapter**: Wraps registry + root + inputs into callable path helpers.
  Usage: `in_paths("group", "member")` returns a path pattern with wildcards.
- **Dynamic input functions**: For conditional inputs, define a function that returns
  a dict and use `unpack()`:
  ```python
  def _my_inputs(wildcards):
      inp = {"required": in_paths("group", "member").format(**dict(wildcards))}
      optional = some_path.format(**dict(wildcards))
      if Path(optional).exists():
          inp["optional"] = optional
      return inp

  rule my_rule:
      input: unpack(_my_inputs)
  ```
- **Registry rule**: Always include a rule that writes `output_manifest` from
  `config["registry"]` for downstream flow consumption.

## Step 5 — Write scripts

Use `pipeio_script_create` or `pipeio_mod_create` to scaffold, then fill in
the processing logic.

### Script template

```python
#!/usr/bin/env python
"""
Title: <script_name>.py
Status: DRAFT
Summary: <one-line description of what this script does>
"""

# %% Imports
from pathlib import Path
from types import SimpleNamespace

from sutil.repo_root import repo_abs
# <add domain-specific imports from codio core libs>

# %% Configuration / Snakemake Mock
if "snakemake" not in globals():
    print("Running in interactive mode (IDE)")
    snakemake = SimpleNamespace(
        input=SimpleNamespace(
            <name>="<path/to/test/input>",
        ),
        output=SimpleNamespace(
            <name>="<path/to/test/output>",
        ),
        params=SimpleNamespace(
            <param>=<default_value>,
        ),
    )

from pipeio.smk_log import setup_logging as setup_snakemake_logging
logger, _ = setup_snakemake_logging(
    globals().get("snakemake", None), name=Path(__file__).stem
)

# %% Parameter unpacking
INPUT = snakemake.input.<name>
OUTPUT = snakemake.output.<name>
PARAM = getattr(snakemake.params, "<param>", <default>)

# Normalize to absolute paths
if not Path(INPUT).is_absolute():
    INPUT = str(repo_abs(INPUT))

# Ensure output directory exists
Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)

# %% Processing
# <main processing logic>
```

### Conventions

- **Docstring**: Title / Status / Summary — always present
- **Snakemake mock**: Enables running the script in an IDE without Snakemake.
  Use test-subject paths for mock data.
- **`repo_abs`**: Always convert relative paths to absolute
- **`mkdir`**: Always create output parent directories
- **`# %%` cell markers**: Facilitate notebook-style execution in IDEs
- **Logging**: Use `pipeio.smk_log.setup_logging` for consistent log handling

Check which core libraries are available:
```
codio_discover(query="<capability needed>")
codio_get(name="<library>")
```

Import from core libraries rather than reimplementing. If a needed function
doesn't exist, consider adding it to the core library.

## Step 6 — Datalad subdataset

Before the first run, create a datalad subdataset for the derivative output:

```bash
datalad run-procedure create-reckless-subdataset derivatives/<FLOW_NAME>
```

The derivative directory name **must match the flow name** exactly.

If the project doesn't use datalad, skip this step.

## Step 7 — Verify

### Dry-run

```
pipeio_run(flow=FLOW_NAME, dryrun=True)
```

This validates that Snakemake can resolve all rules, inputs, and outputs
without actually running anything.

**Use `pipeio_run`** — never run `snakemake` or `conda run` manually.

### Validate

```
pipeio_registry_validate()
pipeio_contracts_validate()
```

Check that the registry is consistent and I/O contracts across flows resolve.

## Guardrails

- **Never overwrite scaffolded files** (Makefile, notebook.yml, publish.yml)
- **Never remove `configfile: "config.yml"`** from the Snakefile
- **Always call `pipeio_registry_scan`** after `pipeio_flow_new`
- **Always use `pipeio_run`** for execution — never manual conda/snakemake
- **Always create the datalad subdataset** before the first run
- **Survey first** — match existing project patterns before writing code
- **Do not create notebooks at this stage** — focus on getting the pipeline
  running. Notebooks come later for investigation and demos.

## Output format

Report:
1. Flow name and directory path
2. Config summary: input source, output groups, parameters
3. Rules created and their scripts
4. Dry-run result (pass/fail)
5. Any remaining steps (datalad subdataset, manual parameter tuning, etc.)
