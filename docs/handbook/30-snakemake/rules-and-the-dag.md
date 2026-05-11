# Rules and the DAG

!!! note "Sources & anchors"
    - **Stack component:** Snakemake
    - **Canonical artifact:** `cogpy/src/cogpy/workflows/preprocess/Snakefile`
    - **Workshop session:** Day-1 PM session 1 (Snakemake basics)
    - **Outline:** [`_outline.md`](../_outline.md) §B
    - **Port source:** `teaching/NeuroPySeminar/docs/slides/bootcamp-ii/tutorial-plan.md (step 5: shell + single-file rule)` (NeuroPySeminar — needs refresh for current stack)

## What a rule is

A Snakemake rule is a Python-like block that names one step of an analysis
by declaring what it needs (`input`), what it produces (`output`), and how
to produce it — via a `run` block, a `script` reference, or a `shell`
command. The declaration is not a call. Snakemake reads the file, builds a
graph, and decides later whether and when to execute each rule.

A concrete example from `cogpy/src/cogpy/workflows/preprocess/Snakefile`:

```python
rule raw_zarr:
    """Converts the input dat signal to zarr format."""
    input:
        dat=generate_input_path(".lfp"),
        xml=generate_input_path(".xml")
    output:
        zarr=directory(generate_pipe_path("raw_zarr", ".zarr"))
    threads: 4
    run:
        from cogpy.io import ecog_io
        sigx = ecog_io.from_file(input.dat, input.xml)
        ecog_io.to_zarr(output.zarr, sigx)
```

This rule says: given a `.lfp` signal file and its `.xml` sidecar, produce
a `.zarr` directory by reading with `cogpy.io.ecog_io` and serialising.
The `generate_input_path` and `generate_pipe_path` helpers are ordinary
Python functions that build path strings with wildcard placeholders — when
Snakemake resolves a specific target, it fills in those placeholders for
the requested subject/session/modality combination.

When you ask Snakemake to produce the zarr for subject 01, it looks
backwards from the requested output, finds `raw_zarr`, resolves its inputs,
and schedules the job. That backward resolution — starting from targets and
walking the dependency graph — is the defining property of Snakemake and
the source of its analytical leverage.

## The DAG

A `Snakefile` with several rules is not a script; it is a graph definition.
Snakemake reads all the rules, identifies which outputs each rule can
produce and which inputs it consumes, and builds a **directed acyclic graph
(DAG)** of jobs required to produce the requested targets from the current
state of the filesystem.

The cogpy preprocess pipeline is a clean four-step chain:

```
raw_zarr → lowpass → downsample → feature → badlabel
```

Each step's output is the next step's input. Define these five rules once;
Snakemake runs the chain for every recording session in the dataset without
any explicit looping. The final `rule all` aggregates the terminal outputs:

```python
rule all:
    input:
        interp=generate_pipe_path("interpolate", ".zarr"),
        featuremap=generate_pipe_path("badlabel", ".featuremap.png"),
        pairplot=generate_pipe_path("badlabel", ".pairplot.png")
    output:
        touch(generate_pipe_path("all", ".all"))
```

Snakemake works backwards from `rule all`'s inputs, and the complete chain
is scheduled automatically.

The architectural consequence: **the DAG is constructed from declarations,
not execution history.** A new user can read the Snakefile and see the
entire analysis graph without running anything. A new subject folder dropped
into `raw/` is enough for Snakemake to know it must run all five steps for
that subject.

## Staleness detection

Snakemake's scheduler compares file modification times. If an output file
already exists *and* all its inputs are older than the output, the step is
considered current and skipped. If any input is newer — because a data file
was updated, a script was edited, or a parameter changed — the affected
output and all its downstream descendants are re-queued.

For research workflows this matters: after fixing a bug in the lowpass
filter script, run `snakemake --cores 4`; only the `lowpass` step and
everything downstream regenerates. The raw zarr files, produced before the
edit, are left untouched.

Two flags are worth knowing immediately:

- `--dryrun` prints which jobs *would* run without executing anything —
  the fastest way to audit a re-run before committing to it.
- `--touch` marks all outputs as up-to-date (adjusts their modification
  times) without re-running anything, useful when you've manually verified
  a set of outputs but want Snakemake to consider them current.

## Parallelism

The `--cores` flag tells Snakemake how many CPU cores to use. Given 8
cores and 5 independent subjects, Snakemake schedules up to 5 `raw_zarr`
jobs simultaneously, each allocated `threads: 4`. The `threads:` directive
inside a rule signals that the job is multi-threaded; the scheduler
multiplies across available cores and never over-books.

For compute clusters, `--cluster` and `--executor` flags dispatch jobs to
SLURM or SGE without changing the Snakefile. The rule is identical whether
the job runs on a laptop with 8 cores or a cluster node with 400.

## Why Snakemake over alternatives

**It is Python.** Rules embed Python directly. Scripts are Python.
Configuration is YAML consumed by Python. There is no DSL boundary between
the pipeline description and the analysis code; a researcher who knows
Python can read a Snakefile without learning a second language.

**Staleness is file-based, not database-backed.** Unlike Airflow (execution
history in a database) or CWL (external workflow engine), Snakemake's
staleness model requires no persistent service: the filesystem is the
ground truth. Reproducibility means the output file exists and was produced
from known inputs — and Snakemake can verify this without any external
state.

**BIDS-aware parameterization via snakebids.** The next chapter covers
`generate_inputs()`, which turns a BIDS directory into a table of wildcard
values that Snakemake can expand across subjects, sessions, and runs. No
other mainstream pipeline tool has an equivalent BIDS integration.

The tradeoff: Snakemake does not have a built-in scheduling UI, requires a
Python environment with correct dependencies at execution time, and the
staleness model breaks down when outputs are not files (e.g., database
writes). For the study projects in this cohort — local datasets, SSH
clusters, conda/pixi environments — none of these are binding constraints.

The workshop runs Snakemake through the project's package manager:
`pixi run snakemake --cores 4` in pixi-managed projects (msol, pixecog);
`conda run -n cogpy snakemake --cores 4` in conda-managed ones. This
ensures the correct Python environment without polluting the system PATH.

## Further reading

- **[Snakemake documentation](https://snakemake.readthedocs.io/)** — reference for rule syntax, `input`/`output`, `run`, `shell`, and `script` directives; cluster execution profiles.
- **[Mölder et al. 2021](https://doi.org/10.12688/f1000research.29032.2)** — "Sustainable data analysis with Snakemake," F1000Research; the paper to cite in a methods section.
- **[Snakemake tutorial](https://snakemake.readthedocs.io/en/stable/tutorial/tutorial.html)** — hands-on walkthrough; fastest path from zero to a running first rule.
