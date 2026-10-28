"""``projio skills usage``: how often each skill is used, read from Claude Code transcripts.

Claude Code keeps one JSONL transcript per session under
``~/.claude/projects/<slug>/`` (``<slug>`` is the project path with every
character outside ``[A-Za-z0-9]`` turned into ``-``), and subagent transcripts
under ``<session>/subagents/``. A skill use shows up as either

- a ``Skill`` tool call (``tool_use`` block, ``input.skill``), or
- a user slash command (``<command-name>/name</command-name>`` in a user turn).

A forked or resumed session is a new file that repeats the earlier records with
their original ``uuid`` and tool-use ``id``, and starts with the same first
prompt. So each event is counted once by its id, and files that share a first
prompt count as one session. The report is read-only.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_COMMAND_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")


def transcripts_dir(root: str | Path) -> Path:
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(root).expanduser().resolve()))
    return base / "projects" / slug


def parse_since(value: str | None, now: datetime | None = None) -> datetime | None:
    """``30d``, ``6w``, ``12h`` or an ISO date (``2026-10-01``)."""
    if not value:
        return None
    now = now or datetime.now(timezone.utc)
    m = re.fullmatch(r"(\d+)([hdw])", value.strip())
    if m:
        n, unit = int(m.group(1)), m.group(2)
        return now - {"h": timedelta(hours=n), "d": timedelta(days=n), "w": timedelta(weeks=n)}[unit]
    dt = datetime.fromisoformat(value.strip())
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _timestamp(rec: dict[str, Any]) -> datetime | None:
    ts = rec.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _records(path: Path):
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if isinstance(rec, dict):
                    yield rec
    except OSError:
        return


def _first_prompt(path: Path) -> str | None:
    for rec in _records(path):
        if rec.get("type") == "user" and not rec.get("isMeta"):
            text = _text((rec.get("message") or {}).get("content"))
            if text.strip():
                return text
    return None


def known_skills(root: Path) -> dict[str, str]:
    """Skill name -> status (``synced``, ``disabled`` or ``own``) for this project."""
    from .skills import disabled_skills, is_disabled

    names: dict[str, str] = {}
    old = os.environ.get("PROJIO_ROOT")
    os.environ["PROJIO_ROOT"] = str(root)
    try:
        from projio.mcp.context import _discover_skills
        discovered = _discover_skills(root)
    except Exception:
        discovered = []
    finally:
        if old is None:
            os.environ.pop("PROJIO_ROOT", None)
        else:
            os.environ["PROJIO_ROOT"] = old
    disabled = disabled_skills(root)
    for s in discovered:
        names[s["name"]] = "disabled" if is_disabled(s["name"], disabled) else "synced"
    skills_dir = root / ".claude" / "skills"
    if skills_dir.is_dir():
        for d in skills_dir.iterdir():
            if (d / "SKILL.md").is_file():
                names.setdefault(d.name, "own")
    return names


def skill_usage(root: str | Path, *, since: datetime | None = None,
                transcripts: str | Path | None = None) -> dict[str, Any]:
    """Count skill uses per skill: tool calls, slash commands, distinct sessions, last use."""
    root = Path(root).expanduser().resolve()
    tdir = Path(transcripts) if transcripts else transcripts_dir(root)
    known = known_skills(root)
    result: dict[str, Any] = {"transcripts": str(tdir), "since": since.isoformat() if since else None,
                              "sessions": 0, "skills": []}
    if not tdir.is_dir():
        result["error"] = f"no transcripts at {tdir}"
        return result

    # one session per first prompt: forks and resumes start with the same one
    session_of: dict[str, str] = {}
    for f in sorted(tdir.glob("*.jsonl")):
        session_of[f.stem] = _first_prompt(f) or f.stem

    seen: set[str] = set()
    calls: list[tuple[str, str, str, datetime | None]] = []      # (kind, skill, session, time)
    active: set[str] = set()
    for f in sorted(tdir.glob("*.jsonl")):
        session = session_of[f.stem]
        files = [f, *sorted((tdir / f.stem / "subagents").glob("*.jsonl"))]
        for path in files:
            for rec in _records(path):
                ts = _timestamp(rec)
                if since and (ts is None or ts < since):
                    continue
                if rec.get("type") in ("user", "assistant"):
                    active.add(session)
                content = (rec.get("message") or {}).get("content")
                if rec.get("type") == "assistant" and isinstance(content, list):
                    for b in content:
                        if not (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill"):
                            continue
                        name = (b.get("input") or {}).get("skill")
                        key = b.get("id") or f"{rec.get('uuid')}:{name}"
                        if name and key not in seen:
                            seen.add(key)
                            calls.append(("call", str(name), session, ts))
                elif rec.get("type") == "user" and not rec.get("isMeta"):
                    m = _COMMAND_RE.search(_text(content))
                    key = rec.get("uuid") or ""
                    if m and key not in seen:
                        seen.add(key)
                        calls.append(("slash", m.group(1), session, ts))

    called = {name for kind, name, _, _ in calls if kind == "call"}
    rows: dict[str, dict[str, Any]] = {}
    for kind, name, session, ts in calls:
        if kind == "slash" and name not in known and name not in called:
            continue                                  # a built-in command (/clear, /model), not a skill
        row = rows.setdefault(name, {"skill": name, "calls": 0, "slash": 0, "sessions": set(), "last": None})
        row["calls" if kind == "call" else "slash"] += 1
        row["sessions"].add(session)
        if ts and (row["last"] is None or ts > row["last"]):
            row["last"] = ts
    for name, status in known.items():
        rows.setdefault(name, {"skill": name, "calls": 0, "slash": 0, "sessions": set(), "last": None})
    out = []
    for row in rows.values():
        out.append({"skill": row["skill"], "status": known.get(row["skill"], "other"),
                    "calls": row["calls"], "slash": row["slash"], "uses": row["calls"] + row["slash"],
                    "sessions": len(row["sessions"]),
                    "last_used": row["last"].date().isoformat() if row["last"] else None})
    out.sort(key=lambda r: (-r["uses"], -r["sessions"], r["skill"]))
    result["sessions"] = len(active)
    result["skills"] = out
    return result


def print_usage(root: str | Path, *, since: str | None = None, unused: bool = False,
                as_json: bool = False, transcripts: str | None = None) -> int:
    res = skill_usage(root, since=parse_since(since), transcripts=transcripts)
    if as_json:
        print(json.dumps(res, indent=1))
        return 0
    if res.get("error"):
        print(f"[!] {res['error']}")
        return 1
    rows = [r for r in res["skills"] if (r["uses"] == 0) == unused]
    window = f"since {res['since'][:10]}" if res["since"] else "all time"
    print(f"{res['sessions']} sessions ({window}), from {res['transcripts']}")
    if unused:
        print("Skills with 0 uses in the window (retirement or skills.disabled candidates):")
        for r in rows:
            print(f"  {r['skill']:<32} {r['status']}")
        return 0
    width = max([len(r["skill"]) for r in rows] + [5])
    print(f"{'skill':<{width}}  {'calls':>5}  {'slash':>5}  {'sessions':>8}  {'last used':<10}  status")
    for r in rows:
        print(f"{r['skill']:<{width}}  {r['calls']:>5}  {r['slash']:>5}  {r['sessions']:>8}  "
              f"{r['last_used'] or '-':<10}  {r['status']}")
    n_unused = sum(1 for r in res["skills"] if r["uses"] == 0)
    if n_unused:
        print(f"{n_unused} known skills unused in the window; list them with --unused.")
    return 0
