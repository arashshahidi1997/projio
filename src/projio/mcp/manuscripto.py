"""MCP tools: manuscript assembly, rendering, and validation."""
from __future__ import annotations

from .common import JsonDict, get_project_root, json_dict


def _manuscript_available() -> bool:
    try:
        import notio.manuscript  # noqa: F401
        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {"error": f"{tool} requires the notio manuscript subpackage. Install with: pip install notio"}


def _find_manuscript_dir(root, name: str):
    """Locate the manuscript directory under docs/manuscript/<name>/."""
    from pathlib import Path
    base = Path(root) / "docs" / "manuscript" / name
    spec_path = base / "manuscript.yml"
    if not spec_path.is_file():
        return None, None
    return base, spec_path


def manuscript_init(name: str, template: str = "generic") -> JsonDict:
    """Scaffold a new manuscript with default sections.

    Args:
        name: Manuscript name (used as directory name).
        template: Template preset (currently only 'generic' supported).
    """
    if not _manuscript_available():
        return _unavailable("manuscript_init")
    root = get_project_root()
    try:
        from notio.manuscript.schema import scaffold_spec

        base_dir = root / "docs" / "manuscript" / name
        base_dir.mkdir(parents=True, exist_ok=True)
        spec = scaffold_spec(name, base_dir)
        return json_dict({
            "name": spec.name,
            "title": spec.title,
            "path": str(base_dir.relative_to(root)),
            "sections": [s.key for s in spec.sections],
            "spec_file": str((base_dir / "manuscript.yml").relative_to(root)),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_list() -> JsonDict:
    """List all manuscripts in the project."""
    if not _manuscript_available():
        return _unavailable("manuscript_list")
    root = get_project_root()
    try:
        manuscript_dir = root / "docs" / "manuscript"
        if not manuscript_dir.is_dir():
            return json_dict({"manuscripts": [], "count": 0})

        manuscripts = []
        for child in sorted(manuscript_dir.iterdir()):
            spec_path = child / "manuscript.yml"
            if child.is_dir() and spec_path.is_file():
                from notio.manuscript.schema import ManuscriptSpec
                spec = ManuscriptSpec.from_yaml(spec_path)
                manuscripts.append({
                    "name": spec.name,
                    "title": spec.title,
                    "path": str(child.relative_to(root)),
                    "sections": len(spec.sections),
                    "formats": spec.render.formats,
                })
        return json_dict({"manuscripts": manuscripts, "count": len(manuscripts)})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_status(name: str) -> JsonDict:
    """Show manuscript sections, figures, and completion status.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_status")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        spec = ManuscriptSpec.from_yaml(spec_path)

        sections_status = []
        for entry in sorted(spec.sections, key=lambda s: s.order):
            section_path = base_dir / entry.path
            exists = section_path.is_file()
            word_count = 0
            if exists:
                text = section_path.read_text(encoding="utf-8")
                # Strip frontmatter for word count
                from notio.manuscript.assembly import strip_frontmatter
                body = strip_frontmatter(text)
                word_count = len(body.split())
            sections_status.append({
                "key": entry.key,
                "path": entry.path,
                "order": entry.order,
                "exists": exists,
                "word_count": word_count,
            })

        from notio.manuscript.figures import resolve_figure_paths, validate_figures
        missing_figs = validate_figures(spec, base_dir)
        resolved_figs = resolve_figure_paths(spec, base_dir)

        return json_dict({
            "name": spec.name,
            "title": spec.title,
            "path": str(base_dir.relative_to(root)),
            "sections": sections_status,
            "total_words": sum(s["word_count"] for s in sections_status),
            "figures": {
                "total": len(spec.figures.mappings),
                "resolved": len(resolved_figs),
                "missing": missing_figs,
            },
            "render_formats": spec.render.formats,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_build(name: str, format: str = "pdf") -> JsonDict:
    """Assemble sections and render to PDF/LaTeX/Markdown.

    Args:
        name: Manuscript name.
        format: Output format (pdf, latex, md, docx, html).
    """
    if not _manuscript_available():
        return _unavailable("manuscript_build")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        from notio.manuscript.render import render

        spec = ManuscriptSpec.from_yaml(spec_path)
        outputs = render(spec, base_dir, formats=[format])
        return json_dict({
            "name": spec.name,
            "format": format,
            "outputs": [str(p.relative_to(root)) for p in outputs],
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_validate(name: str) -> JsonDict:
    """Validate citations, figures, sections, and pandoc availability.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_validate")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        from notio.manuscript.validate import validate_manuscript

        spec = ManuscriptSpec.from_yaml(spec_path)
        result = validate_manuscript(spec, base_dir)
        return json_dict({
            "name": spec.name,
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_assemble(name: str) -> JsonDict:
    """Generate assembled markdown without rendering.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_assemble")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        from notio.manuscript.assembly import write_assembled

        spec = ManuscriptSpec.from_yaml(spec_path)
        output_path = write_assembled(spec, base_dir)
        return json_dict({
            "name": spec.name,
            "output": str(output_path.relative_to(root)),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_figure_insert(name: str, section: str, figure_id: str, position: str = "end") -> JsonDict:
    """Insert a figio figure reference into a manuscript section.

    Args:
        name: Manuscript name.
        section: Section key (e.g. 'methods', 'results').
        figure_id: Figure identifier (e.g. 'fig-overview').
        position: Where to insert: 'end' (default) or 'start'.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_figure_insert")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        spec = ManuscriptSpec.from_yaml(spec_path)

        # Find the section
        target = None
        for entry in spec.sections:
            if entry.key == section:
                target = entry
                break
        if target is None:
            return json_dict({"error": f"Section '{section}' not found in manuscript '{name}'"})

        section_path = base_dir / target.path
        if not section_path.is_file():
            return json_dict({"error": f"Section file not found: {target.path}"})

        # Build the figure reference line
        fig_ref = f"\n![](fig:{figure_id})\n"

        text = section_path.read_text(encoding="utf-8")
        if position == "start":
            # Insert after frontmatter
            from notio.manuscript.assembly import FRONTMATTER_RE
            match = FRONTMATTER_RE.match(text)
            if match:
                insert_pos = match.end()
                text = text[:insert_pos] + fig_ref + text[insert_pos:]
            else:
                text = fig_ref + text
        else:
            # Append at end
            text = text.rstrip() + "\n" + fig_ref

        section_path.write_text(text, encoding="utf-8")
        return json_dict({
            "name": name,
            "section": section,
            "figure_id": figure_id,
            "position": position,
            "path": str(section_path.relative_to(root)),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})
