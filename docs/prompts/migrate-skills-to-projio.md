# Task: Migrate Codex Skills to .projio/skills/

## Context

This project has 18 Codex skills in `.codex/skills/` that guide agents through the research grand routine. These skills reference MCP tools from two servers:

1. **projio** — the primary MCP server (configured in `.claude/claude.json`)
2. **pixecog** — a transitional project-specific server (3 retained tools)

The MCP transition is documented at `docs/reference/infra/mcp-transition-map.md`.

We are consolidating skills under `.projio/skills/` as the canonical location, with symlinks so both Codex and Claude Code can consume them:

```
.projio/skills/           ← canonical (single source of truth)
.codex/skills             ← symlink → ../.projio/skills
.claude/commands/<name>.md ← per-skill symlinks → ../../.projio/skills/<name>/SKILL.md
```

## What to do

### Phase 1: Move skills to `.projio/skills/`

1. Create `.projio/skills/` directory
2. Copy every skill directory from `.codex/skills/` into `.projio/skills/`:
   ```
   .codex/skills/add-feature-cogpy/     → .projio/skills/add-feature-cogpy/
   .codex/skills/codelib-discovery/     → .projio/skills/codelib-discovery/
   .codex/skills/codelib-update/        → .projio/skills/codelib-update/
   .codex/skills/cogpy-schema/          → .projio/skills/cogpy-schema/
   .codex/skills/cogpy-test/            → .projio/skills/cogpy-test/
   .codex/skills/cogpy-test-spec/       → .projio/skills/cogpy-test-spec/
   .codex/skills/flow-run/              → .projio/skills/flow-run/
   .codex/skills/idea-capture/          → .projio/skills/idea-capture/
   .codex/skills/literature-discovery/  → .projio/skills/literature-discovery/
   .codex/skills/manifest-checklist/    → .projio/skills/manifest-checklist/
   .codex/skills/mod-review-update/     → .projio/skills/mod-review-update/
   .codex/skills/note-commit-fast/      → .projio/skills/note-commit-fast/
   .codex/skills/notebook/              → .projio/skills/notebook/
   .codex/skills/pipeline-docs-generator/ → .projio/skills/pipeline-docs-generator/
   .codex/skills/pipeline-kickstart/    → .projio/skills/pipeline-kickstart/
   .codex/skills/presentation/          → .projio/skills/presentation/
   .codex/skills/rag-query/             → .projio/skills/rag-query/
   .codex/skills/utility-promote/       → .projio/skills/utility-promote/
   ```
   Include all `references/` subdirectories.

### Phase 2: Fix reference paths and MCP tool names

#### 2a. Reference paths

Some skills use skill-relative paths to reference files. These must become project-relative because Claude Code slash commands resolve from project root.

Known cases to fix:

- **add-feature-cogpy/SKILL.md** contains:
  ```
  READ `.codex/skills/integrate-into-cogpy/references/codelib_mcp.md`
  ```
  Change to:
  ```
  READ `.projio/skills/add-feature-cogpy/references/codelib_mcp.md`
  ```

- **utility-promote/SKILL.md** contains:
  ```
  - `references/cogpy_architecture_summary.md`
  - `references/utils_architecture_summary.md`
  ```
  Change to:
  ```
  - `.projio/skills/utility-promote/references/cogpy_architecture_summary.md`
  - `.projio/skills/utility-promote/references/utils_architecture_summary.md`
  ```

- Scan ALL SKILL.md files for any other `references/` or `.codex/skills/` paths and fix them.

#### 2b. MCP tool name updates

Per the transition map, update tool references in SKILL.md frontmatter and body text. The rule: if a tool has been superseded by projio, use the projio name. If a tool is retained in pixecog, keep the pixecog server reference.

**Superseded tools — rename these everywhere:**

| Old (pixecog) | New (projio) |
|---|---|
| `notes_list` | `note_list` |
| `notes_latest` | `note_latest` |
| `notes_template` | `note_types` |
| `citekey_resolve` | `citekey_resolve` (same name, projio server) |
| `docling_snippets` | `biblio_docling` |
| `docling_figures` | `biblio_docling` |
| `codelib_registry` | `codio_registry` |
| `codelib_vocab` | `codio_vocab` |
| `codelib_get` | `codio_get` |
| `codelib_list` | `codio_list` |
| `codelib_validate` | `codio_validate` |
| `rag_query` | `rag_query` (same name, projio server) |
| `rag_query_multi` | `rag_query_multi` (same name, projio server) |
| `runtime_conventions` | `runtime_conventions` (same name, projio server) |

**Retained tools — keep these as pixecog server:**

| Tool | Reason |
|---|---|
| `pipeline_registry` | Pipe/flow/mod is pixecog-specific |
| `modkey_resolve` | Coupled to pipe/flow/mod structure |
| `module_context` | Extracts pixecog-specific doc sections |

**Update the frontmatter** in each SKILL.md to split the server references:

```yaml
metadata:
  tooling:
    mcp:
      - server: projio
        tools:
          - runtime_conventions
          - rag_query
          - codio_discover
          - note_list
      - server: pixecog
        tools:
          - pipeline_registry
          - modkey_resolve
```

Skills that only use projio tools should drop the pixecog server reference entirely.

