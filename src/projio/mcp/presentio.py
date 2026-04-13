"""MCP tools: presentation deck scaffolding, assembly, rendering (Marp).

Mirrors :mod:`projio.mcp.manuscripto`. Phase 1 exposes six tools:

- ``present_init`` — scaffold a new deck under ``docs/presentations/<name>/``
- ``present_list`` — enumerate all decks
- ``present_status`` — per-section state, figures, bibliography
- ``present_assemble`` — write assembled markdown without calling marp-cli
- ``present_build`` — full pipeline (assemble → preresolve → marp-cli)
- ``present_seed_from_paper`` — delegate to ``biblio.present.generate_slides``
  to produce a paper-seeded deck; the seed output is written into a new
  presentio deck as a starting ``sections/seed.md`` file.

Cross-package glue (biblio for seeding, figio for figures, worklog for
cross-project imports) lives here, not in ``notio.present`` itself — this
keeps the notio subpackage cheap to graduate to a standalone
``packages/presentio/`` later.
"""

from __future__ import annotations

from pathlib import Path

from .common import JsonDict, get_project_root, json_dict


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
    """Build the deck via marp-cli.

    Runs the full pipeline: assembly → figure resolution → citation
    preresolve (pandoc, if bib configured) → marp-cli render.

    Args:
        name: Deck name.
        format: Output format override (``html``, ``pdf``, ``pptx``).
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

        from notio.present.schema import DeckSpec

        spec = DeckSpec.from_yaml(spec_path)

        if spec.format == "marp":
            from notio.present.render_marp import render_marp

            formats = [format] if format else None
            outputs = render_marp(spec, base_dir, formats=formats)
            return json_dict(
                {
                    "name": spec.name,
                    "format": spec.format,
                    "outputs": [str(p.relative_to(root)) for p in outputs],
                }
            )
        elif spec.format == "revealjs":
            return json_dict(
                {
                    "error": (
                        "Reveal.js backend arrives in phase 3. "
                        "Set format: marp in deck.yml to build with phase 1."
                    )
                }
            )
        else:
            return json_dict({"error": f"Unknown deck format: {spec.format!r}"})
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
