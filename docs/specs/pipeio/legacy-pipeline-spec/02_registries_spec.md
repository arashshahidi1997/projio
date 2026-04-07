# Registries Specification (Current)

This document defines the canonical registries required to make pipelines discoverable, validateable, and refactorable.
Registries are the practical contract between documentation, code, and derivative layout.

## Registry responsibilities (overview)

Registries SHOULD provide:

- **Discovery**: enumerate inputs and outputs for a flow.
- **IO contract**: define all derivative products and their identities for that flow.
- **Validation**: enable consistency checks between a flow's config, registry, and produced derivatives.

Flow registries are the single source of truth for derivative layout and product identity for that flow.

## Registry types

### 1) Flow-local registry

Each flow owns a registry that defines its products and layout. The registry lives on disk (often under
`derivatives/<pipe>/flow-<flow>_registry.yml`) and is referenced by the flow's `config.yml`.

Minimum required fields (current practice):

- `root`: derivative root for the flow (relative to `derivatives/<pipe>`).
- `datatype`: BIDS-like datatype (e.g., `ieeg`, `ecephys`).
- `members`: mapping of named products (e.g., `lfp`, `json`, `electrodes`, `inputs`).
- Optional `base_input`, `bids` sections used by `BidsPaths` for path construction.

### 2) Flow config registry block

The flow `config.yml` carries a local `registry:` block used by `out_paths(...)` and `in_paths(...)`.
This block mirrors the flow-local registry file and is the canonical source for in-flow path building.

### 3) Inputs registry references

Input registries are referenced from `config.yml`:

- `input_dir` and `input_registry` point to upstream flow registries.
- `pybids_inputs` governs raw input selection.
- Cross-session outputs are represented by setting `session: null` in registry definitions when needed.

## Validation invariants (current checks)

An implementation MUST provide validation checks that enforce:

1) **Registry-backed path building**
   - A flow MUST be able to build all output paths using `out_paths(...)` and registry entries.
   - Hard-coded derivative output roots in Snakefiles SHOULD be rejected in review.

2) **Input registries resolve**
   - Every configured `input_registry` MUST exist and be readable.

3) **Registry and config consistency**
   - Flow `config.yml` and registry file MUST agree on root/datatype/members used by rules.
