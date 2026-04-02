---
name: pipeio-guide
description: >
  Reference guide for the pipeio ontology — flow/mod hierarchy, directory layout,
  config conventions, notebook workspaces, mod docs, and MCP tools. Read this
  before creating or modifying pipeline flows.
metadata:
  short-description: pipeio ontology reference
  tags: [pipeline, pipeio, reference]
  tooling:
    mcp:
      - server: projio
        tools:
          - pipeio_flow_list
          - pipeio_flow_status
          - pipeio_mod_list
          - pipeio_mod_context
          - pipeio_mod_create
          - pipeio_nb_create
          - pipeio_nb_status
          - pipeio_rule_list
          - pipeio_rule_stub
          - pipeio_rule_insert
          - pipeio_config_read
          - pipeio_config_patch
          - pipeio_registry_scan
          - pipeio_registry_validate
          - pipeio_contracts_validate
          - pipeio_mod_audit
          - pipeio_mod_doc_refresh
          - pipeio_script_create
          - pipeio_nb_promote
          - pipeio_docs_collect
---

# pipeio Guide

pipeio is the agent-facing authoring and discovery layer for computational pipelines. It provides structured access to pipeline metadata and safe authoring operations via MCP tools.

## Ontology

### Flow

A **flow** is a self-contained snakebids app. One flow = one derivative directory. Flow names are globally unique, underscore-separated (e.g., `preprocess_ieeg`, `spectrogram_burst`).

Directory: `code/pipelines/{flow}/`

### Mod

A **mod** is a logical group of Snakemake rules within a flow, identified by rule name prefix. Rules named `filter_bandpass`, `filter_notch` belong to mod `filter`.

### Rule

A Snakemake rule. Three execution modes:
- `script:` — runs a Python script from `scripts/`
- `shell:` — runs a CLI command
- `run:` — inline Python

Multiple rules can share the same script with different params/inputs/outputs.

## Flow Directory Structure

```
code/pipelines/{flow}/
├── Snakefile                     # workflow definition
├── config.yml                    # I/O config (see below)
├── publish.yml                   # site publish config (dag, report, scripts)
├── Makefile                      # convenience targets
├── rules/                        # optional per-mod rule files ({mod}.smk)
├── scripts/                      # rule scripts (may be shared across rules)
├── docs/                         # flow-local documentation
│   ├── index.md                  # flow overview
│   └── {mod}/                    # per-mod faceted docs
│       ├── theory.md             # scientific rationale + citations
│       ├── spec.md               # I/O contracts, parameters
│       └── delta.md              # optional: current issues, plans
└── notebooks/
    ├── notebook.yml              # notebook registry
    ├── explore/                  # exploratory (never published)
    │   ├── .src/{name}.py        # percent-format source
    │   ├── .myst/{name}.md       # generated MyST
    │   └── {name}.ipynb          # generated Jupyter
    └── demo/                     # demos (published to site)
        ├── .src/{name}.py
        ├── .myst/{name}.md
        └── {name}.ipynb
```

## config.yml

```yaml
input_dir: "raw"
output_dir: "derivatives/{flow}"
input_manifest: "raw/manifest.yml"
output_manifest: "derivatives/{flow}/manifest.yml"

registry:
  group_name:
    base_input: ieeg              # pybids_inputs key
    bids:
      root: output_dir
      datatype: ieeg
    members:
      cleaned: {suffix: cleaned, extension: .fif}
```

Key fields:
- `input_manifest` / `output_manifest` — cross-flow wiring (NOT `input_registry`/`output_registry`)
- `registry:` — declarative output groups with BIDS path construction

### Cross-flow wiring

Downstream flow references upstream's manifest:
```yaml
input_dir: "derivatives/preprocess_ieeg"
input_manifest: "derivatives/preprocess_ieeg/manifest.yml"
```

## Mod Documentation Facets

Each mod has up to three docs in `{flow}/docs/{mod}/`:

| Facet | File | Purpose |
|-------|------|---------|
| **Theory** | `theory.md` | Scientific rationale, citations (`[@citekey]`) |
| **Spec** | `spec.md` | I/O contracts, parameters, component manifest |
| **Delta** | `delta.md` | Temporary: known issues, refactor plans |

## Notebook Workspaces

Notebooks are routed by `kind`:
- `investigate`, `explore` → `notebooks/explore/.src/`
- `demo`, `validate` → `notebooks/demo/.src/`

Explore notebooks are never published. Demo notebooks are published to the project site as HTML.

### notebook.yml

