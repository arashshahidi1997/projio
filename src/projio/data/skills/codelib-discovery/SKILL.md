---
name: codelib-discovery
description: >
  Search code and docs corpora for existing implementations, patterns,
  utilities, and prior decisions relevant to a topic. Captures results
  as a structured reference note. Step 2 of the grand routine.

  Use when starting step 2 (before implementing), checking if a utility
  already exists, exploring what registered libraries provide, or
  auditing prior decisions on a convention or pattern.
metadata:
  short-description: Search code corpora for existing implementations
  tags: [grand-routine, step-2, exploration, search-before-creation]
  tooling:
    mcp:
      - server: projio
        tools:
          - rag_query
          - rag_query_multi
          - codio_discover
          - codio_get
          - codio_list
          - note_create
          - note_latest
---

# Codelib Discovery

Search the code and docs corpora for existing implementations,
patterns, utilities, and prior decisions relevant to a topic.
Captures results as a structured reference note.

## When to use

- Starting step 2 of the grand routine (before implementing)
- Checking if a utility already exists before writing new code
- Exploring what registered libraries provide on a topic
- Auditing prior decisions on a convention or pattern

Do NOT use as a substitute for `literature-discovery` when
scientific methods or parameter ranges are the primary need.

## Inputs

- `TOPIC` (required): what to search for
- `IDEA_NOTE` (optional): path to idea note for context

## Phase 1: Search planning

Before running any queries, identify:

1. Core concept terms (for code corpus)
   e.g. "ripple detection", "bandpass filter", "threshold"

2. Convention / spec terms (for docs corpus)
   e.g. "schema", "pipeline convention"

3. Library candidates to check via codio
   e.g. specific library names if known

Plan 4–8 distinct queries across code + docs.
Queries must be meaningfully different — do not repeat
the same phrase with minor variation.

## Phase 2: Run queries

### Code corpus queries

```
rag_query(query="<term>", corpus="code", k=8)
```

Run all planned code queries. For each result:
- Note the source path
- Is it internal code or a library mirror?
- What does it actually implement?

### Docs corpus queries (if conventions relevant)

```
rag_query(query="<term>", corpus="docs", k=6)
```

For convention / spec / prior-decision queries.

### Codio registry checks

```
codio_discover("<capability query>")
```

For each promising candidate:
```
codio_get("<library_name>")
```

Read the library entry to understand:
- intended scope and caveats
- import patterns
- what it does and does not cover

### Read promising source files directly

For any hit that looks relevant, read the actual source file.
Do not rely on snippet alone — read enough to understand
the actual interface.

## Phase 3: Write output note

```
note_create(note_type="task", title="Codelib: <TOPIC>")
```

### Content structure

```markdown
# Codelib: <TOPIC>

## Queries run
- code: ["<query 1>", "<query 2>", ...]
- docs: ["<query 1>", ...]
- libraries checked: [<lib1>, <lib2>, ...]

## What already exists internally

For each relevant hit:
- Module path
- Function/class name
- What it does (1–2 sentences)
- Caveats or gaps

If nothing relevant: state explicitly.

## What exists in registered libraries

| Library | Module / Function | What it does | Use or skip? | Reason |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## What exists in docs (conventions / prior decisions)

For relevant hits:
- Doc path
- What convention or decision it captures

## Gaps

What is NOT covered by any existing implementation.

## Recommended implementation path

One of:
  existing  — use <module>.<function>
  wrap      — wrap <library>.<function>, needs interface alignment
  new       — implement from scratch (reason: ...)
  direct    — call <library> directly, no wrapper needed

## Next step

Suggested follow-on skill:
  literature-discovery (if gaps suggest novel territory)
  implement-feature workflow (if path is clear)
```

## Guardrails

- Search code corpus first, docs corpus second
- Always check internal code before checking libraries
- Never recommend a library without reading its codio entry
- Read actual source for any "looks relevant" hit —
  do not assess from snippet alone
- Capture ALL queries run in the note —
  this note is a reproducible record
- Do not recommend implementing something that already exists
- Do not mix bib/papers corpus into this skill — that is
  `literature-discovery`'s job
