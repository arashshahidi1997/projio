"""The project-manager skill's helper scripts, run against a throwaway git repo."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HELPERS = Path(__file__).resolve().parents[1] / "src" / "projio" / "data" / "skills" / "project-manager"
LONG = "Details of the problem, long enough not to count as a stub. " * 5


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def _note(repo: Path, kind: str, ts: str, title: str, status: str = "open", body: str = LONG) -> Path:
    p = repo / "docs" / "log" / kind / f"{kind}-arash-{ts}-000000.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f'---\ntitle: "{title}"\nstatus: {status}\ntimestamp: {ts}-000000\n---\n\n{body}\n')
    return p


def _run(repo: Path, script: str, *args: str) -> str:
    return subprocess.run([sys.executable, str(HELPERS / script), *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.org")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / ".projio").mkdir()
    (tmp_path / ".projio" / "manager.yml").write_text(
        'prefix: "demo-"\n'
        'incoming:\n  body_markers: ["### Source context:"]\n  open_statuses: [open, partial]\n'
        "units:\n  - {name: core, paths: [src]}\n  - {name: notes, paths: [docs/log]}\n")
    return tmp_path


def test_incoming_senders_states_and_flags(repo: Path) -> None:
    _note(repo, "issue", "20261101-100000", "[from alpha] old bug", status="partial")
    _note(repo, "issue", "20261102-100000", "plain title", body=LONG + "\n### Source context: beta\n")
    _note(repo, "issue", "20261103-100000", "[from alpha] closed one", status="done")
    _note(repo, "idea", "20261104-100000", "no sender at all")
    _note(repo, "idea", "20261105-100000", "[from gamma] short", body="cut off")
    _note(repo, "idea", "20261105-100500", "[from delta, R12] same text twice")
    _note(repo, "idea", "20261105-101000", "[from delta, R12] same text twice")
    _git(repo, "add", "docs/log/issue")
    _git(repo, "commit", "-q", "-m", "docs(issue): progress on 20261101-100000 (first part)")

    out = json.loads(_run(repo, "incoming.py", "--json"))
    notes = {n["id"]: n for n in out["notes"]}
    assert set(notes) == {"20261101-100000", "20261102-100000", "20261105-100000",
                          "20261105-100500", "20261105-101000"}
    assert notes["20261101-100000"]["sender"] == "alpha"
    assert notes["20261101-100000"]["state"] == "committed"
    assert notes["20261101-100000"]["cited"][0].startswith("commit ")
    assert notes["20261102-100000"]["sender"] == "beta"
    assert notes["20261105-100000"]["state"] == "UNCOMMITTED"
    assert "stub" in notes["20261105-100000"]["flags"]
    assert notes["20261105-101000"]["sender"] == "delta"
    assert any(f.startswith("dup?") for f in notes["20261105-101000"]["flags"])

    every = json.loads(_run(repo, "incoming.py", "--all", "--json"))
    assert "20261104-100000" in {n["id"] for n in every["notes"]}


def test_round_watermark_and_units(repo: Path) -> None:
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("x = 1\n")
    _git(repo, "add", "src/a.py")
    _git(repo, "commit", "-q", "-m", "feat: first")
    sha = _git(repo, "rev-parse", "HEAD").strip()
    h = repo / "docs" / "log" / "handoff" / "handoff-arash-20261105-090000-000000.md"
    h.parent.mkdir(parents=True)
    h.write_text(f"---\ntitle: manager\nseries: manager\nstatus: open\ngit_commit: {sha}\n---\n")
    (repo / "src" / "a.py").write_text("x = 2\n")
    _git(repo, "commit", "-q", "-am", "fix: second")
    (repo / "src" / "b.py").write_text("y = 1\n")

    out = _run(repo, "round.py")
    assert "manager" in out.split("## since")[0]                   # the open manager series is listed
    since = out.split("## since")[1].split("## dirty")[0]
    assert "1 commits" in since and "fix: second" in since and "feat: first" not in since
    assert "[core]" in since
    dirty = out.split("## dirty")[1]
    assert "core" in dirty and "src/b.py" in dirty and "notes" in dirty
