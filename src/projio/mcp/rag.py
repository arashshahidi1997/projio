"""MCP tools: rag_query, rag_query_multi, corpus_list, indexio_build, indexio_sources_list, indexio_sources_sync."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .common import JsonDict, get_project_root, json_dict


def _get_config() -> tuple[Any, str]:
    """Return (config_path, root) from the projio workspace config."""
    from projio.init import load_projio_config

    root = get_project_root()
    cfg = load_projio_config(root)
    idx_cfg = cfg.get("indexio") or {}
    config_rel = idx_cfg.get("config", "infra/indexio/config.yaml")
    return str(root / config_rel), str(root)


def rag_query(query: str, corpus: str = "", k: int = 8) -> JsonDict:
    """Similarity search against the project Chroma store.

    Args:
        query: Search query.
        corpus: Optional corpus filter (empty = all).
        k: Number of results.
    """
    from indexio.query import query_index

    config_path, root = _get_config()
    payload = query_index(
        config_path=config_path,
        root=root,
        query=query,
        corpus=corpus or None,
        k=k,
        prefer_canonical=True,
    )
    return json_dict(payload)


def rag_query_multi(queries: list[str], corpus: str = "", k: int = 5) -> JsonDict:
    """Similarity searches for multiple queries, deduplicating by source path.

    Args:
        queries: List of search queries.
        corpus: Optional corpus filter (empty = all).
        k: Results per query.
    """
    from indexio.query import query_index_multi

    config_path, root = _get_config()
    payload = query_index_multi(
        config_path=config_path,
        root=root,
        queries=queries,
        corpus=corpus or None,
        k=k,
        prefer_canonical=True,
    )
    return json_dict(payload)


def corpus_list() -> JsonDict:
    """List indexed corpora with document counts."""
    from indexio.config import load_indexio_config, resolve_store

    config_path, root = _get_config()
    config = load_indexio_config(config_path, root=root)
    try:
        store_cfg = resolve_store(config, prefer_canonical=True, must_exist=True)
    except FileNotFoundError:
        return json_dict({"corpora": [], "error": "index store not found — run: indexio build"})

    from langchain_chroma import Chroma
    from indexio.query import make_embeddings

    embeddings = make_embeddings(config.embedding_model)
    db = Chroma(
        embedding_function=embeddings,
        persist_directory=str(store_cfg.persist_directory),
    )
    collection = db._collection
    all_meta = collection.get(include=["metadatas"])["metadatas"] or []
    counts: dict[str, int] = {}
    for meta in all_meta:
        corpus = (meta or {}).get("corpus", "")
        counts[corpus] = counts.get(corpus, 0) + 1

    return json_dict({
        "store": store_cfg.name,
        "persist_directory": str(store_cfg.persist_directory),
        "corpora": [{"corpus": c, "chunks": n} for c, n in sorted(counts.items())],
    })


def indexio_sources_list() -> JsonDict:
    """List sources registered in the indexio config with last-build stats.

    Returns each source's id, corpus, selector (glob or path), and — if a
    status manifest exists from a previous build — the file/char/chunk counts
    from that build.
    """
    from indexio.config import load_indexio_config, resolve_store

    config_path, root = _get_config()
    config = load_indexio_config(config_path, root=root)

    # Try to read build stats from the status manifest
    status_sources: dict[str, Any] = {}
    built_at: str = ""
    try:
        store_cfg = resolve_store(config, prefer_canonical=True, must_exist=False)
        status_path = Path(store_cfg.persist_directory) / "indexio.status.json"
        if status_path.exists():
            with open(status_path) as fh:
                manifest = json.load(fh)
            status_sources = manifest.get("sources", {})
            built_at = manifest.get("built_at", "")
    except Exception:
        pass

    sources = []
    for src in config.sources:
        entry: dict[str, Any] = {
            "id": src.id,
            "corpus": src.corpus,
            "selector": src.glob or src.path or "",
        }
        if src.id in status_sources:
            stats = status_sources[src.id]
            entry["files"] = stats.get("files", 0)
            entry["chars"] = stats.get("chars", 0)
            entry["chunks"] = stats.get("chunks", 0)
        sources.append(entry)

    result: dict[str, Any] = {"sources": sources, "total": len(sources)}
    if built_at:
        result["built_at"] = built_at
    return json_dict(result)


def indexio_sources_sync(build: bool = False, sources_filter: list[str] | None = None) -> JsonDict:
    """Sync all subsystem sources (biblio, codio) into the indexio config, then optionally rebuild.

    Convenience wrapper that calls biblio_rag_sync and codio_rag_sync in sequence,
    collecting results. Gracefully skips unavailable subsystems.

    Args:
        build: If true, trigger indexio_build after syncing sources.
        sources_filter: Optional list of source IDs to rebuild (only used when build=True).
    """
    results: dict[str, Any] = {"synced": [], "skipped": [], "errors": []}

    # Biblio sync
    try:
        from .biblio import biblio_rag_sync as _biblio_sync, _biblio_available
        if _biblio_available():
            res = _biblio_sync()
            results["synced"].append({"subsystem": "biblio", "result": res})
        else:
            results["skipped"].append("biblio (not installed)")
    except Exception as exc:
        results["errors"].append({"subsystem": "biblio", "error": str(exc)})

    # Codio sync
    try:
        from .codio import codio_rag_sync as _codio_sync, _codio_available
        if _codio_available():
            res = _codio_sync()
            results["synced"].append({"subsystem": "codio", "result": res})
        else:
            results["skipped"].append("codio (not installed)")
    except Exception as exc:
        results["errors"].append({"subsystem": "codio", "error": str(exc)})

    # Optional build
    if build:
        try:
            build_result = indexio_build(sources=sources_filter)
            results["build"] = build_result
        except Exception as exc:
            results["errors"].append({"subsystem": "indexio_build", "error": str(exc)})

    return json_dict(results)


def _build_progress_path(root: str | Path, job_id: str) -> Path:
    """Return the path to a build progress file."""
    p = Path(root) / ".projio" / "indexio" / "jobs" / f"{job_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _build_worker_script(
    config_path: str,
    root: str,
    sources: list[str] | None,
    job_id: str,
    job_file: str,
) -> str:
    """Build the Python code that runs in a detached subprocess."""
    sources_repr = repr(sources)
    return f"""\
