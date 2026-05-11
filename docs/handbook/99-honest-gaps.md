# Honest gaps

!!! note "Sources & anchors"
    - **Stack component:** Meta
    - **Canonical artifact:** [stack-axis survey](../log/result/result-arash-20260508-stack-axis-survey.md) §Honest gaps (8 items, verbatim mapping)
    - **Workshop session:** Day-1 closing + Day-3 closing
    - **Outline:** [`_outline.md`](_outline.md) §B

## Frame

This chapter is the audit trail. Every other chapter in the handbook
asserts that some component of the stack is *adopted* across the
project cohort and *teachable* from a canonical artifact. The
[stack-axis survey](../log/result/result-arash-20260508-stack-axis-survey.md)
that produced the chapter list also produced an inventory of places
where the assertion breaks: conventions that are enforced socially
rather than mechanically, idioms that coexist instead of converging,
features that exist as scaffolding without content, and a structural
fact about the cohort that the rest of the handbook has to treat as a
permanent condition rather than a bug to fix.

The companion chapter [single-author
fragility](00-frame/single-author-fragility.md) names the structural
fact. This chapter names the rest. Each gap is stated once, plainly,
followed by what the handbook does about it. **No new gaps are
introduced here** — the eight below are the survey's enumeration, and
this chapter is the resolution layer, not a new source of truth.

## 1. Derivative roots aren't BIDS-valid

Across pixecog and gecog every flow produces a `derivatives/<flow>/`
tree that *looks* BIDS-shaped — `sub-XX/` directories, modality-typed
files, consistent wildcard ordering — but does not include a
per-derivative `dataset_description.json`. A strict BIDS validator
treating one of those derivative roots as its own BIDS root would
reject it. The shape is there; the metadata that promotes the shape to
a portable BIDS dataset is not.

**What the handbook does about it.** The chapter
[derivatives-and-manifest](10-bids/derivatives-and-manifest.md) teaches
`manifest.yml` as **a projio convention layered on BIDS**, not as BIDS
itself. Workshop participants leave knowing that the manifest is what
makes pipeio's cross-flow contracts work, and that emitting a
`dataset_description.json` for tool-portability beyond the projio
ecosystem is an open convention question — currently considered for
`pipeio_flow_new`, not yet implemented.

## 2. Subdataset-per-derivative is socially enforced

DataLad does not require a study to register every derivative as its
own subdataset. pixecog and gecog both follow the convention (25 and 9
`.gitmodules` entries respectively, every flow's `derivatives/<flow>/`
registered). msol is the counterexample: DataLad-initialized,
one subdataset entry total (`code/lib/ratcave`), every other directory
treated as ordinary in-repo content. Nothing in the stack flagged
this — the convention is carried by humans, not by tooling.

**What the handbook does about it.** The chapter
[code-as-subdataset](20-datalad/code-as-subdataset.md) presents
subdataset-per-derivative as **a deliberate choice the user makes at
flow-creation time**, not as automatic projio behaviour. The right
moment to register the subdataset is when `pipeio_flow_new` scaffolds
the flow, and the handbook treats prompting at that moment as a
plausible future improvement rather than a current guarantee. msol is
named as the project mid-way through adopting the convention so that
participants who inherit a similarly partial setup recognise the
state.

## 3. Three Snakemake idioms coexist

cogpy runs snakebids alone — `generate_inputs()` plus custom path
helpers, no BidsPaths, no manifest. pixecog and gecog run snakebids +
BidsPaths, the style that participates in pipeio's cross-flow
contracts. msol runs plain snakemake with `glob_wildcards()` on flat
paths and no snakebids layer at all. Three real, working styles, one
ecosystem.

**What the handbook does about it.** The chapter
[three-idioms](30-snakemake/three-idioms.md) picks **snakebids +
BidsPaths** as the workshop default and labels the other two
explicitly — snakebids-alone as the predecessor pattern (new flows
should not use it) and plain snakemake as the minimal-ceremony
variant for non-BIDS or one-shot pipelines. The workshop teaches one
style and motivates the others as contrast; trying to teach all three
in four days would dilute the message.

## 4. Marimo explorables have zero existing examples

Marimo plays two roles in the planned stack: per-flow exploratory
notebooks (real on disk in pixecog, scaffolded but mostly empty
elsewhere) and **handbook explorables** exported via `marimo export
html-wasm`. The second role has zero examples in any surveyed
project — every existing marimo file is an exploration notebook tied
to a pipeline, not an embeddable, backend-free WASM bundle for the
docs site.

**What the handbook does about it.** The chapter
[handbook-explorables](40-marimo/handbook-explorables.md) treats the
explorable role as **a deliberate handbook target rather than an
existing artifact to dissect**. Outline §F caps the handbook at five
WASM explorables and names each one (E1–E5) with its host chapter.
Writing those explorables is part of writing the chapter; the
handbook is honest that the first marimo-WASM bundle in the projio
ecosystem will be authored *for the handbook*, not lifted from a
study project.

