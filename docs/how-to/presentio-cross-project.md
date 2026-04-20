# Import a deck section from another project

Pull a section from another project's presentio deck into the current project's deck. This is the projio-slides-inside-pixecog-talk use case.

## Prerequisites

- Both projects registered in worklog (the source project must be resolvable by `worklog_read_file`)
- Source project must have a deck at `docs/deliverables/presentations/<source_deck>/sections/<section>.md`
- Host project has a scaffolded deck (`present_init` already run)
- `worklog` package installed — presentio lazy-imports it and raises a friendly error if missing

## Steps

### 1. Confirm the source exists

In the host project's agent session:

```text
list_projects()                            # find the source project_id
worklog_project_context(project_id=<id>)   # confirm the deck exists
```

You can also read the source deck.yml directly if you need to confirm section keys:

```text
worklog_read_file(project_id=<id>, path="docs/deliverables/presentations/<source_deck>/deck.yml")
```

### 2. Import the section

```text
present_section_import(
  name="<host-deck-name>",
  from_project="<source-project-id>",
  source_deck="<source-deck-name>",
  section="<source-section-key>",
  key="",                  # optional: host-side section key (defaults to <project>-<section>)
  order=0,                 # optional: host-side order (defaults to max(existing) + 10)
  mode="reference"         # or "freeze"
)
```

What happens:

1. Presentio fetches `docs/deliverables/presentations/<source_deck>/sections/<section>.md` from the source project via `worklog_read_file`
2. Strips any existing frontmatter from the remote body
3. Writes a new cache file at `docs/deliverables/presentations/<host-deck>/imports/<project>-<deck>-<section>.md` with a stamped provenance header:
   ```yaml
   ---
   title: "Imported: <section>"
   order: <order>
   deck: <host-deck>
   imported_from_project: <from_project>
   imported_from_deck: <source_deck>
   imported_from_section: <section>
   import_mode: <mode>
   status: imported
   tags: [presentation, section, imported]
   ---
   ```
4. Appends a `DeckSection` entry to the host `deck.yml` with an `import:` metadata block
5. Scans the imported body for citekeys and figure refs
6. Returns a report with `imported_citekeys`, `missing_citekeys` (not in host bib), `imported_figures`, and actionable `suggestions`

### 3. Handle missing citekeys

The import tool does **not** run `biblio_ingest` automatically — that would be an unexpected network side-effect. Instead, read the `missing_citekeys` field of the return value and run `biblio_ingest` explicitly:

```text
biblio_ingest(dois=[<dois for missing keys>])
biblio_merge()
```

Then re-run `present_cite_check(name=<host-deck>)` to confirm the imported section's citations now resolve against the host bibliography.

### 4. Handle figure references

If the imported section contains `fig:<id>` placeholders, those ids must exist in the host project's figio registry. Options:

- **Rebuild locally**: if the host project has a `figures/<id>.figurespec.yaml`, run `figio_build(figure_id=<id>)` to produce the output.
- **Copy the source figure**: the simplest cross-project figure approach today is to manually copy the SVG/PNG from the source project into `docs/deliverables/presentations/<host-deck>/figures/` and adjust the reference to an inline markdown image (`![](figures/<id>.png)`) instead of a `fig:<id>` placeholder.
- **Defer**: leave the `fig:<id>` placeholder in the imported section. `present_validate` will warn about unresolved figures but the rest of the deck still builds.

Full cross-project figure resolution (a worklog-backed figure resolver) is a phase-4.1 follow-up.

### 5. Refresh on upstream edits

If the source project updates the section you imported, re-fetch to pick up the changes:

```text
present_refresh_import(name="<host-deck>", section="<host-section-key>")
```

This only works on **reference-mode** imports. Frozen imports refuse to refresh.

The refresh preserves the cache file's provenance header — only the body is overwritten.

### 6. Freeze before a talk

Before giving a talk from a deck that depends on another project's in-flight work, lock the imports to prevent accidental refresh:

```text
present_freeze_import(name="<host-deck>", section="")
```

An empty `section` argument freezes every imported section in the deck. Pass a specific `section` to freeze only one.

Freezing flips `import_mode: reference → freeze` in both `deck.yml` and the cache file's frontmatter. The cache files themselves don't change — you can still edit them manually if you need to patch a section before the talk.

After the talk, you can unfreeze by editing `deck.yml` to set `import_mode: reference` again (or by deleting and re-importing the section).

## Example: pixecog pulls projio ecosystem slides

```text
# In pixecog project's agent session, with PROJIO_ROOT=<pixecog-repo>

# 1. Confirm source exists
list_projects()  # returns: [..., {id: "projio", ...}]
worklog_read_file(project_id="projio", path="docs/deliverables/presentations/ecosystem-intro/deck.yml")

# 2. Scaffold host deck if not already
present_init(name="thesis-defense", format="revealjs", template="conference-talk")

# 3. Import the projio architecture slide
present_section_import(
  name="thesis-defense",
  from_project="projio",
  source_deck="ecosystem-intro",
  section="architecture",
  key="projio-architecture",
  order=45,
  mode="reference"
)

# 4. Handle any missing citekeys the tool reports
biblio_ingest(dois=["10.xxxx/yyy", ...])
biblio_merge()
present_cite_check(name="thesis-defense")

# 5. Iterate on the rest of the thesis deck alongside the imported section
present_section_context(name="thesis-defense", section="projio-architecture")

# 6. Before the defense, freeze the import
present_freeze_import(name="thesis-defense", section="projio-architecture")

# 7. Build
present_build(name="thesis-defense", format="html")
```

The imported section lives alongside native sections in the host deck's output. Its order is driven by the host deck's `deck.yml`, not by the source deck's section order.

## Tool reference

???+ info "MCP tools used in this guide"

    | Tool | Purpose |
    |------|---------|
    | `present_section_import` | Fetch, cache, and register a remote section |
    | `present_refresh_import` | Re-fetch a reference-mode import |
    | `present_freeze_import` | Lock imports against future refresh |
    | `worklog_read_file` | Read a file from another project (via worklog MCP) |
    | `list_projects` | Enumerate projects in the worklog registry |
    | `biblio_ingest` | Ingest missing citekeys from the imported section |
    | `present_cite_check` | Re-validate citations after ingesting |
    | `present_validate` | Structural check including figure resolution |

    Full reference: [Presentation tools](../reference/mcp-tools.md#presentation-tools-via-notiopresent).
