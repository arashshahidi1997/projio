"""MCP tools: pipeio pipeline management, notebook lifecycle, Snakemake execution."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict, resolve_makefile_vars
from .context import _expand


def _resolve_project_python() -> str | None:
    """Resolve the project PYTHON binary.

    Checks ``code.envs.default`` in config first, then falls back to
    Makefile/projio.mk variables.  Returns ``None`` when no override is
    configured.
    """
    from projio.config import resolve_env_python

    root = get_project_root()
    env_python = resolve_env_python(root, "default")
    if env_python:
        return env_python

    vars_ = resolve_makefile_vars()
    if "PYTHON" in vars_:
        return _expand(vars_["PYTHON"], vars_)
    return None


def _resolve_snakemake_cmd(use_conda: str = "") -> list[str]:
    """Resolve the snakemake command with conda wrapping if needed.

    Checks (in order):
    1. Explicit ``use_conda`` env name (e.g. ``"cogpy"``)
    2. ``SNAKEMAKE`` Makefile variable
    3. ``snakemake`` on PATH (with conda wrapping if in a conda env)
    4. Known fallback: ``cogpy`` conda env
    5. Bare ``["snakemake"]``

    Args:
        use_conda: Force a specific conda environment name.
    """
    import shlex
    import shutil

    from .datalad import _conda_wrap

    # 1. Explicit conda env override
    if use_conda:
        return _conda_run_cmd(use_conda, "snakemake")

    # 2. Makefile variable
    vars_ = resolve_makefile_vars()
    if "SNAKEMAKE" in vars_:
        expanded = _expand(vars_["SNAKEMAKE"], vars_)
        tokens = shlex.split(expanded)
        if len(tokens) > 1:
            return tokens
        wrapped = _conda_wrap(tokens[0])
        if wrapped:
            return wrapped
        return tokens

    # 3. On PATH
    binary = shutil.which("snakemake")
    if binary:
        wrapped = _conda_wrap(binary)
        if wrapped:
            return wrapped
        return [binary]

    # 4. Known fallback: cogpy conda env
    cmd = _conda_run_cmd("cogpy", "snakemake")
    if cmd:
        return cmd

    # 5. Bare fallback
    return ["snakemake"]


def _conda_run_cmd(env_name: str, cmd_name: str) -> list[str]:
    """Build a ``conda run -n <env> <cmd>`` token list.

    Finds the conda binary by checking common Anaconda installation paths.
    Returns bare ``[cmd_name]`` if conda cannot be found.
    """
    from pathlib import Path

    # Find conda binary from known locations
    for base in ("/storage/share/python/environments/Anaconda3",):
        for rel in ("condabin/conda", "bin/conda"):
            conda = Path(base) / rel
            if conda.is_file():
                return [str(conda), "run", "-n", env_name, cmd_name]

    # Try conda on PATH
    import shutil
    conda_bin = shutil.which("conda")
    if conda_bin:
        return [conda_bin, "run", "-n", env_name, cmd_name]

    return [cmd_name]


def _pipeio_available() -> bool:
    try:
        import pipeio  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the pipeio package. Install with: pip install pipeio"}


def pipeio_flow_list(prefix: str | None = None) -> JsonDict:
    """List registered flows, optionally filtered by name prefix.

    Args:
        prefix: Filter by flow name prefix (e.g. 'preprocess', 'brainstate').
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_list")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_list  # type: ignore[import]
        return json_dict(mcp_flow_list(root, prefix=prefix))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_flow_status(flow: str) -> JsonDict:
    """Show status of a specific flow.

    Args:
        flow: Flow name.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_status")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_status  # type: ignore[import]
        return json_dict(mcp_flow_status(root, flow=flow))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_flow_fork(
    flow: str,
    new_flow: str,
) -> JsonDict:
    """Fork a flow: copy its code directory and register as a new flow.

    Creates a full copy of the source flow's code (Snakefile, config,
    notebooks, scripts) under a new name. The original is untouched.

    Args:
        flow: Source flow name.
        new_flow: Name for the forked flow.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_fork")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_fork  # type: ignore[import]
        return json_dict(mcp_flow_fork(
            root, flow=flow, new_flow=new_flow,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_flow_deregister(flow: str) -> JsonDict:
    """Remove a flow from the registry.

    Only removes the registry entry — does NOT delete code, config, docs,
    or notebook files from the filesystem. Use pipeio_registry_scan() to
    re-register if needed.

    Args:
        flow: Flow name.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_deregister")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_deregister  # type: ignore[import]
        return json_dict(mcp_flow_deregister(root, flow=flow))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_flow_new(flow: str) -> JsonDict:
    """Scaffold a new pipeline flow with standard directory structure.

    Creates the full flow scaffold under ``code/pipelines/<flow>/``:
    Snakefile, config.yml, publish.yml, Makefile, scripts/, rules/,
    docs/index.md, and notebook workspaces (explore + demo).

    Idempotent: only writes missing files, so it can augment an
    existing flow without overwriting.

    Args:
        flow: Flow name (lowercase slug with underscores).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_new")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_new  # type: ignore[import]
        return json_dict(mcp_flow_new(root, flow=flow))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_status(
    flow: str = "",
    name: str = "",
) -> JsonDict:
    """Show notebook sync and publication status.

    Optionally filter by flow or notebook name to avoid scanning
    the entire project.

    Args:
        flow: Filter to a specific flow (optional).
        name: Filter to a specific notebook name (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_status")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_status  # type: ignore[import]
        return json_dict(mcp_nb_status(
            root,
            flow=flow or None,
            name=name or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_update(
    flow: str,
    name: str,
    status: str = "",
    description: str = "",
    kind: str = "",
    mod: str = "",
    kernel: str = "",
) -> JsonDict:
    """Update notebook metadata in notebook.yml.

    Args:
        flow: Flow name.
        name: Notebook name (stem, without extension).
        status: New status (draft/active/stale/promoted/archived).
        description: New one-line description.
        kind: New kind (investigate/explore/demo/validate).
        mod: Associated mod name.
        kernel: Jupyter kernel name.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_update")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_update  # type: ignore[import]
        return json_dict(mcp_nb_update(
            root, flow=flow, name=name,
            status=status or None,
            description=description or None,
            kind=kind or None,
            mod=mod or None,
            kernel=kernel or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_list(flow: str = "") -> JsonDict:
    """List mods for a specific flow.

    Args:
        flow: Flow name (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_list")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_list  # type: ignore[import]
        return json_dict(mcp_mod_list(root, flow=flow or None))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_resolve(modkeys: list[str]) -> JsonDict:
    """Resolve modkeys (flow-X_mod-Y) into metadata and doc locations.

    Args:
        modkeys: List of modkey strings to resolve.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_resolve")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_resolve  # type: ignore[import]
        return json_dict(mcp_mod_resolve(root, modkeys=modkeys))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_context(flow: str = "", mod: str = "") -> JsonDict:
    """Bundled read context for a mod: rules, scripts, doc, config params.

    Returns everything needed to understand and work on a mod in one call.

    Args:
        flow: Flow name (optional).
        mod: Module name.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_context")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_context  # type: ignore[import]
        return json_dict(mcp_mod_context(root, flow=flow or None, mod=mod))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_registry_scan() -> JsonDict:
    """Scan the filesystem for pipelines and rebuild the registry.

    Discovers pipes, flows, and mods from the pipelines directory
    (code/pipelines/ or pipelines/) and writes a fresh registry.yml.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_registry_scan")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_registry_scan  # type: ignore[import]
        return json_dict(mcp_registry_scan(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_modkey_bib(
    output_path: str = "",
    project_name: str = "",
) -> JsonDict:
    """Generate a BibTeX file with @misc entries for all registered pipeline mods.

    Each mod gets a citekey ``flow-X_mod-Y`` for use in manuscripts
    (e.g. ``[@flow-ieeg_mod-badlabel]``).

    Args:
        output_path: Where to write the .bib file (relative to project root).
                     Default: .projio/pipeio/modkey.bib.
        project_name: Author/project name for bib entries. Default: project dir name.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_modkey_bib")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_modkey_bib  # type: ignore[import]
        return json_dict(mcp_modkey_bib(
            root,
            output_path=output_path or None,
            project_name=project_name or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_docs_collect() -> JsonDict:
    """Collect flow-local docs and notebook outputs into docs/pipelines/.

    Copies hand-written docs from each flow's docs/ directory and publishes
    notebooks into the MkDocs site structure.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_docs_collect")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_docs_collect  # type: ignore[import]
        return json_dict(mcp_docs_collect(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_docs_nav() -> JsonDict:
    """Generate MkDocs nav YAML fragment for collected pipeline docs."""
    if not _pipeio_available():
        return _unavailable("pipeio_docs_nav")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_docs_nav  # type: ignore[import]
        return json_dict(mcp_docs_nav(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_contracts_validate() -> JsonDict:
    """Validate I/O contracts for all flows (config completeness, dirs, groups)."""
    if not _pipeio_available():
        return _unavailable("pipeio_contracts_validate")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_contracts_validate  # type: ignore[import]
        return json_dict(mcp_contracts_validate(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_create(
    flow: str,
    name: str,
    kind: str = "investigate",
    description: str = "",
) -> JsonDict:
    """Scaffold a new notebook for a flow.

    Creates a percent-format .py script with bootstrap cells and registers
    it in notebook.yml.

    Args:
        flow: Flow name.
        name: Notebook name (e.g. 'investigate_noise').
        kind: Prefix convention (investigate, explore, demo).
        description: One-line purpose for the notebook header.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_create")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_create  # type: ignore[import]
        return json_dict(mcp_nb_create(
            root, flow=flow, name=name,
            kind=kind, description=description,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_sync(
    flow: str,
    name: str,
    formats: list[str] | None = None,
    direction: str = "py2nb",
    force: bool = False,
) -> JsonDict:
    """Sync a specific notebook via jupytext (pair + convert).

    Supports bidirectional sync:
    - direction='py2nb' (default): regenerate .ipynb/.md from .py source.
      Use after the agent edits the .py file.
    - direction='nb2py': update .py from the paired .ipynb.
      Use after a human edits the .ipynb interactively.

    Skips files that are already up-to-date (mtime check) unless force=True.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
        formats: Which formats to produce (default: ['ipynb', 'myst']).
            Only used for py2nb direction.
        direction: 'py2nb' or 'nb2py'.
        force: If True, sync even if files are up-to-date.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_sync")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_sync  # type: ignore[import]
        python_bin = _resolve_project_python()
        return json_dict(mcp_nb_sync(
            root, flow=flow, name=name, formats=formats,
            python_bin=python_bin, direction=direction, force=force,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_sync_flow(
    flow: str,
    direction: str = "py2nb",
    force: bool = False,
) -> JsonDict:
    """Batch-sync all notebooks in a flow.

    Args:
        flow: Flow name.
        direction: 'py2nb' or 'nb2py'.
        force: If True, sync even if up-to-date.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_sync_flow")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_sync_flow  # type: ignore[import]
        python_bin = _resolve_project_python()
        return json_dict(mcp_nb_sync_flow(
            root, flow=flow,
            direction=direction, force=force,
            python_bin=python_bin,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_publish(flow: str, name: str, format: str = "") -> JsonDict:
    """Publish a notebook to docs/pipelines/<flow>/notebooks/.

    Publishes MyST markdown and/or HTML based on notebook.yml settings.
    Pass format='html' to force HTML output (for demo notebooks),
    or format='myst' for markdown only.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
        format: Force format ('myst', 'html', or '' for auto from notebook.yml).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_publish")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_publish  # type: ignore[import]
        return json_dict(mcp_nb_publish(
            root, flow=flow, name=name, format=format,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_analyze(flow: str, name: str) -> JsonDict:
    """Analyze a notebook's static structure.

    Parses the percent-format .py notebook and returns structured metadata:
    imports, RunCard @dataclass fields, PipelineContext usage, section headers,
    and cogpy function calls.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_analyze")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_analyze  # type: ignore[import]
        return json_dict(mcp_nb_analyze(root, flow=flow, name=name))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_diff(flow: str, name: str) -> JsonDict:
    """Show sync state between .py and paired .ipynb for a notebook.

    Returns which file is newer, whether they're in sync, and the
    recommended sync direction. Call this before nb_sync to decide
    the right direction, or to check if human edits need to be
    pulled into the .py source.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_diff")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_diff  # type: ignore[import]
        return json_dict(mcp_nb_diff(root, flow=flow, name=name))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_lab(
    flow: str = "",
    sync: bool = False,
) -> JsonDict:
    """Build/refresh the Jupyter Lab symlink manifest.

    Creates .projio/pipeio/lab/<flow>/<name>.ipynb symlinks
    pointing to real notebook files. Optionally syncs py→ipynb first.
    Returns manifest state: linked notebooks, stale cleaned, lab_dir.

    Args:
        flow: Filter to a specific flow (optional).
        sync: If True, sync py→ipynb before linking (default False).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_lab")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_lab  # type: ignore[import]
        python_bin = _resolve_project_python()
        return json_dict(mcp_nb_lab(
            root, flow=flow or None,
            sync=sync, python_bin=python_bin,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_scan(register: bool = False) -> JsonDict:
    """Scan for percent-format .py notebooks and compare against notebook.yml.

    Discovers .py files with # %% cell markers in notebooks/ directories
    and reports which are registered vs unregistered.

    Args:
        register: If True, auto-register unregistered notebooks into
            notebook.yml with defaults (pair_ipynb=True, status=draft).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_scan")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_scan  # type: ignore[import]
        return json_dict(mcp_nb_scan(root, register=register))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_read(flow: str, name: str) -> JsonDict:
    """Read a notebook's .py content with metadata, sync state, and analysis.

    Returns the full .py source alongside status, kernel, mod, description,
    structural analysis (sections, imports, RunCard), and sync state — all
    in a single call.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_read")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_read  # type: ignore[import]
        return json_dict(mcp_nb_read(root, flow=flow, name=name))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_audit() -> JsonDict:
    """Audit all notebooks: staleness, config completeness, mod coverage.

    Returns per-notebook issues (missing description, stale ipynb, no kernel,
    no mod, draft-but-substantial) and flow-level mod coverage gaps.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_audit")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_audit  # type: ignore[import]
        return json_dict(mcp_nb_audit(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_pipeline(
    flow: str,
    name: str,
    formats: list[str] | None = None,
    build_site: bool = False,
) -> JsonDict:
    """Composite notebook publish: sync → publish → docs_collect → docs_nav.

    Runs the full notebook-to-docs pipeline in one call.  Optionally triggers
    a site build at the end.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
        formats: Jupytext formats to produce (default: ['ipynb', 'myst']).
        build_site: If True, run site_build after docs collection.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_pipeline")

    steps: dict[str, JsonDict] = {}

    # Step 1: nb_sync
    result = pipeio_nb_sync(flow=flow, name=name, formats=formats)
    steps["nb_sync"] = result
    if "error" in result:
        return json_dict({"steps": steps, "completed": False, "failed_at": "nb_sync"})

    # Step 2: nb_publish
    result = pipeio_nb_publish(flow=flow, name=name)
    steps["nb_publish"] = result
    if "error" in result:
        return json_dict({"steps": steps, "completed": False, "failed_at": "nb_publish"})

    # Step 3: docs_collect
    result = pipeio_docs_collect()
    steps["docs_collect"] = result
    if "error" in result:
        return json_dict({"steps": steps, "completed": False, "failed_at": "docs_collect"})

    # Step 4: docs_nav
    result = pipeio_docs_nav()
    steps["docs_nav"] = result
    if "error" in result:
        return json_dict({"steps": steps, "completed": False, "failed_at": "docs_nav"})

    # Optional Step 5: site_build
    if build_site:
        from .site import site_build
        result = site_build()
        steps["site_build"] = result
        if "error" in result:
            return json_dict({"steps": steps, "completed": False, "failed_at": "site_build"})

    return json_dict({"steps": steps, "completed": True})


def pipeio_mkdocs_nav_patch() -> JsonDict:
    """Update the pipeio docs nav for mkdocs.

    Writes ``docs/pipelines/mkdocs.yml`` (the monorepo sub-nav file).
    The root ``mkdocs.yml`` includes it via ``!include``, set up by
    ``projio sync``.  If the ``!include`` is missing, runs sync to add it.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mkdocs_nav_patch")

    root = get_project_root()

    # Write the sub-mkdocs.yml via docs_nav
    try:
        from pipeio.mcp import mcp_docs_nav
        nav_result = mcp_docs_nav(root, write=True)
    except Exception as exc:
        return json_dict({"error": f"docs_nav failed: {exc}"})

    if not nav_result.get("written"):
        return json_dict({"error": "No pipeline docs to write (docs/pipelines/ empty or missing)"})

    # Ensure root mkdocs.yml has monorepo + !include
    try:
        from projio.sync import _sync_mkdocs_monorepo
        sync_result = _sync_mkdocs_monorepo(root)
    except Exception:
        sync_result = {"action": "skipped", "reason": "sync unavailable"}

    return json_dict({
        "written": True,
        "sub_mkdocs": nav_result.get("sub_mkdocs"),
        "mkdocs_sync": sync_result.get("action", "unknown"),
    })


def pipeio_rule_list(flow: str = "") -> JsonDict:
    """List rules for a flow with input/output signatures and mod membership.

    Parses the flow's Snakefile (and any .smk includes) and returns
    structured metadata for each rule: name, input/output/params dicts,
    script path, and which mod the rule belongs to.

    Args:
        flow: Flow name (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_rule_list")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_rule_list  # type: ignore[import]
        return json_dict(mcp_rule_list(root, flow=flow or None))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_rule_stub(
    flow: str = "",
    rule_name: str = "",
    inputs: dict | None = None,
    outputs: dict | None = None,
    params: dict | None = None,
    script: str = "",
) -> JsonDict:
    """Generate a syntactically correct Snakemake rule stub from a contract spec.

    Returns formatted rule text for human review — does NOT auto-insert into
    the Snakefile.

    Args:
        flow: Flow name (optional).
        rule_name: Name for the new rule.
        inputs: ``{name: bids_pattern}`` or ``{name: {source_rule, member}}``.
        outputs: ``{name: bids_kwargs_dict}`` or ``{name: bids_pattern_str}``.
        params: ``{name: config_dot_path}`` e.g. ``{"ttl_freq": "ttl_removal.ttl_freq"}``.
        script: Relative path to the script file.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_rule_stub")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_rule_stub  # type: ignore[import]
        return json_dict(mcp_rule_stub(
            root,
            flow=flow or None,
            rule_name=rule_name,
            inputs=inputs,
            outputs=outputs,
            params=params,
            script=script or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_rule_insert(
    flow: str = "",
    rule_name: str = "",
    rule_text: str = "",
    target_file: str = "",
    after_rule: str = "",
    inputs: dict | None = None,
    outputs: dict | None = None,
    params: dict | None = None,
    script: str = "",
) -> JsonDict:
    """Insert a Snakemake rule into the correct .smk or Snakefile.

    Provide either ``rule_text`` directly or ``inputs``/``outputs``/``params``/
    ``script`` to generate the rule (same spec as rule_stub).

    Args:
        flow: Flow name (optional).
        rule_name: Name for the rule.
        rule_text: Pre-formatted rule text (optional — generated if omitted).
        target_file: Which .smk/Snakefile to insert into (auto-selected if omitted).
        after_rule: Insert after this rule name (appends at end if omitted).
        inputs: ``{name: bids_pattern}`` (for generation).
        outputs: ``{name: bids_kwargs_dict}`` (for generation).
        params: ``{name: config_dot_path}`` (for generation).
        script: Relative path to script file (for generation).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_rule_insert")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_rule_insert  # type: ignore[import]
        return json_dict(mcp_rule_insert(
            root,
            flow=flow or None,
            rule_name=rule_name,
            rule_text=rule_text or None,
            target_file=target_file or None,
            after_rule=after_rule or None,
            inputs=inputs,
            outputs=outputs,
            params=params,
            script=script or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_rule_update(
    flow: str = "",
    rule_name: str = "",
    add_inputs: dict | None = None,
    add_outputs: dict | None = None,
    add_params: dict | None = None,
    set_script: str = "",
    apply: bool = False,
) -> JsonDict:
    """Patch an existing Snakemake rule by merging new sections.

    Adds new entries to input/output/params without overwriting existing ones.
    Returns a unified diff preview by default; set ``apply=True`` to write.

    Args:
        flow: Flow name (optional).
        rule_name: Name of the existing rule to patch.
        add_inputs: ``{name: spec}`` entries to add to input.
        add_outputs: ``{name: spec}`` entries to add to output.
        add_params: ``{name: config_dot_path}`` entries to add to params.
        set_script: New script path (replaces existing).
        apply: Write the patched file (default False).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_rule_update")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_rule_update  # type: ignore[import]
        return json_dict(mcp_rule_update(
            root,
            flow=flow or None,
            rule_name=rule_name,
            add_inputs=add_inputs,
            add_outputs=add_outputs,
            add_params=add_params,
            set_script=set_script or None,
            apply=apply,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_config_read(flow: str = "") -> JsonDict:
    """Read and parse a flow's config.yml with bids() signature resolution.

    Args:
        flow: Flow name (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_config_read")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_config_read  # type: ignore[import]
        return json_dict(mcp_config_read(root, flow=flow or None))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_config_patch(
    flow: str = "",
    registry_entry: dict | None = None,
    params_entry: dict | None = None,
    apply: bool = False,
) -> JsonDict:
    """Validate and optionally patch a flow's config.yml.

    Validates ``registry_entry`` against the snakebids schema (base_input,
    member suffix/extension) and returns a unified diff for review.
    Pass ``apply=True`` to write the patched file.

    Args:
        flow: Flow name (optional).
        registry_entry: ``{group_name: group_dict}`` to add/replace in ``registry:``.
        params_entry: ``{section: {key: value}}`` to update in top-level params.
        apply: Write the patch to disk (default False — diff preview only).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_config_patch")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_config_patch  # type: ignore[import]
        return json_dict(mcp_config_patch(
            root,
            flow=flow or None,
            registry_entry=registry_entry,
            params_entry=params_entry,
            apply=apply,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_config_init(
    flow: str = "",
    input_dir: str = "",
    output_dir: str = "",
    pybids_inputs: dict | None = None,
    registry_groups: dict | None = None,
    params: dict | None = None,
) -> JsonDict:
    """Scaffold a new flow's config.yml with pybids_inputs and registry structure.

    Creates a well-structured config.yml for a flow that doesn't have one yet.
    Use ``config_patch`` to modify an existing config.

    Args:
        flow: Flow name (optional).
        input_dir: Path to input data (relative to project root).
        output_dir: Path to output derivatives (relative to project root).
        pybids_inputs: Workflow-engine input spec (passed through to config).
        registry_groups: ``{group_name: group_dict}`` for the output registry.
        params: Additional top-level config parameters.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_config_init")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_config_init  # type: ignore[import]
        return json_dict(mcp_config_init(
            root,
            flow=flow or None,
            input_dir=input_dir,
            output_dir=output_dir,
            pybids_inputs=pybids_inputs,
            registry_groups=registry_groups,
            params=params,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_registry_validate() -> JsonDict:
    """Validate pipeline registry consistency (code vs docs, config schema)."""
    if not _pipeio_available():
        return _unavailable("pipeio_registry_validate")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_registry_validate  # type: ignore[import]
        return json_dict(mcp_registry_validate(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_create(
    flow: str,
    mod: str,
    description: str = "",
    from_notebook: str | None = None,
    inputs: dict | None = None,
    outputs: dict | None = None,
    params_spec: dict | None = None,
    use_pipeline_context: bool = False,
) -> JsonDict:
    """Scaffold a new mod (script skeleton + doc stub).

    When ``inputs``/``outputs``/``params_spec`` are provided, generates a
    script with Snakemake I/O unpacking and parameter binding so only the
    processing logic needs to be filled in.

    Args:
        flow: Flow name.
        mod: Mod name (lowercase, underscore-separated).
        description: One-line purpose for the mod.
        from_notebook: Notebook name to seed imports from (optional).
        inputs: ``{var_name: description}`` for snakemake.input unpacking.
        outputs: ``{var_name: description}`` for snakemake.output unpacking.
        params_spec: ``{var_name: description}`` for snakemake.params unpacking.
        use_pipeline_context: Generate PipelineContext setup boilerplate.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_create")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_create  # type: ignore[import]
        return json_dict(mcp_mod_create(
            root, flow=flow, mod=mod,
            description=description, from_notebook=from_notebook,
            inputs=inputs, outputs=outputs,
            params_spec=params_spec,
            use_pipeline_context=use_pipeline_context,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_exec(
    flow: str,
    name: str,
    params: dict | None = None,
    timeout: int = 600,
) -> JsonDict:
    """Execute a notebook via papermill with optional parameter overrides.

    Both jupytext (sync) and papermill (orchestration) run from the MCP
    server's own ``sys.executable``.  Cell execution is delegated to the
    Jupyter kernel specified in ``notebook.yml`` via the ``-k`` flag.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
        params: RunCard parameter overrides (optional).
        timeout: Cell execution timeout in seconds (default 600).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_exec")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_exec  # type: ignore[import]
        return json_dict(mcp_nb_exec(
            root, flow=flow, name=name,
            params=params, timeout=timeout,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_audit(
    flow: str = "",
    mod: str = "",
) -> JsonDict:
    """Audit a mod's health: contract drift, doc/script existence, naming.

    Returns structured findings without modifying anything. Checks:
    script existence, contract drift, doc coverage, naming conventions,
    and registry consistency.

    Args:
        flow: Flow name.
        mod: Mod name (audits all mods if empty).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_audit")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_audit  # type: ignore[import]
        return json_dict(mcp_mod_audit(root, flow=flow or None, mod=mod))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_doc_refresh(
    flow: str,
    mod: str,
    facet: str = "spec",
    apply: bool = False,
) -> JsonDict:
    """Regenerate a mod doc facet from current mod context.

    Generates an updated spec.md or theory.md skeleton from the mod's
    current rules, scripts, config params, and bids signatures.

    Args:
        flow: Flow name.
        mod: Mod name.
        facet: Which facet to refresh ('spec' or 'theory').
        apply: Write the refreshed doc to disk (default False — preview only).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_doc_refresh")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_doc_refresh  # type: ignore[import]
        return json_dict(mcp_mod_doc_refresh(
            root, flow=flow, mod=mod, facet=facet, apply=apply,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_script_create(
    flow: str,
    mod: str,
    script_name: str,
    description: str = "",
    inputs: dict | None = None,
    outputs: dict | None = None,
    params_spec: dict | None = None,
) -> JsonDict:
    """Create an additional script for an existing mod.

    Generates a Snakemake-compatible script template with I/O unpacking.
    Discovers the project's compute library via codio for imports.

    Args:
        flow: Flow name.
        mod: Mod name.
        script_name: Script filename (without .py).
        description: One-line purpose.
        inputs: {var_name: description} for snakemake.input.
        outputs: {var_name: description} for snakemake.output.
        params_spec: {var_name: description} for snakemake.params.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_script_create")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_script_create  # type: ignore[import]
        return json_dict(mcp_script_create(
            root, flow=flow, mod=mod, script_name=script_name,
            description=description, inputs=inputs, outputs=outputs,
            params_spec=params_spec,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_promote(
    flow: str,
    name: str,
    mod: str,
    rule_name: str = "",
    description: str = "",
    apply: bool = False,
) -> JsonDict:
    """Promote a notebook to a pipeline mod.

    Orchestrates: analyze notebook → generate script → rule stub → docs.
    By default only creates the script. Returns rule stub and next steps
    for review. Set apply=True to also create doc stubs.

    Args:
        flow: Flow name.
        name: Notebook basename (without extension).
        mod: Target mod name.
        rule_name: Rule name (default: same as mod).
        description: One-line purpose for the mod.
        apply: If True, also create doc stubs on disk.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_promote")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_promote  # type: ignore[import]
        return json_dict(mcp_nb_promote(
            root, flow=flow, name=name, mod=mod,
            rule_name=rule_name, description=description,
            apply=apply,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_dag_export(
    flow: str = "",
    graph_type: str = "rulegraph",
    output_format: str = "dot",
) -> JsonDict:
    """Export rule/job DAG via snakemake's native graph output.

    Args:
        flow: Flow name (optional).
        graph_type: rulegraph (compact), dag (full jobs), or d3dag (JSON).
        output_format: dot, mermaid, svg (requires graphviz), or json (d3dag only).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_dag_export")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_dag_export  # type: ignore[import]
        return json_dict(mcp_dag_export(
            root, flow=flow or None,
            graph_type=graph_type, output_format=output_format,
            snakemake_cmd=_resolve_snakemake_cmd(),
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_report(
    flow: str = "",
    output_path: str = "",
    target: str = "",
) -> JsonDict:
    """Generate a snakemake HTML report for a flow.

    Args:
        flow: Flow name (optional).
        output_path: Where to write the report (relative to root). Auto-generated if empty.
        target: Target rule to run before report (e.g. "report" for partial output flows).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_report")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_report  # type: ignore[import]
        return json_dict(mcp_report(
            root, flow=flow or None,
            output_path=output_path, target=target,
            snakemake_cmd=_resolve_snakemake_cmd(),
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_target_paths(
    flow: str = "",
    group: str = "",
    member: str = "",
    entities: dict[str, str] | None = None,
    expand: bool = False,
) -> JsonDict:
    """Resolve output paths for a flow's registry entries.

    Three modes:
    - No group: list available groups and members with path patterns.
    - group + member + entities: resolve a single concrete path.
    - expand=True: glob for all matching paths on disk, filtered by entities.

    Args:
        flow: Flow name (optional).
        group: Registry group name (e.g. "preproc").
        member: Registry member name (e.g. "cleaned").
        entities: Wildcard entities (e.g. {"sub": "01", "ses": "04"}).
        expand: If True, enumerate all matching paths on disk.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_target_paths")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_target_paths  # type: ignore[import]
        return json_dict(mcp_target_paths(
            root, flow=flow or None,
            group=group, member=member,
            entities=entities, expand=expand,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_completion(
    flow: str = "",
    mod: str = "",
) -> JsonDict:
    """Check session completion by comparing expected outputs against filesystem.

    Args:
        flow: Flow name (optional).
        mod: Filter to a specific mod (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_completion")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_completion  # type: ignore[import]
        return json_dict(mcp_completion(
            root, flow=flow or None, mod=mod or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_cross_flow(
    flow: str = "",
) -> JsonDict:
    """Map output_registry → input_registry chains across flows.

    Args:
        flow: Filter by flow name (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_cross_flow")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_cross_flow  # type: ignore[import]
        return json_dict(mcp_cross_flow(
            root, flow=flow or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_log_parse(
    flow: str = "",
    run_id: str = "",
    log_path: str = "",
) -> JsonDict:
    """Extract structured data from Snakemake log files.

    Args:
        flow: Flow name (optional).
        run_id: Specific run ID (optional).
        log_path: Direct path to a Snakemake log file (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_log_parse")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_log_parse  # type: ignore[import]
        return json_dict(mcp_log_parse(
            root, flow=flow or None,
            run_id=run_id or None, log_path=log_path or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_run(
    flow: str = "",
    targets: list[str] | None = None,
    cores: int = 1,
    dryrun: bool = False,
    use_conda: bool = False,
    extra_args: list[str] | None = None,
    wildcards: dict[str, str] | None = None,
) -> JsonDict:
    """Launch Snakemake in a detached screen session.

    Args:
        flow: Flow name (optional).
        targets: Snakemake target rules (optional).
        cores: Number of cores (default 1).
        dryrun: If True, do a dry run.
        use_conda: Pass --use-conda to snakemake (use conda envs defined in rules).
        extra_args: Additional Snakemake CLI arguments.
        wildcards: Entity filters for scoping runs (e.g. {"subject": "01", "session": "04"}).
            Maps to snakebids --filter-{key} {value} CLI flags.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_run")
    root = get_project_root()
    run_extra = list(extra_args or [])
    if use_conda:
        run_extra.append("--use-conda")
    try:
        from pipeio.mcp import mcp_run  # type: ignore[import]
        return json_dict(mcp_run(
            root, flow=flow or None,
            targets=targets, cores=cores, dryrun=dryrun,
            extra_args=run_extra or None,
            snakemake_cmd=_resolve_snakemake_cmd(),
            wildcards=wildcards,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_run_status(
    run_id: str = "",
    flow: str = "",
) -> JsonDict:
    """Query progress of running or recent Snakemake runs.

    Args:
        run_id: Specific run ID to query (optional).
        flow: Filter by flow (optional).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_run_status")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_run_status  # type: ignore[import]
        return json_dict(mcp_run_status(
            root, run_id=run_id or None, flow=flow or None,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_run_dashboard() -> JsonDict:
    """Rich summary of all tracked Snakemake runs across flows."""
    if not _pipeio_available():
        return _unavailable("pipeio_run_dashboard")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_run_dashboard  # type: ignore[import]
        return json_dict(mcp_run_dashboard(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_run_kill(run_id: str) -> JsonDict:
    """Gracefully stop a running Snakemake screen session.

    Args:
        run_id: Run ID to stop.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_run_kill")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_run_kill  # type: ignore[import]
        return json_dict(mcp_run_kill(root, run_id=run_id))
    except Exception as exc:
        return json_dict({"error": str(exc)})
