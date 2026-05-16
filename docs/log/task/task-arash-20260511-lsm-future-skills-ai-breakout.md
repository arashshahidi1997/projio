---
title: "LSM Future Skills 'AI in Daily Research' breakout — submit contribution by 2026-05-27"
date: 2026-05-11
timestamp: 20260511-lsm-future-skills-ai-breakout
status: pending
actionable: true
prompt: ""
source_note: docs/log/idea/idea-arash-20260507-221835-382557.md
project_primary: projio
priority: high
due: 2026-05-27
goal: agentic-workshop-2026-09
blocked: false
blocked_by: ""
tags: [outreach, workshop, lsm, future-skills, agentic-workshop-2026-09]
gmail_thread: 19e16cf3eb2a658b
event_date: 2026-09-22
event_location: LMU Biomedical Center
contact: tobias.niemann@med.uni-muenchen.de
---

## Event

**LSM Future Skills 2026 — breakout: "AI in Daily Research — Sharing What Works (and What Doesn't)"**

- **Date:** 2026-09-22, LMU Biomedical Center
- **Audience:** PhDs + postdocs across the Life Science Munich Campus Network
- **Format:** each participant prepares a contribution — slides, demo,
  practical example, or own-format — followed by discussion. Intentionally
  informal but structured by short presentations.
- **Submission deadline:** **2026-05-27** — short summary + estimated
  duration → `tobias.niemann@med.uni-muenchen.de`
- **Organizer:** Future Skills - AI Session Organizing Team, LSM Campus
  Network (Tobias Niemann, med.uni-muenchen.de)
- **Email source:** Gmail thread `19e16cf3eb2a658b`, forwarded by `gsn@lmu.de`
  on 2026-05-11
- **PDF attachment:** `260504a_FutureSkills-SaveDate.pdf` (save date flyer)

## Why this matters (strategic fit)

This breakout's date and audience overlap the September 2026 workshop
(goal `agentic-workshop-2026-09`):

- **Audience overlap:** LMU early-career researchers — same recruiting
  pool the workshop targets.
- **Date proximity:** ~ 1 week before / after the workshop window (per
  goal-note milestone calendar, workshop is "mid–late September").
- **Theme alignment:** "AI in daily research, what works/doesn't" is
  exactly the Deep Research synthesis frame and the agentic-workshop
  pitch.

Treat the breakout as a **soft launch** for the workshop:

1. Road-test the demo + honest-gaps narrative on a small audience first.
2. Recruit 2–3 workshop participants directly out of the room.
3. Establish the framing before the workshop landing page is even live.

## Proposed contribution

**Working title:** *"Treating your research workflow as a manipulable
object: an agentic stack experiment"* (lead with the pattern; introduce
projio mid-talk as one implementation, not the headline).

**Slot:** 12–15 min talk + ~5 min Q&A. Confirm slot length with Tobias.

**Structure:**

| min | section | content |
|---|---|---|
| 1 | Hook | Most AI-in-research demos = single-task autocompletion. What if your whole workflow — notes, code, pipelines, dispatch — was a queryable, manipulable object? |
| 2 | Frame | Deep Research gap: mature interactive tools exist for individual computations (Jupyter, Snakemake) — not for the workflow as a whole. Reference the 7-paradigm taxonomy briefly. |
| 5–6 | **Demo** | Live (with recorded backup) — agents handing off through files. Show this session's own chain: research idea → survey → spec → roadmap, with each agent's output landing as a markdown file the next agent reads. Land outputs in `docs/log/result/`. Show `note_search` recall. **30-sec non-projio anchor:** show `grep -r` over `lab-notebook/` returning the same kind of result the agent-mediated query does — to prove the pattern lives outside projio. |
| 2 | What works | MCP permissions as real constraints; file-mediated agent handoffs (durable to SDK shifts); structured project memory; opus for synthesis / haiku for triage. |
| 2 | **What doesn't** | Lead with **provenance gap** (concrete: agent wrote `result-X.md` claiming a p-value; nothing forces it to cite the executed cell). Secondary: single-author fragility (Quantomatic), aspiration-gaps (figio adoption uneven, manuscript subsystem unexercised). Cite stack-axis survey honest-gaps. |
| 1 | Pitch | Primary: "clone `projio-starter` and try one MCP query today." Secondary: "4-day deep-dive workshop late September — adopt or adapt." |

