# References

## Inspirations (handbook-wide)

The handbook owes its shape to several solo-author works and traditions. Primary inspirations:

- **[goodresearch.dev](https://goodresearch.dev)** — Patrick Mineault. The canonical solo-author research-workflow handbook; this handbook's most direct influence.
- **[xcorr.net](https://xcorr.net)** — Patrick Mineault (blog companion to goodresearch.dev).
- **[cartesian.app](https://cartesian.app)** — Elias Yilma (interactive DSA handbook; explorable-essay pattern).

Additional inspirations (organised by tradition):

- **Solo handbooks:** Jenny Bryan (*Happy Git with R*); Hadley Wickham (*R Packages*, *R for Data Science*); Karpathy ("Recipe for Training Neural Networks"); Stas Bekman (*ml-engineering*); *Google DL Tuning Playbook*; Vince Buffalo (*Bioinformatics Data Skills*); *The Turing Way*.
- **Note-to-blog essayists:** Simon Willison; Julia Evans; Lilian Weng; Jay Alammar; Chris Olah; Andy Matuschak; Eugene Yan; Chip Huyen; Maggie Appleton; Dan Luu.
- **Interactive / explorable:** Bartosz Ciechanowski; Amit Patel (Red Blob Games); Nicky Case; Bret Victor; Distill.pub; Setosa.io; Seeing Theory; Immersive Linear Algebra.
- **Neuroscience-specific:** Mike X Cohen (*Analyzing Neural Time Series Data*); Russell Poldrack (*Statistical Thinking for the 21st Century*); Neuromatch Academy.

## Source documents

- **Deep Research synthesis (2026-05-07):** *Interactive Mathematics Beyond the Static Page* — see [`reference/research/Interactive Mathematics Beyond the Static Page.pdf`](../reference/research/Interactive Mathematics Beyond the Static Page.pdf). Source of the 7-paradigm taxonomy and the gap argument in `00-frame/why-interactivity.md`.

## Per-chapter further reading

### §00 Framing

**[Why this stack](00-frame/why-this-stack.md)**

- **[goodresearch.dev](https://goodresearch.dev)** (Patrick Mineault) — the closest companion handbook: solo-author research workflows from question to figure.
- **[The Turing Way](https://the-turing-way.netlify.app/)** — community handbook for reproducible, ethical, collaborative research; especially the *Reproducible Research* guide.
- **[ml-engineering](https://github.com/stas00/ml-engineering)** (Stas Bekman) — large-scale engineering handbook for ML practitioners; model for the opinionated practitioner-guide format.

**[Why interactivity](00-frame/why-interactivity.md)**

- **[Interactive Mathematics Beyond the Static Page](../reference/research/Interactive Mathematics Beyond the Static Page.pdf)** — Deep Research synthesis; 7-paradigm taxonomy and gap argument that frames this chapter.
- **[Explorable Explanations](https://explorableexplanations.com/)** (Bret Victor) — the foundational manifesto for reactive, manipulable documents.
- **[Distill.pub](https://distill.pub/)** — archive of interactive ML essays; exemplar of the explorable-essay pattern at publication quality.
- **[Bartosz Ciechanowski](https://ciechanow.ski/)** — physics and engineering simulations as interactive essays; the gold standard for manipulable embedded figures.

**[Single-author fragility](00-frame/single-author-fragility.md)**

- **[The Turing Way](https://the-turing-way.netlify.app/)** — patterns for transitioning from solo to collaborative research practice; bus-factor and FAIR principles.
- **[goodresearch.dev](https://goodresearch.dev)** — Patrick Mineault; team and continuity considerations alongside the solo-author workflow.
- **[ml-engineering](https://github.com/stas00/ml-engineering)** (Stas Bekman) — large single-author effort that grew into a community resource; case study in sustainability.

---

### §10 BIDS

**[Strict raw root](10-bids/strict-raw-root.md)**

- **[BIDS specification](https://bids-specification.readthedocs.io/)** — canonical source for all entity names, sidecar requirements, and `dataset_description.json` fields.
- **[bids-validator](https://github.com/bids-standard/bids-validator)** — run `bids-validator raw/` to catch layout violations; JavaScript and Python variants.
- **[PyBIDS](https://pybids.readthedocs.io/)** — Python library for querying BIDS datasets; complement to snakebids for non-Snakemake code.
- **[MNE-BIDS](https://mne.tools/mne-bids/stable/index.html)** — BIDS-aware I/O for electrophysiology; handles sidecar creation from raw EEG/iEEG recordings.

**[Derivatives and manifest](10-bids/derivatives-and-manifest.md)**

- **[BIDS derivatives specification](https://bids-specification.readthedocs.io/en/stable/derivatives/introduction.html)** — formal rules for derivative dataset layout, `dataset_description.json` in `derivatives/`, and `GeneratedBy` provenance fields.
- **[PyBIDS derivatives](https://pybids.readthedocs.io/)** — `BIDSLayout(derivatives=True)` for querying processed outputs alongside raw.

**[BIDS beyond electrophysiology](10-bids/bids-beyond-electrophysiology.md)**

- **[BIDS Extension Proposals](https://bids-specification.readthedocs.io/en/stable/extensions.html)** — active proposals extending BIDS to video (BEP 024), microscopy, MEG, and other modalities.
- **[BIDS starter kit](https://bids-standard.github.io/bids-starter-kit/)** — annotated examples and templates for adopting BIDS in a new modality.

---

### §20 DataLad

**[Superdataset and subdatasets](20-datalad/superdataset-and-subdatasets.md)**

- **[DataLad handbook](https://handbook.datalad.org/)** — comprehensive reference covering `datalad install`, nested datasets, provenance recording, and the YODA principles.
- **[git-annex](https://git-annex.branchable.com/)** — underlying binary-tracking layer; useful when DataLad's abstraction is insufficient or when working with non-DataLad repositories.

**[Siblings and RIA](20-datalad/siblings-and-ria.md)**

- **[DataLad handbook §Publishing](https://handbook.datalad.org/)** — `datalad push`, sibling setup, SSH and GitHub/GitLab configurations; RIA store creation and usage.
- **[git-annex special remotes](https://git-annex.branchable.com/special_remotes/)** — the protocol layer underlying DataLad siblings, including `ria+file://` and `ria+ssh://` transports.

**[Code as subdataset](20-datalad/code-as-subdataset.md)**

- **[DataLad handbook §YODA principles](https://handbook.datalad.org/)** — the layout principle that keeps code pinned at a commit inside the superdataset; rationale and workflow.
- **[DataLad run](https://handbook.datalad.org/)** — `datalad run` records a command's provenance; the complement to pinning code versions.

---

### §30 Snakemake

**[Rules and the DAG](30-snakemake/rules-and-the-dag.md)**

- **[Snakemake documentation](https://snakemake.readthedocs.io/)** — reference for rule syntax, `input`/`output`, `run`, `shell`, and `script` directives; cluster execution profiles.
- **[Mölder et al. 2021](https://doi.org/10.12688/f1000research.29032.2)** — "Sustainable data analysis with Snakemake," F1000Research; cite this when describing the pipeline engine in a methods section.
- **[Snakemake tutorial](https://snakemake.readthedocs.io/en/stable/tutorial/tutorial.html)** — hands-on walkthrough; fastest path from zero to a running first rule.

**[Snakebids wildcards](30-snakemake/snakebids-wildcards.md)**

- **[snakebids documentation](https://snakebids.readthedocs.io/)** — `generate_inputs()`, `BidsComponent`, and the snakebids YAML config format.
- **[BIDS specification §entities](https://bids-specification.readthedocs.io/)** — entity definitions (`sub`, `ses`, `run`, `task`) that map directly to snakebids wildcard names.

**[Config-driven pipelines](30-snakemake/config-driven-pipelines.md)**

- **[Snakemake §Configuration](https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html)** — `configfile:`, the `config` dict, and profile-based configuration for reproducible parameter sweeps.
- **[snakebids documentation](https://snakebids.readthedocs.io/)** — how snakebids config extends Snakemake's own config with BIDS-aware input specifications.

**[Three idioms](30-snakemake/three-idioms.md)**

- **[snakebids documentation](https://snakebids.readthedocs.io/)** — full reference for idioms 1 and 2 (snakebids-only and snakebids + BidsPaths).
- **[Snakemake documentation](https://snakemake.readthedocs.io/)** — idiom 3 baseline; plain Snakemake without BIDS-aware parameterisation.

---

### §40 Marimo

**[Reactive cells](40-marimo/reactive-cells.md)**

- **[Marimo documentation](https://docs.marimo.io/)** — installation, the reactive execution model, UI element API (`mo.ui.*`), and the `.py` file format.
- **[Marimo GitHub](https://github.com/marimo-team/marimo)** — source and issues; the blog posts in the repository explain core design decisions.

**[Analysis notebooks](40-marimo/analysis-notebooks.md)**

- **[xarray](https://docs.xarray.dev/)** — `DataArray`, `Dataset`, `.sel()`/`.isel()` coordinate selection, and groupby operations on labelled N-D arrays.
- **[HoloViews](https://holoviews.org/)** — declarative multi-dimensional plotting; the `.hvplot` accessor that bridges xarray and interactive bokeh/panel renderers.
- **[MNE-Python](https://mne.tools/)** — EEG/iEEG processing; `read_raw_*`, epochs, and time-frequency representations.

**[Handbook explorables](40-marimo/handbook-explorables.md)**

- **[Marimo §WASM export](https://docs.marimo.io/guides/exporting.html)** — `marimo export html-wasm`; bundle size limits, supported PyPI packages, and embedding options.
- **[Pyodide](https://pyodide.org/)** — Python in WebAssembly; the runtime that powers Marimo's browser-side execution.

---

### §50 Publication

**[MkDocs for the site](50-publication/mkdocs-for-the-site.md)**

- **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** — theme reference; navigation, admonitions, search, social cards, and the full plugin list.
- **[MkDocs documentation](https://www.mkdocs.org/)** — `nav:` structure, `mkdocs.yml`, custom hooks, and deployment to GitHub Pages.

**[Quarto for deliverables](50-publication/quarto-for-deliverables.md)**

- **[Quarto documentation](https://quarto.org/docs/)** — formats (`html`, `pdf`, `revealjs`, `docx`), YAML front-matter, `_quarto.yml` project files, and the `include` shortcode.
- **[Quarto revealjs guide](https://quarto.org/docs/presentations/revealjs/)** — slide transitions, incremental lists, fragment animations, and code-block highlighting options.

**[Two surfaces, one cross-link protocol](50-publication/two-surfaces-one-cross-link-protocol.md)**

- **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** — cross-page links and the `mkdocs-ezlinks` plugin that resolves bare filenames.
- **[Quarto projects](https://quarto.org/docs/projects/quarto-projects.html)** — `_quarto.yml` and `{{< include >}}` for cross-document transclusion within a Quarto project.

---

### §60 Projio

**[Stack-aware layer](60-projio/00-stack-aware-layer.md)**

- **[Model Context Protocol specification](https://modelcontextprotocol.io/)** — the JSON-RPC wire format that projio's MCP server implements; tool and resource schemas.
- **[FastMCP](https://github.com/jlowin/fastmcp)** — Python library used to register projio's MCP tools; decorator-based tool definition.

**[Notio](60-projio/10-notio.md)**

- **[The Turing Way §Research Data Management](https://the-turing-way.netlify.app/)** — structured note-keeping, provenance recording, and metadata conventions in team research.

**[Pipeio](60-projio/20-pipeio.md)**

- **[Snakemake documentation](https://snakemake.readthedocs.io/)** — underlying execution engine; pipeio wraps its scheduling and wildcard resolution.
- **[snakebids documentation](https://snakebids.readthedocs.io/)** — BIDS-aware input generation used inside pipeio-managed flows.

**[Biblio and indexio](60-projio/30-biblio-indexio.md)**

- **[Docling](https://docling-project.github.io/docling/)** — PDF text extraction library; table, figure, and structured reference extraction.
- **[GROBID](https://github.com/kermitt2/grobid)** — ML tool for structured reference and header extraction from PDFs; powers `biblio_grobid`.
- **[OpenAlex API](https://docs.openalex.org/)** — open scholarly metadata API; powers DOI resolution and citation-graph expansion in biblio.

**[Figio and manuscript](60-projio/40-figio-and-manuscript.md)**

- **[Pandoc user manual](https://pandoc.org/MANUAL.html)** — `--citeproc`, `--bibliography`, Lua filter interface, and all output format options.
- **[Citation Style Language](https://citationstyles.org/)** — CSL spec; the APA, IEEE, Chicago, and Vancouver styles bundled by projio are drawn from this repository.

**[Codio](60-projio/50-codio.md)**

- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager; `uv tool install --editable` is used to share editable core libraries across environments without per-project installs.

---

### §70 Agentic workflows

**[Claude Code and MCP](70-agentic/claude-code-and-mcp.md)**

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — installation, `.mcp.json` configuration, CLAUDE.md memory hierarchy, and the tool-permission model.
- **[Model Context Protocol](https://modelcontextprotocol.io/)** — the JSON-RPC wire format; reference for writing a new MCP server from scratch.

**[Permissions and bounded context](70-agentic/permissions-and-bounded-context.md)**

- **[Claude Code settings reference](https://docs.anthropic.com/en/docs/claude-code/settings)** — `permissions.allow`, `allowedTools`, `additionalDirectories`, `defaultMode`, and hook configuration.

**[Skills](70-agentic/skills.md)**

- **[Claude Code §Memory and context](https://docs.anthropic.com/en/docs/claude-code/memory)** — the CLAUDE.md memory hierarchy that skills plug into; project-level vs user-level instructions.

**[Captures, tasks, and queues](70-agentic/captures-tasks-queues.md)**

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — the execution model underpinning `execute_task()` and `run_prompt()`; session and subagent lifecycle.
- **[Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models)** — haiku / sonnet / opus capability tiers; the basis for model selection in dispatch calls.

---

### §80 Orchestration

**[Worklog overview](80-orchestration/worklog-overview.md)**

- **[Claude Code §Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)** — the subagent model that worklog's queue taps into; how sessions are isolated and parallelised.
- **[Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models)** — the model-tier ladder (haiku → sonnet → opus) that worklog uses for cost-sensitive dispatch.

**[Goals and critical path](80-orchestration/goals-and-critical-path.md)**

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — the agent primitives (tasks, sessions, captures) that goals decompose into.

**[Cross-project dispatch](80-orchestration/cross-project-dispatch.md)**

- **[Anthropic model overview](https://docs.anthropic.com/en/docs/about-claude/models)** — haiku / sonnet / opus capability tiers; guidance for matching model to task complexity in dispatch calls.
- **[Claude Code §Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)** — how the `Agent(...)` tool spawns isolated subagent contexts; the mechanism `run_prompt()` drives.

---

### §90 Future directions

**[Agent hierarchies](90-future-directions/agent-hierarchies.md)**

- **[Claude Code §Sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents)** — the current `Agent(subagent_type=...)` primitive that two-tier hierarchies are built on today.
- **[Model Context Protocol](https://modelcontextprotocol.io/)** — the shared communication layer that makes tool-access portable across agent tiers.

**[Live agent communication](90-future-directions/live-agent-communication.md)**

- **[Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)** — the current session model; context for understanding what a "persistent multi-agent session" would extend.

---

### §99 Honest gaps

**[Honest gaps](99-honest-gaps.md)**

- **[BIDS specification](https://bids-specification.readthedocs.io/)** — the authoritative source for derivative validation requirements described in gap 1.
- **[The Turing Way §Reproducibility checklist](https://the-turing-way.netlify.app/)** — community-assembled checklist of common gaps in reproducible research practice.
- **[goodresearch.dev](https://goodresearch.dev)** — the companion handbook against which this cohort's gaps were calibrated.
