"""MCP tools: pipeio_flow_list, pipeio_flow_status, pipeio_nb_status, pipeio_mod_list, pipeio_mod_resolve, pipeio_registry_scan, pipeio_registry_validate, pipeio_docs_collect, pipeio_docs_nav, pipeio_contracts_validate."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict, resolve_makefile_vars
from .context import _expand


def _resolve_project_python() -> str | None:
    """Resolve the project PYTHON from Makefile/projio.mk variables.

    Returns ``None`` when no override is configured.
    """
    vars_ = resolve_makefile_vars()
    if "PYTHON" in vars_:
        return _expand(vars_["PYTHON"], vars_)
    return None


def _pipeio_available() -> bool:
    try:
        import pipeio  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the pipeio package. Install with: pip install pipeio"}


def pipeio_flow_list(pipe: str | None = None) -> JsonDict:
    """List pipeline flows, optionally filtered by pipe.

    Args:
        pipe: Filter by pipeline name (e.g. 'preprocess', 'brainstate').
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_list")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_list  # type: ignore[import]
        return json_dict(mcp_flow_list(root, pipe=pipe))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_flow_status(pipe: str, flow: str) -> JsonDict:
    """Show status of a specific pipeline flow.

    Args:
        pipe: Pipeline name.
        flow: Flow name.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_flow_status")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_flow_status  # type: ignore[import]
        return json_dict(mcp_flow_status(root, pipe=pipe, flow=flow))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_status() -> JsonDict:
    """Show notebook sync and publication status across all flows."""
    if not _pipeio_available():
        return _unavailable("pipeio_nb_status")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_status  # type: ignore[import]
        return json_dict(mcp_nb_status(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_list(pipe: str, flow: str = "") -> JsonDict:
    """List mods for a specific pipeline flow.

    Args:
        pipe: Pipeline name.
        flow: Flow name (optional for single-flow pipes).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mod_list")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_mod_list  # type: ignore[import]
        return json_dict(mcp_mod_list(root, pipe=pipe, flow=flow or None))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_mod_resolve(modkeys: list[str]) -> JsonDict:
    """Resolve modkeys (pipe-X_flow-Y_mod-Z) into metadata and doc locations.

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
    pipe: str,
    flow: str,
    name: str,
    kind: str = "investigate",
    description: str = "",
) -> JsonDict:
    """Scaffold a new notebook for a flow.

    Creates a percent-format .py script with bootstrap cells and registers
    it in notebook.yml.

    Args:
        pipe: Pipeline name.
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
            root, pipe=pipe, flow=flow, name=name,
            kind=kind, description=description,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_sync(
    pipe: str,
    flow: str,
    name: str,
    formats: list[str] | None = None,
) -> JsonDict:
    """Sync a specific notebook via jupytext (pair + convert).

    Args:
        pipe: Pipeline name.
        flow: Flow name.
        name: Notebook basename (without extension).
        formats: Which formats to produce (default: ['ipynb', 'myst']).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_sync")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_sync  # type: ignore[import]
        python_bin = _resolve_project_python()
        return json_dict(mcp_nb_sync(
            root, pipe=pipe, flow=flow, name=name, formats=formats,
            python_bin=python_bin,
        ))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_publish(pipe: str, flow: str, name: str) -> JsonDict:
    """Publish a notebook's myst markdown to the docs tree.

    Copies the .md file to docs/pipelines/<pipe>/<flow>/notebooks/nb-<name>.md.

    Args:
        pipe: Pipeline name.
        flow: Flow name.
        name: Notebook basename (without extension).
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_publish")
    root = get_project_root()
    try:
        from pipeio.mcp import mcp_nb_publish  # type: ignore[import]
        return json_dict(mcp_nb_publish(root, pipe=pipe, flow=flow, name=name))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def pipeio_nb_pipeline(
    pipe: str,
    flow: str,
    name: str,
    formats: list[str] | None = None,
    build_site: bool = False,
) -> JsonDict:
    """Composite notebook publish: sync → publish → docs_collect → docs_nav.

    Runs the full notebook-to-docs pipeline in one call.  Optionally triggers
    a site build at the end.

    Args:
        pipe: Pipeline name.
        flow: Flow name.
        name: Notebook basename (without extension).
        formats: Jupytext formats to produce (default: ['ipynb', 'myst']).
        build_site: If True, run site_build after docs collection.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_nb_pipeline")

    steps: dict[str, JsonDict] = {}

    # Step 1: nb_sync
    result = pipeio_nb_sync(pipe=pipe, flow=flow, name=name, formats=formats)
    steps["nb_sync"] = result
    if "error" in result:
        return json_dict({"steps": steps, "completed": False, "failed_at": "nb_sync"})

    # Step 2: nb_publish
    result = pipeio_nb_publish(pipe=pipe, flow=flow, name=name)
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
    """Apply the pipeio docs nav fragment to mkdocs.yml.

    Reads the generated nav from ``pipeio_docs_nav``, finds or creates the
    ``Pipelines`` section in ``mkdocs.yml``, and writes the updated file.
    Returns the diff of what changed.
    """
    if not _pipeio_available():
        return _unavailable("pipeio_mkdocs_nav_patch")

    root = get_project_root()
    mkdocs_path = root / "mkdocs.yml"
    if not mkdocs_path.exists():
        mkdocs_path = root / "mkdocs.yaml"
    if not mkdocs_path.exists():
        return json_dict({"error": "mkdocs.yml not found"})

    # Get nav fragment from pipeio
    try:
        from pipeio.mcp import mcp_docs_nav
        nav_result = mcp_docs_nav(root)
    except Exception as exc:
        return json_dict({"error": f"docs_nav failed: {exc}"})

    fragment_yaml = nav_result.get("nav_fragment", "")
    if not fragment_yaml or fragment_yaml.startswith("#"):
        return json_dict({"error": "No pipeline docs to inject (docs/pipelines/ empty or missing)"})

    # Parse the nav fragment
    try:
        import yaml
        fragment = yaml.safe_load(fragment_yaml)
    except Exception as exc:
        return json_dict({"error": f"Failed to parse nav fragment: {exc}"})

    if not isinstance(fragment, list):
        fragment = [fragment]

    # The fragment is a list like [{"Pipelines": {...}}]
    # Extract the Pipelines entry
    pipelines_entry = None
    for item in fragment:
        if isinstance(item, dict) and "Pipelines" in item:
            pipelines_entry = item
            break
    if pipelines_entry is None:
        pipelines_entry = {"Pipelines": fragment}

    # Read and patch mkdocs.yml
    try:
        import yaml
        original = mkdocs_path.read_text(encoding="utf-8")
        config = yaml.safe_load(original) or {}
    except Exception as exc:
        return json_dict({"error": f"Failed to read mkdocs.yml: {exc}"})

    nav = config.get("nav")
    if nav is None:
        nav = []
        config["nav"] = nav

    # Find and replace existing Pipelines entry, or append
    replaced = False
    for i, entry in enumerate(nav):
        if isinstance(entry, dict) and "Pipelines" in entry:
            nav[i] = pipelines_entry
            replaced = True
            break
    if not replaced:
        nav.append(pipelines_entry)

    # Write back
    try:
        updated = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
        mkdocs_path.write_text(updated, encoding="utf-8")
    except Exception as exc:
        return json_dict({"error": f"Failed to write mkdocs.yml: {exc}"})

    return json_dict({
        "patched": True,
        "path": str(mkdocs_path.relative_to(root)),
        "replaced_existing": replaced,
        "pipelines_nav": pipelines_entry,
    })


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
