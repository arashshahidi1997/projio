"""Kickoffs as data (skill project-manager): one file per kickoff instead of hand-kept board text.

A kickoff is `<kickoffs.dir>/<CODE>.md` (default `.scratch/kickoffs/`, next to the board, gitignored): YAML
frontmatter, then the prompt as the body, exactly as it is sent to the new session.

  ---
  code: BASE
  title: "inf-server · BASE · ASUS server baseline"   # the session title: <prefix><unit> · <CODE> · <item>
  unit: server                                       # the collision unit (`units` in the manager config)
  depends_on: [STACK, "user:sudo window"]            # kickoff codes (met when done) or "user:<what>" (never met)
  status: proposed                                   # proposed | started | done | retired
  session_id: ""                                     # set by `kickoff start`
  started_at: ""                                     # YYYY-MM-DD HH:MM, set by `kickoff start`
  rank: 1                                            # order under "Recommended now"; empty = after the ranked
  use_worktree: false                                # for start_session
  background: ""                                     # for start_session ("fresh" needs >= 80 characters)
  why: ""                                            # optional: why now, shown under Recommended now
  note: ""                                           # optional: one line shown under the tag line
  ---
  Title this session `inf-server · BASE · ASUS server baseline`. …

Commands (through round.py):

  round.py kickoff list                         every kickoff: code, status, rank, unit, depends_on, title
  round.py kickoff show <CODE> [--json]         the kickoff as the board shows it; --json gives
                                                {title, prompt, background, use_worktree} for start_session
  round.py kickoff new <CODE> [--unit U] [--item TEXT | --title T] [--depends A,user:x] [--rank N]
                                                a new proposed kickoff with a prompt skeleton to fill in
  round.py kickoff check <CODE>                the collision guard alone (exit 1 with the reason), before start_session
  round.py kickoff start <CODE> --session <id> [--force]
                                                mark it started; refuses (exit 1, with the reason) when the unit
                                                has uncommitted paths or another started kickoff writes the unit
  round.py kickoff done <CODE>                  mark it done (met for kickoffs that depend on it)
  round.py kickoff retire <CODE>                mark it retired (dropped or merged elsewhere)

`round.py board` renders Delegate from these files between auto markers: "Recommended now" on top and the
kickoffs (`### <CODE> · <title without the code>`, tag line, ```text block) after the hand-written text.
Kickoffs closed (done or retired) since the newest manager handoff show as one "Closed:" line; once a newer
manager handoff exists (it records them) they drop off the board. The files stay. `user:` dependencies are
never met automatically: the manager deletes the entry from `depends_on` once the user has done the thing.
The frontmatter is read with PyYAML when importable, else with _common's small reader plus `|` block scalars.
"""

from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import git, kickoffs_dir, read_yaml, unit_of  # noqa: E402

FIELDS = ["code", "title", "unit", "depends_on", "status", "session_id", "started_at", "rank", "use_worktree",
          "background", "why", "note"]
STATUSES = ("proposed", "started", "done", "retired")
CODE = re.compile(r"^[A-Za-z0-9]{2,5}$")  # what the worklog hub's Launch parser accepts after ###
FRONT = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)\Z", re.S)
PLAIN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-/]*$")
RESERVED = {"true", "false", "yes", "no", "on", "off", "null", "none", "~"}


# ---- files ----

def _block_scalars(text: str) -> tuple[str, dict]:
    """Pull `key: |` / `key: |-` blocks out of a frontmatter (the fallback reader has no multi-line scalars)."""
    lines, out, blocks, i = text.splitlines(), [], {}, 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*\|([+-]?)\s*$", lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        body, i = [], i + 1
        while i < len(lines) and (not lines[i].strip() or lines[i][:1] in " \t"):
            body.append(lines[i])
            i += 1
        while body and not body[-1].strip():
            body.pop()
        ind = min((len(b) - len(b.lstrip()) for b in body if b.strip()), default=0)
        val = "\n".join(b[ind:] for b in body)
        blocks[m.group(1)] = val if m.group(2) == "-" else val + "\n"
    return "\n".join(out), blocks


