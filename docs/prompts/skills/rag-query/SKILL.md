---
name: rag-query
description: >
  Query the project RAG index for code, docs, or literature using
  projio MCP tools. Handles corpus selection, query refinement, and
  result formatting. Use when searching the codebase, project docs,
  or paper corpus.
metadata:
  short-description: Search code / docs / papers via RAG
  tags: [search, rag, cross-cutting]
  tooling:
    mcp:
      - server: projio
        tools:
          - rag_query
          - rag_query_multi
          - corpus_list
          - citekey_resolve
          - paper_context
---

# RAG Query

Search the project RAG index for code, documentation, or literature.

## Corpora

Available corpora depend on what is indexed. Check with `corpus_list()`
if unsure. Common corpora:

| Corpus | Contains | Use when |
|---|---|---|
| `code` | project source, library mirrors | finding implementations, function signatures |
| `docs` | project docs, specs, decision notes | finding conventions, specs, prior decisions |
| `papers` | extracted paper content (via biblio) | finding methods, parameters, validation |
| `codelib` | shared code library mirrors | finding external reference implementations |

## Inputs

- `QUERY` (required): what to search for
- `CORPUS` (optional): corpus name (default: infer from query)
- `K` (optional): number of results (default: 5)

## Workflow

### 1) Infer corpus if not specified

Infer from query intent:
- "how is X implemented" / "find function" / "which library" → `code`
- "what is the convention" / "spec for" → `docs`
- "paper about" / "method for" / "reference for" → `papers`

If ambiguous: ask the user to confirm.

### 2) Run primary query

```
rag_query(query=QUERY, corpus=CORPUS, k=K)
```

### 3) Refine if needed

If results are sparse or off-target, run 1–2 follow-up queries
with alternative terms:

```
rag_query_multi(queries=[
  {"query": QUERY, "corpus": CORPUS},
  {"query": "<alternative>", "corpus": CORPUS}
])
```

### 4) For papers results — deep read

If corpus is `papers` and a promising citekey appears:
```
citekey_resolve(citekeys=[<key>])
paper_context(citekey="<key>")
```

### 5) Format results

**For code:**
```
File: <path>
Relevance: <why this matches>
```

**For docs:**
```
Document: <path>
Section: <heading>
Summary: <key point>
```

**For papers:**
```
Paper: <citekey>
Key point: <paraphrased — never reproduce verbatim>
```

### 6) Suggest next action

Based on results, suggest:
- For code: "read file X lines Y-Z"
- For docs: "see spec at path X"
- For papers: "get full context with paper_context(<citekey>)"

## Guardrails

- Never mix corpora in a single query.
- Never reproduce copyrighted paper text verbatim — always paraphrase.
- Never fabricate results if RAG returns nothing — report "no results"
  and suggest alternative queries.
