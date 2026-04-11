---
name: literature-discovery
description: >
  Search the paper corpus for relevant methods, parameter ranges, and
  validation plots using projio bibliography tools. Step 3 of the grand
  routine — use when codelib discovery reveals gaps or novel territory.
  Produces a curated shortlist note linked to the idea note.
metadata:
  short-description: Search paper corpus for methods and parameters
  tags: [grand-routine, step-3, exploration, literature]
  tooling:
    mcp:
      - server: projio
        tools:
          - rag_query
          - rag_query_multi
          - citekey_resolve
          - paper_context
          - paper_absent_refs
          - biblio_docling
          - biblio_ingest
          - note_create
          - note_latest
---

# Literature Discovery

Search the paper corpus for methods, parameter ranges, and validation
plots relevant to an analysis idea.

## When to use

- Step 3 of the grand routine (gaps found in codelib discovery)
- Novel territory requiring scientific grounding
- Need parameter defaults justified by literature

Do NOT use for code searches — that is `codelib-discovery`.

## Inputs

- `QUERY` (required): what method, measure, or phenomenon to search for
- `IDEA_NOTE` (optional): path to idea note from `idea-capture`
- `CITEKEYS` (optional): known citekeys to read directly

## Workflow

### 1) Seed context from idea note

If `IDEA_NOTE` provided, read it and extract:
- the raw idea / problem statement
- expected output shape
- any citekeys or library names already mentioned

### 2) Broad RAG search (papers corpus only)

```
rag_query(query=QUERY, corpus="papers", k=10)
```

Then refine with 1–2 follow-up queries targeting:
- specific method names found in first results
- parameter ranges or validation conventions mentioned

### 3) Resolve promising citekeys

For each relevant result:
```
citekey_resolve(citekeys=[<key>])
```

Confirm the paper exists in the bibliography.

### 4) Deep-read relevant papers

For each confirmed citekey:

```
paper_context(citekey="<key>")
```

Extract:
- Methods and algorithms
- Parameter defaults and ranges
- Validation approach / expected behavior
- Key figures

Check for unresolved references worth ingesting:
```
paper_absent_refs(citekey="<key>")
```

### 5) Ingest missing key papers (if needed)

```
biblio_ingest(dois=["<doi>", ...], tags=["<relevant_tags>"])
```

### 6) Write curated shortlist note

```
note_create(note_type="task", title="Literature: <QUERY>")
```

Content structure:

```markdown
# Literature: <QUERY>

## Summary
2–3 sentences: what the literature says about this method.

## Candidate methods

| Method | Citekey | Key parameters | Notes |
|---|---|---|---|
| ... | ... | ... | ... |

## Recommended approach
Which method to implement, which defaults, why.

## Validation plots to reproduce
Which figures from which papers define correct behavior.
What synthetic signal should produce what output.

## Parameter ranges
Table of parameter names, typical values, units.

## Caveats
Known pitfalls, edge cases, sensitivity.

## Citekeys read
List with one-line summary each.
```

### 7) Link back to idea note

If `IDEA_NOTE` exists, update it with a reference to this note:
```
note_update(path=IDEA_NOTE, fields={"references": ["<literature_note_path>"]})
```

## Guardrails

- NEVER query code or docs corpus — papers corpus only.
- NEVER invent citekeys — only use keys returned by RAG or
  provided by the user.
- NEVER reproduce copyrighted text verbatim — paraphrase all content.
- If `rag_query` returns no results: report "no results found for
  query X" and suggest alternative query terms. Do not fabricate results.

## Output format

Report:
1. Queries run + result counts
2. Citekeys resolved (found / not found)
3. Path to curated shortlist note
4. Recommended approach (one paragraph)
5. Suggested next step
