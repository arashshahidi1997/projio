# Pathbuilder + IO Specification (Current)

This document defines the current IO behavior, path construction, and product identity.
It assumes flow-local registries and `BidsPaths`-style builders are the source of truth for product definitions.

## Separation of concerns (required)

Implementations MUST separate these concerns:

1) Dataset selection (what inputs are considered)
   - Expressed as `pybids_inputs` in `config.yml`.

2) Derivative layout (where outputs live)
   - Derived from the flow-local registry plus `out_paths(...)`.

3) Cross-session products
   - Represented by setting `session: null` in registry definitions.

## Product identity signature

Every output path MUST be derivable from a **product identity signature**.

The identity signature is defined by the flow-local registry entry and the entity values
used by `BidsPaths` when formatting a path. The signature includes:

- `root`, `datatype`
- `suffix` + `extension` (from member definition)
- selected entity values (e.g., subject/session/task/acq/run/recording)

Invariants:

- Two distinct registry members SHOULD NOT share an identity signature space.
- A single member MUST yield one and only one path for a given identity signature.

## Cross-session identity

When a product is cross-session, set `session: null` in the registry definition. This
causes `BidsPaths` to omit the session entity from the formatted path.

## Aggregation rules

If a flow aggregates over entities (e.g., cross-session), aggregation semantics MUST be explicit
in the rule or in reusable helpers under `utils`.

## No raw string paths in rules (required)

Rules MUST NOT construct output file paths via ad-hoc string concatenation.

- All outputs MUST be expressed as registered products via `out_paths(...)`.
- Path construction MUST be delegated to `in_paths(...)` / `out_paths(...)` which read registries.
- Rules MAY still use Snakemake `expand` / `multiext` / `ancient` / `temp` wrappers, but the base paths MUST come from product-aware builders.

## Output registration (required)

- All outputs MUST be registered products in the flow-local registry.
- A flow MUST NOT write to a path that cannot be traced back to a registry member and identity signature.

## Inputs: product references (recommended)

To enable reproducibility and refactoring:

- Inputs SHOULD be referenced as products (registered) whenever the input is a derivative product.
- Raw dataset inputs are referenced through `pybids_inputs` selection.
