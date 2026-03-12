# Search Before Creation

Before implementing new functionality or reading literature, the system encourages discovery of existing project knowledge.

## Typical order

1. Search local code intelligence (codio registry)
2. Inspect prior notes and documentation
3. Check external libraries
4. Consult literature
5. Implement new work

This reduces duplicated effort and improves reuse.

## From discovery to decision

Discovery results feed into explicit engineering decisions:

- **Reuse** existing internal implementation
- **Wrap** an external library with a project-specific interface
- **Depend** on an external library directly
- **Implement** new code

Projio aims to turn discovery into actionable engineering decisions rather than leaving agents to guess.

## Agent workflows

The MCP tool surface supports this workflow directly:

1. `codio_list` / `codio_discover` — search for existing implementations
2. `codio_get` — inspect curated library notes
3. `rag_query` — search code and documentation corpora
4. `note_search` — check prior design decisions
5. `citekey_resolve` / `paper_context` — consult literature

Parallel agents can study multiple libraries simultaneously. Results feed back into curated library notes for future reference.
