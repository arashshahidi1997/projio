"""Kickoffs as data in the project-manager core (kickoffs.py through round.py), stdlib unittest.

Each test runs round.py in a fresh temp git repo with a generic manager config and a hand-written board.
Brought in from inf-manager's KDAT trial; runs under pytest with the rest of the suite.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "src", "projio", "data", "skills", "project-manager")
ROUND = os.path.join(HERE, "round.py")
sys.path.insert(0, HERE)
import kickoffs  # noqa: E402

# the worklog hub's Launch parser (worklog/hub.py _KICK_HEAD): what a kickoff heading must match
HUB_HEAD = re.compile(r"^###\s+([A-Za-z0-9]{2,5})\s+[·\-–—:]\s+(.+?)\s*$")

CONFIG = """prefix: "t-"
board:
  path: .scratch/t-manager-board.md
units:
  - {name: server, paths: [server]}
  - {name: docs, paths: [docs]}
"""

BOARD = """# t-manager board

Updated 2026-01-01 00:00 on host.

## What's up

As of 2026-01-01 00:00.

- Running now: nothing.

## Delegate

Hand-written note that must survive.

## Decisions waiting for you

(none open)

## Custom section

Kept as written.
"""


def sh(*args, cwd, check=True):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, check=check)


class KickoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.d = self.tmp.name
        sh("git", "init", "-q", cwd=d)
        sh("git", "config", "user.email", "t@example.invalid", cwd=d)
        sh("git", "config", "user.name", "t", cwd=d)
        os.makedirs(os.path.join(d, ".claude"))
        os.makedirs(os.path.join(d, ".scratch"))
        os.makedirs(os.path.join(d, "server"))
        with open(os.path.join(d, ".claude/manager.yml"), "w") as fh:
            fh.write(CONFIG)
        with open(os.path.join(d, ".gitignore"), "w") as fh:
            fh.write(".scratch/\n")
        with open(os.path.join(d, ".scratch/t-manager-board.md"), "w") as fh:
            fh.write(BOARD)
        with open(os.path.join(d, "server/a.txt"), "w") as fh:
            fh.write("a\n")
        sh("git", "add", ".", cwd=d)
        sh("git", "commit", "-qm", "init", cwd=d)

    def tearDown(self):
        self.tmp.cleanup()

    def run_round(self, *args, check=True):
        return subprocess.run([sys.executable, ROUND, *args], cwd=self.d, capture_output=True, text=True, check=check)

    def board(self):
        with open(os.path.join(self.d, ".scratch/t-manager-board.md")) as fh:
            return fh.read()

    def kfile(self, code):
        return os.path.join(self.d, ".scratch/kickoffs/%s.md" % code)

    def set_body(self, code, body):
        with open(self.kfile(code)) as fh:
            fm, _ = kickoffs.parse(fh.read())
        with open(self.kfile(code), "w") as fh:
            fh.write(kickoffs.dump(fm, body))

    # ---- tests ----

    def test_new_list_show_json(self):
        out = self.run_round("kickoff", "new", "SRV", "--unit", "server", "--item", "set up the box", "--rank", "1")
        self.assertTrue(out.stdout.strip().endswith(".scratch/kickoffs/SRV.md"))
        self.assertEqual(self.run_round("kickoff", "new", "SRV", check=False).returncode, 1)  # exists
        self.assertEqual(self.run_round("kickoff", "new", "TOOLONG", check=False).returncode, 2)  # hub needs 2-5
        lst = self.run_round("kickoff", "list").stdout
        self.assertIn("SRV", lst)
        self.assertIn("proposed", lst)
        js = json.loads(self.run_round("kickoff", "show", "SRV", "--json").stdout)
        self.assertEqual(set(js), {"title", "prompt", "background", "use_worktree"})
        self.assertEqual(js["title"], "t-server · SRV · set up the box")
        self.assertTrue(js["prompt"].startswith("Title this session `t-server · SRV · set up the box`."))
        self.assertIs(js["use_worktree"], False)

    def test_board_render_and_hub_format(self):
        self.run_round("kickoff", "new", "SRV", "--unit", "server", "--item", "set up the box", "--rank", "2")
        self.run_round("kickoff", "new", "DOC", "--unit", "docs", "--item", "write docs", "--rank", "1")
        self.run_round("board")
        b = self.board()
        self.assertIn("Hand-written note that must survive.", b)
        self.assertIn("## Custom section\n\nKept as written.", b)
        delegate = b.split("## Delegate", 1)[1].split("\n## ", 1)[0]
        # Recommended now on top, by rank; hand-written in the middle; kickoffs after
        self.assertLess(delegate.index("Recommended now"), delegate.index("Hand-written note"))
        self.assertLess(delegate.index("Hand-written note"), delegate.index("### DOC"))
        rec = delegate.split("<!-- /auto:recommended -->")[0]
        self.assertLess(rec.index("`DOC`"), rec.index("`SRV`"))
        heads = [line for line in delegate.splitlines() if line.startswith("### ")]
        self.assertEqual(heads, ["### DOC · t-docs · write docs", "### SRV · t-server · set up the box"])
        for h in heads:
            self.assertTrue(HUB_HEAD.match(h), h)
        # heading, blank, tag line, blank, ```text
        lines = delegate.splitlines()
        i = lines.index("### DOC · t-docs · write docs")
        self.assertEqual(lines[i + 2], "**independent** · proposed, rank 1")
        self.assertEqual(lines[i + 4], "```text")
        # a second render changes nothing but the stamps
        first = re.sub(r"(Updated|As of) [^\n]*", "", b)
        self.run_round("board")
        self.assertEqual(first, re.sub(r"(Updated|As of) [^\n]*", "", self.board()))

    def test_depends_on_hold(self):
        self.run_round("kickoff", "new", "AAA", "--unit", "docs", "--item", "first")
        self.run_round("kickoff", "new", "BBB", "--unit", "server", "--item", "second",
                       "--depends", "AAA,user:buy a hub")
        self.run_round("board")
        rec = self.board().split("<!-- auto:recommended -->")[1].split("<!-- /auto:recommended -->")[0]
        self.assertIn("1. `AAA`", rec)
        self.assertIn("`BBB` waits on AAA (proposed), you: buy a hub", rec)
        self.assertIn("**depends on AAA, you: buy a hub**", self.board())
        self.run_round("kickoff", "done", "AAA")
        self.run_round("board")
        rec = self.board().split("<!-- auto:recommended -->")[1].split("<!-- /auto:recommended -->")[0]
        self.assertIn("`BBB` waits on you: buy a hub", rec)
        self.assertNotIn("### AAA", self.board())  # done kickoffs leave the list
        self.assertIn("Closed: `AAA` done", self.board())

    def test_start_collision_guard(self):
        self.run_round("kickoff", "new", "SRV", "--unit", "server", "--item", "one")
        self.run_round("kickoff", "new", "SR2", "--unit", "server", "--item", "two")
        self.assertEqual(self.run_round("kickoff", "start", "SRV", check=False).returncode, 2)  # no --session
        with open(os.path.join(self.d, "server/a.txt"), "a") as fh:
            fh.write("dirty\n")
        self.assertEqual(self.run_round("kickoff", "check", "SRV", check=False).returncode, 1)
        r = self.run_round("kickoff", "start", "SRV", "--session", "local_x", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("unit server has 1 uncommitted path(s): server/a.txt", r.stderr)
        sh("git", "checkout", "--", "server/a.txt", cwd=self.d)
        self.assertIn("clear to start", self.run_round("kickoff", "check", "SRV").stdout)
        self.run_round("kickoff", "start", "SRV", "--session", "local_x")
        with open(self.kfile("SRV")) as fh:
            fm, _ = kickoffs.parse(fh.read())
        self.assertEqual((fm["status"], fm["session_id"]), ("started", "local_x"))
        r = self.run_round("kickoff", "start", "SR2", "--session", "local_y", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("kickoff SRV is started in unit server", r.stderr)
        self.run_round("kickoff", "start", "SR2", "--session", "local_y", "--force")
        self.assertEqual(self.run_round("kickoff", "start", "SRV", "--session", "z", check=False).returncode, 1)
        self.run_round("kickoff", "retire", "SR2")
        self.assertIn("retired", self.run_round("kickoff", "list").stdout)

    def test_prompt_with_fences_and_headings(self):
        self.run_round("kickoff", "new", "FNC", "--unit", "docs", "--item", "tricky")
        body = "Title this session `t-docs · FNC · tricky`.\n\n## Not a board section\n\n```bash\nls\n```\n"
        self.set_body("FNC", body)
        self.run_round("board")
        b = self.board()
        self.assertIn("````text\n" + body.rstrip("\n") + "\n````", b)
        self.assertNotIn("## Not a board section\n\n```bash", b.split("````text")[0])
        self.run_round("board")  # the "## " inside the prompt must not become a section
        self.assertEqual(self.board().count("## Not a board section"), 1)
        self.assertEqual(self.board().count("## Decisions waiting for you"), 1)

    def handoff(self, ts, series="manager"):
        d = os.path.join(self.d, "docs/handoffs")  # handoffs.dir of the generic layout
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "handoff-t-%s-%s.md" % (ts, series)), "w") as fh:
            fh.write('---\ntitle: "h"\nseries: %s\nstatus: open\ntimestamp: %s-000000\n---\n\nbody\n' % (series, ts))

    def test_closed_line_until_next_manager_handoff(self):
        self.run_round("kickoff", "new", "AAA", "--unit", "docs", "--item", "first")
        self.run_round("kickoff", "new", "BBB", "--unit", "server", "--item", "second")
        self.handoff("20200101-000000")  # an old manager handoff: AAA closed after it
        self.run_round("kickoff", "done", "AAA")
        self.run_round("board")
        self.assertIn("Closed: `AAA` done", self.board())
        self.handoff("29990101-000000", series="core")  # not a manager handoff: changes nothing
        self.run_round("board")
        self.assertIn("Closed: `AAA` done", self.board())
        self.handoff("29990101-000000")  # the next manager handoff records AAA: it drops off
        self.run_round("board")
        self.assertNotIn("Closed:", self.board())
        self.assertIn("### BBB", self.board())
        self.assertIn("done", self.run_round("kickoff", "list").stdout)  # the file stays

    def test_board_without_kickoff_files_as_before(self):
        self.run_round("board")
        b = self.board()
        self.assertNotIn("auto:kickoffs", b)
        self.assertNotIn("auto:recommended", b)
        self.assertIn("**Recommended now** (the manager's pick", b)  # the 0.5.0 placeholder
        self.assertIn("Hand-written note that must survive.", b)

    def test_new_skeleton_has_verify_and_report(self):
        self.run_round("kickoff", "new", "SRV", "--unit", "server", "--item", "box")
        prompt = json.loads(self.run_round("kickoff", "show", "SRV", "--json").stdout)["prompt"]
        self.assertIn("Verify: ", prompt)
        self.assertIn("three lines to t-manager by name", prompt)

    def test_frontmatter_roundtrip_without_pyyaml(self):
        fm = {"code": "XYZ", "title": "t-docs · XYZ · a: b # c", "unit": "docs",
              "depends_on": ["AAA", "user:the hub: powered"], "status": "proposed", "session_id": "",
              "started_at": "2026-11-26 03:10", "rank": 3, "use_worktree": True,
              "background": "line one\nline \"two\"\n", "note": "yes"}
        text = kickoffs.dump(fm, "body\n")
        saved = sys.modules.get("yaml")
        sys.modules["yaml"] = None  # import yaml -> ImportError: the fallback reader
        try:
            got, body = kickoffs.parse(text)
        finally:
            if saved is None:
                del sys.modules["yaml"]
            else:
                sys.modules["yaml"] = saved
        self.assertEqual(body, "body\n")
        self.assertEqual(got, fm)
        try:
            import yaml  # noqa: F401
        except ImportError:
            return
        self.assertEqual(kickoffs.parse(text)[0], fm)


if __name__ == "__main__":
    unittest.main(verbosity=2)
