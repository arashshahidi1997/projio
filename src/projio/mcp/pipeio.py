"""MCP tools: pipeio_flow_list, pipeio_flow_status, pipeio_nb_status, pipeio_registry_validate."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict


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
