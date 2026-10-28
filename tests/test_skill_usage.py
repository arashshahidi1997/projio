"""projio skills usage: counts from Claude Code transcripts, forks counted once."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from projio import skill_usage as su


def _user(uuid, text, ts):
    return {"type": "user", "uuid": uuid, "timestamp": ts, "message": {"role": "user", "content": text}}


def _skill_call(uuid, tid, name, ts):
    return {"type": "assistant", "uuid": uuid, "timestamp": ts, "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": tid, "name": "Skill", "input": {"skill": name}}]}}


def _write(path, recs):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in recs))


def _cmd(name, args=""):
    return f"<command-message>{name}</command-message>\n<command-name>/{name}</command-name>\n<command-args>{args}</command-args>"


def test_usage_counts_calls_slash_sessions_and_dedupes_forks(tmp_path, monkeypatch):
    monkeypatch.setattr(su, "known_skills", lambda root: {"session-wrap": "synced", "px-log": "own",
                                                          "questio-next": "synced"})
    t = tmp_path / "t"
    base = [_user("u1", "start the analysis", "2026-10-01T10:00:00Z"),
            _skill_call("a1", "toolu_1", "px-log", "2026-10-01T10:01:00Z"),
            _user("u2", _cmd("session-wrap"), "2026-10-01T11:00:00Z"),
            _user("u3", _cmd("clear"), "2026-10-01T11:05:00Z")]                 # built-in, not a skill
    _write(t / "s1.jsonl", base)
    # a fork: same first prompt, repeats the records, then adds one call
    _write(t / "s1fork.jsonl", base + [_skill_call("a9", "toolu_9", "px-log", "2026-10-02T09:00:00Z")])
    # another session, with a subagent that calls a skill
    _write(t / "s2.jsonl", [_user("v1", "other work", "2026-10-20T10:00:00Z")])
    _write(t / "s2" / "subagents" / "agent-x.jsonl",
           [_skill_call("w1", "toolu_w", "marimo-pair", "2026-10-20T10:30:00Z")])

    res = su.skill_usage(tmp_path, transcripts=t)
    rows = {r["skill"]: r for r in res["skills"]}
    assert res["sessions"] == 2
    assert (rows["px-log"]["calls"], rows["px-log"]["sessions"], rows["px-log"]["last_used"]) == (2, 1, "2026-10-02")
    assert (rows["session-wrap"]["slash"], rows["session-wrap"]["calls"]) == (1, 0)
    assert rows["marimo-pair"]["status"] == "other" and rows["marimo-pair"]["calls"] == 1
    assert "clear" not in rows
    assert rows["questio-next"]["uses"] == 0

    since = su.parse_since("2026-10-10")
    res = su.skill_usage(tmp_path, transcripts=t, since=since)
    rows = {r["skill"]: r for r in res["skills"]}
    assert res["sessions"] == 1 and rows["px-log"]["uses"] == 0 and rows["marimo-pair"]["uses"] == 1


def test_parse_since_and_slug(monkeypatch, tmp_path):
    now = datetime(2026, 10, 28, tzinfo=timezone.utc)
    assert su.parse_since("30d", now) == datetime(2026, 9, 28, tzinfo=timezone.utc)
    assert su.parse_since("2w", now) == datetime(2026, 10, 14, tzinfo=timezone.utc)
    assert su.parse_since(None) is None
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    assert su.transcripts_dir("/storage2/a_b/pixecog") == tmp_path / "projects" / "-storage2-a-b-pixecog"


def test_print_usage_unused_and_missing_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(su, "known_skills", lambda root: {"questio-next": "synced"})
    _write(tmp_path / "t" / "s.jsonl", [_user("u", "hi", "2026-10-01T10:00:00Z")])
    assert su.print_usage(tmp_path, unused=True, transcripts=str(tmp_path / "t")) == 0
    assert "questio-next" in capsys.readouterr().out
    assert su.print_usage(tmp_path, transcripts=str(tmp_path / "none")) == 1
