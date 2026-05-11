---
title: "Handbook + workshop roadmap (May → Sept 2026)"
date: 2026-05-08
timestamp: 20260508-handbook-workshop-roadmap
tags: [handbook, workshop, roadmap, planning, agentic-workshop-2026-09]
source_idea: docs/log/idea/idea-arash-20260507-221835-382557.md
source_goal: docs/log/goal/goal-arash-20260507-221912-674817.md
source_survey: docs/log/result/result-arash-20260508-tool-use-survey.md
source_spec: docs/log/result/result-arash-20260508-021908-627443.md
project_primary: projio
goal: agentic-workshop-2026-09
status: draft
---

## Purpose

This roadmap sequences the handbook + workshop initiative working backwards
from the September 2026 workshop. The spec
(`result-arash-20260508-021908-627443.md`) defined the chapter list and the
per-day workshop layout; the goal note
(`goal-arash-20260507-221912-674817.md`) defined the milestone calendar; this
document tells Arash **what to do, in what order, by when, and what to cut
first if behind**.

It is planning only. No prose, no provisioning, no code.

A note on inputs: the dispatcher task referenced two inputs that are not
yet on disk — `docs/handbook/_outline.md` (the chapter-1 task is what
will create it) and a separate `result-arash-20260508-workshop-syllabus-spec.md`
(folded into the layout/spec result). The roadmap below treats the layout/spec
result as the spec source and the handbook outline as a deliverable owed by
the chapter-1 task.

## 1. Backwards-planned milestone calendar

Anchoring milestones (from the goal note):

- 2026-05: workspace provisioned
- 2026-06: announcement finalized & sent
- 2026-07: syllabus drafted (per-session outcomes, exercise specs, prereqs)
- 2026-08: day 1–3 lecture/handout/exercises; manim opening rendered
- early 2026-09: dry run with one volunteer
- mid 2026-09: workshop delivered
- end 2026-09: post-mortem captured

Competing pressures the calendar absorbs (per goal note "Dependencies" and
the idea note `project_research_priorities.md` reference): **TAC III in May**
and **manuscript writing through June** are the dominant pulls. The May and
June workshop columns are deliberately light, with the heavy authoring load
pushed into July–August once those clear.

