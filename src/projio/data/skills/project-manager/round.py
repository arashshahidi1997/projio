"""What changed since the last manager round (skill project-manager). Read-only. Run from anywhere in the repo:

  python3 .claude/skills/project-manager/round.py                     # all sections
  python3 .claude/skills/project-manager/round.py handoffs since      # chosen sections
  python3 .claude/skills/project-manager/round.py since --since <sha>

Sections:
  handoffs  newest open handoff per series in `handoffs.dir`; a series with more than one open handoff is flagged
  since     commits since the watermark, with the units each touched. The watermark is `git_commit` of the
            newest `series: manager` handoff, or two days when there is none. Sessions often wrap without
            reporting, so this is how the manager sees what finished.
  dirty     uncommitted paths grouped by unit (`units` in .projio/manager.yml): two live sessions in one unit
            is a collision; subdatasets with their own uncommitted changes or a moved pointer
"""

from __future__ import annotations

import collections
import glob
import os
import sys

sys.dont_write_bytecode = True  # the synced copy of this folder must stay byte-identical
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import age, front, git, load_adapter, stamp, to_root, unit_of  # noqa: E402


def handoff_rows(cfg: dict) -> list[dict]:
    rows = []
    for f in glob.glob(os.path.join(cfg["handoffs"]["dir"], "*.md")):
        if os.path.basename(f) == "index.md":
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            fm, _ = front(fh.read())
        nid = os.path.basename(f)[:-3]
        ts = stamp(fm.get("timestamp", "") or nid)
        rows.append({"path": f, "id": ts.strftime("%Y%m%d-%H%M%S") if ts else nid, "ts": ts,
                     "series": fm.get("series", "") or "-", "status": fm.get("status", ""),
                     "title": fm.get("title", ""), "git_commit": fm.get("git_commit", "")})
    rows.sort(key=lambda r: r["id"], reverse=True)
    return rows


def show_handoffs(rows: list[dict]) -> None:
    open_by = collections.defaultdict(list)
    for r in rows:
        if r["status"] == "open":
            open_by[r["series"]].append(r)
    print("## handoffs: newest open per series (%d series)" % len(open_by))
    for series, rs in sorted(open_by.items(), key=lambda x: x[1][0]["id"], reverse=True):
        r = rs[0]
        more = "  (+%d older open: consume?)" % (len(rs) - 1) if len(rs) > 1 else ""
        print("  %-22s %s %4s  %s%s" % (series[:22], r["id"], age(r["ts"]), r["title"][:80], more))


def watermark(rows: list[dict], given: str) -> tuple[str, str]:
    if given:
        return given + "..HEAD", "given " + given
    for r in rows:
        sha = r["git_commit"]
        if r["series"] == "manager" and sha and git("cat-file", "-t", sha).strip() == "commit":
            return sha + "..HEAD", "manager handoff %s (%s)" % (r["id"], sha[:9])
    return "", "two days (no manager handoff with git_commit)"


def show_since(rows: list[dict], cfg: dict, given: str) -> None:
    rng, why = watermark(rows, given)
    args = ["log", "--format=\x1e%h %ad %s", "--date=short", "--name-only"]
    args += [rng] if rng else ["--since=2.days"]
    out = git(*args)
    commits = [c.strip().splitlines() for c in out.split("\x1e") if c.strip()]
    print("## since %s: %d commits" % (why, len(commits)))
    for c in commits:
        units = sorted({unit_of(p, cfg["units"]) for p in c[1:] if p.strip()})
        print("  %s  [%s]" % (c[0][:110], ",".join(units) or "-"))


def show_dirty(cfg: dict) -> None:
    by_unit = collections.defaultdict(list)
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        by_unit[unit_of(path, cfg["units"])].append(line[:2] + " " + path)
    print("## dirty: %d paths in %d units" % (sum(map(len, by_unit.values())), len(by_unit)))
    for u, ps in sorted(by_unit.items(), key=lambda x: -len(x[1])):
        print("  %-14s %3d  %s%s" % (u, len(ps), "; ".join(ps[:4]), " …" if len(ps) > 4 else ""))
    subs = [line.split() for line in git("submodule", "status").splitlines() if line.strip()]
    for s in subs:
        mark, path = s[0][0], s[1]
        own = len(git("status", "--porcelain", cwd=path).splitlines()) if os.path.isdir(path) else 0
        if mark == "+" or own:
            print("  subdataset %-20s %s%s" % (path, "pointer moved; " if mark == "+" else "",
                                               "%d uncommitted inside" % own if own else ""))


def main(argv: list[str]) -> int:
    to_root()
    cfg = load_adapter()
    given = ""
    if "--since" in argv:
        i = argv.index("--since")
        given = argv[i + 1] if i + 1 < len(argv) else ""
        argv = argv[:i] + argv[i + 2:]
    sections = [a for a in argv if not a.startswith("-")] or ["handoffs", "since", "dirty"]
    rows = handoff_rows(cfg)
    for s in sections:
        if s == "handoffs":
            show_handoffs(rows)
        elif s == "since":
            show_since(rows, cfg, given)
        elif s == "dirty":
            show_dirty(cfg)
        else:
            print("unknown section: " + s, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
