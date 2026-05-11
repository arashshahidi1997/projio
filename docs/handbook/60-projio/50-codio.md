# codio: code as catalog

!!! note "Sources & anchors"
    - **Stack component:** projio
    - **Canonical artifact:** `cogpy`'s ~40 external mirrors + `code/lib/*` registered with `role: core` (pixecog, gecog)
    - **Workshop session:** Day-3 AM session 2
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

Library catalog with `role: core/shared/external`; `codio_discover`
for cross-project code search. The pain codio solves is *the agent
reinvents primitives*.

## The pain

A new analysis flow needs a band-pass filter, a BIDS path helper, a
yaml-loading helper, and a small dataclass for electrode metadata.
The agent doing the drafting has three options. (1) Write each from
scratch — risk: the dataclass already exists in `code/lib/cogpy/`,
the band-pass is in `code/lib/labbox/`, and the path helper is in
`code/lib/labpy/`. (2) Search the codebase by grep — risk: the agent
finds nothing for "filter" because the function is called
`lowpass()`. (3) Ask the lab maintainer — risk: turnaround, and the
maintainer has to remember which library hosts each helper.

The fourth option is a *queryable code catalog*: every library the
project uses, named, kind-tagged, role-tagged, with a short
description of what it does and what its primary entry points are.
That catalog is codio.

## The five-layer architecture

codio sits on five layers, from concrete to abstract:

1. **Physical code** — the actual source trees under
   `code/lib/<name>/` and `.projio/codio/mirrors/<vendor>--<repo>/`.
   These are git/datalad subdatasets pinned at known commits.
2. **Catalog** (`.projio/codio/catalog.yml`) — for each library, a
   record with `name`, `kind` (`internal`, `external`,
   `external_mirror`), `role` (`core`, `shared`, `external`), a
   description, and entry-point hints. The role field governs agent
   write access: agents may add code to libraries with `role: core`,
   but never to `role: external`.
3. **Project profile** — per-project lists of which libraries are
   in scope. A library may exist in the catalog without being active
   for the current project.
4. **Curated notes** under `docs/reference/codelib/libraries/<name>.md`
   — human-authored summaries of when to reach for a library, with
   a few representative call-sites.
5. **MCP query tools** — the surface that humans and agents actually
   call.

The five layers are deliberate: the physical code is the source of
truth; the catalog is the registry; the project profile is the
filter; the notes are the prose; the MCP tools are the API.

## The MCP surface

The codio tool surface is small:

- `codio_list()` returns every library the project knows about.
- `codio_get(name)` returns one library's full record.
- `codio_discover(query)` semantic-searches the catalog and the
  curated notes for libraries that match a capability query — e.g.
  `codio_discover("band-pass filter")` returns the libraries whose
  notes or descriptions mention filters, ranked by relevance.
- `codio_add(name, kind, role)` and `codio_add_urls(urls)` register
  a new library; `projio sync` auto-detects `code/lib/<name>/` and
  calls `codio_add(name, kind="internal", role="core")` for each.
- `codio_validate()` checks the registry for consistency.
- `codio_rag_sync()` registers the catalog + notes + mirror sources
  with indexio so `rag_query(corpus="codelib")` returns the matched
  source text.
- `codio_vocab()` returns the controlled vocabulary used in the
  catalog so an agent does not invent new role names.

## Roles: `core / shared / external`

Roles are the field that makes the catalog *governable*:

- `core` — the project's own first-party libraries. The agent may
  write to them. In pixecog and gecog, `code/lib/cogpy/`,
  `code/lib/labpy/`, and (in pixecog) `code/lib/labbox/` are all
  `role: core`. They are pinned subdatasets owned by the lab.
- `shared` — libraries owned by the lab but reused across projects
  with stricter change discipline. Agents may *read* them and propose
  changes via PR, but not write directly.
- `external` — third-party libraries the project depends on. The
  source is mirrored read-only under `.projio/codio/mirrors/` so
  that indexio can include it in the `codelib` corpus, but the
  agent must never touch it. Pull-requests go to upstream.

The role field maps to the access policy at agent time. An attempt to
edit a `role: external` file is rejected by convention; the project's
`.claude/settings.json` does not include external mirrors in the
write allow-list.

## Two cohort extremes

**cogpy** is the catalog-heaviest project in the cohort. Its
`.projio/codio/catalog.yml` carries ~40 external mirrors —
snakemake, snakebids, mne, neo, spikeinterface, openalex tooling,
docling, grobid — each mirrored under
`.projio/codio/mirrors/<vendor>--<repo>/` and indexed by indexio.
This is the *most invested* the cohort gets in cross-project code
search: every dependency cogpy uses is queryable, with full source
indexed, so a question like "how does spikeinterface handle missing
channels?" resolves to a code chunk rather than to a documentation
page.

**pixecog and gecog** sit at the other end: their first-party
libraries (`code/lib/cogpy`, `code/lib/labpy`, `code/lib/labbox`)
are registered with `role: core` and are mounted as DataLad
subdatasets at pinned commits. They demonstrate the other side of
the catalog: *the lab's own code* as a curated, version-pinned,
catalog-aware artifact, not a one-off `utils.py`.

`projio sync` ties the ends together. On every sync, it walks
`code/lib/*/`, registers each library it finds with
`role=core, kind=internal`, and updates the catalog. Adding a new
internal library is one `git submodule add` followed by one
`projio sync`.

## Search before creation

The workflow codio enables is the one the [explanation
chapter](../../explanation/search-before-creation.md) documents:
**search before creation**. Before writing a new utility, an agent
(or a careful human) calls `codio_discover(query)` and
`rag_query(query, corpus="codelib")` to see what already exists. The
discoveries fall into three buckets:

- *Reuse directly* — the function exists, it does what's needed,
  import it.
- *Wrap* — the function exists but has the wrong calling convention
  or output type; write a thin wrapper, don't re-implement.
- *Depend* — the library exists but is not currently in the project
  profile; add the dependency rather than copy-paste.
- *Implement new* — nothing matches; document why in the commit
  message so the next search has a paper trail.

The explicit decision is the point. The catalog does not stop
duplication; it makes duplication a *choice*, with a record.

## What codio costs

The catalog is not free. Every external library worth indexing has
to be mirrored as a subdataset, and curated notes have to be written
by hand for the libraries that matter. The role assignment is a
social contract, not a build-system constraint — an agent ignoring
roles can still write to anywhere it has filesystem access. The
mitigation is layered: `.claude/settings.json` restricts the write
path and `codio_validate()` catches accidental policy violations.

The reward is that the **agent stops reinventing primitives**. With
the catalog populated, "is there already a function for this?" is
one MCP call, not a half-day of codebase archaeology.

## Further reading

- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager; `uv tool install --editable` is used to share editable core libraries across environments without per-project installs.
