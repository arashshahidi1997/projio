# Workflow: Integrate into Pipeline

**Phase:** Production (Grand Routine steps 8–9)
**Purpose:** Operationalize validated code as a Snakemake pipeline flow.
**Input:** Implemented and tested feature from `implement-feature.md`.
**Output:** Registered pipeline flow with Snakemake rules, config, and docs.

## When to use

When the exploration phase is complete: code works, tests pass, demo notebook
shows expected behavior, and the user wants to run at scale.

## Assumptions

This workflow assumes Snakemake as the workflow engine. The pipeio tools and
registry are workflow-engine-agnostic, but the scaffolding targets Snakemake
conventions.

## Steps

### 1. Survey existing pipelines

```
pipeio_flow_list()
pipeio_flow_status(pipe="<target_pipe>", flow="<existing_flow>")
```

Determine:
- Which pipe this belongs to (existing or new)
- Whether to add to an existing flow or create a new one
- What the output directory convention is

### 2. Create or update the flow

**New flow:**
```bash
pipeio flow new <pipe> <flow>
```

This scaffolds `config.yml` and `Snakefile`. Then populate:

**config.yml:**
```yaml
input_dir: "<input_source>"
output_dir: "derivatives/<pipe>"
registry:
  <group_name>:
    bids:
      root: "<group_root>"
    members:
      <member>: { suffix: "<suffix>", extension: "<ext>" }
```

**Snakemake rules:**
- Create scripts under `code/pipelines/<pipe>/<flow>/scripts/`
- Write rules that consume inputs and produce registered outputs
- All output paths should use the config registry — no hardcoded paths

### 3. Update the pipeline registry

```bash
pipeio registry scan
```

Or via MCP after the scan:
```
pipeio_flow_list()     # verify the new flow appears
```

### 4. Validate

```
pipeio_registry_validate()
```

Check for:
- [ ] Slug compliance (lowercase, underscores)
- [ ] Config path existence
- [ ] Code path existence
- [ ] No duplicate flow IDs

Also validate the flow config programmatically:
```python
from pipeio import FlowConfig
cfg = FlowConfig.from_yaml(config_path)
issues = cfg.validate_config()
```

### 5. Update documentation

- Flow docs under `docs/explanation/pipelines/pipe-<pipe>/flow-<flow>/`
- Update the idea/task notes with pipeline location

```
note_update(task_path, fields={"status": "pipeline-integrated"})
```

### 6. Test the pipeline

Run the Snakemake pipeline on a small test dataset:
```bash
snakemake --configfile code/pipelines/<pipe>/<flow>/config.yml -n  # dry run
snakemake --configfile code/pipelines/<pipe>/<flow>/config.yml -j4  # execute
```

## Output

1. **Pipeline flow** with Snakefile, config.yml, and scripts
2. **Registry** updated and validated
3. **Documentation** for the new flow
4. **Task note** updated to `pipeline-integrated`

## Transition

→ Hand off to `validate-and-deploy.md` for pre-flight and deployment.
