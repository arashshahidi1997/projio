"""Tests for projio.mcp.config_gen: merging into an existing .mcp.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from projio.mcp import config_gen
from projio.mcp.config_gen import stale_managed_entries, write_mcp_config

CONDA = "/storage/share/python/environments/Anaconda3/envs/rag/bin/python"
UV = "/opt/uv-tools/projio/bin/python3"


@pytest.fixture
def no_worklog(monkeypatch):
    """Generate only the projio entry, whatever is installed here."""
    monkeypatch.setattr(config_gen.shutil, "which", lambda name: None)
    monkeypatch.setitem(sys.modules, "worklog.mcp_server", None)


def _existing(tmp_path: Path) -> Path:
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({
        "mcpServers": {
            "projio": {"command": CONDA, "args": ["-m", "projio.mcp.server"],
                       "env": {"PROJIO_ROOT": str(tmp_path)}},
            "sirocampus": {"command": CONDA, "args": ["-m", "projio.mcp.server"],
                           "env": {"PROJIO_ROOT": "/storage/share/sirocampus",
                                   "PROJIO_MCP_TOOLS": "codio,biblio,rag"}},
            "worklog": {"command": CONDA, "args": ["-m", "worklog.mcp_server"]},
            "excalidraw": {"command": "npx", "args": ["-y", "excalidraw-mcp"],
                           "env": {"PORT": "3000"}},
        },
        "otherKey": {"keep": True},
    }))
    return path


def test_rewrites_other_projio_entries_and_keeps_env(tmp_path, no_worklog):
    path = _existing(tmp_path)
    write_mcp_config(tmp_path, python_bin=UV, yes=True)
    servers = json.loads(path.read_text())["mcpServers"]

    assert servers["projio"]["command"] == UV
    assert servers["sirocampus"]["command"] == UV
    assert servers["sirocampus"]["args"] == ["-m", "projio.mcp.server"]
    assert servers["sirocampus"]["env"] == {
        "PROJIO_ROOT": "/storage/share/sirocampus",
        "PROJIO_MCP_TOOLS": "codio,biblio,rag",
    }


def test_leaves_unrelated_entries_untouched(tmp_path, no_worklog):
    path = _existing(tmp_path)
    before = json.loads(path.read_text())
    write_mcp_config(tmp_path, python_bin=UV, yes=True)
    after = json.loads(path.read_text())

    assert after["mcpServers"]["excalidraw"] == before["mcpServers"]["excalidraw"]
    assert after["otherKey"] == {"keep": True}
    # No worklog def was generated, so the existing worklog entry is not touched.
    assert after["mcpServers"]["worklog"] == before["mcpServers"]["worklog"]


def test_worklog_entry_moves_to_console_script(tmp_path, monkeypatch):
    monkeypatch.setattr(
        config_gen.shutil, "which",
        lambda name: "/home/u/.local/bin/worklog-mcp" if name == "worklog-mcp" else None,
    )
    path = _existing(tmp_path)
    data = json.loads(path.read_text())
    data["mcpServers"]["worklog-lab"] = {
        "command": CONDA, "args": ["-m", "worklog.mcp_server"], "env": {"X": "1"},
    }
    path.write_text(json.dumps(data))

    write_mcp_config(tmp_path, python_bin=UV, yes=True)
    servers = json.loads(path.read_text())["mcpServers"]

    assert servers["worklog"] == {"command": "/home/u/.local/bin/worklog-mcp", "args": []}
    assert servers["worklog-lab"] == {
        "command": "/home/u/.local/bin/worklog-mcp", "args": [], "env": {"X": "1"},
    }


def test_preview_reports_changes_and_conda_and_does_not_write(tmp_path, no_worklog, capsys):
    path = _existing(tmp_path)
    before = path.read_text()
    write_mcp_config(tmp_path, python_bin=UV, yes=False)
    out = capsys.readouterr().out

    assert path.read_text() == before
    assert f"[update] sirocampus: {CONDA} -> {UV}" in out
    assert f"[update] projio: {CONDA} -> {UV}" in out
    assert "excalidraw" not in "\n".join(l for l in out.splitlines() if "[update]" in l)
    # The untouched worklog entry still runs from conda: warned, not changed.
    assert "[warn] worklog: command runs from a conda env" in out
    assert "[warn] sirocampus" not in out


def test_fresh_file_lists_added_entries(tmp_path, no_worklog, capsys):
    write_mcp_config(tmp_path, python_bin=UV, yes=True)
    out = capsys.readouterr().out
    assert f"[add] projio: {UV}" in out
    assert json.loads((tmp_path / ".mcp.json").read_text())["mcpServers"]["projio"]["command"] == UV


def test_stale_managed_entries(tmp_path):
    path = _existing(tmp_path)
    assert stale_managed_entries(path, python_bin=UV) == ["projio", "sirocampus"]
    assert stale_managed_entries(path, python_bin=CONDA) == []
    assert stale_managed_entries(tmp_path / "missing.json") == []


def test_copilot_config_refreshes_too(tmp_path, no_worklog):
    path = tmp_path / ".vscode" / "mcp.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"servers": {
        "hub": {"command": CONDA, "args": ["-m", "projio.mcp.server"],
                "env": {"PROJIO_ROOT": "/hub"}},
    }}))
    config_gen.write_copilot_config(tmp_path, python_bin=UV)
    servers = json.loads(path.read_text())["servers"]
    assert servers["hub"]["command"] == UV
    assert servers["hub"]["env"] == {"PROJIO_ROOT": "/hub"}
