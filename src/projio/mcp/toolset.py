"""Expose a reduced tool set: ``PROJIO_MCP_TOOLS`` on the server's environment.

Two ``projio.mcp.server`` entries in one ``.mcp.json`` (say the project's own
and a shared lab project's, differing only in ``PROJIO_ROOT``) load every tool
name twice. Set ``PROJIO_MCP_TOOLS`` on the second entry to keep only what that
server is for::

    "env": {"PROJIO_ROOT": "/path/to/lab", "PROJIO_MCP_TOOLS": "codio,biblio,rag"}

The value is a comma- or space-separated list of subsystem names (``SUBSYSTEMS``)
and tool-name globs (``paper_*``, ``note_read``). A ``-`` prefix removes
(``biblio,-biblio_zotero_*``); a list of removals only starts from every tool.
Unset or empty keeps every tool except the opt-in groups (``OPT_IN``).

Opt-in groups (deprecated or parked subsystems) are left out unless the project
enables them: the group's entry in ``.projio/packages.yml`` with
``enabled: true``, or ``PROJIO_MCP_TOOLS`` naming the group or one of its tools
(``present`` or ``present_build``).
"""
from __future__ import annotations

import os
import re
import sys
from fnmatch import fnmatchcase

ENV_VAR = "PROJIO_MCP_TOOLS"

SUBSYSTEMS: dict[str, tuple[str, ...]] = {
    "rag": ("rag_query", "rag_query_multi", "corpus_list"),
    "indexio": ("indexio_*",),
    "biblio": ("biblio_*", "paper_*", "citekey_resolve", "library_get"),
    "codio": ("codio_*",),
    "notio": ("note_*", "notio_*"),
    "manuscript": ("manuscript_*", "master_*"),
    "present": ("present_*",),
    "report": ("report_*",),
    "pipeio": ("pipeio_*",),
    "figio": ("figio_*",),
    "questio": ("questio_*",),
    "datalad": ("datalad_*", "git_status"),
    "site": ("site_*",),
    "context": ("project_context", "runtime_conventions", "agent_instructions", "module_context",
                "skill_read", "projio_init", "ecosystem_status", "permissions_sync"),
}


# Groups left out unless the project opts in: group name -> packages.yml key.
# present: deprecated 2026-11-24 (docs/specs/notio/slim.md §7), use Quarto reveal.js.
OPT_IN: dict[str, str] = {
    "present": "present",
}


def _patterns(token: str) -> tuple[str, ...]:
    return SUBSYSTEMS.get(token, (token,))


def select_tools(names: list[str], spec: str | None) -> tuple[list[str], list[str]]:
    """``(kept, unmatched_tokens)`` for the tool *names* under *spec*."""
    tokens = [t for t in re.split(r"[,\s]+", spec or "") if t]
    if not tokens:
        return list(names), []
    include = [t for t in tokens if not t.startswith("-")]
    exclude = [t[1:] for t in tokens if t.startswith("-")]
    unmatched = [t for t in include + exclude
                 if not any(fnmatchcase(n, p) for n in names for p in _patterns(t))]
    kept = [n for n in names
            if (not include or any(fnmatchcase(n, p) for t in include for p in _patterns(t)))
            and not any(fnmatchcase(n, p) for t in exclude for p in _patterns(t))]
    return kept, unmatched


def enabled_packages(root: str | os.PathLike | None = None) -> set[str]:
    """Names with ``enabled: true`` in ``<root>/.projio/packages.yml`` (root: ``$PROJIO_ROOT`` or cwd)."""
    from pathlib import Path

    base = Path(root or os.environ.get("PROJIO_ROOT") or os.getcwd())
    path = base / ".projio" / "packages.yml"
    if not path.is_file():
        return set()
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()
    pkgs = data.get("packages") if isinstance(data, dict) else None
    if not isinstance(pkgs, dict):
        return set()
    return {k for k, v in pkgs.items() if isinstance(v, dict) and v.get("enabled")}


def opt_in_dropped(names: list[str], spec: str | None, enabled: set[str]) -> set[str]:
    """Tools of the ``OPT_IN`` groups that neither *spec* nor *enabled* packages turn on."""
    tokens = [t for t in re.split(r"[,\s]+", spec or "") if t and not t.startswith("-")]
    dropped: set[str] = set()
    for group, pkg in OPT_IN.items():
        if pkg in enabled or group in tokens:
            continue
        group_tools = {n for n in names if any(fnmatchcase(n, p) for p in SUBSYSTEMS[group])}
        named = {n for n in group_tools if any(fnmatchcase(n, p) for t in tokens for p in _patterns(t))}
        dropped |= group_tools - named
    return dropped


def apply_tool_filter(server, spec: str | None = None, enabled: set[str] | None = None) -> None:
    """Disable on *server* every tool that *spec* (default: ``$PROJIO_MCP_TOOLS``) does not keep,
    and the ``OPT_IN`` groups the project has not enabled (*enabled*: default from packages.yml)."""
    import asyncio

    spec = os.environ.get(ENV_VAR, "") if spec is None else spec
    enabled = enabled_packages() if enabled is None else enabled
    names = [t.name for t in asyncio.run(server.list_tools())]
    kept, unmatched = select_tools(names, spec)
    opted_out = opt_in_dropped(names, spec, enabled)
    kept = [n for n in kept if n not in opted_out]
    dropped = set(names) - set(kept)
    if dropped:
        server.disable(names=dropped, components={"tool"})
    if spec.strip():
        for token in unmatched:
            print(f"[projio mcp] {ENV_VAR}: '{token}' matches no tool", file=sys.stderr)
        print(f"[projio mcp] {ENV_VAR}={spec!r}: {len(kept)} of {len(names)} tools", file=sys.stderr)
    if opted_out:
        groups = sorted(g for g in OPT_IN if any(n in opted_out for n in names
                                                  if any(fnmatchcase(n, p) for p in SUBSYSTEMS[g])))
        print(f"[projio mcp] opt-in groups left out: {', '.join(groups)} "
              f"(enable in .projio/packages.yml or {ENV_VAR})", file=sys.stderr)
