# Manuscript tools: real use and the Quarto cutover (MTUSE)

Status: survey, 2026-11-24. Read-only; no code changed.
Input to the decision in [slim.md §7](slim.md#7-e-manuscript-and-present-options-only): `notio.manuscript` retires
after pixecog's Quarto cutover, and the `manuscript_*` / `master_*` MCP tools are checked for real use first.

## 1. How the use was counted

- Every Claude Code transcript on gamma2 under `~/.claude/projects/*/` (all `*.jsonl`, subagent files included):
  `tool_use` blocks whose tool name ends in `manuscript_*` or `master_*`, paired with their `tool_result`.
- Bash commands in the same transcripts for the CLI paths: `notio manuscript …`, `projio manuscript …`,
  `prepare_includes.py`, `collect_stats.py`.
- Codex session logs under `~/.codex/sessions` for the same tool names.

Coverage. Transcripts start 2026-07-13 (pixecog, 207 files), 2026-08-12 (gecog, 3), 2026-08-15
(largescale-infraslow, 72), 2026-08-24 (sirocampus, 7), 2026-09-11 (projio, 62). `cleanupPeriodDays` is 3650, so
nothing was pruned. lit-studio has no Claude transcript folder on gamma2. Sessions on the laptop are not covered.
pixecog's `manuscript.yml` dates from 2026-04, before the transcripts begin, so any use in its first three months is
not visible here.

## 2. Result: five calls in total

| When | Project | Tool | What it was for | Outcome |
|------|---------|------|-----------------|---------|
| 2026-09-18 14:34 | pixecog | `manuscript_status pixecog` | check sections before a build | ok |
| 2026-09-18 14:34 | pixecog | `manuscript_build pixecog pdf` | render the PDF | `_build/pixecog.pdf` |
| 2026-09-18 14:34 | pixecog | `manuscript_build pixecog latex` | render LaTeX | `_build/pixecog.latex` |
| 2026-09-19 21:48 | pixecog | `manuscript_build pixecog pdf` | rebuild, the evening before the Quarto path was added (2026-09-19/20) | `_build/pixecog.pdf` |
| 2026-08-07 20:02 | gecog | `manuscript_list` | discovery | no manuscripts |

No CLI use (`notio manuscript`, `projio manuscript`) appears in any Bash call, and nothing in the Codex logs.
largescale-infraslow, sirocampus, projio and lit-studio: zero calls. lit-studio's `_quarto.yml` is a local website
render of its wiki, not a manuscript.

Since 2026-09-20 pixecog builds the paper through Quarto (`snakemake paper` runs `quarto render pixecog.qmd`); the
pandoc outputs in `_build/` were last written 2026-09-19.

## 3. Per tool

"Quarto?" says whether the tool can target a Quarto manuscript. Today every tool locates the manuscript by
`docs/manuscript/<name>/manuscript.yml` and reads `ManuscriptSpec`, so none works on a Quarto project without an
adapter. The column says what the adapter would take.

| Tool | Calls | Quarto? | Verdict |
|------|------:|---------|---------|
| `manuscript_init` | 0 | no: scaffolds `manuscript.yml` | retire (the decision: Quarto templates and `quarto create` scaffold) |
| `manuscript_list` | 1 (empty) | easy: find `_quarto.yml` beside an entry `.qmd` under `docs/manuscript/` | retire; `find` does it |
| `manuscript_status` | 1 | adapter: section list from the entry `.qmd` include lines, status from section frontmatter | retire unless section status tracking is kept (gap G7) |
| `manuscript_build` | 3 | no: pandoc | retire; `quarto render` or `snakemake paper` |
| `manuscript_validate` | 0 | partial: section existence and citekeys could read the include graph | retire; fold the citekey part into `cite_check` |
| `manuscript_assemble` | 0 | no: writes `_build/assembled.md` | retire |
| `manuscript_figure_insert` | 0 | no: `fig:<id>` mappings (pixecog's are empty) | retire |
| `manuscript_figure_build_all` | 0 | no: figio mappings; figio is parked | retire |
| `manuscript_section_context` | 0 | adapter: needs section files and the bibliography path | candidate to port (named in the decision); unused |
| `manuscript_overview` | 0 | adapter, same as status | retire |
| `manuscript_cite_check` | 0 | adapter: citekeys from section text, bib path from the `.qmd` frontmatter or render.yml | port (named in the decision); the useful one |
| `manuscript_cite_suggest` | 0 | text only, but built on RAG, which is not trusted yet | retire; literature-sourcing covers it |
| `manuscript_diff` | 0 | adapter: needs a snapshot; `assembled.md` does not exist under Quarto, so diff against git or a `quarto render --to markdown` output | port only if asked; unused |
| `manuscript_journal_check` | 0 | adapter: word count from sections, figure count from `{#fig-…}` labels | port (named in the decision); unused |
| `manuscript_nav` | 0 | no: MkDocs nav | retire with MkDocs |
| `master_list` / `master_build` / `master_generate` / `master_nav` | 0 | no: `{% include-markdown %}` + Lua filter master docs for MkDocs | retire. Remaining `master.md` files: gecog `docs/plan/master.md` (2026-04, questio plan), projio `examples/demo-01` and `docs/specs/pipeio/legacy-pipeline-spec` |

Summary: only `manuscript_status`, `manuscript_build` and `manuscript_list` were ever called, by one project, in two
days of September. The four text tools the decision names (`cite_check`, `journal_check`, `section_context`, `diff`)
have no calls. Porting is a choice for the future, not something current work depends on. If one is ported,
`cite_check` gives the most for the least: unresolved citekeys are the one check Quarto reports only as render
warnings.

## 4. pixecog: the two builds side by side

Both read `docs/manuscript/pixecog/sections/*.md`.

| | pandoc (manuscripto) | Quarto |
|---|---|---|
| entry | `manuscript.yml` (`defaults_from: .projio/render.yml`) | `_quarto.yml` + `pixecog.qmd` |
| order | `sections[].order` | `{{< include _includes/<key>.qmd >}}` lines in `pixecog.qmd` |
| section frontmatter | stripped in `assemble()` | stripped by `scripts/prepare_includes.py` into `_includes/` (gitignored) |
| title block | `sections/cover.md` (hand-written superscripts, equal contribution, corresponding author, submission date) | `.qmd` frontmatter: `author`, `affiliations`, `equal-contributor`, `corresponding` |
| bibliography, CSL | from render.yml via `defaults_from` | hard-coded paths in `pixecog.qmd` frontmatter (same files) |
| pdf engine, layout | `lualatex` from render.yml; no geometry or fonts set | `lualatex`, a4, 2.5 cm, 11 pt, colored links in `_quarto.yml` |
| figures | none (`figures.mappings: []`) | three figures from `results/figures/` with `#fig-` labels and cross-refs |
| numbers in prose | `{{< meta stats.… >}}` passes through literally (8 in `methods.md`) | `scripts/collect_stats.py` folds `results/stats/*.yml` into `_stats_meta.yml` |
| formats | pdf, latex | pdf (`keep-tex` gives `.tex`), docx for co-author comments |
| sections included | all nine, cover and the empty `authors` stub included | seven; cover replaced by frontmatter, `authors` stub left out |
| build target | `manuscript_build` MCP tool | `snakemake paper` (paper_figures flow), depends on `figures.done` |

The pandoc path is already behind: its Methods prints raw shortcodes and it has no figures.

Two things the pandoc path claims but does not do, noted for the record (no fix, since it retires):
`resolve_render_config` resolves `lua_filter` but `render()` never passes it to pandoc, and render.yml's
`manuscript` profile (`number_sections`, `citeproc`) is not applied by `manuscript_build`.

## 5. Gap list for pixecog's cutover

What the pandoc path gives that the Quarto path does not have yet:

- **G1. One source for render settings.** The pandoc path reads bibliography, CSL and pdf engine from
  `.projio/render.yml`. The Quarto path copies them into `pixecog.qmd` and `_quarto.yml` by hand ("Render values
  mirror .projio/render.yml"). If render.yml changes (say a different CSL), the paper silently keeps the old one.
  Fix: a pre-render step, or `projio sync`, that writes `_render_meta.yml` (bibliography, csl, pdf-engine) from
  render.yml, listed under `metadata-files`.
- **G2. Compiled bibliography freshness.** Neither path rebuilds `compiled.bib`. The `paper` rule does not depend on
  it, so a citekey added to Zotero after the last `biblio_compile` renders as "?". Fix: make `compiled.bib` an input
  of `rule paper`, or run `biblio compile` as the first pre-render step.
- **G3. Title block rendering.** The pandoc cover printed affiliations, equal contribution and the corresponding
  author. Quarto's frontmatter carries all of these, but the default `pdf` article format may print names only.
  Check the built PDF; if they are missing, pick a Quarto journal format or a small title-block partial.
  Submission date: set `date:` in the frontmatter.
- **G4. Citation check before render.** `manuscript_validate` and `manuscript_cite_check` listed unresolved
  citekeys per section. Quarto prints "Citation not found" warnings into the render log only
  (`derivatives/.../logs/paper.log`). Fix: a ported `cite_check` that reads the include graph, or a log grep in the
  rule.
- **G5. A build agents can call.** `manuscript_build` was an MCP tool. Now the build is `snakemake paper`
  (reachable through `pipeio_run`) or `quarto render` in the Quarto pixi env. No new tool needed; the template's
  README and the project CLAUDE.md should name the command.
- **G6. Section order lives in the `.qmd`.** `manuscript.yml` stops being read. Delete it at cutover so two
  orders cannot drift; `pixecog.qmd` is then the only order.
- **G7. Section status.** Section frontmatter (`status`, `order`, `tags`) fed `manuscript_status`. The Quarto path
  strips it and nothing reads it. Decide: keep `sections/*.md` with frontmatter plus `prepare_includes.py`
  (status stays greppable), or convert sections to frontmatter-free `.qmd` and track status elsewhere. Keeping the
  frontmatter costs one script and keeps sections as notio notes.
- **G8. The `authors.md` stub.** Empty, dropped by the Quarto path. Author contributions need a home before
  submission (a `sections/contributions.md` include).
- **G9. Retire the pandoc build.** Then remove `manuscript.yml`, `_build/assembled.md`, `_build/pixecog.{pdf,latex}`,
  `sections/cover.md`, and the "coexists" comment in `_quarto.yml`. `docs/manuscript/draft/manuscript.yml`
  (Ramon's working draft, one section, no authors) goes the same way or becomes a plain markdown file.

Not gaps: LaTeX output (`keep-tex`), figure mappings (unused; `results/` indirection replaces them), heading-level
shifts (unused), the Lua include filter (never applied).

## 6. Proposed projio "Quarto manuscript" template

Per the decision, notio does not scaffold Quarto, and the project glue lives in projio. The template is files plus
a skill; there is no new MCP tool.

```
src/projio/data/templates/quarto-manuscript/
  README.md                 how to copy, the conventions below, the build command
  _quarto.yml               project.render = [<name>.qmd]; pre-render scripts; metadata-files;
                            format pdf (lualatex, keep-tex) + docx; resource-path: ., ../../../results
  template.qmd              frontmatter: title, author (affiliations, corresponding, equal-contributor),
                            date; bibliography/csl come from _render_meta.yml; include list; # References + ::: {#refs}
  sections/                 abstract, introduction, methods, results, discussion, contributions (.md, notio frontmatter optional)
  scripts/
    prepare_includes.py     pixecog's, unchanged: sections/*.md -> _includes/*.qmd, .qmd passed through
    collect_stats.py        pixecog's, unchanged: results/stats/*.yml -> _stats_meta.yml
    render_meta.py          new (G1): .projio/render.yml -> _render_meta.yml (bibliography, csl, pdf-engine);
                            optional biblio compile check (G2)
  .gitignore                _includes/, _build/, *.tex, _stats_meta.yml, _render_meta.yml, .quarto/
```

Conventions the README states:

1. Prose lives in `sections/`; `_includes/` is generated and never edited.
2. Numbers in prose come from stats sidecars: `{{< meta stats.<file>.<key> >}}`, presentation-ready values, stable
   keys, no dots in keys.
3. Figures are referenced from `results/`, never from a producing derivative directory.
4. Build: `quarto render <name>.qmd` in the project's Quarto env, or a Snakemake target that depends on the figures
   and on `compiled.bib`. A snippet for the `paper` rule ships in the README.
5. Citations: `[@citekey]` against `.projio/render/compiled.bib`.

Delivery: a short ecosystem skill (`quarto-manuscript`) that copies the folder into `docs/manuscript/<name>/`,
renames `template.qmd`, and fills the frontmatter; it pairs with the existing `quarto-authoring` skill for Quarto
syntax. The scripts stay stdlib + PyYAML so they run under whatever Python Quarto resolves.

## 7. Order of work this suggests

1. pixecog: G1, G2, G3 check, G8, then G9 (drop the pandoc path). That is the cutover.
2. projio: lift the three scripts into the template above, with pixecog's copies as the source.
3. notio: remove `notio.manuscript` and `master.py`; projio: remove `mcp/manuscripto.py` and `manuscript_cmd.py`,
   or keep `cite_check` alone, ported to read a Quarto manuscript (the only tool with a case).
