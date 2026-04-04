# Manuscript Subpackage Design Spec

**Status:** Draft
**Date:** 2026-03-31
**Package:** `notio.manuscript`
**Location:** `packages/notio/src/notio/manuscript/`

## Motivation

Academic manuscripts are fundamentally **ordered sequences of sections** — the
same primitive that notio already manages as notes with frontmatter, templates,
and indexing. Rather than creating a sixth standalone subsystem, manuscript
functionality lives as a notio subpackage that reuses the existing note
infrastructure and adds:

1. A `ManuscriptSpec` YAML schema for declaring manuscripts
2. Section ordering and assembly (concatenation by `order` field)
3. Pandoc-based rendering with `--citeproc` for bibliography integration
4. Figure insertion bridging figio assets into the manuscript

The full paper pipeline is: **figio** (figures) + **biblio** (citations) +
**notio/manuscript** (assembly + render) = paper.

## Design Principles

- **Sections are notes.** Each manuscript section is a Markdown file with YAML
  frontmatter, created and queried through standard notio mechanisms.
- **ManuscriptSpec is the manifest.** A single YAML file declares the section
  order, bibliography, CSL style, figure mappings, and render settings.
- **Assembly is concatenation.** No Lua transclusion filters — sections are
  concatenated in `order` field sequence with optional heading-level adjustment.
- **Rendering is pandoc.** The subpackage shells out to pandoc with `--citeproc`,
  passing the assembled Markdown and bibliography.
- **Filesystem-backed.** All state lives in files; no database.

## ManuscriptSpec Schema

The manifest lives at a user-chosen path (conventionally
`docs/manuscript/<name>/manuscript.yml`).

```yaml
# manuscript.yml
name: my-paper                    # unique identifier
title: "My Paper Title"
authors:
  - name: "Alice Smith"
    affiliation: "University X"
    email: alice@example.com
  - name: "Bob Jones"
    affiliation: "Institute Y"

# Section ordering — each entry maps to a note file
sections:
  - key: abstract
    path: sections/abstract.md      # relative to manuscript.yml parent
    order: 1
    heading_level: 0                # 0 = no heading adjustment
  - key: introduction
    path: sections/introduction.md
    order: 2
  - key: methods
    path: sections/methods.md
    order: 3
  - key: results
    path: sections/results.md
    order: 4
  - key: discussion
    path: sections/discussion.md
    order: 5
  - key: references
    path: sections/references.md
    order: 6
    heading_level: 0

# Bibliography — inherits from .projio/render.yml by default
# Override per-manuscript if needed; compiled.bib is the project-wide default
bibliography:
  bib_file: .projio/render/compiled.bib   # project compiled bib (default from render.yml)
  csl: .projio/render/csl/apa.csl         # CSL style file (default from render.yml)

# Figures (figio integration)
figures:
  dir: figures/                     # directory for figure specs/outputs
  mappings:                         # optional: map figure IDs to labels
    - id: fig-overview
      label: "Figure 1"
      caption: "System overview"
      spec: figures/overview.figurespec.yaml
    - id: fig-results
      label: "Figure 2"
      caption: "Main results"
      spec: figures/results.figurespec.yaml

# Render settings
render:
  output_dir: _build/              # relative to manuscript.yml parent
  formats: [pdf, docx, html]       # pandoc output formats
  template: null                    # optional pandoc template
  pandoc_args: []                   # extra pandoc CLI arguments
  variables: {}                     # pandoc template variables
```

## Section Notes

Each section file is a standard Markdown file. Sections may optionally include
YAML frontmatter for metadata, but it is **stripped during assembly** — only the
body content is concatenated.

```markdown
---
title: "Introduction"
order: 2
manuscript: my-paper
tags: [manuscript, section]
---

# Introduction

The study of neural oscillations...
```

Frontmatter fields used by the manuscript system:

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Section title |
| `order` | int | Sort position within manuscript |
| `manuscript` | str | Manuscript name (for cross-referencing) |
| `status` | str | Draft status: `draft`, `review`, `final` |

## Module Structure

```
src/notio/manuscript/
├── __init__.py          # Public API exports
├── schema.py            # ManuscriptSpec dataclass + YAML loading + render.yml merging
├── assembly.py          # Section ordering, frontmatter stripping, concatenation
├── render.py            # Pandoc subprocess invocation
├── figures.py           # Figure reference resolution, figio bridge
├── validate.py          # Section/citation/figure/pandoc validation
└── master.py            # Dual-marker master documents (Lua transclusion for plans/specs)
```

