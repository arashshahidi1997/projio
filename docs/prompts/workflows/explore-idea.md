# Workflow: Explore Idea

**Phase:** Exploration (Grand Routine steps 1–4)
**Purpose:** Go from an analysis idea to a recorded implementation decision.
**Input:** A research question, analysis request, or metric idea.
**Output:** An idea note + a task note with an implementation decision.

## When to use

When the user has a new analysis idea, metric request, or wants to evaluate
a method — and no implementation decision has been made yet.

## Steps

### 1. Capture the idea

```
note_create(note_type="idea", title="<descriptive title>")
```

The note should include:
- What problem / what data / what success criteria
- Expected output shapes and formats
- Known reference papers or terms
- Rough placement in pipeline topology (which pipe would own this?)

### 2. Discover existing code (ALWAYS do this first)

Run these in parallel:

```
codio_discover("<capability query>")
rag_query("<query>", corpus="code", k=8)
rag_query("<query>", corpus="codelib", k=5)    # if codelib corpus exists
```

For each promising candidate:
```
codio_get("<library_name>")
```

**Decision gate:** If a well-tested internal implementation exists → recommend
`existing`, skip literature, proceed to decision.

### 3. Search literature (conditional)

Only if step 2 reveals gaps, ambiguity, or novel territory.

```
rag_query("<query>", corpus="papers", k=8)
```

For key papers found:
```
paper_context("<citekey>")
paper_absent_refs("<citekey>")    # find unresolved references
```

Ingest missing key papers:
```
biblio_ingest(dois=["<doi>", ...], tags=["<relevant_tags>"])
```

### 4. Make the implementation decision

Choose one per component:

| Decision | When |
|----------|------|
| `existing` | Stable internal implementation covers it |
| `wrap` | Good external library, needs interface alignment |
| `new` | No suitable library, or APIs are unstable |
| `direct` | External library usable as-is |

Record the decision:

```
note_create(note_type="task", title="Implement <feature>")
note_update(path, fields={"status": "open", "tags": [...], "priority": "high"})
```

If new libraries were discovered:
```
codio_add_urls(urls=["<url>", ...])
```

Mark key papers:
```
biblio_library_set(citekeys=["<key>"], status="reading", priority="high")
```

## Output

1. An **idea note** documenting the question, discovery results, and literature
2. A **task note** with the implementation decision, tagged and prioritized
3. Any new libraries registered in codio
4. Any new papers ingested in biblio

## Transition

→ Hand off to `implement-feature.md` with the task note path as input.
