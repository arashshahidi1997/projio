"""MCP tools: presentation deck scaffolding, assembly, rendering, iteration.

Mirrors :mod:`projio.mcp.manuscripto`.

**Phase 1** — scaffolding + Marp build:
- ``present_init`` — scaffold a new deck under ``docs/presentations/<name>/``
- ``present_list`` — enumerate all decks
- ``present_status`` — per-section state, figures, bibliography
- ``present_assemble`` — write assembled markdown without calling marp-cli
- ``present_build`` — full pipeline (assemble → preresolve → marp-cli)
- ``present_validate`` — structural checks (sections, figures, citations)
- ``present_seed_from_paper`` — delegate to ``biblio.present.generate_slides``
  to produce a paper-seeded deck as a starting ``sections/seed.md``.

**Phase 2** — iteration ergonomics:
- ``present_section_context`` — one-call context for drafting a slide section
- ``present_figure_insert`` — insert a figio figure reference into a section
- ``present_cite_check`` — cross-check section citekeys against the bibliography
- ``present_overview`` — rich dashboard (per-section stats, missing/stale
  figures and citations, slide count)
- ``present_diff`` — compare current sections against the last assembled.md

**Phase 4** — cross-project imports:
- ``present_section_import`` — fetch a section from another project's deck via
  worklog and register it as an imported section in the host deck
- ``present_refresh_import`` — re-fetch a previously imported section
- ``present_freeze_import`` — lock an import against future refreshes

Cross-package glue (biblio for seeding, figio for figures, worklog for
cross-project imports) lives here, not in ``notio.present`` itself — this
keeps the notio subpackage cheap to graduate to a standalone
``packages/presentio/`` later.
"""

from __future__ import annotations

import re
from pathlib import Path

from .common import JsonDict, get_project_root, json_dict

# Shared with notio.manuscript — same pandoc citation syntax across both.
_CITE_RE = re.compile(r"@([a-zA-Z0-9_:.\-]+)")
_FIG_REF_RE = re.compile(r"!\[([^\]]*)\]\(fig:([a-zA-Z0-9_\-]+)\)")


def _present_available() -> bool:
    try:
        import notio.present  # noqa: F401

        return True
    except ImportError:
        return False


def _unavailable(tool: str) -> JsonDict:
    return {
        "error": (
            f"{tool} requires the notio.present subpackage. "
            "Install with: pip install -e packages/notio"
        )
    }


def _find_deck_dir(root: Path, name: str) -> tuple[Path | None, Path | None]:
    base = root / "docs" / "presentations" / name
    spec_path = base / "deck.yml"
    if not spec_path.is_file():
        return None, None
    return base, spec_path