## Submission abstract (pattern-first hedge, 4-month-robust — send by 2026-05-27)

> **Treating your research workflow as a manipulable object: an agentic
> stack experiment** — 15 min + 5 min discussion
>
> Most AI-in-research stories are about a single task: cleaning code,
> summarising a paper, drafting an email. I want to share something
> different — making the *whole research workflow* (data, pipelines,
> notebooks, notes, dispatched compute) into a queryable, manipulable
> object an agent can navigate.
>
> The demo: one prompt produces three linked documents — a literature
> survey, a design spec, and a roadmap — written by three agents that
> hand off work to each other through the project's own files, in under
> 20 minutes, with the audit trail back to source visible the whole way.
> The stack underneath is open-source and you may already use parts of
> it: BIDS for data layout, DataLad for versioning, Snakemake for
> pipelines, Marimo for reactive notebooks, Quarto/MkDocs for
> publication, and the Model Context Protocol (MCP) for agent
> permissions.
>
> The pattern I want to share is **treating those layers as a single
> queryable surface** an agent can navigate. I'll demo one
> implementation — an open-source tool, projio, that I've built around
> this stack — but the convention work (receipts on disk, permissioned
> tools, file-mediated handoff) is portable to whatever stack you
> already use.
>
> I'll show what works (permissioned MCP tools as real constraints,
> file-mediated handoffs between agents, structured project memory) and
> one concrete failure I haven't solved: agents write confident
> result-claims that aren't pinned to the executed notebook cell that
> produced them, so I still re-run analyses by hand to verify
> provenance.
>
> Attendees leave with a starter repo URL and one MCP query to try on
> their own project — adapt the convention work to your own stack. A
> longer follow-up workshop is planned for late September; details on
> request.

### Pre-pattern-hedge version (kept for diff — 2026-05-12)

The May 12 version led "*One tool — projio — composes them into something
agent-navigable*" (tool-first) and named *"chained dispatch with
dependency graphs"* in the what-works list. Adversarial review §2 flagged
both as 4-month-fragile:

- *"chained dispatch with dependency graphs"* is pinned to the current
  `schedule_queue(after=...)` mechanism. Per `handbook/90-future-directions/
  live-agent-communication.md`, the Claude Agents SDK will likely replace
  batched chains with live peer/supervisor dialogue within months —
  making "three chained agents" the dated-looking artifact by September.
- *"One tool — projio — composes them..."* is tool-first; reads as a
  projio commercial, doesn't survive single-author-fragility scenario in
  18 months. Replaced with the pattern-first hedge above: projio is one
  implementation; the convention work (receipts on disk, permissioned
  tools, file-mediated handoff) is the portable takeaway.

### Pre-rewrite version (kept for diff)

The earlier abstract led with "a single queryable, manipulable system"
(reads as product-marketing for projio), named no underlying stack
components before projio, listed "what doesn't" generically (single-
author fragility, brittle hooks, agent-confidence gap), and pitched the
4-day workshop directly. Adversarial review flagged all four; the
rewrite above addresses them.

## Decisions resolved (2026-05-11)

1. **Slot length:** 15 min talk + ~5 min discussion.
2. **Branding:** pattern-first; projio appears at minute 6 as one
   implementation alongside the named stack (BIDS / DataLad / Snakemake /
   Marimo / Quarto / MCP).
3. **Workshop dates:** option (a) — **workshop runs Sept 24–27 or
   Sept 29–Oct 2** so the breakout is a *teaser*, not a competitor.
   Action: update goal-note milestone calendar; close idea-note open
   question #3 (final dates) before announcement finalization.
