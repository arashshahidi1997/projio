# Workflow: Implement Feature

**Phase:** Exploration (Grand Routine steps 5–7)
**Purpose:** Implement, test, and validate a feature in a notebook demo.
**Input:** A task note with an implementation decision from `explore-idea.md`.
**Output:** Working code, passing tests, and a demo notebook with decision plots.

## When to use

When an implementation decision exists (task note with decision recorded)
and the user is ready to write code.

## Steps

### 1. Review the decision

```
note_read("<task_note_path>")
```

Extract:
- Implementation decision (`existing` / `wrap` / `new` / `direct`)
- Target libraries and their APIs
- Expected output shapes and formats

### 2. Study reference implementations

Based on the decision:

```
rag_query("<implementation pattern>", corpus="code", k=5)
codio_get("<library_name>")
```

If wrapping an external library, study its API:
```
rag_query("<library> API usage", corpus="codelib", k=5)
```

### 3. Implement

Write the code. Use RAG throughout to find patterns:
- Existing calling conventions in the project
- Similar implementations to follow
- Library-specific idioms

Check available build/test commands:
```
runtime_conventions()
```

### 4. Test

Write tests covering:
- **Shape checks** on known-shape inputs
- **Known-signal checks**: synthetic inputs → expected outputs
- **Edge cases**: single element, empty, all-NaN, zero signal
- **Regression anchor** (if wrapping): wrapper output matches direct library call

Run tests and fix failures before proceeding.

### 5. Notebook demo (scientific validation)

Create a notebook that:
- Imports the new API
- Runs on a small representative dataset (1–2 sessions)
- Produces 2–3 **decision plots** that would reveal bugs
- Includes enough narrative for a reviewer to assess correctness

**Gate:** Do NOT proceed to pipeline integration until:
- [ ] All tests pass
- [ ] Decision plots show expected behavior
- [ ] API is stable (no more signature changes expected)

### 6. Update the task note

```
note_update(path, fields={"status": "implemented", "tags": [...add "tested", "demo-ready"...]})
```

## Output

1. **Implementation** in the project's code directory
2. **Tests** passing
3. **Demo notebook** with decision plots
4. **Task note** updated to `implemented` status

## Transition

→ Hand off to `integrate-pipeline.md` when the user confirms the demo is satisfactory.
