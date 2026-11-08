---
title: "LSM Future Skills submission — prep status at deadline (2026-05-27)"
date: 2026-05-27
tags: [result, lsm, agentic-workshop-2026-09, session-checkpoint]
source_task: docs/log/task/task-arash-20260511-lsm-future-skills-ai-breakout.md
goal: agentic-workshop-2026-09
project_primary: projio
status: in-flight
---

## What this note is

A complete checkpoint of the LSM Future Skills 2026 breakout submission
work spanning May 11 → May 27. Captures decisions, artifacts, open
threads, and style guidance. Self-sufficient enough that a fresh session
can pick up either finishing the send or planning September.

## The submission, in one line

A two-page flyer plus a brief cover-note email, proposed contribution to
the LSM Future Skills 2026 breakout *AI in Daily Research — Sharing What
Works (and What Doesn't)* at LMU Biomedical Center on **2026-09-22**.
Submission deadline: **today, 2026-05-27**.

## Locked decisions

| Decision | Value |
|---|---|
| Title | *Open-science conventions as agent infrastructure* |
| Subtitle | *A stack-aware workflow experiment* |
| Slot | ~10 min talk + ~10 min discussion |
| Format | Short presentation + evidence walkthrough (no live demo) |
| Pattern-vs-tool framing | Pattern-first hedge. projio appears as one implementation; the convention work is the takeaway. |
| Diagram in flyer | TikZ (clean, polished, modern sans-serif) for the deadline. Swap with a hand-drawn Excalidraw before September. |
| Workshop dates | TBD (Sept 24–27 *or* Sept 29–Oct 2). Lock before announcement-finalization. |
| Drive folder | Created but unused for this send (manual PDF attachment is faster). |
| Sharing model | Anyone-with-link, when used. |
| Submission delivery | Direct PDF attachment to Tobias Niemann's email. |

## Artifacts on disk

| Path | Status |
|---|---|
| `docs/deliverables/presentations/lsm-future-skills-2026/proposal-flyer.qmd` | Two-page A4 flyer source. Renamed from `proposal-onepager.qmd` once it grew past one page. |
| `docs/deliverables/presentations/lsm-future-skills-2026/proposal-flyer.pdf` | Rendered. Re-render after final edits land. |
| `docs/deliverables/presentations/lsm-future-skills-2026/slides.qmd` + `slides.html` | Talk slide deck. Title aligned with submission title. Slide 5+6 reframed from live demo to evidence walkthrough. |
| `docs/deliverables/starters/projio-starter-lsm/` | Starter skeleton (README + `.mcp.json` + `.claude/settings.json` + one example idea note). Not yet populated with the working pipeline; deadline 2026-09-08 for that build-out. |
| `docs/log/task/task-arash-20260511-lsm-future-skills-ai-breakout.md` | The LSM task note. Talk-structure table, prep checklist, expanded 8-entry risk register, decisions log. |
| `docs/log/result/result-arash-20260527-lsm-prep-status.md` | This note. |

## Drive

| Folder | URL | Contains |
|---|---|---|
| Parent: *Agentic research workflow — public materials* | https://drive.google.com/drive/folders/1EqPDk4R2tD4BfaxC2i1qE6PjCPM_mLko | (empty; created during this session for future use) |
| LSM subfolder | https://drive.google.com/drive/folders/132DjdLzKuIGfzDmnHKFWBKMJDd0BkCHS | Empty; the flyer can be uploaded here later for a sharable URL, or skipped (current submission goes via direct attachment). |
| Workshop subfolder | https://drive.google.com/drive/folders/1dSkvR6sYmpmWpmKQo2e4_71UGirY_ZKm | Empty; for the 4-day workshop materials in late September. |

## Gmail

**Active draft:** `r-3680826232881077690` (the only one). Brief 4-paragraph
cover note with corrected signature. Subject: *Contribution to LSM Future
Skills 2026 breakout — "AI in Daily Research"*. Recipient:
`tobias.niemann@med.uni-muenchen.de`. **Needs the flyer PDF attached
before sending** (drag-drop in the Gmail UI; the MCP attach-by-base64
path failed earlier with size limits).

## Adversarial review history

Three rounds with an interact-session adversarial agent
(transcript: `~/.claude/projects/-storage2-arash-projects-projio/cdee1096-bab5-4c20-8598-c7920b6712b5.jsonl`,
total spend ~$0.94 in opus tokens).

- **Round 1** — pressure-tested the original abstract + 5-min projio
  deck + handbook frame chapter. Verdict: POLISH. Surfaced
  claim-evidence gaps, the pattern-vs-product trap, demo risk, and the
  too-soft honest-gaps content.
- **Round 2** — checked 4-month robustness and the pattern-first
  re-frame. Verdict: GO WITH HEDGE. Pattern-first framing, projio
  retained as the concrete implementation. Replaced "chained dispatch
  with dependency graphs" → "agents that hand off work to each other
  through the project's own files" for SDK-shift durability.
- **Round 3** — pressure-tested the LSM-specific slide deck + starter
  README. Verdict: POLISH. Six concrete edits applied (`.mcp.json`
  pixi-wrap, drop `projio init` from README, `idea-example.md` multi-file
  requirement, slide-6 scaffold replacing empty `*— live demo —*`
  placeholder, slide-7 fair comparison instead of grep strawman, slide-9
  bench-biology pattern-limit replacing aspiration-gaps).

## Style guidance discovered during this session

Captured to memory at `feedback_no_ai_prose_tells.md`. Short version:

- **No em-dashes** in prose. Use commas, parentheses, semicolons, or
  sentence breaks instead.
- **US spelling** (organized, summarized, catalog). Avoid US colloquial
  jargon ("crank it up", "kick the tires", "rubber meets the road").
- **Tone target:** modest about claims, enthusiastic about the
  conversation, technical, simple. Hedge claims with "I've found" /
  "In my experience". Express curiosity ("I'd love to hear how others…").
- **Avoid common AI-prose tells:** "not X but Y" constructions,
  antithesis patterns ("X is doing the work; the agent is the
  interface"), triadic lists when binary or single works, pithy
  closers ("Receipts, not recordings"), and jargon like "delve",
  "leverage", "robust", "ensure", "facilitate".

## Edits still pending on the flyer before final render

These are the unfinished edits in this session (as of writing the note).
Most can be done in 5–10 minutes:

1. **Evidence-section bullets** — full rewrite for em-dash removal +
   AI-tell cleanup. Includes:
   - Memory bullet: drop the `git log on the project is git log on its
     thinking` antithesis.
   - Grounding bullet: rewrite "The agent's claims trace back to
     citations; its code reuses what already exists rather than
     reinventing" antithesis. Replace "catalogue" → "catalog".
   - Exploratory bullet: remove em-dash; rewrite triadic-ish run-on.
   - Communication bullet: **add agentic maintenance of a GitHub/GitLab
     Pages site shareable with public/collaborators** (per the user's
     last instruction).
2. **Closing line** of the Evidence section — drop "Receipts, not
   recordings." pithy closer; rephrase the auditability line without
   it.
3. **Format section** — remove em-dashes around the projio link;
   rephrase "the takeaway I'd most like to land" tone.
4. **Workshop pointer** — minor tone polish; drop or rephrase "Happy to
   share more if it's useful" hedge-y closer.
5. **Re-render** the flyer after edits.

## Open threads for after-send / new session

### Excalidraw MCP setup (post-deadline)

User wants the diagram swapped from TikZ to a hand-drawn Excalidraw
before September. Available MCPs (web-searched 2026-05-27):

- `yctimlin/mcp_excalidraw` — 13 tools, but `export_to_image` requires
  a running browser canvas instance. Two-terminal setup (Express server
  + MCP server). Not feasible in this session.
- `excalidraw/excalidraw-mcp` (official) — similar streamable canvas
  model.
- `cmd8/excalidraw-mcp`, `i-tozer/excalidraw-mcp`, others — variants.

Alternative path: hand-author `.excalidraw` JSON + use
`@timhor/excalidraw-export-cli` (or similar) to render to SVG. Doesn't
need a browser.

Easiest path for the user: draw it in 10 minutes at excalidraw.com,
export SVG to `docs/assets/excalidraw/stack-as-agent-infrastructure.excalidraw.svg`,
ask me to embed.

### Other September-prep todos (already in Todoist as `lsm` and `agentic-workshop-2026-09` labels)

- Build out `projio-starter-lsm`: `pyproject.toml` with projio version
  pin, `pixi.toml`, `Snakefile`, `clean.py`, synthetic signal,
  `dataset_description.json` + `participants.tsv`. Target 2026-09-08.
- Audit slides + starter for projio API drift before talk. Target
  2026-09-15.
- Record asciinema cast of demo. Target 2026-09-15. *Note:* the talk now
  uses an evidence walkthrough, not a live demo, so this task may be
  scoped down to "screenshot capture" instead.
- Decide whether to extract starter to its own GitHub repo. Target
  2026-09-15.
- Practice run with one volunteer. Target 2026-09-20.
- Day-before hygiene: `fewer-permission-prompts` skill + venue display
  test.
- Deliver talk: 2026-09-22.

### 4-day workshop track (`agentic-workshop-2026-09` label, separate from LSM)

- Decide workshop dates (Sept 24–27 vs Sept 29–Oct 2) by 2026-06-15.
- Finalize workshop announcement + send by 2026-06-30.
- Draft `2026-09/syllabus.qmd` by 2026-07-31.
- Manim opening animation: storyboard by 2026-07-15, render by 2026-08-31.
- Pre-workshop setup checklist test on fresh VM by 2026-08-31.
- Workshop dry run with one volunteer by 2026-09-14.
- Workshop delivery: 2026-09-28.
- Post-mortem: early October.

## Recommendation if user starts a new session

A new session should:

1. **Read this note** in full.
2. **Read the LSM task note**
   (`docs/log/task/task-arash-20260511-lsm-future-skills-ai-breakout.md`)
   for the talk-structure table + risk register + prep checklist.
3. **Inspect the flyer source**
   (`docs/deliverables/presentations/lsm-future-skills-2026/proposal-flyer.qmd`)
   and apply the remaining edits listed above.
4. **Re-render** via
   `quarto render proposal-flyer.qmd` (Quarto v1.9 via pixi global; LuaLaTeX).
5. **Surface the PDF path** to the user, who attaches manually in Gmail
   and sends.
6. **Update the LSM task note status** from `pending` to `done` once
   sent.

If user is *not* starting a new session, finish here.
