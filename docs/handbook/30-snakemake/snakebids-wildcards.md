# Snakebids and wildcards

!!! note "Sources & anchors"
    - **Stack component:** Snakemake
    - **Canonical artifact:** `cogpy/src/cogpy/workflows/preprocess/Snakefile`; `pixecog/code/pipelines/lfp_extrema/config.yml` (for `generate_inputs()` shape)
    - **Workshop session:** Day-1 PM session 1 (Snakemake basics)
    - **Outline:** [`_outline.md`](../_outline.md) §B
    - **Port source:** `teaching/NeuroPySeminar/docs/slides/bootcamp-ii/tutorial-plan.md (step 5: multifile + snakebids)` (NeuroPySeminar — needs refresh for current stack)

## The problem wildcards solve

A preprocessing pipeline that has five rules should not care whether the
dataset has five subjects or five hundred. Without wildcards, the researcher
either (a) writes one rule per subject by hand, (b) wraps the Snakefile in
a Python loop, or (c) invokes Snakemake inside a shell loop — all of which
produce fragile, hard-to-read pipelines where the number of subjects is
baked into the code.

Snakemake wildcards eliminate this. A wildcard is a named placeholder
inside an input or output path. Snakemake infers which values each wildcard
can take from the requested targets, then instantiates one job per
combination. Change the dataset from 5 to 50 subjects and re-run — no
Snakefile edit required.

## Wildcards in a plain Snakemake rule

The cogpy preprocess pipeline (`cogpy/src/cogpy/workflows/preprocess/Snakefile`)
uses a `path_placeholderstring()` helper that embeds wildcard placeholders
directly in path templates:

```python
def path_placeholderstring():
    return "{sub}/{session}/{modality}/{sub}-{session}-{task}"

def generate_pipe_path(step_name, ext):
    return str(Path("preproc-results") / step_name / path_placeholderstring()) + ext
```

The `{sub}`, `{session}`, and `{task}` tokens are Snakemake wildcards.
When `rule lowpass` declares:

```python
rule lowpass:
    input:
        raw=ancient(generate_pipe_path("denoised", ".zarr"))
    output:
        filtered=directory(generate_pipe_path("lowpass", ".zarr"))
    params:
        cutoff=config["prep"]["cutoff_lp"],
        order=config["prep"]["order"],
        btype="lowpass"
    script:
        "scripts/01_filter.py"
```

Snakemake infers the wildcard values from the targets passed to `rule all`.
Every distinct `(sub, session, modality, task)` tuple in the target list
becomes one independent job. The rule body — the script call — is identical
across all tuples.

## The four-step chain end-to-end

The full cogpy preprocess chain is:

```
raw_zarr → lowpass → downsample → feature → badlabel
```

In rule form, each step passes its output directory to the next as input.
Snakemake materialises this chain for every subject/session combination
defined by the targets in `rule all`. If there are 20 sessions in the
dataset, Snakemake schedules 20 independent five-step chains and runs them
in parallel up to the `--cores` limit — without any explicit parallelism
in the Snakefile.

This is the core leverage: **one chain definition covers any number of
sessions.** The researcher writes the analysis logic once, in a form that
documents the dependency graph, and Snakemake handles the combinatorial
expansion.

## `generate_inputs()` — BIDS-aware wildcard generation

The cogpy Snakefile uses a custom path scheme that predates the current
BIDS-integrated pattern. The current workshop default — used in pixecog and
gecog — replaces custom path helpers with `snakebids.generate_inputs()`,
which reads a BIDS directory and returns a dictionary of wildcard tables
keyed by modality.

The `pixecog/code/pipelines/lfp_extrema/config.yml` shows the configuration
shape:

```yaml
pybids_inputs:
  ecephys:
    filters:
      suffix: 'ecephys'
      extension: '.lfp'
      recording: 'lf'
      acquisition: 'lshank'
    wildcards:
    - subject
    - session
    - task
    - acquisition
    - recording
  ieeg:
    filters:
      suffix: "ieeg"
      extension: ".lfp"
      datatype: "ieeg"
    wildcards:
    - subject
    - session
    - task
```

Each entry under `pybids_inputs` is one input modality. `filters` selects
which files match (by BIDS suffix, extension, and sidecar metadata).
`wildcards` lists which BIDS entities become Snakemake wildcards for that
modality.

In the Snakefile, this config is consumed as:

```python
from snakebids import generate_inputs, set_bids_spec
set_bids_spec("v0_0_0")

configfile: "config.yml"

inputs = {}
if _ecephys_pb and Path(_bids_dir_ecephys).exists():
    inputs.update(generate_inputs(_bids_dir_ecephys, _ecephys_pb))
if _ieeg_pb and Path(_bids_dir_ieeg).exists():
    inputs.update(generate_inputs(_bids_dir_ieeg, _ieeg_pb))
```

`generate_inputs()` walks the BIDS directory, applies the filters, and
returns an `inputs` dict. Each key (e.g. `"ecephys"`, `"ieeg"`) maps to a
`BidsDatasetDict` that knows (a) which files match and (b) what wildcard
values each matched file carries. Rules can then use `inputs["ecephys"]`
to get the expanded input list, and a `bids()` call to construct the
output path in BIDS format.

The workshop will run `generate_inputs()` on a small BIDS dataset (6
subjects, 2 sessions each) and print the resulting wildcard table, making
the mapping from directory structure to wildcard table explicit before
writing any rules.

## `expand()` for aggregation

Individual rules are per-session. Some steps — group-level statistics,
quality reports, manifest assembly — need to run once over *all* sessions.
Snakemake's `expand()` function materialises a wildcard pattern across all
known values:

```python
rule all:
    input:
        expand(
            generate_pipe_path("badlabel", ".npy"),
            sub=inputs["ieeg"].wildcards.subject,
            session=inputs["ieeg"].wildcards.session,
            modality=...,
            task=...,
        )
```

`expand()` takes a path template and keyword arguments whose values are
lists; it returns the full cross-product of paths. The `rule all` input is
the full list of expected terminal outputs; asking Snakemake to build `all`
triggers the entire graph for every combination.

In the pixecog + gecog style, `BidsPaths` replaces the raw `expand()` call
with a structured object that knows the registry layout — the next chapter
covers this in full.

## How wildcards collapse 50 files into one rule

The practical summary: a dataset with 5 subjects × 10 sessions ×
2 tasks = 100 recordings. Without wildcards, 100 separate rule invocations
or a loop. With wildcards and `generate_inputs()`, one rule handles all
100. The Snakemake scheduler builds the DAG for all 100 in one pass,
parallelises them across available cores, and tracks staleness per output.
Add a 6th subject — drop one folder into `raw/` — and re-run. Snakemake
infers the new wildcard values, adds the corresponding jobs, and runs only
what is missing.

This is the reason wildcards are not a convenience feature but the
architectural foundation of BIDS-aware pipelines: the BIDS directory
structure is the runtime parameter table for the wildcard expansion.

## Further reading

- **[snakebids documentation](https://snakebids.readthedocs.io/)** — `generate_inputs()`, `BidsComponent`, and the snakebids YAML config format.
- **[BIDS specification §entities](https://bids-specification.readthedocs.io/)** — entity definitions (`sub`, `ses`, `run`, `task`) that map directly to snakebids wildcard names.
