"""MCP tools: manuscript assembly, rendering, and validation."""
from __future__ import annotations

import difflib
import re

from .common import JsonDict, get_project_root, json_dict

# Matches @citekey in pandoc citation syntax ([@key] or [@k1; @k2])
_CITE_RE = re.compile(r"@([a-zA-Z0-9_:.\-]+)")


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

        # Build the figure reference line — pull caption from manuscript.yml mapping
        caption = ""
        for mapping in spec.figures.mappings:
            if mapping.id == figure_id and mapping.caption:
                caption = mapping.caption
                break
        fig_ref = f"\n![{caption}](fig:{figure_id})\n"

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


def manuscript_section_context(name: str, section: str) -> JsonDict:
    """One-call context gathering for drafting a manuscript section.

    Returns current content, RAG hits, figure info, citations used,
    related notes, and word count — everything an agent needs to draft.

    Args:
        name: Manuscript name.
        section: Section key (e.g. 'introduction', 'methods').
    """
    if not _manuscript_available():
        return _unavailable("manuscript_section_context")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        from notio.manuscript.assembly import strip_frontmatter

        spec = ManuscriptSpec.from_yaml(spec_path)

        # Find the section entry
        target = None
        for entry in spec.sections:
            if entry.key == section:
                target = entry
                break
        if target is None:
            available = [s.key for s in spec.sections]
            return json_dict({"error": f"Section '{section}' not found", "available_sections": available})

        # 1. Read section content
        section_path = base_dir / target.path
        current_content = ""
        word_count = 0
        citations_used: list[str] = []
        if section_path.is_file():
            raw = section_path.read_text(encoding="utf-8")
            current_content = strip_frontmatter(raw)
            word_count = len(current_content.split())
            citations_used = sorted(set(_CITE_RE.findall(raw)))

        # 2. RAG hits for section title/key
        rag_hits: list[dict] = []
        try:
            from .rag import rag_query
            query_text = section.replace("-", " ").replace("_", " ")
            rag_result = rag_query(query=query_text, k=6)
            rag_hits = rag_result.get("results", [])  # type: ignore[union-attr]
        except Exception:
            pass  # RAG unavailable — degrade gracefully

        # 3. Figures mapped to this section
        figures_info: list[dict] = []
        from notio.manuscript.figures import resolve_figure_paths
        resolved_figs = resolve_figure_paths(spec, base_dir)
        for mapping in spec.figures.mappings:
            # Include figure if its section mapping matches, or include all
            # (the agent can filter). Check if figure ref appears in section text.
            fig_in_section = f"fig:{mapping.id}" in current_content
            fig_entry: dict = {
                "id": mapping.id,
                "label": mapping.label,
                "caption": mapping.caption,
                "in_section": fig_in_section,
                "built": mapping.id in resolved_figs,
            }
            if mapping.spec:
                fig_entry["spec"] = mapping.spec
            if mapping.id in resolved_figs:
                fig_entry["output_path"] = str(resolved_figs[mapping.id].relative_to(root))
            figures_info.append(fig_entry)

        # 4. Related notes via semantic search
        related_notes: list[dict] = []
        try:
            from .notio import note_search
            search_result = note_search(query=section.replace("-", " ").replace("_", " "), k=5)
            related_notes = search_result.get("results", [])  # type: ignore[union-attr]
        except Exception:
            pass  # note search unavailable

        return json_dict({
            "name": name,
            "section": section,
            "current_content": current_content,
            "word_count": word_count,
            "citations_used": citations_used,
            "rag_hits": rag_hits,
            "figures": figures_info,
            "related_notes": related_notes,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_overview(name: str) -> JsonDict:
    """Rich manuscript dashboard with per-section stats, citation/figure analysis.

    Superset of manuscript_status — adds citation cross-checking, figure staleness
    detection, and bibliography stats.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_overview")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from pathlib import Path
        from notio.manuscript.schema import ManuscriptSpec, resolve_render_config
        from notio.manuscript.assembly import strip_frontmatter
        from notio.manuscript.figures import resolve_figure_paths

        spec = ManuscriptSpec.from_yaml(spec_path)
        resolved = resolve_render_config(spec, base_dir)

        # --- Per-section stats ---
        all_citekeys: set[str] = set()
        sections_status: list[dict] = []
        for entry in sorted(spec.sections, key=lambda s: s.order):
            section_path = base_dir / entry.path
            exists = section_path.is_file()
            word_count = 0
            citation_count = 0
            figure_ref_count = 0
            section_cites: list[str] = []
            status = "missing"
            if exists:
                raw = section_path.read_text(encoding="utf-8")
                body = strip_frontmatter(raw)
                word_count = len(body.split())
                section_cites = _CITE_RE.findall(raw)
                citation_count = len(set(section_cites))
                all_citekeys.update(section_cites)
                # Count figure references
                figure_ref_count = raw.count("fig:")
                # Parse status from frontmatter
                import yaml as _yaml
                fm_match = re.match(r"\A---\s*\n(.*?)\n---", raw, re.DOTALL)
                if fm_match:
                    try:
                        fm = _yaml.safe_load(fm_match.group(1)) or {}
                        status = fm.get("status", "draft")
                    except Exception:
                        status = "draft"
                else:
                    status = "draft"
            sections_status.append({
                "key": entry.key,
                "title": entry.key.replace("_", " ").replace("-", " ").capitalize(),
                "word_count": word_count,
                "citation_count": citation_count,
                "figure_ref_count": figure_ref_count,
                "status": status,
            })

        # --- Bibliography analysis ---
        bib_file = resolved.bib_file
        bib_keys: set[str] = set()
        bib_entry_count = 0
        bib_path_str = ""
        if bib_file:
            bib_path = base_dir / bib_file
            if bib_path.is_file():
                bib_text = bib_path.read_text(encoding="utf-8")
                bib_keys = set(re.findall(r"@\w+\{([^,\s]+)", bib_text))
                bib_entry_count = len(bib_keys)
                bib_path_str = str(bib_path.relative_to(root))

        missing_citations = sorted(all_citekeys - bib_keys) if bib_keys else []

        # --- Figure analysis ---
        resolved_figs = resolve_figure_paths(spec, base_dir)
        missing_figures: list[str] = []
        stale_figures: list[str] = []
        for mapping in spec.figures.mappings:
            if mapping.id not in resolved_figs:
                missing_figures.append(mapping.id)
            elif mapping.spec:
                # Check staleness: spec mtime > built output mtime
                spec_file = base_dir / mapping.spec
                built_file = resolved_figs[mapping.id]
                if spec_file.is_file() and built_file.is_file():
                    if spec_file.stat().st_mtime > built_file.stat().st_mtime:
                        stale_figures.append(mapping.id)

        # --- Docling fulltext count (best-effort) ---
        papers_with_fulltext = 0
        try:
            from .biblio import _biblio_available
            if _biblio_available():
                from biblio.docling_status import count_extracted
                papers_with_fulltext = count_extracted(root)
        except Exception:
            pass  # biblio or docling_status not available

        return json_dict({
            "name": spec.name,
            "title": spec.title,
            "path": str(base_dir.relative_to(root)),
            "sections": sections_status,
            "total_words": sum(s["word_count"] for s in sections_status),
            "total_citations": len(all_citekeys),
            "total_figures": len(spec.figures.mappings),
            "missing_citations": missing_citations,
            "missing_figures": missing_figures,
            "stale_figures": stale_figures,
            "bibliography": {
                "path": bib_path_str,
                "entry_count": bib_entry_count,
                "papers_with_fulltext": papers_with_fulltext,
            },
            "render_formats": spec.render.formats,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_cite_check(name: str) -> JsonDict:
    """Citation-focused validation across sections, .bib, and biblio fulltext.

    Scans all sections for [@citekey] patterns, cross-checks against the .bib
    file, and reports which cited papers have fulltext available for RAG.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_cite_check")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec, resolve_render_config

        spec = ManuscriptSpec.from_yaml(spec_path)
        resolved = resolve_render_config(spec, base_dir)

        # Collect all citations per section
        cite_to_sections: dict[str, list[str]] = {}
        for entry in spec.sections:
            section_path = base_dir / entry.path
            if section_path.is_file():
                text = section_path.read_text(encoding="utf-8")
                for citekey in _CITE_RE.findall(text):
                    cite_to_sections.setdefault(citekey, [])
                    if entry.key not in cite_to_sections[citekey]:
                        cite_to_sections[citekey].append(entry.key)

        # Parse .bib for known keys
        bib_keys: set[str] = set()
        bib_file = resolved.bib_file
        if bib_file:
            bib_path = base_dir / bib_file
            if bib_path.is_file():
                bib_text = bib_path.read_text(encoding="utf-8")
                bib_keys = set(re.findall(r"@\w+\{([^,\s]+)", bib_text))

        # Check docling extraction status per citekey (best-effort)
        docling_keys: set[str] = set()
        try:
            from .biblio import _biblio_available
            if _biblio_available():
                from biblio.docling_status import list_extracted_citekeys
                docling_keys = set(list_extracted_citekeys(root))
        except Exception:
            pass

        found: list[dict] = []
        missing: list[dict] = []
        suggestions: list[str] = []

        for citekey, sections in sorted(cite_to_sections.items()):
            if citekey in bib_keys:
                has_fulltext = citekey in docling_keys
                found.append({
                    "citekey": citekey,
                    "sections": sections,
                    "has_fulltext": has_fulltext,
                })
                if not has_fulltext:
                    suggestions.append(f"Run biblio_docling on '{citekey}' to enable RAG over its fulltext")
            else:
                missing.append({
                    "citekey": citekey,
                    "sections": sections,
                })

        if missing:
            missing_keys = [m["citekey"] for m in missing]
            suggestions.insert(0, f"Run biblio_ingest for missing citekeys: {missing_keys}")

        return json_dict({
            "name": name,
            "found": found,
            "missing": missing,
            "suggestions": suggestions,
            "total_citations": len(cite_to_sections),
            "bib_entries": len(bib_keys),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_figure_build_all(name: str) -> JsonDict:
    """Batch-build all figures in a manuscript via figio.

    Iterates figure mappings with spec paths and invokes figio build on each.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_figure_build_all")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec

        spec = ManuscriptSpec.from_yaml(spec_path)

        # Check if figio is available
        figio_available = False
        try:
            import figio  # noqa: F401
            figio_available = True
        except ImportError:
            pass

        results: list[dict] = []
        for mapping in spec.figures.mappings:
            if not mapping.spec:
                results.append({
                    "figure_id": mapping.id,
                    "status": "skipped",
                    "reason": "no spec path configured",
                })
                continue

            spec_file = base_dir / mapping.spec
            if not spec_file.is_file():
                results.append({
                    "figure_id": mapping.id,
                    "status": "skipped",
                    "reason": f"spec file not found: {mapping.spec}",
                })
                continue

            if not figio_available:
                results.append({
                    "figure_id": mapping.id,
                    "status": "skipped",
                    "reason": "figio not installed",
                })
                continue

            try:
                from figio.build import build_figure
                output = build_figure(spec_file)
                results.append({
                    "figure_id": mapping.id,
                    "status": "built",
                    "path": str(output.relative_to(root)) if output else None,
                })
            except Exception as exc:
                results.append({
                    "figure_id": mapping.id,
                    "status": "failed",
                    "error": str(exc),
                })

        built = sum(1 for r in results if r["status"] == "built")
        failed = sum(1 for r in results if r["status"] == "failed")
        skipped = sum(1 for r in results if r["status"] == "skipped")

        return json_dict({
            "name": name,
            "figures": results,
            "summary": {"built": built, "failed": failed, "skipped": skipped},
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_diff(name: str) -> JsonDict:
    """Compare current section content against last _build/assembled.md snapshot.

    Detects section-level changes, word count deltas, and citation drift.

    Args:
        name: Manuscript name.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_diff")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        from notio.manuscript.assembly import assemble, strip_frontmatter

        spec = ManuscriptSpec.from_yaml(spec_path)

        # Current assembled text
        current_text = assemble(spec, base_dir)
        word_count_after = len(current_text.split())

        # Previous build
        build_path = base_dir / spec.render.output_dir / "assembled.md"
        has_previous_build = build_path.is_file()
        previous_text = ""
        if has_previous_build:
            previous_text = build_path.read_text(encoding="utf-8")
        word_count_before = len(previous_text.split()) if previous_text else 0

        # Build per-section content maps for current state
        current_sections: dict[str, str] = {}
        for entry in spec.sections:
            section_path = base_dir / entry.path
            if section_path.is_file():
                raw = section_path.read_text(encoding="utf-8")
                current_sections[entry.key] = strip_frontmatter(raw).strip()

        # Build per-section content map from previous assembled text.
        # Sections in assembled.md are separated by headings; use a heuristic:
        # split on section keys found in the spec (matching heading lines).
        previous_sections: dict[str, str] = {}
        if has_previous_build:
            # Parse previous assembled text by splitting on heading markers
            # that match section keys. We scan for lines starting with #
            # and try to match them to section keys.
            lines = previous_text.splitlines(keepends=True)
            # Build a mapping from normalised section title to key
            key_variants: dict[str, str] = {}
            for entry in spec.sections:
                # Headings may be the key itself or its title-cased form
                normalised = entry.key.replace("_", " ").replace("-", " ").lower()
                key_variants[normalised] = entry.key
            current_key: str | None = None
            current_lines: list[str] = []
            for line in lines:
                stripped = line.strip().lstrip("#").strip().lower()
                matched_key: str | None = None
                for variant, key in key_variants.items():
                    if stripped == variant:
                        matched_key = key
                        break
                if matched_key is not None:
                    # Save accumulated content for previous section
                    if current_key is not None:
                        previous_sections[current_key] = "".join(current_lines).strip()
                    current_key = matched_key
                    current_lines = []
                else:
                    current_lines.append(line)
            if current_key is not None:
                previous_sections[current_key] = "".join(current_lines).strip()

        # Compute diffs
        all_keys = set(list(current_sections.keys()) + list(previous_sections.keys()))
        sections_changed: list[str] = []
        sections_added: list[str] = []
        sections_removed: list[str] = []
        for key in sorted(all_keys):
            in_current = key in current_sections
            in_previous = key in previous_sections
            if in_current and not in_previous:
                sections_added.append(key)
            elif in_previous and not in_current:
                sections_removed.append(key)
            elif in_current and in_previous:
                # Compare using difflib to ignore trivial whitespace
                cur_lines = current_sections[key].splitlines()
                prev_lines = previous_sections[key].splitlines()
                if list(difflib.unified_diff(prev_lines, cur_lines)):
                    sections_changed.append(key)

        # Citation drift
        current_cites = set(_CITE_RE.findall(current_text))
        previous_cites = set(_CITE_RE.findall(previous_text)) if previous_text else set()
        citations_added = sorted(current_cites - previous_cites)
        citations_removed = sorted(previous_cites - current_cites)

        return json_dict({
            "name": name,
            "has_previous_build": has_previous_build,
            "sections_changed": sections_changed,
            "sections_added": sections_added,
            "sections_removed": sections_removed,
            "word_count_before": word_count_before,
            "word_count_after": word_count_after,
            "word_count_delta": word_count_after - word_count_before,
            "citations_added": citations_added,
            "citations_removed": citations_removed,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def manuscript_cite_suggest(name: str, section: str, claim: str = "") -> JsonDict:
    """Search RAG biblio corpus for papers relevant to a section or claim.

    Returns ranked citekeys with relevance scores and snippets.

    Args:
        name: Manuscript name.
        section: Section key (e.g. 'introduction', 'methods').
        claim: Optional claim text to search for (overrides section content).
    """
    if not _manuscript_available():
        return _unavailable("manuscript_cite_suggest")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec
        from notio.manuscript.assembly import strip_frontmatter

        spec = ManuscriptSpec.from_yaml(spec_path)

        # Find the section entry
        target = None
        for entry in spec.sections:
            if entry.key == section:
                target = entry
                break
        if target is None:
            available = [s.key for s in spec.sections]
            return json_dict({"error": f"Section '{section}' not found", "available_sections": available})

        # Determine query text
        query_text = claim.strip() if claim.strip() else ""
        if not query_text:
            section_path = base_dir / target.path
            if section_path.is_file():
                raw = section_path.read_text(encoding="utf-8")
                body = strip_frontmatter(raw).strip()
                # Use first ~500 words to stay within reasonable query size
                words = body.split()
                query_text = " ".join(words[:500]) if words else ""
            if not query_text:
                # Fall back to section key as query
                query_text = section.replace("_", " ").replace("-", " ")

        # Query RAG with biblio corpus filter
        try:
            from .rag import rag_query
            rag_result = rag_query(query=query_text, corpus="biblio", k=10)
            hits = rag_result.get("results", [])  # type: ignore[union-attr]
        except Exception:
            # Try without corpus filter if biblio corpus doesn't exist
            try:
                from .rag import rag_query
                rag_result = rag_query(query=query_text, k=10)
                hits = rag_result.get("results", [])  # type: ignore[union-attr]
            except Exception:
                return json_dict({
                    "error": "RAG unavailable — ensure indexio is installed and the index is built",
                    "section": section,
                    "query_used": query_text[:200],
                })

        # Extract citekeys from source paths and filter to bib-related hits
        suggestions: list[dict] = []
        seen_citekeys: set[str] = set()
        for hit in hits:
            source = hit.get("source", "") or hit.get("path", "") or ""
            snippet = hit.get("text", "") or hit.get("content", "") or ""
            score = hit.get("score", 0.0) or hit.get("distance", 0.0) or 0.0

            # Try to extract citekey from source path
            # Common patterns: bib/derivatives/docling/<citekey>/...,
            # bib/derivatives/grobid/<citekey>.xml, bib/articles/<citekey>.pdf
            citekey = _extract_citekey_from_path(source)

            entry: dict = {
                "citekey": citekey,
                "relevance_score": round(float(score), 4) if score else 0.0,
                "snippet": snippet[:300] if snippet else "",
                "source": source,
            }

            # Deduplicate by citekey (keep highest score)
            if citekey and citekey in seen_citekeys:
                continue
            if citekey:
                seen_citekeys.add(citekey)
            suggestions.append(entry)

        return json_dict({
            "name": name,
            "section": section,
            "query_used": query_text[:200],
            "suggestions": suggestions,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def _extract_citekey_from_path(source: str) -> str:
    """Best-effort citekey extraction from a RAG source path.

    Recognises patterns like:
    - bib/derivatives/docling/<citekey>/...
    - bib/derivatives/grobid/<citekey>.tei.xml
    - bib/articles/<citekey>.pdf
    """
    if not source:
        return ""
    parts = source.replace("\\", "/").split("/")
    # Look for bib/derivatives/<tool>/<citekey> pattern
    for i, part in enumerate(parts):
        if part == "derivatives" and i + 2 < len(parts):
            candidate = parts[i + 2]
            # Remove file extensions
            candidate = candidate.split(".")[0]
            if candidate:
                return candidate
        if part == "articles" and i + 1 < len(parts):
            candidate = parts[i + 1]
            candidate = candidate.split(".")[0]
            if candidate:
                return candidate
    return ""


# --- Journal profiles ---

# Minimal built-in profiles: word_limit, figure_limit, required_sections, csl_name
_JOURNAL_PROFILES: dict[str, dict] = {
    "nature": {
        "name": "Nature",
        "word_limit": 3000,
        "figure_limit": 6,
        "required_sections": ["abstract", "introduction", "results", "discussion", "methods", "references"],
        "csl_name": "nature",
    },
    "plos-one": {
        "name": "PLOS ONE",
        "word_limit": 0,  # no strict limit
        "figure_limit": 0,  # no strict limit
        "required_sections": ["abstract", "introduction", "methods", "results", "discussion", "references"],
        "csl_name": "plos",
    },
    "elife": {
        "name": "eLife",
        "word_limit": 0,  # no strict limit
        "figure_limit": 0,  # no strict limit
        "required_sections": ["abstract", "introduction", "results", "discussion", "methods", "references"],
        "csl_name": "elife",
    },
    "biorxiv": {
        "name": "bioRxiv",
        "word_limit": 0,  # no strict limit
        "figure_limit": 0,  # no strict limit
        "required_sections": ["abstract", "introduction", "methods", "results", "discussion", "references"],
        "csl_name": "",  # any CSL accepted
    },
}


def manuscript_journal_check(name: str, journal: str = "") -> JsonDict:
    """Check manuscript against journal target profile.

    Compares word count, figure count, required sections, and CSL style
    against built-in journal profiles.

    Args:
        name: Manuscript name.
        journal: Journal key (e.g. 'nature', 'plos-one'). Omit to list available profiles.
    """
    if not _manuscript_available():
        return _unavailable("manuscript_journal_check")

    # List profiles when no journal specified
    if not journal.strip():
        profiles = []
        for key, profile in _JOURNAL_PROFILES.items():
            profiles.append({
                "key": key,
                "name": profile["name"],
                "word_limit": profile["word_limit"] or "none",
                "figure_limit": profile["figure_limit"] or "none",
            })
        return json_dict({
            "available_profiles": profiles,
            "hint": "Pass a journal key to check your manuscript against it.",
        })

    journal = journal.strip().lower()
    if journal not in _JOURNAL_PROFILES:
        return json_dict({
            "error": f"Unknown journal '{journal}'",
            "available_profiles": list(_JOURNAL_PROFILES.keys()),
        })

    profile = _JOURNAL_PROFILES[journal]
    root = get_project_root()
    try:
        base_dir, spec_path = _find_manuscript_dir(root, name)
        if base_dir is None:
            return json_dict({"error": f"Manuscript '{name}' not found at docs/manuscript/{name}/manuscript.yml"})

        from notio.manuscript.schema import ManuscriptSpec, resolve_render_config
        from notio.manuscript.assembly import strip_frontmatter

        spec = ManuscriptSpec.from_yaml(spec_path)
        resolved = resolve_render_config(spec, base_dir)

        # --- Word count ---
        total_words = 0
        section_keys_present: set[str] = set()
        for entry in spec.sections:
            section_path = base_dir / entry.path
            if section_path.is_file():
                raw = section_path.read_text(encoding="utf-8")
                body = strip_frontmatter(raw)
                total_words += len(body.split())
                section_keys_present.add(entry.key)

        word_limit = profile["word_limit"]
        word_info: dict = {"current": total_words, "limit": word_limit or "none"}
        if word_limit and total_words > word_limit:
            word_info["over_by"] = total_words - word_limit

        # --- Figure count ---
        fig_count = len(spec.figures.mappings)
        fig_limit = profile["figure_limit"]
        fig_info: dict = {"current": fig_count, "limit": fig_limit or "none"}
        if fig_limit and fig_count > fig_limit:
            fig_info["over_by"] = fig_count - fig_limit

        # --- Required sections ---
        required_sections: list[dict] = []
        for req_key in profile["required_sections"]:
            present = req_key in section_keys_present
            required_sections.append({
                "key": req_key,
                "required": True,
                "present": present,
            })

        # --- CSL match ---
        csl_expected = profile["csl_name"]
        csl_configured = ""
        if resolved.csl:
            # Extract CSL name from path (e.g. ".projio/render/csl/apa.csl" → "apa")
            from pathlib import PurePosixPath
            csl_configured = PurePosixPath(resolved.csl).stem

        csl_info: dict = {
            "expected": csl_expected or "any",
            "configured": csl_configured or "none",
            "match": (not csl_expected) or (csl_expected in csl_configured),
        }

        # --- Warnings ---
        warnings: list[str] = []
        if word_limit and total_words > word_limit:
            warnings.append(f"Word count ({total_words}) exceeds {profile['name']} limit ({word_limit}) by {total_words - word_limit} words")
        if fig_limit and fig_count > fig_limit:
            warnings.append(f"Figure count ({fig_count}) exceeds {profile['name']} limit ({fig_limit}) by {fig_count - fig_limit}")
        missing_required = [s["key"] for s in required_sections if not s["present"]]
        if missing_required:
            warnings.append(f"Missing required sections for {profile['name']}: {', '.join(missing_required)}")
        if csl_expected and csl_expected not in csl_configured:
            warnings.append(f"CSL mismatch: {profile['name']} expects '{csl_expected}' but '{csl_configured or 'none'}' is configured")

        return json_dict({
            "name": name,
            "journal": journal,
            "journal_name": profile["name"],
            "word_count": word_info,
            "figure_count": fig_info,
            "required_sections": required_sections,
            "csl_match": csl_info,
            "warnings": warnings,
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


# --- Master document tools ---

def _master_available() -> bool:
    try:
        import notio.manuscript.master  # noqa: F401
        return True
    except ImportError:
        return False


def master_list() -> JsonDict:
    """List all master documents (docs/*/master.md) in the project."""
    if not _master_available():
        return _unavailable("master_list")
    root = get_project_root()
    try:
        from notio.manuscript.master import find_master_files
        masters = find_master_files(root)
        return json_dict({"masters": masters, "count": len(masters)})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def master_build(name: str, format: str = "pdf") -> JsonDict:
    """Build a master document to PDF/LaTeX/MD using the Lua transclusion filter.

    Args:
        name: Master document name (subdirectory under docs/).
        format: Output format (pdf, latex, md, docx, html).
    """
    if not _master_available():
        return _unavailable("master_build")
    root = get_project_root()
    try:
        from notio.manuscript.master import build_master
        output = build_master(root, name, format=format)
        return json_dict({
            "name": name,
            "format": format,
            "output": str(output.relative_to(root)),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})


def master_generate(name: str, sections: list[dict]) -> JsonDict:
    """Generate or regenerate a master.md with dual markers from a section list.

    Args:
        name: Document name (subdirectory under docs/).
        sections: List of section dicts with 'path' key (relative .md path) and optional 'title'.
    """
    if not _master_available():
        return _unavailable("master_generate")
    root = get_project_root()
    try:
        from notio.manuscript.master import generate_master_md

        content = generate_master_md(sections, name)
        master_path = root / "docs" / name / "master.md"
        master_path.parent.mkdir(parents=True, exist_ok=True)
        master_path.write_text(content, encoding="utf-8")
        return json_dict({
            "name": name,
            "path": str(master_path.relative_to(root)),
            "sections": len(sections),
        })
    except Exception as exc:
        return json_dict({"error": str(exc)})
