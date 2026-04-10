# Issue Triage

Read open issues, analyze root causes, and produce an implementation plan.

## Workflow

### 1) List open issues

```
note_list(note_type="issue", limit=20)
```

Filter for `status: open`. Present a summary table to the user.

### 2) Read each open issue

For each open issue, read the full note content. Extract:
- **Problem**: what's broken or missing
- **Root cause**: which file/function is responsible
- **Suggested fix**: from the issue or your own analysis

### 3) Locate the relevant code

Read the source files identified in the root cause analysis.
Understand the current behavior before proposing changes.

### 4) Produce a plan

For each issue, output:
- Exact files to change and what to change
- Implementation order (fix dependencies first)
- Whether it's a bug fix, new feature, or test fix
- Estimated complexity (1-line fix vs. new function)

Present the plan to the user for approval before implementing.

## Inputs

- `SCOPE` (optional): filter issues by keyword (e.g. "pipeio", "biblio")
- `LIMIT` (optional): max issues to triage (default: all open)

## Output

A numbered plan with one section per issue, ready for `/issue-fix`.

User input: $ARGUMENTS
