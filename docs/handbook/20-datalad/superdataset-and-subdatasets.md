# Superdataset and subdatasets

**Status:** draft

!!! note "Sources & anchors"
    - **Stack component:** DataLad
    - **Canonical artifact:** `gecog/.gitmodules` (survey component 2)
    - **Workshop session:** Day-1 AM session 2 (DataLad)
    - **Outline:** [`_outline.md`](../_outline.md) §B
    - **Port source:** `teaching/NeuroPySeminar/docs/slides/bootcamp-ii/tutorial-plan.md (step 1)` (NeuroPySeminar — needs refresh for current stack)

## Frame

DataLad builds on git by adding content-addressed storage for large files and a
nesting model for repositories. Understanding this two-layer design — git for
metadata, git-annex for content, datasets for composition — is the prerequisite
for everything else in the DataLad chapters.

## git + git-annex: the two-layer design

DataLad layers one idea on top of git: content-addressable storage for files
that should not live inside git's object database. Every binary, every
multi-gigabyte EEG recording, every intermediate file that would bloat a
repository into unusability stays in **git-annex** — a companion store managed
alongside the git object store. git itself tracks the metadata: filenames,
directory layout, checksums, and commit history. git-annex tracks the content,
either locally or in a configured "special remote." The two stores move together;
`datalad save` updates both atomically.

From the user's perspective the split is invisible most of the time. A
`datalad save -m "preprocess: add notch filter"` commits scripts and config to
git and adds large output files to the annex in one command. What makes the
split visible is a freshly cloned repository: the directory tree is there, git
history is there, but the annexed files are hollow symlinks pointing at a
content hash that has not been fetched yet. Running `datalad get
raw/sub-01/ses-pre/ieeg/` pulls those files on demand from whichever sibling has
them. This *thin clone* behavior is why DataLad is practical for
hundreds-of-gigabytes datasets — you fetch exactly what the next step needs,
nothing more.

## Datasets, superdatasets, and subdatasets

The second idea DataLad adds is **nested repositories**. A *dataset* is a
directory that is simultaneously a git repository and a DataLad-managed annex.
A *superdataset* mounts other datasets at specific sub-paths, recorded in
`.gitmodules`. The mounted datasets are *subdatasets* — they have independent
git histories, independent annex stores, and their own siblings, but from the
superdataset's perspective they look like a normal directory.

The superdataset records not just *which* subdatasets are mounted, but *which
commit* of each subdataset is current. That commit SHA is the lock: changing it
is an explicit action (`datalad update code/lib/cogpy` + `datalad save`) that
produces a new superdataset commit. You do not get inadvertent upstream changes
from a library someone else updated.

## Reading `gecog/.gitmodules`

gecog's `.gitmodules` is the canonical teaching artifact (survey component 2 —
nine entries, single RIA store, no rename aliasing). It shows the three-tier
structure in its simplest form:

```ini
[submodule "raw"]
    path = raw
    url = /storage2/ria-store/alias/ds-gecog
    datalad-url = "ria+file:///storage2/ria-store/#~ds-gecog"

[submodule "code/lib/cogpy"]
    path = code/lib/cogpy
    url = /storage/share/git/ria-store/alias/cogpy
    datalad-url = "ria+file:///storage/share/git/ria-store#~cogpy"

[submodule "code/lib/labpy"]
    path = code/lib/labpy
    url = /storage/share/git/ria-store/alias/labpy
    datalad-url = "ria+file:///storage/share/git/ria-store#~labpy"

[submodule "derivatives/fullband_imported"]
    path = derivatives/fullband_imported
    url = /storage2/ria-store/alias/gecog-fullband_imported
    datalad-url = "ria+file:///storage2/ria-store#~gecog-fullband_imported"

[submodule "derivatives/spectrogram"]
    path = derivatives/spectrogram
    url = /storage2/ria-store/alias/gecog-spectrogram
    datalad-url = "ria+file:///storage2/ria-store#~gecog-spectrogram"

[submodule "derivatives/factor_analysis"]
    path = derivatives/factor_analysis
    url = /storage2/ria-store/alias/gecog-factor_analysis
    datalad-url = "ria+file:///storage2/ria-store#~gecog-factor_analysis"

[submodule "derivatives/preprocess_ieeg"]
    path = derivatives/preprocess_ieeg
    url = /storage2/ria-store/alias/gecog-preprocess_ieeg
    datalad-url = "ria+file:///storage2/ria-store#~gecog-preprocess_ieeg"

[submodule "derivatives/brainstate"]
    path = derivatives/brainstate
    url = /storage2/ria-store/alias/gecog-brainstate
    datalad-url = "ria+file:///storage2/ria-store#~gecog-brainstate"
```

