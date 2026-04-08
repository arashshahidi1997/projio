# pipeio: Pipeline Documentation Conventions

## Problem

Pipeline documentation exists at three levels of abstraction, but only one (mod-level) has defined conventions and tooling:

| Level | What it describes | Convention? | Scaffolded? | Collected? |
|-------|-------------------|-------------|-------------|------------|
| **Mod** | One processing step: rationale, spec, known issues | theory/spec/delta facets | `mod_create` | `docs_collect` → `mods/` |
| **Flow** | How mods chain within a workflow: ordering rationale, DAG, design decisions | **Ad-hoc** | Only stub `index.md` | Copied as-is |
| **Pipeline** | How flows compose across a project: layer architecture, data flow, status | **Manual** | Nothing | Nothing |

Agents and humans writing flow-level or pipeline-level docs have no template, no scaffold, and no guidance on what sections to include. The result is inconsistency: some flows have 170-line overviews with full DAG diagrams and design rationale, others have 3-line stubs.

## Design

### Principle: convention over generation

These docs are primarily **human-authored narratives** — scientific rationale, design decisions, known gaps. Pipeio should define what sections belong at each level and scaffold templates, but not attempt to auto-generate the narrative content. Auto-generation is limited to structural metadata that pipeio already knows (mod listings, manifest chains, config summaries).

### Flow Overview: `docs/overview.md`

Each flow gets an `overview.md` in its `docs/` directory. This is the entry point for understanding the flow as a whole — how mods compose into a processing chain and why.

#### Sections

| Section | Content | Auto-populatable? |
|---------|---------|-------------------|
| **Purpose** | What this flow produces and why it exists as a unit | No — requires scientific context |
| **Input / Output** | Input sources, output derivative, manifest paths | Partially — from `config.yml` |
| **Mod Chain** | Processing order, dependencies between mods, DAG | Partially — mod list from registry, DAG from snakemake |
| **Design Decisions** | Why this ordering, why these flow boundaries, alternatives considered | No — human narrative |
| **Known Gaps** | Flow-level issues, missing mods, planned additions | No — human narrative (delta-like) |

#### Template

```markdown
# {flow} — Flow Overview

## Purpose

<!-- What does this flow produce? Why is it a single flow rather than
     split into multiple? What downstream flows consume its output? -->

## Input

- Input directory: `{input_dir}`
- Input manifest: `{input_manifest}` (from flow: `{source_flow}`)
- Wildcards: {wildcards}

## Output

- Output directory: `{output_dir}`
- Output manifest: `{output_manifest}`

## Mod Chain

<!-- How do the mods compose? What is the processing order and why?
     Include an ASCII or mermaid DAG if helpful. -->

| Order | Mod | Purpose |
|-------|-----|---------|
| 1 | {mod} | {one-line description} |
| ... | ... | ... |

## Design Decisions

<!-- Key choices: why this mod ordering, why certain steps read from
     raw vs intermediate, why certain operations are combined or split. -->

## Known Gaps

<!-- Flow-level issues. Unlike mod-level delta.md, these are about
     missing mods, architectural problems, or cross-mod concerns.
     Remove entries as they are resolved. -->
```

#### Lifecycle

```
flow_new scaffold (stub) → agent/human fills Purpose + Mod Chain
  → mods evolve → update Mod Chain + Design Decisions
    → issues found → add Known Gaps
      → gaps resolved → remove from Known Gaps
```

The overview is a **living document** that evolves with the flow. It is not a one-time scaffold.

#### Relationship to mod docs

Flow overview describes **how** mods compose. Mod theory describes **why** a specific processing step works. Mod spec describes **what** it does technically. There should be no duplication — the overview references mods by name and defers detail to their facet docs.

```
flow overview.md    "We apply badlabel before interpolation because..."
  └→ badlabel/theory.md   "DBSCAN outlier detection on quantile-aggregated features..."
  └→ badlabel/spec.md     "Input: feature.zarr (nch × nwin × 5). Output: mask.npy (nch,)"
```

### Pipeline Architecture: `code/pipelines/architecture.md`

One document per project describing how flows compose into a multi-stage analysis. This is the highest level of pipeline documentation.

#### Sections