def parse(text: str) -> tuple[dict, str]:
    """(frontmatter, body) of a kickoff file; body is everything after the closing `---`."""
    m = FRONT.match(text)
    if not m:
        return {}, text
    raw, body = m.group(1), m.group(2)
    try:
        import yaml
        fm = yaml.safe_load(raw) or {}
    except ImportError:
        rest, blocks = _block_scalars(raw)
        fm = read_yaml(rest) or {}
        fm.update(blocks)
    fm = {k: (v.isoformat(sep=" ") if isinstance(v, dt.datetime) else v.isoformat() if isinstance(v, dt.date) else v)
          for k, v in fm.items()}
    return fm, body


def _q(v) -> str:
    """A YAML scalar that both PyYAML and _common.read_yaml read back unchanged."""
    if v is None:
        return '""'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if PLAIN.match(s) and s.lower() not in RESERVED:
        return s
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def dump(fm: dict, body: str) -> str:
    out = ["---"]
    for k in FIELDS + sorted(k for k in fm if k not in FIELDS):
        if k not in fm:
            continue
        v = fm[k]
        if isinstance(v, list):
            out.append("%s: [%s]" % (k, ", ".join(_q(x) for x in v)))
        elif isinstance(v, str) and "\n" in v.strip("\n"):
            out.append("%s: |%s" % (k, "" if v.endswith("\n") else "-"))
            out += [("  " + line) if line else "" for line in v.rstrip("\n").split("\n")]
        else:
            out.append("%s: %s" % (k, _q(v)))
    out.append("---")
    return "\n".join(out) + "\n" + body.lstrip("\n")


def load_all(cfg: dict) -> list[dict]:
    """Every kickoff, each a dict of its frontmatter plus `_body` and `_path`; sorted by code."""
    out = []
    for f in sorted(glob.glob(os.path.join(kickoffs_dir(cfg), "*.md"))):
        with open(f, encoding="utf-8") as fh:
            fm, body = parse(fh.read())
        fm["code"] = str(fm.get("code") or os.path.basename(f)[:-3])
        fm.setdefault("status", "proposed")
        deps = fm.get("depends_on") or []
        fm["depends_on"] = [str(d) for d in (deps if isinstance(deps, list) else [deps])]
        fm["_body"], fm["_path"] = body, f
        out.append(fm)
    return out


def find(cfg: dict, code: str) -> dict | None:
    return next((k for k in load_all(cfg) if str(k["code"]).lower() == code.lower()), None)


def save(k: dict) -> None:
    fm = {key: v for key, v in k.items() if not key.startswith("_")}
    with open(k["_path"], "w", encoding="utf-8") as fh:
        fh.write(dump(fm, k["_body"]))


# ---- what the board shows ----

def heading(k: dict) -> str:
    """`### <CODE> · <title without its CODE part>`: `inf-server · BASE · ASUS…` → `### BASE · inf-server · ASUS…`."""
    code, title = str(k["code"]), str(k.get("title") or "")
    parts = title.split(" · ")
    rest = " · ".join(parts[:1] + parts[2:]) if len(parts) >= 3 and parts[1].strip() == code else title
    return "### %s · %s" % (code, rest or code)


def unmet(k: dict, by_code: dict) -> list[str]:
    """depends_on entries not met: a code whose kickoff is not done, and every `user:` entry."""
    out = []
    for d in k["depends_on"]:
        if d.startswith("user:"):
            out.append("you: " + d[5:].strip())
            continue
        dep = by_code.get(d.lower())
        if not dep:
            out.append("%s (no kickoff file)" % d)
        elif dep.get("status") != "done":
            out.append("%s (%s)" % (d, dep.get("status")))
    return out


def tag(k: dict) -> str:
    deps = k["depends_on"]
    t = "**depends on %s**" % ", ".join(d.replace("user:", "you: ") for d in deps) if deps else "**independent**"
    st = k.get("status")
    if st == "started":  # no session id: the board names sessions, never their ids (core, Messaging)
        t += " · started %s" % (k.get("started_at") or "?")
    elif st == "proposed":
        t += " · proposed" + (", rank %s" % k["rank"] if k.get("rank") not in (None, "") else "")
    else:
        t += " · " + str(st)
    return t


def _fence(body: str) -> str:
    longest = max((len(m.group(0)) for m in re.finditer(r"^`{3,}", body, re.M)), default=0)
    return "`" * max(3, longest + 1)


