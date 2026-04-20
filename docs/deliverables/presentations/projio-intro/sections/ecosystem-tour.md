---
title: "Ecosystem Tour"
order: 60
deck: projio-intro
status: draft
tags: [presentation, section]
---

# Ecosystem Tour

Four layers. Each subpackage owns one domain and can be used independently.

---

## Retrieval substrate

**indexio** — domain-agnostic corpus indexing, chunking, embedding, semantic search.

Every other package registers sources here. RAG queries cross all of them.

---

## Knowledge layer

- **biblio** — project-centric bibliography. Zotero sync, OpenAlex/Crossref enrichment, PDF fetch, GROBID/Docling parsing, compiled BibTeX
- **notio** — structured project notes, idea capture, worklog. Hosts `manuscript` and `present` subpackages for paper/deck production
- **codio** — code-library registry with three tiers (core / shared / external), reuse discovery

---

## Engineering layer

- **pipeio** — agent-facing pipeline authoring. Flows, contracts, notebook lifecycle, Snakemake integration. Owns engineering, **not** science
- **figio** — declarative figure orchestration. FigureSpec YAML → panels → SVG/PDF composition

---

## Science & delivery

- **questio** (in projio core) — research questions, hypothesis tracking, prior art, binding of questions → results
- **notio/manuscript** — section assembly, citation checking, pandoc → PDF/LaTeX
- **notio/present** — reveal.js and Marp decks; cross-project section import
- **deliverables** — reports, decks, posters for external audiences

<aside class="notes">
Pixecog uses every layer: indexio queries its docs corpus, biblio tracks neuropixels / ECoG references, pipeio owns `preprocess_ieeg` and the SWR-detection flows, figio renders spectrograms, questio binds findings back to hypotheses. This deck itself is a presentio deliverable in the projio repo.
</aside>
