---
name: questio-iterate
description: "Execute-and-evaluate cycle within a human feedback loop — modify, run, assess, report, receive feedback"
tools: [questio_status, questio_gap, pipeio_flow_status, pipeio_run, pipeio_run_status, pipeio_nb_exec, pipeio_nb_read, pipeio_target_paths, pipeio_log_parse, paper_context, codio_discover, rag_query, note_create]
---

# Questio Iterate

Use this skill to execute an analysis cycle with human feedback at each step.
The agent modifies parameters or code, executes the pipeline or notebook,
assesses the output against grounded expectations, reports to the human, and
waits for direction before the next cycle.

## Inputs

- `MILESTONE` (required): the milestone being worked toward
- `FLOW` (optional): the pipeio flow. Resolved from the milestone's `flow`
  field if not provided.
- `GOAL` (optional): specific success criteria. If not provided, derive from
  grounding brief or literature.

## Workflow

### 1) Establish the goal

```
questio_gap(question_id="<parent question>")
```

Determine:
- What **milestone** are we working toward?
- What does **success** look like? Use criteria from:
  - Prior grounding brief (if `questio-ground` was run)
  - Literature values (from `paper_context`)
  - Human-stated criteria (from the current conversation)
- What **flow** will be executed?

If no success criteria exist, ask the user or recommend running
`questio-ground` first.

### 2) Ground before first iteration

If this is the first iteration (no prior grounding brief in context):

```
paper_context(citekey="<relevant citations>")
codio_discover(query="<analysis keywords>")
rag_query(query="<milestone description>")
```

Synthesize:
- **Approach:** what method to use and why
- **Expected results:** quantitative ranges from literature
- **Quality criteria:** what "good enough" looks like
- **Known pitfalls:** what to watch for

If a grounding brief already exists in the conversation, skip this step.

### 3) Pre-flight check

```
pipeio_flow_status(flow="<FLOW>")
```

Verify the flow is configured and inputs are available.

**For expensive runs** (full dataset, many subjects, long compute):
- Present what will execute: targets, estimated scope, resource requirements
- Ask for human confirmation before proceeding
- Example: "This will run sharpwaveripple for all 5 subjects (~2h). Proceed?"

**For cheap runs** (single notebook, single subject, quick test):
- Note what will execute but proceed without blocking
- Example: "Running SWR detection notebook for sub-01 (quick validation)."

### 4) Execute

Depending on scope:

**Pipeline run:**
```
pipeio_run(flow="<FLOW>")
```
Monitor with:
```
pipeio_run_status()
```

**Notebook execution:**
```
pipeio_nb_exec(flow="<FLOW>", name="<notebook>")
```

**On failure:** do not retry blindly. Enter the investigate loop:
- Reference the `questio-investigate` skill
- Diagnose the failure
- Report findings before attempting another iteration

### 5) Evaluate

Read outputs:
```
pipeio_target_paths(flow="<FLOW>")
```

Inspect key output files. For notebooks:
```
pipeio_nb_read(flow="<FLOW>", name="<notebook>")
```

Compare against grounded expectations:
- Do metrics fall within the expected range?
- Are results consistent across subjects?
- Are there anomalies that need investigation?

Create an observation note:
```
note_create(note_type="idea")
```

Frontmatter:
```yaml
---
title: "Iteration <N>: <brief description of what was run>"
tags: [observation, iterate, <flow_name>]
series: <flow_name>
---
```

Body:
- **Ran:** what was executed (flow, parameters, subjects)
- **Produced:** key metrics and outputs
- **Assessment:** how results compare to expectations
- **Recommendation:** what to do next

### 6) Report to human

Present results clearly:
- **Key metrics:** the numbers that matter, compared to expectations
- **Comparison:** how this iteration compares to prior iterations (if any)
- **Assessment:** does this meet quality criteria? Why or why not?
- **Recommendation:** one of:
  - "Results meet criteria — ready to record as evidence"
  - "Adjust X to improve Y — suggest next iteration with [specific change]"
  - "Unexpected finding — recommend investigation of Z"
  - "Diminishing returns — consider changing approach"

### 7) Human feedback gate

**Wait for human response.** Do not autonomously iterate.

Possible feedback and responses:
- **"Looks good"** → record evidence via `questio-record` skill, propose
  milestone status update
- **"Adjust X"** → modify the specified parameter/code, return to step 4
- **"Investigate Y"** → switch to `questio-investigate` skill for that issue
- **"Stop"** → record current state as observation note, summarize what was
  tried and where things stand
- **"Change approach"** → re-ground with new approach, reset iteration count

### 8) Record

**Each iteration:** observation note (step 5) — lightweight, captures what
was tried and what happened.

**On success (human confirms):** create a result note via `questio-record`
skill with full evidence schema (question, milestone, metric, value,
confidence, subjects).

**On exit (human says stop):** observation note summarizing:
- Total iterations attempted
- What was tried at each step
- Current best result
- Why iteration was stopped
- Suggested next steps if work resumes

**Milestone update:** always propose-review-confirm. Never auto-update
milestone status. Example: "Milestone `swr-detection-validated` appears to
have sufficient evidence. Should I update its status to `complete`?"

### 9) Convergence tracking

After 3+ iterations, add a trajectory summary to the report:

> "Iteration 1: detection rate 8.2/min (below expected 10-15).
> Iteration 2: detection rate 11.4/min (threshold adjusted to 3.0 SD).
> Iteration 3: detection rate 11.6/min (minimal change from iter 2).
> Trend: improving then plateauing."

If **plateauing** (< 5% change between iterations):
- Suggest changing approach rather than continuing to tune
- Recommend re-grounding with alternative methods from literature

If **degrading** (metrics getting worse):
- Stop and investigate — something is wrong
- Do not continue iterating in a degrading direction

If **improving** (steady progress toward criteria):
- Continue iterating with the human's direction
- Note the rate of improvement to estimate remaining iterations

## Hard rules

- Never iterate without human feedback between cycles. The agent proposes,
  the human directs.
- Never auto-update milestone status. Always propose-review-confirm.
- Always create an observation note for each iteration, even failed ones.
  The trail of what was tried is valuable.
- If a run fails, enter investigate mode — do not retry with the same
  parameters.
- For expensive runs, always get human confirmation before executing.
- After 3 iterations of plateauing or degrading results, recommend changing
  approach rather than continuing to tune.
- Always compare against grounded expectations. "The number is 12.3" is not
  an assessment — "12.3/min is within the expected 10-15/min range from
  @AuthorYear2024" is.
- Do not skip the pre-flight check. Running against a misconfigured flow
  wastes time.
- Record the iteration number in each observation note title for easy
  sequencing.
