pipeio: Contracts & Testing Specification

## Overview

Pipeline validation operates at three levels, each with distinct scope and ownership:

| Level | Scope | Runs when | Who owns it |
|-------|-------|-----------|-------------|
| **Registry contracts** | Config structure, dirs, registry groups | `contracts_validate` (existing) | pipeio |
| **Flow contracts** | Domain-specific I/O validation (`contracts.py`) | Snakemake rules + `contracts_validate` (enhanced) | Flow author |
| **Rule unit tests** | Individual rule correctness against expected outputs | `snakemake --generate-unit-tests` / pytest | Snakemake |

pipeio coordinates all three but only *implements* the first. Flow contracts are user code; rule unit tests are snakemake's built-in capability.

## Level 1: Registry Contracts (existing)

Validates flow metadata — config file exists, `input_dir`/`output_dir` set, registry groups have members with suffix+extension. No code changes needed.

## Level 2: Flow Contracts (enhanced)

### Current state

Flows may define a `contracts.py` module with `validate_inputs()` and/or `validate_outputs()` functions. These are called from Snakemake rules via wrapper scripts (`scripts/validate_inputs.py`, `scripts/validate_outputs.py`) that:

1. Hack `sys.path` to import `contracts.py` from the flow directory
2. Call the validation function with paths from `snakemake.input`/`snakemake.output`
3. Write a summary `.ok` file that downstream rules depend on

This works at runtime but has two problems:
- **No standalone validation**: `contracts_validate` doesn't execute the contract functions — it only checks config metadata. An agent can't ask "are the inputs valid for this flow?" without running snakemake.
- **Fragile imports**: Both the wrapper scripts and any external tests must hack `sys.path` to import from the flow directory.

### Design: contracts_validate executes flow contracts

`contracts_validate` gains the ability to **discover and execute** `contracts.py` modules. For each registered flow:

1. **Discovery** — look for `{flow_dir}/contracts.py`
2. **Import** — `importlib.util.spec_from_file_location()` + `module_from_spec()` (no sys.path mutation)
3. **Introspection** — check for `validate_inputs` and `validate_outputs` callables
4. **Execution** (optional, requires `--run` or `run=True`) — resolve paths from flow config and call the functions
5. **Reporting** — extend `FlowValidation` with contract execution results

#### Path resolution for standalone execution

When contracts run inside snakemake, paths come from `snakemake.input`. When `contracts_validate` runs them standalone, pipeio must resolve paths from the flow's `config.yml`. This uses the existing `FlowConfig` registry to map group/member names to path patterns, then resolves against a specific subject/session (or the first available).

```python
@dataclass
class FlowValidation:
    flow_id: str
    passed: list[str]
    warnings: list[str]
    errors: list[str]
    # New fields:
    has_contracts: bool = False
    contract_functions: list[str] = field(default_factory=list)  # discovered function names
    contract_results: dict[str, Any] = field(default_factory=dict)  # execution results (if run)
```

#### API

```python
# Discovery only (default) — reports which flows have contracts.py
validate_flow_contracts(root, run=False)

# Discovery + execution — actually calls validate_inputs/validate_outputs
validate_flow_contracts(root, run=True, subject="sub-01", session="ses-04")
```

#### MCP tool

```python
def pipeio_contracts_validate(run: bool = False) -> JsonDict:
    """Validate I/O contracts for all flows.

    With run=False (default): checks config structure + reports which flows
    have contracts.py with validate_inputs/validate_outputs.

    With run=True: also executes contract functions against resolved paths.
    """
```

#### Contract module convention

Flow `contracts.py` files follow this convention:

```python
# contracts.py — must be importable standalone (no snakemake dependency)

def validate_inputs(*, path_a: Path, path_b: Path, ...) -> dict[str, Any]:
    """Validate pipeline inputs. Raise on failure, return info dict on success."""
    ...

def validate_outputs(*, path_x: Path, path_y: Path, ...) -> dict[str, Any]:
    """Validate pipeline outputs. Raise on failure, return info dict on success."""
    ...
```