def present_init(
    name: str,
    format: str = "marp",
    template: str = "lab-meeting",
    title: str = "",
) -> JsonDict:
    """Scaffold a new presentation deck.

    Args:
        name: Deck name (used as directory name under docs/presentations/).
        format: Renderer — ``marp`` (phase 1) or ``revealjs`` (phase 3).
        template: Section template — one of ``lab-meeting``, ``journal-club``,
            ``conference-talk``, ``progress-report``.
        title: Optional display title (defaults to a titleized ``name``).
    """
    if not _present_available():
        return _unavailable("present_init")
    root = get_project_root()
    try:
        from notio.present.schema import scaffold_deck

        base_dir = root / "docs" / "presentations" / name
        base_dir.mkdir(parents=True, exist_ok=True)
        spec = scaffold_deck(
            name,
            base_dir,
            format=format,
            template=template,
            title=title,
        )
        return json_dict(
            {
                "name": spec.name,
                "title": spec.title,
                "format": spec.format,
                "template": template,
                "path": str(base_dir.relative_to(root)),
                "spec_file": str(
                    (base_dir / "deck.yml").relative_to(root)
                ),
                "sections": [s.key for s in spec.sections],
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_list() -> JsonDict:
    """List all decks under docs/presentations/."""
    if not _present_available():
        return _unavailable("present_list")
    root = get_project_root()
    try:
        decks_dir = root / "docs" / "presentations"
        if not decks_dir.is_dir():
            return json_dict({"decks": [], "count": 0})

        from notio.present.schema import DeckSpec

        decks = []
        for child in sorted(decks_dir.iterdir()):
            spec_path = child / "deck.yml"
            if child.is_dir() and spec_path.is_file():
                try:
                    spec = DeckSpec.from_yaml(spec_path)
                    decks.append(
                        {
                            "name": spec.name,
                            "title": spec.title,
                            "format": spec.format,
                            "path": str(child.relative_to(root)),
                            "sections": len(spec.sections),
                        }
                    )
                except Exception as exc:
                    decks.append(
                        {
                            "name": child.name,
                            "error": f"failed to load deck.yml: {exc}",
                        }
                    )
        return json_dict({"decks": decks, "count": len(decks)})
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_status(name: str) -> JsonDict:
    """Show deck section state, figures, and bibliography inheritance."""
    if not _present_available():
        return _unavailable("present_status")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {
                    "error": (
                        f"Deck '{name}' not found at "
                        f"docs/presentations/{name}/deck.yml"
                    )
                }
            )

        from notio.manuscript.assembly import strip_frontmatter
        from notio.present.figures import resolve_figure_paths
        from notio.present.schema import DeckSpec, resolve_deck_render

        spec = DeckSpec.from_yaml(spec_path)

        sections_status = []
        for entry in sorted(spec.sections, key=lambda s: s.order):
            section_path = base_dir / entry.path
            exists = section_path.is_file()
            word_count = 0
            slide_breaks = 0
            if exists:
                raw = section_path.read_text(encoding="utf-8")
                body = strip_frontmatter(raw)
                word_count = len(body.split())
                slide_breaks = body.count("\n---\n")
            sections_status.append(
                {
                    "key": entry.key,
                    "path": entry.path,
                    "order": entry.order,
                    "exists": exists,
                    "word_count": word_count,
                    "slide_breaks": slide_breaks,
                    "imported": entry.import_ is not None,
                }
            )

        resolved_figs = resolve_figure_paths(spec, base_dir, format=spec.format)  # type: ignore[arg-type]
        missing_figs = [
            f.id for f in spec.figures if f.id not in resolved_figs
        ]

        resolved_render = resolve_deck_render(spec, base_dir)

        # Last build: look at output_dir mtime of deck.html / deck.pdf / deck.pptx
        build_dir = base_dir / spec.render.output_dir
        last_built: dict[str, str] = {}
        if build_dir.is_dir():
            for ext in ("html", "pdf", "pptx"):
                p = build_dir / f"{spec.name}.{ext}"
                if p.is_file():
                    last_built[ext] = str(p.relative_to(root))

        # Approximate total slide count: one per section + each intra-section break
        total_slides = sum(
            1 + s["slide_breaks"] for s in sections_status if s["exists"]
        )

        return json_dict(
            {
                "name": spec.name,
                "title": spec.title,
                "format": spec.format,
                "path": str(base_dir.relative_to(root)),
                "sections": sections_status,
                "total_words": sum(s["word_count"] for s in sections_status),
                "total_slides": total_slides,
                "figures": {
                    "total": len(spec.figures),
                    "resolved": len(resolved_figs),
                    "missing": missing_figs,
                },
                "bibliography": {
                    "bib_file": resolved_render["bib_file"],
                    "csl": resolved_render["csl"],
                    "inherited": (
                        not spec.bibliography.bib_file
                        and bool(resolved_render["bib_file"])
                    ),
                },
                "last_built": last_built,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_assemble(name: str) -> JsonDict:
    """Generate assembled markdown without calling marp-cli."""
    if not _present_available():
        return _unavailable("present_assemble")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.assembly import write_assembled
        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)
        path = write_assembled(spec, base_dir)
        return json_dict(
            {
                "name": spec.name,
                "assembled_path": str(path.relative_to(root)),
                "bytes": path.stat().st_size,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_build(
    name: str,
    format: str | None = None,
) -> JsonDict:
    """Build the deck.

    Dispatches on ``deck.yml``'s ``format:`` field:
    - ``marp`` → marp-cli (html/pdf/pptx)
    - ``revealjs`` → pandoc ``-t revealjs`` (html only)

    Args:
        name: Deck name.
        format: Output format override (e.g. ``html``, ``pdf``, ``pptx``).
            When omitted, uses ``spec.outputs`` or defaults to html.
    """
    if not _present_available():
        return _unavailable("present_build")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.render import render
        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)
        formats = [format] if format else None
        outputs = render(spec, base_dir, formats=formats)
        return json_dict(
            {
                "name": spec.name,
                "format": spec.format,
                "outputs": [str(p.relative_to(root)) for p in outputs],
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_validate(name: str) -> JsonDict:
    """Validate sections, figures, citations, and renderer availability."""
    if not _present_available():
        return _unavailable("present_validate")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.schema import DeckSpec
        from notio.present.validate import validate_deck

        spec = DeckSpec.from_yaml(spec_path)
        result = validate_deck(spec, base_dir)
        return json_dict(
            {
                "name": spec.name,
                "valid": result.valid,
                "errors": result.errors,
                "warnings": result.warnings,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_seed_from_paper(
    name: str,
    citekey: str,
    template: str = "journal-club",
    *,
    model: str = "sonnet",
    force: bool = False,
) -> JsonDict:
    """Scaffold a deck and seed its first section from a paper citekey.

    Delegates to :func:`biblio.present.generate_slides` for the LLM call
    (which reads docling output, figures, and metadata), then drops the
    result into ``docs/presentations/<name>/sections/seed.md`` of a
    newly-scaffolded deck.

    This tool is the bridge between biblio's paper-context machinery and
    presentio's iteration-first deck model. The LLM output is a *starting
    point*, not a finished deck — the agent iterates on the scaffolded
    sections from there.
    """
    if not _present_available():
        return _unavailable("present_seed_from_paper")
    try:
        import biblio.present  # noqa: F401
    except ImportError:
        return {
            "error": (
                "present_seed_from_paper requires the biblio package for "
                "paper-context assembly. Install with: pip install -e packages/biblio"
            )
        }

    root = get_project_root()
    try:
        from biblio.present import generate_slides
        from notio.present.schema import DeckSpec, scaffold_deck

        base_dir = root / "docs" / "presentations" / name
        deck_yml = base_dir / "deck.yml"

        # Scaffold the deck if it doesn't already exist.
        if not deck_yml.is_file():
            base_dir.mkdir(parents=True, exist_ok=True)
            scaffold_deck(name, base_dir, format="marp", template=template)

        # Generate LLM seed via biblio.
        seed_result = generate_slides(
            citekey,
            root,
            template=template,
            prompt_only=False,
            force=force,
            model=model,
        )
        if seed_result.get("error"):
            return json_dict({"error": seed_result["error"], "deck": name})

        seed_text = seed_result.get("slides_text") or ""
        if not seed_text:
            return json_dict(
                {
                    "error": "biblio.present returned no slide text",
                    "deck": name,
                }
            )

        # Strip any Marp frontmatter biblio prepended — presentio's
        # assemble_marp will prepend a deck-level frontmatter itself.
        from notio.manuscript.assembly import strip_frontmatter

        body = strip_frontmatter(seed_text)

        seed_section = base_dir / "sections" / "seed.md"
        seed_section.parent.mkdir(parents=True, exist_ok=True)
        seed_section.write_text(
            f"---\n"
            f"title: \"Seed from {citekey}\"\n"
            f"order: 15\n"
            f"deck: {name}\n"
            f"source_citekey: {citekey}\n"
            f"status: draft\n"
            f"tags: [presentation, section, seed]\n"
            f"---\n\n{body.strip()}\n",
            encoding="utf-8",
        )

        # Append the seed section to the deck if not already present.
        spec = DeckSpec.from_yaml(deck_yml)
        if not any(s.key == "seed" for s in spec.sections):
            from notio.present.schema import DeckSection

            spec.sections.append(
                DeckSection(key="seed", path="sections/seed.md", order=15)
            )
            import yaml

            deck_yml.write_text(
                yaml.dump(spec.to_dict(), default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )

        return json_dict(
            {
                "deck": name,
                "citekey": citekey.lstrip("@"),
                "template": template,
                "model": seed_result.get("model_used", model),
                "seed_section": str(seed_section.relative_to(root)),
                "deck_spec": str(deck_yml.relative_to(root)),
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


# ────────────────────────────────────────────────────────────────────
# Phase 2 — iteration ergonomics
# ────────────────────────────────────────────────────────────────────


def _parse_section_frontmatter(raw: str) -> dict:
    """Extract YAML frontmatter from a section file, returning {} on failure."""
    import yaml

    m = re.match(r"\A---\s*\n(.*?)\n---", raw, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def present_section_context(name: str, section: str) -> JsonDict:
    """One-call context for drafting a slide section.

    Returns current body, citations used, figures referenced, related
    notes and RAG hits seeded from the section key. Mirrors
    :func:`manuscripto.manuscript_section_context` but aware of slide
    breaks and figio-source figures.
    """
    if not _present_available():
        return _unavailable("present_section_context")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.manuscript.assembly import strip_frontmatter
        from notio.present.figures import resolve_figure_paths
        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        target = next((s for s in spec.sections if s.key == section), None)
        if target is None:
            return json_dict(
                {
                    "error": f"Section '{section}' not found",
                    "available_sections": [s.key for s in spec.sections],
                }
            )

        section_path = base_dir / target.path
        current_content = ""
        word_count = 0
        citations_used: list[str] = []
        slide_breaks = 0
        figures_used: list[str] = []
        frontmatter: dict = {}
        if section_path.is_file():
            raw = section_path.read_text(encoding="utf-8")
            frontmatter = _parse_section_frontmatter(raw)
            body = strip_frontmatter(raw)
            current_content = body
            word_count = len(body.split())
            citations_used = sorted(set(_CITE_RE.findall(raw)))
            slide_breaks = body.count("\n---\n")
            figures_used = [m.group(2) for m in _FIG_REF_RE.finditer(body)]

        # RAG hits seeded from section key + deck title
        rag_hits: list[dict] = []
        try:
            from .rag import rag_query

            query_text = f"{section.replace('-', ' ').replace('_', ' ')} {spec.title}"
            rag_result = rag_query(query=query_text, k=6)
            rag_hits = rag_result.get("results", [])  # type: ignore[union-attr]
        except Exception:
            pass

        # Figures from the deck spec — show built status
        resolved_figs = resolve_figure_paths(spec, base_dir, format="marp")  # type: ignore[arg-type]
        figures_info: list[dict] = []
        for fig in spec.figures:
            fig_entry = {
                "id": fig.id,
                "source": fig.source,
                "figio_figure": fig.figure,
                "caption": fig.caption,
                "built": fig.id in resolved_figs,
                "in_section": fig.id in figures_used,
            }
            if fig.id in resolved_figs:
                try:
                    fig_entry["output_path"] = str(
                        resolved_figs[fig.id].relative_to(root)
                    )
                except ValueError:
                    fig_entry["output_path"] = str(resolved_figs[fig.id])
            figures_info.append(fig_entry)

        # Related notes via semantic search
        related_notes: list[dict] = []
        try:
            from .notio import note_search

            search_result = note_search(
                query=section.replace("-", " ").replace("_", " "), k=5
            )
            related_notes = search_result.get("results", [])  # type: ignore[union-attr]
        except Exception:
            pass

        return json_dict(
            {
                "name": name,
                "section": section,
                "order": target.order,
                "path": str(section_path.relative_to(root)),
                "frontmatter": frontmatter,
                "current_content": current_content,
                "word_count": word_count,
                "slide_breaks": slide_breaks,
                "citations_used": citations_used,
                "figures_referenced": figures_used,
                "figures": figures_info,
                "rag_hits": rag_hits,
                "related_notes": related_notes,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_figure_insert(
    name: str,
    section: str,
    figure_id: str,
    position: str = "end",
) -> JsonDict:
    """Insert a figio figure reference into a deck section.

    Writes ``![caption](fig:<figure_id>)`` into the section file. At
    render time :func:`notio.present.figures.resolve_figure_paths`
    swaps the placeholder for the real path.

    Registers the figure id in ``deck.yml`` under ``figures:`` if it's
    not already there. Caption is taken from the existing mapping, or
    from a ``caption`` keyword you can set by editing the deck spec.

    Args:
        name: Deck name.
        section: Section key.
        figure_id: Figio figure id.
        position: ``"end"`` (default) or ``"start"`` — insert after
            frontmatter when ``"start"``.
    """
    if not _present_available():
        return _unavailable("present_figure_insert")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.manuscript.assembly import FRONTMATTER_RE
        from notio.present.schema import DeckFigure, DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        target = next((s for s in spec.sections if s.key == section), None)
        if target is None:
            return json_dict(
                {
                    "error": f"Section '{section}' not found",
                    "available_sections": [s.key for s in spec.sections],
                }
            )

        section_path = base_dir / target.path
        if not section_path.is_file():
            return json_dict(
                {"error": f"Section file not found: {target.path}"}
            )

        # Look up caption from any pre-existing figure mapping.
        caption = ""
        for fig in spec.figures:
            if fig.id == figure_id:
                caption = fig.caption
                break

        fig_ref = f"\n![{caption}](fig:{figure_id})\n"
        text = section_path.read_text(encoding="utf-8")

        if position == "start":
            m = FRONTMATTER_RE.match(text)
            if m:
                insert_pos = m.end()
                text = text[:insert_pos] + fig_ref + text[insert_pos:]
            else:
                text = fig_ref + text
        else:
            text = text.rstrip() + "\n" + fig_ref

        section_path.write_text(text, encoding="utf-8")

        # Register figure in deck.yml if missing.
        registered = any(f.id == figure_id for f in spec.figures)
        if not registered:
            spec.figures.append(
                DeckFigure(
                    id=figure_id,
                    source="figio",
                    figure=figure_id,
                    caption=caption,
                )
            )
            import yaml

            spec_path.write_text(
                yaml.dump(spec.to_dict(), default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )

        return json_dict(
            {
                "name": name,
                "section": section,
                "figure_id": figure_id,
                "position": position,
                "path": str(section_path.relative_to(root)),
                "registered_new_figure": not registered,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_cite_check(name: str) -> JsonDict:
    """Citation-focused validation across deck sections.

    Scans every section for ``@citekey`` markers, cross-checks against
    the inherited bibliography, and reports docling fulltext availability
    per citation (best-effort via biblio).
    """
    if not _present_available():
        return _unavailable("present_cite_check")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.schema import DeckSpec, resolve_deck_render

        spec = DeckSpec.from_yaml(spec_path)
        resolved = resolve_deck_render(spec, base_dir)

        # Collect citations per section
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
        bib_path_str = ""
        bib_rel = resolved["bib_file"]
        if bib_rel:
            bib_path = base_dir / bib_rel
            if bib_path.is_file():
                bib_text = bib_path.read_text(encoding="utf-8")
                bib_keys = set(re.findall(r"@\w+\{([^,\s]+)", bib_text))
                try:
                    bib_path_str = str(bib_path.relative_to(root))
                except ValueError:
                    bib_path_str = str(bib_path)

        # Docling extraction status
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
                found.append(
                    {
                        "citekey": citekey,
                        "sections": sections,
                        "has_fulltext": has_fulltext,
                    }
                )
                if not has_fulltext:
                    suggestions.append(
                        f"Run biblio_docling on '{citekey}' to enable RAG over its fulltext"
                    )
            else:
                missing.append({"citekey": citekey, "sections": sections})

        if missing:
            missing_keys = [m["citekey"] for m in missing]
            suggestions.insert(
                0, f"Run biblio_ingest for missing citekeys: {missing_keys}"
            )

        return json_dict(
            {
                "name": name,
                "bibliography_path": bib_path_str,
                "found": found,
                "missing": missing,
                "suggestions": suggestions,
                "total_citations": len(cite_to_sections),
                "bib_entries": len(bib_keys),
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_overview(name: str) -> JsonDict:
    """Rich deck dashboard — per-section stats, citations, figures, slide count.

    Superset of :func:`present_status` with citation cross-checking,
    figure staleness detection, and estimated slide count.
    """
    if not _present_available():
        return _unavailable("present_overview")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.manuscript.assembly import strip_frontmatter
        from notio.present.figures import resolve_figure_paths
        from notio.present.schema import DeckSpec, resolve_deck_render

        spec = DeckSpec.from_yaml(spec_path)
        resolved = resolve_deck_render(spec, base_dir)

        all_citekeys: set[str] = set()
        sections_status: list[dict] = []
        total_slides = 0
        for entry in sorted(spec.sections, key=lambda s: s.order):
            section_path = base_dir / entry.path
            exists = section_path.is_file()
            word_count = 0
            citation_count = 0
            figure_ref_count = 0
            slide_breaks = 0
            status = "missing"
            if exists:
                raw = section_path.read_text(encoding="utf-8")
                body = strip_frontmatter(raw)
                word_count = len(body.split())
                section_cites = _CITE_RE.findall(raw)
                citation_count = len(set(section_cites))
                all_citekeys.update(section_cites)
                figure_ref_count = len(_FIG_REF_RE.findall(body))
                slide_breaks = body.count("\n---\n")
                fm = _parse_section_frontmatter(raw)
                status = fm.get("status", "draft")
                total_slides += 1 + slide_breaks
            sections_status.append(
                {
                    "key": entry.key,
                    "title": entry.key.replace("_", " ").replace("-", " ").capitalize(),
                    "order": entry.order,
                    "word_count": word_count,
                    "citation_count": citation_count,
                    "figure_ref_count": figure_ref_count,
                    "slide_breaks": slide_breaks,
                    "status": status,
                    "imported": entry.import_ is not None,
                }
            )

        # Bibliography
        bib_file = resolved["bib_file"]
        bib_keys: set[str] = set()
        bib_entry_count = 0
        bib_path_str = ""
        if bib_file:
            bib_path = base_dir / bib_file
            if bib_path.is_file():
                bib_text = bib_path.read_text(encoding="utf-8")
                bib_keys = set(re.findall(r"@\w+\{([^,\s]+)", bib_text))
                bib_entry_count = len(bib_keys)
                try:
                    bib_path_str = str(bib_path.relative_to(root))
                except ValueError:
                    bib_path_str = str(bib_path)

        missing_citations = sorted(all_citekeys - bib_keys) if bib_keys else []

        # Figures
        resolved_figs = resolve_figure_paths(spec, base_dir, format="marp")  # type: ignore[arg-type]
        missing_figures = [f.id for f in spec.figures if f.id not in resolved_figs]
        # Staleness: source figio spec mtime > built output mtime
        stale_figures: list[str] = []
        from notio.present.figures import _figio_build_dir

        for fig in spec.figures:
            if fig.id not in resolved_figs or fig.source != "figio":
                continue
            build_dir = _figio_build_dir(fig, base_dir)
            # Find the source spec if we can — try common paths
            from notio.repo import repo_root

            proj_root = repo_root(base_dir) or base_dir
            fig_target = fig.figure or fig.id
            candidates = [
                proj_root / "figures" / f"{fig_target}.figurespec.yaml",
                proj_root / "figures" / f"{fig_target}.yaml",
            ]
            source_spec = next((c for c in candidates if c.is_file()), None)
            if source_spec is None:
                continue
            built = resolved_figs[fig.id]
            if source_spec.stat().st_mtime > built.stat().st_mtime:
                stale_figures.append(fig.id)

        # Last-built outputs
        build_dir = base_dir / spec.render.output_dir
        last_built: dict[str, str] = {}
        if build_dir.is_dir():
            for ext in ("html", "pdf", "pptx"):
                p = build_dir / f"{spec.name}.{ext}"
                if p.is_file():
                    try:
                        last_built[ext] = str(p.relative_to(root))
                    except ValueError:
                        last_built[ext] = str(p)

        return json_dict(
            {
                "name": spec.name,
                "title": spec.title,
                "format": spec.format,
                "path": str(base_dir.relative_to(root)),
                "sections": sections_status,
                "total_words": sum(s["word_count"] for s in sections_status),
                "total_slides": total_slides,
                "total_citations": len(all_citekeys),
                "total_figures": len(spec.figures),
                "missing_citations": missing_citations,
                "missing_figures": missing_figures,
                "stale_figures": stale_figures,
                "bibliography": {
                    "path": bib_path_str,
                    "entry_count": bib_entry_count,
                },
                "last_built": last_built,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_diff(name: str) -> JsonDict:
    """Compare current section content against the last assembled.md.

    Reports per-section word-count deltas, citekey drift, figure-ref
    drift, and a unified diff of the assembled markdown. Use after a
    round of edits to see what the next build would actually change.
    """
    if not _present_available():
        return _unavailable("present_diff")
    import difflib

    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.manuscript.assembly import strip_frontmatter
        from notio.present.assembly import assemble_marp
        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        current_text = assemble_marp(spec, base_dir)
        word_count_after = len(current_text.split())

        build_path = base_dir / spec.render.output_dir / "assembled.md"
        has_previous = build_path.is_file()
        previous_text = build_path.read_text(encoding="utf-8") if has_previous else ""
        word_count_before = len(previous_text.split()) if previous_text else 0

        # Per-section deltas
        section_changes: list[dict] = []
        for entry in spec.sections:
            section_path = base_dir / entry.path
            if not section_path.is_file():
                continue
            raw = section_path.read_text(encoding="utf-8")
            body = strip_frontmatter(raw)
            cites_now = sorted(set(_CITE_RE.findall(raw)))
            figs_now = sorted({m.group(2) for m in _FIG_REF_RE.finditer(body)})
            # Best-effort: find the matching section body in previous assembled.md
            # by locating the heading that matches the section key.
            previous_body = ""
            if has_previous:
                # Sections in Marp assembled.md are separated by "\n---\n".
                # Split on slide separators and match by first heading line.
                parts = previous_text.split("\n---\n")
                key_norm = entry.key.replace("-", " ").replace("_", " ").lower()
                for part in parts:
                    first_heading = next(
                        (
                            ln.lstrip("# ").strip().lower()
                            for ln in part.strip().splitlines()
                            if ln.strip().startswith("#")
                        ),
                        "",
                    )
                    if first_heading == key_norm or key_norm in first_heading:
                        previous_body = part
                        break
            prev_cites = sorted(set(_CITE_RE.findall(previous_body)))
            prev_figs = sorted({m.group(2) for m in _FIG_REF_RE.finditer(previous_body)})
            section_changes.append(
                {
                    "key": entry.key,
                    "word_count_before": len(previous_body.split()),
                    "word_count_after": len(body.split()),
                    "citations_added": sorted(set(cites_now) - set(prev_cites)),
                    "citations_removed": sorted(set(prev_cites) - set(cites_now)),
                    "figures_added": sorted(set(figs_now) - set(prev_figs)),
                    "figures_removed": sorted(set(prev_figs) - set(figs_now)),
                    "text_changed": previous_body.strip() != body.strip(),
                }
            )

        unified_diff = ""
        if has_previous:
            diff_lines = difflib.unified_diff(
                previous_text.splitlines(keepends=True),
                current_text.splitlines(keepends=True),
                fromfile=f"{spec.name} (last build)",
                tofile=f"{spec.name} (current)",
                lineterm="",
            )
            unified_diff = "".join(diff_lines)

        return json_dict(
            {
                "name": name,
                "has_previous_build": has_previous,
                "word_count_before": word_count_before,
                "word_count_after": word_count_after,
                "word_count_delta": word_count_after - word_count_before,
                "sections": section_changes,
                "unified_diff": unified_diff,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


# ────────────────────────────────────────────────────────────────────
# Phase 4 — cross-project imports via worklog
# ────────────────────────────────────────────────────────────────────


def _worklog_read_file(project_id: str, path: str):
    """Delegate to the worklog MCP tool for cross-project file reads.

    Imports the worklog MCP module lazily — worklog is not a hard
    dependency of projio, and decks can still be built without it.
    Returns the fetched text, or raises RuntimeError with a friendly
    message if worklog is unavailable.
    """
    try:
        # Worklog is typically mounted as its own MCP server; its functions
        # are importable from `worklog.mcp` when installed.
        from worklog.mcp import worklog_read_file as wl_read_file  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "worklog not available — cross-project imports require the "
            "worklog package. Install with: pip install -e <worklog-repo>"
        ) from exc
    result = wl_read_file(project_id=project_id, path=path)
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError(f"worklog_read_file failed: {result['error']}")
    if isinstance(result, dict) and "content" in result:
        return str(result["content"])
    if isinstance(result, str):
        return result
    raise RuntimeError(
        f"worklog_read_file returned unexpected shape: {type(result).__name__}"
    )


def _imports_dir(base_dir: Path) -> Path:
    """Return the per-deck imports cache directory."""
    return base_dir / "imports"


def _import_filename(from_project: str, source_deck: str, section: str) -> str:
    """Canonical file name for an imported section."""
    safe = (
        f"{from_project}-{source_deck}-{section}"
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )
    return f"{safe}.md"


def present_section_import(
    name: str,
    from_project: str,
    source_deck: str,
    section: str,
    key: str = "",
    order: int = 0,
    mode: str = "reference",
) -> JsonDict:
    """Import a section from another project's deck into the host deck.

    Fetches ``docs/presentations/<source_deck>/sections/<section>.md`` from
    the ``from_project`` via the worklog MCP server, writes a local copy
    under ``docs/presentations/<name>/imports/``, and registers a new
    section in the host deck's ``deck.yml`` with ``import:`` metadata.

    Extracts citekeys from the imported body and reports which are missing
    from the host project's bibliography — the agent is expected to run
    ``biblio_ingest`` on them explicitly. This keeps side effects scoped.

    Args:
        name: Host deck name.
        from_project: Source project id (as registered in worklog).
        source_deck: Source deck name in the remote project.
        section: Section key in the source deck.
        key: Section key in the host deck. Defaults to
            ``<from_project>-<section>``.
        order: Sort order in the host deck. Defaults to one slot after
            the current max.
        mode: ``"reference"`` (default, can be refreshed) or ``"freeze"``
            (locked against re-fetch).
    """
    if not _present_available():
        return _unavailable("present_section_import")
    if mode not in ("reference", "freeze"):
        return {"error": f"Invalid mode {mode!r}. Use 'reference' or 'freeze'."}
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.schema import DeckSection, DeckSectionImport, DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        # Fetch remote section via worklog
        remote_path = f"docs/presentations/{source_deck}/sections/{section}.md"
        try:
            body = _worklog_read_file(from_project, remote_path)
        except RuntimeError as exc:
            return json_dict({"error": str(exc), "remote_path": remote_path})

        # Resolve local key / order
        host_key = key or f"{from_project}-{section}".replace("/", "-")
        if any(s.key == host_key for s in spec.sections):
            return json_dict(
                {
                    "error": (
                        f"Section key '{host_key}' already exists in deck "
                        f"'{name}'. Pass a different key= to override."
                    )
                }
            )
        if order <= 0:
            existing_orders = [s.order for s in spec.sections]
            order = (max(existing_orders) + 10) if existing_orders else 10

        # Write the cache file. Prepend a small header so the imported
        # section carries projio-compatible frontmatter.
        imports_dir = _imports_dir(base_dir)
        imports_dir.mkdir(parents=True, exist_ok=True)
        filename = _import_filename(from_project, source_deck, section)
        cache_path = imports_dir / filename

        # Strip any pre-existing frontmatter from the remote body and
        # stamp our own with import provenance.
        from notio.manuscript.assembly import strip_frontmatter

        remote_body = strip_frontmatter(body).strip()

        import_header = (
            f"---\n"
            f'title: "Imported: {section}"\n'
            f"order: {order}\n"
            f"deck: {name}\n"
            f"imported_from_project: {from_project}\n"
            f"imported_from_deck: {source_deck}\n"
            f"imported_from_section: {section}\n"
            f"import_mode: {mode}\n"
            f"status: imported\n"
            f"tags: [presentation, section, imported]\n"
            f"---\n\n"
        )
        cache_path.write_text(import_header + remote_body + "\n", encoding="utf-8")

        # Add a DeckSection pointing at the cache file with import metadata
        import_meta = DeckSectionImport(
            from_project=from_project,
            deck=source_deck,
            section=section,
            mode=mode,
        )
        spec.sections.append(
            DeckSection(
                key=host_key,
                path=f"imports/{filename}",
                order=order,
                import_=import_meta,
            )
        )

        import yaml

        spec_path.write_text(
            yaml.dump(spec.to_dict(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        # Extract citekeys from the imported body and report which are
        # present in the host project's bibliography already.
        imported_citekeys = sorted(set(_CITE_RE.findall(remote_body)))
        missing_citekeys: list[str] = []
        if imported_citekeys:
            # Best-effort: consult the resolved bibliography to compute
            # missing keys. Same pattern as present_cite_check.
            try:
                from notio.present.schema import resolve_deck_render

                resolved = resolve_deck_render(spec, base_dir)
                bib_rel = resolved["bib_file"]
                if bib_rel:
                    bib_path = base_dir / bib_rel
                    if bib_path.is_file():
                        bib_text = bib_path.read_text(encoding="utf-8")
                        bib_keys = set(
                            re.findall(r"@\w+\{([^,\s]+)", bib_text)
                        )
                        missing_citekeys = sorted(
                            set(imported_citekeys) - bib_keys
                        )
                    else:
                        missing_citekeys = imported_citekeys
                else:
                    missing_citekeys = imported_citekeys
            except Exception:
                missing_citekeys = imported_citekeys

        # Extract figure references for reporting
        imported_figures = sorted(
            {m.group(2) for m in _FIG_REF_RE.finditer(remote_body)}
        )

        suggestions: list[str] = []
        if missing_citekeys:
            suggestions.append(
                f"Run biblio_ingest for missing citekeys: {missing_citekeys}"
            )
        if imported_figures:
            suggestions.append(
                f"Imported figure refs: {imported_figures}. Ensure they exist "
                f"in the host project (figio_build, or freeze them manually)."
            )

        return json_dict(
            {
                "deck": name,
                "from_project": from_project,
                "source_deck": source_deck,
                "source_section": section,
                "host_key": host_key,
                "host_path": f"imports/{filename}",
                "order": order,
                "mode": mode,
                "imported_citekeys": imported_citekeys,
                "missing_citekeys": missing_citekeys,
                "imported_figures": imported_figures,
                "suggestions": suggestions,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_refresh_import(name: str, section: str) -> JsonDict:
    """Re-fetch a previously imported section from its source project.

    Works on sections in ``reference`` mode only. Sections in ``freeze``
    mode refuse to refresh — use ``present_freeze_import`` to unfreeze
    first if you really mean it.

    Args:
        name: Host deck name.
        section: Section key in the host deck.
    """
    if not _present_available():
        return _unavailable("present_refresh_import")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        target = next((s for s in spec.sections if s.key == section), None)
        if target is None:
            return json_dict(
                {
                    "error": f"Section '{section}' not found in deck '{name}'",
                    "available_sections": [s.key for s in spec.sections],
                }
            )
        if target.import_ is None:
            return json_dict(
                {
                    "error": (
                        f"Section '{section}' is not an imported section. "
                        "Only imports can be refreshed."
                    )
                }
            )
        if target.import_.mode == "freeze":
            return json_dict(
                {
                    "error": (
                        f"Section '{section}' is frozen (import_mode=freeze). "
                        "Nothing to refresh."
                    )
                }
            )

        remote_path = (
            f"docs/presentations/{target.import_.deck}/sections/"
            f"{target.import_.section}.md"
        )
        try:
            body = _worklog_read_file(target.import_.from_project, remote_path)
        except RuntimeError as exc:
            return json_dict({"error": str(exc), "remote_path": remote_path})

        from notio.manuscript.assembly import strip_frontmatter

        remote_body = strip_frontmatter(body).strip()

        # Overwrite the cache file, preserving the existing frontmatter header
        cache_path = base_dir / target.path
        existing = (
            cache_path.read_text(encoding="utf-8") if cache_path.is_file() else ""
        )
        m = re.match(r"\A(---\s*\n.*?\n---\s*\n\s*)", existing, re.DOTALL)
        header = m.group(1) if m else ""
        cache_path.write_text(header + remote_body + "\n", encoding="utf-8")

        return json_dict(
            {
                "deck": name,
                "section": section,
                "from_project": target.import_.from_project,
                "source_deck": target.import_.deck,
                "source_section": target.import_.section,
                "mode": target.import_.mode,
                "bytes": cache_path.stat().st_size,
                "refreshed": True,
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})


def present_freeze_import(name: str, section: str = "") -> JsonDict:
    """Lock an imported section (or all imports) against future refreshes.

    Setting ``import_mode: freeze`` in deck.yml is all this does — the
    cache file itself doesn't change. Freezing is a deliberate act:
    use it before giving a talk from a deck that depends on another
    project's in-flight work.

    Args:
        name: Host deck name.
        section: Section key. Empty string freezes every imported
            section in the deck.
    """
    if not _present_available():
        return _unavailable("present_freeze_import")
    root = get_project_root()
    try:
        base_dir, spec_path = _find_deck_dir(root, name)
        if base_dir is None:
            return json_dict(
                {"error": f"Deck '{name}' not found at docs/presentations/{name}/deck.yml"}
            )

        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        frozen: list[str] = []
        skipped: list[str] = []
        for entry in spec.sections:
            if entry.import_ is None:
                continue
            if section and entry.key != section:
                continue
            if entry.import_.mode == "freeze":
                skipped.append(entry.key)
                continue
            entry.import_.mode = "freeze"
            # Update the cache file's frontmatter header too
            cache_path = base_dir / entry.path
            if cache_path.is_file():
                raw = cache_path.read_text(encoding="utf-8")
                raw = re.sub(
                    r"(?m)^import_mode:\s*reference\s*$",
                    "import_mode: freeze",
                    raw,
                )
                cache_path.write_text(raw, encoding="utf-8")
            frozen.append(entry.key)

        if section and not frozen and not skipped:
            return json_dict(
                {"error": f"Section '{section}' is not an imported section."}
            )

        import yaml

        spec_path.write_text(
            yaml.dump(spec.to_dict(), default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        return json_dict(
            {
                "deck": name,
                "frozen": frozen,
                "already_frozen": skipped,
                "total_frozen": len(frozen),
            }
        )
    except Exception as exc:
        return json_dict({"error": str(exc)})