def _rank_key(k: dict):
    r = k.get("rank")
    return (0, int(r)) if isinstance(r, int) or (isinstance(r, str) and r.isdigit()) else (1, 0), str(k["code"])


def recommended_md(kicks: list[dict]) -> str:
    by_code = {str(k["code"]).lower(): k for k in kicks}
    ready, hold = [], []
    for k in sorted((k for k in kicks if k.get("status") == "proposed"), key=_rank_key):
        u = unmet(k, by_code)
        (hold if u else ready).append((k, u))
    running = sorted((k for k in kicks if k.get("status") == "started"), key=_rank_key)
    lines = ["**Recommended now** (from the kickoff files by rank; rewritten by round.py board):", ""]
    lines += ["%d. `%s`: %s%s" % (i, k["code"], heading(k)[4 + len(str(k["code"])) + 3:],
                                  " · " + k["why"] if k.get("why") else "") for i, (k, _) in enumerate(ready, 1)]
    if not ready:
        lines.append("Nothing ready to start.")
    if running:
        lines += ["", "**Running:** " + "; ".join(
            "`%s` since %s" % (k["code"], k.get("started_at") or "?") for k in running)]
    if hold:
        lines += ["", "**Hold:** " + "; ".join("`%s` waits on %s" % (k["code"], ", ".join(u)) for k, u in hold)]
    return "<!-- auto:recommended -->\n%s\n<!-- /auto:recommended -->" % "\n".join(lines)


