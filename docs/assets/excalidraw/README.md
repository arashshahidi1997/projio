# Excalidraw diagrams

Hand-drawn-style diagrams for projio docs and decks. Source files
(`.excalidraw`, JSON) live alongside their rendered SVGs
(`.excalidraw.svg`) using the Obsidian-style **pair-file convention**:

```
docs/assets/excalidraw/
  <name>.excalidraw          # editable JSON — source of truth
  <name>.excalidraw.svg      # rendered SVG — what docs/slides reference
```

## Editing

**Primary editor: self-hosted Excalidraw at <http://beta:5000>**
(see `/storage2/arash/infra/README.md` for setup + persistence details).
Same UI as excalidraw.com, fully local, lab-network only.

1. Open <http://beta:5000>
2. **File → Open** → load `<name>.excalidraw`
3. Make changes
4. **File → Save to disk** to overwrite the `.excalidraw`
5. **Export image (⌘/Ctrl+Shift+E)** → SVG → save as `<name>.excalidraw.svg`

Both files get committed.

Alternatives:
- **VS Code extension** — `pomdtr.excalidraw-editor` or
  `excalidraw.excalidraw-editor`, edits in-IDE without a server
- **excalidraw.com** — fallback if beta is down; same UI, files stay
  local since "File → Save to disk" never uploads

## Programmatic SVG export (batch)

To re-render every SVG without clicking through the canvas, use
`@swiftlysingh/excalidraw-cli` via npx on a host with Node ≥ 18 (e.g.
beta):

```bash
ssh beta
cd /storage2/arash/projects/projio/docs/assets/excalidraw
for f in *.excalidraw; do
  npx -y @swiftlysingh/excalidraw-cli convert "$f" --format svg -o "${f}.svg"
done
```

The `<!-- svg-source:excalidraw -->` watermark in each output confirms
the official Excalidraw rendering pipeline produced the SVG — visual
fidelity matches the live app.

Tools that did **not** work, in case you find them recommended elsewhere:
- `excalidraw-to-svg` (npm) — broken peer-dep path when run via npx
- `excalirender` — only published as a Bun-compiled binary on GitHub
  releases, not on npm

## Embedding

Markdown:

```markdown
![Projio shape](../assets/excalidraw/projio-shape.excalidraw.svg)
```

Reveal.js / Marp section files: same syntax, paths relative to the
section file.

## Why two formats

The SVG is what builds — every renderer (mkdocs, reveal.js, Marp,
pandoc) handles it natively, no plugin needed. The `.excalidraw` JSON
keeps the diagram **editable** so future-you (or a collaborator) can
adjust labels, positions, or add elements without redrawing from
scratch. SVG-only would lose that.

## When to use Excalidraw vs. mermaid

- **Excalidraw**: conceptual / explanatory diagrams that change rarely
  and benefit from a friendly hand-drawn aesthetic. Examples:
  architecture sketches, the delegation model, code-tier promotion,
  figure-lifecycle.
- **Mermaid**: anything that should track code or auto-render — DAGs,
  dependency graphs, schema diagrams. Mermaid is grep-able; Excalidraw
  is not.

Don't replace mermaid wholesale. Both have a place.

## Current diagrams

| File | Concept | Intended embed sites |
|------|---------|---------------------|
| `projio-shape.excalidraw{,.svg}` | Repo → projio → MCP → 4 layered subpackages | `docs/index.md`, deck `shape.md` |
| `delegation-model.excalidraw{,.svg}` | Engineering vs. science panels with downstream→upstream arrows | `docs/explanation/delegation-model.md`, deck `delegation-model.md` |
| `figure-lifecycle.excalidraw{,.svg}` | notebook → report → figio → manuscript/deck (one-way promotion door at figio) | `docs/specs/quarto-reports.md` §5, possibly home page sidebar |
| `code-tiers.excalidraw{,.svg}` | notebook → script → utils → core lib (stacked tiers) | `docs/specs/pipeio/code-tiers.md` |
| `bib-pipeline.excalidraw{,.svg}` | srcbib + modkey → merged.bib + modkey.bib → compile → compiled.bib | `docs/specs/biblio/bib-architecture.md` |

(Skipping `subpackage-layers` — redundant with `projio-shape` since both convey the same layering.)