4. **Demo content:** hybrid "scripted-replay middle ground" —
   - **Primary:** pre-recorded chain-dispatch run via `asciinema rec` (or
     OBS screen capture for the file-tree side), trimmed to ~3 min.
   - **Live segment:** one ~30-sec `doitlive` typing-replay of a single
     MCP prompt + the queue entry appearing in `list_queue` — the
     credibility moment.
   - **Split screen:** terminal on left, live `docs/log/result/` tree on
     right (e.g. via `watch -n 1 ls`) so audience sees outputs *appear*.
   - **Fallback:** if `doitlive` segment fails, asciinema playback covers
     the same content.

### Demo tooling notes

- `doitlive` (Python, single binary) — scripted "live typing": one keypress
  types the next chunk of a pre-vetted shell session. Conference-talk
  standard. Pip-installable.
- `asciinema rec` — record full terminal session as JSON, replay with
  `asciinema play` (terminal) or `asciinema-player` (web embed for slides).
- `demo-magic.sh` — lighter bash alternative to doitlive (`pe "cmd"` lines).
- `vhs` (Charmbracelet) — declarative `.tape` → headless GIF/MP4 render
  for slide embedding.
- TBD: clipboard-based variant the user remembered — possibly `doitlive`
  + tmux integration, or a custom `xdotool type "$(xclip -o)"` keybind.
  Confirm name before recording if found.

## Prep checklist (S/M/L)

- [ ] **S** — Reply to Tobias with abstract + slot length (deadline
  **2026-05-27**).
- [ ] **S** — Confirm workshop dates resolved (decision 3 above).
- [ ] **M** — **Starter repo** — minimal projio-init project the
  audience can `git clone` and run one `rag_query` against, with the
  starter MCP query baked into a `README.md`. Promised in the abstract;
  needs to exist before the talk. Target: 2026-09-08 (two weeks before
  delivery).
- [ ] **M** — Slides (8–10 panels) **for LSM-specific audience**.
  The existing `docs/deliverables/presentations/projio-5min/slides.qmd`
  is for projio adopters and **does not transfer wholesale** — the
  subpackage table is wrong for a wet-lab-heavy LSM audience per
  adversarial review. Build LSM-specific deck: hook + frame + named
  stack + demo + provenance-failure + starter-repo CTA. Do NOT reuse
  slide 3 (subpackage table).
- [ ] **M** — Demo flow scripted with credibility moment **anchored on
  output file appearing in right pane**, not on `doitlive` keystroke.
  Pre-warm one dispatch in the green-room 15 min before the talk so
  there is *always* on-disk output to point at; live segment dispatches
  a *second* job that confirms the pattern.
