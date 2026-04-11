"""Tests for projio.mcp.context — ecosystem_status, skill_read, discovery."""
from __future__ import annotations

from pathlib import Path

import yaml

from projio.config import Layout
from projio.mcp.context import (
    _discover_skills,
    _discover_workflow_prompts,
    _parse_yaml_frontmatter,
    ecosystem_status,
    module_context,
    project_context,
    skill_read,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_project(root: Path, **extra) -> None:
    """Create a minimal .projio/config.yml."""
    cfg = {"project_name": root.name, **extra}
    _write_yaml(root / ".projio" / "config.yml", cfg)


def _set_root(monkeypatch, root: Path) -> None:
    monkeypatch.setenv("PROJIO_ROOT", str(root))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(root / ".xdg"))


# ---------------------------------------------------------------------------
# _parse_yaml_frontmatter
# ---------------------------------------------------------------------------


def test_parse_frontmatter_extracts_yaml() -> None:
    text = "---\ntitle: Hello\ntags: [a, b]\n---\n\nBody text."
    fm = _parse_yaml_frontmatter(text)
    assert fm["title"] == "Hello"
    assert fm["tags"] == ["a", "b"]


def test_parse_frontmatter_no_frontmatter() -> None:
    assert _parse_yaml_frontmatter("No frontmatter here.") == {}


# ---------------------------------------------------------------------------
# _discover_skills
# ---------------------------------------------------------------------------


def test_discover_skills_no_project_skills(tmp_path: Path) -> None:
    # With no project skills dir, only bundled skills are returned
    skills = _discover_skills(tmp_path)
    assert all(s.get("source") == "bundled" for s in skills)


def test_discover_skills_finds_project_skills(tmp_path: Path) -> None:
    skill_dir = tmp_path / ".projio" / "skills" / "my-skill"
    _write(skill_dir / "SKILL.md", "---\nname: my-skill\ndescription: test skill\n---\n\nBody.")
    skills = _discover_skills(tmp_path)
    project_skills = [s for s in skills if s.get("source") != "bundled"]
    assert len(project_skills) == 1
    assert project_skills[0]["name"] == "my-skill"


def test_discover_skills_custom_layout(tmp_path: Path) -> None:
    skill_dir = tmp_path / "custom" / "skills" / "s1"
    _write(skill_dir / "SKILL.md", "---\nname: s1\ndescription: custom\n---\n")
    layout = Layout(skills="custom/skills")
    skills = _discover_skills(tmp_path, layout)
    assert len(skills) >= 1
    names = [s["name"] for s in skills]
    assert "s1" in names


def test_discover_skills_project_overrides_bundled(tmp_path: Path) -> None:
    # If project has a skill with same name as bundled, project wins
    skill_dir = tmp_path / ".projio" / "skills" / "pipeio-guide"
    _write(skill_dir / "SKILL.md", "---\nname: pipeio-guide\ndescription: project override\n---\n")
    skills = _discover_skills(tmp_path)
    pipeio_skills = [s for s in skills if s["name"] == "pipeio-guide"]
    assert len(pipeio_skills) == 1
    assert "project override" in pipeio_skills[0]["description"]


# ---------------------------------------------------------------------------
# _discover_workflow_prompts
# ---------------------------------------------------------------------------


def test_discover_workflows_falls_back_to_package(tmp_path: Path) -> None:
    # With no project workflows dir, falls back to installed projio package
    layout = Layout(docs="nonexistent_docs")
    prompts = _discover_workflow_prompts(tmp_path, layout)
    # Either empty (if projio not installed from source) or bundled
    assert isinstance(prompts, list)


def test_discover_workflows_finds_prompts(tmp_path: Path) -> None:
    wf_dir = tmp_path / "docs" / "prompts" / "workflows"
    _write(wf_dir / "explore-idea.md", "# Explore Idea")
    _write(wf_dir / "session-bootstrap.md", "# Bootstrap")
    prompts = _discover_workflow_prompts(tmp_path)
    assert len(prompts) == 2
    names = {p["name"] for p in prompts}
    assert names == {"explore-idea", "session-bootstrap"}


