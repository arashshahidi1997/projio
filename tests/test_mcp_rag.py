"""Tests for projio.mcp.rag — MCP wrapper delegation, error handling, availability."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from projio.mcp.rag import (
    _build_progress_path,
    _build_worker_script,
    _get_config,
    _pid_alive,
    indexio_build,
    indexio_build_status,
    indexio_sources_list,
    indexio_sources_sync,
    indexio_status,
    rag_query,
    rag_query_multi,
    corpus_list,
)


# ---------------------------------------------------------------------------
# _get_config
# ---------------------------------------------------------------------------


class TestGetConfig:
    def test_returns_config_path_and_root(self) -> None:
        with mock.patch(
            "projio.mcp.rag.get_project_root",
            return_value=Path("/fake/root"),
        ), mock.patch(
            "projio.init.load_projio_config",
            return_value={"indexio": {"config": "infra/indexio/config.yaml"}},
        ):
            config_path, root = _get_config()
        assert config_path == str(Path("/fake/root/infra/indexio/config.yaml"))
        assert root == str(Path("/fake/root"))

    def test_uses_default_config_path(self) -> None:
        with mock.patch(
            "projio.mcp.rag.get_project_root",
            return_value=Path("/fake/root"),
        ), mock.patch(
            "projio.init.load_projio_config",
            return_value={},
        ):
            config_path, root = _get_config()
        assert "infra/indexio/config.yaml" in config_path


# ---------------------------------------------------------------------------
# _build_progress_path
# ---------------------------------------------------------------------------


class TestBuildProgressPath:
    def test_returns_path_in_jobs_dir(self, tmp_path: Path) -> None:
        path = _build_progress_path(tmp_path, "build-abc12345")
        assert path.name == "build-abc12345.json"
        assert "jobs" in str(path)
        assert path.parent.exists()


# ---------------------------------------------------------------------------
# _build_worker_script
# ---------------------------------------------------------------------------


class TestBuildWorkerScript:
    def test_generates_valid_python(self) -> None:
        script = _build_worker_script(
            config_path="/fake/config.yaml",
            root="/fake/root",
            sources=["src1", "src2"],
            job_id="build-test",
            job_file="/fake/jobs/build-test.json",
        )
        # Should be valid Python (compilable)
        compile(script, "<test>", "exec")

    def test_includes_job_id(self) -> None:
        script = _build_worker_script(
            config_path="/c", root="/r", sources=None,
            job_id="build-abc", job_file="/j/build-abc.json",
        )
        assert "build-abc" in script

    def test_includes_sources(self) -> None:
        script = _build_worker_script(
            config_path="/c", root="/r", sources=["biblio-notes", "codio-src"],
            job_id="j1", job_file="/j/j1.json",
        )
        assert "biblio-notes" in script
        assert "codio-src" in script


# ---------------------------------------------------------------------------
# _pid_alive
# ---------------------------------------------------------------------------


class TestPidAlive:
    def test_current_process_is_alive(self) -> None:
        import os
        assert _pid_alive(os.getpid()) is True

    def test_nonexistent_pid_is_dead(self) -> None:
        # PID 0 is special on Unix; use a very large PID
        assert _pid_alive(999999999) is False


# ---------------------------------------------------------------------------
# rag_query / rag_query_multi
# ---------------------------------------------------------------------------


class TestRagQuery:
    def _mock_config(self):
        return mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", "/fake/root"),
        )

    def test_rag_query_delegates(self) -> None:
        with self._mock_config(), mock.patch(
            "indexio.query.query_index", create=True,
            return_value={"results": [{"doc": "test"}], "count": 1},
        ) as m:
            result = rag_query("brain connectivity", corpus="notes", k=5)
        m.assert_called_once_with(
            config_path="/fake/config.yaml",
            root="/fake/root",
            query="brain connectivity",
            corpus="notes",
            k=5,
            prefer_canonical=True,
        )
        assert result["count"] == 1

    def test_rag_query_empty_corpus_passes_none(self) -> None:
        with self._mock_config(), mock.patch(
            "indexio.query.query_index", create=True,
            return_value={"results": []},
        ) as m:
            rag_query("test")
        m.assert_called_once()
        assert m.call_args.kwargs["corpus"] is None

    def test_rag_query_multi_delegates(self) -> None:
        with self._mock_config(), mock.patch(
            "indexio.query.query_index_multi", create=True,
            return_value={"results": [], "count": 0},
        ) as m:
            result = rag_query_multi(["q1", "q2"], corpus="papers")
        m.assert_called_once_with(
            config_path="/fake/config.yaml",
            root="/fake/root",
            queries=["q1", "q2"],
            corpus="papers",
            k=5,
            prefer_canonical=True,
        )


# ---------------------------------------------------------------------------
# indexio_sources_list
# ---------------------------------------------------------------------------


class TestIndexioSourcesList:
    def test_returns_sources(self) -> None:
        fake_config = mock.MagicMock()
        fake_src = mock.MagicMock()
        fake_src.id = "notes"
        fake_src.corpus = "notes"
        fake_src.glob = "notes/**/*.md"
        fake_src.path = None
        fake_config.sources = [fake_src]

        with mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", "/fake/root"),
        ), mock.patch(
            "indexio.config.load_indexio_config", create=True,
            return_value=fake_config,
        ), mock.patch(
            "indexio.config.resolve_store", create=True,
            side_effect=FileNotFoundError("no store"),
        ):
            result = indexio_sources_list()
        assert result["total"] == 1
        assert result["sources"][0]["id"] == "notes"


# ---------------------------------------------------------------------------
# indexio_sources_sync
# ---------------------------------------------------------------------------


class TestIndexioSourcesSync:
    def test_skips_unavailable_subsystems(self) -> None:
        with mock.patch(
            "projio.mcp.rag.indexio_build",
        ), mock.patch(
            "projio.mcp.biblio._biblio_available", return_value=False,
        ), mock.patch(
            "projio.mcp.codio._codio_available", return_value=False,
        ):
            result = indexio_sources_sync()
        assert len(result["skipped"]) == 2
        assert any("biblio" in s for s in result["skipped"])
        assert any("codio" in s for s in result["skipped"])

    def test_triggers_build_when_requested(self) -> None:
        with mock.patch(
            "projio.mcp.biblio._biblio_available", return_value=False,
        ), mock.patch(
            "projio.mcp.codio._codio_available", return_value=False,
        ), mock.patch(
            "projio.mcp.rag.indexio_build",
            return_value={"status": "ok"},
        ) as m:
            result = indexio_sources_sync(build=True)
        m.assert_called_once()
        assert "build" in result


# ---------------------------------------------------------------------------
# indexio_build
# ---------------------------------------------------------------------------


class TestIndexioBuild:
    def test_foreground_build_delegates(self) -> None:
        with mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", "/fake/root"),
        ), mock.patch(
            "indexio.build.build_index", create=True,
            return_value={"built": True, "source_stats": {}},
        ) as m:
            result = indexio_build(sources=["notes"])
        m.assert_called_once_with(
            config_path="/fake/config.yaml",
            root="/fake/root",
            sources_filter=["notes"],
            verbose=False,
        )
        assert result["built"] is True

    def test_update_mode_skips_when_uptodate(self) -> None:
        with mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", "/fake/root"),
        ), mock.patch(
            "projio.mcp.rag._resolve_update_sources",
            return_value=[],
        ):
            result = indexio_build(update=True)
        assert result["status"] == "up_to_date"


# ---------------------------------------------------------------------------
# indexio_build_status
# ---------------------------------------------------------------------------


class TestIndexioBuildStatus:
    def test_missing_job_returns_error(self, tmp_path: Path) -> None:
        with mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", str(tmp_path)),
        ):
            result = indexio_build_status("nonexistent-job")
        assert "error" in result

    def test_completed_job_returns_result(self, tmp_path: Path) -> None:
        job_id = "build-test123"
        progress_path = tmp_path / ".projio" / "indexio" / "jobs" / f"{job_id}.json"
        progress_path.parent.mkdir(parents=True)
        progress_path.write_text(json.dumps({
            "job_id": job_id,
            "status": "completed",
            "result": {"built": True},
        }))

        with mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", str(tmp_path)),
        ):
            result = indexio_build_status(job_id)
        assert result["status"] == "completed"
        assert result["result"]["built"] is True

    def test_crashed_job_detected(self, tmp_path: Path) -> None:
        job_id = "build-crash"
        progress_path = tmp_path / ".projio" / "indexio" / "jobs" / f"{job_id}.json"
        progress_path.parent.mkdir(parents=True)
        progress_path.write_text(json.dumps({
            "job_id": job_id,
            "status": "running",
            "pid": 999999999,  # non-existent PID
        }))

        with mock.patch(
            "projio.mcp.rag._get_config",
            return_value=("/fake/config.yaml", str(tmp_path)),
        ):
            result = indexio_build_status(job_id)
        assert result["status"] == "failed"
        assert "crashed" in result.get("error", "").lower()
