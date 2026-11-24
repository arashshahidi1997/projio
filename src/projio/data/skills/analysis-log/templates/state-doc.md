---
thread: {{key}}
title: "{{title}} — analysis state"
state_as_of:
  date: {{date}}
  git_commit: {{git_commit}}
  branch: {{branch}}
  latest_note: {{latest_note}}
  series: [{{key}}]
verification:
  synthesis: agent-extracted
  human_reviewed: false
labels:
  evidence: exploratory | single-session | multi-session | cohort-replicated | independently-validated
  record_status: candidate | active | superseded | invalidated
  review: agent-extracted | human-reviewed
---

# {{title}} — current state

::: {.callout-note}
## What this page is
The current state of the `{{key}}` thread: what we believe now and where the open questions are. It cites result
notes, figures and commits and never copies them. Numbers here are for orientation, with a pointer to their source.
Read the `state_as_of` watermark first: notes in series `{{key}}` newer than it are not folded in yet.

IDs: **R** observed result · **I** interpretation · **D** analysis decision · **O** open question, prefixed
`{{PREFIX}}-`. IDs are stable; a wrong entry is marked `superseded` or `invalidated`, never deleted.
:::

## Scientific question

{{question}}

## Current working model

{{model}}

## Established results

<!-- One entry per finding:
**{{PREFIX}}-R01 — <the observation in one plain sentence>.**
<what was measured, on what, with denominators>.
`evidence: exploratory · record_status: candidate · review: agent-extracted` · hypothesis: H1 ·
→ [[result-…]], <figure path or commit>
-->

## Interpretations

<!-- **{{PREFIX}}-I01 — <the explanation beyond the observations>.** From {{PREFIX}}-R01. `record_status: candidate`
(mark it *untested* when it is; a test it needs is an O item). -->

## Literature grounding

<!-- Prior art per R/I/D entry by citekey, kept apart from the project's own literature derivatives. -->

## Analysis decisions

<!-- **{{PREFIX}}-D01 — <the choice>.** `status: accepted` (<who>, <date>). Why, and what it rules out. → <pointer> -->

## Rejected / superseded

## Open questions

<!-- - **{{PREFIX}}-O01 — <the question it would answer>?** status: open · hypothesis: H1 · <what it needs, or
  "blocked on <ID or substrate>"> → <idea note or pointer>
  - Literature before (<date>): <expected values and traps, by citekey>
  - Literature after (<date>): <our value vs the field's: agree / differ / not comparable, and why>
A resolved item stays, marked `status: resolved → {{PREFIX}}-R0n`. -->

## Next analyses

<!-- Priority order, no time estimates. Each line names the O item it serves. -->

## Evidence index

<!-- Notes, newest first: - [[result-…]] — <one line> ({{PREFIX}}-R01). -->
