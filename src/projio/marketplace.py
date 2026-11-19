"""Export projio's shared skills as a light Claude Code marketplace.

projio's own ``.claude-plugin/marketplace.json`` lists the portable skills. Adding
the projio repository as a marketplace makes Claude Code clone it with all its
submodules, which is slow or times out. ``export_marketplace`` writes the same
plugins into a small directory (the ``projio-plugins`` repository): the skill
folders copied as they are, a marketplace manifest and a README. Nothing else.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

MANIFEST = Path(".claude-plugin") / "marketplace.json"
README = "README.md"
PLUGINS_DIR = "plugins"
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

# Plugin-entry keys that only make sense for projio's in-repo, non-strict plugin.
_SOURCE_ONLY_KEYS = ("source", "strict", "skills", "mcpServers")


def load_source_manifest(root: str | Path) -> dict:
    """Read projio's marketplace manifest from a projio checkout at ``root``."""
    path = Path(root) / MANIFEST
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found: run from a projio checkout (-C <projio root>)")
    return json.loads(path.read_text())


def source_skills(root: str | Path, plugin: dict) -> list[Path]:
    """The skill folders a plugin of projio's manifest ships."""
    return [(Path(root) / p).resolve() for p in plugin["skills"]]


def export_manifest(manifest: dict) -> dict:
    """The exported marketplace manifest: each plugin served from ``./plugins/<name>``."""
    out = {k: v for k, v in manifest.items() if k != "plugins"}
    out["plugins"] = []
    for plugin in manifest["plugins"]:
        entry = {"name": plugin["name"], "source": f"./{PLUGINS_DIR}/{plugin['name']}"}
        entry.update({k: v for k, v in plugin.items() if k not in _SOURCE_ONLY_KEYS and k != "name"})
        out["plugins"].append(entry)
    return out


def _readme(manifest: dict) -> str:
    market = manifest["name"]
    lines = [
        f"# {market} plugins",
        "",
        manifest.get("metadata", {}).get("description", "").strip(),
        "",
        "Install in Claude Code:",
        "",
        "```text",
        "/plugin marketplace add arashshahidi1997/projio-plugins",
    ]
    lines += [f"/plugin install {p['name']}@{market}" for p in manifest["plugins"]]
    lines += ["```", ""]
    for p in manifest["plugins"]:
        lines += [f"- `{p['name']}` {p.get('version', '')}: {p.get('description', '')}"]
    lines += [
        "",
        "Updates: `/plugin marketplace update " + market + "`, then update the plugin from the `/plugin` menu.",
        "",
        "This repository is generated from [projio](https://github.com/arashshahidi1997/projio) "
        "with `projio skills export --marketplace <dir>`; edit the skills there, not here. "
        "Guide: https://arashshahidi1997.github.io/projio/how-to/skills-without-projio/",
        "",
    ]
    return "\n".join(lines)


def export_marketplace(dest: str | Path, root: str | Path = ".") -> dict:
    """Write the light marketplace into ``dest``; return a summary.

    ``dest/plugins/`` is replaced as a whole, so a skill dropped from projio's
    manifest disappears from the export. Other files in ``dest`` (``.git``, a
    LICENSE) are left alone.
    """
    root = Path(root).resolve()
    dest = Path(dest).resolve()
    if dest == root or root in dest.parents:
        raise ValueError(f"export into a directory outside projio, not {dest}")
    manifest = load_source_manifest(root)

    plugins_root = dest / PLUGINS_DIR
    if plugins_root.exists():
        shutil.rmtree(plugins_root)
    copied: dict[str, list[str]] = {}
    for plugin in manifest["plugins"]:
        skills_dir = plugins_root / plugin["name"] / "skills"
        skills_dir.mkdir(parents=True)
        for src in source_skills(root, plugin):
            shutil.copytree(src, skills_dir / src.name, ignore=_IGNORE)
        copied[plugin["name"]] = [s.name for s in source_skills(root, plugin)]

    out = export_manifest(manifest)
    (dest / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (dest / MANIFEST).write_text(json.dumps(out, indent=2) + "\n")
    (dest / README).write_text(_readme(out))
    return {"dest": str(dest), "plugins": copied}
