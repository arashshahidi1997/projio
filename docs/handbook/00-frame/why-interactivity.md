# Why interactivity

!!! note "Sources & anchors"
    - **Stack component:** Meta
    - **Canonical artifact:** idea note §Conceptual frame 7-paradigm table
    - **Workshop session:** Day-1 AM kickoff (10 min)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

7-paradigm taxonomy (from idea note) translated to research workflow;
the manipulable workflow as the gap.

## The borrowed taxonomy

The argument that interactivity is a medium, not just a feature, has been
made most carefully for mathematics. The Deep Research synthesis
[Interactive Mathematics Beyond the Static
Page](../../reference/research/Interactive Mathematics Beyond the Static Page.pdf)
identifies seven interaction paradigms that recur across the modern
mathematical-software ecosystem, each closing a specific representational
gap that static prose cannot. The table below reproduces the taxonomy from
the [idea note §Conceptual frame](../log/idea/idea-arash-20260507-221835-382557.md)
with the mathematics paradigm on the left and the research-workflow analog
on the right.

| Math paradigm | Research-workflow analog | What it makes visible |
|---|---|---|
| Domain coloring | Pipeline state heatmap | Where in the DAG; what's stale |
| Reactive notebook | Marimo / Observable for analyses | Param → cascade |
| Executable notebook | Jupyter / Marimo narratives | Code + prose + figure together |
| Diagrammatic | Snakemake DAG, projio dependency graph | Composition of computations |
| Proof-aware doc | Provenance-aware doc (claim ↔ data ↔ commit) | Reproducibility as navigable object |
| Expository animation | Manim explainer | Why a workflow is shaped a certain way |
| Geometry viewer | Project topology viewer (multi-repo, cross-link) | What touches what |

The translation is not metaphorical. In each row the *representational
problem* is structurally the same: a high-dimensional or path-dependent
object that resists being read off a page. The mathematics ecosystem
solved its version of that problem by inventing interaction paradigms.
Research workflows can borrow most of them directly: a Snakemake DAG is
already diagrammatic, a Marimo notebook is already reactive, and a
worklog goal graph is already a proof-aware document in everything but
name.

## The gap

The Deep Research synthesis singles out *operator theory* as the
under-served subfield of mathematics — the area where individual
computations (matrix pseudospectra, finite-dimensional solvers) are
well-instrumented but the ambient structure (resolvents, continuous
spectrum, semigroup growth, Banach-space geometry) has no mature
interactive layer. The analog for research practice is direct: tools
exist for individual computations — Jupyter for analysis, Snakemake for
pipelines, DataLad for data — but nothing makes the **whole research
workflow** a manipulable object the way complex-analysis.com makes a
complex function manipulable. The workflow is the operator theory of
research. projio, worklog, and this handbook exist explicitly to close
that gap.

The relevant move is not to add yet another notebook. It is to extend the
*set of paradigms* up one level: from interactive computations to an
interactive composition of computations. A pipeline state heatmap that
shows which rule fired on which subject; a permission scope diagram that
shows what a sandboxed agent can touch; a goal critical-path render that
shows which task unblocks which milestone — these are the workflow-level
analogs of phase portraits and string diagrams.

## Reusable media forms

The Deep Research synthesis makes one further observation that this
handbook takes seriously: the most influential interactive resources did
not just produce content, they invented *forms* that other people then
reused. Sanderson's Manim style, Wegert's phase portraits, IMAGINARY's
exhibition format, and JuliaDynamics' interactive bifurcation diagrams
have become genres in their own right. The handbook commits to three
candidate forms — small enough to be sustainable, opinionated enough to
be recognizable — and uses each one repeatedly so readers learn the
vocabulary by example.

- **Workflow trace.** A visual representation of a research session as
  it actually unfolds: a note becomes a captured idea, the capture is
  promoted to a task, the task dispatches a run, the run produces an
  output, the output is recorded back as a note. This is what an audit
  trail looks like when the audit trail is the primary deliverable. The
  [notio chapter](../60-projio/10-notio.md) introduces the underlying
  log; the [orchestration chapters](../80-orchestration/cross-project-dispatch.md)
  show how traces span projects.

- **Permission scope diagram.** A picture of a project's sandbox: which
  MCP servers are wired up, which Bash patterns are pre-approved, which
  paths the agent can read or write. The diagram makes the agent's
  *blast radius* legible at a glance. It first appears in
  [permissions and bounded context](../70-agentic/permissions-and-bounded-context.md)
  and recurs whenever a chapter introduces a new MCP surface.

- **Goal critical path.** A render of a worklog goal as a milestone
  graph with the critical path highlighted, click-through to each
  milestone's captures and dispatched tasks. This is the orchestration
  layer's flagship form — a planning artifact that is also an
  inspection artifact. It is the worked example in
  [goals and critical path](../80-orchestration/goals-and-critical-path.md).

These three forms are not exhaustive and not final. They are the minimum
working set of media that the handbook commits to making *recognizable*.
If a reader can leave the handbook able to read and produce a workflow
trace, a permission scope diagram, and a goal critical-path render, the
vocabulary has done its job.

## A worked example (placeholder)

The chapter's running example is a workflow trace rendered as a live
explorable: the reader manipulates a small task graph and watches the
worklog scheduler resolve dependencies and dispatch in order. The
explorable is built as a Marimo notebook exported to WASM and embedded
inline; the surrounding stack is taught in [handbook
explorables](../40-marimo/handbook-explorables.md). The prototype is
tracked separately (`docs/log/task/task-arash-20260507-222051-589638.md`).
Until the prototype lands, the slot below is intentionally empty rather
than mocked.

<!-- TODO: E1 — embed marimo-WASM workflow-trace explorable here.
     Real prototype lands via task-arash-20260507-222051-589638.md.
     Do not replace this placeholder with a static image; the whole point
     of the chapter is that the form is live. -->
<div class="explorable-placeholder" data-explorable="E1">
  <em>Explorable E1 — Workflow trace: notes → tasks → dispatched runs →
  outputs. Prototype pending.</em>
</div>

## The caution

The same Deep Research synthesis that motivates this chapter also issues
a warning: interactive systems mislead when rendering artifacts, hidden
defaults, or discretization choices get confused with the underlying
mathematics. The research-workflow analog is the agent's confident output
when the underlying provenance is broken. A polished workflow trace that
omits a failed run, a permission scope diagram that does not reflect the
real settings file, a goal graph rendered from stale capture data — all
of these can produce plausible-looking artifacts that are wrong in ways
the reader cannot see. The handbook's standing answer is the same as
mathematics': keep the symbolic and numerical layers close together,
expose the source, and link every rendered claim back to the data and
commit that produced it. The provenance-aware document is not a luxury;
it is what makes the rest of the medium honest.

## Further reading

- **[Interactive Mathematics Beyond the Static Page](../../reference/research/Interactive Mathematics Beyond the Static Page.pdf)** — Deep Research synthesis; 7-paradigm taxonomy and gap argument that frames this chapter.
- **[Explorable Explanations](https://explorableexplanations.com/)** (Bret Victor) — the foundational manifesto for reactive, manipulable documents.
- **[Distill.pub](https://distill.pub/)** — archive of interactive ML essays; exemplar of the explorable-essay pattern at publication quality.
- **[Bartosz Ciechanowski](https://ciechanow.ski/)** — physics and engineering simulations as interactive essays; the gold standard for manipulable embedded figures.
