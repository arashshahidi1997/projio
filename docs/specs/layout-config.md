# Spec: Centralize directory layout into config

**Status:** draft  
**Related:** idea-arash-20260411-193310-336553  
**Branch:** `feat/layout-config-centralize`

## Problem

Directory paths throughout projio are hardcoded or use discovery patterns that override config values. This prevents profiles from customizing project layout (e.g., `pipelines/` instead of `code/pipelines/`, `lib/` instead of `code/lib/`).

The idea audit identified 8 hardcoded path families across 5 files in projio core and 4 files in the pipeio submodule (~27 occurrences in pipeio alone).

## Design

### 1. Config schema: `layout:` section

Add a `layout:` section to `.projio/config.yml`:

```yaml
layout:
  docs: docs
  notes: docs/log
  pipelines: code/pipelines
  libraries: code/lib
  utils: code/utils
  skills: .projio/skills
  plan: plan
```

All values are **relative to project root**, no trailing slashes. Every key has a default matching current hardcoded values, so existing projects with no `layout:` section work unchanged.

### 2. `Layout` dataclass in `config.py`

```python
@dataclasses.dataclass(frozen=True)
class Layout:
    docs: str = "docs"
    notes: str = "docs/log"
    pipelines: str = "code/pipelines"
    libraries: str = "code/lib"
    utils: str = "code/utils"
    skills: str = ".projio/skills"
    plan: str = "plan"

    def resolve(self, root: Path, key: str) -> Path:
        """Return absolute path for a layout key."""
        return root / getattr(self, key)

    @classmethod
    def from_config(cls, cfg: dict) -> "Layout":
        raw = cfg.get("layout", {}) or {}
        # Only pass known fields
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in known})
```

### 3. Loading convention

- `load_effective_config()` already merges user + project config — `Layout.from_config()` reads from that merged dict.
- Add a convenience `load_layout(root) -> Layout` that does both steps.
- Subsystems receive the `Layout` (or specific paths) rather than doing their own discovery.

### 4. Derived paths

Some paths are computed from layout keys. These are **not** independent layout keys — they're conventions within a layout key's subtree:

| Derived path | Computed from | Example |
|---|---|---|
| `docs/pipelines/` | `{layout.docs}/pipelines/` | Published pipeio docs |
| `docs/prompts/workflows/` | `{layout.docs}/prompts/workflows/` | Workflow prompts |
| `{flow}/scripts/` | `{layout.pipelines}/{flow}/scripts/` | Flow scripts |
| `{flow}/docs/{mod}/` | `{layout.pipelines}/{flow}/docs/{mod}/` | Mod faceted docs |

These are **not** configurable independently — they follow from the parent layout key. This keeps the config surface small.

### 5. Pipeio integration

Pipeio currently discovers `pipelines_dir` via filesystem fallback (`code/pipelines` → `pipelines`). The fix:

- **Projio → pipeio bridge:** When projio's MCP server calls pipeio functions, it passes `pipelines_dir` resolved from `Layout`. Pipeio functions already accept a `root` param — extend the ones that do discovery to also accept an optional `pipelines_dir: Path | None` parameter.
- **Pipeio standalone:** When pipeio runs without projio (e.g., `pipeio` CLI), it keeps its own discovery fallback. Layout centralization is a projio concern.
- **No Layout dependency in pipeio:** Pipeio does NOT import from projio. The projio MCP wrapper resolves paths and passes them down.

### 6. Migration plan

Discovery fallback stays as a **last resort** during migration. The resolution order becomes:

1. Explicit path from `Layout` (passed by caller)
2. Config key (e.g., `pipeio.pipelines_dir`)  
3. Filesystem discovery fallback (current behavior, emits deprecation warning)

This means existing projects keep working even if they haven't added `layout:` to config.

## Scope of changes

### Phase 1: Layout model + projio core (this branch)

| File | Change |
|---|---|
| `src/projio/config.py` | Add `Layout` dataclass, `load_layout()` |
| `src/projio/sync.py` | Use `layout.libraries` and `layout.utils` instead of hardcoded `code/lib`, `code/utils` |
| `src/projio/mcp/context.py` | Use `layout.skills`, `layout.notes`, `layout.docs` in `ecosystem_status()`, `_discover_skills()`, `_discover_workflow_prompts()` |
| `src/projio/init.py` | Scaffold `layout:` section in generated config.yml templates |
| `tests/` | Test `Layout` defaults, `from_config()`, override behavior |

### Phase 2: Pipeio integration (separate PR or continuation)

| File | Change |
|---|---|
| `packages/pipeio/src/pipeio/mcp.py` | Accept optional `pipelines_dir` in functions that currently discover |
| `packages/pipeio/src/pipeio/cli.py` | Accept optional `pipelines_dir` in `_cmd_flow_new` |
| `packages/pipeio/src/pipeio/docs.py` | Accept `docs_base` param instead of hardcoding `docs/pipelines` |
| `src/projio/mcp/pipeio.py` | Resolve `layout.pipelines` and pass to pipeio functions |

### Phase 3: Profile support (future)

- Profile templates (e.g., `standard`, `flat`) that set `layout:` values
- `projio init --profile flat` scaffolds `pipelines/` and `lib/` at root

## What this does NOT change

- **Subsystem config keys** like `notio.notes_dir` or `pipeio.pipelines_dir` are kept for now. They serve as subsystem-specific overrides. `Layout` provides the project-wide default; subsystem keys can still override if needed.
- **Pipeio's internal architecture** — no new imports from projio into pipeio.
- **Published docs paths** in MkDocs nav — these are output paths, not input layout.

## Risks

- **Submodule coordination:** Phase 2 touches pipeio (a datalad subdataset). Changes there need a submodule commit bump in projio.
- **Config drift:** If `layout.pipelines` and `pipeio.pipelines_dir` disagree, which wins? Answer: `layout.*` is the source of truth; subsystem keys override for backward compat during migration, with a deprecation warning.
- **Test coverage:** Discovery fallbacks are implicitly tested by existing tests. Need explicit tests for layout override paths.

## Acceptance criteria

- [ ] `Layout.from_config({})` returns all current defaults — zero behavior change for existing projects
- [ ] `Layout.from_config({"layout": {"pipelines": "pipelines"}})` overrides just that key
- [ ] `sync.py` reads `layout.libraries` / `layout.utils`
- [ ] `ecosystem_status()` reads `layout.notes` instead of hardcoding `docs/log`
- [ ] `_discover_skills()` reads `layout.skills`
- [ ] `_discover_workflow_prompts()` reads `layout.docs`
- [ ] Existing test suite passes without config changes (defaults match current paths)
