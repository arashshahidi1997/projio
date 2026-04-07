# Naming RFC (Current): pipe / flow / mod

This document defines current naming rules for identifiers, directories, and documentation.
Rules here reflect actual usage and are intended to be stable guidance.

## Slug rules

A **slug** is the canonical identifier component used in names.

- Slugs MUST be lowercase ASCII.
- Slugs MAY contain digits (`0-9`).
- Slugs MAY contain hyphens (`-`).
- Slugs MUST NOT contain underscores (`_`), spaces, or periods.
- Slugs MUST NOT start or end with a hyphen.
- Slugs SHOULD be short but unambiguous.

## Canonical IDs

Canonical IDs MUST be used in registries, logs, and documentation references.

### Pipe + flow

Canonical ID for a flow:

- `pipe-<pipe>_flow-<flow>`

### Pipe + flow + mod

Canonical ID for a mod:

- `pipe-<pipe>_flow-<flow>_mod-<mod>`

Where `<pipe>`, `<flow>`, and `<mod>` are slugs.

## Canonical path mappings

The following mappings SHOULD hold.

### Code paths

- A pipe root SHOULD be: `code/pipelines/<pipe>/`.
- A flow root SHOULD be: `code/pipelines/<pipe>/<flow>/`.
- A flow entrypoint Snakefile SHOULD be named `Snakefile` in the flow root.
- A mod is a module in the flow that can be a set of scripts and importable code that live under the flow root, for example:
  - `code/pipelines/<pipe>/<flow>/...` (recommended)

```
<flow>/
  Snakefile
  scripts/
  report/
  config.yml
```
There is no enforced boundary between module scripts belonging to the same flow.
Code that is shared across mods or flows SHOULD live in `utils` and be imported. 

### Documentation paths

Documentation MUST use `pipe-`, `flow-`, and `mod-` naming.

- Pipe documentation SHOULD live at: `docs/explanation/pipelines/pipe-<pipe>/`.
- Flow documentation SHOULD live at: `docs/explanation/pipelines/pipe-<pipe>/flow-<flow>/`.
- Mod documentation SHOULD live under the flow documentation directory.

This canonical specification suite lives at:

- `docs/explanation/infra/pipeline-spec/`

### Derivative paths

- All derivatives for a pipe SHOULD live under: `derivatives/<pipe>/`.
- Flow derivatives SHOULD live under: `derivatives/<pipe>/flow-<flow>/...`.
- Flows and mods SHOULD NOT write outside `derivatives/<pipe>/` for their owning pipe.

## Mandatory migration: legacy flow prefix -> `flow-`

The term `flow` is canonical. Any legacy naming that uses a non-canonical flow prefix MUST be migrated to `flow-`.

- Canonical documentation MUST use `flow-<flow>` for flow identifiers.
- All future docs, registries, and directory names MUST use `flow-<flow>` for flow identifiers.
- During migration, any directory, registry key, or identifier that represents a flow using a legacy prefix SHOULD be renamed to the equivalent `flow-<flow>` form.

## Derived naming: files and identifiers

### Human-readable names

- Human-readable headings MAY omit prefixes (pipe/flow/mod) for readability, but canonical IDs MUST appear at least once per document section that defines a pipe/flow/mod.

### Snakefile structure

- A Snakefile SHOULD be orchestration-only (rule graph, inputs/outputs, resources, wildcards).
- Non-trivial Python logic SHOULD live in `utils` and be imported.
- A Snakefile BETTER NOT contain hard-coded derivative output roots; it's BETTER to build outputs from registered products.

### Mod concept (flow-internal)

A **mod** is a conceptual step within a flow. It is represented by:

- A set of rules in the flow Snakefile, typically named `mod_<name>` or `<mod>_<rule>` for discoverability.
- A dedicated theory/spec/delta doc set (reasoning, expected artifacts, dependencies, and current implementation gaps).
- Artifacts produced by those rules SHOULD include the mod label where practical (without enforcing a path structure).
