# Pipeline Architecture Specification (Canonical): pipe / flow / mod

This is the canonical, normative specification for the pipeline architecture.
It defines enforceable rules for how code, documentation, registries, and derivatives are structured.
The architecture is expressed using **pipe / flow / mod** terminology only:
`pipe` is the derivative namespace (`derivatives/<pipe>/`), `flow` is a runnable Snakemake workflow under a pipe,
and `mod` is a module inside a flow.
All IO is product-based: rules MUST write only registered derivative products, and paths MUST be built from registries
using shared Python utilities in the `utils` package.
Analysis levels are modes implemented as entrypoint targets, not separate flows.

---

## Concepts

![[explanation/infra/pipeline-spec/00_concepts]]

{% include-markdown "explanation/infra/pipeline-spec/00_concepts.md" %}

## Naming RFC

![[explanation/infra/pipeline-spec/01_naming_rfc]]

{% include-markdown "explanation/infra/pipeline-spec/01_naming_rfc.md" %}

## Registries Specification

![[explanation/infra/pipeline-spec/02_registries_spec]]

{% include-markdown "explanation/infra/pipeline-spec/02_registries_spec.md" %}

## Pathbuilder + IO Specification

![[explanation/infra/pipeline-spec/03_pathbuilder_spec]]

{% include-markdown "explanation/infra/pipeline-spec/03_pathbuilder_spec.md" %}

## Refactor Guide (HOW-TO)

![[how-to/refactor_to_pipeflowmod]]

{% include-markdown "how-to/refactor_to_pipeflowmod.md" %}
