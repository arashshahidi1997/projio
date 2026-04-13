# Skills

Skills are prompt-based workflow templates that orchestrate MCP tools into a coherent task. They live under `src/projio/data/skills/<name>/SKILL.md` (ecosystem) and `.projio/skills/<name>/SKILL.md` (per-project override).

Agents discover skills via `agent_instructions()` and load the full body via `skill_read(name)`.

## Discovery

| Tool | Description |
|------|-------------|
| `agent_instructions()` | Enumerate available skills with short descriptions |
| `skill_read(name)` | Return the full SKILL.md body for a named skill |

## Skill index

### Project setup & orchestration

| Skill | Purpose |
|-------|---------|
| `projio-setup` | Initialize a projio workspace and enable relevant packages |
| `agent-orchestration` | Pattern guide for coordinating multiple agents across subsystems |
| `idea-capture` | Record an idea note with structured frontmatter and linked refs |
| `mcp-tool-scaffold` | Build a new MCP tool end-to-end across a package + projio wrapper |

### Knowledge discovery

| Skill | Purpose |
|-------|---------|
| `literature-discovery` | Search the paper corpus for methods, parameters, validation plots |
| `codelib-discovery` | Search the code-library catalog for reusable implementations |
| `rag-query` | Run a focused semantic search across any corpus |
| `biblio-batch-curate` | Curate a batch of freshly ingested papers (tags, status, priority) |

### Research orchestration (questio)

| Skill | Purpose |
|-------|---------|
| `questio-ground` | Ground a research question in existing literature + project state |
| `questio-investigate` | Drive a focused investigation against a specific question |
| `questio-iterate` | Tighten an investigation loop based on prior findings |
| `questio-next` | Pick the next question from the plan given current state |
| `questio-record` | Capture investigation findings as structured plan entries |
| `questio-report` | Generate a stakeholder-facing progress report from plan state |
| `questio-session` | Open a time-bounded research session with a clear deliverable |

### Pipelines

| Skill | Purpose |
|-------|---------|
| `pipeio-guide` | Pipeio ontology reference (flows, mods, rules, notebooks, configs) |
| `pipeio-flow-create` | Scaffold a new pipeline flow with a starter mod and notebook |
| `pipeio-nb-extract` | Extract figures/outputs from an executed notebook and write a curated flow-local report (renamed from `pipeio-report`) |
| `marimo-session` | Run a marimo notebook live-edit session with agent oversight |

### Presentations

| Skill | Purpose |
|-------|---------|
| `literature-presentation` | Build a multi-paper literature-background deck section-by-section |
| `progress-report-deck` | Worklog-sourced cross-project progress report, drafted iteratively |

### Issue handling

| Skill | Purpose |
|-------|---------|
| `issue-triage` | Triage a newly filed issue into scope, priority, and owner |
| `issue-fix` | Fix a triaged issue and probe for related robustness problems |

## Skill shape

Every skill is a `SKILL.md` file with YAML frontmatter (`name`, `description`, `metadata.tags`, `metadata.tooling.mcp[]`) followed by sections named **When to use**, **Inputs**, **Workflow** (numbered steps with MCP tool examples), and **Hard rules**. The structure is enforced by convention, not by a validator.

Skills that touch multiple MCP servers declare them explicitly:

```yaml
metadata:
  tooling:
    mcp:
      - server: projio
        tools: [rag_query, biblio_ingest, present_init, ...]
      - server: worklog
        tools: [list_projects, worklog_project_context, ...]
```

## Presentation skills in detail

### literature-presentation

Build a presentation deck that grounds an article in its literature context. Enforces the presentio iteration loop: **one section, human review, next section**. No batch drafting.

**When to use**

- Preparing an introduction/background talk for a paper or thesis chapter
- Framing current work against prior art and open questions

**Workflow**

1. Broad lit RAG via `rag_query` / `rag_query_multi` + `citekey_resolve`
2. `biblio_ingest` for anything missing
3. `present_init(format="marp", template="conference-talk")` to scaffold
4. Propose a narrative outline to the human — accept, reject, reshape
5. Draft one section at a time via `present_section_context` → edit → human review
6. `present_figure_insert` for figio figures (build with `figio_build` if stale)
7. `present_cite_check` before the first build
8. `present_validate` + `present_build` + `present_diff` for iteration

See the full skill body with `skill_read("literature-presentation")`.

### progress-report-deck

Build a recurring progress report by orchestrating across projects via worklog, with presentio owning the deck artifact. The deck lives in one project but draws material from all.

**When to use**

- Weekly / biweekly progress report to a PI or committee
- Monthly research group update
- Any recurring meeting rooted in cross-project activity data

**Workflow**

1. Gather cross-project briefing via worklog (`list_projects`, `worklog_project_context`, `goal_milestones`, `list_sessions`, `list_notes`)
2. Classify material into **Done / In-flight / Blockers / Next / Side-findings**
3. `present_init(template="progress-report")` in the host project
4. Propose the outline from the bucketed data — human approves
5. Draft one section at a time via `present_section_context`
6. `present_figure_insert` or `present_section_import` for cross-project figures
7. `present_cite_check` + `present_validate` + `present_build`
8. Log decisions/action items back to worklog — they become next week's input

See the full skill body with `skill_read("progress-report-deck")`.
