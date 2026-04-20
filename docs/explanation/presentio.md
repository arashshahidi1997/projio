# Presentio: Decks as Iteratable Artifacts

## The problem

Research presentations — journal clubs, conference talks, lab meetings, progress reports, thesis defenses — were a gap in the projio ecosystem. Before presentio, the only slide tooling was a single-paper LLM-backed Marp generator in biblio (`biblio present`). It was one-shot, paper-scoped, not exposed via projio's MCP server, and couldn't pull figures from figio or reuse content across projects.

Meanwhile, manuscripts had notio.manuscript — a full YAML-spec-and-sections artifact model with pandoc rendering, citation support, and figure integration. The pattern worked. The missing piece was a parallel subsystem for slides.

## The design principle

**Decks are artifacts, not outputs.** The same mental model as manuscripts: a YAML spec plus an ordered section tree plus a render pipeline. Agents iterate on sections one at a time; the system never generates a full deck in one shot.

This matters because research slides live or die by iteration. A journal-club deck needs to get the framing right before the results. A conference talk rewrites its motivation three times. A progress report is a narrative, not a data dump. One-shot generation optimizes for the wrong thing — it gives you something that looks done but isn't right.

Presentio treats the deck as a collaborative workspace between the human and the agent, with MCP tools as the conversation surface.

## What presentio is

A subpackage of notio at `notio.present`, parallel to `notio.manuscript`. Decks live under `docs/deliverables/presentations/<name>/` with:

```
docs/deliverables/presentations/<name>/
├── deck.yml                     # DeckSpec manifest
├── sections/
│   ├── title.md                 # each section = markdown + YAML frontmatter
│   ├── body.md
│   └── closing.md
├── imports/                     # cross-project section cache (phase 4)
├── figures/                     # local or frozen cross-project figures
└── build/
    ├── assembled.md             # concatenated source (gitignored)
    └── <name>.html              # rendered output (gitignored)
```

The DeckSpec YAML carries:

- `format: marp | revealjs` — which renderer to use
- `sections[]` — ordered list of section files with per-section `import:` metadata when imported from another project
- `figures[]` — figio figure references
- `bibliography:` — optional per-deck override, inherits from `.projio/render.yml` by default
- `render:` — theme, ratio, paginate, backend-specific args

Section files are plain markdown with notio-compatible YAML frontmatter so notio indexing surfaces them in note search.

## Dual backends, single source

Presentio supports two renderers:

| Backend | Binary | Output formats | Strengths |
|---------|--------|----------------|-----------|
| Marp | `marp-cli` | html, pdf, pptx | Fast, good defaults, pptx export |
| reveal.js | `pandoc -t revealjs` | html | Native pandoc citeproc, reuses manuscript's render stack |

The key insight is that section source files are **format-agnostic**. Pandoc's `--slide-level=0` makes horizontal rules (`---`) act as slide separators — which is exactly how Marp already splits slides. So the same `sections/*.md` source builds both backends by flipping `format:` in `deck.yml`. Only the frontmatter and renderer differ.

This lets you start a deck in Marp for fast iteration on content, then switch to reveal.js for a web-hosted talk with speaker notes and interactive features, without rewriting a single section.

Assembly is split from the start into `assemble_marp` and `assemble_pandoc`. Marp wants its own YAML-ish frontmatter (`marp: true`, `theme:`, `size:`); pandoc wants a full YAML metadata block (`title:`, `author:`, `date:`). These are incompatible, so sharing a single function would have grown a `if spec.format == "marp"` branch. Splitting up front keeps each assembly path simple.

Citation handling also diverges by backend:

- **Marp** has no citeproc support. Presentio runs a **render-stage** pandoc preresolve pass on the assembled markdown, replacing `@key` with formatted inline citations before handing off to marp-cli. The assembled markdown on disk keeps raw `@key` literals so the same source can be re-rendered in reveal.js without information loss.
- **reveal.js** uses pandoc's native `--citeproc`. No preresolve needed.

## Iteration ergonomics

The phase-2 tools exist specifically to make the section-by-section loop work:

| Need | Tool |
|------|------|
| What should I draft next? | `present_section_context(name, section)` — body + citations + figures + RAG hits + related notes in one call |
| Add a figure to a section | `present_figure_insert(name, section, figure_id)` — also registers in `deck.yml` |
| Are all my citations valid? | `present_cite_check(name)` — finds missing keys, suggests `biblio_ingest` |
| What changed since the last build? | `present_diff(name)` — per-section deltas + unified diff |
| Am I on track structurally? | `present_overview(name)` — stats, stale figures, slide count |

