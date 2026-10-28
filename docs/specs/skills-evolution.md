# Skills: planning layer, overlays, usage signal (design note)

Status: **proposal, awaiting decision.** Nothing here is implemented.
Source: issue `20261028-105833-463321`, items 3 to 5, filed from pixecog's
workspace refactor (pixecog decisions WR-D9, WR-D12). Items 1 and 2 of the
same issue (synced-copy header, read-only copies, `projio sync --check`,
the skill lint) are done; see [skills reference](../reference/skills.md).

Each section gives the problem, the options, and a recommendation.

## 3. A pluggable planning layer

**Problem.** The seven `questio-*` skills assume a milestone and question
model (`plan/questions.yml`, statuses, dated milestones). In pixecog it went
unused: 7 of 241 result notes carry a valid `question:`, all 9 questions are
`not_started`, and across 136 transcripts `px-next` ran 0 times. The layer
that did get used is per-thread state docs (`docs/analysis/<thread>/index.md`
with stable finding IDs R/I/D/O, driven by `px-analysis-log` and
`px-analysis-orientation`). Today every projio project gets the questio
skills synced whether it plans that way or not, so they cost context and
mislead the agent.

**Options.**

- **A. Per-project skill selection.** A `skills:` block in
  `.projio/config.yml` with `disable: [questio-*]` (globs), honored by
  `_discover_skills`, `agent_instructions()` and `projio sync`. Generic,
  small, and useful beyond planning (a project without pipelines can drop the
  pipeio skills).
- **B. Planning as a named mode.** `planning: questio | threads | none`;
  skills declare `metadata.planning: questio` and are synced only when the
  mode matches. More explicit, but a new concept that only one subsystem
  uses.
- **C. Upstream the state-doc model.** Ship generic `analysis-log` and
  `analysis-orientation` skills (thread index page, stable finding IDs,
  orientation read at session start) as a projio pattern, with a small
  `projio`/notio helper to create a thread and allocate IDs. questio shrinks
  to a hypothesis registry that threads can reference.

**Recommendation.** A now, C after pixecog has run WR-D12 for a few weeks.
A is a few lines in discovery and fixes the immediate cost for every
project. C should be generalized from a model that has held up in use,
not from its first month; when it lands, `planning` becomes a documented
convention ("disable questio-*, enable the thread skills"), so B is not
needed.

## 4. Overlays: `extends:` instead of forked skills

**Problem.** Projects copy a generic skill to add project specifics
(`px-session-wrap` vs `session-wrap`), or chain aliases (`px-gallery` is an
alias of an alias). Forks go stale when the generic skill changes (item 2
of the same issue). `pixecog-flow-setup` shows the better pattern: it
layers on `pipeio-flow-create` and tells the agent to read that first, but
the layering is prose, so nothing checks it and the agent pays an extra
skill load.

**Options.**

- **A. Sync-time composition.** A project skill declares
  `extends: pipeio-flow-create` in its frontmatter. `projio sync` renders
  the synced copy as the base body followed by a "Project specifics" part
  from the overlay; the overlay's own `description` wins. The stamp hashes
  both sources, so `--check` reports the copy stale when either changes.
  With `replaces: true` the base skill is not synced on its own, which
  removes the duplicate entry from the skill list.
- **B. Runtime reference only.** Keep the prose pattern, but have
  `agent_instructions()` and the synced copy show "extends X" and hide X
  from the listing. No composition, so the agent still loads two skills.
- **C. Section-level overrides.** The overlay replaces named sections of the
  base (`## Workflow`, `## Hard rules`). Most precise, but it couples
  overlays to the base's headings and breaks silently when they move.

**Recommendation.** A, append-only. Composition happens once at sync, the
result is a single read-only copy (with the GENERATED header naming both
sources), and `--check` already covers staleness. Add to the lint: an
`extends:` target that does not exist, an overlay that extends another
overlay (the alias-of-alias case), and a project skill whose body is mostly
a copy of a bundled skill (suggest `extends:`). Skip C until a real overlay
needs to remove base text.

## 5. Skill usage signal

**Problem.** Nobody knows which skills are used. pixecog counted by hand
from transcripts to find that `px-next` was never used while
`px-analysis-log` ran 24 times.

**Options.**

- **A. Count from transcripts after the fact.** Claude Code transcripts
  (`~/.claude/projects/<slug>/*.jsonl`) record each `Skill` tool call with
  its skill name, and MCP `skill_read(name)` calls for other agents. A
  `projio skills usage [--since 30d]` command (or a worklog aggregation
  across projects) counts them per skill and per session. No runtime
  change; works on history that already exists.
- **B. Log at invocation.** A `PreToolUse` hook on the `Skill` tool, plus a
  line in the `skill_read` MCP tool, appends `{time, project, skill,
  session}` to `.projio/skills/usage.jsonl` (gitignored). Exact and cheap,
  but only counts from the day it is installed, and the hook lives in
  per-user Claude Code settings.
- **C. Both.** A for the backfill and the report; B later if transcript
  parsing proves brittle across Claude Code versions.

**Recommendation.** A, as a `projio skills usage` report that lists each
skill with its call count, last use and sessions since last use, and flags
skills unused for N sessions (default 30) as retirement candidates; worklog
can call it per project for a cross-project view. It answers the question
with data that already exists and adds nothing to the agent's runtime path.
Revisit B only if the transcript format changes under it.

## Decisions needed

1. Item 3: per-project `skills.disable` now, and upstream the thread
   state-doc model later? Which project leads the generic version?
2. Item 4: `extends:` composition at sync time, append-only, with
   `replaces:` to hide the base?
3. Item 5: transcript-based `projio skills usage`, and the retirement
   threshold (sessions unused)?
4. From item 1: rename the default project skills folder from
   `.projio/skills/` to `.projio/project-skills/` (proposal in the
   [handbook skills page](../handbook/70-agentic/skills.md))?
