---
name: always-complete
description: >
  The project's development philosophy "always complete, never finished": make
  what exists whole before adding anything new. Use when the user types
  /always-complete, says "always complete, never finished", asks to apply,
  recall or check against this philosophy, or asks what to complete before
  starting something new, in any project. With no other request it runs a
  read-only completeness check of the current project.
metadata:
  short-description: Complete what exists before expanding; read-only completeness check
  tags: [workflow, philosophy, completeness, planning, backlog]
  portable: true
---

# Always complete, never finished

Two different words:

- Complete: already whole. Every part is there and works with the rest, nothing is half-done, it is usable as it is.
- Finished: no more work needed, ever. Nothing is finished; everything keeps improving.

So every delivery is complete at its own scope and is never treated as finished. Growth comes from improving complete things, not from adding half-done features.

## How to apply it

1. Before building or proposing anything new, look at what exists in this project and list what is incomplete: half-built features, untested paths, known bugs, unreviewed content, stale docs, parts that don't work with each other. Offer those first.
2. Completion versus expansion: work that makes an existing feature whole (tests, docs, the missing piece of a flow, review fixes, real content for an existing structure) is completion. A new feature, mode or content area is expansion.
3. Park new ideas in the project's backlog (an "Ideas (parked)" section or its equivalent) rather than starting them; say where they went.
4. Scope each delivery so it is complete: smaller and whole beats bigger and half-done. If a piece of work can't be completed now, narrow its scope until it can, and name what was left out.
5. Never call something finished. Note what could improve next, without starting it.

## When invoked

If the user invokes this with no other request, run a short completeness check of the current project: what exists, what is incomplete (by the list in step 1), and what to complete first, in order. Plain words, no time estimates. Read-only unless the user asks for changes.

The check needs only the repository: git (`git status`, unpushed commits, recent log), the issue or todo notes and handoffs the project keeps, tests and docs. Use project tools such as projio's when they are there; none are required.
