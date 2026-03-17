"""MCP tools: codio_list, codio_get, codio_registry, codio_vocab, codio_validate, codio_discover."""
from __future__ import annotations

import dataclasses
from typing import Any

from .common import JsonDict, get_project_root, json_dict


def _codio_available() -> bool:
    try:
        import codio  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the codio package. Install with: pip install codio"}


def codio_list(
    kind: str | None = None,
    language: str | None = None,
    capability: str | None = None,
    priority: str | None = None,
    runtime_import: str | None = None,
) -> JsonDict:
    """Filtered library listing from the code reuse registry.

    Args:
        kind: Filter by library kind (internal, external_mirror, utility).
        language: Filter by programming language.
        capability: Filter by capability tag.
        priority: Filter by priority tier (tier1, tier2, tier3).
        runtime_import: Filter by runtime import policy.
    """
    if not _codio_available():
        return _unavailable("codio_list")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.mcp import mcp_list  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        result = mcp_list(
            registry,
            kind=kind,
            language=language,
            capability=capability,
            priority=priority,
            runtime_import=runtime_import,
        )
        return json_dict({"libraries": result})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_get(name: str) -> JsonDict:
    """Full merged record for a single library from the code reuse registry.

    Args:
        name: Library slug name.
    """
    if not _codio_available():
        return _unavailable("codio_get")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.mcp import mcp_get  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        result = mcp_get(registry, name)
        if result is None:
            return json_dict({"error": f"Library '{name}' not found"})
        return json_dict(result)
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_registry() -> JsonDict:
    """Full snapshot of the code reuse registry (catalog + profiles)."""
    if not _codio_available():
        return _unavailable("codio_registry")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.mcp import mcp_registry  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        return json_dict(mcp_registry(registry))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_vocab() -> JsonDict:
    """Controlled vocabulary for the code reuse registry fields."""
    if not _codio_available():
        return _unavailable("codio_vocab")
    try:
        from codio.mcp import mcp_vocab  # type: ignore[import]
        return json_dict(mcp_vocab())
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_validate() -> JsonDict:
    """Validate code reuse registry consistency."""
    if not _codio_available():
        return _unavailable("codio_validate")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.mcp import mcp_validate  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        return json_dict(mcp_validate(registry))
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_add_urls(urls: list[str], clone: bool = False) -> JsonDict:
    """Add libraries to the code reuse registry from GitHub/GitLab URLs.

    Fetches metadata (language, license, description) from GitHub API automatically.

    Args:
        urls: List of repository URLs (GitHub, GitLab, or any git URL).
        clone: If True, clone repositories as local mirrors.
    """
    if not _codio_available():
        return _unavailable("codio_add_urls")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.mcp import mcp_add_urls  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        result = mcp_add_urls(registry, urls, clone=clone)
        return json_dict({"results": result})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_discover(query: str, language: str | None = None) -> JsonDict:
    """Search for libraries matching a capability query.

    Args:
        query: Capability or keyword to search for.
        language: Optional language filter.
    """
    if not _codio_available():
        return _unavailable("codio_discover")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.skills.discovery import discover  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        result = discover(query, registry, language=language)
        return json_dict(dataclasses.asdict(result))
    except Exception as exc:
        return json_dict({"error": str(exc)})
