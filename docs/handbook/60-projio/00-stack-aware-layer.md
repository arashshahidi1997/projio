# projio: the stack-aware layer

!!! note "Sources & anchors"
    - **Stack component:** projio
    - **Canonical artifact:** `pixecog/.projio/config.yml` + `pixecog/.projio/pipeio/registry.yml`
    - **Workshop session:** Day-2 PM session 2 (projio enters)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

*The stack already does the work; projio makes it queryable.* This chapter
introduces `project_context()`, `runtime_conventions()`, the six-subsystem
map, and `projio sync` — the periodic reconciliation step.

## The pivot

The first five chapters of this handbook covered five separate tools.
[BIDS](../10-bids/strict-raw-root.md) lays out raw data;
[DataLad](../20-datalad/superdataset-and-subdatasets.md) versions it;
[Snakemake](../30-snakemake/rules-and-the-dag.md) runs the pipelines;
[Marimo](../40-marimo/reactive-cells.md) hosts the notebooks;
[MkDocs and Quarto](../50-publication/mkdocs-for-the-site.md) publish the
output. Each is excellent at its layer. None of them know about each other.
A pipeline does not know whether its outputs are checked into git-annex.
A notebook does not know which flow produced its inputs. A manuscript
does not know whether the figure it cites is up to date with the pipeline
that built it.

projio is the layer that knows. It does not replace any of the prior
tools — Snakemake still runs the DAG, DataLad still versions the tree,
MkDocs still builds the site — but it builds a queryable representation
of the *whole composition* on top of them. The unit of that
representation is the **MCP tool call**: `project_context()` to ask
"what is this project?", `runtime_conventions()` to ask "how do I run
things here?", `pipeio_flow_list()` to ask "what pipelines are
registered?", `rag_query(...)` to ask "what does the lab corpus say
about X?". Each tool returns structured JSON — not files for an LLM to
re-parse, not configuration for a human to memorise — that an agent or
a new collaborator can consume directly.

## The two orientation calls

Two MCP tools sit at the front of every session and frame the rest.

**`project_context()`** returns the structured identity of the
repository: its `project_name`, `project_kind` (`generic`, `tool`, or
`study`), the active subsystems and their on-disk paths, the configured
runtime environment, and the code-tier layout. It is what a freshly
spawned agent reads first; the structured payload is what a human would
otherwise reconstruct by tabbing through `README.md`, `.projio/config.yml`,
`pyproject.toml`, and a few `ls` calls. The point of the tool is not
that the information is hidden — it is in plain text — but that the
shape of the answer is uniform across every projio-aware project.

**`runtime_conventions()`** returns the Makefile targets and command
recipes a project actually uses: `make dev`, `make docs`, `make save`,
the Snakemake runner (`conda` vs `pixi`), the env names. This replaces
the per-project README archaeology that every agent or new contributor
otherwise has to perform. When a project is consistent with the
ecosystem convention, the answer is short; when it diverges, the
divergence is visible.

The two calls together establish a contract: every projio-aware
project speaks the same identity protocol, regardless of which subset
of the stack it uses.

## The six subsystems

projio is a *meta*-tool because it composes six narrower tools, each
owning a knowledge domain. They are git submodules under `packages/`
and are optional dependencies — the system degrades gracefully when
one is absent.

| Subsystem | Domain | What it makes queryable |
|---|---|---|
| **indexio** | retrieval | Corpus indexing, chunking, embedding, semantic search (`rag_query`) |
| **biblio** | literature | Citekey resolution, paper context extraction (docling/grobid), Zotero round-trip |
| **notio** | notes + manuscripts | Structured `docs/log/{idea,task,result,…}/` entries; manuscript assembly |
| **codio** | code intelligence | Library catalog with `role: core/shared/external`; cross-project code discovery |
| **pipeio** | pipelines | Flow registry, mods, rules, notebooks, `manifest.yml` contracts |
| **figio** | figures | Declarative FigureSpec YAML → composed multi-panel SVG/PDF |

The next five sub-chapters introduce each subsystem in the order the
graded workshop sequence uses (see survey §"Graded introduction
sequence"): notio first (project memory), then pipeio (pipelines as
data), then biblio + indexio (literature and retrieval), then figio
and manuscript (figures and assembled deliverables), then codio
(code reuse). Each is motivated by a pain the *previous* stage
exposes.

## `projio sync` — the meta-command

projio's state is not implicit; it is materialised on disk under
`.projio/`. `projio sync` is the periodic reconciliation step that
keeps the materialisation in step with the rest of the repository. It
auto-discovers `code/lib/<name>/` subdatasets and registers them in
codio with `role=core`; detects `code/utils/` and writes
`code.project_utils` in `.projio/config.yml`; copies the bundled Lua
filter and CSL files into `.projio/filters/` and `.projio/render/csl/`;
generates `.projio/projio.mk` (the Makefile fragment that exposes
`projio` and `datalad` runners); rebuilds stale index sources; and
regenerates the skill index. Each operation is idempotent; running
`projio sync` again on an unchanged tree is a no-op.

The convention is *write your project layout normally, let `projio sync`
do the bookkeeping*. The reciprocal — letting projio scaffold whole new
directories you did not ask for — is deliberately avoided.

## What projio is not

projio is **not** an alternative to Snakemake, DataLad, MkDocs, or any
of the prior layers. It does not replace `snakemake -p`; `pipeio_run`
shells out to snakemake with the correct environment and flags. It
does not replace `datalad save`; `datalad_save` is a thin MCP wrapper
that returns structured output instead of raw stderr. It does not
replace `mkdocs build`; `site_build` invokes mkdocs through the
configured runner. The value-add is in the *meta-knowledge*: projio
knows which env to use for which command, which flows exist under
`code/pipelines/`, which CSL file the manuscripts cite. The underlying
tools are still the source of truth.

projio is **not** a workflow engine. It does not schedule jobs or
enforce DAG dependencies; that is Snakemake's job. It does not store
binary artefacts; that is git-annex. It does not parse PDF body text
itself; that is docling/grobid (wrapped through biblio).

projio is **not** uniformly adopted. The stack-axis survey records that
each of the four study projects in the cohort enables a different
subset of subsystems, and one project (msol) has `biblio.enabled:
false` while still carrying a populated `bib/` directory. The
`enabled:` flag is a switch, not a deletion, and drift between flag
and state is possible. This is the first of several
[honest gaps](../99-honest-gaps.md) the handbook is upfront about.

## What follows

The six sub-chapters that follow walk the subsystem map in the same
order the workshop introduces them, each motivated by a pain felt
upstream in the stack: [notio](10-notio.md) for project memory,
[pipeio](20-pipeio.md) for pipelines-as-data,
[biblio + indexio](30-biblio-indexio.md) for literature and retrieval,
[figio and manuscript](40-figio-and-manuscript.md) for figures and
deliverables, and [codio](50-codio.md) for code reuse.

## Further reading

- **[Model Context Protocol specification](https://modelcontextprotocol.io/)** — the JSON-RPC wire format that projio's MCP server implements; tool and resource schemas.
- **[FastMCP](https://github.com/jlowin/fastmcp)** — Python library used to register projio's MCP tools; decorator-based tool definition API.
