# pipeio: Contracts Specification

## Purpose

Contracts define expectations about pipeline inputs and outputs — file existence, required keys, shape constraints, metadata consistency — that can be validated before or after a pipeline run.

## Reference: pixecog's contracts.py

The sharpwaveripple pipeline has an explicit `contracts.py` with two functions:

### `validate_inputs()`

Validates before the pipeline runs:

- LFP file exists and size is divisible by `dtype.itemsize * ChannelCount`
- JSON sidecar has required keys (`SamplingFrequency`, `ChannelCount`)
- Electrodes TSV has a depth column with numeric values
- Brainstate .mat file exists and contains NREM epochs

Returns a dict with validated metadata (`fs`, `nch`, `nrem_epochs`, `depth_col`).

### `validate_outputs()`

Validates after the pipeline runs:

- All expected output files exist (hpclayers.mat, events.mat, triggered.mat)
- events.mat has required keys (`ripples`, `pyrCh`, `Fs`)
- Sampling rate in events.mat matches JSON sidecar
- pyrCh index is within valid channel range
- triggered.mat has required keys (`lfp_avg`, `csd_avg`, `time_axis`)

## pipeio Contracts Framework

### Design

pipeio provides a **generic framework** — individual validators are project-specific. The framework handles:

1. **Check definition** — named checks with descriptions and validation functions
2. **Contract grouping** — a contract bundles related checks
3. **Execution** — run checks against paths, collect pass/fail/error
4. **Reporting** — structured results for CLI and MCP

### API

```python
from pipeio.contracts import Contract, Check, ContractResult

# Define checks
def file_exists(path: Path) -> bool:
    return path.exists()

def file_not_empty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0

# Build a contract
input_contract = Contract(
    name="preprocess-ieeg-inputs",
    checks=[
        Check("exists", "File must exist", file_exists),
        Check("not-empty", "File must not be empty", file_not_empty),
    ],
)

# Validate
result: ContractResult = input_contract.validate([lfp_path, json_path])
assert result.ok
```

### ContractResult

```python
@dataclass
class ContractResult:
    name: str
    passed: list[str]       # "check_name: path"
    failed: list[str]       # "check_name: path"
    errors: list[str]       # "check_name: path: exception message"

    @property
    def ok(self) -> bool:
        return len(self.failed) == 0 and len(self.errors) == 0
```

### Declarative Contracts (Future)

A YAML-driven contract definition for common patterns:

```yaml
# .pipeio/contracts/preprocess-ieeg.yml
name: preprocess-ieeg-inputs
checks:
  - name: lfp-exists
    type: file_exists
    paths: ["${input_dir}/**/*.lfp"]
  - name: json-keys
    type: json_has_keys
    paths: ["${input_dir}/**/*.json"]
    keys: ["SamplingFrequency", "ChannelCount"]
  - name: electrodes-tsv
    type: tsv_has_columns
    paths: ["${input_dir}/**/*_electrodes.tsv"]
    columns: ["x", "y", "z"]
```

### Built-in Check Types

| Type | Description |
|------|-------------|
| `file_exists` | Path exists |
| `file_not_empty` | Path exists and size > 0 |
| `json_has_keys` | JSON file contains required keys |
| `tsv_has_columns` | TSV file has required column headers |
| `yaml_valid` | YAML file parses without error |
| `size_divisible` | File size is divisible by a given factor |

### CLI

```
$ pipeio contracts validate preprocess/ieeg --stage inputs
Contract: preprocess-ieeg-inputs
  ✓ lfp-exists: 24/24 passed
  ✓ json-keys: 24/24 passed
  ✗ electrodes-tsv: 22/24 passed, 2 failed
    FAIL: sub-A01/ses-02 — missing column 'z'
    FAIL: sub-A03/ses-01 — file not found

$ pipeio contracts validate preprocess/ieeg --stage outputs
Contract: preprocess-ieeg-outputs
  ✓ all checks passed (96/96)
```