import json, time, traceback, threading
from pathlib import Path

def _write(data):
    p = Path({job_file!r})
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\\n", encoding="utf-8")

_start = time.monotonic()
_start_iso = time.strftime("%Y-%m-%dT%H:%M:%S%z")
_current_source = None
_sources_completed = 0
_sources_total = 0
_timer_lock = threading.Lock()
_timer = None
_done = False

def _periodic_update():
    if _done:
        return
    with _timer_lock:
        elapsed = round(time.monotonic() - _start, 1)
        data = {{
            "job_id": {job_id!r},
            "status": "running",
            "started_at": _start_iso,
            "elapsed_seconds": elapsed,
            "current_source": _current_source,
            "sources_completed": _sources_completed,
            "sources_total": _sources_total,
        }}
        _write(data)
    global _timer
    _timer = threading.Timer(30.0, _periodic_update)
    _timer.daemon = True
    _timer.start()

def _on_progress(source_id, idx, total, stats):
    global _current_source, _sources_completed, _sources_total
    with _timer_lock:
        _current_source = source_id
        _sources_total = total
        _sources_completed = idx if stats is None else idx + 1
        elapsed = round(time.monotonic() - _start, 1)
        data = {{
            "job_id": {job_id!r},
            "status": "running",
            "started_at": _start_iso,
            "elapsed_seconds": elapsed,
            "current_source": source_id,
            "sources_completed": _sources_completed,
            "sources_total": total,
        }}
        if stats is not None:
            data["last_source_stats"] = stats
        _write(data)

# Start periodic timer for intra-source updates
_periodic_update()

try:
    from indexio.build import build_index

    result = build_index(
        config_path={config_path!r},
        root={root!r},
        sources_filter={sources_repr},
        verbose=False,
        on_progress=_on_progress,
    )
    _done = True
    if _timer:
        _timer.cancel()
    elapsed = round(time.monotonic() - _start, 1)
    _write({{
        "job_id": {job_id!r},
        "status": "completed",
        "started_at": _start_iso,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "elapsed_seconds": elapsed,
        "sources_completed": len(result.get("source_stats", {{}})),
        "sources_total": len(result.get("source_stats", {{}})),
        "result": result,
    }})

except Exception:
    _done = True
    if _timer:
        _timer.cancel()
    elapsed = round(time.monotonic() - _start, 1)
    _write({{
        "job_id": {job_id!r},
        "status": "failed",
        "started_at": _start_iso,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "elapsed_seconds": elapsed,
        "error": traceback.format_exc(),
    }})
