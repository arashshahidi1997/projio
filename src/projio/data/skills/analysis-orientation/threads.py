#!/usr/bin/env python3
"""Read-only survey of a project's analysis threads (analysis-orientation, analysis-log).

A thread is a folder under the analysis dir with an ``index.md`` state doc. This script reads the state docs'
``state_as_of`` watermarks and their Open questions sections, and compares them with the notes and commits made since.
It never writes. Standard library only; needs git for the commit counts.

Usage (from anywhere inside the repository):
    python3 threads.py                     # OVERVIEW: one row per thread
    python3 threads.py thread <key>        # THREAD: freshness of one thread (uncited notes, commits since watermark)
    python3 threads.py open                # NEXT: open O items across threads
Options: --dir <analysis dir> (default: layout.analysis in .projio/config.yml, else docs/analysis)
         --log-dir <notes dir> (default: analysis.log_dir in .projio/config.yml, else docs/log)
         --paths <p1,p2>  extra repo paths for the THREAD commit count (default: the thread's own folder plus
                          code/explore/<key>/ when it exists)
         --all            NEXT: list resolved O items too; THREAD: list older uncited notes too
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ID_RE = r"[A-Z][A-Z0-9]*-O\d+"
RESOLVED_RE = re.compile(r"\b(RESOLVED|resolved|answered|ANSWERED|closed|CLOSED|dropped|DONE)\b|~~|status:\s*(resolved|closed|dropped)")


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()
    except FileNotFoundError:
        return ""


# ---- tiny config / frontmatter readers (PyYAML when present, else a block-mapping reader) ----

def _mini_yaml(text: str) -> dict:
    """Block mappings of scalars and flow lists; enough for config keys and state-doc watermarks."""
    root: dict = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        m = re.match(r"^([A-Za-z_][\w.-]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), re.sub(r"\s+#.*$", "", m.group(2)).strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if val in ("", ">", "|", ">-", "|-"):
            parent[key] = {}
            stack.append((indent, parent[key]))
        elif val.startswith("{") and val.endswith("}"):
            parent[key] = {
                k.strip(): _scalar(v) for k, v in (p.split(":", 1) for p in _split_flow(val[1:-1]) if ":" in p)
            }
        else:
            parent[key] = _scalar(val)
    return root


def _split_flow(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def _scalar(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in _split_flow(v[1:-1]) if x.strip()]
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def load_yaml(text: str) -> dict:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return _mini_yaml(text)


def frontmatter(path: Path) -> dict:
    text = path.read_text(errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    return load_yaml(m.group(1)) if m else {}


def config(root: Path) -> dict:
    p = root / ".projio" / "config.yml"
    return load_yaml(p.read_text()) if p.is_file() else {}


# ---- state docs ----

def watermark(fm: dict) -> dict:
    wm = fm.get("state_as_of") or {}
    if not isinstance(wm, dict):
        wm = {}
    series = wm.get("series") or wm.get("notio_series") or []
    if isinstance(series, str):
        series = [series]
    return {
        "date": str(wm.get("date", "") or ""),
        "commit": str(wm.get("git_commit", "") or ""),
        "latest_note": str(wm.get("latest_note") or wm.get("latest_notio_note") or ""),
        "series": [str(s) for s in series] or ([str(fm["thread"])] if fm.get("thread") else []),
    }


def section(text: str, title_re: str) -> str:
    """Body of the first `## <title>` section matching title_re, up to the next `## `."""
    m = re.search(rf"^##\s+(?:{title_re})[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.S | re.M | re.I)
    return m.group(1) if m else ""


def thread_prefix(text: str) -> str:
    """The thread's own ID prefix: the most frequent `<KEY>` in `<KEY>-R01`-style IDs of the doc."""
    counts: dict[str, int] = {}
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for k in re.findall(r"\b([A-Z][A-Z0-9]*)-[RIDO]\d+\b", text):
        counts[k] = counts.get(k, 0) + 1
    return max(counts, key=counts.get) if counts else ""


