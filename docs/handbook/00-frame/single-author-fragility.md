# Single-author fragility

!!! note "Sources & anchors"
    - **Stack component:** Meta
    - **Canonical artifact:** survey §Honest gaps cross-cutting #8
    - **Workshop session:** Day-1 AM kickoff (5 min)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Quantomatic precedent; docs+examples+community as survival strategy;
honest scope.

## The precedent

The Deep Research synthesis [Interactive Mathematics Beyond the Static
Page](../../reference/research/Interactive Mathematics Beyond the Static Page.pdf)
closes with an observation that is uncomfortable to read as the sole
author of a tool you hope other people will use. After cataloguing the
ecosystem's strongest interactive systems, it notes that "many powerful
resources are still tied either to single creators, niche labs, or
volunteer-maintained academic software. This produces brilliance, but
also fragility. Quantomatic's maintenance status is a reminder that
elegant research software can become historically important before it
becomes infrastructurally stable." Quantomatic — a string-diagram
rewriting tool that shaped the diagrammatic-reasoning paradigm in
quantum computing — is still cited, still studied, and effectively no
longer maintained. The category-theory ecosystem moved on to Catlab,
Globular, and homotopy.io; the historically pivotal tool became
historical.

## Direct application

projio and worklog are in exactly that risk class today. Both are
single-creator. Both have made architectural choices — the MCP-first
agent surface, the captures-to-tasks-to-queues flow, the
six-subsystem partition of project knowledge — that other people would
have to *understand* before they could maintain. The handbook does not
pretend otherwise. The seam between "this is the tool I use every day"
and "this is a tool other people can depend on" is precisely the seam
that single-author projects fail to cross.

This is not a counsel of despair. The same Deep Research synthesis
identifies what the healthy end of the ecosystem looks like: "the
healthiest ecosystems are the ones that already combine code, docs,
examples, and community governance: Jupyter, the Wolfram notebook
ecosystem, JuliaDynamics, FEniCSx, Dedalus, SnapPy, and IMAGINARY." Each
of those projects survived a transition out of single-author fragility by
investing in three things that a code repository does not produce on its
own: documentation that a stranger can follow, examples that a stranger
can run, and a community that can take over a chapter, a module, or an
entire subsystem.

## What this handbook is, structurally

This makes the handbook plus the September workshop the documented half
of a deliberate survival strategy. The handbook is the docs+examples leg.
The workshop is the seed of the community leg. They are not outreach,
not marketing, and not (only) pedagogy; they are the components that
move projio from a single-creator dependency into something that has a
chance of outliving its creator. The handbook is published on the same
site as the project's living docs and notes precisely so the chapters
sit next to the artifacts they describe — readers can click through from
a worked example to the actual `pixecog/.projio/pipeio/registry.yml`
that produced it. The workshop hands every participant a copy of the
stack, a working agent setup, and the social context to ask questions
that turn into issues that turn into patches.

## Honest limits

A handbook that is itself part of a survival strategy has to be honest
about scope. Three limits are worth stating up front.

- **The system is not stable yet.** Subsystem APIs change. Notebook
  layouts change. The MCP tool set changes. The handbook is versioned
  with the repository for exactly this reason; a chapter that was right
  six months ago may be wrong today.

- **Two of the six projio subsystems are aspirational at present.**
  Figio and the manuscript pipeline both work in principle but have
  near-zero adoption across the cohort of study projects in the survey.
  The relevant chapters say so directly; they teach what the subsystems
  are *meant* to do without overselling what they currently produce.

- **The agentic layer presupposes Claude Code.** The architecture is
  MCP-first and therefore portable in theory, but every tested workflow
  in this handbook assumes Claude Code as the editor. A chapter that
  describes "the agent" is describing Claude Code with the projio and
  worklog MCP servers wired up. The single-host bias is acknowledged,
  not hidden.

A full inventory of the gaps the handbook is aware of — and what it
intends to do about each — lives in [honest gaps](../99-honest-gaps.md).
That chapter is the natural companion to this one and is written to the
same standard: name the gap, describe what would close it, do not
promise a date.

## The reading

If the handbook succeeds, three things follow. First, a stranger can
stand up the stack from this site alone. Second, a workshop participant
walks out able to read another project's `.projio/` directory and know
what it does. Third, the projects in the survey stop being the only
projects in the survey. None of that is guaranteed by writing the
handbook. All of it is impossible without it.

## Further reading

- **[The Turing Way](https://the-turing-way.netlify.app/)** — patterns for transitioning from solo to collaborative research practice; bus-factor and FAIR principles.
- **[goodresearch.dev](https://goodresearch.dev)** — Patrick Mineault; sustainability and continuity considerations alongside the solo-author workflow.
- **[ml-engineering](https://github.com/stas00/ml-engineering)** (Stas Bekman) — large single-author effort that grew into a community resource; case study in how a solo handbook survives.
