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
pipeio_registry_validate()       # registry consistency
pipeio_contracts_validate()      # I/O contracts, manifest chains
pipeio_mod_audit(flow)           # per-mod: scripts, docs, naming, contract drift
pipeio_nb_audit()                # notebook lifecycle issues
codio_validate()                 # code library registry
```

Fix errors before proceeding. Warnings are informational.

### 2. Execute at scale

Dry run first:
```
pipeio_run(flow, dryrun=True)
```

Then execute:
```
pipeio_run(flow, cores=4)
pipeio_run_status()              # monitor progress
```

### 3. Sync and publish notebooks

```
pipeio_nb_sync_flow(flow)        # sync all stale notebooks
pipeio_nb_pipeline(flow, name)   # sync → publish → collect → nav (per demo notebook)
```

### 4. Collect and publish docs

```
pipeio_docs_collect()            # collect flow docs + notebooks + publish.yml artifacts
pipeio_docs_nav()                # generate nav fragment
pipeio_mkdocs_nav_patch()        # apply nav to mkdocs.yml
```

Preview and deploy:
```
site_detect()                    # verify site framework
site_serve()                     # preview locally
site_deploy()                    # deploy
```

### 5. Record completion

```
note_update(task_path, fields={"status": "deployed"})
```

### 6. Rebuild search indexes

After new docs and notebooks are published:
```
indexio_sources_sync(build=True)
```

This ensures new pipeline documentation is searchable in future sessions.

## Output

1. **Validated** registry, contracts, mods, notebooks
2. **Executed** pipeline (or dry-run confirmed)
3. **Published** notebooks and documentation (with DAG, reports, scripts via publish.yml)
4. **Updated** search indexes
5. **Closed** task note

## If problems are found at scale

Return to `explore-idea.md` with a new idea note referencing this pipeline run.
Do not patch the pipeline without recording the reasoning.
