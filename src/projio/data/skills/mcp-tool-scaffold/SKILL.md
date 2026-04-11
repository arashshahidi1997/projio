---
name: mcp-tool-scaffold
description: >
  Scaffold a new MCP tool end-to-end: implement the function in the
  subsystem package, create the MCP wrapper in projio, register it in
  server.py, and update agent instructions in all required locations.
  Use when adding a new tool to any projio subsystem.
metadata:
  short-description: Implement → wrap → register → update instructions
  tags: [development, mcp, scaffold, meta]
  tooling:
    mcp:
      - server: projio
        tools:
          - project_context
          - module_context
          - skill_read
---

# MCP Tool Scaffold

End-to-end checklist for adding a new MCP tool to a projio subsystem.
Ensures nothing is missed — especially the instruction updates that
agents depend on for tool discovery.

## When to use

- Adding a new MCP tool to any subsystem (biblio, codio, notio, pipeio, indexio, figio)
- Exposing an existing package function as an MCP tool
- After a design spec calls for a new tool

Do NOT use for modifying existing tool signatures — that is a refactor, not a scaffold.

## Inputs

- `TOOL_NAME` (required): the MCP tool name (e.g. `biblio_pool_resolve`)
- `PACKAGE` (required): which subsystem package (biblio, codio, notio, pipeio, indexio, figio)
- `SPEC` (optional): path to design spec describing the tool's behavior
- `DESCRIPTION` (required): one-line tool description for the MCP decorator
- `PARAMS` (required): parameter names, types, defaults, and descriptions

## Workflow

### 1) Read context

```
project_context()
module_context(module="PACKAGE")
```

If `SPEC` provided, read it. Understand the subsystem's existing patterns.

### 2) Implement the function in the subsystem package

**Location:** `packages/{PACKAGE}/src/{PACKAGE}/` (or the appropriate submodule)

Find the module where related functions live. Follow the existing patterns:
- Same return format (dict with structured fields)
- Same error handling (return `{"error": "..."}` on failure, not exceptions)
- Same logging conventions
- Respect `_get_root()` for path resolution

Write the implementation. Include a docstring matching the MCP description.

### 3) Create the MCP wrapper in projio

**Location:** `src/projio/mcp/{PACKAGE}.py`

Read the existing file first. Follow the delegation pattern:

```python
def tool_name(param1: type, param2: type = default) -> dict:
    """One-line description matching the MCP decorator."""
    from package import module
    return module.function(param1=param1, param2=param2)
```

Key patterns:
- Wrapper delegates to the package function — NO logic in the wrapper
- Convert empty strings/lists to None where the package expects Optional
- Type hints must match the MCP schema expectations

### 4) Register in server.py

**Location:** `src/projio/mcp/server.py`

Add the tool registration under the correct section comment (`# --- Biblio tools ---`, etc.):

```python
@server.tool("tool_name")
def tool_name_tool(param1: type, param2: type = default):
    """One-line description — this becomes the MCP tool description."""
    return package_module.tool_name(param1=param1, param2=param2)
```

Key patterns:
- Function name: `{tool_name}_tool` (suffix `_tool` to avoid name collisions)
- Decorator string: exact tool name as exposed via MCP
- Docstring: same text as the wrapper — this is what agents see
- Place it next to related tools in the same section

### 5) Update agent instructions — routing table in `_generate_claude_md()`

**Location:** `src/projio/init.py`, inside `_generate_claude_md()`

Find the section guarded by `if has_{PACKAGE}:` and add a routing row:

```python
rows.append("| {Intent} | `{tool_name}({key_params})` | {Anti-pattern} |")
```

Where:
- **Intent**: what the user/agent is trying to do (e.g. "Resolve pool derivatives")
- **Key params**: the most important parameters shown inline
- **Anti-pattern**: what NOT to do instead (e.g. "Parse derivative dirs manually")

### 6) Update CLAUDE.md tool list in projio repo

**Location:** `CLAUDE.md` (repo root), under `### MCP Server`

Find the bullet for `mcp/{PACKAGE}.py` and add the new tool name to the list.

### 7) Update worklog instructions (if applicable)

This step applies when the tool changes cross-project behavior or is
relevant to worklog orchestration.

**Two locations:**

a. **Worklog MCP server instructions** — the `instructions=` string in
   worklog's `src/worklog/mcp_server.py`. Update the tool routing table
   if the new tool affects cross-project workflows.

b. **Worklog CLAUDE.md** — the routing table in the worklog repo root.

If the tool is purely internal to a subsystem and not relevant to
cross-project orchestration, skip this step and note that in your report.

### 8) Verify

Run a quick validation:

```bash
PYTHONPATH=src python -c "from projio.mcp.{PACKAGE} import {tool_name}; print('import ok')"
```

If tests exist for the MCP module:
```bash
PYTHONPATH=src python -m pytest tests/ -q -k "{PACKAGE}" 2>&1 | head -20
```

## Checklist summary

Use this as a final verification before reporting done:

- [ ] Function implemented in `packages/{PACKAGE}/src/{PACKAGE}/`
- [ ] MCP wrapper in `src/projio/mcp/{PACKAGE}.py`
- [ ] Registered in `src/projio/mcp/server.py` with `@server.tool()`
- [ ] Routing row added in `_generate_claude_md()` in `src/projio/init.py`
- [ ] Tool name added to CLAUDE.md tool list under `### MCP Server`
- [ ] Worklog instructions updated (or noted as not applicable)
- [ ] Import verified

## Guardrails

- NEVER put business logic in the MCP wrapper — it delegates only.
- NEVER add a tool to server.py without the routing table row — agents won't discover it.
- NEVER skip the CLAUDE.md update — it's the persistent documentation.
- The `_generate_claude_md()` routing table is code-generated into every project's CLAUDE.md on `projio sync`. If you miss it, no project will know about the tool.
- Follow existing naming conventions: tool names are `{package}_{action}` (e.g. `biblio_merge`, `pipeio_mod_create`).
- If the tool has a `background` parameter returning a `job_id`, also scaffold the corresponding `{tool_name}_status` tool for polling.

## Output format

Report:
1. Files created/modified (with paths)
2. Tool name as registered
3. Parameters exposed
4. Routing table row added
5. Worklog update status (done / not applicable)
6. Import verification result
7. Suggested next step (test, docs, or related tools)