Three tiers appear immediately: raw data (`raw/`), shared code libraries
(`code/lib/cogpy`, `code/lib/labpy`), and per-flow derivatives
(`derivatives/*`). Every URL is a RIA alias — no GitHub, no HTTP, just a
content-addressed local path. The clean uniformity (study-specific subdatasets
under `ria-store/alias/gecog-*`, shared libraries under
`storage/share/git/ria-store`) is a deliberate design decision, not a default.

The `datalad-url` field uses the `ria+file://` protocol with a `#~alias`
fragment. This is how DataLad addresses a named alias inside a RIA store —
`#~cogpy` resolves to the cogpy dataset regardless of where the store moves on
disk, as long as the alias entry exists inside the store.

## The subdataset-per-derivative convention

The convention across this stack (gecog and pixecog follow it fully; msol is
mid-adoption) is: **every Snakemake flow's derivative output lives in its own
subdataset.** When `pipeio_flow_new` scaffolds `derivatives/<flow>/`, the
recommended next step is registering it as a DataLad subdataset before the
first `snakemake` run. The rationale: reproducibility requires stating "this
brainstate result was produced by this version of the preprocess_ieeg pipeline
at this commit of cogpy." A flat git repository cannot make that statement in
an auditable form — only the subdataset graph can.

The honest gap: this convention is socially enforced, not automatic. msol has
three Snakemake flows and zero derivative subdatasets registered in
`.gitmodules`. The workshop and handbook should teach the convention as a
deliberate choice the user makes at flow-creation time, not as something projio
enforces. See [honest gaps](../99-honest-gaps.md) for the fuller treatment.

## When to create a new subdataset

Two clear triggers:

1. **Large binary content** — files that would bloat the superdataset's git
   history if committed directly. Raw EEG recordings, model checkpoints, large
   intermediate outputs. If it's bigger than a few megabytes and produced by a
   pipeline, it belongs in the annex, and probably in its own subdataset.

2. **Independent version history** — the directory's history diverges from the
   superdataset's own timeline. Code libraries evolve independently; derivative
   flows produce results on their own cadence. Both warrant a subdataset so
   their history can be pinned, updated, and rolled back independently.

What does *not* need a subdataset: a `scripts/` directory under a flow (small
files, tightly coupled to the flow), a `configs/` directory (YAML, no large
content), or a `docs/` directory. These can live directly in the superdataset.

One trigger that looks obvious but is often wrong: "this is a separate concern."
Code that is reused *across* projects belongs in a shared library subdataset
mounted via a RIA alias — not as a copy in each project. The `code/lib/cogpy`
and `code/lib/labpy` patterns in gecog illustrate this: one store, many
consuming superdatasets, each at a pinned commit.

## Further reading

- **[DataLad handbook](https://handbook.datalad.org/)** — comprehensive reference covering `datalad install`, nested datasets, provenance recording, and the YODA principles.
- **[git-annex](https://git-annex.branchable.com/)** — underlying binary-tracking layer; useful when DataLad's abstraction is insufficient or when working with non-DataLad repositories.
