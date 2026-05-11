# Config-driven pipelines

!!! note "Sources & anchors"
    - **Stack component:** Snakemake
    - **Canonical artifact:** `pixecog/code/pipelines/lfp_extrema/Snakefile` + `pixecog/code/pipelines/lfp_extrema/config.yml`
    - **Workshop session:** Day-1 PM session 2 (advanced rule chain)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## The configuration file is a pipeline parameter

Every Snakemake pipeline that ships under `code/pipelines/<flow>/` carries
a `config.yml` alongside the Snakefile. This file is not metadata or
documentation — it is the runtime parameter table that the Snakefile reads
with `configfile: "config.yml"` before any rule runs. Changing a value in
`config.yml` changes what outputs are produced without editing the
Snakefile at all.

This separation — *logic in the Snakefile, parameters in config* — is the
difference between a hardcoded analysis and a reusable pipeline. A pipeline
where the subject list, the filter cutoff, the BIDS root, and the detection
parameters are all in `config.yml` can be redeployed on a new dataset by
writing a new config. The analysis code is untouched.

## The `lfp_extrema` pipeline as the canonical example

`pixecog/code/pipelines/lfp_extrema/` is the richest example of
config-driven design in the project cohort. Its `config.yml` declares the
pipeline's two input roots (raw LFP from ecephys and TTL-cleaned LFP from
ieeg), the output root, the BIDS wildcard filters per modality, and the
detection parameters:

```yaml
bids_dir: "raw"
bids_dir_ieeg: "derivatives/preprocess_ieeg/ttl_removal"

pybids_inputs:
  ecephys:
    filters:
      suffix: 'ecephys'
      extension: '.lfp'
      recording: 'lf'
      acquisition: 'lshank'
    wildcards: [subject, session, task, acquisition, recording]
  ieeg:
    filters:
      suffix: "ieeg"
      extension: ".lfp"
      datatype: "ieeg"
    wildcards: [subject, session, task]

output_dir: "derivatives/lfp_extrema"
output_manifest: "derivatives/lfp_extrema/manifest.yml"
```

This is the static part of the config: it does not change across
experimental conditions. The *dynamic* part — the detection sweep — is
declared separately.

## The registry-extension pattern

The `lfp_extrema` Snakefile builds its output registry dynamically by
reading a `detections` list from config and extending the registry with one
group per detection-tuple:

```python
_registry = dict(config.get("registry") or {})
_detections_cfg = config.get("detections") or []

for _det in _detections_cfg:
    _name = _det["name"]
    _device = _det.get("device", "ieeg")
    _datatype = "ieeg" if _device == "ieeg" else "ecephys"
    _base_input = "ieeg" if _device == "ieeg" else "ecephys"
    _registry[f"detect_{_name}"] = {
        "base_input": _base_input,
        "bids": {"root": f"detect/{_name}", "datatype": _datatype},
        "members": {
            "events": {"suffix": _name, "extension": ".tsv"},
            "log": {"suffix": _name, "extension": ".log"},
        },
    }
```

The `detections` list in `config.yml` might look like:

```yaml
detections:
  - name: spindle_v1
    device: ieeg
  - name: spindle_v2
    device: ieeg
  - name: ripple_v1
    device: ecephys
```

Three entries in config → three registry groups added programmatically →
three output trees under `derivatives/lfp_extrema/detect/<name>/`.
**The Snakefile did not change.** The survey design changed in config.

After the loop, `BidsPaths` is constructed from the extended registry:

```python
out_paths = BidsPaths(_registry, repo_abs(config["output_dir"]), inputs)
```

`BidsPaths` resolves every registry group against the wildcard expansion
from `generate_inputs()`, so every detection-tuple gets a full path table
for every subject/session/task combination. `rule all` asks for all of
them; Snakemake builds the complete DAG in one pass.

## Slow-wave as a deep case: seven outputs per detection

The `slowwave_so` entries in `config.yml` demonstrate how the
registry-extension pattern handles non-trivial fan-out. Each slow-wave
detection algorithm produces not one but seven output types: one cycle
parquet (intermediate) plus six event TSVs corresponding to phase-detection
variants (up, down, four transition methods). The Snakefile registers all
seven per detection-tuple:

```python
for _det in _slowwave_so_cfg:
    _name = _det["name"]
    # base group: cycle + log
    _registry[f"detect_{_name}"] = { ... }
    # six sub-groups, one per event suffix
    for _suffix in ("up", "down", "down2up_dvdt",
                    "up2down_dvdt", "down2up_zc", "up2down_zc"):
        _registry[f"detect_{_name}_{_suffix}"] = { ... }
```

Adding a new slow-wave algorithm to the sweep means adding one entry to
`config.yml`. The seven output groups for the new detector are registered
automatically; `manifest_assemble` (a downstream flow) picks them up via
the manifest. No Snakefile edit, no rule duplication.

## The leverage of declarative sweep design

The practical consequence of the registry-extension pattern is that the
config file *is* the experimental design. A collaborator can read
`config.yml` and understand exactly what conditions are being compared:
which detection algorithms, on which modality, with which parameters.
The Snakefile is the machinery; the config is the science.

This is qualitatively different from parameterizing a script with command-line
flags. Command-line flags run one condition at a time; config-driven registry
extension runs all conditions in a single `snakemake --cores 16` invocation,
producing all outputs in parallel, tracking staleness per condition, and
writing results to a structured output tree that downstream flows (and
pipeio's `manifest_assemble`) can consume without knowing which conditions
were active.

For sweep designs — comparing filter settings, algorithm hyperparameters,
or preprocessing choices across subjects — this is the right unit of
abstraction. The researcher defines the sweep in config, verifies the
expected DAG with `snakemake --dryrun`, and runs.

<!-- TODO: E2 — DAG explorable: render pixecog/code/pipelines/lfp_extrema/Snakefile
as interactive DAG; toggle config detection entries → DAG re-fans-out.
See _outline.md §F #E2. -->

## Config as the cross-flow contract input

The config file also points to upstream manifests — the structured outputs
written by prior flows that this flow consumes as inputs:

```yaml
input_manifest: "derivatives/preprocess_ecephys/manifest.yml"
input_manifest_ieeg: "derivatives/preprocess_ieeg/manifest.yml"
```

The Snakefile reads these manifests at startup and uses them to resolve
which preprocessed files are available. If the upstream flow has not been
run for a given subject, that subject's wildcard combination will not
appear in `generate_inputs()` results, and no detection jobs will be
scheduled for it. The config drives what runs; the manifests constrain
what is possible.

This two-level design — config as the *intent*, manifest as the
*actuality* — is the cross-flow contract that replaces ad-hoc path
construction. See [`60-projio/20-pipeio.md`](../60-projio/20-pipeio.md)
for how pipeio's `BidsPaths` formalises this contract at the tool level.

## Further reading

- **[Snakemake §Configuration](https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html)** — `configfile:`, the `config` dict, and profile-based configuration for reproducible parameter sweeps.
- **[snakebids documentation](https://snakebids.readthedocs.io/)** — how snakebids config extends Snakemake's own config with BIDS-aware input specifications.
