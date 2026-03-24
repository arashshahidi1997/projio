# Workflow: Session Bootstrap

**Phase:** Any (always run first)
**Purpose:** Gather project context and determine what workflow phase to enter.

## When to use

At the start of every agent session, before doing any other work.

## Steps

### 1. Gather project context

Call these tools in parallel:

```
project_context()          → project name, config, README, key paths
runtime_conventions()      → Makefile targets, available commands
agent_instructions()       → tool routing table, enabled packages
```

### 2. Check recent activity

```
note_list(limit=5)                    → recent notes (what's been worked on)
note_list(note_type="task", limit=5)  → open tasks
pipeio_flow_list()                    → existing pipelines
```

### 3. Determine phase

Based on the context gathered:

| Signal | Phase | Next workflow |
|--------|-------|---------------|
| User mentions a new idea or question | Exploration | → `explore-idea.md` |
| An open task note exists with a decision recorded | Implementation | → `implement-feature.md` |
| Code is written, tests pass, user mentions pipeline | Production | → `integrate-pipeline.md` |
| User asks to validate or deploy | Deployment | → `validate-and-deploy.md` |
| Unclear | Ask | Ask the user what they'd like to work on |

### 4. Report state

Before proceeding, briefly report:
- Project name and enabled subsystems
- Recent activity summary (last 2-3 notes)
- Recommended next phase and why

## Output

A short status summary and a recommendation for which workflow to enter next.
