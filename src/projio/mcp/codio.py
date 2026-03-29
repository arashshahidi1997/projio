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


def codio_add_urls(urls: list[str], clone: bool = False, shallow: bool = False) -> JsonDict:
    """Add libraries to the code reuse registry from GitHub/GitLab URLs.

    Fetches metadata (language, license, description) from GitHub API automatically.

    Args:
        urls: List of repository URLs (GitHub, GitLab, or any git URL).
        clone: If True, clone repositories as local mirrors.
        shallow: If True (and clone=True), perform a depth-1 shallow clone.
    """
    if not _codio_available():
        return _unavailable("codio_add_urls")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.mcp import mcp_add_urls  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)
        result = mcp_add_urls(registry, urls, clone=clone, shallow=shallow)
        return json_dict({"results": result})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_rag_sync(force_init: bool = False) -> JsonDict:
    """Register codio library sources into the indexio config.

    Wraps ``codio rag sync``. Generates ``codio-notes``, ``codio-catalog``,
    and per-library ``codio-src-{name}`` sources from the registry. After this,
    run ``indexio_build`` to index code-library knowledge.

    The target indexio config path is read from ``indexio.config`` in
    ``.projio/config.yml`` (defaults to ``.projio/indexio/config.yaml``).
    Source-tree globs are language-dependent: Python → ``**/*.py``,
    MATLAB → ``**/*.m``, unknown languages → ``**/*``.

    Args:
        force_init: Re-initialize the RAG config even if it already exists.
    """
    if not _codio_available():
        return _unavailable("codio_rag_sync")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.rag import sync_codio_rag_sources  # type: ignore[import]
        from projio.init import load_projio_config
        config = load_config(root)
        registry = Registry(config=config)
        # Resolve indexio config path from the projio project config so we
        # write to the same file that rag_query and indexio_build use.
        projio_cfg = load_projio_config(root)
        idx_cfg = projio_cfg.get("indexio") or {}
        config_rel = idx_cfg.get("config", ".projio/indexio/config.yaml")
        config_path = root / config_rel
        result = sync_codio_rag_sources(
            root, config, config_path=config_path, force_init=force_init,
            catalog=registry.catalog,
        )
        return json_dict({
            "config_path": str(result.config_path),
            "created": result.created,
            "initialized": result.initialized,
            "added": list(result.added),
            "updated": list(result.updated),
            "removed": list(result.removed),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def codio_add(
    name: str,
    kind: str,
    path: str = "",
    language: str = "",
    repo_url: str = "",
    pip_name: str = "",
    license: str = "",  # noqa: A002
    summary: str = "",
    capabilities: list[str] | None = None,
    priority: str = "tier2",
    runtime_import: str = "reference_only",
    status: str = "active",
) -> JsonDict:
    """Register a library into the codio registry with metadata.

    Adds or updates both the catalog entry (shared identity) and the project
    profile entry (local policies). Use this when ``codio_discover`` returns
    empty and you want to register a locally available library.

    Args:
        name: Library slug (e.g. "yasa", "mne").
        kind: Library kind — one of: internal, external_mirror, utility.
        path: Local filesystem path to the library source tree (for mirrors).
        language: Dominant programming language (e.g. "python").
        repo_url: Upstream repository URL.
        pip_name: PyPI / conda package name.
        license: Software license identifier (e.g. "MIT", "Apache-2.0").
        summary: Short one-line description.
        capabilities: List of capability tags (e.g. ["signal-processing", "sleep-staging"]).
        priority: Project priority tier — one of: tier1, tier2, tier3.
        runtime_import: Import policy — one of: internal, pip_only, reference_only.
        status: Registry status — one of: active, candidate, deprecated, archived.
    """
    if not _codio_available():
        return _unavailable("codio_add")
    root = get_project_root()
    try:
        from codio import load_config, Registry  # type: ignore[import]
        from codio.models import LibraryCatalogEntry, ProjectProfileEntry  # type: ignore[import]
        from codio.skills.update import add_library  # type: ignore[import]
        config = load_config(root)
        registry = Registry(config=config)

        catalog_entry = LibraryCatalogEntry(
            name=name,
            kind=kind,
            path=path,
            language=language,
            repo_url=repo_url,
            pip_name=pip_name,
            license=license,
            summary=summary,
        )
        profile_entry = ProjectProfileEntry(
            name=name,
            priority=priority,
            runtime_import=runtime_import,
            capabilities=capabilities or [],
            status=status,
        )
        add_library(registry, catalog_entry, profile_entry)
        return json_dict({
            "name": name,
            "kind": kind,
            "status": "registered",
        })
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