```yaml
kernel: cogpy
entries:
  - path: notebooks/explore/.src/investigate_noise.py
    kind: investigate
    mod: filter
    status: active
    pair_ipynb: true
```

## publish.yml

Controls what `docs_collect` publishes for this flow:

```yaml
dag: true           # publish dag.svg
report: false        # publish report.html
scripts: true        # generate script index with git links
```

## Registry Schema

```yaml
# .projio/pipeio/registry.yml
flows:
  preprocess_ieeg:
    name: preprocess_ieeg
    code_path: code/pipelines/preprocess_ieeg
    config_path: code/pipelines/preprocess_ieeg/config.yml
    mods:
      filter:
        name: filter
        rules: [filter_bandpass, filter_notch]
```

No `pipe:` field. Flow names are flat, underscore-separated.

## MCP Tool Workflow

### Discovery (read-only)

```
pipeio_flow_list(prefix="preprocess")     # find flows
pipeio_flow_status(flow="preprocess_ieeg") # flow details
pipeio_mod_list(flow="preprocess_ieeg")   # list mods + rules
pipeio_mod_context(flow=..., mod=...)     # bundled: rules, scripts, docs, config
pipeio_config_read(flow=...)              # parsed config with bids signatures
pipeio_rule_list(flow=...)                # all rules with I/O signatures
pipeio_nb_status(flow=...)                # notebook sync/publish state
```

### Authoring (write operations)

```
pipeio_mod_create(flow, mod, description, inputs, outputs)  # scaffold script + docs
pipeio_script_create(flow, mod, script_name, inputs, outputs)  # add script to existing mod
pipeio_rule_stub(flow, rule_name, inputs, outputs, script)  # generate rule text
pipeio_rule_insert(flow, rule_name, rule_text, after_rule)  # insert into Snakefile
pipeio_config_patch(flow, registry_entry, apply=True)       # add registry group
pipeio_nb_create(flow, name, kind="investigate", mod=...)   # scaffold notebook (kind-aware)
pipeio_mod_doc_refresh(flow, mod, facet="spec", apply=True) # regenerate spec.md from code
```

`nb_create` generates kind-aware templates:
- `investigate`/`explore`: config loading → registry groups → data iteration → analysis → findings
- `demo`/`validate`: load final outputs → visualization → summary

Both `mod_create` and `script_create` discover the project's compute library via codio (`role=core`) and project utils (from `code.project_utils` in `.projio/config.yml`), then add imports to generated templates.

### Code tiers

Projects organize code in three tiers. Scaffolding tools are tier-aware:

| Tier | Location | codio `role` | Scaffolding behavior |
|------|----------|-------------|---------------------|
| Core library | `code/lib/{name}/` | `core` | `nb_create`, `script_create`, `mod_create` auto-import |
| Project utils | `code/utils/` | — | `nb_create` imports PipelineContext when configured |
| Flow scripts | `scripts/` | — | Created by `mod_create`, `script_create` |

Run `projio sync` to auto-discover `code/lib/*/` and register in codio with `role=core`.
`project_context()` returns the active code tier configuration (core libraries, project_utils path, flow count).

### Validation & audit

```
pipeio_registry_scan()          # discover flows from filesystem
pipeio_registry_validate()      # check registry consistency
pipeio_contracts_validate()     # check I/O contracts across flows
pipeio_nb_audit()               # notebook lifecycle issues
pipeio_mod_audit(flow, mod)     # mod health: contract drift, doc/script existence
```

### Notebook promotion

```
pipeio_nb_promote(flow, name, mod)  # notebook → mod: analyze → script → rule stub → docs
```

Orchestrates the full extraction pipeline. Creates the script, returns rule stub
and next steps for review. Use `apply=True` to also scaffold doc stubs.

### Notebook lifecycle

```
pipeio_nb_sync(flow, name)              # py → ipynb/myst
pipeio_nb_lab(flow)                     # build Jupyter symlink manifest
pipeio_nb_publish(flow, name)           # publish to docs
pipeio_nb_pipeline(flow, name)          # sync → publish → collect → nav
```

## CLI Quick Reference

```bash
pipeio flow new <flow>             # scaffold (idempotent — augments existing)
pipeio flow list                   # list registered flows
pipeio flow status <flow>          # show flow details
pipeio flow mods <flow>            # list mods and rules
pipeio registry scan               # rediscover flows from filesystem
pipeio registry validate           # check consistency
pipeio contracts validate          # check I/O contracts
pipeio nb status                   # notebook sync state
pipeio docs collect                # publish docs to site
```

`pipeio flow new` on an existing flow fills in missing directories (rules/, explore/, demo/, publish.yml) without overwriting existing files.