| Month | Workshop track | Handbook track | Cross-cutting |
|---|---|---|---|
| **May (residual)** | Provision `teaching/agentic-workshop/2026-09/` (task A); move announcement into the new workspace; register in worklog. | Handbook tree stub under `docs/handbook/` (empty files with H1 + "from survey: artifact X" pointers) per spec §B; outline committed to `_outline.md`; chapter 1 draft (task C). | Move Deep Research PDF into projio (task B); fix mkdocs nav patch for `Handbook` + `Blog` sections; **TAC III is the dominant claim — keep cross-cutting work small**. |
| **June** | Finalize announcement (room/dates/capacity/prereqs/credits); open registration. | Marimo-WASM prototype embedded in chapter 1 (task D); validate mkdocs embedding pattern; if it fails, decide fallback this month. Chapter 2 ("Reproducible foundations") drafted from artifacts #1, #5, #9 (lfp_extrema, cogpy primitives, ttl/ieeg re-BIDS). | Manuscript writing remains the dominant pull; protect a 4-h weekly "handbook slot" via `focus()`. |
| **July** | Syllabus.qmd authored: per-session learning outcomes, exercise specs (which dataset → which end state), pre-workshop checklist, day-4 rubric. Pre-workshop setup checklist test-run on a fresh machine. | Chapters 3 and 4 ("agentic layer", "working with the agent") drafted, anchored in artifact #2 (gecog mlclassifier iteration arc) — survey identifies this as "the cleanest single-feature iteration arc in the corpus". | Manim opening animation: storyboard locked, render started (long pole; cut-threshold mid-July if not storyboarded). |
| **August** | Day-1, day-2, day-3 lecture.qmd + handout.qmd + exercises/ (marimo `.py`) per spec §C; revealjs theme finalized; teaching dataset slice frozen in `shared/datasets/`. Day-4 rubric finalized. | Chapters 5 and 6 ("projio ecosystem", "worklog as orchestrator") drafted, anchored in artifacts #3 (factor_analysis), #4 (manifest_assemble + BidsPaths), #7 (notio agent-activity). Chapter 7 ("field notes") deferred — see §8. | Cross-link audit: every workshop handout `link into` correct handbook URL per spec §F; manim animation rendered final cut. |
| **early September** | Dry run with one volunteer through full day 1 (3 h morning + 3 h afternoon); friction notes captured; iterate exercises. | Honest-gaps page (`99-honest-gaps.md`) written from survey §"Honest gaps" — workshop participants will encounter the same gaps and need the page as a release valve. | Pre-workshop email with setup checklist + Claude credit instructions sent to participants. |
| **mid September** | Workshop delivered (days 1–4). Day-4 participant presentations. | (frozen — no handbook edits during delivery week to avoid breaking links) | Live `notio` capture during workshop for post-mortem feedstock. |
| **late September** | Post-mortem.qmd written same week; rubric outcomes captured; deltas for 2027 iteration logged in `shared/`. | Re-open handbook; back-port any clarifications discovered during teaching (anti-pattern: don't promise wholesale rewrite). | Goal `agentic-workshop-2026-09` closed; success criteria scored honestly (≥6 register, ≥5 present, ≥1 adopts). |

## 2. Dispatch order for the four pending tasks

The user's stated order is "provision first" (workspace). I disagree with it
narrowly: **the PDF move (task B) goes first** because it unblocks chapter 1
which is the marimo-WASM prototype's host, and the prototype is the
fail-fast signal for the entire interactivity strategy.

Numbered order with rationale:

1. **`task-arash-20260507-222003-098400.md` — Move Deep Research PDF.**
   Rationale: cheapest action (single `cp -L` + remove); unblocks chapter 1
   prose (task C) which depends on the PDF as conceptual frame; and
   unblocks the pattern decision in task D (chapter 1 hosts the
   marimo-WASM prototype). No dependencies upstream.

2. **`task-arash-20260507-221947-582556.md` — Provision workshop workspace.**
   Rationale: must precede *any* workshop authoring (announcement
   finalization, syllabus, day-N materials); and it reveals the
   `projio init` ergonomics that the workshop itself teaches in day-3
   exercise 01 (per spec §C). Doing this in May is on-time per the goal
   note; doing it later compounds delay because milestones 2 (June
   announcement) and 3 (July syllabus) sit on top of it.

3. **`task-arash-20260507-222028-504938.md` — Handbook outline +
   chapter 1 draft.** Rationale: the outline (`_outline.md`) is a
   prerequisite for committing the spec's nav patch to `mkdocs.yml`;
   chapter 1 sets the conceptual frame the rest of the handbook
   borrows vocabulary from. Should follow task B (PDF in place) and can
   run in parallel with task A's later steps.

4. **`task-arash-20260507-222051-589638.md` — marimo-WASM prototype.**
   Rationale: depends on chapter 1's existence to have a host page;
   serves as the **go/no-go signal** for the interactive-explorable
   strategy across the rest of the handbook. Defer until June so the
   prototype can iterate without competing with TAC III.

**Disagreement explicit, surface trade-off:** the user's "provision first"
order would push the PDF move and chapter-1 work behind the workspace
scaffold. The trade-off is small — task B is hours, not days — but doing
B before A means chapter-1 prose can begin the same evening and the
handbook nav patch lands in the same week. If the user prefers the
literal stated order (A → B → C → D) the cost is roughly one week of
chapter-1 latency, no other consequence.

## 3. Proposed new tasks (descriptions only — do not file)

Below are eight task notes that should exist for the roadmap to be
executable. Each has: title, priority, blocked-by, target month,
description, source note ref, goal ref. Arash files them himself.

> **Workshop announcement finalization** (priority: high; blocked-by:
> task A; target: 2026-06) — Finalize the announcement draft already
> moved into `2026-09/announcement.md`. Fill in: department + room +
> exact dates, capacity (idea note suggests 8–12), hardware/Claude
> credits policy, prereq strictness (PhD only? postdocs? PIs?). Send
> to department mailing list once registration form is wired. Source:
> `docs/log/idea/idea-arash-20260507-221835-382557.md` §"Workshop
> announcement draft". Goal: `agentic-workshop-2026-09`.

> **Workshop syllabus drafting** (priority: high; blocked-by:
> announcement-finalization; target: 2026-07) — Author
> `2026-09/syllabus.qmd`: per-session learning outcomes, hands-on
> exercise specs naming the dataset slice and end state, pre-workshop
> setup checklist for participants, backup plans (no internet, agent
> rate-limited, weird BYO data), day-4 assessment rubric, post-workshop
> deliverables. Cite spec §C session structure. Source:
> `docs/log/result/result-arash-20260508-021908-627443.md` §C. Goal:
> `agentic-workshop-2026-09`.

> **Handbook chapters 2–7 drafts** (priority: medium; blocked-by:
> chapter 1 draft + survey; target: 2026-06 → 2026-08, two chapters per
> month) — Six task notes (one per chapter), each anchored in the spec's
> chapter list (§B) and assigned its survey artifacts (§D table). Chapter
> 2 → artifacts 1/5/9; chapter 3 → 7/8; chapter 4 → 2; chapter 5 →
> 3/4/6; chapter 6 → worklog tools (no specific survey artifact, draw
> from worklog README); chapter 7 → "field notes" pulled from `docs/log/
> result/` cohort posts (artifact 10). Each chapter: H1 + frame + ≤ 1
> embedded marimo-WASM (only if §G.3 prototype validated) + cross-links
> to source artifacts. Source: `docs/log/result/result-arash-20260508-
> 021908-627443.md` §B and §D. Goal: `agentic-workshop-2026-09`.

> **Manim opening animation** (priority: medium; blocked-by: none —
> it's a long-pole render; target: storyboard 2026-07, render 2026-08)
> — One 3–5 min animation showing data → pipeline → dispatch → result
> through the projio architecture vs. a manual workflow. Source under
> `teaching/agentic-workshop/shared/manim/`. Reusable across iterations
> and as blog/social asset. Source:
> `docs/log/idea/idea-arash-20260507-221835-382557.md` §"Tooling
> decisions" → "Manim". Goal: `agentic-workshop-2026-09`.

> **Participant pre-workshop setup checklist + dry-run** (priority:
> high; blocked-by: syllabus draft; target: 2026-08) — Author
> `2026-09/pre-workshop-setup.qmd` with a step-by-step participant
> checklist: BIDS + DataLad install, conda/pixi env, Claude Code +
> account, projio init dry-run, `.mcp.json` permissions test. Run it
> end-to-end on a fresh VM or volunteer machine to flush hidden
> assumptions. Cite the runner-selection spec (CLAUDE.md "Runtime
> Environment Convention"). Source: `docs/log/goal/goal-arash-
> 20260507-221912-674817.md` "Milestones 3". Goal:
> `agentic-workshop-2026-09`.

> **Workshop dry run with one volunteer** (priority: high; blocked-by:
> day 1–3 materials drafted; target: early 2026-09) — Walk one volunteer
> through full day-1 (6 h) and capture friction notes via `notio`. Iterate
> exercises before the real workshop. Acceptance: post-dry-run friction
> log in `2026-09/dry-run-notes.qmd`; identified blockers fixed before
> workshop start. Source: `docs/log/goal/goal-arash-20260507-221912-
> 674817.md` Milestone 5. Goal: `agentic-workshop-2026-09`.

> **Workshop post-mortem** (priority: medium; blocked-by: workshop
> delivery; target: late 2026-09) — Write `2026-09/post-mortem.qmd` the
> week after delivery, before content fades. Score success criteria
> from the goal note (≥ 6 register, ≥ 5 present, ≥ 1 adopts). Capture
> deltas for 2027 iteration in `shared/`. Source: `docs/log/goal/goal-
> arash-20260507-221912-674817.md` Milestone 7. Goal:
> `agentic-workshop-2026-09`.

> **Open-question decision tasks** (priority: low; blocked-by: see
> §7; target: 2026-07 latest) — Three small task notes corresponding
> to the deferred questions in §7 below: public-OSS decision, blog
> co-residence decision, public title. Each is a half-day decision
> with the §7 evidence test. Source:
> `docs/log/idea/idea-arash-20260507-221835-382557.md` §"Open
> questions deferred". Goal: `agentic-workshop-2026-09`.

## 4. Cadence + publishing rhythm (≤ 150 words)

**Recommendation: Willison-style note→blog promotion, with a *fixed* weekly
4-hour handbook slot until July, doubling to two slots in July–August.**

- **May–June (TAC III + manuscript):** one 4-h handbook slot/week. Target:
  one chapter stub + one short blog post promoted from the week's `notio`
  captures. Mineault's drip cadence is the upper bound here; Willison's
  note→blog is a better fit for solo + competing-claim weeks.
- **July:** add a second slot/week. Target: two chapters/month + one Observable
  essay (per spec §E "one interactive essay/quarter").
- **August:** chapters drop weekly. Workshop materials dominate but reuse
  chapter prose verbatim where possible.
- **September:** **freeze** during delivery week. Resume Willison-style posting
  with workshop reflections post-event.

Defended against: solo author (low cost / no editorial coordination),
TAC pressure (visible weekly slot, not a vague intent), workshop deadline
(July escalation aligns with the syllabus deliverable).

## 5. Resource budget

| Resource | Budget | Cut threshold |
|---|---|---|
| Manim opening animation | 25 h total (10 h storyboard, 15 h render+iterate) over July–August | If not storyboarded by **2026-07-15**, drop to a static figure-storyboard slide deck. Animation is high-leverage but not workshop-critical. |
| Marimo-WASM explorables | 1 prototype (chapter 1) in June; up to 3 more (1 per "part" not per chapter) by August. Build cost: S = 4 h, M = 8 h, L = 16 h per explorable | If chapter-1 prototype fails to embed in mkdocs by **2026-06-30**, freeze at zero explorables and use static figures + "open notebook" links for the workshop. |
| Workshop teaching dataset | One curated slice per day (3 total) frozen in `shared/datasets/` by **2026-08-15**; reuse pixecog `lfp_extrema` (already TTL-clean) and a small gecog cohort for day-2/3 | If not frozen by 2026-08-15, fall back to an existing public dataset (e.g., a small OpenNeuro slice) — loses lab-specific motivation but keeps the workshop runnable. |
| Slide design | One shared revealjs theme under `shared/slide-templates/`, applied across all 3 lecture days. **8 h total** | If theme work overruns, default to revealjs default theme. Aesthetic, not didactic. |
| Figio figures specifically authored for the handbook | Zero new figio specs. Reuse the gecog May-02 cohort spec (artifact #10) as the sole demonstration; honest about "ad-hoc still common" per spec §F | This is already a hard cut. Do not budget more. |
| Observable interactive essay | One essay by 2026-07-31 ("How a worklog goal becomes a dispatched task" candidate per idea note). 12 h budget | If not started by 2026-07-15, defer to post-workshop blog. Not workshop-critical. |

Total cross-cutting investment ceiling: ~85 h between now and Sept 1.
Compared to the 4-h/week handbook slot (≈ 70 h) over 17 weeks, this is
sustainable only if July–August doubles to 8 h/week, as §4 prescribes.

## 6. Risk register

| # | Risk | Likelihood | Impact | Mitigation | Trigger |
|---|---|---|---|---|---|
| 1 | TAC III overruns May | M | M | Cut May handbook track to chapter-1 outline only; defer chapter-2 draft to June. Protect the workshop track (provision + announcement) at all costs. | TAC III deliverable not submitted by **2026-05-31**. |
| 2 | Manuscript writing overruns June | H | H | Reduce June workshop-track to announcement only; freeze handbook chapters 2–4 at "stub + outline"; reschedule full drafts to July. | Manuscript not submitted by **2026-06-30**; weekly handbook slot missed twice in a row. |
| 3 | marimo-WASM doesn't embed cleanly in mkdocs | M | M | Fall back to static figures + "open notebook" iframe-less links; document the fallback in §B's note for future chapters; no cascading impact on workshop (workshop uses native `.py` marimo, not WASM). | Chapter-1 prototype build (task D) fails or produces > 5 MB HTML or breaks mkdocs nav by **2026-06-30**. |
| 4 | Low workshop registrations (< 6) | M | H | Two weeks before, open registration to neighboring labs / collaborators; if still < 6, hold the workshop with the registered participants and publish the materials as a self-paced course. **Don't cancel** — materials are sunk cost regardless. | < 4 registrations by **2026-08-15**. |
| 5 | Lab/sirocampus infrastructure interruption (gamma/storage downtime, EZProxy outage) | L | M | Ensure all workshop materials are buildable from a participant's laptop without lab infra (no `worklog_*` calls in the handbook prose per `feedback_worklog_personal.md`; no sirocampus-specific paths in exercise scaffolds). Pre-workshop checklist tests this. | Any > 24 h infra interruption inside September. |
| 6 | Single-creator burnout | M | H | Hard cut to "what gets cut first" §8 list at first sign (missed slot 2 weeks running, or qualitative self-report). Goal note already cites this as the project's existential risk (Quantomatic warning). The workshop-with-fewer-chapters is a viable path; the workshop-with-burnt-out-author is not. | Two consecutive missed weekly handbook slots, or self-reported drag on `notio` ≥ 1 week. |

## 7. Open-question resolution plan

| # | Question | Evidence needed | Latest decision date | Default if undecided |
|---|---|---|---|---|
| 1 | Will projio become a public open-source tool with external adopters? | Workshop registrations + post-workshop survey of ≥ 1 participant adopting projio (success criterion in goal note) | **2026-09-30** (workshop end). No decision needed before then; the architecture (handbook in `projio/docs/`) doesn't lock the answer. | Default: keep projio personal-stack-shaped. Revisit only if ≥ 2 external adopters appear within 6 months post-workshop. |
| 2 | Is the blog a section of the handbook site or its own surface? | Count and shape of first ~10 essays. If they're heavily projio-internal → stay co-resident. If they generalize beyond projio → consider extraction. | **2026-12-31** (after first 10 essays). | Default: stay co-resident on the projio mkdocs site (per idea note "Same site for now"). |
| 3 | Final public title (`coherence`, personal handle, …) | Working title *The Agentic Research Workflow* tested on the announcement audience. Reception of the announcement is the data. | **2026-06-15** (announcement send-out date). The title appears in the announcement — must be picked by then. | Default: ship with *The Agentic Research Workflow* as the workshop title; defer the "handbook brand" title to post-workshop. |

## 8. What gets cut first (ranked, hardest-to-easiest cut)

Read this top-down: the first item is what gets cut at first sign of
slippage. The workshop-delivery date is sacred; everything below is
*content* that can shrink to protect the delivery.

1. **Observable blog essay.** Cut first. Pure outreach, not workshop-critical, not a goal-note success criterion. Frees ~12 h.
2. **Marimo-WASM explorables for chapters 2–7.** Keep only chapter 1's prototype (the validation of the pattern). Replace with static figures + "open notebook" links. Frees ~30 h if all four would have been built.
3. **Chapter 7 "Field notes".** Open-ended, no workshop session depends on it. Freeze at one introductory paragraph. Frees ~8 h.
4. **Handbook chapter 5 "projio ecosystem" depth.** Reduce to a stub with cross-links to existing tutorials/how-to/explanation surfaces (already comprehensive per the survey). Workshop day-3 morning can be authored from those existing surfaces directly. Frees ~10 h.
5. **Manim opening animation.** Cut threshold mid-July (storyboard) or early-August (full render). Replace with a hand-drawn slide-deck storyboard. Frees up to 25 h. Workshop loses visual punch but keeps content.
6. **Workshop day-4 rubric depth.** Default to a one-page rubric (criterion, level, score) rather than detailed exemplars. Frees ~6 h.
7. **One workshop teaching dataset slice (drop day-3's bespoke slice).** Reuse day-2's dataset for day-3 exercises with a different question. Frees ~8 h.
8. **Chapter 4 "Working with the agent" depth.** This is workshop-day-2-afternoon's anchor and survey calls artifact #2 the cleanest single-feature arc — **don't cut below "stub + key beats"**. If pressure is severe, reduce to bullet outline; do not eliminate.
9. **Honest-gaps page (`99-honest-gaps.md`).** Last-resort cut, but cuttable: if not written by dry-run, gather verbal during teaching and back-port post-workshop.
10. **Workshop dry run with volunteer.** Absolute last cut. Removing this is a quality-of-delivery risk; the goal note's success criterion (≥ 5 present on day 4) likely requires day-1 to be smooth.

The handbook's chapters 1–3 are workshop-critical (frame + day-1 +
day-2 anchors). Chapters 5–7 are slack. This is the honest accounting
the dispatcher asked for.

## Method note

- Read all four pending tasks, the goal note, the idea note, the
  layout/spec result, and the tool-use survey.
- Verified: `docs/handbook/` and the workshop workspace do not yet
  exist (matches spec §"Method note"); `docs/log/result/` is the
  only path written to.
- Cited artifacts trace to the survey's table of 10 entries and the
  spec's §D mapping table — no fresh filesystem scans of study
  projects performed.
- Planning-only: no files created outside this single roadmap.
