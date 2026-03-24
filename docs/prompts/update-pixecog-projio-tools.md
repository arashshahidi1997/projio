# pixecog MCP Migration — Completion Record

## Status: Complete (2026-03-23)

All pixecog-specific MCP tools have been superseded by projio equivalents.
The pixecog-mcp server has been retired.

## Migration summary

### Tool mapping (all complete)

| pixecog tool | projio replacement | Parameter changes |
|---|---|---|
| `notes_list` | `note_list` | — |
| `notes_latest` | `note_latest` | — |
| `notes_template` | `note_types` | — |
| `codelib_list` | `codio_list` | — |
| `codelib_get` | `codio_get` | — |
| `codelib_validate` | `codio_validate` | — |
| `codelib_vocab` | `codio_vocab` | — |
| `codelib_discover` | `codio_discover` | — |
| `docling_snippets` | `biblio_docling` | — |
| `docling_figures` | `biblio_docling` | — |
| `runtime_conventions` | `runtime_conventions` | — |
| `pipeline_registry` | `pipeio_flow_list` + `pipeio_mod_list` | Split into flow/mod queries |
| `modkey_resolve` | `pipeio_mod_resolve` | `modkeys_list` → `modkeys` |
| `module_context` | `module_context` | `module_doc_path` → `doc_path` |

### Skills updated (Phase 1+4)

10 skill SKILL.md files in `.projio/skills/` updated:
- All `server: pixecog` frontmatter sections removed
- All tool references and parameter names updated to projio equivalents
- `pipeline_registry(scan=false)` → `pipeio_flow_list()` / `pipeio_mod_list()`
- `modkey_resolve(modkeys_list=[...])` → `pipeio_mod_resolve(modkeys=[...])`
- `module_context(module_doc_path="...")` → `module_context(doc_path="...")`

### Server configs retired (Phase 3)

- Removed `pixecog` entry from `.claude/claude.json`
- Deleted `.codex/mcp_servers.pixecog.toml`
- `code/utils/pixecog_mcp/` retained (smoke test imports docling module)

### pipeio consolidation

pipeio registry path lookup now checks:
1. `.projio/pipeio/registry.yml` (preferred, consolidated under .projio/)
2. `.pipeio/registry.yml` (legacy fallback)

`projio init -c full` now activates pipeio alongside other packages,
creating `.projio/pipeio/registry.yml`.

## Verification

All 8 verification checks passed:
- Zero stale pixecog tool names in skills
- Zero `server: pixecog` references
- Zero `modkeys_list` or `module_doc_path` parameter references
- All 18 skills present
- All symlinks resolve (.codex/skills, .claude/commands)
- No pixecog MCP config remains