## 5. The handbook and the workshop don't cross-link

The handbook is an MkDocs site (mkdocs-material, plugin-decorated). The
workshop is a Quarto project under `teaching/agentic-workshop/` that
renders the same source to website + book + slides + executable
notebooks. They live on two different surfaces with two different
generators, and projio currently has no convention for cross-linking
between them. A workshop participant who wants the handbook does so
through the URL bar.

**What the handbook does about it.** The chapter
[two-surfaces-one-cross-link-protocol](50-publication/two-surfaces-one-cross-link-protocol.md)
surfaces this as **a deliberate architectural choice**, not as an
unsolved problem. Workshop handouts link into the handbook by
published URL; handbook chapters cite source artifacts by
repo-relative path. The separation keeps the workshop dataset
detachable, and the handbook does not pretend the gap is a bug.

## 6. `subsystems.<name>.enabled` flags drift from on-disk reality

projio's `.projio/config.yml` carries `subsystems.<name>.enabled` flags
for biblio, notio, codio, figio, pipeio, indexio. msol has biblio and
notio set to off in its config while clearly using both — there are
`.bib` files, there are notes in `docs/log/`, the subsystems are
working. projio does not auto-reconcile the flag with what's actually
on disk.

**What the handbook does about it.** The chapter
[00-stack-aware-layer](60-projio/00-stack-aware-layer.md) advises
periodic `projio sync` to bring the config in line with the
repository state and names the drift as a real failure mode. The
right long-term fix is auto-reconciliation; the present fix is a
documented hygiene command. The handbook does not pretend the flag
is authoritative.

## 7. Hooks are unused and skills aren't uniform

`.claude/settings.json` supports a `hooks` key that lets a project
fire commands on `Stop`, `PreToolUse`, and similar events. **Zero of
the five surveyed projects have any hooks configured.**
Project-local skills under `.projio/skills/` are present in three
projects (projio, cogpy, pixecog) and absent in two (gecog, msol).
The "agent operates with bounded permissions and structured context"
pattern is real — every project has the MCP-server allow-list, the
Bash command shape, the Read globs — but the *richer* expressions of
that pattern (hooks for cross-cutting automation, skills for prompt
templates) are not yet baseline.

**What the handbook does about it.** The chapter
[skills](70-agentic/skills.md) introduces SKILL.md as a graduated
adoption — useful when a project has a repeatable workflow worth
naming, not required from day one. Hooks appear in
[permissions-and-bounded-context](70-agentic/permissions-and-bounded-context.md)
as an *advanced* configuration, not as baseline. The handbook teaches
the shape these features take when present; the workshop does not
require participants to ship a project with either.

## 8. Every project in the cohort has one author

The five projects surveyed (projio, cogpy, pixecog, gecog, msol) are
all sole-authored by Arash. The single-author fragility named in the
source idea note — Quantomatic as the cautionary precedent — applies
to *every* component of the stack as projio currently uses it. There
is no second author, no co-maintainer, no upstream community for
projio itself. The cohort is not representative of multi-author
research practice because it cannot be.

**What the handbook does about it.** [single-author
fragility](00-frame/single-author-fragility.md) names this as
**motivation**, not deflection. The handbook plus the September
workshop are the docs + examples + community legs of a deliberate
survival strategy: the handbook is the docs leg, the workshop is the
seed of the community leg, and the published handbook artifacts (every
chapter cites real files in real projects) are the examples leg. The
goal is not to hide the fragility but to do something about it. The
honest scope statements in that chapter — system not stable yet, two
subsystems aspirational, agentic layer presupposes Claude Code — are
this chapter's natural pair.

## Reading the audit

A reader can use this chapter two ways. Forward, as a way of
calibrating expectations chapter by chapter — when chapter
[code-as-subdataset](20-datalad/code-as-subdataset.md) says
"register every derivative as its own subdataset," the reader knows
that gap 2 already named msol as the project that does not. Backward,
as a way of asking what would close each gap: a derivative
`dataset_description.json` emitter (gap 1), a `pipeio_flow_new` prompt
that registers the subdataset (gap 2), a documented migration off
snakebids-alone (gap 3), the first marimo-WASM bundle (gap 4), a
Quarto-to-MkDocs cross-link mechanism (gap 5), `subsystems.enabled`
auto-reconciliation (gap 6), a starter hook configuration and a
skills-by-default checklist (gap 7), and a second author (gap 8).

Seven of the eight are convention or tooling work that could happen
in a quarter. The eighth is the work the handbook itself is for.

## Further reading

- **[BIDS specification](https://bids-specification.readthedocs.io/)** — the authoritative source for derivative validation requirements described in gap 1.
- **[The Turing Way](https://the-turing-way.netlify.app/)** — community-assembled checklist of common gaps in reproducible research practice.
- **[goodresearch.dev](https://goodresearch.dev)** — the companion handbook against which this cohort's gaps were calibrated.
