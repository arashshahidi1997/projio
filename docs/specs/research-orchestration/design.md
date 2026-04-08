# Research Orchestration Layer — Design Spec

**Status:** draft
**Date:** 2026-04-07
**Origin:** idea-arash-20260407-225257-089158 (pixecog), idea-arash-20260407-225436-752515 (projio)

## 1. Problem

Projio's six subsystems cover execution (pipeio), knowledge capture (notio, biblio, codio), retrieval (indexio), and presentation (figio, manuscripto). But no subsystem understands **why** work is being done. An agent can run a pipeline and capture a note, but cannot answer:

- "What pipeline runs are needed to test hypothesis H3?"
- "Is there enough evidence to draft the Results section for H4?"
- "What is the highest-impact unblocked task right now?"
- "What should the supervisor see this week?"

These require a **research reasoning layer** that connects hypotheses to evidence to manuscript — the missing ~40% of the research workflow.

### The gap in concrete terms

| Capability | Current state | What's missing |
|------------|--------------|----------------|
| Track research questions | Manual markdown in `plan/` | Machine-readable registry, query tools |
| Link results to hypotheses | Unstructured note tags | Typed evidence records with hypothesis/milestone fields |
| Assess evidence sufficiency | Human reads notes and judges | Automated gap analysis per hypothesis |
| Decide what to work on next | Human reads milestones | Dependency-aware dispatch based on hypothesis impact |
| Bridge evidence to manuscript | Human copy-pastes results | Structured evidence → manuscript section mapping |
| Report progress | Human writes summary | Automated progress aggregation |

## 2. Design principles

