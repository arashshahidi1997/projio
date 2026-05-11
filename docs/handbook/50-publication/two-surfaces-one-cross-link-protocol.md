# Two surfaces, one cross-link protocol

!!! note "Sources & anchors"
    - **Stack component:** Quarto/MkDocs
    - **Canonical artifact:** survey component 5 §Honest gap; prior-spec §F
    - **Workshop session:** Day-2 PM session 2 transition
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Handbook (mkdocs) + workshop (Quarto); cross-link via published URL.

## Two generators, two datasets

By the end of this chapter sequence you have seen two static-site generators
with complementary roles: MkDocs for the handbook (an evergreen docs site),
Quarto for the workshop (a multi-format course package). The handbook lives
in the projio repository. The workshop lives in its own DataLad dataset —
`teaching/agentic-workshop/` — that can be cloned, archived, or handed to
participants without pulling the entire projio repo.

That separation is a deliberate design choice. It keeps the workshop dataset
self-contained and lets it track its own version history independently of the
projio codebase. The cost of that independence is that the two surfaces cannot
link to each other with file-relative paths: a Quarto handout in
`teaching/agentic-workshop/` does not know where `docs/handbook/50-publication/mkdocs-for-the-site.md`
lives on a participant's machine. Relative paths break at the dataset
boundary.

The cross-link protocol exists to solve that problem without abandoning the
separation.

## The protocol

Three rules cover all the cross-linking cases that arise in practice.

**Rule 1 — Workshop → handbook: use the published URL.**
When a workshop handout references handbook content, it links to the
published site rather than a relative path:

```markdown
For a complete reference on plugin configuration, see the
[MkDocs for the site](https://projio.example.org/handbook/50-publication/mkdocs-for-the-site/)
chapter.
```

This works regardless of where the workshop dataset is cloned because the
published URL is stable and globally reachable. A participant running
through the exercises offline can follow the link on their phone. An
instructor distributing handouts as PDFs gets a clickable link that does
not rot. The workshop dataset stays detachable.

**Rule 2 — Handbook → source artifacts: use repo-relative paths with project name.**
When a handbook chapter references a canonical artifact, it cites the path
relative to the project root and names the project explicitly:

```markdown
The canonical example is `pixecog/mkdocs.yml` — in particular the
`plugins:` block, which demonstrates the full four-plugin baseline.
```

This is readable as prose, unambiguous about which project's copy is meant,
and does not depend on the handbook author's local working-copy path.
Never write `/storage2/arash/projects/pixecog/mkdocs.yml`; write
`pixecog/mkdocs.yml`. The latter is a pointer the reader can verify; the
former is a path that is wrong everywhere except one machine.

**Rule 3 — Handbook → handbook: use MkDocs-relative links.**
Cross-references within the handbook use MkDocs-resolved paths. The
`ezlinks` plugin resolves wiki-style `[[page-name]]` links automatically;
explicit paths like `../40-marimo/handbook-explorables.md` also work. Do
not duplicate content: if a concept is defined in one chapter, the other
chapter links to it. The handbook's internal cross-reference graph is
searchable and navigable; the Quarto workshop is not the place to maintain
a parallel explanation of the same concept.

## What this means in practice

Consider a Day-2 PM handout that covers MkDocs and transitions to projio.
The handout might contain:

```markdown
## MkDocs plugins

The four-plugin baseline (`search`, `monorepo`, `ezlinks`, `bibtex`) is
described in detail in the
[handbook chapter on MkDocs](https://projio.example.org/handbook/50-publication/mkdocs-for-the-site/).
We will not reproduce that content here — open the link and follow along.

## Exercise: add a plugin

Edit `msol/mkdocs.yml` to add `git-revision-date-localized`. Then run
`make docs` and verify the last-modified date appears on at least one page.
```

The handout delegates the explanation to the handbook and uses its own
space for the exercise. This is the intended pattern: the workshop is
practice; the handbook is reference. When the handbook explanation changes
(because a plugin is renamed, or the baseline grows), the handout does not
need to change — the published URL still resolves to the current version.

## The honest gap

As of the stack-axis survey (component 5 §Honest gap), projio has no
automated tooling for cross-linking from the workshop dataset into the
handbook's published site. The protocol above is a **social convention**,
not an enforced constraint. Nothing prevents a workshop handout from using
a broken absolute path or duplicating handbook prose inline.

The convention is workable at small scale. If the workshop grows beyond one
cohort, or if the published URL changes (e.g., because the site moves from
GitHub Pages to a lab server), a grep across the workshop dataset will find
all occurrences. A `linkcheck` step in the workshop's CI would catch broken
links automatically. Neither of these is implemented today; both are
straightforward additions. See [99-honest-gaps.md](../99-honest-gaps.md)
for the full accounting.

## The transition this chapter marks

At the end of Day-2 PM, the publication layer is complete: MkDocs hosts
the handbook; Quarto produces the workshop deliverables; cross-links
connect them without coupling the datasets. The next chapter introduces
[projio as the stack-aware layer](../60-projio/00-stack-aware-layer.md)
that makes the whole composition queryable — which is, among other things,
how an agent can locate the right handbook chapter to link to without
constructing the URL by hand.

## Further reading

- **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** — cross-page links and the `mkdocs-ezlinks` plugin that resolves bare filenames to correct relative paths.
- **[Quarto projects](https://quarto.org/docs/projects/quarto-projects.html)** — `_quarto.yml` and `{{< include >}}` for cross-document transclusion within a Quarto project.