"""


def _pid_alive(pid: int) -> bool:
    """Check whether a process with the given PID is still running."""
    import os
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _resolve_update_sources() -> list[str]:
    """Identify sources that need rebuilding: new, changed, or missing files."""
    from indexio.config import load_indexio_config, resolve_store
    from indexio.build import load_status_manifest, source_snapshot

    config_path, root = _get_config()
    config = load_indexio_config(config_path, root=root)

    try:
        store_cfg = resolve_store(config, prefer_canonical=True, must_exist=False)
    except Exception:
        # No store — rebuild everything
        return [src.id for src in config.sources]

    manifest = load_status_manifest(store_cfg.persist_directory)
    if manifest is None:
        return [src.id for src in config.sources]

    manifest_sources = dict(manifest.get("sources", {}))
    needs_build: list[str] = []
    for src in config.sources:
        previous = manifest_sources.get(src.id)
        if previous is None:
            needs_build.append(src.id)
            continue
        snapshot = source_snapshot(config, src)
        if (
            previous.get("matched_paths") != snapshot["matched_paths"]
            or previous.get("file_state") != snapshot["file_state"]
        ):
            needs_build.append(src.id)
    return needs_build


def indexio_build(
    sources: list[str] | None = None,
    background: bool = False,
    update: bool = False,
) -> JsonDict:
    """Rebuild the search index. Full rebuild by default, or partial if sources are specified.

    Args:
        sources: Optional list of source IDs to rebuild (partial). Empty or null = full rebuild.
        background: If true, launch in a detached subprocess and return a job_id immediately.
                    Use indexio_build_status(job_id) to check progress.
        update: If true (and sources is empty), auto-detect sources that are new or changed
                since the last build and only rebuild those. Skips up-to-date sources.
    """
    config_path, root = _get_config()

    if update and not sources:
        sources = _resolve_update_sources()
        if not sources:
            return json_dict({
                "status": "up_to_date",
                "message": "All sources are up to date — nothing to rebuild.",
            })

    if background:
        job_id = f"build-{uuid.uuid4().hex[:8]}"
        progress_path = _build_progress_path(root, job_id)

        worker_code = _build_worker_script(
            config_path=config_path,
            root=root,
            sources=sources or None,
            job_id=job_id,
            job_file=str(progress_path),
        )

        proc = subprocess.Popen(
            [sys.executable, "-c", worker_code],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Write initial state with PID for crash detection
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(json.dumps({
            "job_id": job_id,
            "status": "starting",
            "pid": proc.pid,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "sources_completed": 0,
            "sources_total": 0,
        }, indent=2) + "\n", encoding="utf-8")

        return json_dict({
            "background": True,
            "job_id": job_id,
            "pid": proc.pid,
            "status": "starting",
            "hint": "Use indexio_build_status(job_id) to check progress.",
        })

    from indexio.build import build_index
    result = build_index(
        config_path=config_path,
        root=root,
        sources_filter=sources or None,
        verbose=False,
    )
    return json_dict(result)


def indexio_build_status(job_id: str) -> JsonDict:
    """Check the status and progress of a background indexio_build job.

    Returns current status, sources completed/total, elapsed time, and result
    when finished.  Detects crashed processes automatically.

    Args:
        job_id: Job ID returned by indexio_build(..., background=True).
    """
    _config_path, root = _get_config()
    progress_path = _build_progress_path(root, job_id)

    if not progress_path.exists():
        return json_dict({"error": f"No build job found with id: {job_id}"})

    try:
        data = json.loads(progress_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return json_dict({"error": f"Failed to read progress: {exc}"})

    # Detect crashed process: still marked running/starting but PID is dead
    status = data.get("status", "")
    pid = data.get("pid")
    if status in ("running", "starting") and pid is not None and not _pid_alive(pid):
        data["status"] = "failed"
        data["error"] = "Process exited without writing results (likely crashed)"
        data["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        progress_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    return json_dict(data)


def indexio_status() -> JsonDict:
    """Show per-source index status with change detection.

    Returns each source's build stats (files, chars, chunks), its current state
    (indexed, changed, not_yet_built, missing_files, empty_match), and
    actionable source IDs that need rebuilding.  This is the MCP equivalent
    of ``indexio status``.
    """
    from indexio.config import load_indexio_config, resolve_store
    from indexio.build import load_status_manifest, source_snapshot

    config_path, root = _get_config()
    config = load_indexio_config(config_path, root=root)

    try:
        store_cfg = resolve_store(config, prefer_canonical=True, must_exist=False)
    except Exception:
        return json_dict({"error": "No store configured"})

    manifest = load_status_manifest(store_cfg.persist_directory)
    manifest_sources = {} if manifest is None else dict(manifest.get("sources", {}))

    sources = []
    actionable: list[str] = []
    for src in config.sources:
        snapshot = source_snapshot(config, src)
        previous = manifest_sources.get(src.id)

        # Determine state (mirrors indexio.cli._source_state logic)
        if snapshot["files"] == 0:
            state = "empty_match" if previous is None else "missing_files"
        elif previous is None:
            state = "not_yet_built"
        elif (
            previous.get("matched_paths") == snapshot["matched_paths"]
            and previous.get("file_state") == snapshot["file_state"]
        ):
            state = "indexed"
        else:
            state = "changed"

        entry: dict[str, Any] = {
            "id": src.id,
            "corpus": src.corpus,
            "selector": src.glob or src.path or "",
            "state": state,
            "files": snapshot["files"],
        }
        if previous is not None:
            entry["chars"] = previous.get("chars", 0)
            entry["chunks"] = previous.get("chunks", 0)

        sources.append(entry)
        if state in ("changed", "not_yet_built", "missing_files", "empty_match"):
            actionable.append(src.id)

    result: dict[str, Any] = {
        "store": store_cfg.name,
        "persist_directory": str(store_cfg.persist_directory),
        "total_sources": len(sources),
        "sources": sources,
    }
    if manifest:
        result["built_at"] = manifest.get("built_at", "")
    if actionable:
        result["actionable_source_ids"] = actionable
        result["hint"] = f"Rebuild with: indexio_build(sources={actionable})"
    return json_dict(result)