Key constraint: contract functions must be **pure validators** — no side effects, no snakemake dependency. The wrapper scripts (`scripts/validate_inputs.py`) handle logging, `.ok` file writing, and snakemake integration.

### Import mechanism

pipeio provides a helper to cleanly import flow-local modules:

```python
# pipeio.contracts
def import_flow_module(flow_dir: Path, module_name: str) -> ModuleType | None:
    """Import a module from a flow directory without mutating sys.path."""
    module_path = flow_dir / f"{module_name}.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        f"pipeio._flow_modules.{module_name}",
        module_path,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
```

This eliminates `sys.path` hacking in wrapper scripts and external tests. Wrapper scripts can use:

```python
from pipeio.contracts import import_flow_module
contracts = import_flow_module(FLOW_DIR, "contracts")
contracts.validate_inputs(...)
```

**Caveat**: `contracts.py` may import from project libraries (`cogpy`, `utils`). For standalone execution via `contracts_validate`, those libraries must be on `PYTHONPATH` or installed. pipeio should catch `ImportError` gracefully and report it as a warning rather than failing silently.

## Level 3: Snakemake Rule Unit Tests

### How it works

Snakemake's `--generate-unit-tests` captures the state of a successful run:

```
{flow_dir}/.tests/
├── __init__.py
├── common.py                # OutputChecker — byte-level comparison by default
└── unit/
    ├── {rule_name}/
    │   ├── data/            # input files (copied)
    │   └── expected/        # output files (baseline)
    └── test_{rule_name}.py  # pytest file — runs rule in isolation
```

Requires:
1. A prior successful run with small test data
2. `snakemake --generate-unit-tests` to capture inputs/outputs
3. `pytest .tests/` to run

### pipeio's role

pipeio should **surface** snakemake's unit test capability without reimplementing it. Two additions:

#### Discovery: report test status in `flow_status`

`pipeio_flow_status` already reports flow metadata. Extend it to detect `.tests/`:

```python
{
    "flow": "sharpwaveripple",
    "unit_tests": {
        "exists": True,
        "rules_tested": ["validate_inputs", "detect_spwr_events", ...],
        "run_command": "pytest code/pipelines/sharpwaveripple/.tests/"
    }
}
```

#### Generation hint: `pipeio_report`

After a successful `pipeio_run`, the report or status output can suggest generating unit tests if `.tests/` doesn't exist:

```
Hint: run `snakemake --generate-unit-tests` in the flow directory
to capture baselines for rule-level regression testing.
```

pipeio does NOT wrap `--generate-unit-tests` as its own tool — it's a one-time setup step that benefits from manual review of the generated `common.py`.

## What to remove

The pixecog top-level test (`tests/test_sharpwaveripple_contracts.py`) should be deleted once `contracts_validate` can execute flow contracts. Its job — verifying that `validate_inputs()` and `validate_outputs()` work — is subsumed by level 2.

## Migration path

1. **Add `import_flow_module()`** to `pipeio.contracts` — eliminates sys.path hacking
2. **Extend `validate_flow_contracts()`** to discover contracts.py and introspect functions
3. **Add `run=True` mode** to execute contract functions with resolved paths
4. **Update `FlowValidation`** dataclass with contract discovery/execution fields
5. **Extend `flow_status`** to detect `.tests/` directory
6. **Update wrapper scripts** in pixecog to use `import_flow_module()` instead of sys.path hacking
7. **Delete** `tests/test_sharpwaveripple_contracts.py` from pixecog

## Non-goals

- **pipeio is not a test runner** — it discovers and reports; pytest and snakemake do execution
- **No declarative YAML contracts** — the existing `contracts.py` convention with `validate_inputs()`/`validate_outputs()` is expressive enough for domain-specific validation. The YAML schema from the earlier spec draft adds complexity without clear benefit.
- **No flow-local test scaffolding** — pipeio doesn't create `tests/` directories in flows. Snakemake's `--generate-unit-tests` handles rule-level testing; flow-level contract testing is handled by `contracts_validate`.
