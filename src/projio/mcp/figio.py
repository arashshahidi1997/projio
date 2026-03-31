"""MCP tools: figio figure orchestration, build, validation."""
from __future__ import annotations

from typing import Any

from .common import JsonDict, get_project_root, json_dict


def _figio_available() -> bool:
    try:
        import figio  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the figio package. Install with: pip install figio"}


def figio_figure_list() -> JsonDict:
    """List all figurespec YAML files in the project."""
    if not _figio_available():
        return _unavailable("figio_figure_list")
    root = get_project_root()
    try:
        from figio.mcp import mcp_figure_list
        return json_dict(mcp_figure_list(root))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def figio_inspect(figure_id: str = "") -> JsonDict:
    """Inspect a figure spec: panels, layout, constraints, annotations, style.

    Args:
        figure_id: Figure ID to inspect. If empty, lists all figures.
    """
    if not _figio_available():
        return _unavailable("figio_inspect")
    root = get_project_root()
    try:
        from figio.mcp import mcp_inspect
        return json_dict(mcp_inspect(root, figure_id=figure_id))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def figio_build(
    figure_id: str,
    panels: str = "",
    force: bool = False,
) -> JsonDict:
    """Build a figure from its spec. Returns output paths and validation.

    Args:
        figure_id: Figure ID to build.
        panels: Comma-separated panel IDs to rebuild (empty = all).
        force: Bypass cache and re-render all panels.
    """
    if not _figio_available():
        return _unavailable("figio_build")
    root = get_project_root()
    try:
        from figio.mcp import mcp_build
        return json_dict(mcp_build(root, figure_id=figure_id, panels=panels, force=force))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def figio_validate(
    figure_id: str,
    target: str = "",
) -> JsonDict:
    """Validate a figure spec against a target profile.

    Args:
        figure_id: Figure ID to validate.
        target: Override target profile name (empty = use spec's target).
    """
    if not _figio_available():
        return _unavailable("figio_validate")
    root = get_project_root()
    try:
        from figio.mcp import mcp_validate
        return json_dict(mcp_validate(root, figure_id=figure_id, target=target))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def figio_edit_spec(
    figure_id: str,
    patch: dict[str, Any] = {},
) -> JsonDict:
    """Apply a JSON merge-patch to a figure spec.

    Args:
        figure_id: Figure ID to edit.
        patch: JSON merge-patch object to apply.
    """
    if not _figio_available():
        return _unavailable("figio_edit_spec")
    root = get_project_root()
    try:
        from figio.mcp import mcp_edit_spec
        return json_dict(mcp_edit_spec(root, figure_id=figure_id, patch=patch))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def figio_query_output(
    figure_id: str,
    query: str,
) -> JsonDict:
    """Query structured data from the last build output.

    Args:
        figure_id: Figure ID to query.
        query: Query string (e.g. "bounding_box of panel X", "dimensions", "all panels").
    """
    if not _figio_available():
        return _unavailable("figio_query_output")
    root = get_project_root()
    try:
        from figio.mcp import mcp_query_output
        return json_dict(mcp_query_output(root, figure_id=figure_id, query=query))
    except Exception as exc:
        return json_dict({"error": str(exc)})
