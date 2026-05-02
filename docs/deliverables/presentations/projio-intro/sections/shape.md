---
title: "The Shape"
order: 30
deck: projio-intro
status: draft
tags: [presentation, section]
---

# The Shape

Projio sits between a research repository and the tools — human or AI — that want to query it.

- One **MCP entrypoint** exposes ~70 tools
- Each tool delegates to a focused **sibling package**
- Projio itself stays small: scaffolding, site workflows, questio, MCP wiring

![](../../../../assets/excalidraw/projio-shape.excalidraw.svg)

<!-- code-grep-able fallback; uncomment if the SVG is missing or stale.
```
        your research repo (code · papers · notes · data)
                         │
                       projio
                         │
         ┌───────────────┴────────────────┐
         │    MCP server  —  ~70 tools    │
         └─┬──────┬──────┬──────┬──────┬──┘
           │      │      │      │      │
      indexio biblio  notio  codio  questio
                        │      │
                     pipeio  figio
```
-->

<aside class="notes">
Core idea: the repo stays the primary unit of knowledge. Projio makes it queryable without asking you to move anything.
</aside>
