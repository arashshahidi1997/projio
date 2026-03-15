# Package Integration

Analysis of how each ecosystem package determines its root directory and what changes are required to support the managed workspace layout (`.projio/<package>/`).

## Current state by package

### biblio

**Root detection**: automatic, in `biblio/paths.py:find_repo_root()`.
Walks up from a start directory looking for `bib/config/biblio.yml`, then `.git` or `pyproject.toml`.

**State directory**: none. Biblio uses a visible `bib/` directory tree (`bib/config/`, `bib/articles/`, `bib/derivatives/`). There is no hidden `.biblio/` folder.

**Config file**: `bib/config/biblio.yml`, loaded by `biblio/config.py:load_biblio_config()`.

**Projio awareness**: none. Biblio has no knowledge of `.projio/`.

**Impact assessment**: low friction. Since biblio already uses a visible directory (`bib/`), its data does not contribute to hidden-folder sprawl. The managed layout would provide `.projio/biblio/` for any future state that should be hidden (caches, indexes). The main config and article tree can remain at `bib/` — projio would only need to point `config.yml` at the right location.

**Required changes**:

1. Add a resolution step in `find_repo_root()` that checks `.projio/packages.yml` for a biblio entry
2. Allow `load_biblio_config()` to accept a root override from the registry path
3. No changes to the `bib/` directory structure — it remains user-facing content

### notio

**Root detection**: explicit `--root` argument (defaults to `.`), in `notio/cli.py`.

**State directory**: `.notio/templates/` for note templates. Created by `notio/core.py:ensure_default_templates()`.

**Config file**: `notio.toml` or `[tool.notio]` in `pyproject.toml`, loaded by `notio/config.py:load_config()`.

**Projio awareness**: none. Notio reads `NOTIO_ROOT` env var for MCP server context.

**Impact assessment**: moderate. The `.notio/` directory is the main source of hidden-folder sprawl from this package. Template storage should move to `.projio/notio/templates/` in managed mode.

**Required changes**:

1. In `load_config()`, add a check for `.projio/packages.yml` to determine managed mode
2. In managed mode, resolve `template_root` relative to `.projio/notio/` instead of `.notio/`
3. `ensure_default_templates()` must respect the resolved template root
4. `NOTIO_ROOT` continues to work as an explicit override

### codio

**Root detection**: automatic, in `codio/paths.py:find_project_root()`.
Walks up looking for `.codio/catalog.yml`, then `.projio/config.yml`, then `.git`/`pyproject.toml`.

**State directory**: `.codio/` containing `catalog.yml` and `profiles.yml`.

**Config file**: reads `.projio/config.yml` section `codio:` if present, otherwise uses defaults from `.codio/`.

**Projio awareness**: yes — codio already reads `.projio/config.yml` and uses `.projio/` as a root detection signal.

**Impact assessment**: low. Codio is the most projio-aware package. It already supports path overrides via `.projio/config.yml`. The transition to `.projio/codio/` mainly requires changing default paths in the config.

**Required changes**:

1. In `find_project_root()`, also check `.projio/packages.yml` for a codio entry
2. In `load_config()`, when managed mode is detected, default `catalog_path` and `profiles_path` to `.projio/codio/catalog.yml` and `.projio/codio/profiles.yml`
3. Keep the existing `.projio/config.yml` override mechanism as a fallback

### indexio

**Root detection**: explicit `--root` argument (defaults to `.`), in `indexio/cli.py`.

**State directory**: `.indexio/` containing `config.yaml` (the main config file).

**Config file**: `.indexio/config.yaml`, loaded by `indexio/config.py:load_indexio_config()`. Supports `includes:` for config composition.

**Projio awareness**: indirect. Indexio does not read `.projio/` itself, but projio's config points to indexio's config path and persist directory.

**Impact assessment**: moderate. The `.indexio/` directory is user-visible in every indexed project. In managed mode, config should live at `.projio/indexio/config.yaml` and the persist directory (chroma DB) should move to `.projio/cache/index/`.

**Required changes**:

1. Add a utility function that checks `.projio/packages.yml` for an indexio entry
2. When managed mode is detected, resolve config path relative to `.projio/indexio/`
3. The persist directory is already configurable — projio just needs to set it to `.projio/cache/index/` in the generated config
4. `--root` argument continues to work as an explicit override

## Shared integration pattern

All four packages need the same resolution logic. Rather than duplicating code, we should provide a **shared utility** — either a tiny standalone module or a convention that each package implements.

### Proposed resolution function

```python
def resolve_component_root(
    package_name: str,
    start: Path | None = None,
) -> Path | None:
    """Return the managed component path if inside a projio workspace."""
    root = _find_projio_root(start or Path.cwd())
    if root is None:
        return None
    registry = root / ".projio" / "packages.yml"
    if not registry.exists():
        return None
    data = yaml.safe_load(registry.read_text())
    entry = data.get("packages", {}).get(package_name, {})
    if entry.get("enabled") and "path" in entry:
        return root / entry["path"]
    return None
```

This function:

- Returns `None` if not in a projio workspace (package uses standalone mode)
- Returns the component path if the package is registered and enabled
- Has no dependency on projio — it only reads a YAML file

Each package can vendor this ~15-line function or import it from a shared `projio-common` micro-package.

## Compatibility strategy

### Dual-mode support

Packages must not break when switching between standalone and managed mode. The recommended approach:

1. Check for managed mode first (`.projio/packages.yml`)
2. Fall back to standalone mode (own hidden directory)
3. Accept explicit overrides (`--root`, env vars, config fields) that take highest priority

### Migration

Existing projects with standalone directories (`.codio/`, `.indexio/`, etc.) continue to work. `projio add <package>` could offer to migrate state from the standalone directory to the managed location:

```
$ projio add codio
Found existing .codio/ directory.
Migrate to .projio/codio/? [y/N]
```

### No breaking changes

The managed layout is purely additive. No package should remove support for its standalone directory. Standalone mode remains the default when projio is not present.

## Summary

| Package | Hidden dir | Projio aware | Change effort | Key change |
|---------|-----------|-------------|--------------|------------|
| biblio | none (`bib/`) | no | low | Add registry check to `find_repo_root()` |
| notio | `.notio/` | no | moderate | Redirect template root in managed mode |
| codio | `.codio/` | yes | low | Update default paths when registry present |
| indexio | `.indexio/` | indirect | moderate | Add registry check, redirect config path |
