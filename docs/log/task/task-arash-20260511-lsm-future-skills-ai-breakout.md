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
| 5–6 | **Demo** | Live (with recorded backup) — chained MCP dispatch pattern. Show this session's own chain: research idea → survey → spec → roadmap, executed by 3 chained agents over ~17 min. Land outputs in `docs/log/result/`. Show `note_search` recall. |
| 2 | What works | MCP permissions as real constraints; `schedule_queue` with `after=` chains; notio as queryable project memory; opus for synthesis / haiku for triage. |
| 2 | **What doesn't** | Single-author fragility (Quantomatic warning); manuscript subsystem unexercised; figio adoption uneven across study projects; hooks brittle; gap between agent confidence and verifiable provenance. Cite stack-axis survey honest-gaps. |
| 1 | Pitch | "Agentic-research-workflow workshop runs end of September — same stack, more depth. Talk to me after." |

## Submission abstract (draft — send by 2026-05-27)

> **Treating your research workflow as a manipulable object: an agentic
> stack experiment** — 15 min + discussion
>
> Most AI-in-research stories are about a single task: cleaning code,
> summarising a paper, drafting an email. I want to share something
> different: how I'm reshaping my whole research workflow — notes, code,
> pipelines, dispatched compute — into a single queryable, manipulable
> system that an agent can navigate. I'll demo a live chained-MCP
> dispatch (one prompt → a survey, a spec, and a roadmap, written by
> three agents in sequence), show what works (permissioned tool
> surfaces, `schedule_queue` with dependency chains, structured project
> memory) and what doesn't (single-author fragility, brittle hooks, the
> gap between agent confidence and verifiable provenance). I'll also
> pitch a 4-day deep-dive workshop on the same stack at the end of
> September for anyone who wants to go further.

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
  2026-05-27).
- [ ] **S** — Confirm workshop dates resolved (decision 3 above) so
  the pitch slide has real registration URL.
- [ ] **M** — Slides (8–10 panels). Reuse content from existing 5-min
  projio intro deck under `docs/deliverables/presentations/projio-5min/`
  where it fits.
- [ ] **M** — Demo flow chosen + scripted. If recorded: capture a clean
  17-min chain run (or trimmed to ~5 min via cuts), narrate over it.
  If live: pre-warm the queue and validate timing on the actual venue
  laptop / network.
- [ ] **M** — "What doesn't" slide content: pull 4 specific items from
  the stack-axis survey honest-gaps section (when it lands at
  `docs/log/result/result-arash-20260508-stack-axis-survey.md`).
- [ ] **S** — Practice run with one volunteer (timeboxed, fresh ears).

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
