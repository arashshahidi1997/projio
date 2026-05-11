# Derivatives and manifest

**Status:** draft

!!! note "Sources & anchors"
    - **Stack component:** BIDS
    - **Canonical artifact:** `pixecog/derivatives/preprocess_ieeg/manifest.yml`
    - **Workshop session:** Day-1 AM session 1 (BIDS)
    - **Outline:** [`_outline.md`](../_outline.md) §B
    - **Port source:** `teaching/NeuroPySeminar/docs/slides/bootcamp-ii/tutorial-plan.md (step 4)` (NeuroPySeminar — needs refresh for current stack)

## Frame

`derivatives/<flow>/`; `manifest.yml` as a projio convention layered on BIDS.

## One derivative root per flow

BIDS reserves `derivatives/` for processed output. The convention this cohort
follows — and the one pipeio enforces by default — is one subdirectory per
pipeline flow:

```
derivatives/
├── preprocess_ieeg/
├── calibrate_ieeg/
├── lfp_extrema/
├── spectrogram_burst/
├── brainstate/
└── ...                  # pixecog has 18 in total
```

The separation is deliberate. An individual flow's output directory is
self-contained: it holds the outputs of exactly one computational step. When
a flow is rerun with new parameters, only its derivative root changes.
Downstream flows that depend on it read from that root and are unaffected by
reprocessing upstream flows that they don't use.

Each derivative root is also a DataLad subdataset in the electrophysiology
projects (pixecog, gecog). That means a collaborator can `datalad install`
just `derivatives/preprocess_ieeg/` — getting exactly the preprocessed
intracranial recordings without the raw data or any other derivative — inspect
provenance, and verify outputs without cloning the entire study dataset. The
subdataset-per-derivative pattern is discussed further in
[Code as subdataset](../20-datalad/code-as-subdataset.md).

## What BIDS says and what it doesn't

BIDS specifies that derivative outputs go under `derivatives/<name>/` and
recommends that each derivative directory contain a `dataset_description.json`
identifying the pipeline that produced it. That is the full extent of BIDS's
guidance on derivatives: where they live and how to label the generating
pipeline. BIDS says nothing about:

- Which output file types a flow can produce for each subject
- What BIDS path coordinates (root, datatype, suffix, extension) each output
  occupies
- How a downstream flow should locate and pattern-match its upstream inputs
  when those inputs come from a prior derivative rather than from `raw/`

The cross-flow contract problem — "downstream flow B needs to know exactly
where upstream flow A's outputs live" — is real and BIDS doesn't solve it.
`manifest.yml` does.

## manifest.yml: the cross-flow contract

A `manifest.yml` at the root of a derivative directory names the output groups
that flow can produce, expressed in BIDS path coordinates. Here is a
representative excerpt from `pixecog/derivatives/preprocess_ieeg/manifest.yml`:

```yaml
interpolate:
  base_input: ieeg
  bids:
    root: interpolate
    datatype: ieeg
  members:
    lfp:
      suffix: ieeg
      extension: .lfp
    json:
      suffix: ieeg
      extension: .json
    electrodes:
      suffix: electrodes
      extension: .tsv
    channels:
      suffix: channels
      extension: .tsv
    log:
      suffix: ieeg
      extension: .log

noise:
  base_input: ieeg
  bids:
    root: noise
    datatype: ieeg
  members:
    tsv:
      suffix: rowcol_noise
      extension: .tsv
    npz:
      suffix: rowcol_noise
      extension: .npz
    log:
      suffix: rowcol_noise
      extension: .log
```

Each top-level key (`interpolate`, `noise`, `linenoise`, `crosstalk_correct`,
and others in the full file) is a named output group. Each group declares:

- `bids.root` — which subdirectory within `derivatives/preprocess_ieeg/` to
  treat as the local BIDS root for this group's outputs
- `bids.datatype` — the BIDS datatype folder (`ieeg`, `ecephys`, etc.)
- `members` — one entry per output file kind, each with the BIDS `suffix` and
  `extension`

The `base_input` field names which BIDS input query this group's wildcards
derive from — it tells pipeio's `BidsPaths` adapter how to map subject/session
wildcards to file paths.

## How downstream flows consume the manifest

A downstream flow loads the manifest and constructs paths through pipeio's
`BidsPaths` adapter. The pattern in pixecog's `lfp_extrema` Snakefile:

```python
from pipeio.adapters.bids import BidsPaths
import yaml

manifest = yaml.safe_load(
    Path(config["bids_dir_ieeg"], "manifest.yml").read_text()
)
paths = BidsPaths(manifest, config["bids_dir_ieeg"], inputs)
```

After that, path construction for any group/member combination becomes a
method chain:

```python
# Resolve the .lfp output for sub-01, ses-04, run-01
paths.interpolate.lfp.subject("01").session("04").run("01")
```

`pipeio_target_paths(flow, group, member)` is the MCP tool equivalent: it
resolves the same path without writing any Python. An agent authoring a new
rule can ask "where does `preprocess_ieeg`'s `interpolate.lfp` output for
subject 01 land?" and get the answer without constructing the path by hand.

The downstream Snakefile never sees path strings. It sees wildcard-resolved
`BidsPaths` objects. When the upstream flow changes its internal naming, the
manifest is updated and every downstream flow automatically follows — the
contract surface is the manifest, not each individual output path.

## What the manifest is and isn't

The manifest is a **projio convention layered on BIDS**, not a BIDS
specification. A standard BIDS tool or validator will not know what to do with
it. A derivative directory that contains only a `manifest.yml` and not a
`dataset_description.json` is not BIDS-valid as an independent derivative
dataset — and pixecog's and gecog's derivative roots are exactly in that
situation.

The tradeoff was made deliberately. The manifest solves the cross-flow
contract problem BIDS doesn't address. The cost is that derivative roots are
not tool-portable beyond the pipeio ecosystem. A future iteration of pipeio
may emit a `dataset_description.json` per derivative root alongside the
manifest, which would make the directory both BIDS-valid and pipeio-queryable.
For now, the manifest pattern is documented as an explicit departure from full
BIDS and is catalogued in [Honest gaps](../99-honest-gaps.md) §1.

The practical rule: treat `raw/` as strictly BIDS, treat `derivatives/<flow>/`
as pipeio-extended BIDS. Both use BIDS path grammar. Only the former is
validator-clean.

## Further reading

- **[BIDS derivatives specification](https://bids-specification.readthedocs.io/en/stable/derivatives/introduction.html)** — formal rules for derivative dataset layout, `dataset_description.json` in `derivatives/`, and `GeneratedBy` provenance fields.
- **[PyBIDS](https://pybids.readthedocs.io/)** — `BIDSLayout(derivatives=True)` for querying processed outputs alongside raw data.