def o_items(text: str) -> list[dict]:
    """O items in the Open questions section: an entry starts with its ID (optionally after `- ` and `**`).
    Lines that start with another thread's O ID are cross-references and are folded into the entry above."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # template examples
    prefix = thread_prefix(text)
    body = section(text, r"Open questions")
    items: list[dict] = []
    for line in body.splitlines():
        m = re.match(rf"^\s*(?:[-*]\s+)?(?:~~)?\**\s*(?:~~)?({ID_RE})\b\s*[—:-]*\s*(.*)$", line)
        if m and prefix and not m.group(1).startswith(prefix + "-"):
            m = None
        if not m:
            if items and line.strip():
                items[-1]["text"] += " " + line.strip()
            continue
        items.append({"id": m.group(1), "text": m.group(2).strip(), "line": line})
    for it in items:
        head = it["line"] + " " + it["text"][:240]
        it["resolved"] = bool(RESOLVED_RE.search(head))
        title = re.sub(r"\*\*", "", it["text"]).strip()
        it["title"] = re.split(r"(?<=[?.])\s", title, maxsplit=1)[0][:140]
        h = re.search(r"\bhypothes[ie]s:\s*([^·\n]+)", it["text"]) or re.search(r"\b(H\d+[a-z]?)\b", it["text"])
        it["hyp"] = h.group(1).strip() if h else "H?"
        it["blocked"] = bool(re.search(r"\bblocked\b|\bdepends on\b|\bwaits? (on|for)\b", it["text"], re.I))
    return items


def threads(adir: Path) -> list[Path]:
    return sorted(p.parent for p in adir.glob("*/index.md") if not p.parent.name.startswith(("_", ".")))


# ---- notes ----

def note_series(path: Path) -> list[str]:
    head = path.read_text(errors="replace")[:4000]
    m = re.search(r"^series:\s*(.+)$", head, re.M)
    if not m:
        return []
    v = _scalar(m.group(1))
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


_SERIES_CACHE: dict[Path, list[tuple[Path, list[str]]]] = {}


def _all_notes(logdir: Path) -> list[tuple[Path, list[str]]]:
    if logdir not in _SERIES_CACHE:
        _SERIES_CACHE[logdir] = [(p, note_series(p)) for p in logdir.rglob("*.md") if p.name != "index.md"] \
            if logdir.is_dir() else []
    return _SERIES_CACHE[logdir]


def note_stamp(p: Path) -> str:
    m = re.search(r"(\d{8})-(\d{6})", p.stem)
    return m.group(1) + m.group(2) if m else ""


def notes_in_series(logdir: Path, series: list[str]) -> list[Path]:
    if not series:
        return []
    want = set(series)
    out = [p for p, s in _all_notes(logdir) if want & set(s)]
    return sorted(out, key=note_stamp, reverse=True)


def newer_than(notes: list[Path], wm: dict) -> list[Path]:
    """Notes stamped after the watermark (its latest note, else its date); all notes when there is no watermark."""
    m = re.search(r"(\d{8})-(\d{6})", wm["latest_note"])
    # Without a note id, count the whole watermark day as possibly newer: flag rather than miss.
    cut = m.group(1) + m.group(2) if m else re.sub(r"\D", "", wm["date"])[:8] + "000000" if wm["date"] else ""
    return [p for p in notes if note_stamp(p) > cut] if cut else notes


def uncited(doc_text: str, notes: list[Path]) -> list[Path]:
    def cited(p: Path) -> bool:
        ts = re.search(r"\d{8}-\d{6}(?:-\d+)?", p.stem)
        return p.stem in doc_text or bool(ts and ts.group(0) in doc_text)

    return [p for p in notes if not cited(p)]


def commits_since(commit: str, paths: list[str]) -> list[str]:
    if not commit or not git("cat-file", "-t", commit):
        return []
    out = git("log", "--oneline", f"{commit}..HEAD", "--", *paths)
    return [l for l in out.splitlines() if l.strip()]


def thread_paths(root: Path, adir: Path, key: str, extra: list[str]) -> list[str]:
    doc = os.path.relpath(adir / key / "index.md", root)
    # the state doc's own edits are not deltas; other files in its folder (figures, tables) are
    paths = [os.path.relpath(adir / key, root), f":(exclude){doc}"]
    if (root / "code" / "explore" / key).is_dir():
        paths.append(f"code/explore/{key}")
    return paths + extra


# ---- modes ----

def mode_overview(root, adir, logdir, extra):
    rows = []
    for t in threads(adir):
        doc = t / "index.md"
        fm, text = frontmatter(doc), doc.read_text(errors="replace")
        wm = watermark(fm)
        items = o_items(text)
        n_open = sum(1 for i in items if not i["resolved"])
        unc = newer_than(uncited(text, notes_in_series(logdir, wm["series"])), wm)
        since = commits_since(wm["commit"], thread_paths(root, adir, t.name, extra)) if wm["commit"] else []
        rows.append((t.name, wm["date"] or "-", wm["commit"] or "-", n_open, len(unc), len(since)))
    print(f"analysis dir: {os.path.relpath(adir, root)}   notes: {os.path.relpath(logdir, root)}"
          f"{'' if logdir.is_dir() else ' (missing)'}")
    for extra_doc in ("index.md", "hypotheses.md"):
        print(f"  {extra_doc}: {'present' if (adir / extra_doc).is_file() else 'missing'}")
    if not rows:
        print("no threads yet (no <thread>/index.md)")
        return
    print(f"{'thread':24} {'as of':11} {'commit':10} {'open O':>6} {'new uncited':>11} {'commits since':>13}")
    for r in rows:
        print(f"{r[0]:24} {r[1]:11} {r[2][:10]:10} {r[3]:>6} {r[4]:>11} {r[5]:>13}")


def mode_thread(root, adir, logdir, key, extra, show_all=False):
    doc = adir / key / "index.md"
    if not doc.is_file():
        names = ", ".join(t.name for t in threads(adir)) or "none"
        print(f"no state doc {os.path.relpath(doc, root)}; threads: {names}")
        return 1
    fm, text = frontmatter(doc), doc.read_text(errors="replace")
    wm = watermark(fm)
    ver = fm.get("verification") or {}
    print(f"thread: {key}   doc: {os.path.relpath(doc, root)}")
    print(f"state_as_of: date {wm['date'] or '-'}, commit {wm['commit'] or '-'}, latest note {wm['latest_note'] or '-'}")
    print(f"series: {', '.join(wm['series']) or '-'}   verification: {ver if ver else '-'}")
    notes = notes_in_series(logdir, wm["series"])
    unc_all = uncited(text, notes)
    unc = newer_than(unc_all, wm)
    print(f"notes in series: {len(notes)}; not cited by the doc: {len(unc_all)}, "
          f"of them newer than the watermark: {len(unc)}")
    for p in (unc_all if show_all else unc)[:40]:
        ti = re.search(r'^title:\s*"?(.*?)"?\s*$', p.read_text(errors="replace")[:3000], re.M)
        print(f"  uncited: {p.stem}  {(ti.group(1) if ti else '')[:100]}")
    paths = thread_paths(root, adir, key, extra)
    if wm["commit"]:
        since = commits_since(wm["commit"], paths)
        known = bool(git("cat-file", "-t", wm["commit"]))
        print(f"commits since {wm['commit']} on {', '.join(p for p in paths if not p.startswith(':'))}"
              f" (state doc itself excluded): "
              f"{len(since) if known else 'unknown commit'}")
        for l in since[:20]:
            print(f"  {l}")
    items = o_items(text)
    print(f"O items ({thread_prefix(text) or 'no prefix'}): {sum(1 for i in items if not i['resolved'])} open, {sum(1 for i in items if i['resolved'])} resolved")
    fresh = not unc and wm["commit"] and not commits_since(wm["commit"], paths)
    print("verdict: " + ("fresh as of the watermark" if fresh else
                         f"stale: {len(unc)} newer uncited notes, "
                         + (f"{len(commits_since(wm['commit'], paths))} commits since" if wm["commit"] else "no watermark commit")
                         + "; series are often shared umbrellas, so judge thread membership by title"))
    return 0


def mode_open(root, adir, show_all):
    total = 0
    for t in threads(adir):
        text = (t / "index.md").read_text(errors="replace")
        for it in o_items(text):
            if it["resolved"] and not show_all:
                continue
            total += 1
            flag = "resolved" if it["resolved"] else ("blocked?" if it["blocked"] else "open")
            print(f"{it['id']:12} {t.name:22} {it['hyp'][:12]:12} {flag:9} {it['title']}")
    print(f"{total} {'O items' if show_all else 'open O items'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", nargs="?", default="overview", choices=["overview", "thread", "open"])
    ap.add_argument("key", nargs="?")
    ap.add_argument("--dir")
    ap.add_argument("--log-dir")
    ap.add_argument("--paths", default="")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    root = Path(git("rev-parse", "--show-toplevel") or ".").resolve()
    os.chdir(root)
    cfg = config(root)
    layout = cfg.get("layout") if isinstance(cfg.get("layout"), dict) else {}
    acfg = cfg.get("analysis") if isinstance(cfg.get("analysis"), dict) else {}
    adir = root / (a.dir or layout.get("analysis") or "docs/analysis")
    logdir = root / (a.log_dir or acfg.get("log_dir") or "docs/log")
    extra = [p for p in a.paths.split(",") if p]
    if not adir.is_dir():
        print(f"no analysis dir at {os.path.relpath(adir, root)}")
        return 1
    if a.mode == "thread":
        if not a.key:
            ap.error("thread mode needs a thread key")
        return mode_thread(root, adir, logdir, a.key, extra, a.all)
    if a.mode == "open":
        mode_open(root, adir, a.all)
        return 0
    mode_overview(root, adir, logdir, extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())
