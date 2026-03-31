# pipeio: MCP Tools Specification

## Purpose

pipeio exposes tools through projio's MCP server for AI agent access to pipeline authoring and discovery. pipeio is an agent-facing layer — it does not own execution (Snakemake), provenance (DataLad), path resolution (snakebids), or app lifecycle (snakebids).

### Tool Categories (v2)

| Category | Count | Status |
|----------|-------|--------|
| Flow & registry | 4 | **Keep** |
| Notebook lifecycle | 10 | **Keep** |
| Mod management | 4 | **Keep** |
| Rule authoring | 4 | **Keep** |
| Config authoring | 3 | **Keep** (config_read, config_patch, config_init) |
| Contracts & tracking | 3 | **Keep** (contracts_validate, cross_flow, completion) |
| Documentation | 4 | **Keep** |
| Path resolution | 1 | **Keep** (target_paths) |
| DAG & reporting | 2 | **Thin adapter** (dag_export, report) |
| Logging | 1 | **Thin adapter** (log_parse) |
| Execution | 4 | **Deprecated** — migrate to `datalad run` (run, run_status, run_dashboard, run_kill) |

## Tool Registration

Tools are registered in `src/projio/mcp/server.py` following the same pattern as codio, biblio, and notio. The implementation lives in two layers:

1. **`src/projio/mcp/pipeio.py`** — thin MCP wrappers with availability checks
2. **`packages/pipeio/src/pipeio/mcp.py`** — actual tool logic

## Tools

### Flow & Registry

#### `pipeio_flow_list`

List pipeline flows, optionally filtered by pipe.

```
pipeio_flow_list(pipe: str = "") → dict
```

**Returns:**
```json
{
  "flows": [
    {
      "name": "ieeg",
      "pipe": "preprocess",
      "code_path": "code/pipelines/preprocess/ieeg",
      "config_path": "code/pipelines/preprocess/ieeg/config.yml",
      "doc_path": "docs/explanation/pipelines/pipe-preprocess/flow-ieeg",
      "mods": {"badchannel": {...}, "linenoise": {...}}
    }
  ]
}
```

#### `pipeio_flow_status`

Show status of a specific pipeline flow.

```
pipeio_flow_status(pipe: str, flow: str) → dict
```

**Returns:**
```json
{
  "pipe": "preprocess",
  "flow": "ieeg",
  "config_exists": true,
  "output_dir": "derivatives/preprocess",
  "registry_groups": ["raw_zarr", "badlabel", "filter", "interpolate"],
  "notebook_count": 2,
  "docs_exists": true
}
```

#### `pipeio_registry_scan`

Scan the filesystem for pipelines and rebuild the registry.

```
pipeio_registry_scan() → dict
```

#### `pipeio_registry_validate`

Validate pipeline registry consistency.

```
pipeio_registry_validate() → dict
```

**Returns:**
```json
{
  "valid": false,
  "errors": ["Flow DGgamma/DGgamma: config_path is null"],
  "warnings": ["Flow DGgamma/DGgamma: slug 'DGgamma' does not pass naming convention"],
  "stats": {"pipes": 8, "flows": 12, "mods": 31}
}
```

### Notebook Lifecycle

#### `pipeio_nb_status`

Show notebook sync and publication status across all flows. Optionally filter by pipe, flow, or notebook name.

```
pipeio_nb_status(pipe: str = "", flow: str = "", name: str = "") → dict
```

#### `pipeio_nb_create`

Scaffold a new percent-format notebook with bootstrap cells and register in notebook.yml.

```
pipeio_nb_create(pipe: str, flow: str, name: str, kind: str = "investigate", description: str = "") → dict
```

#### `pipeio_nb_sync`

Sync a specific notebook via jupytext (bidirectional: py2nb or nb2py).

```
pipeio_nb_sync(
    pipe: str, flow: str, name: str,
    formats: list[str] = ["ipynb", "myst"],
    direction: str = "py2nb",
    force: bool = False,
) → dict
```

#### `pipeio_nb_publish`

Publish a notebook's myst markdown to `docs/pipelines/<pipe>/<flow>/notebooks/`.

