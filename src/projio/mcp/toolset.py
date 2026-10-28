"""Expose a reduced tool set: ``PROJIO_MCP_TOOLS`` on the server's environment.

Two ``projio.mcp.server`` entries in one ``.mcp.json`` (say the project's own
and a shared lab project's, differing only in ``PROJIO_ROOT``) load every tool
name twice. Set ``PROJIO_MCP_TOOLS`` on the second entry to keep only what that
server is for::

    "env": {"PROJIO_ROOT": "/path/to/lab", "PROJIO_MCP_TOOLS": "codio,biblio,rag"}

The value is a comma- or space-separated list of subsystem names (``SUBSYSTEMS``)
and tool-name globs (``paper_*``, ``note_read``). A ``-`` prefix removes
(``biblio,-biblio_zotero_*``); a list of removals only starts from every tool.
Unset or empty keeps every tool.
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


def apply_tool_filter(server, spec: str | None = None) -> None:
    """Disable on *server* every tool that *spec* (default: ``$PROJIO_MCP_TOOLS``) does not keep."""
    import asyncio

    spec = os.environ.get(ENV_VAR, "") if spec is None else spec
    if not spec.strip():
        return
    names = [t.name for t in asyncio.run(server.list_tools())]
    kept, unmatched = select_tools(names, spec)
    dropped = set(names) - set(kept)
    if dropped:
        server.disable(names=dropped, components={"tool"})
    for token in unmatched:
        print(f"[projio mcp] {ENV_VAR}: '{token}' matches no tool", file=sys.stderr)
    print(f"[projio mcp] {ENV_VAR}={spec!r}: {len(kept)} of {len(names)} tools", file=sys.stderr)
