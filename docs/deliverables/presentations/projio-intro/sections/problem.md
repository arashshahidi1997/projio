---
title: "Problem"
order: 20
deck: projio-intro
status: draft
tags: [presentation, section]
---

# Problem

A research project's knowledge is scattered.

- Code in `code/`, notebooks in `notebooks/`
- Papers in Zotero or a `bib/` folder, PDFs who-knows-where
- Meeting notes and hypotheses in Obsidian, Google Docs, or nowhere
- Figures baked into slides that nobody can rebuild
- Pipelines in Snakemake, outputs in `derivatives/`, nothing linking them

An AI coding assistant walking into this repo sees files. Not knowledge.

A new collaborator takes weeks to get oriented. Returning after six months feels the same way.

<aside class="notes">
Pixecog is the motivating case: BIDS-structured ecog + neuropixels data, dozens of derivatives, spindle/SWR detection pipelines in active iteration. Without projio, every question — "where did this plot come from? which pipeline produced it? what paper motivated the detector?" — was a multi-step hunt. Projio makes those questions answerable through one MCP surface.
</aside>
