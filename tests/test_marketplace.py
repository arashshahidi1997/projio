"""The Claude Code plugin marketplace (.claude-plugin/marketplace.json) shares projio's portable
skills: those that work in any git project without projio installed."""
from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "src" / "projio" / "data" / "skills"


def _market() -> dict:
    return json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())


def _frontmatter(skill_md: Path) -> tuple[dict, str]:
    text = skill_md.read_text()
    _, head, body = text.split("---\n", 2)
    return yaml.safe_load(head), body


def _shipped() -> list[Path]:
    return [ROOT / p for plugin in _market()["plugins"] for p in plugin["skills"]]


def test_plugins_are_versioned_with_projio():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    market = _market()
    assert market["name"] == "projio"
    for plugin in market["plugins"]:
        assert plugin["version"] == version, plugin["name"]
        assert plugin["source"] == "./" and plugin["strict"] is False
        # the repo root is the plugin root: keep its .mcp.json (the projio server) out
        assert plugin["mcpServers"] == {}


def test_marketplace_ships_exactly_the_portable_skills():
    shipped = _shipped()
    for path in shipped:
        assert (path / "SKILL.md").is_file(), path
        meta, _ = _frontmatter(path / "SKILL.md")
        assert meta["name"] == path.name
    portable = {d.name for d in SKILLS.iterdir()
                if (d / "SKILL.md").is_file() and _frontmatter(d / "SKILL.md")[0]["metadata"].get("portable")}
    assert sorted(p.name for p in shipped) == sorted(portable)
    assert len(shipped) == len(set(shipped))


def _required_imports(py: Path) -> set[str]:
    """Top-level modules a helper imports outside a try block (a guarded import is optional)."""
    tree = ast.parse(py.read_text())
    optional = {id(n) for t in ast.walk(tree) if isinstance(t, ast.Try)
                for stmt in t.body for n in ast.walk(stmt)}
    names = set()
    for node in ast.walk(tree):
        if id(node) in optional:
            continue
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_portable_skills_need_no_projio():
    for path in _shipped():
        meta, body = _frontmatter(path / "SKILL.md")
        for server in meta["metadata"].get("tooling", {}).get("mcp", []):
            assert server.get("optional") is True, f"{path.name}: MCP server {server['server']} is required"
        assert "mcp__projio" not in body, path.name
        fenced = re.findall(r"```[^\n]*\n(.*?)```", body, flags=re.S)
        for block in fenced:
            for line in block.splitlines():
                assert not re.match(r"\s*(\$\s*)?projio\s", line), f"{path.name}: requires the projio CLI: {line}"
        siblings = {p.stem for p in path.glob("*.py")}
        for py in path.glob("*.py"):
            extra = _required_imports(py) - set(sys.stdlib_module_names) - siblings - {"__future__"}
            assert not extra, f"{py.relative_to(ROOT)} imports {extra}"
