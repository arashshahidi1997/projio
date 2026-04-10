---
name: projio-setup
description: "Guide agent through setting up or fixing projio ecosystem configuration for a project"
tools: [project_context, runtime_conventions, ecosystem_status, projio_init]
---

# Projio Setup

Use this skill when setting up projio for a new project or diagnosing/fixing
a broken configuration. Covers environment resolution, subsystem activation,
site builds, and sync.

## 1) Assess current state

```
project_context()
ecosystem_status()
runtime_conventions()
```

Check what's configured, what's missing, what's broken. Key signals:
- `ecosystem_status` reports subsystem health and missing deps
- `runtime_conventions` shows Makefile variables and their resolved values
- `project_context` shows project kind, enabled packages, config paths

## 2) Environment resolution

This is the most common source of breakage. projio needs to know which
conda env runs each tool.

### Preferred: `code.envs` in `.projio/config.yml`

```yaml
code:
  conda_prefix: /path/to/anaconda3    # conda installation root
  envs:
    default: myenv      # PYTHON — project code (snakemake, analysis scripts)
    projio: projio      # PROJIO, NOTIO — projio CLI + MCP server
    docs: projio        # MKDOCS — site builds
    datalad: labpy      # DATALAD, PANDOC — datalad + pandoc binary
```

**Fallback rules:**
- `projio` falls back to `docs` (both need projio + mkdocs)
- `docs` falls back to `projio`
- If neither is set, PROJIO/MKDOCS use the `default` env — usually wrong

**To find conda_prefix:** look for the anaconda/miniconda installation:
```bash
conda info --base
```

**To verify an env has projio:**
```bash
/path/to/anaconda3/envs/myenv/bin/python -c "import projio; print('ok')"
```

**To verify mkdocs is available:**
```bash
/path/to/anaconda3/envs/myenv/bin/python -m mkdocs --version
```

### Legacy: `runtime.*` in `~/.config/projio/config.yml`

```yaml
runtime:
  projio_python: /path/to/env/bin/python    # PROJIO + NOTIO
  docs_python: /path/to/env/bin/python      # MKDOCS (falls back to projio_python)
  datalad_bin: /path/to/env/bin/datalad     # DATALAD + PANDOC
```

Legacy keys work but `code.envs` is preferred — it's per-project and
more explicit.

### Diagnosing wrong env

Symptom: `make site-build` fails with missing plugin/package errors.

Check what `projio.mk` resolved:
```bash
head -10 .projio/projio.mk
```

If PROJIO or MKDOCS point to the wrong env:
1. Check `.projio/config.yml` for `code.envs`
2. If missing, add the `code:` block above
3. Run `projio sync` to regenerate `projio.mk`
4. Verify with `head -10 .projio/projio.mk`

## 3) Subsystem activation

Each subsystem is optional. Activate with:

```
projio add biblio    # bibliography management
projio add notio     # notes + manuscripts
projio add codio     # code library registry
projio add indexio   # semantic search
```

Or set `enabled: true` in `.projio/config.yml`:

```yaml
biblio:
  enabled: true
  config: .projio/biblio/biblio.yml

notio:
  enabled: true
  notes_dir: docs/log/

codio:
  enabled: true

pipeio:
  enabled: true
  pipelines_dir: code/pipelines
```

pipeio and figio are detected automatically from directory structure.

## 4) Site configuration

```yaml
site:
  framework: mkdocs       # mkdocs | sphinx | vite (auto-detected if omitted)
  base_port: 8000
  mkdocs:
    config_file: mkdocs.yml
    site_dir: site
```

Framework is auto-detected from `mkdocs.yml`, `docs/conf.py`, or
`package.json`. Only set explicitly when detection fails.

## 5) Run sync

After any config change:

```bash
projio sync
```

This regenerates `projio.mk`, wires mkdocs plugins, generates
sub-`mkdocs.yml` files for monorepo, syncs agent configs, and
optionally rebuilds the search index.

## 6) Verify

```
ecosystem_status()
```

All subsystems should show healthy. Then test:

```bash
make site-build     # or: projio site build
```

## Hard rules

- Never guess conda env names — ask the user or inspect `conda info --base`
- Always run `projio sync` after editing `.projio/config.yml`
- Never edit `projio.mk` by hand — it's regenerated on every sync
- If `code.envs` and `runtime.*` both exist, `code.envs` takes precedence
- The `default` env is for project code, not for projio — don't install
  projio/mkdocs there unless it's a single-env setup
