---
name: projio-orient
description: >
  Orient a new user or a fresh agent in a projio workspace: survey what the
  project is, which subsystems are active, what work already exists, and then
  suggest concrete next actions mapped to the right skills and MCP tools. Use at
  the start of a session in an unfamiliar projio repo, or when the user asks
  "what is this project / what can I do here / where do I start / give me a tour".
metadata:
  short-description: Tour a projio workspace and suggest next actions
  tags: [onboarding, orientation, discovery, getting-started]
  tooling:
    mcp:
      - server: projio
        tools:
          - project_context
          - ecosystem_status
          - agent_instructions
          - runtime_conventions
          - pipeio_flow_list
          - note_list
          - notio_log_nav
          - corpus_list
          - codio_list
          - manuscript_list
---

# projio-orient — workspace tour + next-step menu

Use this when someone lands in a projio project and needs to understand what it
is and what they can do, without reading the whole repo by hand. The goal is a
short, accurate briefing plus a menu of concrete next actions, each pointing at
the skill or MCP tool that does it.

This is orientation, not repair. If projio itself is misconfigured or a subsystem
is broken, hand off to the **projio-setup** skill instead.

## Inputs

- `FOCUS` (optional): a subsystem or goal to bias the tour toward (e.g.
  "pipelines", "literature", "manuscript"). If absent, give a balanced tour.

## Step 1 — Survey the workspace (read-only)

Run these and read the results; do not act yet:

```
project_context()        # project kind (generic/tool/study), enabled packages, code tiers, config paths
ecosystem_status()       # which subsystems are active/healthy, and missing deps
agent_instructions()     # conventions in force + the skills available in THIS project
runtime_conventions()    # resolved env/Makefile variables (what runs what)
```

`project_context` tells you the shape of the project. `ecosystem_status` tells you
which of the six subsystems (indexio, biblio, notio, codio, pipeio, figio) are
actually wired up here — only tour the ones that are active.

## Step 2 — Survey existing work, per active subsystem

For each subsystem that `ecosystem_status` reports as active, run its cheap
listing tool so the briefing reflects what is really here, not the generic
feature set:

- **pipeio** → `pipeio_flow_list()` — existing pipelines and their status.
- **notio** → `notio_log_nav()` and/or `note_list()` — ideas, issues, tasks,
  results already captured.
- **indexio** → `corpus_list()` — which corpora are indexed for RAG.
- **codio** → `codio_list()` — registered code libraries and their roles.
- **notio/manuscript** → `manuscript_list()` — manuscripts in progress.

Skip the listing for any subsystem that is not active. Keep this quick; you are
sampling the state, not auditing it.

## Step 3 — Brief the user

Write a short briefing (not a wall of text):

1. **What this workspace is** — one or two sentences from `project_context`:
   project kind, what it studies or builds, which subsystems are live.
2. **What already exists** — the highlights from Step 2 (e.g. "3 pipeline flows,
   12 idea notes, 1 manuscript in draft, 2 indexed corpora"). Name a few concrete
   items, do not dump full lists.
3. **How things run here** — the one or two facts from `runtime_conventions` a
   newcomer needs (e.g. which env runs the pipelines, whether this is a datalad
   dataset).

## Step 4 — Offer a next-step menu

Close with a short menu of concrete next actions, each tied to a skill or tool.
Pick the handful that fit what is active and any `FOCUS`. Examples:

- "Capture a new idea to investigate" → **idea-capture** skill.
- "Create a new pipeline flow" → **pipeio-flow-create** skill.
- "Find or reuse existing code before writing new" → **codelib-discovery** skill.
- "Ask a question against the indexed literature/corpora" → **rag-query** skill.
- "Pull literature on a topic" → **literature-discovery** skill.
- "Assemble or build a manuscript / deck" → the manuscript / present tools.
- "Wrap up and hand off at the end of the session" → **session-wrap** skill.

Only list actions whose subsystem is active. Prefer the skill (via `skill_read`)
over raw tools when a skill covers the task. If the user gave a `FOCUS`, lead with
that subsystem's actions and keep the rest brief.

## Guardrails

- **Read-only** — this skill surveys and suggests. It does not create notes,
  scaffold flows, commit, or change config.
- **Only tour active subsystems** — do not describe features that are not wired up
  in this project.
- **Hand off broken config to projio-setup** — orientation assumes a working
  install; do not try to fix env resolution or missing deps here.
- **Keep it short** — a briefing plus a menu, not an exhaustive inventory. Sample
  the state; link to skills for the depth.

## Output format

1. What this workspace is (1-2 sentences).
2. What already exists (highlights, a few named items).
3. How things run here (1-2 facts).
4. Next-step menu (3-6 actions, each mapped to a skill or tool).
