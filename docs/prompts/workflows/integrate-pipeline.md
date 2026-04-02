# Workflow: Integrate into Pipeline

**Phase:** Production (Grand Routine steps 8–9)
**Purpose:** Operationalize validated code as a Snakemake pipeline flow.
**Input:** Implemented and tested feature from `implement-feature.md`.
**Output:** Registered pipeline flow with Snakemake rules, config, and docs.

## Prerequisites

Read `skill_read("pipeio-guide")` for the full pipeio ontology, directory layout,
and tool reference. All tools use `flow` (not `pipe`) addressing.

## When to use

When the exploration phase is complete: code works, demo notebook shows expected
behavior, and the user wants to run at scale.

## Steps

### 1. Survey existing flows

```
pipeio_flow_list()
pipeio_flow_status(flow="<target>")
pipeio_cross_flow()
```

Determine:
- Whether to add a mod to an existing flow or create a new flow
- What upstream flows this depends on (via `input_manifest`)
- What the derivative directory convention is (`derivatives/{flow}/`)

### 2. Create or augment the flow

**New flow:**
```bash
pipeio flow new <flow_name>    # idempotent — fills in missing dirs
```

This scaffolds: Snakefile, config.yml, publish.yml, Makefile, rules/, scripts/,
docs/index.md, notebooks/explore/.src/, notebooks/demo/.src/, notebook.yml.

**Config:**
```
pipeio_config_init(flow, input_dir="...", output_dir="derivatives/<flow>")
```

Or patch an existing config:
```
pipeio_config_patch(flow, registry_entry={...}, apply=True)
```

### 3. Create the mod

```
pipeio_mod_create(flow, mod, description="...", inputs={...}, outputs={...})
```

This creates:
- `scripts/{mod}.py` with Snakemake I/O template (+ compute library import via codio)
- `docs/{mod}/theory.md` + `spec.md` stubs

If promoting from a notebook:
```
pipeio_nb_promote(flow, name, mod)
```

### 4. Wire the rules

Generate and review:
```
pipeio_rule_stub(flow, rule_name, inputs={...}, outputs={...}, script="scripts/{mod}.py")
```

Insert into Snakefile:
```
pipeio_rule_insert(flow, rule_name, rule_text="...", after_rule="...")
```

### 5. Fill in documentation

**theory.md** — use biblio for citations:
```
rag_query(corpus="bib", query="<method>")
citekey_resolve(citekey)
biblio_docling(citekey, query="method algorithm")
```
Write rationale with `[@citekey]` pandoc citations.

**spec.md** — regenerate from code:
```
pipeio_mod_doc_refresh(flow, mod, facet="spec", apply=True)
```

### 6. Validate

```
pipeio_registry_scan()           # rediscover flows
pipeio_registry_validate()       # slug compliance, paths
pipeio_contracts_validate()      # I/O contracts, manifest chains
pipeio_mod_audit(flow, mod)      # script existence, doc coverage, naming
```

Dry run:
```
pipeio_run(flow, dryrun=True)
```

### 7. Create demo notebook

```
pipeio_nb_create(flow, name="demo_<mod>", kind="demo", mod="<mod>")
```

Execute, verify outputs, publish:
```
pipeio_nb_pipeline(flow, name)
```

## Output

1. **Flow** with Snakefile, config.yml, scripts, docs
2. **Registry** updated and validated
3. **Mod docs** — theory.md with citations, spec.md with I/O contracts
4. **Demo notebook** published to site

## Transition

→ Hand off to `validate-and-deploy.md` for pre-flight and deployment.
