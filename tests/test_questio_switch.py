"""Deliverables indexes are their own step, apart from questio's plan pages."""
from __future__ import annotations

from projio import sync as sync_mod
from projio.mcp import questio


def _project(tmp_path, *, questio_cfg: str = "", plan: bool = True, deliverables: bool = True):
    (tmp_path / ".projio").mkdir()
    (tmp_path / ".projio" / "config.yml").write_text(questio_cfg)
    if plan:
        (tmp_path / "plan").mkdir()
        (tmp_path / "plan" / "questions.yml").write_text(
            "questions:\n  Q1:\n    title: Does it work?\n    status: open\n")
        (tmp_path / "plan" / "milestones.yml").write_text("milestones:\n  M1:\n    title: First\n    questions: [Q1]\n")
    if deliverables:
        (tmp_path / "docs" / "deliverables").mkdir(parents=True)
    return tmp_path


def test_enabled_by_default_writes_plan_and_deliverables(tmp_path, monkeypatch):
    root = _project(tmp_path)
    monkeypatch.setenv("PROJIO_ROOT", str(root))
    res = questio.questio_docs_collect()
    assert "questio" not in res and (root / "docs/plan/index.md").is_file()
    assert (root / "docs/deliverables/index.md").is_file()

    (root / "docs/deliverables/index.md").unlink()
    res = questio.questio_docs_collect(include_deliverables=False)
    assert (root / "docs/plan/questions.md").is_file() and not (root / "docs/deliverables/index.md").exists()


def test_sync_with_questio_on_runs_both_steps(tmp_path):
    root = _project(tmp_path)
    assert sync_mod._sync_questio_docs(root)["action"] == "generated"
    assert (root / "docs/plan/index.md").is_file() and not (root / "docs/deliverables/index.md").exists()
    assert sync_mod._sync_deliverables_index(root)["action"] == "generated"   # plan exists: old trigger
    assert (root / "docs/deliverables/index.md").is_file()


def test_hand_written_deliverables_pages_are_kept(tmp_path):
    root = _project(tmp_path, plan=False)
    d = root / "docs" / "deliverables"
    questio.deliverables_docs_collect(root)
    (d / "reports" / "index.md").write_text("# Reports\n\nMy own words.\n")
    res = questio.deliverables_docs_collect(root)
    assert res["kept"] == [str(d / "reports" / "index.md")]
    assert (d / "reports" / "index.md").read_text() == "# Reports\n\nMy own words.\n"
    assert res["generated"] == 4


def test_deliverables_step_needs_a_generated_index_or_a_plan(tmp_path):
    root = _project(tmp_path, plan=False)
    assert sync_mod._sync_deliverables_index(root)["action"] == "skipped"
    questio.deliverables_docs_collect(root)
    assert sync_mod._sync_deliverables_index(root)["files"] == 5