**Update the body text** — replace old tool names in workflow steps, code blocks, and examples. For example in `codelib-discovery/SKILL.md`:
```
# Before
codelib_get("<library>")
codelib_list(capability="<capability>")

# After
codio_get("<library>")
codio_list(capability="<capability>")
```

And in `literature-discovery/SKILL.md`:
```
# Before
docling_snippets(citekey="<key>", query="method algorithm formula")
docling_figures(citekey="<key>")

# After
biblio_docling(citekey="<key>", query="method algorithm formula")
biblio_docling(citekey="<key>")
```

Note: `biblio_docling` combines the old `docling_snippets` + `docling_figures` into one tool. Update the call patterns accordingly — where the old code called both separately, a single `biblio_docling` call now returns both snippets and figures.

#### 2c. Fix idea-capture skill

The file `.codex/skills/idea-capture/SKILL.md` is truncated — it's missing its frontmatter and opening workflow steps (the file starts mid-sentence at "Capture the exact path printed..."). Add proper frontmatter:

```yaml
---
name: idea-capture
description: >
  Capture a new analysis idea as a structured note using the repo's Make
  target and note template. Use when a user has a new analysis idea,
  metric request, or observation to investigate. Step 1 of the grand routine.
metadata:
  short-description: Capture analysis idea as structured note
  tooling:
    mcp:
      - server: projio
        tools:
          - note_list
          - note_latest
          - note_types
---
```

And add the missing opening section before the existing content:

```markdown
# Idea Capture

Use this skill when the user has a new analysis idea, metric request, or
observation to investigate. This is step 1 of the grand routine.

## Inputs

- `IDEA` (required): the raw idea, question, or observation

## Workflow

### 1) Create the idea note

Run:
```
make note-idea IDEA="<IDEA>"
```
```

Then the existing content continues from "Capture the exact path printed...".

### Phase 3: Set up symlinks

#### 3a. Replace `.codex/skills/` with a symlink

```bash
rm -rf .codex/skills
ln -s ../.projio/skills .codex/skills
```

Verify: `ls .codex/skills/notebook/SKILL.md` should resolve correctly.

#### 3b. Create Claude Code commands directory with symlinks

```bash
mkdir -p .claude/commands
```

Create one symlink per skill:

```bash
for skill_dir in .projio/skills/*/; do
    name=$(basename "$skill_dir")
    ln -s "../../.projio/skills/${name}/SKILL.md" ".claude/commands/${name}.md"
done
```

Verify: `ls -la .claude/commands/` should show symlinks, and `head -3 .claude/commands/notebook.md` should show the SKILL.md frontmatter.

### Phase 4: Update the `codelib_mcp.md` reference file

The file at `.projio/skills/add-feature-cogpy/references/codelib_mcp.md` references old pixecog tool names. Update it:

```markdown
# Codelib MCP quick reference

The **projio** MCP server exposes codio registry tools:

## Tool calls (typical)

- List candidate libraries for a capability:
  - `codio_list(capability="coherence")`
  - `codio_list(capability="multitaper_psd")`
- Fetch one entry (mirror/doc pointers):
  - `codio_get("mne-python")`
- Validate registry points to real paths:
  - `codio_validate()`
- Get normalized vocabulary:
  - `codio_vocab()`
- Discover libraries by capability query:
  - `codio_discover("phase gradient")`

## Interpretation

- Registry entries come from `.projio/codio/catalog.yml` + `.projio/codio/profiles.yml`.
- `mirror_path` points into `code/lib/...` (read-only inspiration mirror).
- Curated notes are referenced via the profile's `curated_note` field.
```

### Phase 5: Verification

1. Confirm `.codex/skills` symlink resolves:
   ```bash
   ls .codex/skills/notebook/SKILL.md
   ```

2. Confirm Claude Code commands resolve:
   ```bash
   ls -la .claude/commands/
   head -3 .claude/commands/notebook.md
   ```

3. Grep for any remaining old tool names that should have been renamed:
   ```bash
   grep -r "codelib_get\|codelib_list\|codelib_validate\|codelib_vocab\|codelib_registry" .projio/skills/
   grep -r "notes_list\|notes_latest\|notes_template" .projio/skills/
   grep -r "docling_snippets\|docling_figures" .projio/skills/
   grep -r "\.codex/skills/" .projio/skills/
   ```
   All of these should return zero results.

4. Grep for retained pixecog tools (these should still exist):
   ```bash
   grep -r "pipeline_registry\|modkey_resolve\|module_context" .projio/skills/
   ```
   These are expected and correct.

5. Count skills to confirm none were lost:
   ```bash
   ls -d .projio/skills/*/  | wc -l
   ```
   Expected: 18 directories.

## Do NOT

- Do not modify `.codex/mcp_servers.pixecog.toml` — the pixecog MCP server stays as-is
- Do not modify `.claude/claude.json` — projio MCP server config stays as-is
- Do not modify `code/utils/pixecog_mcp/server.py` — the server code stays as-is
- Do not modify any files outside `.projio/skills/`, `.codex/`, and `.claude/commands/`
- Do not run git commands — the user will handle commits
- Do not create new skills or modify skill logic — only fix paths, tool names, and frontmatter
