# figio: parked, tools opt-in (decision, 2026-11-19)

Session `projio-figio · contemplation`. Decided by the user from the options below.

## Decision

1. **Park the figio package as it is.** Keep its tests green; add no features. Its status stays pre-alpha.
2. **Make the `figio_*` MCP tools opt-in.** Agents should not see them in projects that don't use figio.
3. **One named trigger for a trial:** pixecog's first manuscript figure. That figure combines a studio method
   schematic (SVG) with matplotlib data panels and needs journal checks. After that trial, decide again: narrow,
   fold or archive.

## The problem figio was meant to solve

figio assembles a journal figure from panels that were rendered separately. It works from a YAML FigureSpec
(panels, grid, annotations, style tokens), checks the composed SVG against a journal profile (width, minimum font
size, DPI, colour-blind safety), and caches unchanged panels between builds. In the figure lifecycle
([report vs figio boundary](quarto-reports.md)) it was the step after reports: maturing figures promoted to a spec
and carried into manuscripts and decks.

## What figio is today

- `packages/figio`: about 2,560 lines of source and 132 tests, all passing on 2026-11-19.
  - Matplotlib and script adapters; composer with constraints, arrows, brackets and a shared colorbar.
  - 13 journal profiles; validation; CairoSVG export; guides for a tutorial, targets and troubleshooting.
  - No change to `src/` since 2026-04-08 apart from housekeeping.
- All 8 issues in `packages/figio/docs/log/issue/` (2026-03-31) are implemented in the code and tests. Their
  `status: open` is out of date.
- In projio:
  - Six `figio_*` MCP tools, plus `manuscript_figure_insert`, `manuscript_figure_build_all` and
    `present_figure_insert`, which call figio.
  - notio's `manuscript/figures.py` reads figio build output, and `present/figures.py` accepts only
    `source: figio`.
  - The `figio` extra, which is also in `all`.
  - 14 tests in `tests/test_mcp_figio.py`, the figio-guide skill, handbook pages, mentions in 4 bundled skills.
  - About 113 tracked files mention figio.

## Does the problem show up in the user's work?

Not yet. The search covered tracked files. Untracked files in pixecog and largescale-infraslow were not searched.

| Project | figio | How figures are made |
|---|---|---|
| largescale-infraslow | not enabled | One Snakemake flow per figure (`code/pipelines/fig1`–`fig5`). Each figure comes from one matplotlib script, and nested `gridspec` lays out the panels (e.g. `fig2/scripts/render_fig2_ab.py`). Output goes to `results/figures_assembled/`. The graphical abstract came from the viz studio. |
| pixecog | enabled, `.projio/figio/` empty | Finding-set scripts with a shared style (`utils.figstyle`) and the `paper_figures` flow. `docs/infra/figures.md` (2026-11-05) lists figio as "installed, unused; try when the first manuscript figure is assembled". |
| lit-studio | enabled, `.projio/figio/` empty | Cropped published figures and Quarto pages. It also supplies the visual ontology and palette. |
| viz studio | n/a | About 92 deliveries, all schematics and animations, no data figures. |
| projio | `.projio/figio/` empty | — |

The only FigureSpec on disk is figio's own tutorial example.

## Why park rather than build, fold or archive

- **Matplotlib already covers the common case.** When every panel comes from one script, `gridspec` or
  `subplot_mosaic` composes the figure. A fixed figure size plus the shared style covers what the journal profiles
  would check. figio adds nothing there.
- **figio's distinct value is mixed-source composition.** It can put a studio SVG beside matplotlib panels in one
  checked figure. Matplotlib can't do this, and the alternative is hand assembly in Inkscape. That case has not come
  up yet, and pixecog's first manuscript figure is the first place it will.
- **Building more would be expansion with no user.** By always-complete, the package is complete at its scope
  (tests pass, the issues are done). Further work waits for a real figure.
- **Folding or archiving now would cost more than it saves.** Both would mean moving or removing tested code
  before the one real trial, and changing notio's present and manuscript figure code with nothing to test it
  against.
- **Its cost is mostly agent context, and opt-in tools remove that.** Nine figure tools load in every project
  while no project uses them.

## Follow-up kickoffs for the manager (not started)

1. **projio-core · figio tools opt-in.**
   - Default the projio MCP server to leave out `figio_*` unless the project enables figio. The trigger could be
     the `figio` entry in `.projio/packages.yml` or an explicit `PROJIO_MCP_TOOLS` entry; `toolset.py` already
     has a `figio` subsystem group.
   - Decide whether `manuscript_figure_build_all`, `manuscript_figure_insert` and `present_figure_insert` follow
     the same switch.
   - Update the instructions in the places named by the MCP tool-instructions rule and the 4 bundled skills that
     mention figio.
   - Keep `tests/test_mcp_figio.py` green.
2. **projio-figio · close stale issues.**
   - Mark the 8 figio issues done, each pointing to the commit or test that implemented it.
   - Make the README and pyproject status say pre-alpha and parked: the classifier says "3 - Alpha".
   - No code changes.
3. **pixecog (for the manager to pass on; another project) · figio trial at the first manuscript figure.**
   - When the first `paper_figures` figure that mixes a studio schematic with data panels is built, try it as a
     FigureSpec under `.projio/figio/`.
   - Report back what worked and what had to be done by hand.
   - That report reopens this decision.

## Ideas (parked)

- notio present figures accept only `source: figio`. Accepting a plain file source would remove that coupling.
  Do it only if a deck needs it before the trial.
- If the trial shows that only the composition and checks matter, fold `composer.py`, `validate.py` and
  `targets.py` into the notio manuscript figures and retire the YAML and adapter layers.