def closed_at(k: dict) -> dt.datetime | None:
    """When a done or retired kickoff closed: `done_at` / `retired_at`, else the file's mtime."""
    raw = str(k.get("%s_at" % k.get("status")) or "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(raw, fmt)
        except ValueError:
            pass
    try:
        return dt.datetime.fromtimestamp(os.path.getmtime(k["_path"]))
    except (KeyError, OSError):
        return None


def kickoffs_md(kicks: list[dict], since: dt.datetime | None = None) -> str:
    """The kickoff list for Delegate. `since` (the newest manager handoff's time): closed kickoffs older than it
    are left out, because that handoff records them."""
    order = {"proposed": 0, "started": 1}
    live = sorted((k for k in kicks if k.get("status") in order), key=lambda k: (order[k["status"]], _rank_key(k)))
    closed = [k for k in kicks if k.get("status") not in order
              and (since is None or (closed_at(k) or since) > since)]
    out = []
    for k in live:
        body = k["_body"].strip("\n")
        fence = _fence(body)
        out += [heading(k), "", tag(k), ""]
        if k.get("note"):
            out += [str(k["note"]), ""]
        out += [fence + "text", body, fence, ""]
    if closed:
        out.append("Closed: " + "; ".join("`%s` %s" % (k["code"], k.get("status")) for k in closed))
    if not out:
        out = ["No kickoffs. Add one with `round.py kickoff new <CODE>`."]
    return "<!-- auto:kickoffs -->\n%s\n<!-- /auto:kickoffs -->" % "\n".join(out).rstrip("\n")


# ---- the collision guard ----

def collisions(cfg: dict, k: dict, kicks: list[dict]) -> list[str]:
    """Why starting `k` now would collide: its unit has uncommitted paths, or another started kickoff writes it."""
    unit = k.get("unit")
    if not unit:
        return ["no unit in %s: set `unit:` so the collision guard can check it" % k["_path"]]
    reasons = []
    dirty = []
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        if unit_of(path, cfg["units"]) == unit:
            dirty.append(path)
    if dirty:
        reasons.append("unit %s has %d uncommitted path(s): %s%s" % (
            unit, len(dirty), ", ".join(dirty[:4]), " …" if len(dirty) > 4 else ""))
    for o in kicks:
        if o is not k and o.get("status") == "started" and o.get("unit") == unit:
            reasons.append("kickoff %s is started in unit %s (session %s)" % (o["code"], unit, o.get("session_id") or "?"))
    return reasons


# ---- the CLI ----

def _opt(argv: list[str], name: str, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def _now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def cli(argv: list[str], cfg: dict) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__.split("Commands (through round.py):", 1)[1].split("`round.py board`", 1)[0].strip("\n"))
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    kicks = load_all(cfg)
    if cmd == "list":
        if not kicks:
            print("no kickoffs in %s/" % kickoffs_dir(cfg))
        for k in sorted(kicks, key=lambda k: (STATUSES.index(k["status"]) if k["status"] in STATUSES else 9,
                                              _rank_key(k))):
            print("%-5s %-9s %-4s %-17s %-22s %s" % (k["code"], k["status"], k.get("rank") if k.get("rank") not in
                                                     (None, "") else "-", (k.get("unit") or "-")[:17],
                                                     (",".join(k["depends_on"]) or "-")[:22], k.get("title") or ""))
        return 0
    if not rest or rest[0].startswith("-"):
        print("kickoff %s: give a CODE" % cmd, file=sys.stderr)
        return 2
    code = rest[0]
    if cmd == "new":
        if not CODE.match(code):
            print("code %r: 2-5 letters or digits (the hub's Launch parser needs that)" % code, file=sys.stderr)
            return 2
        if find(cfg, code):
            print("kickoff %s exists: %s" % (code, find(cfg, code)["_path"]), file=sys.stderr)
            return 1
        unit = _opt(rest, "--unit", "")
        prefix = cfg.get("prefix") or ""
        title = _opt(rest, "--title") or "%s%s · %s · %s" % (prefix, unit or "<unit>", code, _opt(rest, "--item", "<item>"))
        rank = _opt(rest, "--rank")
        deps = [d.strip() for d in (_opt(rest, "--depends", "") or "").split(",") if d.strip()]
        fm = {"code": code, "title": title, "unit": unit, "depends_on": deps, "status": "proposed", "session_id": "",
              "started_at": "", "rank": int(rank) if rank and rank.isdigit() else None, "use_worktree": False,
              "background": ""}
        body = ("Title this session `%s`. <where to work, what to read first; files it may touch and what not to "
                "touch>\n\n<the task>\n\nVerify: <files expected to change>; tests: <command>.\n\n"
                "Commit by path, no push. Wrap: three lines to %smanager by name.\n" % (title, prefix))
        os.makedirs(kickoffs_dir(cfg), exist_ok=True)
        path = os.path.join(kickoffs_dir(cfg), code + ".md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(dump(fm, body))
        print(path)
        return 0
    k = find(cfg, code)
    if not k:
        print("no kickoff %s in %s/" % (code, kickoffs_dir(cfg)), file=sys.stderr)
        return 1
    if cmd == "show":
        if "--json" in rest:
            print(json.dumps({"title": k.get("title") or "", "prompt": k["_body"].strip("\n"),
                              "background": k.get("background") or "", "use_worktree": bool(k.get("use_worktree"))},
                             ensure_ascii=False, indent=2))
        else:
            print(kickoffs_md([k]).split("\n", 1)[1].rsplit("\n", 1)[0])
        return 0
    if cmd == "check":
        reasons = ([] if k["status"] == "proposed" else ["%s is %s, not proposed" % (code, k["status"])])
        reasons += collisions(cfg, k, kicks)
        if reasons:
            print("collides: %s\n  - %s" % (code, "\n  - ".join(reasons)), file=sys.stderr)
            return 1
        print("%s: clear to start (unit %s)" % (code, k.get("unit")))
        return 0
    if cmd == "start":
        sid = _opt(rest, "--session")
        if not sid:
            print("kickoff start: give --session <id> (from start_session)", file=sys.stderr)
            return 2
        if k["status"] != "proposed" and "--force" not in rest:
            print("refused: %s is %s, not proposed (--force to override)" % (code, k["status"]), file=sys.stderr)
            return 1
        reasons = collisions(cfg, k, kicks)
        if reasons and "--force" not in rest:
            print("refused: starting %s would collide:\n  - %s\n(--force to start anyway)" % (
                code, "\n  - ".join(reasons)), file=sys.stderr)
            return 1
        k.update(status="started", session_id=sid, started_at=_now())
        save(k)
        print("%s started (%s)%s" % (code, sid, "; forced past: " + "; ".join(reasons) if reasons else ""))
        return 0
    if cmd in ("done", "retire"):
        k["status"] = "done" if cmd == "done" else "retired"
        k[k["status"] + "_at"] = _now()
        save(k)
        print("%s %s" % (code, k["status"]))
        return 0
    print("unknown kickoff command: %s" % cmd, file=sys.stderr)
    return 2