| Section | Content | Auto-populatable? |
|---------|---------|-------------------|
| **Architecture Diagram** | Mermaid/ASCII graph of flow dependencies | Partially — from `cross_flow` manifest chains |
| **Flow Table** | Status, layer/stage, description per flow | Partially — flow names + status from registry |
| **Data Flow** | How derivatives chain: which flow consumes which | Yes — from `cross_flow` |
| **Design Principles** | Why these flow boundaries, what defines a flow | No — human narrative |
| **References** | Links to architecture decision notes | No — human curation |

#### Template

```markdown
# Pipeline Architecture

<!-- High-level description of the project's analysis pipeline.
     How do flows compose from raw data to final results? -->

## Architecture Diagram

```mermaid
graph TD
    %% Auto-generated scaffold from cross_flow manifest chains.
    %% Edit to add layers, groupings, and planned flows.
{mermaid_body}
```

## Flows

| Flow | Stage | Status | Description |
|------|-------|--------|-------------|
{flow_table}

## Data Flow

| Consumer | Input Manifest | Producer |
|----------|----------------|----------|
{chain_table}

## Design Principles

<!-- What defines a flow boundary in this project?
     What invariants does the architecture maintain? -->

## References

<!-- Links to idea notes, meeting notes, or decision records
     that shaped the architecture. -->
```

#### Location

`code/pipelines/architecture.md` is the source of truth. `docs_collect` copies it to `docs/pipelines/architecture.md` for inclusion in the site.

The choice of `code/pipelines/` (not `docs/`) follows the same principle as flow docs: **source lives next to code**, site copies are build artifacts.

#### Lifecycle

```
first flow registered → scaffold architecture.md with flow table + manifest chains
  → human adds layers, grouping, design principles
    → new flows added → update diagram + table (agent or human)
      → architecture decisions → add References
```

### `docs_collect` Changes

1. **Flow overview collection** — already handled: `overview.md` → `index.md` renaming exists.

2. **Pipeline architecture collection** — new: if `code/pipelines/architecture.md` exists, copy it to `docs/pipelines/architecture.md` (with source-path header). Include in nav before per-flow entries.

### Commands: Who Scaffolds What

#### Flow overview: `pipeio_flow_new` (existing, extended)

**CLI:** `pipeio flow new <flow>`
**MCP:** `pipeio_flow_new(flow)`

Currently scaffolds `docs/index.md` only. Extended to also scaffold `docs/overview.md`.

**Idempotent behavior** (unchanged): only writes files that don't exist. Running `flow_new` on an existing flow with a hand-written `overview.md` is safe — it won't overwrite.

Change to `mcp_flow_new` in `pipeio/mcp.py`:
```python
# docs/overview.md (new — flow overview template)
overview = flow_dir / "docs" / "overview.md"
if not overview.exists():
    overview.write_text(FLOW_OVERVIEW_TEMPLATE.format(
        flow=flow,
        input_dir=raw.get("input_dir", ""),
        output_dir=raw.get("output_dir", f"derivatives/{flow}"),
        input_manifest=raw.get("input_manifest", ""),
        output_manifest=raw.get("output_manifest", f"derivatives/{flow}/manifest.yml"),
    ), encoding="utf-8")
    created.append("docs/overview.md")
```

The existing `docs/index.md` stays as a lightweight landing page (title + mod listing). The overview carries the narrative.

**For existing flows that lack an overview:** run `pipeio flow new <flow>` again. Since it's idempotent, it only creates the missing `overview.md` — everything else is skipped.

#### Pipeline architecture: `pipeio_architecture_init` (new tool)

**CLI:** `pipeio docs architecture-init [--force]`
**MCP:** `pipeio_architecture_init(force=False)`

Scaffolds `code/pipelines/architecture.md` from live registry + manifest chain data.

**Behavior:**
1. If `code/pipelines/architecture.md` exists and `force=False` → return `{"status": "exists", "path": "..."}`. No overwrite.
2. If missing or `force=True`:
   - Call `cross_flow` to get manifest chains
   - Read registry for flow names
   - Generate mermaid diagram: one node per flow, edges from `input_manifest` → `output_manifest` chains
   - Generate flow table: name + code_path (status/layer/description left as placeholders for human)
   - Generate data flow table from chains
   - Write to `code/pipelines/architecture.md`
