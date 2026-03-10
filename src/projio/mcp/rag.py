"""MCP tools: rag_query, rag_query_multi, corpus_list."""
from __future__ import annotations

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