```
pipeio_nb_publish(pipe: str, flow: str, name: str) → dict
```

#### `pipeio_nb_analyze`

Static structural analysis of a percent-format notebook: imports, RunCard fields, PipelineContext usage, section headers, cogpy calls.

```
pipeio_nb_analyze(pipe: str, flow: str, name: str) → dict
```

#### `pipeio_nb_exec`

Execute a notebook via papermill with optional parameter overrides.

```
pipeio_nb_exec(pipe: str, flow: str, name: str, params: dict = {}, timeout: int = 600) → dict
```

#### `pipeio_nb_update`

Update notebook metadata (status, description, kind) in `notebook.yml`.

```
pipeio_nb_update(
    pipe: str, flow: str, name: str,
    status: str = "",        # draft | active | stale | promoted | archived
    description: str = "",
    kind: str = "",          # investigate | explore | demo | validate
) → dict
```

#### `pipeio_nb_diff`

Show sync state between `.py` and paired `.ipynb`: which file is newer, whether in sync, and the recommended sync direction. Call before `nb_sync` to decide direction.

```
pipeio_nb_diff(pipe: str, flow: str, name: str) → dict
```

Returns: `status` (synced | py_newer | ipynb_newer | unpaired | orphaned_ipynb | missing), `recommendation`, `executed`, `cell_count`.

#### `pipeio_nb_lab`

Build/refresh a Jupyter Lab symlink manifest in `.projio/pipeio/lab/`. Creates `<pipe>/<flow>/<name>.ipynb` symlinks pointing to real notebook files. Optionally syncs py→ipynb first.

```
pipeio_nb_lab(pipe: str = "", flow: str = "", sync: bool = True) → dict
```

Returns: `lab_dir`, `linked` (list of name/pipe/flow/target), `stale_cleaned`, `count`.

#### `pipeio_nb_pipeline`

Composite: sync → publish → docs_collect → docs_nav (optionally site_build).

```
pipeio_nb_pipeline(pipe: str, flow: str, name: str, formats: list[str] = None, build_site: bool = False) → dict
```

### Mod Management

#### `pipeio_mod_list`

List mods for a specific pipeline flow.

```
pipeio_mod_list(pipe: str, flow: str = "") → dict
```

#### `pipeio_mod_resolve`

Resolve modkey strings (`pipe-X_flow-Y_mod-Z`) into metadata and doc locations.

```
pipeio_mod_resolve(modkeys: list[str]) → dict
```

#### `pipeio_mod_context`

Bundled read context for a mod: rules, scripts content, doc content, config params, bids signatures. Returns everything needed to understand and work on a mod in one MCP call.

```
pipeio_mod_context(pipe: str, flow: str = "", mod: str = "") → dict
```

**Returns:**
```json
{
  "pipe": "preprocess", "flow": "ieeg", "mod": "badlabel",
  "rules": [{"name": "badlabel_detect", "inputs": {...}, "outputs": {...}}],
  "scripts": {"badlabel.py": "...contents..."},
  "doc": "...markdown contents...",
  "config_params": {"threshold": 0.5},
  "bids_signatures": {"npy": "sub-{subject}_ses-{session}_suffix-ieeg.npy"}
}
```

#### `pipeio_mod_create`

Scaffold a new pipeline mod: `scripts/<mod>.py` + `docs/mod-<mod>.md`.

When `inputs`/`outputs`/`params_spec` are provided, generates Snakemake I/O unpacking and parameter binding so only processing logic needs filling in. When `use_pipeline_context=True`, generates PipelineContext setup boilerplate.

```
pipeio_mod_create(
    pipe: str, flow: str, mod: str,
    description: str = "",
    from_notebook: str = "",
    inputs: dict = {},        # {var_name: description}
    outputs: dict = {},       # {var_name: description}
    params_spec: dict = {},   # {var_name: description}
    use_pipeline_context: bool = False,
) → dict
```

**Example with I/O wiring:**
```python
pipeio_mod_create(
    pipe="preprocess", flow="ieeg", mod="badlabel",
    description="Detect bad channels via feature-based labeling",
    inputs={"lfp": "raw LFP signal", "channels": "channel metadata"},
    outputs={"npy": "labeled channel array", "featuremap": "feature visualization"},
    params_spec={"threshold": "detection threshold"},
)
```

