# Canonical Concepts: pipe / flow / mod

This document defines the canonical pipeline architecture vocabulary and invariants.
It is normative and MUST be treated as the single source of truth for terminology.

## Definitions

### pipe

A **pipe** is a derivative namespace.

- A pipe MUST map 1:1 to a derivative root directory: `derivatives/<pipe>/`.
- A pipe MUST be the top-level unit of ownership for derivative products written under `derivatives/<pipe>/`.
- A pipe SHOULD be named for the scientific or technical function of the derivative namespace (e.g., `preprocess`, `spectrogram`).

### flow

A **flow** is a runnable Snakemake workflow that lives under exactly one pipe.

- A flow MUST be runnable (i.e., have an entrypoint Snakefile).
- A flow MUST live at: `code/pipelines/<pipe>/<flow>/<pipe>_<flow>.smk`.
- A flow MUST write only to registered derivative products under its owning pipe (see registry and IO specifications).
- A flow MAY depend on products produced by other flows (including flows in other pipes) only via registered products.

### mod

A **mod** is a module inside a flow.

- A mod MUST be a cohesive unit of computation that produces one or more registered products.
- A mod SHOULD correspond to a small set of rules (or a rule group) and a single conceptual transformation.
- A mod SHOULD keep non-trivial Python logic in `utils` (importable package), not embedded in the Snakefile.

## Pipeline invariants

### Pipeline == derivative namespace invariant

In this architecture, a pipeline is defined by its **derivative namespace** rather than by a single workflow file.

- The term "pipeline" MUST be interpreted as "the pipe's derivative namespace" (i.e., `derivatives/<pipe>/...`).
- A pipe MAY contain multiple flows.
- Multiple flows MAY write into the same pipe ONLY if product identity does not collide (see product identity).

### Analysis levels are modes, not separate flows

An **analysis level** is a mode of execution for a flow, expressed through entrypoint targets.

- Analysis levels MUST be implemented as entrypoint targets (e.g., `all`, `participant`, `session`, `group`), not as separate flows.
- Analysis level selection MUST affect **output identity only** (e.g., entity dropping / aggregation behavior), not the definition of the underlying products.
- A flow MAY expose additional analysis levels beyond common conventions, but each MUST be explicitly registered.

## Product-based IO model

All IO is defined in terms of **products** (named derivative artifacts), not ad-hoc file paths.

- Every output a rule writes MUST correspond to a registered product.
- Rules MUST NOT write outputs outside registered products.
- Raw string paths in rules SHOULD be avoided; outputs SHOULD be constructed via `utils` pathbuilders that reference registries.
- A product MUST have a stable identity signature (see Pathbuilder + IO specification).

## Ownership of derivative products

Products are owned at the pipe level and produced at the flow/mod level.

- Every product MUST declare an owning pipe.
- Every product MUST declare at least one owner flow (the flow(s) permitted to write that product).
- A product MAY be writable by multiple flows ONLY if:
  - those flows are in the same pipe, and
  - the product identity signature guarantees non-collision across those flows' outputs (e.g., distinct entity sets or mutually exclusive subsets).