## Agentic Workflows: pipeio + ecosystem tools

pipeio manages orchestration; biblio, codio, and notio provide the knowledge
that flows into mod docs, notebooks, and scripts.

### New mod workflow (idea → production)

```
1. CAPTURE         notio: note_create(kind="idea")
                   Record the analysis idea, success criteria, expected outputs

2. LITERATURE      biblio: rag_query(corpus="bib", query="...")
                   biblio: citekey_resolve(citekey) → biblio_docling(citekey, query)
                   Find methods, parameter ranges, validation approaches

3. CODE SEARCH     codio: codio_discover(query="...") → codio_get(name)
                   Check if the compute library already has the algorithm
                   rag_query(corpus="code", query="...") for implementation patterns

4. THEORY DOC      pipeio: mod_create(flow, mod, description)
                   Edit docs/{mod}/theory.md: paste findings from steps 2-3
                   Use [@citekey] citations from biblio

5. EXPLORE         pipeio: nb_create(flow, name, kind="investigate", mod=mod)
                   Prototype in notebook. Import from compute library (codio).
                   Validate against literature expectations (biblio).

6. SPEC DOC        Edit docs/{mod}/spec.md: document I/O contracts discovered
                   during exploration, or:
                   pipeio: mod_doc_refresh(flow, mod, facet="spec", apply=True)

7. PROMOTE         pipeio: nb_promote(flow, name, mod)
                   Extract notebook → script + rule stub + config patch
                   If logic is reusable: promote to compute library (codio)

8. WIRE            pipeio: rule_insert(flow, rule_name, rule_text)
                   pipeio: config_patch(flow, registry_entry, apply=True)

9. VALIDATE        pipeio: mod_audit(flow, mod) → contracts_validate()
                   Dry run: pipeio_run(flow, dryrun=True)

10. DEMO           pipeio: nb_create(flow, name, kind="demo", mod=mod)
                   Show final outputs, publish to site
```

### Maintaining existing mods

```
pipeio: mod_audit(flow, mod)              → find contract drift, missing docs/scripts
pipeio: mod_doc_refresh(flow, mod, "spec") → regenerate spec.md from current code
pipeio: mod_context(flow, mod)            → read rules, scripts, docs, config
biblio: rag_query(corpus="bib")           → update theory.md with new citations
pipeio: nb_audit()                        → find stale/orphaned notebooks
```

### Writing theory.md (biblio integration)

```
1. biblio: rag_query(corpus="bib", query="<method name>")
2. biblio: citekey_resolve(citekey) → confirm paper exists
3. biblio: biblio_docling(citekey, query="method algorithm") → extract method details
4. Edit theory.md with [@citekey] pandoc citations
5. Theory feeds into manuscript methods via manuscripto
```

### Writing scripts (codio integration)

```
1. codio: codio_discover(query="<capability>") → find existing implementations
2. codio: codio_get(name) → read library details, check role (core = can add code)
3. pipeio: script_create(flow, mod, script_name, inputs, outputs)
   → auto-imports core library (role=core) + project utils from config
4. Script calls library functions, uses snakemake.input/output for I/O wiring
5. If new reusable logic emerges: promote to core library (role=core) or project utils
```

### Cross-flow dependency management

```
pipeio: cross_flow()                    → map manifest chains
pipeio: contracts_validate()            → verify all manifests resolve
pipeio: config_read(flow)              → check input_manifest/output_manifest
```

When extracting a mod into its own flow (e.g., hpclayers from sharpwaveripple):
1. `pipeio flow new <new_flow>` — scaffold
2. Move rules + scripts from source flow
3. Create `derivatives/<new_flow>/` as datalad subdataset
4. Update downstream configs: `input_manifest: "derivatives/<new_flow>/manifest.yml"`
5. `pipeio registry scan` + `contracts_validate()`

## Conventions (strict, no fallbacks)

- **No `pipe` parameter** — flows are addressed directly by name
- **`input_manifest` / `output_manifest`** — not `input_registry` / `output_registry`
- **Mod docs are faceted** — `docs/{mod}/theory.md` + `spec.md`, not `mod-{mod}.md`
- **Notebooks use workspace dirs** — `explore/.src/` and `demo/.src/`, not flat `.src/`
- **Modkey format** — `{flow}_mod-{mod}`, not `pipe-X_flow-Y_mod-Z`
- **Published docs** — `docs/pipelines/{flow}/`, not `docs/pipelines/{pipe}/{flow}/`
- **Derivative naming** — `derivatives/{flow}/` must match the flow name 1:1
