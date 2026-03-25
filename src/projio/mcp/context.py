"""MCP tools: project_context, runtime_conventions, agent_instructions."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .common import JsonDict, get_project_root, json_dict, resolve_makefile_vars

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n", re.DOTALL)

_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(\?=|:=|=)\s*(.*?)\s*$")
_VAR_REF_RE = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")
_INCLUDE_RE = re.compile(r"^-?include\s+(.+)$")


def _parse_makefile_vars(text: str, base_dir: Path | None = None) -> dict[str, str]:
    """Parse Makefile variable assignments, following ``include`` directives.

    When *base_dir* is given, ``include`` and ``-include`` lines are resolved
    relative to it and their variables merged (included files are parsed first,
    so the including file can override them — matching Make semantics for simple
    ``?=`` / ``=`` assignments).
    """
    vars_: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        # Handle include / -include directives
        if base_dir is not None:
            inc_match = _INCLUDE_RE.match(line.strip())
            if inc_match:
                for inc_path_str in inc_match.group(1).split():
                    inc_path = base_dir / inc_path_str
                    if inc_path.is_file():
                        try:
                            inc_text = inc_path.read_text(encoding="utf-8")
                            vars_.update(_parse_makefile_vars(inc_text, base_dir=inc_path.parent))
                        except OSError:
                            pass
                continue
        match = _ASSIGN_RE.match(line)
        if not match:
            continue
        name, _, value = match.groups()
        vars_[name] = value.strip()
    return vars_


def _expand(value: str, vars_: dict[str, str], max_rounds: int = 5) -> str:
    expanded = value
    for _ in range(max_rounds):
        new = _VAR_REF_RE.sub(lambda m: vars_.get(m.group(1), m.group(0)), expanded)
        if new == expanded:
            break
        expanded = new
    return expanded


def _parse_yaml_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter from a markdown file."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    try:
        import yaml
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

_MODULE_CONTEXT_KEYWORDS: dict[str, list[str]] = {
    "goal": ["goal", "objective", "overview", "purpose"],
    "assumptions": ["assumption", "assumptions"],
    "parameters": ["parameter", "parameters", "config", "settings"],
    "io": ["inputs", "input", "outputs", "output", "i/o", "io contract", "contract"],
    "limitations": ["limitation", "limitations", "caveat", "caveats"],
}


def module_context(doc_path: str) -> JsonDict:
    """Extract structured sections from a markdown document.

    Looks for standard sections (goal, assumptions, parameters, IO contract,
    limitations) by heading keyword matching. Useful for understanding the
    intent and constraints of any documented module, pipeline mod, or
    component.

    Args:
        doc_path: Path to the markdown file (relative to project root or absolute).
    """
    root = get_project_root()
    p = Path(doc_path).expanduser()
    if not p.is_absolute():
        p = root / p
    p = p.resolve()

    if not p.exists():
        return json_dict({"error": f"File not found: {doc_path}"})
    if p.suffix.lower() not in {".md", ".markdown"}:
        return json_dict({"error": "doc_path must be a markdown file"})

    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()

    # Parse into sections
    sections: list[dict[str, Any]] = []
    current_heading: str | None = None
    current_level: int = 0
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_lines
        if current_heading is not None:
            content = "\n".join(current_lines).strip()
            sections.append({
                "heading": current_heading,
                "level": current_level,
                "content": content,
            })
        current_lines = []

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            flush()
            current_level = len(m.group(1))
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    # Extract by keyword
    extracted: dict[str, Any] = {}
    for key, keywords in _MODULE_CONTEXT_KEYWORDS.items():
        for sec in sections:
            title_lower = sec["heading"].lower()
            if any(kw in title_lower for kw in keywords):
                extracted[key] = {
                    "heading": sec["heading"],
                    "content": sec["content"],
                }
                break
        if key not in extracted:
            extracted[key] = None

    try:
        rel = str(p.relative_to(root))
    except ValueError:
        rel = str(p)

    return json_dict({
        "doc_path": rel,
        "sections_found": len(sections),
        "extracted": extracted,
    })


def skill_read(name: str) -> JsonDict:
    """Read a skill's full SKILL.md content by name.

    Searches project skills (.projio/skills/) first, then ecosystem skills
    bundled with projio. Returns the skill's metadata and full markdown body.
    """
    root = get_project_root()

    # Search project skills first, then ecosystem
    candidates: list[Path] = []
    project_dir = root / ".projio" / "skills" / name / "SKILL.md"
    if project_dir.exists():
        candidates.append(project_dir)
    else:
        try:
            import projio
            pkg_root = Path(projio.__file__).resolve().parent.parent.parent
            eco_path = pkg_root / "docs" / "prompts" / "skills" / name / "SKILL.md"
            if eco_path.exists():
                candidates.append(eco_path)
        except Exception:
            pass

    if not candidates:
        return json_dict({"error": f"Skill not found: {name!r}"})

    skill_path = candidates[0]
    text = skill_path.read_text(encoding="utf-8", errors="ignore")
    fm = _parse_yaml_frontmatter(text)

    try:
        rel = str(skill_path.relative_to(root))
    except ValueError:
        rel = str(skill_path)

    return json_dict({
        "name": fm.get("name", name),
        "description": fm.get("description", ""),
        "path": rel,
        "content": text,
    })


def _parse_skill_md(skill_md: Path, root: Path | None) -> dict[str, Any] | None:
    """Parse a single SKILL.md and return its metadata, or None on failure."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    fm = _parse_yaml_frontmatter(text)
    name = fm.get("name", skill_md.parent.name)
    desc = fm.get("description", "")
    if isinstance(desc, str):
        desc = " ".join(desc.split())
    short = ""
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        short = meta.get("short-description", "")
    path = str(skill_md.relative_to(root)) if root and skill_md.is_relative_to(root) else str(skill_md)
    return {"name": name, "description": short or desc, "path": path}


