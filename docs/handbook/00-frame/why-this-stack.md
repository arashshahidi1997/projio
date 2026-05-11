# Why this stack

!!! note "Sources & anchors"
    - **Stack component:** Meta
    - **Canonical artifact:** stack-axis survey §Universal patterns
    - **Workshop session:** Day-1 AM kickoff
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

The stack as a coherent open-science substrate; what each component
contributes; what's missing and why projio fills it.

## The argument

Research practice has crossed a maturity threshold. Raw data is versioned,
analyses run as declarative DAGs, figures are produced by code, and
manuscripts compile from the same tree that holds the experiments. What
remains stubbornly static is the *workflow itself* — the chain that runs
from a question, through datasets and pipelines and notebooks and figures,
to a published claim. Today that chain mostly lives in a researcher's head,
spread across whiteboards, terminals, and tab-bars. The thesis of this
handbook is that the workflow wants to be a first-class, inspectable,
manipulable object in the same way a research figure does.

The analogy is not casual. The Deep Research synthesis on interactive
mathematics ([Interactive Mathematics Beyond the Static
Page](../../reference/research/Interactive Mathematics Beyond the Static Page.pdf))
observes that the best modern mathematical resources are those that
"reorganize access to rigor by making hidden structure perceptible,
manipulable, and reproducible." Static prose is excellent at logical
structure and weak at deformation, sensitivity, and parameter dependence.
The same is true of research workflows. A `README` can explain what a
pipeline does; only a *running representation* can show what changes when
you swap a wildcard, switch a model, or rerun on a new subject. Static
prose is to research practice what static images are to complex analysis.

## The seven components

This handbook treats the stack as seven interlocking layers, each
responsible for one well-bounded slice of the workflow.

- **BIDS** is the data convention. Directory layout *is* the API: a
  `participants.tsv`, a `dataset_description.json`, and per-subject
  folders give every downstream tool a stable contract. Without BIDS,
  every pipeline has to be told where the data lives; with BIDS, the
  contract is implicit and machine-readable.

- **DataLad** is the version layer. It composes git with git-annex so a
  superdataset and its subdatasets — raw, derivatives, code libraries —
  travel together with pinned commits and content-addressable storage.
  Code is a subdataset; derivatives are subdatasets; the whole repository
  graph is auditable.

- **Snakemake** is the execution layer. Rules declare inputs and outputs;
  the DAG falls out of dependency tracking; parallelism, retries, and
  resource accounting are properties of the engine, not the script.
  Snakebids extends this with BIDS-aware wildcard generation so
  subject/session/run loops are declarative.

- **Marimo** is the notebook layer. Files are `.py`, reactivity is
  built-in, hidden state is gone, and the same notebook can run as an
  exploratory tool, an automated batch job, or a WASM-exported
  explorable. It is the first notebook format that is diff-friendly,
  scriptable, and embeddable in a static site without a kernel.

- **Quarto and MkDocs** are the publication layer. MkDocs (with
  `mkdocs-material`) hosts this handbook and the project's living docs.
  Quarto is the cross-format authoring engine used for deliverables —
  reports, workshop handouts, slides — that need book-style typography or
  multi-output rendering. Two surfaces, one cross-link protocol.

- **projio** is the stack-aware layer. It does not replace any of the
  above; it makes the whole composition queryable. `project_context()`
  tells an agent what the project is, `runtime_conventions()` tells it
  how to run things, `pipeio_target_paths(...)` resolves BIDS wildcards
  to disk paths, and `rag_query(...)` searches the project's own notes,
  papers, and code. Six subsystems — indexio, biblio, notio, codio,
  pipeio, figio — partition the knowledge surface.

- **Agentic workflows on top** — Claude Code with the projio and worklog
  MCP servers — turn the stack into something an LLM can drive. The
  agent does not improvise; it queries the same `project_context()` a
  human would, runs the same `pipeio_run(...)` a human would, and writes
  its observations into the same `docs/log/` a human would.

## What is uncovered

Each of the seven layers solves a real, well-scoped problem. None of them
covers the *seam between layers* — the question "given this BIDS dataset,
these registered pipelines, this notebook, and these notes, what is the
state of the workflow and what should happen next?" In the language of the
Deep Research synthesis, this is the project's *operator theory*: the
domain where individual computations are well-instrumented but the
ambient structure is not. projio fills that gap by representing the
workflow itself as a manipulable object: a registry of flows, a graph of
captures and tasks, a corpus of project knowledge, and an agent layer
that can act on all three through one API.

## Reading the rest of the handbook

The chapters that follow walk the stack from data ([BIDS](../10-bids/strict-raw-root.md))
to publication ([MkDocs / Quarto](../50-publication/mkdocs-for-the-site.md)),
introduce [projio](../60-projio/00-stack-aware-layer.md) as the
stack-aware layer, and end with the [agentic](../70-agentic/claude-code-and-mcp.md)
and [orchestration](../80-orchestration/worklog-overview.md) layers that
sit on top. The vocabulary established here — *workflow as manipulable
object*, *stack-aware layer*, *seam between layers* — recurs throughout.
The full chapter list and per-chapter contract is in
[`_outline.md`](../_outline.md) §A.

## Further reading

- **[goodresearch.dev](https://goodresearch.dev)** (Patrick Mineault) — the closest companion handbook: solo-author research workflows from question to figure.
- **[The Turing Way](https://the-turing-way.netlify.app/)** — community handbook for reproducible, ethical, collaborative research; especially the *Reproducible Research* guide.
- **[ml-engineering](https://github.com/stas00/ml-engineering)** (Stas Bekman) — large-scale engineering handbook for ML practitioners; model for the opinionated practitioner-guide format.
