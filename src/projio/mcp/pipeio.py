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
