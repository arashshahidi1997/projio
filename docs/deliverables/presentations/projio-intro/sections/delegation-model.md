---
title: "Engineering vs. Science"
order: 40
deck: projio-intro
status: draft
tags: [presentation, section]
---

# Engineering vs. Science

Projio splits a research project into two surfaces.

| | **Engineering** | **Science** |
|---|---|---|
| Owned by | pipeio | questio · result notes · deliverables |
| Contains | flows, DAGs, configs, rules, notebooks | questions, findings, narrative |
| Answers | *how was it produced?* | *what do we know? why does it matter?* |

---

## One rule: no subsystem embeds content it doesn't own

- A flow page **does not** embed a result plot
- A result note **does not** duplicate engineering rationale
- A deliverable **does not** re-derive the DAG

## One linking direction: downstream → upstream, via frontmatter

![](../../../../assets/excalidraw/delegation-model.excalidraw.svg)

<!-- code-grep-able fallback; uncomment if the SVG is missing or stale.
```
flow  ←──  result note  ←──  deliverable
              │                  │
              └──  question  ←───┘
```
-->

Backlinks (upstream → downstream) are computed at render time. Never stored.

<aside class="notes">
Pixecog example. `preprocess_ieeg` is a pipeio flow — it owns the Snakefile, configs, rules, and the per-subject bad-channel detection logic. A "we detected spindles at 12 Hz with 0.7 F1" result note lives in docs/log/result/, references preprocess_ieeg as its source_flow, and references the relevant question from plan/. This deck is a deliverable — it references questions and flows, but doesn't re-derive them.
</aside>
