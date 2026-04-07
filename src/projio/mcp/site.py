"""MCP tools: site_detect, site_build, site_deploy, site_serve, site_stop, site_list."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict, resolve_makefile_vars
from .context import _expand


def _resolve_docs_python() -> str | None:
    """Resolve the Python binary for doc-site builds.

    Checks ``code.envs.docs`` in config first, then falls back to Makefile
    vars (``MKDOCS`` → extract python, then ``PYTHON``).  Returns ``None``
    when no override is found (caller should use ``sys.executable``).
    """
    from projio.config import resolve_env_python

    root = get_project_root()
    env_python = resolve_env_python(root, "docs")
    if env_python:
        return env_python

    vars_ = resolve_makefile_vars()
    # Try MKDOCS first — if it's "python -m mkdocs", extract the python part
    if "MKDOCS" in vars_:
        expanded = _expand(vars_["MKDOCS"], vars_)
        parts = expanded.split()
        if len(parts) >= 3 and parts[1] == "-m":
            return parts[0]
    # Fall back to PYTHON
    if "PYTHON" in vars_:
        return _expand(vars_["PYTHON"], vars_)
    return None


def site_build(framework: str | None = None, strict: bool = False) -> JsonDict:
    """Build the doc site (mkdocs build / sphinx-build / vite build).

    Args:
        framework: Override auto-detection ('mkdocs', 'sphinx', 'vite').
        strict: Enable strict mode (warnings become errors).
    """
    root = get_project_root()
    try:
        from projio.site import build, detect_framework

        fw = framework or detect_framework(root)
        python_bin = _resolve_docs_python()
        build(root, strict=strict, framework=framework, python_bin=python_bin)
        return json_dict({
            "built": True,
            "framework": fw,
            "root": str(root),
        })
    except SystemExit as exc:
        return json_dict({"built": False, "error": f"Build failed (exit {exc.code})"})
    except Exception as exc:
        return json_dict({"built": False, "error": str(exc)})


def site_deploy(target: str = "gitlab") -> JsonDict:
    """Deploy the doc site by pushing to the configured pages sibling.

    If ``docs/`` is a git submodule (subdataset), it is pushed first so that
    the subdataset content reaches the remote before the main dataset pushes
    the updated submodule pointer.  Both pushes are non-recursive.

    Args:
        target: Sibling name to push to (default 'gitlab').
    """
    from .datalad import datalad_push

    root = get_project_root()
    results: dict = {}

    # Staged push: if docs/ is a subdataset, push it first
    gitmodules = root / ".gitmodules"
    if gitmodules.is_file() and "docs" in gitmodules.read_text():
        docs_result = datalad_push(sibling=target, dataset="docs")
        results["docs_push"] = docs_result

    # Then push the main dataset (carries the updated submodule pointer)
    main_result = datalad_push(sibling=target)
    results["main_push"] = main_result

    # Report overall success
    docs_ok = "docs_push" not in results or results["docs_push"].get("returncode", 1) == 0
    main_ok = results["main_push"].get("returncode", 1) == 0
    results["deployed"] = docs_ok and main_ok

    return json_dict(results)


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
