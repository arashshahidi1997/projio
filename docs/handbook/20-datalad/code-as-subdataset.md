# Code as subdataset

**Status:** draft

!!! note "Sources & anchors"
    - **Stack component:** DataLad
    - **Canonical artifact:** `pixecog/.gitmodules` `code/lib/{cogpy,labbox,labpy}` rows
    - **Workshop session:** Day-1 AM session 2 (DataLad)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Mounting a compute library as a subdataset instead of installing it as a package
ties the code version to the data version in a single git commit. This chapter
explains why the stack makes that choice and what the discipline costs.

## `code/lib/<name>/` as a mounted subdataset

Every study project in this stack mounts its compute libraries under
`code/lib/<name>/`. In gecog, that means `code/lib/cogpy` (the core
electrophysiology library) and `code/lib/labpy` (the lab utility package). In
pixecog, the same two plus `code/lib/labbox` (the MATLAB toolbox). These are
not installed packages. They are **mounted subdatasets**: git repositories
cloned from a shared RIA alias and pinned to a specific commit inside the
superdataset's own git history.

From gecog's `.gitmodules`:

```ini
[submodule "code/lib/cogpy"]
    path = code/lib/cogpy
    url = /storage/share/git/ria-store/alias/cogpy
    datalad-url = "ria+file:///storage/share/git/ria-store#~cogpy"

[submodule "code/lib/labpy"]
    path = code/lib/labpy
    url = /storage/share/git/ria-store/alias/labpy
    datalad-url = "ria+file:///storage/share/git/ria-store#~labpy"
```

The shared store at `/storage/share/git/ria-store/` is the single source of
truth for both libraries. gecog, pixecog, and any other project that uses cogpy
all point at the same store URL. What differs between projects is the **pinned
commit** — the SHA recorded in the superdataset's `.gitmodules` entry for each
`code/lib/` path. The superdataset does not track the library's HEAD; it tracks
the SHA that was current when the superdataset last committed a change to that
entry.

Updating a library is explicit:

```bash
datalad update code/lib/cogpy   # fetch new commits from the RIA alias
git diff code/lib/cogpy         # review what changed
datalad save -m "cogpy: update to v0.9.2"   # record new SHA in superdataset
```

Rolling back is `git checkout <prev-commit> code/lib/cogpy` followed by
`datalad save`. The update history is part of the superdataset's git log.

## Pinned commits and reproducibility

Reproducibility in this stack means: given a superdataset commit, you can
reconstruct the exact state of data, code, and pipeline configuration that
produced a result. The subdataset graph makes that statement concrete:

1. Check out the superdataset at the commit that produced `derivatives/brainstate/`.
2. `datalad get code/lib/cogpy` fetches cogpy at the SHA pinned in that commit.
3. `datalad get raw/sub-01/` fetches the exact raw data.
4. Run the pipeline — same outputs.

A `pip install cogpy` from PyPI or from a mutable local path cannot make that
guarantee: the installed version depends on what was present at install time,
which may differ from what was present when the result was produced. The
mounted-subdataset pattern ties the code version, data version, and pipeline
configuration into one auditable git commit.

This is the reason the stack does not use editable installs (`pip install -e`)
as the primary code-sharing mechanism between projects. Editable installs are
mutable; subdataset pins are not.

## The deliberate choice and its cost

The subdataset pattern has a real cost:

- You must register the subdataset before the first pipeline run.
- You must decide whether to update the pinned commit when the library changes —
  update is *not* automatic.
- In a fresh clone you must `datalad get code/lib/cogpy` before the pipeline
  can import it.

`pip install -e /storage/share/code/cogpy` is six keystrokes. Mounting a
subdataset is a multi-step operation with discipline attached.

The bet is that this cost is paid once and the benefit is permanent. A pip
install that happened in 2024 is invisible in a 2026 audit. A subdataset pin at
commit `a42e381` is in the git history and can be inspected, rolled back, and
explained at any future date. For a project where the question "which version of
cogpy produced this result?" will eventually arise — and it will — the cost is
worth it.

## projio's role: codio registration

projio's `projio sync` auto-discovers `code/lib/<name>/` directories and
registers them in codio with `role=core`, making them queryable by agents via
`codio_discover("signal processing")`. This registration does not create or
modify the subdataset; it maps the library's on-disk location to a searchable
catalog entry. An agent that needs to filter EEG signals can ask codio "what
libraries handle filtering?" without knowing the path.

The mounting itself is a human action, recorded in `.gitmodules`. projio does
not automate it; `pipeio_flow_new` scaffolds the flow directory but leaves
subdataset registration to the user. The honest gap is noted in the survey
(component 2, honest gap): the convention is socially enforced, not automatic,
and a project can be DataLad-initialized while most of its code dependencies
are plain `pip install`s. msol is the example — DataLad initialized, but
`code/lib/ratcave` is the only subdataset, mounted from an external GitHub
remote rather than a shared RIA alias. See [honest gaps](../99-honest-gaps.md).

## Symmetry with derivatives

The decision framework for code applies symmetrically to derivative outputs.
If the result has value independent of the pipeline that produced it — you
publish it, inspect it across runs, reuse it in downstream flows — it belongs
in its own subdataset with the same pinning logic. The `derivatives/<flow>/`
convention in gecog and pixecog is the data-side mirror of the `code/lib/`
convention. Both are described further in
[superdataset and subdatasets](superdataset-and-subdatasets.md).

## Further reading

- **[DataLad handbook §YODA principles](https://handbook.datalad.org/)** — the layout principle that keeps code pinned at a commit inside the superdataset; rationale and workflow.
- **[DataLad run](https://handbook.datalad.org/)** — `datalad run` records a command's provenance alongside the pinned code version.