def test_discover_workflows_custom_layout(tmp_path: Path) -> None:
    wf_dir = tmp_path / "mydocs" / "prompts" / "workflows"
    _write(wf_dir / "custom.md", "# Custom")
    layout = Layout(docs="mydocs")
    prompts = _discover_workflow_prompts(tmp_path, layout)
    assert len(prompts) == 1
    assert prompts[0]["name"] == "custom"


# ---------------------------------------------------------------------------
# module_context
# ---------------------------------------------------------------------------


def test_module_context_extracts_sections(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _minimal_project(tmp_path)
    doc = tmp_path / "docs" / "test.md"
    _write(doc, "# Module\n\n## Goal\n\nDo something.\n\n## Parameters\n\nParam A.\n")
    result = module_context("docs/test.md")
    assert result["sections_found"] >= 2
    assert result["extracted"]["goal"]["content"] == "Do something."


def test_module_context_file_not_found(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    result = module_context("nonexistent.md")
    assert "error" in result


# ---------------------------------------------------------------------------
# skill_read
# ---------------------------------------------------------------------------


def test_skill_read_project_skill(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _minimal_project(tmp_path)
    skill_dir = tmp_path / ".projio" / "skills" / "test-skill"
    _write(skill_dir / "SKILL.md", "---\nname: test-skill\ndescription: A test\n---\n\nBody content.")
    result = skill_read("test-skill")
    assert result["name"] == "test-skill"
    assert "Body content." in result["content"]


def test_skill_read_not_found(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _minimal_project(tmp_path)
    result = skill_read("nonexistent-skill")
    assert "error" in result


def test_skill_read_custom_layout(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _write_yaml(tmp_path / ".projio" / "config.yml", {
        "project_name": "test",
        "layout": {"skills": "my-skills"},
    })
    skill_dir = tmp_path / "my-skills" / "custom"
    _write(skill_dir / "SKILL.md", "---\nname: custom\ndescription: custom loc\n---\n")
    result = skill_read("custom")
    assert result["name"] == "custom"


# ---------------------------------------------------------------------------
# project_context
# ---------------------------------------------------------------------------


def test_project_context_returns_config(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _minimal_project(tmp_path)
    _write(tmp_path / "README.md", "# Test Project\n\nDescription here.")
    result = project_context()
    assert result["project_name"] == tmp_path.name
    assert "Test Project" in result["readme_excerpt"]


def test_project_context_no_config(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    result = project_context()
    assert result["project_name"] == tmp_path.name


# ---------------------------------------------------------------------------
# ecosystem_status
# ---------------------------------------------------------------------------


def test_ecosystem_status_minimal_project(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _minimal_project(tmp_path)
    result = ecosystem_status()
    assert result["project_name"] == tmp_path.name
    assert "subsystems" in result


def test_ecosystem_status_no_config(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    result = ecosystem_status()
    assert "error" in result


def test_ecosystem_status_notio_counts_layout_notes(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _write_yaml(tmp_path / ".projio" / "config.yml", {
        "project_name": "test",
        "notio": {"enabled": True, "notes_dir": "notes"},
        "layout": {"notes": "docs/log"},
    })
    # Create notes in layout.notes path
    _write(tmp_path / "docs" / "log" / "note1.md", "note 1")
    _write(tmp_path / "docs" / "log" / "note2.md", "note 2")
    _write(tmp_path / "docs" / "log" / "index.md", "index")  # should be excluded

    result = ecosystem_status()
    notio = result["subsystems"]["notio"]
    assert notio["enabled"] is True
    assert notio["note_count"] == 2  # index.md excluded


def test_ecosystem_status_disabled_subsystems(tmp_path: Path, monkeypatch) -> None:
    _set_root(monkeypatch, tmp_path)
    _minimal_project(tmp_path)
    result = ecosystem_status()
    for name in ("biblio", "codio", "pipeio", "figio"):
        assert result["subsystems"][name]["enabled"] is False
