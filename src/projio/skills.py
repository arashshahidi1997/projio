"""Skill scaffolding and listing for projio projects."""
from __future__ import annotations

from pathlib import Path

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


def skill_new(root: str | Path, name: str) -> None:
    """Scaffold a new skill in .projio/skills/<name>/."""
    root_path = Path(root).expanduser().resolve()
    skills_dir = root_path / ".projio" / "skills"
    skill_dir = skills_dir / name
    skill_md = skill_dir / "SKILL.md"

    if skill_md.exists():
        print(f"[SKIP] {skill_md.relative_to(root_path)} already exists")
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