**Generated script includes:**
```python
def main(snakemake):
    # --- Inputs ---
    lfp = Path(snakemake.input.lfp)  # raw LFP signal
    channels = Path(snakemake.input.channels)  # channel metadata

    # --- Outputs ---
    npy = Path(snakemake.output.npy)  # labeled channel array
    featuremap = Path(snakemake.output.featuremap)  # feature visualization

    # --- Parameters ---
    threshold = snakemake.params.threshold  # detection threshold

    # --- Processing (TODO: implement) ---
    npy.parent.mkdir(parents=True, exist_ok=True)
    pass
```

### Rule Authoring

#### `pipeio_rule_list`

Parse Snakefiles and list rules with input/output/params signatures and mod membership.

```
pipeio_rule_list(pipe: str, flow: str = "") → dict
```

#### `pipeio_rule_stub`

Generate a syntactically correct Snakemake rule stub from a contract spec. Returns text for review — does NOT insert.

```
pipeio_rule_stub(
    pipe: str, flow: str, rule_name: str,
    inputs: dict = {},   # {name: bids_pattern} or {name: {source_rule, member}}
    outputs: dict = {},  # {name: bids_kwargs_dict} or {name: bids_pattern_str}
    params: dict = {},   # {name: config_dot_path}
    script: str = "",
) → dict
```

#### `pipeio_rule_insert`

Insert a Snakemake rule into the correct `.smk` or Snakefile.

Provide `rule_text` directly, or `inputs`/`outputs`/`params`/`script` to generate it (same spec as rule_stub). Auto-selects target file by mod prefix if not specified.

```
pipeio_rule_insert(
    pipe: str, flow: str = "", rule_name: str = "",
    rule_text: str = "",       # pre-formatted rule text (optional)
    target_file: str = "",     # .smk or Snakefile basename (auto if omitted)
    after_rule: str = "",      # insert after this rule (append if omitted)
    inputs: dict = {},         # for generation
    outputs: dict = {},
    params: dict = {},
    script: str = "",
) → dict
```

**Returns:**
```json
{
  "inserted": true,
  "rule_name": "badlabel_detect",
  "target_file": "code/pipelines/preprocess/ieeg/badlabel.smk",
  "rule_text": "rule badlabel_detect:\n    input:\n        ...",
  "after_rule": "raw_zarr"
}
```

#### `pipeio_rule_update`

Patch an existing Snakemake rule by merging new sections. Adds entries to input/output/params without overwriting existing ones. Returns a unified diff preview; `apply=True` writes the file.

```
pipeio_rule_update(
    pipe: str, flow: str = "", rule_name: str = "",
    add_inputs: dict = {},    # {name: spec} to add
    add_outputs: dict = {},
    add_params: dict = {},    # {name: config_dot_path}
    set_script: str = "",     # replace script path
    apply: bool = False,
) → dict
```

**Returns:**
```json
{
  "rule_name": "badlabel_detect",
  "source_file": "code/pipelines/preprocess/ieeg/badlabel.smk",
  "diff": "--- a/...\n+++ b/...\n...",
  "applied": false,
  "conflicts": []
}
```

### Config Authoring

#### `pipeio_config_read`

Read and parse a flow's config.yml with YAML anchor resolution and bids() signature mapping.

```
pipeio_config_read(pipe: str, flow: str = "") → dict
```

**Returns:** `pybids_inputs`, `registry` (resolved), `member_sets`, `params`, `bids_signatures`, `resolved_patterns`, `has_anchors`.

#### `pipeio_config_patch`

Validate and optionally patch a flow's config.yml. Returns unified diff preview; `apply=True` writes.

```
pipeio_config_patch(
    pipe: str, flow: str = "",
    registry_entry: dict = {},  # {group_name: group_dict}
    params_entry: dict = {},    # {section: {key: value}}
    apply: bool = False,
) → dict
```

#### `pipeio_config_init`

