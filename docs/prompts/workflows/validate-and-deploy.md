# Workflow: Validate and Deploy

**Phase:** Production (final checks and deployment)
**Purpose:** Run pre-flight validation and deploy documentation/reports.
**Input:** Integrated pipeline from `integrate-pipeline.md`.
**Output:** Validated registry, synced notebooks, deployed docs site.

## When to use

After pipeline integration is complete and the user wants to run at scale
or publish results.

## Steps

### 1. Pre-flight validation

Run all validators in parallel:

```
pipeio_registry_validate()
codio_validate()
```

Check notebook sync state:
```
pipeio_nb_status()
```

Fix any errors before proceeding. Warnings are informational.

### 2. Execute at scale

Run the pipeline over the target dataset scope:
```bash
snakemake --configfile <config> -j <cores> --rerun-incomplete
```

### 3. Sync and publish notebooks

If notebooks need syncing (reported by `pipeio_nb_status`):
```bash
pipeio nb sync    # requires pipeio[notebook]
pipeio nb publish
```

### 4. Build and deploy documentation

```
site_detect()        # verify site framework
site_serve()         # preview locally
```

Or from the command line:
```bash
make docs            # build
make docs-serve      # serve locally
```

### 5. Record completion

```
note_update(task_path, fields={"status": "deployed"})
```

### 6. Rebuild search indexes

After new docs and notebooks are published:
```
indexio_build()
```

This ensures the new pipeline documentation and notebook outputs are
searchable in future sessions.

## Output

1. **Validated** registry and code intelligence
2. **Executed** pipeline (or dry-run confirmed)
3. **Published** notebooks and documentation
4. **Updated** search indexes
5. **Closed** task note

## If problems are found at scale

Return to step 1 of `explore-idea.md` with a new idea note that
references this pipeline run. Do not patch the pipeline without
recording the reasoning.
