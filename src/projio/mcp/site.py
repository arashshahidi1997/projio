"""MCP tools: site_detect, site_serve, site_stop, site_list."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict


def site_detect() -> JsonDict:
    """Detect which doc-site framework the project uses."""
    root = get_project_root()
    try:
        from projio.site import detect_framework

        fw = detect_framework(root)
        return json_dict({"framework": fw, "root": str(root)})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def site_serve(port: int | None = None, framework: str | None = None) -> JsonDict:
    """Start the doc server in background, return URL and PID."""
    root = get_project_root()
    try:
        from projio.site import serve

        result = serve(root, port=port, framework=framework, background=True)
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def site_stop(port: int | None = None, pid: int | None = None) -> JsonDict:
    """Stop a running doc server by port or PID."""
    root = get_project_root()
    try:
        from projio.site import stop

        return json_dict(stop(root, port=port, pid=pid))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def site_list() -> JsonDict:
    """List running doc servers for this project."""
    root = get_project_root()
    try:
        from projio.site import list_servers

        return json_dict({"servers": list_servers(root)})
    except Exception as exc:
        return json_dict({"error": str(exc)})