### schema.py

Dataclass-based schema loaded from YAML. No pydantic dependency — uses
`dataclasses` + a `from_yaml()` classmethod that parses with the stdlib-
compatible `yaml` library (PyYAML, already a transitive dependency).

```python
@dataclass
class Author:
    name: str
    affiliation: str = ""
    email: str = ""

@dataclass
class SectionEntry:
    key: str
    path: str
    order: int
    heading_level: int = 1   # default: keep as-is

@dataclass
class BibConfig:
    bib_file: str = ""
    csl: str = ""

@dataclass
class FigureMapping:
    id: str
    label: str = ""
    caption: str = ""
    spec: str = ""

@dataclass
class FiguresConfig:
    dir: str = "figures/"
    mappings: list[FigureMapping] = field(default_factory=list)

@dataclass
class RenderConfig:
    output_dir: str = "_build/"
    formats: list[str] = field(default_factory=lambda: ["pdf"])
    template: str | None = None
    pandoc_args: list[str] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)

@dataclass
class ManuscriptSpec:
    name: str
    title: str = ""
    authors: list[Author] = field(default_factory=list)
    sections: list[SectionEntry] = field(default_factory=list)
    bibliography: BibConfig = field(default_factory=BibConfig)
    figures: FiguresConfig = field(default_factory=FiguresConfig)
    render: RenderConfig = field(default_factory=RenderConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "ManuscriptSpec": ...

    @classmethod
    def from_dict(cls, data: dict, base_dir: Path) -> "ManuscriptSpec": ...
```

### assembly.py

```python
def load_sections(spec: ManuscriptSpec, base_dir: Path) -> list[Section]:
    """Load and order section files. Returns Section objects sorted by order."""

def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from Markdown text."""

def adjust_headings(text: str, level_offset: int) -> str:
    """Shift Markdown heading levels by offset (e.g., +1 makes # into ##)."""

def assemble(spec: ManuscriptSpec, base_dir: Path) -> str:
    """Concatenate sections in order into a single Markdown document.
    Strips frontmatter, adjusts heading levels, inserts section breaks."""

def write_assembled(spec: ManuscriptSpec, base_dir: Path) -> Path:
    """Assemble and write to output_dir/assembled.md. Returns path."""
```

### render.py

```python
def find_pandoc() -> Path | None:
    """Locate pandoc binary via shutil.which."""

def build_pandoc_command(
    input_path: Path,
    output_path: Path,
    fmt: str,
    spec: ManuscriptSpec,
    base_dir: Path,
) -> list[str]:
    """Build the pandoc CLI argument list."""

def render(spec: ManuscriptSpec, base_dir: Path, *, formats: list[str] | None = None) -> list[Path]:
    """Assemble then render via pandoc. Returns list of output paths."""

def render_single(input_path: Path, output_path: Path, fmt: str,
                  bib_file: Path | None, csl: Path | None,
                  template: Path | None, extra_args: list[str],
                  variables: dict[str, str]) -> Path:
    """Render a single format. Raises on pandoc failure."""
```

### figures.py

```python
def resolve_figure_paths(spec: ManuscriptSpec, base_dir: Path) -> dict[str, Path]:
    """Map figure IDs to their built output paths (SVG/PDF).
    Checks figio _build/ directories for latest outputs."""

def insert_figure_references(text: str, figures: dict[str, Path], base_dir: Path) -> str:
    """Replace figure placeholders (e.g., ![](fig:fig-overview)) with resolved paths."""

def validate_figures(spec: ManuscriptSpec, base_dir: Path) -> list[str]:
    """Check that all referenced figures exist. Returns list of missing figure IDs."""
```

## Public API

Exported from `notio.manuscript.__init__`:

```python
from notio.manuscript.schema import ManuscriptSpec
from notio.manuscript.assembly import assemble, write_assembled
from notio.manuscript.render import render
from notio.manuscript.figures import resolve_figure_paths, validate_figures
```

## CLI Integration

New subcommand group under the `notio` CLI:

```bash
notio manuscript init <name> [--dir PATH]    # scaffold manuscript.yml + sections/
notio manuscript status <spec>               # show section completion status
notio manuscript assemble <spec>             # concatenate sections → assembled.md
notio manuscript build <spec> [--format FMT] # assemble + pandoc render
notio manuscript validate <spec>             # check sections, bib, figures
```

## MCP Tools

Registered in notio's MCP server (`mcp/server.py`) and wrapped by projio at
`src/projio/mcp/manuscripto.py`:

