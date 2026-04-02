"""projio manuscript init / projio master init — scaffold and configure."""
from __future__ import annotations

from pathlib import Path


def _ensure_render_yml(root: Path) -> bool:
    """Create .projio/render.yml with defaults if it doesn't exist.

    Returns True if created, False if already existed.
    """
    render_yml = root / ".projio" / "render.yml"
    if render_yml.is_file():
        return False

    import yaml

    defaults = {
        "pdf_engine": "lualatex",
        "csl": ".projio/render/csl/apa.csl",
        "bibliography": ".projio/render/compiled.bib",
        "bib_sources": [".projio/biblio/merged.bib", ".projio/pipeio/modkey.bib"],
        "lua_filter": ".projio/filters/include.lua",
        "conda_env": "",
        "resource_path": [".", "docs"],
    }
    render_yml.parent.mkdir(parents=True, exist_ok=True)
    render_yml.write_text(
        yaml.dump(defaults, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    print(f"[OK] created {render_yml.relative_to(root)}")
    return True


def _ensure_lua_filter(root: Path) -> None:
    """Copy include.lua to .projio/filters/ if missing."""
    from .sync import _sync_lua_filter

    result = _sync_lua_filter(root)
    if result["action"] in ("copied", "updated"):
        print(f"[OK] {result['action']} include.lua → .projio/filters/")


def _regenerate_projio_mk(root: Path) -> None:
    """Regenerate projio.mk so new targets are immediately available."""
    from .init import _projio_mk, _write_if_needed

    mk_path = root / ".projio" / "projio.mk"
    _write_if_needed(mk_path, _projio_mk(root), root, force=True)
    print(f"[OK] regenerated {mk_path.relative_to(root)}")


def init_manuscript(root: Path, name: str, *, path: str | None = None) -> Path:
    """Scaffold a new manuscript: sections, manuscript.yml, render config, Make targets.

    Args:
        root: Project root directory.
        name: Manuscript name (slug).
        path: Directory for the manuscript. Default: docs/manuscript/<name>.

    Returns:
        Path to the manuscript directory.
    """
    if path:
        base_dir = root / path
    else:
        base_dir = root / "docs" / "manuscript" / name

    if (base_dir / "manuscript.yml").is_file():
        print(f"[SKIP] manuscript already exists: {base_dir.relative_to(root)}")
        return base_dir

    try:
        from notio.manuscript.schema import scaffold_spec
    except ImportError:
        raise SystemExit("notio package not installed — run: pip install -e packages/notio")

    spec = scaffold_spec(name, base_dir)
    print(f"[OK] scaffolded manuscript '{name}' at {base_dir.relative_to(root)}/")
    print(f"     {len(spec.sections)} sections: {', '.join(s.key for s in spec.sections)}")

    # Ensure supporting config
    _ensure_render_yml(root)
    _ensure_lua_filter(root)
    _regenerate_projio_mk(root)

    print()
    print(f"Next steps:")
    print(f"  1. Edit sections in {base_dir.relative_to(root)}/sections/")
    print(f"  2. Configure bibliography in {base_dir.relative_to(root)}/manuscript.yml")
    print(f"  3. Run: make manuscript-{name}-pdf")

    return base_dir


def init_master(
    root: Path,
    name: str,
    *,
    path: str | None = None,
    sections: list[str] | None = None,
) -> Path:
    """Scaffold a dual-marker master document: master.md, section files, render config.

    Args:
        root: Project root directory.
        name: Master document name (slug).
        path: Directory for the master doc. Default: docs/<name>.
        sections: Initial section names. Default: [overview].

    Returns:
        Path to the master document directory.
    """
    if path:
        base_dir = root / path
    else:
        base_dir = root / "docs" / name

    if (base_dir / "master.md").is_file():
        print(f"[SKIP] master document already exists: {base_dir.relative_to(root)}")
        return base_dir

    section_names = sections or ["overview"]

    # Create section subdirectory (same name as the master doc)
    section_dir = base_dir / name
    section_dir.mkdir(parents=True, exist_ok=True)

    # Create section files
    for sec_name in section_names:
        sec_path = section_dir / f"{sec_name}.md"
        if not sec_path.is_file():
            title = sec_name.replace("-", " ").replace("_", " ").capitalize()
            sec_path.write_text(f"# {title}\n\n", encoding="utf-8")

    # Generate master.md with dual markers
    try:
        from notio.manuscript.master import generate_master_md
    except ImportError:
        raise SystemExit("notio package not installed — run: pip install -e packages/notio")

    section_dicts = [
        {"path": f"{name}/{sec_name}.md", "title": sec_name}
        for sec_name in section_names
    ]
    master_content = generate_master_md(section_dicts, name)
    master_path = base_dir / "master.md"
    master_path.write_text(master_content, encoding="utf-8")
    print(f"[OK] scaffolded master document '{name}' at {base_dir.relative_to(root)}/")
    print(f"     {len(section_names)} section(s): {', '.join(section_names)}")

    # Ensure supporting config
    _ensure_render_yml(root)
    _ensure_lua_filter(root)
    _regenerate_projio_mk(root)

    print()
    print(f"Next steps:")
    print(f"  1. Edit sections in {base_dir.relative_to(root)}/{name}/")
    print(f"  2. Run: make {name}-pdf")

    return base_dir