None of these "generate a slide" for you. They give you the context needed to draft well and catch structural problems early. Drafting is still the agent's job, and every draft should be shown to the human before moving to the next section.

The `literature-presentation` skill enforces this loop as a hard rule: *Never draft more than one section before human review*. Batch drafting defeats the whole point of presentio.

## Cross-project reuse

Phase 4 added `present_section_import`, which solves the pixecog-pulls-projio-slides use case: one project can reuse another project's deck sections by reference.

The mechanism is deliberately simple. `present_section_import` fetches a remote section via `worklog_read_file` (worklog is projio's cross-project file-reading MCP server), strips its frontmatter, stamps a new provenance header with `imported_from_project`, `imported_from_deck`, `imported_from_section`, and `import_mode`, then writes the cache file to `docs/deliverables/presentations/<name>/imports/<key>.md` and registers it in `deck.yml` with an `import:` block.

Two modes:

- **reference** (default) — cache is refreshable via `present_refresh_import`
- **freeze** — cache is locked; `present_refresh_import` refuses. Use before giving a talk from a deck that depends on in-flight upstream work.

Imports write physical cache files (not virtual references) for two reasons: (a) the assembly pipeline stays local — the regular `local_resolver` reads the cache, no special plumbing needed; (b) imports are git-tracked content, so the deck is self-contained and reproducible even if the upstream source moves.

The citekey handling is intentional: `present_section_import` *reports* which citekeys in the imported body are missing from the host project's bibliography, but does not run `biblio_ingest` automatically. Automatic network side-effects would violate the principle that MCP tools should do what you asked and not more. The agent is expected to explicitly run `biblio_ingest` for missing keys.

Cross-project **figures** are deferred to a future phase-4.1. Imported sections can still reference figures, but the figure files must exist in the host project (or come in as inline markdown images). In practice this has been enough for progress reports and talks, because figures are usually project-local by nature.

## Relationship to manuscripts and worklog

Presentio reuses three infrastructure pieces from elsewhere in the ecosystem:

| From | What presentio uses | Why |
|------|---------------------|-----|
| `notio.manuscript` | `strip_frontmatter`, `adjust_headings`, `FRONTMATTER_RE`, `HEADING_RE`, `ValidationResult`, `CITE_RE`, `find_pandoc` | Shared markdown parsing and pandoc detection |
| `.projio/render.yml` | `bibliography`, `csl`, `pdf_engine`, `lua_filter`, `resource_path` | Same render config inheritance pattern as manuscripts |
| `worklog_read_file` | Cross-project section imports | Soft dependency — lazy-imported, friendly error if missing |

Notio.present itself depends only on notio, pandoc/marp subprocesses, and the standard library. The cross-package glue (biblio for seeding, figio for figures, worklog for imports) lives in the projio MCP layer at `src/projio/mcp/presentio.py`, not inside the subpackage. This keeps notio.present cheap to graduate to a standalone `packages/presentio/` package later if it accretes enough surface.

The worklog integration is the key to the second use case from the original design conversation: progress reports that draw material from across projects. The `progress-report-deck` skill orchestrates `worklog_project_context`, `list_sessions`, and `goal_milestones` calls to gather material, then classifies into Done / In-flight / Blockers / Next / Side-findings buckets, then drafts the deck section-by-section in the host project.

## Phased delivery

| Phase | What shipped |
|-------|--------------|
| 1 | DeckSpec schema, assembly, Marp backend, 7 MCP tools, 4 scaffold templates |
| 2 | `section_context`, `figure_insert`, `cite_check`, `overview`, `diff`, and the `literature-presentation` / `progress-report-deck` skills |
| 3 | reveal.js backend via pandoc, format dispatcher, dual-backend assembly |
| 4 | Cross-project imports via worklog, refresh, freeze |

Phase 5 is future work: pptx polish, rehearsal skill (slide-count budget, timing estimates, speaker-notes coverage), Google Slides export-only path. The core loop works today without any of these.

## What presentio is not

- **Not a slide generator.** Presentio provides the iteration surface; drafting is the agent's job with the human in the loop.
- **Not a Google Slides replacement.** Google Slides integration would be export-only at best (pptx upload via Drive API with no round-trip), because any collaborative edit in the web UI violates the "repo is the unit of knowledge" principle. If you need live collaborative editing with a non-technical stakeholder, use Google Slides and live with the fact that the source of truth moves off-repo.
- **Not a one-click path from a paper to a finished deck.** `present_seed_from_paper` produces a *starting point* section, not a finished deck. The difference matters — you iterate on the seed the same way you would any other section.
- **Not magic.** Every tool is small, inspectable, and has a narrow contract. The intelligence lives in the agent + human loop, not in hidden heuristics.