| Tool | Description |
|------|-------------|
| `manuscript_init(name, dir?)` | Scaffold manuscript.yml and section files |
| `manuscript_list()` | List manuscripts in project |
| `manuscript_status(spec_path)` | Section count, word counts, missing sections |
| `manuscript_assemble(spec_path)` | Concatenate sections → assembled.md |
| `manuscript_build(spec_path, formats?)` | Full pipeline: assemble + render |
| `manuscript_validate(spec_path)` | Check sections, bibliography, figures |
| `manuscript_figure_insert(spec_path, figure_id, section_key)` | Insert figure reference into section |

## Integration Points

### biblio

- `bibliography.bib_file` in the spec points to a `.bib` file managed by biblio
- Pandoc's `--citeproc` resolves `@citekey` references against this file
- `biblio_merge()` should be run before `manuscript_build` to ensure the bib is up to date

### figio

- `figures.mappings[].spec` points to `*.figurespec.yaml` files
- `resolve_figure_paths()` looks in figio's `_build/` for rendered outputs
- Figure placeholders in section text use `![caption](fig:<figure-id>)` syntax
- `manuscript_validate` checks that all mapped figures have been built

### notio core

- Section files can be created via `notio note section` if a `section` note type
  is configured, or created directly as plain Markdown files
- `series` field can group sections belonging to the same manuscript
- Existing query functions (`list_notes`, `search_notes`) work on section files

## Rendering Pipeline

```
sections/*.md
    │
    ▼
assemble() ──→ assembled.md (frontmatter stripped, headings adjusted, figures resolved)
    │
    ▼
render() ──→ pandoc --citeproc --bibliography=refs.bib --csl=style.csl
    │
    ▼
_build/{name}.{pdf,docx,html}
```

## Error Handling

- Missing section file → `FileNotFoundError` with descriptive message
- Missing pandoc binary → `RuntimeError("pandoc not found")`
- Pandoc failure → `RuntimeError` with stderr captured
- Missing bibliography → warning (rendering proceeds without citeproc)
- Missing figure → warning in validate, placeholder left in assembled text

## Dependencies

- **Required:** PyYAML (already a transitive dep via other notio features)
- **Optional:** pandoc (system binary, checked at render time)
- No new Python package dependencies

## Testing Strategy

- Unit tests for schema loading (`from_yaml`, `from_dict`)
- Unit tests for assembly (ordering, frontmatter stripping, heading adjustment)
- Unit tests for figure reference resolution
- Integration test for full pipeline (requires pandoc fixture)
- All tests under `packages/notio/tests/test_manuscript.py`

## Agentic Tools

Manuscript MCP tools are split into priority tiers. P0 tools ship first and
cover the core agent workflow; later tiers add validation, diffing, and
journal-awareness.

### Ontology

```
ManuscriptSpec ──┬── SectionEntry* ──── section .md file (content)
                 │
                 ├── BibConfig ──────── .bib file (biblio)
                 │
                 ├── FiguresConfig ──── FigureMapping* ──── FigureSpec YAML (figio)
                 │
                 └── RenderConfig ───── pandoc settings
```

Interactions:

- **RAG** (indexio) — `rag_query` for literature/code context per section
- **biblio** — citation resolution, fulltext status, `.bib` parsing
- **figio** — figure build status, spec mtime comparison
- **notio** — `note_search` for related ideas/notes

### Lifecycle

```
scaffold → draft → populate → validate → render → review → submit
   │         │        │          │          │         │
   init    section  cite/fig   cite_check  build   diff/journal
           context  insert     overview
```

### P0 — Core agent tools

#### `manuscript_section_context(name, section)`

One-call context gathering for drafting a section.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |
| `section` | str | Section key (e.g. `introduction`) |

Returns:

| Field | Type | Source |
|-------|------|--------|
| `current_content` | str | Section file text (stripped frontmatter) |
| `rag_hits` | list[dict] | Top RAG results for section title (indexio `rag_query`) |
| `figures` | list[dict] | Figure mappings for this section + build status (figio) |
| `citations_used` | list[str] | `[@citekey]` patterns found in section text |
| `related_notes` | list[dict] | Notes matching section title (notio `note_search`) |
| `word_count` | int | Current word count of section body |

#### `manuscript_overview(name)`

Rich manuscript dashboard — superset of `manuscript_status`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |

Returns:

