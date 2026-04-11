---
name: idea-capture
description: >
  Capture a new analysis idea as a structured note. Step 1 of the
  grand routine. Creates an idea note with problem statement, success
  criteria, expected output, and suggested next step.
metadata:
  short-description: Capture analysis idea as structured note
  tags: [grand-routine, step-1, exploration]
  tooling:
    mcp:
      - server: projio
        tools:
          - note_create
          - note_list
          - note_search
          - project_context
          - pipeio_flow_list
---

# Idea Capture

Use this skill when the user has a new analysis idea, metric request, or
observation to investigate. This is step 1 of the grand routine.

## Inputs

- `IDEA` (required): the raw idea, question, or observation

## MCP-first discovery

Before creating the note, gather context:

```
project_context()          # understand the workspace
note_search(query=IDEA)    # check for existing related ideas
pipeio_flow_list()         # see existing pipelines (if pipeio enabled)
```

If a related idea note already exists, report it and ask whether to
continue or update the existing note.

## Workflow

### 1) Create the idea note

```
note_create(note_type="idea", title="<concise title from IDEA>")
```

### 2) Read the generated template

Open the generated file. Do not assume its structure — read it first.
If the template has changed, adapt to whatever sections are present.

### 3) Fill the template

Fill all sections using the user's `IDEA` as the primary source.
Do not invent details not implied by the idea.

Sections to fill (adapt to actual template):

**title / heading**
- Concise, ≤ 80 chars
- Same in YAML frontmatter and first `#` heading

**Problem / motivation**
- What question is being asked?
- What gap or artifact prompted this?
- 2–4 sentences

**Success criteria**
- What does "done" look like?
- What output shape / plot / metric would confirm success?
- Be concrete

**Expected output**
- Shape description (e.g. `(n_channels, freq)`)
- Whether sampling rate (`fs`) is required
- Data type (xarray, numpy, pandas, etc.)

**Pipe / flow placement**
- Best guess at owning pipeline and flow
- If unknown, write "TBD"

**Related ideas / prior work**
- Link to any existing idea notes found during discovery
- Any known citekeys or library names

**Next step**
- One of: codelib discovery / literature search / direct implementation
- Be specific about which skill to invoke next

### 4) Save the file

Do not run any git commands.

### 5) Optional: seed next step

If the user wants to continue immediately:
- If next step is codelib discovery → invoke `codelib-discovery` skill
- If next step is literature → invoke `literature-discovery` skill

## Guardrails

- Do NOT run git commands.
- Do NOT fill sections with generic placeholders — leave them blank
  rather than writing "TBD" for everything.
- The raw `IDEA` text MUST appear verbatim somewhere in the note
  (either as a quote block or as the problem statement).

## Output format

Report:
1. Path to created idea note
2. Sections filled vs left blank
3. Suggested next step (which skill, which inputs)