3. Return `{"status": "created", "path": "...", "flows": N, "chains": M}`

**Why a separate tool, not part of `flow_new`:**
- `flow_new` operates on a single flow. Architecture is cross-flow.
- `flow_new` is called frequently (every new flow). Architecture init is called once per project, or occasionally to re-scaffold after major changes.
- Different `--force` semantics: `flow_new` is always-safe idempotent. Architecture re-scaffold should require explicit opt-in.

**Implementation location:** `pipeio/docs.py` (new function `architecture_init`), exposed via `pipeio/mcp.py` and `pipeio/cli.py` (`pipeio docs architecture-init`).

#### Collection: `pipeio_docs_collect` (existing, extended)

**CLI:** `pipeio docs collect`
**MCP:** `pipeio_docs_collect()`

Extended to handle `code/pipelines/architecture.md`:
```python
# --- 0. Collect pipeline-level architecture doc ---
arch_src = pipelines_dir / "architecture.md"
if arch_src.is_file():
    _copy_with_header(arch_src, docs_base / "architecture.md", root)
    collected.append(str(docs_base / "architecture.md"))
```

No change to how flow-level docs are collected — `overview.md` → `index.md` renaming already works.

#### Nav: `pipeio_docs_nav` (existing, extended)

Extended to insert `architecture.md` before per-flow entries:

```python
if (docs_base / "architecture.md").exists():
    flow_navs.insert(0, {"Architecture": "architecture.md"})
```

Result:
```yaml
- Pipelines:
  - Architecture: architecture.md
  - preprocess_ieeg:
    - Overview: preprocess_ieeg/index.md
    - Modules: ...
```

### Respect for Existing Content — Summary

| Command | Target file | If exists | If missing |
|---------|------------|-----------|------------|
| `pipeio_flow_new` | `docs/overview.md` | Skip (idempotent) | Create from template |
| `pipeio_flow_new` | `docs/index.md` | Skip (idempotent) | Create stub |
| `pipeio_architecture_init` | `code/pipelines/architecture.md` | Skip (unless `--force`) | Create from registry + cross_flow |
| `pipeio_docs_collect` | `docs/pipelines/architecture.md` | Overwrite (build artifact) | Create from source |
| `pipeio_docs_collect` | `docs/pipelines/{flow}/index.md` | Overwrite if stale (build artifact) | Create stub |

**Invariant:** source files in `code/pipelines/` are never overwritten without `--force`. Build artifacts in `docs/pipelines/` are always overwritten (they're gitignored).

## Implementation Plan

| Step | Component | Change |
|------|-----------|--------|
| 1 | `ontology.md` | Add Flow Overview and Pipeline Architecture sections documenting the conventions |
| 2 | `mcp_flow_new` | Generate `docs/overview.md` template alongside `docs/index.md` (idempotent) |
| 3 | `docs.py` + `mcp.py` + `cli.py` | New `architecture_init` function + `pipeio_architecture_init` MCP tool + `pipeio docs architecture-init` CLI |
| 4 | `docs_collect` | Collect `code/pipelines/architecture.md` → `docs/pipelines/architecture.md` |
| 5 | `docs_nav` | Insert architecture.md at top of pipelines nav |
| 6 | `mod_doc_refresh` | Optionally update the mod chain table in `overview.md` when mods are added/removed |

Steps 1–2 are pure convention + scaffold extension. Steps 3–5 add the architecture tool and collection. Step 6 is optional convenience. The convention is valuable even without the tooling — an agent can scaffold the template manually using `cross_flow` and `flow_status` output.

## Non-Goals

- **Auto-generating narrative content.** The purpose, design decisions, and known gaps sections require human or agent judgment. Pipeio provides the template and structural metadata, not the scientific rationale.
- **Enforcing completeness.** Empty sections are fine. The template signals what *should* be documented, not what *must* be.
- **Versioning architecture docs.** The architecture doc is a living document, not a snapshot. Git history provides versioning. No need for dated copies or changelogs.
- **Replacing project-level planning docs.** `code/pipelines/architecture.md` describes the technical data flow. Higher-level planning (milestones, timelines, priorities) stays in `docs/plan/` or questio.
