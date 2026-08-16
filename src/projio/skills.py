"""Skill scaffolding and listing for projio projects."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

# Ecosystem skills bundled with the projio package.
_BUNDLED_SKILLS_DIR = Path(__file__).resolve().parent / "data" / "skills"

_SKILL_TEMPLATE = """\
---
name: {name}
description: >
  TODO: describe what this skill does and when to use it.
metadata:
  short-description: TODO
  tags: []
  tooling:
    mcp:
      - server: projio
        tools: []
---

# {title}

## When to use

TODO: describe the trigger conditions.

## Inputs

- `INPUT` (required): TODO

## Workflow

### 1) Gather context

```
project_context()
```

### 2) TODO

TODO: describe the steps.

## Guardrails

- Do NOT run git commands.

## Output format

Report:
1. TODO
"""


def _list_bundled_skill_names() -> list[str]:
    """Return the names of ecosystem skills bundled with projio."""
    if not _BUNDLED_SKILLS_DIR.is_dir():
        return []
    return sorted(p.parent.name for p in _BUNDLED_SKILLS_DIR.glob("*/SKILL.md"))


def _retitle_frontmatter(text: str, name: str) -> str:
    """Rewrite the frontmatter ``name:`` field to *name* (first match only)."""
    return re.sub(
        r"^name:.*$",
        f"name: {name}",
        text,
        count=1,
        flags=re.MULTILINE,
    )


def skill_new(
    root: str | Path,
    name: str,
    from_ecosystem: str | None = None,
) -> None:
    """Scaffold a new skill in .projio/skills/<name>/.

    With *from_ecosystem*, seed the new skill from a bundled ecosystem skill of
    that name (fork-and-tailor) instead of the blank template. The project copy
    overrides the ecosystem one via the normal skill-discovery precedence, so you
    can edit it to encode project-specific quirks.
    """
    root_path = Path(root).expanduser().resolve()
    skills_dir = root_path / ".projio" / "skills"
    skill_dir = skills_dir / name
    skill_md = skill_dir / "SKILL.md"

    if skill_md.exists():
        print(f"[SKIP] {skill_md.relative_to(root_path)} already exists")
        return

    if from_ecosystem:
        src_dir = _BUNDLED_SKILLS_DIR / from_ecosystem
        src_md = src_dir / "SKILL.md"
        if not src_md.exists():
            available = ", ".join(_list_bundled_skill_names()) or "(none found)"
            print(f"[ERROR] no bundled ecosystem skill named {from_ecosystem!r}")
            print(f"        available: {available}")
            return
        skill_dir.mkdir(parents=True, exist_ok=True)
        # Copy sibling assets (e.g. references/) verbatim, then the retitled SKILL.md.
        for item in src_dir.iterdir():
            if item.name == "SKILL.md":
                continue
            dest = skill_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        text = _retitle_frontmatter(
            src_md.read_text(encoding="utf-8", errors="ignore"), name
        )
        skill_md.write_text(text, encoding="utf-8")
        print(f"[OK] forked ecosystem skill {from_ecosystem!r} → {skill_md.relative_to(root_path)}")
        print(f"     This local copy overrides the ecosystem one. Edit it to tailor.")
        return

    skill_dir.mkdir(parents=True, exist_ok=True)
    refs_dir = skill_dir / "references"
    refs_dir.mkdir(exist_ok=True)

    title = name.replace("-", " ").title()
    skill_md.write_text(
        _SKILL_TEMPLATE.format(name=name, title=title),
        encoding="utf-8",
    )
    print(f"[OK] created {skill_md.relative_to(root_path)}")
    print(f"     references dir: {refs_dir.relative_to(root_path)}/")
    print(f"     Edit the SKILL.md to define your workflow.")


def skill_list(root: str | Path) -> None:
    """List available skills (project + ecosystem)."""
    import os

    root_path = Path(root).expanduser().resolve()

    # Temporarily set PROJIO_ROOT so discovery works
    old = os.environ.get("PROJIO_ROOT")
    os.environ["PROJIO_ROOT"] = str(root_path)
    try:
        from projio.mcp.context import _discover_skills
        skills = _discover_skills(root_path)
    finally:
        if old is None:
            os.environ.pop("PROJIO_ROOT", None)
        else:
            os.environ["PROJIO_ROOT"] = old

    if not skills:
        print("No skills found.")
        return

    print(f"{'Name':<25} {'Source':<10} {'Description'}")
    for s in skills:
        source = s.get("source", "project")
        desc = s.get("description", "")
        if len(desc) > 60:
            desc = desc[:57] + "..."
        print(f"{s['name']:<25} {source:<10} {desc}")
