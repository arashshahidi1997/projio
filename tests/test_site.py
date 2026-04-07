"""Tests for projio.site — framework detection, port management, server lifecycle."""
from __future__ import annotations

import json
import os
import signal
from pathlib import Path
from unittest import mock

import pytest
import yaml

from projio.site import (
    _is_port_free,
    _mkdocs_config_with_chatbot,
    _pid_alive,
    _prune_dead,
    _read_servers,
    _write_servers,
    detect_framework,
    find_free_port,
    list_servers,
    serve,
    stop,
    stop_all,
)


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------

class TestDetectFramework:
    def test_mkdocs_yml(self, tmp_path: Path) -> None:
        (tmp_path / "mkdocs.yml").write_text("site_name: test\n")
        assert detect_framework(tmp_path) == "mkdocs"

    def test_mkdocs_yaml(self, tmp_path: Path) -> None:
        (tmp_path / "mkdocs.yaml").write_text("site_name: test\n")
        assert detect_framework(tmp_path) == "mkdocs"

    def test_sphinx_conf_py(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "conf.py").write_text("project = 'test'\n")
        assert detect_framework(tmp_path) == "sphinx"

    def test_sphinx_makefile(self, tmp_path: Path) -> None:
        (tmp_path / "Makefile").write_text("html:\n\tsphinx-build -b html docs docs/_build\n")
        assert detect_framework(tmp_path) == "sphinx"

    def test_vite_root(self, tmp_path: Path) -> None:
        pkg = {"devDependencies": {"vite": "^5.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        assert detect_framework(tmp_path) == "vite"

    def test_vite_docs_dir(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        pkg = {"dependencies": {"react-scripts": "5.0.0"}}
        (tmp_path / "docs" / "package.json").write_text(json.dumps(pkg))
        assert detect_framework(tmp_path) == "vite"

    def test_unknown(self, tmp_path: Path) -> None:
        assert detect_framework(tmp_path) == "unknown"

    def test_mkdocs_wins_over_sphinx(self, tmp_path: Path) -> None:
        (tmp_path / "mkdocs.yml").write_text("site_name: test\n")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "conf.py").write_text("project = 'test'\n")
        assert detect_framework(tmp_path) == "mkdocs"


# ---------------------------------------------------------------------------
# Port management
# ---------------------------------------------------------------------------

class TestPortManagement:
    def test_is_port_free_finds_available(self) -> None:
        # Port 0 lets OS pick, but we test the logic with a high port
        assert isinstance(_is_port_free(0, "127.0.0.1"), bool)

    def test_find_free_port_returns_int(self) -> None:
        port = find_free_port(base=49152, host="127.0.0.1")
        assert isinstance(port, int)
        assert port >= 49152

    def test_find_free_port_exhausted(self) -> None:
        with mock.patch("projio.site._is_port_free", return_value=False):
            with pytest.raises(RuntimeError, match="No free port"):
                find_free_port(base=8000, max_attempts=3)


# ---------------------------------------------------------------------------
# Server state persistence
# ---------------------------------------------------------------------------

class TestServerState:
    def test_read_empty(self, tmp_path: Path) -> None:
        assert _read_servers(tmp_path) == []

    def test_write_and_read(self, tmp_path: Path) -> None:
        (tmp_path / ".projio").mkdir()
        records = [{"pid": os.getpid(), "port": 8000, "framework": "mkdocs",
                     "root": str(tmp_path), "started_at": "2026-01-01T00:00:00",
                     "command": ["test"]}]
        _write_servers(tmp_path, records)
        result = _read_servers(tmp_path)
        assert len(result) == 1
        assert result[0]["port"] == 8000

    def test_prune_dead_removes_stale(self) -> None:
        servers = [
            {"pid": 99999999, "port": 8000},  # almost certainly dead
        ]
        pruned = _prune_dead(servers)
        assert len(pruned) == 0

    def test_prune_keeps_alive(self) -> None:
        servers = [{"pid": os.getpid(), "port": 8000}]
        pruned = _prune_dead(servers)
        assert len(pruned) == 1


# ---------------------------------------------------------------------------
# Serve (background mode with mocked Popen)
# ---------------------------------------------------------------------------

class TestServeBackground:
    def test_serve_background(self, tmp_path: Path) -> None:
        (tmp_path / "mkdocs.yml").write_text("site_name: test\n")
        (tmp_path / ".projio").mkdir()

        mock_proc = mock.MagicMock()
        mock_proc.pid = 12345

        with mock.patch("projio.site.subprocess.Popen", return_value=mock_proc) as popen_mock, \
             mock.patch("projio.site.find_free_port", return_value=8001), \
             mock.patch(
                 "projio.site._load_site_config",
                 return_value={"base_port": 8000, "host": "127.0.0.1", "framework": None, "chatbot": {}},
             ):
            result = serve(tmp_path, background=True)

        assert result["pid"] == 12345
        assert result["port"] == 8001
        assert result["framework"] == "mkdocs"
        assert "http://" in result["url"]
        popen_mock.assert_called_once()

    def test_serve_unknown_framework_raises(self, tmp_path: Path) -> None:
        with mock.patch(
            "projio.site._load_site_config",
            return_value={"base_port": 8000, "host": "127.0.0.1", "framework": None, "chatbot": {}},
        ):
            with pytest.raises(RuntimeError, match="Could not detect"):
                serve(tmp_path, background=True)

    def test_serve_background_starts_chatbot_when_enabled(self, tmp_path: Path) -> None:
        (tmp_path / "mkdocs.yml").write_text("site_name: test\n")
        (tmp_path / ".projio").mkdir()

        mock_site_proc = mock.MagicMock()
        mock_site_proc.pid = 12345
        mock_chat_proc = mock.MagicMock()
        mock_chat_proc.pid = 23456

        with mock.patch(
            "projio.site.subprocess.Popen",
            side_effect=[mock_site_proc, mock_chat_proc],
        ) as popen_mock, mock.patch(
            "projio.site.find_free_port",
            side_effect=[8001, 9101],
        ), mock.patch(
            "projio.site._load_site_config",
            return_value={
                "framework": None,
                "base_port": 8000,
                "host": "127.0.0.1",
                "chatbot": {
                    "enabled": True,
                    "backend_url": None,
                    "host": "127.0.0.1",
                    "port": 9100,
                    "title": "Docs Assistant",
                    "storage_key": "test_chat_v1",
                    "indexio_config": ".indexio/config.yaml",
                    "corpus": None,
                    "store": None,
                },
            },
        ), mock.patch("projio.site.importlib.util.find_spec", return_value=object()):
            result = serve(tmp_path, background=True)

        assert result["pid"] == 12345
        assert result["url"] == "http://127.0.0.1:8001"
        assert result["chatbot_url"] == "http://127.0.0.1:9101"
        assert popen_mock.call_count == 2

    def test_serve_uses_configured_framework(self, tmp_path: Path) -> None:
        (tmp_path / ".projio").mkdir()
        mock_proc = mock.MagicMock()
        mock_proc.pid = 12345
        with mock.patch("projio.site.subprocess.Popen", return_value=mock_proc) as popen_mock, mock.patch(
            "projio.site.find_free_port",
            return_value=4173,
        ), mock.patch(
            "projio.site._load_site_config",
            return_value={
                "framework": "vite",
                "base_port": 4173,
                "host": "127.0.0.1",
                "vite": {"app_dir": ".", "build_dir": "site"},
                "chatbot": {},
            },
        ):
            result = serve(tmp_path, background=True)
        assert result["framework"] == "vite"
        popen_mock.assert_called_once()


def test_mkdocs_config_with_chatbot_adds_hook(tmp_path: Path) -> None:
    (tmp_path / "mkdocs.yml").write_text("site_name: test\nnav:\n  - Home: index.md\n", encoding="utf-8")
    cfg_path = _mkdocs_config_with_chatbot(
        tmp_path,
        backend_url="http://127.0.0.1:9101",
        title="Docs Assistant",
        storage_key="proj_chat_v1",
    )
    assert cfg_path.exists()
    payload = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert ".projio/site/indexio_chat_hook.py" in payload["hooks"]
    hook_path = tmp_path / ".projio" / "site" / "indexio_chat_hook.py"
    assert hook_path.exists()


def test_build_vite_uses_projio_site_output_dir(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps({"devDependencies": {"vite": "^5.0"}}), encoding="utf-8")
    run_result = mock.MagicMock()
    run_result.returncode = 0
    with mock.patch("projio.site.subprocess.run", return_value=run_result) as run_mock, mock.patch(
        "projio.site._load_site_config",
        return_value={
            "framework": "vite",
            "output_dir": "site",
            "base_port": 8000,
            "host": "127.0.0.1",
            "vite": {"app_dir": ".", "build_dir": "site"},
            "chatbot": {},
        },
    ):
        from projio.site import build

        build(tmp_path)
    cmd = run_mock.call_args.kwargs["args"] if "args" in run_mock.call_args.kwargs else run_mock.call_args.args[0]
    assert cmd[:3] == ["npx", "vite", "build"]
    assert "--outDir" in cmd


# ---------------------------------------------------------------------------
# Stop / list / stop_all
# ---------------------------------------------------------------------------

class TestStopAndList:
    def _seed_servers(self, tmp_path: Path, pid: int = 12345) -> None:
        (tmp_path / ".projio").mkdir(exist_ok=True)
        records = [{"pid": pid, "port": 8001, "framework": "mkdocs",
                     "root": str(tmp_path), "started_at": "2026-01-01T00:00:00",
                     "command": ["test"]}]
        _write_servers(tmp_path, records)

    def test_stop_by_port(self, tmp_path: Path) -> None:
        self._seed_servers(tmp_path, pid=os.getpid())
        with mock.patch("os.kill") as kill_mock:
            result = stop(tmp_path, port=8001)
        assert result["stopped"] is True
        assert result["port"] == 8001
        # os.kill is called twice: once for prune check (sig 0), once for SIGTERM
        kill_mock.assert_any_call(os.getpid(), signal.SIGTERM)

    def test_stop_not_found(self, tmp_path: Path) -> None:
        result = stop(tmp_path, port=9999)
        assert result["stopped"] is False

    def test_list_servers_empty(self, tmp_path: Path) -> None:
        assert list_servers(tmp_path) == []

    def test_stop_all(self, tmp_path: Path) -> None:
        self._seed_servers(tmp_path, pid=os.getpid())
        with mock.patch("os.kill"):
            result = stop_all(tmp_path)
        assert result["stopped"] == 1
        assert list_servers(tmp_path) == []
