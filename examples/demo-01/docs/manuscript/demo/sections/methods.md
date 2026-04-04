---
title: "Methods"
order: 3
manuscript: demo
status: draft
tags: [manuscript, section]
---

# Methods

## Corpus

We assembled a corpus of two text samples from the demo dataset. Each sample
was tokenized and word frequencies were computed using a custom Python pipeline.

## Analysis

Word frequencies were ranked in descending order. We fitted a power-law model
to the rank-frequency data using least-squares regression on log-transformed
values.