- [ ] **M** — "What doesn't" slide: lead with **provenance failure**
  (concrete instance — "agent wrote `result-X.md` claiming a p-value;
  nothing forces it to cite the executed cell"), not aspiration-gaps
  (figio adoption, manuscript subsystem). Keep secondary failures
  shorter.
- [ ] **S** — Test on venue display before the talk; the split-screen
  pane will get cropped on a 4:3 projector.
- [ ] **S** — Run `fewer-permission-prompts` skill on the demo project
  one day before — an MCP permission prompt mid-demo is fatal.
- [ ] **S** — Practice run with one volunteer (timeboxed, fresh ears).
- [ ] **S** — **Non-projio anchor for the demo**: 30-sec segment showing
  `grep -r` (or similar generic primitive) over markdown returning the
  same shape of result the agent-mediated query does, then explaining
  why the agent-mediated version composes where grep doesn't. Proves
  "the pattern lives outside projio" — defends against the "projio
  commercial" critique and the single-author-fragility narrative. Per
  adversarial review §Q2(d).
- [ ] **S** — **Audit abstract on 2026-09-15** (one week before talk)
  for projio API drift. If `pipeio_target_paths`, `schedule_queue`, or
  `note_search` have been renamed/restructured between May and
  September, update the starter repo `README.md` and the demo asciinema
  recording. Solo-developed project + 4-month gap = real rename risk.

## Risks

1. **Live demo fails.** Record a 60–90 s clip in advance; switch with one
   keystroke. Don't hinge the talk on live cooperation.
2. **Reads as a projio commercial.** Mitigate by leading with the
   *pattern* (workflow as manipulable object) and naming the stack
   components (BIDS, DataLad, Snakemake, Marimo, Quarto, MCP) before
   projio. Frame projio as "one implementation"; honest-gaps slide
   reinforces this.
3. **Workshop dates collide with Sept 22.** Resolve decision 3 above
   before sending the abstract — the workshop pitch slide depends on
   firm dates.
4. **Wet-lab audience loses the stack jargon.** Six unknown nouns (BIDS,
   DataLad, Snakemake, Marimo, Quarto, MCP) in one sentence loses half
   the LSM room. Mitigation: name them in the abstract but the *spoken*
   talk grounds each in one observable artifact before introducing the
   next. Surveyed audience type: PhDs + postdocs across Life Science
   Munich (includes bench biology + clinical research).
5. **4-day workshop ask too big for a 15-min audience.** Conversion
   funnel is ~30% lukewarm interest at 15 min → < 5% commits to 4 days.
   Mitigation: two-tier CTA — primary spoken ask is the starter repo +
   one query; the workshop is a secondary "longer follow-up; details on
   request." Abstract reflects this (workshop in parens, not headline).
6. **Provenance failure goes unnamed.** The honest-gaps content has to
   be specific enough that a skeptical PI in the room respects the
   honesty rather than reading it as apology theatre. Pick the
   provenance-claim-vs-executed-cell example. Bury the aspiration-gaps
   (figio, manuscript) — they sound like an unfinished side project to
   an outside audience.
7. **4-month projio drift (May → September).** Solo-developed,
   weekly-changing tool + 4-month gap between abstract commit and talk
   delivery. Specific risks per adversarial review §Q1:
   - **Tool-name drift** (e.g., `pipeio_target_paths` → `pipeio_paths`).
     Starter repo `README.md` MCP query fails live. Mitigation: audit
     2026-09-15 (one week before talk); re-record asciinema if renames
     landed.
   - **Pattern-shift drift.** The `schedule_queue(after=...)` chain
     pattern is flagged in `90-future-directions/live-agent-communication.md`
     as a transitional baseline the Claude Agents SDK will likely
     supersede with live peer/supervisor dialogue. By September, "three
     chained agents" may read as 2025 vocabulary.
   - **Mitigation built into abstract:** generalised demo phrasing to
     "agents that hand off work to each other through the project's
     own files" (durable to SDK shift; file-mediated handoff is the
     projio invariant). Removed "chained dispatch with dependency
     graphs" from the what-works list.
8. **Pattern-first re-frame risk: loses PhD-adopter audience.** Per
   adversarial review §Q2(b): pattern-first lands with ~30% of the
   room (postdocs with their own pipelines + PIs scouting for
   durable patterns) but risks losing the PhD-adopter majority in the
   first 90 seconds. Mitigation: the spoken talk grounds each stack
   component in a concrete artifact before introducing the next;
   starter-repo CTA at the end is the adopter on-ramp. The talk takes
   a stronger side (commit to the *pattern*), not a softer one — *not*
   "no opinion."

## Acceptance

- Abstract emailed to `tobias.niemann@med.uni-muenchen.de` by **2026-05-27**
- Workshop dates resolved (decision 3 → updated in goal note milestones)
- Slides + demo prepared by **2026-09-15** (one week before delivery)
- Workshop pitch slide finalized with real dates + registration URL

## References

- Idea note (workshop architecture, conceptual frame):
  `docs/log/idea/idea-arash-20260507-221835-382557.md`
- Goal note (workshop milestones, success criteria):
  `docs/log/goal/goal-arash-20260507-221912-674817.md`
- Stack-axis survey (honest-gaps source):
  `docs/log/result/result-arash-20260508-stack-axis-survey.md`
- Existing 5-min projio deck (slide reuse candidates):
  `docs/deliverables/presentations/projio-5min/`