Scaffold a new flow's `config.yml` with pybids_inputs and registry structure. Errors if config already exists (use `config_patch` for existing configs). Auto-sets `output_registry` to `{output_dir}/pipe-{pipe}_flow-{flow}_registry.yml`.

```
pipeio_config_init(
    pipe: str, flow: str = "",
    input_dir: str = "",
    output_dir: str = "",
    pybids_inputs: dict = {},
    registry_groups: dict = {},
    params: dict = {},
) → dict
```

**Returns:**
```json
{
  "created": "code/pipelines/preprocess/ieeg/config.yml",
  "pipe": "preprocess",
  "flow": "ieeg",
  "output_dir": "derivatives/preprocess",
  "registry_groups": ["raw_zarr", "badlabel"],
  "warnings": [],
  "preview": "input_dir: raw\n..."
}
```

### Path Resolution

#### `pipeio_target_paths`

Resolve output paths for a flow's registry entries via `PipelineContext`.

```
pipeio_target_paths(
    pipe: str, flow: str = "",
    group: str = "", member: str = "",
    entities: dict = None,  # e.g. {"sub": "01", "ses": "04"}
    expand: bool = False,
) → dict
```

**Modes:**

- **List** (no group): returns all groups, members, and path pattern templates.
- **Resolve** (group + member + entities): returns a single concrete path and whether it exists.
- **Expand** (`expand=True`): globs the filesystem for all matching paths, filtered by entities.

**Returns (resolve mode):**
```json
{
  "pipe": "preprocess", "flow": "ieeg",
  "mode": "resolve",
  "group": "badlabel", "member": "npy",
  "entities": {"sub": "01", "ses": "04"},
  "path": "/project/derivatives/preprocess/badlabel/sub-01/ses-04/sub-01_ses-04_suffix-npy.npy",
  "exists": true
}
```

### Contracts & Tracking

#### `pipeio_contracts_validate`

Validate I/O contracts for all flows.

```
pipeio_contracts_validate() → dict
```

#### `pipeio_cross_flow`

Map output_registry → input_registry chains across flows. Detects stale or broken references.

```
pipeio_cross_flow(pipe: str = "", flow: str = "") → dict
```

#### `pipeio_completion`

Check per-session completion by comparing expected outputs (from registry) against filesystem.

```
pipeio_completion(pipe: str, flow: str = "", mod: str = "") → dict
```

### DAG & Reporting

Thin adapters over Snakemake's native graph and report features.

#### `pipeio_dag_export`

Export rule/job DAG via Snakemake's native graph output (`--rulegraph`, `--dag`, `--d3dag`).

```
pipeio_dag_export(
    pipe: str, flow: str = "",
    graph_type: str = "rulegraph",   # rulegraph | dag | d3dag
    output_format: str = "dot",       # dot | mermaid | svg | json
) → dict
```

**Returns:**
```json
{
  "pipe": "preprocess", "flow": "ieeg",
  "graph_type": "rulegraph",
  "output_format": "dot",
  "content": "digraph snakemake_dag { ... }"
}
```

#### `pipeio_report`

Generate a Snakemake HTML report with runtime stats, provenance, and annotated outputs. Supports `target` param for partial-output flows.

```
pipeio_report(
    pipe: str, flow: str = "",
    output_path: str = "",    # auto-generated if empty
    target: str = "",         # rule to run first, e.g. "report"
) → dict
```

### Logging

#### `pipeio_log_parse`

Parse Snakemake log files for completed/failed rules, timing, and error summaries.

```
pipeio_log_parse(pipe: str, flow: str = "", run_id: str = "", log_path: str = "") → dict
```

### Execution (deprecated — migrating to datalad run)

These tools manage Snakemake execution via screen sessions and a custom `runs.json` state file. They duplicate concerns better handled by DataLad run records and will be replaced.

#### `pipeio_run` *(deprecated)*

Launch a Snakemake run in a detached screen session.

```
pipeio_run(
    pipe: str, flow: str = "", targets: list[str] = [],
    cores: int = 1, dryrun: bool = False,
    use_conda: bool = False,
    extra_args: list[str] = [],
    wildcards: dict = None,
) → dict
```

