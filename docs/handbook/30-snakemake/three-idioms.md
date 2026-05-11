# Three idioms

!!! note "Sources & anchors"
    - **Stack component:** Snakemake
    - **Canonical artifact:** survey component 3 §Honest gap (three idioms table)
    - **Workshop session:** Day-1 PM closing
    - **Outline:** [`_outline.md`](../_outline.md) §B

## The three styles in the cohort

The project cohort runs Snakemake in three distinct styles — not three
schools of thought, but three historical layers of a maturing convention.

| Idiom | Projects | Core mechanism |
|---|---|---|
| **snakebids alone** | cogpy | `generate_inputs()` + custom path helpers; no pipeio adapter; no cross-flow manifest |
| **snakebids + BidsPaths** | pixecog, gecog | `generate_inputs()` + `BidsPaths` from `pipeio.adapters.bids`; `manifest.yml` as cross-flow contract |
| **plain snakemake** | msol | `glob_wildcards()` on flat paths; no BIDS-aware wildcard generation; no BidsPaths |

## Idiom 1: snakebids alone

`cogpy/src/cogpy/workflows/preprocess/Snakefile` imports `generate_inputs`
and `bids` from snakebids but resolves wildcards through a custom
`path_placeholderstring()` helper rather than a declarative `pybids_inputs`
config. There is no BidsPaths adapter and no manifest output, so the
workflow cannot participate in a cross-flow contract without the downstream
flow knowing the upstream path scheme explicitly.

This style predates the pipeio convention. It is the **predecessor**.
New flows should not use it.

## Idiom 2: snakebids + BidsPaths (workshop default)

pixecog and gecog call `generate_inputs()` with a declarative `pybids_inputs`
section in `config.yml`, then bind the result to `BidsPaths`:

```python
inputs = generate_inputs(bids_dir, config["pybids_inputs"])
out_paths = BidsPaths(_registry, config["output_dir"], inputs)
```

`BidsPaths` resolves output paths per member and per wildcard combination,
and writes a `manifest.yml` on success. Downstream flows read that
manifest through their own `BidsPaths` without hard-coding upstream paths.
pipeio's `pipeio_target_paths(flow, group, member)` MCP tool resolves
paths from the same registry, so agents and humans use the same API.

This is the style all four active study projects have converged on. It is
the **workshop default** and the starting point for any new flow registered
via `pipeio_flow_new`.

## Idiom 3: plain snakemake

msol's three pipelines use `glob_wildcards()` on flat directory layouts
with no snakebids layer:

```python
subjects, = glob_wildcards("data/sub-{subject}/recording.csv")
```

The Snakefile is shorter and easier to read for a first-time Snakemake
user. It is honest about what msol's behaviour+DLC dataset requires: three
short pipelines where full BIDS-aware wildcard generation would be
ceremonial.

This is the **minimal-ceremony variant** — appropriate for small,
self-contained workflows that do not need cross-flow contracts or pipeio
registry integration. The workshop introduces it as a contrast that
motivates why BidsPaths exists.

## Which to use

- **BIDS dataset + output consumed by a downstream flow**: use
  snakebids + BidsPaths. This is the default for any new flow created
  with `pipeio_flow_new`.
- **Non-BIDS dataset or one-shot exploratory pipeline**: plain snakemake
  with `glob_wildcards()` is a clean starting point; add BidsPaths later
  if needed.
- **Inheriting a snakebids-alone codebase**: maintain the existing idiom
  and plan a migration — do not introduce BidsPaths mid-run.

## Honest gap

cogpy is currently mid-migration off the snakebids-alone style. The
preprocess Snakefile has not been updated to the snakebids + BidsPaths
pattern because cogpy is a library repo, not a study project; the migration
is planned but not blocking. See [`99-honest-gaps.md`](../99-honest-gaps.md)
for the broader context of why three idioms coexist and what would resolve
the divergence.

## Further reading

- **[snakebids documentation](https://snakebids.readthedocs.io/)** — full reference for idioms 1 and 2 (snakebids-only and snakebids + BidsPaths).
- **[Snakemake documentation](https://snakemake.readthedocs.io/)** — idiom 3 baseline; plain Snakemake without BIDS-aware parameterisation.