| Field | Type | Source |
|-------|------|--------|
| `sections` | list[dict] | Per-section: key, title, word_count, citation_count, figure_ref_count, status |
| `total_words` | int | Sum of all section word counts |
| `total_citations` | int | Unique citekeys across all sections |
| `total_figures` | int | Number of figure mappings |
| `missing_citations` | list[str] | Citekeys in text but not in .bib |
| `missing_figures` | list[str] | Figure IDs in mappings without built outputs |
| `stale_figures` | list[str] | Figure specs newer than built outputs (mtime comparison) |
| `bibliography` | dict | path, entry_count, papers_with_fulltext |

### P1 — Validation tools

#### `manuscript_cite_check(name)`

Citation-focused cross-subsystem validation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |

Returns:

| Field | Type | Description |
|-------|------|-------------|
| `found` | list[dict] | `{citekey, sections, has_fulltext}` for each resolved citation |
| `missing` | list[dict] | `{citekey, sections}` for unresolved citations |
| `suggestions` | list[str] | Actionable hints (e.g. "run biblio_docling on X") |

Cross-checks: section text → .bib file → biblio docling extraction status.

#### `manuscript_figure_build_all(name)`

Batch figure build via figio.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |

Returns: `list[{figure_id, status: "built"|"failed"|"skipped", path?, error?}]`

Iterates figure mappings with `spec` paths and invokes figio build on each.

### P2 — Diff and suggestion tools

#### `manuscript_diff(name)`

Compare current section content against last `_build/assembled.md` snapshot.
Detects section-level changes, word count deltas, and citation drift.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |

Returns:

| Field | Type | Description |
|-------|------|-------------|
| `sections_changed` | list[str] | Section keys whose content differs from the last build |
| `sections_added` | list[str] | Section keys present now but absent in last build |
| `sections_removed` | list[str] | Section keys in last build but absent now |
| `word_count_before` | int | Word count of last `_build/assembled.md` |
| `word_count_after` | int | Word count of current assembled text |
| `word_count_delta` | int | `after - before` |
| `citations_added` | list[str] | Citekeys in current text but not in last build |
| `citations_removed` | list[str] | Citekeys in last build but not in current text |
| `has_previous_build` | bool | Whether `_build/assembled.md` existed |

Uses `difflib` for comparison — no external dependencies. When no previous
build exists, all current sections are reported as added.

#### `manuscript_cite_suggest(name, section, claim?)`

Search the RAG biblio corpus for papers relevant to a section or claim text.
Returns ranked citekeys with relevance scores and snippets.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |
| `section` | str | Section key (e.g. `introduction`) |
| `claim` | str? | Optional claim text to search for (overrides section content) |

Returns:

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | list[dict] | Ranked citation suggestions |
| `suggestions[].citekey` | str | Citekey if extractable from RAG source path |
| `suggestions[].relevance_score` | float | RAG similarity score |
| `suggestions[].snippet` | str | Matching text snippet from corpus |
| `suggestions[].source` | str | Source document path |
| `query_used` | str | The text that was actually sent to RAG |
| `section` | str | Section key queried |

Degrades gracefully: returns `{error}` when RAG or biblio corpus is unavailable.

### P3 — Journal awareness

#### `manuscript_journal_check(name, journal?)`

Compare manuscript metrics against built-in journal target profiles.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Manuscript name |
| `journal` | str? | Journal key (e.g. `nature`, `plos-one`, `elife`, `biorxiv`). When omitted, lists available profiles. |

Returns:

| Field | Type | Description |
|-------|------|-------------|
| `journal` | str | Journal key used |
| `journal_name` | str | Full journal name |
| `word_count` | dict | `{current, limit, over_by?}` — current total vs journal limit |
| `figure_count` | dict | `{current, limit, over_by?}` — current total vs journal limit |
| `required_sections` | list[dict] | `{key, required, present}` — sections the journal expects, with present/missing status |
| `csl_match` | dict | `{expected, configured, match}` — whether the configured CSL matches the target journal |
| `warnings` | list[str] | Actionable issues (over word limit, missing required sections, CSL mismatch, etc.) |
| `available_profiles` | list[str] | Only returned when `journal` is omitted |

Built-in profiles are minimal dicts — extensible without a new schema. Initial
set: `nature`, `plos-one`, `elife`, `biorxiv`.

## Future Considerations

- **Pandoc filters:** Support for custom Lua/Python pandoc filters in render config
- **LaTeX templates:** First-class support for journal-specific LaTeX templates
- **Collaborative editing:** Section locking/status for multi-author workflows
- **Word count targets:** Per-section word count goals with progress tracking
