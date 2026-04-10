# Issue Fix

Implement fixes for open issues, update documentation, mark resolved, and commit.

## Workflow

### 1) Confirm scope

If no plan exists from `/issue-triage`, run triage first.
Otherwise, confirm the plan with the user before implementing.

### 2) Implement fixes

For each issue in the plan:
- Read the relevant source files
- Make the code changes
- Run tests to verify: `PYTHONPATH=src python -m pytest tests/ -q --tb=short`
- If in a subpackage (packages/*), run its tests too

### 3) Update documentation

After all fixes are implemented:

- **CHANGELOG.md** (repo root): add entries under `## Unreleased` with the
  appropriate section (Added/Fixed/Changed). If fixes span a subpackage,
  update that package's CHANGELOG.md too.
- **CLAUDE.md**: update tool counts or tool lists if tools were added/changed.
- **agent_instructions**: if tools were added, update the routing table in
  `src/projio/init.py` `_generate_claude_md()` and the tool list in the
  subpackage's CLAUDE.md.

### 4) Mark issues resolved

For each fixed issue, update its frontmatter:
```
status: open  ->  status: resolved
```

### 5) Commit via datalad

Use the `datalad_save` MCP tool (NOT bare git commit — submodules have
git-annex pre-commit hooks that need the labpy environment).

Include all changed files in a single save with a descriptive message.
If subpackage files changed, they'll be saved recursively.

Message format:
```
<short summary of all fixes>

- <issue 1 description>
- <issue 2 description>
- ...

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

## Guardrails

- Always run tests BEFORE committing.
- Never use bare `git commit` in datalad-managed repos — use `datalad_save` MCP tool.
- Use `recursive=true` when subpackage files changed.
- Don't batch unrelated pre-existing changes into the commit — only include
  files you actually changed for the fix.

User input: $ARGUMENTS
