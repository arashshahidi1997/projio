---
title: "Adopting Projio"
order: 80
deck: projio-intro
status: draft
tags: [presentation, section]
---

# Adopting Projio

You don't restructure your project to adopt projio. Projio adapts to what's already there.

---

## Start small

```bash
pip install "projio[all]"
cd <your-repo>
projio init --kind <generic | tool | study>
projio sync
```

Open in Claude Code. The MCP tools are permissioned and ready.

Add subpackages one at a time as you need them. Every package degrades gracefully when absent.

---

## Where to go next

- Home: <https://arashshahidi1997.github.io/projio/>
- Quickstart tutorial: `tutorials/quickstart.md`
- Delegation model: `explanation/delegation-model.md` — read this before authoring new flows, results, or deliverables
- Each subpackage has its own docs site

---

## The mental model

> The repository is the primary unit of knowledge.

Projio doesn't ask you to move your work somewhere else. It makes your work legible — to future you, to a collaborator, and to an AI agent — from the place where it already lives.

<aside class="notes">
Close with the line. If one sentence survives the talk, it should be this one.
</aside>