1. **Convention over configuration** — the data model uses plain YAML/markdown in `plan/`. No database, no daemon. Git-native.
2. **Read-first** — most value comes from querying existing plan/ and log/ data. Write tools come later.
3. **Composable, not monolithic** — this layer orchestrates existing subsystems (pipeio, notio, manuscripto), not replaces them.
4. **Project-local** — this is per-project research reasoning. Cross-project coordination belongs to worklog (which may optionally consume this layer's data, never the reverse).
5. **Agentic-first** — tools are designed for autonomous agent workflows: orient → plan → execute → record → assess → write.
6. **Graceful degradation** — works with partial data. A project with only `plan/hypotheses.yml` still gets value; structured result notes and milestone tracking add more.

## 3. Naming

**Decided: questio** — from Latin *quaestio* (question, inquiry). Research is fundamentally question-driven. The central entity is the research question (hypothesis is a specific type). The subsystem manages the cycle from question → evidence → answer → manuscript. Short, clear, follows the `*-io` pattern.

## 4. Architecture

### 4.1 Not a separate package

Unlike biblio or pipeio, this layer is **compositional** — it orchestrates existing subsystems rather than managing a new domain with substantial independent logic. Making it a separate package would create circular import issues (it needs pipeio, notio, manuscripto), add a package for what is primarily query/aggregation logic, and fragment the orchestration that is projio's core value.

### 4.2 Skills-first, convention-driven

Questio is implemented as **three lightweight layers**, not a full subsystem module:

| Layer | What | Where |
|-------|------|-------|
| **Convention** | YAML schemas for questions + milestones | `docs/plan/questions.yml`, `docs/plan/milestones.yml` |
| **Note type** | Dedicated `result` note type with structured frontmatter | notio.toml + `docs/log/result/` |
| **Skills** | Prompt-based skills that compose existing MCP tools | `.projio/skills/questio-*.md` |
| **Query tools** | 2–3 thin MCP tools for structured YAML parsing | `src/projio/mcp/questio.py` |

The "intelligence" lives in the skill prompts — the agent uses existing tools (notio, pipeio, manuscripto) to execute. The only hard code is a thin MCP module for structured queries that skills can't do efficiently (dependency graph resolution, milestone aggregation, evidence gap analysis).

```
# Code footprint (minimal)
src/projio/
  mcp/
    questio.py                # 2–3 MCP tools: questio_status, questio_gap, questio_docs_collect

# Convention footprint (per-project, all under docs/plan/)
docs/plan/
  questions.yml               # research question registry (YAML, source of truth)
  milestones.yml              # milestone definitions with dependencies (YAML, source of truth)
  questions.md                # auto-generated from questions.yml
  milestones.md               # auto-generated from milestones.yml
  roadmap.md                  # auto-generated mermaid diagram from dependency graph
  evidence.md                 # auto-generated evidence index grouped by question

# Evidence capture
docs/log/result/              # notio result notes with structured frontmatter

# Skills
.projio/skills/
  questio-status.md           # orient: show research state
  questio-next.md             # plan: recommend highest-impact work
  questio-record.md           # record: guided result capture
  questio-report.md           # report: supervisor-ready summary
  questio-docs-refresh.md     # docs: regenerate plan/ pages from YAML
```

### 4.3 Data model as convention

Data lives in the project repo under `plan/` as YAML files. No hidden directories, no `.projio/questio/`. Humans can read and edit the YAML directly. The YAML is the **single source of truth**; all rendered markdown in `docs/plan/` is auto-generated output (like `compiled.bib` in the biblio pipeline).

### 4.4 Dedicated `result` note type

Evidence is captured as notio notes with a dedicated `result` type — not just tagged `idea` notes. This gives:

- Own directory (`docs/log/result/`) — avoids cluttering `idea/` with structured data
- Own template with pre-filled frontmatter fields (question, milestone, metric, etc.)
- Own index page on the docs site
- Clear separation between exploratory ideas and structured evidence

Requires adding a `result` note type to notio's configuration (via project-level `notio.toml`).

## 5. Data model

### 5.1 Research questions (`docs/plan/questions.yml`)

```yaml
# docs/plan/questions.yml
questions:
  H1:
    text: "Do cortical delta waves precede ripple initiation?"
    type: hypothesis                    # hypothesis | exploratory | descriptive
    prediction: "Large, spatially coherent cortical delta waves precede ripple initiation"
    pipelines: [spectrogram_burst, sharpwaveripple, coupling_spindle_ripple]
    milestones: [swr-detection-validated, delta-event-detection, delta-ripple-coupling]
    manuscript_section: results/h1-delta-ripple
    status: not_started                 # not_started | in_progress | blocked | sufficient | confirmed | refuted
    depends_on: []                      # other question IDs
    citations: ["@sirota_2003", "@isomura_2006"]

  H2:
    text: "What are the cortical origins of ripple-driving spindles?"
    type: hypothesis
    prediction: "Ripple-triggering spindles originate from specific association regions"
    pipelines: [spectrogram_burst]
    milestones: [spindle-detection-validated, spindle-topography-mapped]
    manuscript_section: results/h2-spindle-origins
    status: not_started
    citations: ["@siapas_1998", "@pedrosa_2024"]
```

**Design choices:**
- Questions are the top-level entity, not hypotheses — supports exploratory research too.
- `type` field distinguishes hypothesis (testable prediction) from exploratory (open-ended) from descriptive (characterization).
- `pipelines` lists pipeio flow names needed to generate evidence.
- `milestones` lists prerequisite milestones (defined separately).
- `manuscript_section` maps to manuscripto section paths.
- `status` uses a research-appropriate vocabulary, not generic task states.

### 5.2 Milestones (`docs/plan/milestones.yml`)

```yaml
# docs/plan/milestones.yml
milestones:
  preprocessing-stable:
    description: "All preprocessing pipelines validated for all subjects"
    pipelines: [preprocess_ieeg, preprocess_ecephys]
    depends_on: [ttl-removal-validated]
    status: in_progress
    evidence: []

  swr-detection-validated:
    description: "SWR detection validated across all subjects"
    pipelines: [sharpwaveripple]
    depends_on: [preprocessing-stable]
    status: not_started
    evidence: []                        # filled by agent or manually: list of note IDs

  delta-ripple-coupling:
    description: "Delta-ripple temporal coupling quantified"
    pipelines: [coupling_spindle_ripple]
    depends_on: [swr-detection-validated, delta-event-detection]
    status: not_started
    evidence: []

  ttl-removal-validated:
    description: "TTL artifact removal validated for iEEG and neuropixels"
    pipelines: [preprocess_ieeg]
    depends_on: []
    status: in_progress
    evidence: []
```

**Design choices:**
- Milestones are decoupled from questions — multiple questions can share a milestone.
- `depends_on` enables dependency graph resolution for dispatch.
- `evidence` is a list of note IDs (pointers to notio result notes).
- Status vocabulary: `not_started | in_progress | blocked | complete`.

### 5.3 Evidence records (notio `result` notes)

Evidence is captured as notio notes with a dedicated `result` type:

```yaml
# docs/log/result/result-arash-20260415-143022-123456.md
---
title: "SWR detection rate across subjects"
tags: [result]
series: sharpwaveripple
question: [H1, H3]                     # links to questions.yml IDs
milestone: swr-detection-validated      # links to milestones.yml ID
subjects: [sub-01, sub-02, sub-03, sub-04, sub-05]
metric: detection_rate_per_minute
value: "12.3 +/- 2.1"
figure: docs/pipelines/sharpwaveripple/notebooks/swr_detection_summary.html
confidence: preliminary                 # preliminary | validated | final
---

SWR detection produces 12.3 +/- 2.1 events per minute across 5 subjects.
Rate is consistent with literature values (10-15/min during NREM).
...
```

**Qualitative evidence** — not all results have metrics. Observations ("the spectrograms
look clean after filtering") use the same note type with `metric: qualitative` and
the `value` field as free text:

```yaml
metric: qualitative
value: "Spectrograms show clean signal after TTL removal, no residual artifacts visible"
confidence: preliminary
```

**Design choices:**
- Uses notio infrastructure — no parallel note system.
- Dedicated `result` note type → own directory (`docs/log/result/`), own template, own index.
- `question` and `milestone` fields are the semantic links that enable evidence querying.
- `confidence` tracks how "done" a result is (preliminary findings vs validated vs final).
- `metric` + `value` support both quantitative and qualitative evidence.

### 5.4 Compatibility with existing pixecog plan/

Pixecog already has `plan/Milestones.md` (markdown tables) and `plan/master/03-Questions-and-Hypotheses.md` (prose). The migration:

1. Convert existing markdown tables → `docs/plan/questions.yml` + `docs/plan/milestones.yml`.
2. Existing `plan/Milestones.md` becomes an auto-generated output (regenerated by `questio_docs_collect`).
3. `plan/master/03-Questions-and-Hypotheses.md` remains as the prose narrative — YAML handles the structured/queryable data, prose handles the scientific context.
4. YAML is the single source of truth. All rendered views in `docs/plan/` are output artifacts.

## 6. Tools and skills

Questio divides its surface into **MCP tools** (structured queries requiring code) and **skills** (prompt-based compositions of existing tools). The split follows a simple rule: if it needs to parse YAML, resolve a dependency graph, or aggregate structured data — it's a tool. If it needs judgment, composition, or natural language output — it's a skill.

### 6.1 MCP tools (hard code — `src/projio/mcp/questio.py`)

| Tool | Args | Returns | Description |
|------|------|---------|-------------|
| `questio_status` | `question_id?` | questions with status, evidence counts, milestone completion %, blockers | Overview of research state. Parses YAML + scans result notes. No args = all questions. |
| `questio_gap` | `question_id` | unmet milestones, missing pipeline runs, confidence levels, dependency blockers | "What's missing to answer H3?" Requires dependency resolution. |
| `questio_docs_collect` | — | list of generated files | Regenerate `docs/plan/` pages from YAML: questions table, milestones table, mermaid roadmap, evidence index. Follows `pipeio_docs_collect` pattern. |

**Tool count: 3.** Everything else is a skill.

### 6.2 Skills (prompt-based — `.projio/skills/questio-*.md`)

| Skill | Composes | Description |
|-------|----------|-------------|
| `questio-next` | `questio_status` + `questio_gap` + `pipeio_flow_status` | "What should I work on?" Agent reasons over status + gaps to recommend highest-impact unblocked work. |
| `questio-ground` | `paper_context` + `codio_discover` + `rag_query` | Before starting work on a milestone: gather literature context, find existing code, search prior decisions. Sets quality criteria and expected values. |
| `questio-record` | `note_create(type="result")` + YAML update | Guided result capture: agent creates a result note with proper frontmatter, then updates `milestones.yml` evidence list. |
| `questio-validate` | `pipeio_nb_exec` + `pipeio_nb_read` + `questio-record` | Run validation notebook across subjects, check against expectations, record evidence if satisfactory. |
| `questio-report` | `questio_status` + `note_search` | Generate supervisor-ready progress summary: milestones hit, key results, blockers, next steps. |
| `questio-ready` | `questio_status` + `questio_gap` + `manuscript_status` | "Which manuscript sections can I draft now?" Check evidence sufficiency per question. |
| `questio-session` | `questio_status` + `questio-next` + `questio-ground` + `questio-report` | Full research session workflow: orient → plan → ground → work → report. |
| `questio-docs-refresh` | `questio_docs_collect` + `pipeio_docs_nav` | Regenerate all plan/ docs and patch mkdocs nav. |

### 6.3 Why this split works

Skills handle **judgment calls** (what's highest-impact? is this evidence sufficient? what should the supervisor see?) — these benefit from LLM reasoning and don't need deterministic code. The agent reads the structured data via `questio_status`/`questio_gap`, then applies research judgment.

MCP tools handle **structured data operations** (parse YAML, resolve dependency graphs, count evidence, generate markdown) — these need deterministic code and would be unreliable as prompt-only skills.

### 6.4 Tools and skills NOT included (and why)

| Excluded | Reason |
|----------|--------|
| `questio_dispatch` (auto-run pipelines for a hypothesis) | Premature automation. Agent calls `questio-next` then `pipeio_run` itself. |
| `questio_milestone_update` as MCP tool | YAML file edit is simple enough for a skill (`questio-record`) to handle via file write. |
| `questio_evidence` as MCP tool | `questio_status` returns evidence counts; the skill can `note_search(tags=["result"], series=...)` for full details. |
| `questio_deps` as MCP tool | `questio_gap` already returns dependency information. Mermaid diagram is in the auto-generated `roadmap.md`. |
| Anything calling worklog | Worklog is external. One-way data flow: worklog reads `plan/` files, never the reverse. |

## 7. Agentic workflow

A fully autonomous research session using the tool set:

```
# 1. Orient
agent → questio_status()
  "7 questions. H1-H3 (CTX→HPC) blocked on preprocessing.
   Preprocessing: 2/4 milestones in_progress."

# 2. Plan
agent → questio_next()
  "Highest impact: complete ttl-removal-validated (blocks 3 milestones,
   which block 5 hypotheses). Action: run preprocess_ieeg for remaining subjects."

# 3. Execute (via pipeio)
agent → pipeio_run(flow="preprocess_ieeg", ...)
agent → pipeio_nb_exec(flow="preprocess_ieeg", notebook="validate_ttl_removal")

# 4. Record
agent → questio_record(
    question=["H1","H2","H3"],
    milestone="ttl-removal-validated",
    metric="ttl_artifact_residual_uv",
    value="< 0.5 uV across all subjects",
    confidence="validated",
    title="TTL removal validated — residual < 0.5 uV"
  )

# 5. Update milestone
agent → questio_milestone_update("ttl-removal-validated", status="complete",
    evidence=["idea-arash-20260415-143022-123456"])

# 6. Assess
agent → questio_gap(question_id="H1")
  "ttl-removal-validated: complete. preprocessing-stable: in_progress (ecephys pending).
   swr-detection-validated: not_started. delta-event-detection: not_started.
   delta-ripple-coupling: not_started. 3 milestones remaining."

# 7. Report
agent → questio_report(period="week")
  "This week: completed TTL validation milestone. Unblocked preprocessing-stable.
   Next: ecephys preprocessing, then SWR detection.
   Blockers: none. Estimated: 2 milestones achievable next week."

# 8. Write (when ready, future sessions)
agent → questio_ready()
  "H2 has sufficient evidence (2 validated results, all milestones complete).
   Manuscript section: results/h2-spindle-origins. Ready to draft."
agent → questio_evidence("H2")
  → feeds into manuscript_section_context for drafting
```

## 8. Operational workflows

Questio's value is not in tracking alone — it's in enabling **autonomous research loops** where the agent grounds its work in literature and code, executes analyses, assesses results, and iterates. This section defines the action components, the loops they compose into, and what can be automated.

### 8.1 Action components

Every research action maps to a projio subsystem. These are the atomic operations an agent performs:

| Phase | Action | Subsystem | Tool/Skill |
|-------|--------|-----------|------------|
| **Ground** | Check literature for methods, expected results, pitfalls | biblio | `paper_context`, `rag_query`, `biblio_discover_authors` |
| **Ground** | Find existing implementations, utilities, patterns | codio | `codio_discover`, `codio_get`, `codio_vocab` |
| **Ground** | Search project knowledge for prior work/decisions | indexio | `rag_query`, `rag_query_multi` |
| **Ground** | Check questio state — what's done, what's needed | questio | `questio_status`, `questio_gap` |
| **Develop** | Create new analysis notebook | pipeio | `pipeio_nb_create` |
| **Develop** | Update existing notebook (parameters, code) | pipeio | `pipeio_nb_update`, `pipeio_nb_sync` |
| **Develop** | Implement/modify pipeline rules and scripts | pipeio | `pipeio_rule_insert`, `pipeio_script_create` |
| **Execute** | Run notebook (single analysis) | pipeio | `pipeio_nb_exec` |
| **Execute** | Run pipeline (full dataset, Snakemake) | pipeio | `pipeio_run` |
| **Assess** | Inspect notebook outputs and figures | pipeio | `pipeio_nb_read`, `pipeio_nb_analyze` |
| **Assess** | Check pipeline run status and logs | pipeio | `pipeio_run_status`, `pipeio_log_parse` |
| **Assess** | Compare results against literature expectations | biblio + agent | `paper_context` + agent judgment |
| **Assess** | Validate against codio conventions | codio | `codio_validate` |
| **Record** | Capture structured evidence | questio | `questio-record` skill |
| **Record** | Capture unstructured observation or decision | notio | `note_create` |
| **Record** | Update milestone status | questio | via `questio-record` skill |
| **Plan** | Identify evidence gaps | questio | `questio_gap` |
| **Plan** | Recommend next action | questio | `questio-next` skill |
| **Write** | Check manuscript readiness | questio | `questio-ready` skill |
| **Write** | Draft manuscript section from evidence | manuscripto | `manuscript_section_context` |
| **Report** | Summarize progress | questio | `questio-report` skill |

### 8.2 Workflow loops

Research operates as nested loops at different timescales. Each loop has a clear entry condition, iteration logic, and exit condition.

#### Inner loop: Notebook development (minutes–hours)

The tightest loop. Agent iterates on a single notebook until it produces satisfactory results. **Fully automatable** for well-defined analyses.

```
                    ┌──────────────────────────────────────┐
                    │      NOTEBOOK DEVELOPMENT LOOP       │
                    │                                      │
  ground ──→ create/update notebook ──→ execute ──→ inspect
                    ↑                                 │
                    │          unsatisfactory          │
                    └─────────────────────────────────┘
                                                      │ satisfactory
                                                      ↓
                                               record evidence
```

**Entry:** milestone identified, analysis approach chosen.
**Grounding:** before first iteration, agent checks biblio for expected values/methods and codio for existing implementations.
**Iteration:** modify notebook code/parameters → execute → read outputs → assess quality.
**Exit:** results meet quality criteria (statistical significance, consistency with literature, no artifacts). Agent creates a result note.

**Example — SWR detection validation:**
```
1. biblio: paper_context("@sirota_2003") → expected ripple rate 10-15/min NREM
2. codio: codio_discover("sharp wave ripple detection") → cogpy.detection.swr exists
3. pipeio: pipeio_nb_create(flow="sharpwaveripple", notebook="validate_swr")
4. pipeio: pipeio_nb_exec(notebook="validate_swr", subjects=["sub-01"])
5. pipeio: pipeio_nb_read(notebook="validate_swr") → 12.3/min, looks good
6. pipeio: pipeio_nb_update(notebook="validate_swr") → add remaining subjects
7. pipeio: pipeio_nb_exec(notebook="validate_swr", subjects=["sub-01".."sub-05"])
8. pipeio: pipeio_nb_read → 12.3 ± 2.1/min across all subjects, consistent with literature
9. questio: questio-record(milestone="swr-detection-validated", ...)
```

#### Middle loop: Milestone completion (hours–days)

Agent works through all milestones required for a hypothesis. **Semi-automated** — needs checkpoint reviews between milestones.

```
                    ┌───────────────────────────────────────────────┐
                    │          MILESTONE COMPLETION LOOP            │
                    │                                               │
  questio_gap ──→ pick unblocked milestone ──→ inner loop(s) ──→ update milestone
                    ↑                                               │
                    │            milestones remain                  │
                    └──────────────────────────────────────────────┘
                                                                    │ all milestones complete
                                                                    ↓
                                                         question has sufficient evidence
```

**Entry:** `questio_gap(H3)` reveals unmet milestones.
**Iteration:** pick the deepest unblocked milestone → run inner loop(s) for required analyses → record evidence → update milestone → re-check gap.
**Exit:** all milestones for a question are complete.
**Checkpoint:** after each milestone completion, agent reports progress. Human may redirect priorities.

#### Outer loop: Research cycle (days–weeks)

Agent works across questions, prioritizing by impact. **Agent-guided, human-directed** — the agent proposes, the human approves direction changes.

```
                    ┌──────────────────────────────────────────────────┐
                    │              RESEARCH CYCLE                      │
                    │                                                  │
  orient ──→ questio-next ──→ middle loop ──→ assess ──→ report
                    ↑                                        │
                    │        questions remain                 │
                    └───────────────────────────────────────┘
                                                             │ question answered
                                                             ↓
                                                    questio-ready → manuscript
```

**Entry:** session start, `questio_status`.
**Iteration:** `questio-next` picks highest-impact question → middle loop → report progress.
**Exit (per question):** evidence sufficient → draft manuscript section.
**Human checkpoints:** direction changes, surprising results, interpretation decisions.

### 8.3 Automated action sequences

These are concrete, automatable sequences that map onto skills or scheduled agents:

#### Sequence A: Literature-grounded development

Before implementing any analysis, the agent grounds itself in literature and code. This sequence precedes every inner loop iteration.

```
biblio: paper_context(citations from questions.yml)
  → expected methods, expected values, potential pitfalls
codio: codio_discover(keywords from milestone description)
  → existing implementations, reusable utilities
rag_query: search project notes for prior attempts
  → what was tried before, what worked/failed
→ agent synthesizes: approach, expected results, quality criteria
```

**Skill:** `questio-ground` — "before starting work on milestone X, gather context."

#### Sequence B: Validation sweep

Agent runs a validation notebook across all subjects, checking each result against expectations. Fully automatable.

```
for subject in subjects:
  pipeio_nb_exec(notebook="validate_*", subject=subject)
  pipeio_nb_read → extract metrics
  compare against literature expectations (from grounding)
if all subjects pass:
  questio-record(confidence="validated")
else:
  flag failures, create observation note, iterate
```

**Skill:** `questio-validate` — "run validation for milestone X across all subjects."

#### Sequence C: Pipeline-to-evidence

After a pipeline completes, agent inspects results and converts outputs to evidence.

```
pipeio_run_status(flow) → check completion
pipeio_nb_exec(validation notebook) → run post-hoc analysis
pipeio_nb_read → inspect figures, metrics
biblio: compare to literature
if satisfactory:
  questio-record(question, milestone, metrics)
else:
  note_create(type="idea", tags=["observation"]) → capture what went wrong
  iterate on pipeline
```

#### Sequence D: Morning research session

Full session workflow from orient to report.

```
questio_status → orient
questio-next → pick highest-impact work
questio-ground → literature + code context
[inner loop: develop notebook/pipeline]
[middle loop: complete milestone if possible]
questio-report → summarize what was accomplished
questio_docs_collect → regenerate plan docs
```

**Skill:** `questio-session` — "start a research session on this project."

### 8.4 Human-in-the-loop checkpoints

Not everything should be automated. These decision points require human judgment:

| Decision | Why human needed | Agent's role |
|----------|-----------------|--------------|
| Changing research direction | Scientific judgment about hypothesis viability | Present evidence, flag surprises, suggest alternatives |
| Interpreting unexpected results | Requires domain expertise + intuition | Surface the anomaly, provide literature context |
| Judging evidence sufficiency | "Enough" is a scientific and political judgment | Report what exists, flag gaps, but don't decide |
| Choosing between competing methods | Trade-offs require contextual priorities | Present options with literature backing |
| Approving manuscript drafts | Quality and accuracy bar | Draft, but human reviews |

The agent should **surface** these decision points rather than silently resolving them. When an inner loop produces surprising results (metrics far from literature expectations), the agent should create an observation note and flag it rather than iterate silently.

### 8.5 Loop automation levels

| Loop | Automation | Agent autonomy | Human role |
|------|-----------|---------------|------------|
| Notebook development (inner) | Fully automatable for well-defined analyses | High — iterate until quality criteria met | Set quality criteria upfront |
| Validation sweep | Fully automatable | High — run, check, record | Review flagged failures |
| Milestone completion (middle) | Semi-automated | Medium — works through milestones, pauses at checkpoints | Approve direction, review evidence |
| Research cycle (outer) | Agent-guided | Low — proposes next steps | Approve priorities, interpret results |
| Session workflow | Structured by skill | Medium — follows session structure | Initiate, review report |

## 9. Integration with existing subsystems

### 9.1 pipeio

- `questions.yml` references pipeio flow names in `pipelines` field.
- `questio-next` resolves which pipelines need running by checking `pipeio_flow_status`.
- Inner loop composes `pipeio_nb_create` → `pipeio_nb_exec` → `pipeio_nb_read` for notebook development.
- Pipeline runs via `pipeio_run`; results assessed via `pipeio_run_status` + `pipeio_log_parse`.
- No changes to pipeio itself — questio reads pipeio state, doesn't modify it.

### 9.2 notio

- Evidence records are notio notes with extended frontmatter.
- Requires a `result` note type in notio.toml with the structured fields.
- `questio_record` delegates to notio's note creation infrastructure.
- `questio_evidence` queries notio by tags/series + parses frontmatter fields.

**Proposed notio.toml addition:**
```toml
[note_types.result]
mode = "event"
template = "result.md"
filename = "result-{owner}-{timestamp}"
toc_keys = ["question", "milestone", "metric", "confidence"]
toc_groupby = "series"
```

### 9.3 manuscripto

- `questions.yml` maps questions to manuscript sections via `manuscript_section`.
- `questio_ready` checks evidence sufficiency and reports which sections are draftable.
- `questio_evidence` output feeds into `manuscript_section_context` for drafting.
- No changes to manuscripto — questio provides structured input.

### 9.4 biblio

- `questions.yml` can reference citekeys in `citations` field.
- `questio_evidence` can include relevant literature alongside result notes.
- Grounding actions (sequence A) use biblio to set quality criteria and expected values before analysis.
- Assessment actions compare results against literature expectations.
- Minimal coupling — biblio is consulted, not modified.

### 9.5 codio

- Grounding actions use `codio_discover` and `codio_get` to find existing implementations before writing new code.
- Prevents re-invention: agent checks whether a method already exists in project libraries before implementing in a notebook.
- `codio_validate` can check that new implementations follow project conventions.
- No changes to codio — questio's grounding skills call codio read tools.

### 9.6 indexio

- `rag_query` and `rag_query_multi` provide project-wide knowledge search during grounding.
- Agent searches prior notes, decisions, and documentation before starting new work.
- `questio-ground` skill uses indexio to find prior attempts at similar analyses.

### 9.7 worklog (boundary)

**Strict separation:**

- Questio is **project-local**. It manages within-project research reasoning.
- Worklog is **cross-project**. It manages goals, capacity, scheduling across projects.
- Questio **never calls** worklog tools.
- Worklog **may optionally read** `docs/plan/questions.yml` and `docs/plan/milestones.yml` to derive goal progress. This is a one-way data flow: project → worklog, never the reverse.
- If worklog wants to track "pixecog-detection is 40% done," it can compute that from milestone completion in `milestones.yml` — it doesn't need questio tools to do so.

**Distinct responsibilities:**

| Concern | Questio | Worklog |
|---------|---------|---------|
| "What should I investigate?" | `questio_next` | — |
| "Which project should I work on?" | — | `focus()` |
| "How is H3 progressing?" | `questio_progress("H3")` | — |
| "How is pixecog overall?" | — | `get_project("pixecog")` |
| "What happened this week on H1-H7?" | `questio_report(period="week")` | — |
| "What happened this week across all projects?" | — | `agenda()` |

## 10. Docs site rendering

The docs site is where questio data becomes visible to humans — the supervisor, collaborators, and the researcher reviewing their own progress. `questio_docs_collect` generates all plan/ pages from YAML, following the same pattern as `pipeio_docs_collect`.

### 9.1 Generated pages

All pages below are **output artifacts** — auto-generated from `docs/plan/questions.yml` and `docs/plan/milestones.yml`. They should not be hand-edited (regeneration overwrites them).

#### `docs/plan/questions.md` — Research question registry

Rendered table with status indicators and cross-links:

```markdown
# Research Questions

| ID | Question | Type | Status | Milestones | Evidence | Section |
|----|----------|------|--------|------------|----------|---------|
| H1 | Do cortical delta waves precede ripple initiation? | hypothesis | not_started | 0/3 | 0 results | [results/h1](../manuscript/results/h1-delta-ripple/) |
| H2 | What are the cortical origins of ripple-driving spindles? | hypothesis | in_progress | 1/2 | 2 results | [results/h2](../manuscript/results/h2-spindle-origins/) |
```

Status uses text markers scannable in both rendered HTML and raw markdown:
- `not_started`, `in_progress`, `blocked`, `sufficient`, `confirmed`, `refuted`

#### `docs/plan/milestones.md` — Milestone tracker

Rendered table replacing the hand-maintained `Milestones.md`:

```markdown
# Milestones

## Preprocessing

| Milestone | Status | Pipeline | Depends on | Evidence |
|-----------|--------|----------|------------|----------|
| TTL artifact removal validated | complete | preprocess_ieeg | — | [result-arash-20260415-...](../log/result/result-arash-20260415-143022-123456/) |
| iEEG preprocessing stable | in_progress | preprocess_ieeg | ttl-removal-validated | |

## Event Detection
...
```

Milestones are grouped by the questions they serve (computed from `questions.yml` → `milestones` field). Milestones shared across questions appear in a "Shared prerequisites" group.

#### `docs/plan/roadmap.md` — Dependency diagram

Auto-generated mermaid graph with status-colored nodes (same structure as pixecog's current hand-maintained `roadmap.md`, but regenerated from YAML):

```markdown
# Roadmap

graph LR
    subgraph Preprocessing
        M_ttl["TTL removal<br/>● complete"]:::done
        M_ieeg["iEEG stable"]:::progress
    end
    ...
    M_ttl --> M_ieeg
    M_ieeg --> M_swr
    ...
    classDef done fill:#2d6a4f,stroke:#1b4332,color:#fff
    classDef progress fill:#e9c46a,stroke:#f4a261,color:#000
    classDef pending fill:#adb5bd,stroke:#6c757d,color:#000
```

#### `docs/plan/evidence.md` — Evidence index

Evidence grouped by question, with links to result notes and figures:

```markdown
# Evidence

## H1: Do cortical delta waves precede ripple initiation?

**Status:** not_started | **Milestones:** 0/3 complete | **Results:** 0

No evidence recorded yet. Required milestones:
- [ ] swr-detection-validated
- [ ] delta-event-detection
- [ ] delta-ripple-coupling

## H2: What are the cortical origins of ripple-driving spindles?

**Status:** in_progress | **Milestones:** 1/2 complete | **Results:** 2

| Result | Milestone | Metric | Value | Confidence | Date |
|--------|-----------|--------|-------|------------|------|
| [Spindle detection validated](../log/result/result-arash-...) | spindle-detection-validated | detection_rate | 8.1 ± 1.3/min | validated | 2026-04-12 |
| [Spindle topography preliminary](../log/result/result-arash-...) | spindle-topography-mapped | qualitative | "Clear frontal-parietal gradient" | preliminary | 2026-04-14 |
```

This page gives per-question evidence trails — combining the question overview with all linked result notes. As evidence accumulates, each question's section grows into a self-contained evidence dossier.

#### `docs/plan/index.md` — Plan overview

Landing page with high-level progress and links:

```markdown
# Research Plan

**Progress:** 3/12 milestones complete | 1/7 questions with sufficient evidence

- [Questions](questions.md) — 7 research questions (3 hypothesis groups)
- [Milestones](milestones.md) — progress tracker with evidence links
- [Roadmap](roadmap.md) — visual dependency graph
- [Evidence](evidence.md) — result index by question
- [Backlog](../log/result/) — all result notes
```

### 9.2 Result note index

The dedicated `result` note type gets its own auto-generated index at `docs/log/result/index.md` (standard notio index behavior). This provides a chronological view of all evidence, complementing the per-question grouping in `docs/plan/evidence.md`.

### 9.3 MkDocs nav integration

`questio_docs_collect` also patches the mkdocs nav (via `pipeio_mkdocs_nav_patch` or equivalent) to include the plan section:

```yaml
nav:
  - Plan:
    - plan/index.md
    - Questions: plan/questions.md
    - Milestones: plan/milestones.md
    - Roadmap: plan/roadmap.md
    - Evidence: plan/evidence.md
  - Log:
    - Results: log/result/index.md
    # ... other note types
```

### 9.4 Rendering workflow

```
docs/plan/questions.yml ──┐
                     ├──→ questio_docs_collect ──→ docs/plan/*.md ──→ mkdocs build ──→ site
docs/plan/milestones.yml ─┘                                │
                                                      ├──→ mkdocs nav patch
docs/log/result/*.md ─── (notio index) ──→ docs/log/result/index.md
```

The skill `questio-docs-refresh` wraps this: calls `questio_docs_collect`, then triggers a site rebuild if desired.

## 11. Implementation phases

### Phase 0: Data model convention (no code)
- Define `questions.yml` and `milestones.yml` YAML schemas (JSON Schema or documented convention).
- Validate with pixecog: convert existing `plan/Milestones.md` and `plan/master/03-Questions-and-Hypotheses.md` to YAML.
- Add `result` note type to pixecog's `notio.toml`.
- Create 2–3 manual result notes with structured frontmatter to test the schema.
- **Deliverable:** pixecog has `docs/plan/questions.yml`, `docs/plan/milestones.yml`, and a few `docs/log/result/` notes.

### Phase 1: Docs generation (`questio_docs_collect`)
- Implement `questio_docs_collect` MCP tool — generates `docs/plan/` pages from YAML.
- Includes questions table, milestones table, mermaid roadmap, evidence index, plan index.
- Patches mkdocs nav.
- **Deliverable:** pixecog docs site shows auto-generated plan pages.

### Phase 2: Query tools (`questio_status`, `questio_gap`)
- `questio_status` — parse YAML + scan result notes, return structured overview.
- `questio_gap` — dependency resolution, evidence gap analysis per question.
- **Deliverable:** agent can orient at session start and assess what's missing.

### Phase 3: Skills
- `questio-next` — compose status + gap + pipeio to recommend work.
- `questio-record` — guided result capture with note creation + milestone YAML update.
- `questio-report` — supervisor-ready summary.
- `questio-ready` — manuscript readiness check.
- `questio-docs-refresh` — regenerate docs.
- **Deliverable:** full agentic research cycle is possible.

### Phase 4: Agent instructions integration
- `agent_instructions()` detects `docs/plan/questions.yml` and includes a questio summary in session context.
- `questio-session-start` skill for full orientation.
- **Deliverable:** agents automatically know the research state when entering a questio-enabled project.

## 12. Open questions

1. **Milestone auto-update** — when `questio-record` creates a result note for a milestone, should the skill auto-update the milestone YAML? Or require explicit confirmation? Auto-update is convenient but risks premature status changes.

2. **`questio_next` sophistication** — the skill needs to reason about what's highest-impact. Should it just sort by dependency depth (simple), or weigh hypothesis impact, pipeline cost, and evidence gaps (complex)? Start simple, iterate?

3. **Multi-study projects** — some projects may have multiple independent studies (e.g., a methods paper + an application paper). Should `questions.yml` support study grouping, or is that a future concern?

4. **Agent instructions integration scope** — should `agent_instructions()` include full questio status (potentially verbose), or just a one-line summary with a pointer to `questio_status`?

5. **Backlog rendering** — pixecog has a `plan/backlog.md` with task checklists. Should this be YAML-ified and included in `questio_docs_collect`, or left as a hand-maintained file? Backlog items are more granular than milestones and may not need the same structured treatment.

6. **Evidence sufficiency criteria** — `questio-ready` needs to judge "enough evidence to draft." Is this purely milestone-based (all milestones complete → ready), or should it also check confidence levels (all results must be `validated` or `final`)?

7. **Inner loop guardrails** — the notebook development loop can iterate indefinitely. What's the stopping condition? Max iterations? Human review after N attempts? Quality criteria defined upfront in the milestone?

8. **Grounding depth** — `questio-ground` could be shallow (check 2–3 papers, one codio search) or deep (comprehensive literature review, full code audit). Should the depth be configurable per milestone, or should the agent judge based on the novelty of the task?

9. **Scheduled automation** — could the outer loop run as a scheduled agent (via worklog triggers)? E.g., "every morning, check questio_status for pixecog and run the next unblocked milestone." What's the right autonomy level for unattended operation?

10. **Cross-subsystem skill design** — skills like `questio-ground` and `questio-validate` compose tools from 3–4 subsystems. How detailed should the skill prompts be? Should they be prescriptive step-by-step, or give the agent latitude to adapt? Pixecog's archived skills suggest prescriptive works well.