Auto-resolves snakemake via conda env wrapping (cogpy env). Uses `stdbuf -oL` for unbuffered output, passes `--directory` to Snakemake. `use_conda` enables `--use-conda`. `wildcards` maps to snakebids `--filter-{key} {value}` flags for single-session scoping.

#### `pipeio_run_status` *(deprecated)*

Check status of a running or completed Snakemake run.

```
pipeio_run_status(run_id: str = "", pipe: str = "", flow: str = "") → dict
```

#### `pipeio_run_dashboard` *(deprecated)*

Aggregate status of all tracked runs.

```
pipeio_run_dashboard() → dict
```

#### `pipeio_run_kill` *(deprecated)*

Kill a running Snakemake run by terminating its screen session.

```
pipeio_run_kill(run_id: str) → dict
```

### Documentation

#### `pipeio_docs_collect`

Collect flow-local docs and notebook outputs into `docs/pipelines/`.

```
pipeio_docs_collect() → dict
```

#### `pipeio_docs_nav`

Generate MkDocs nav YAML fragment for `docs/pipelines/`.

```
pipeio_docs_nav() → dict
```

#### `pipeio_mkdocs_nav_patch`

Apply the pipeio docs nav fragment to mkdocs.yml.

```
pipeio_mkdocs_nav_patch() → dict
```

#### `pipeio_modkey_bib`

Generate a BibTeX file with `@misc` entries for all registered pipeline mods.

```
pipeio_modkey_bib(output_path: str = "", project_name: str = "") → dict
```

## Agent Routing

For agent instructions (CLAUDE.md / `agent_instructions` tool):

| Intent | MCP tool | Do NOT |
|--------|----------|--------|
| List pipelines | `pipeio_flow_list()` | Parse registry YAML manually |
| Check flow status | `pipeio_flow_status(pipe, flow)` | Read config.yml directly |
| Scaffold a new config | `pipeio_config_init(pipe, flow)` | Create config.yml manually |
| Read config | `pipeio_config_read(pipe, flow)` | Parse config.yml directly |
| Patch config | `pipeio_config_patch(pipe, flow)` | Edit config.yml directly |
| Scaffold a mod | `pipeio_mod_create(pipe, flow, mod)` | Create script/doc files manually |
| Generate rule text | `pipeio_rule_stub(pipe, flow, name)` | Write rule text manually |
| Insert rule into file | `pipeio_rule_insert(pipe, flow, name)` | Edit Snakefiles manually |
| Patch an existing rule | `pipeio_rule_update(pipe, flow, name)` | Edit Snakefiles manually |
| Resolve output paths | `pipeio_target_paths(pipe, flow, group, member, entities)` | Construct BIDS paths manually |
| Export DAG | `pipeio_dag_export(pipe, flow, graph_type)` | Run snakemake --rulegraph manually |
| Generate report | `pipeio_report(pipe, flow)` | Run snakemake --report manually |
| Mod context (bundled read) | `pipeio_mod_context(pipe, flow, mod)` | Multiple reads manually |
| Update notebook metadata | `pipeio_nb_update(pipe, flow, name, status)` | Edit notebook.yml directly |
| Launch a run | `pipeio_run(pipe, flow, wildcards={"subject": "01"})` | Run snakemake in terminal |
| Check notebook state | `pipeio_nb_status()` | Compare file timestamps manually |
| Validate registry | `pipeio_registry_validate()` | Run validation scripts directly |

### Authoring chain

The recommended tool chain for creating a new pipeline step:

1. `pipeio_config_init` — scaffold config.yml (if new flow)
2. `pipeio_config_patch` — add registry groups and params
3. `pipeio_mod_create` — scaffold script with I/O wiring
4. `pipeio_rule_stub` or `pipeio_rule_insert` — create and insert the rule
5. `pipeio_rule_update` — refine rules incrementally
6. `pipeio_contracts_validate` — verify I/O contracts

## Graceful Degradation

All tools check for pipeio availability:

```python
def _pipeio_available() -> bool:
    try:
        import pipeio
        return True
    except ImportError:
        return False
```

When pipeio is not installed, tools return:

```json
{"error": "pipeio_flow_list requires the pipeio package. Install with: pip install pipeio"}
```