def _discover_skills(root: Path) -> list[dict[str, Any]]:
    """Scan .projio/skills/ and projio ecosystem skills for SKILL.md files."""
    seen_names: set[str] = set()
    skills: list[dict[str, Any]] = []

    # 1. Project-level skills (take precedence)
    project_dir = root / ".projio" / "skills"
    if project_dir.is_dir():
        for skill_md in sorted(project_dir.glob("*/SKILL.md")):
            entry = _parse_skill_md(skill_md, root)
            if entry:
                seen_names.add(entry["name"])
                skills.append(entry)

    # 2. Ecosystem-level skills bundled with projio (skip if project overrides)
    try:
        import projio
        pkg_root = Path(projio.__file__).resolve().parent.parent.parent
        eco_dir = pkg_root / "docs" / "prompts" / "skills"
        if eco_dir.is_dir() and eco_dir != project_dir:
            for skill_md in sorted(eco_dir.glob("*/SKILL.md")):
                entry = _parse_skill_md(skill_md, root if skill_md.is_relative_to(root) else None)
                if entry and entry["name"] not in seen_names:
                    entry["source"] = "projio"
                    skills.append(entry)
    except Exception:
        pass

    return skills


def _discover_workflow_prompts(root: Path) -> list[dict[str, Any]]:
    """Scan for projio workflow prompts shipped with the package."""
    prompts: list[dict[str, Any]] = []
    # Check for workflow prompts in project docs (projio itself or a project
    # that copied them in)
    workflows_dir = root / "docs" / "prompts" / "workflows"
    if not workflows_dir.is_dir():
        # Try the installed projio package location
        try:
            import projio
            pkg_root = Path(projio.__file__).resolve().parent.parent.parent
            workflows_dir = pkg_root / "docs" / "prompts" / "workflows"
        except Exception:
            pass
    if not workflows_dir.is_dir():
        return prompts
    _WHEN_TO_USE: dict[str, str] = {
        "session-bootstrap": "Start of every session — gather context, determine phase",
        "explore-idea": "New analysis idea — capture, discover code, search literature, decide",
        "implement-feature": "Decision exists — implement, test, notebook demo",
        "integrate-pipeline": "Code validated — operationalize as pipeline",
        "validate-and-deploy": "Pipeline integrated — pre-flight, execute, deploy",
    }
    for md in sorted(workflows_dir.glob("*.md")):
        if md.name.lower() == "readme.md":
            continue
        slug = md.stem
        prompts.append({
            "name": slug,
            "when": _WHEN_TO_USE.get(slug, ""),
            "path": str(md.relative_to(root)) if md.is_relative_to(root) else str(md),
        })
    return prompts


def project_context() -> JsonDict:
    """Structured snapshot of the project: config, README excerpt, key paths.

    Reads .projio/config.yml and the project README.
    """
    root = get_project_root()
    try:
        from projio.init import load_projio_config
        cfg = load_projio_config(root)
    except FileNotFoundError:
        cfg = {}

    readme_excerpt = ""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        readme_path = root / name
        if readme_path.exists():
            text = readme_path.read_text(encoding="utf-8", errors="ignore")
            readme_excerpt = text[:2000]
            break

    payload: dict[str, Any] = {
        "project_name": cfg.get("project_name", root.name),
        "description": cfg.get("description", ""),
        "root": str(root),
        "config": cfg,
        "readme_excerpt": readme_excerpt,
    }
    return json_dict(payload)


def runtime_conventions() -> JsonDict:
    """Parse Makefile variables and targets from the project root, return as dict."""
    root = get_project_root()
    makefile = root / "Makefile"
    exists = makefile.exists()
    vars_ = resolve_makefile_vars()
    command_keys = {
        "python": "PYTHON",
        "datalad": "DATALAD",
        "mkdocs": "MKDOCS",
        "projio": "PROJIO",
    }
    commands = {
        name: _expand(vars_[key], vars_)
        for name, key in command_keys.items()
        if key in vars_
    }
    payload: dict[str, Any] = {
        "makefile": {
            "path": str(makefile.relative_to(root)) if exists else "Makefile",
            "exists": exists,
        },
        "vars": vars_,
        "commands": commands,
    }
    return json_dict(payload)


def agent_instructions() -> JsonDict:
    """Return agent execution context: tool routing table and workflow conventions.

    This is the dynamic equivalent of the CLAUDE.md tool routing section.
    Worklog and other orchestrators should call this before dispatching
    prompts to get project-aware agent instructions.

    Includes:
    - Generated CLAUDE.md instructions (tool routing, conventions)
    - Available project skills from .projio/skills/
    - Workflow prompts for the research grand routine
    """
    root = get_project_root()
    # Check if projio is actually configured for this project
    projio_dir = root / ".projio"
    if not projio_dir.is_dir():
        return json_dict({"error": "projio not configured (no .projio directory)"})

    try:
        from projio.init import _generate_claude_md, _load_packages

        packages = _load_packages(root).get("packages", {})
        enabled = [
            name for name, entry in packages.items()
            if entry.get("enabled", False)
        ]
        instructions = _generate_claude_md(root)
    except Exception as exc:
        return json_dict({"error": str(exc)})

    payload: dict[str, Any] = {
        "project_root": str(root),
        "enabled_packages": enabled,
        "instructions": instructions,
    }

    # Discover project skills
    skills = _discover_skills(root)
    if skills:
        payload["skills"] = skills

    # Discover workflow prompts
    workflow_prompts = _discover_workflow_prompts(root)
    if workflow_prompts:
        payload["workflow_prompts"] = workflow_prompts

    return json_dict(payload)
