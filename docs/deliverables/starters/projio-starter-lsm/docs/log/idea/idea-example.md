---
title: "Example idea: detect bursts in the resting-state EEG — but the proposed threshold conflicts with the pipeline"
date: 2026-09-01
tags: [idea, example, starter]
---

## The idea

The synthetic signal in `data/raw/sub-01/eeg/sub-01_task-rest_eeg.txt`
contains transient bursts. A first analysis pass should:

1. High-pass filter (**1 Hz**) and notch (50 Hz)
2. Compute a moving-window RMS envelope
3. Threshold at `mean + Nσ` and segment burst events
4. Report event count + mean duration per burst

**Open question I want the agent to resolve:** the threshold should be
either `3σ` or `4σ`. I haven't picked one. The right answer depends on
the noise floor of this specific recording — the agent should look at
the actual signal in `data/raw/sub-01/eeg/sub-01_task-rest_eeg.txt`
(check its sampling rate from `data/raw/sub-01/eeg/sub-01_task-rest_eeg.json`
if present, otherwise estimate from the file's line count vs.
`participants.tsv`) and the existing cleaning script
`code/pipelines/demo/scripts/clean.py` and *recommend a threshold
with justification.*

## What the agent has to do

A good response to *"summarise the idea in `docs/log/idea/` and propose
one next step"* is **not** a paraphrase of the list above. It should:

1. **Read at least two files beyond this one** — at minimum
   `code/pipelines/demo/scripts/clean.py` (to see the actual filter
   settings the pipeline applies) and `data/raw/sub-01/eeg/…` (to see
   what's in the signal).
2. **Flag the inconsistency** between this idea's *1 Hz high-pass* and
   whatever the script actually uses. If `clean.py` uses a different
   cutoff (e.g., 0.5 Hz), the agent must surface that as a decision the
   human has to make, not silently adopt one side.
3. **Pick `3σ` or `4σ`** with a sentence of justification grounded in
   the actual signal, not a textbook default.
4. **Propose the next step**: usually "run the pipeline, write a
   result note in `docs/log/result/` citing this idea note as
   `source_idea:`."

## Why this is in `docs/log/idea/`

This file captures *intent* — the question, the hypothesis, the open
sub-decisions — before any code lands. In a real project the intent
note is the artifact the result note cites as its provenance source.
Closing that loop (claim → code → idea → data) is the whole point of
the *receipts-on-disk* convention.

## Suggested next step (after the agent does its work)

```bash
cd code/pipelines/demo
pixi run snakemake --cores 1
```

The output lands in `data/derivatives/demo/sub-01/`. The agent's
result note (`docs/log/result/result-…burst-counts.md`) cites this
idea note and the executed pipeline rule as its two sources.
