# Slide draft — LSM Future Skills 2026

Derived from `draft.md` (the raw talking draft). This is the pruned plan.

- **On slide** = what the audience sees: title, a few short bullets, the visual.
  Keep it sparse. No paragraphs.
- **Speaker** = a short point list to talk from. The stories live here, not on
  the slide.
- **Footer** = tool logos + citation, pinned bottom-left (`.tinyfoot`).
- Visuals: each section has its own concrete schematic as the hero (meal-prep,
  code-ground, lit-ground, snakemake-dag, explore-loop, mcp-skills, goals). The
  small build-up rail is retired; the full stack diagram gets ONE big animated
  spotlight recap on "what carried over" (each component lights up in flow).
- Global `incremental: true` — bullets and `.fragment` blocks reveal in turn.

Total: 6 slides, ~11 min. (Entry numbers below are approximate labels.)

**Slide titles are the stack components, each with a takeaway subtitle:**
1. the mess (Desk Entropy comic + one line; story in notes) · 2. **Data specification (BIDS)** (3 meal-prep photos; robot chopping source→raw and cooking raw→derivative, SPECS doc into head, curved arrow under each; staged reveal; ends on a question bubble "how can we get derivatives and results reliably?") · 3. **Pipelines (Snakemake)** (reconstructed, and never run by hand again; three columns — "Let me do that by hand…" comic that animates setup→frustration strip, workflow-dag, snakemake-workflow-rules; DataLad `local_wf` versioning figure bottom-left; story + pointers in notes) · 4. **Exploration, grounded (Marimo)** (Notebooks + Code&Bibliography merged into one `explore-ground.svg`: left 1/3 = minimal Marimo notebook, you+agent live; middle = MCP·skills channel; right 2/3 = code (libs + search-first skill → codio_get) and literature (PDFs → Docling → searchable corpus → rag_query); larger Marimo logo bottom-left; explore-loop/code-ground/lit-ground retired to disk) · 5. **Publication (Quarto)** (staged flow: `results-folder.svg` → agent `robot-assemble.svg` (fed SPECS, assembles one source) → `docs-stack.svg` (slides·manuscript·report, same live `4.2` everywhere); the folder is the prior slide's deliverables, the identical `4.2` carries the live-sync mechanism; blue bubble on the capabilities shift) · 7. **what carried over** (combined finale: animated spotlight stack recap medium-left; below the stack: reproducible · adaptable · transparent + "human remains responsible for judgment and validation"; right column = workshop QR (larger, text beside) top, "still brittle" limits bottom (from the flyer: structure outpaces upkeep · retrieval needs checking)).

---

## 1 — the mess  *(~90s · PhD comic on right)*

**On slide:**
- inherited a dataset with no convention
- weeks hand-building tools just to load it
- leave, come back, cannot reorient
- *never doing this by hand again*
- **boxed (fragment):** describe the problem well, and AI surveys for the best existing tools — discovery, not typing
- *visual: PhD Comics "Desk Entropy"* · **footer:** comic credit

**Speaker (merges origin + sprawl + entropy + the AI-discovery pivot):**
- PhD dataset from a departing postdoc, no naming convention, changing every session
- hand-built a DB manager, batch runner, a tool that emailed me when batches finished (PyRatECoG, if asked)
- a personal lab-ops stack before any science; every new analysis meant more
- months later I could not reorient; the conventions lived only in my head
- comic: projects trend to disorder, tidying is temporary; an agent adds entropy faster without specs
- the pivot: describe the problem well, AI surveys for the best existing tools, stop reinventing

## 2 — grounding: data (BIDS)  *(~90s · meal-prep photo · footer BIDS Starter Kit)*

**On slide:**
- directory is the API; filename is the metadata — **S = Specification**
- **modular**: source → raw → derivatives, separate folders
- *visual (hero): the meal-prep photos (source = ingredients, raw = prepped, derivative = the dish)*

**Speaker (one BIDS slide, folder-compare + modularize folded in):**
- BIDS = community standard; self-describing, so I stop writing bespoke loaders
- filename carries the metadata (subject/session/datatype); S = Specification keeps the agent inside your rules
- modular: source/raw/derivatives kept apart; raw stays pristine; derivatives regenerable
- that separation is what let the agent reconstruct provenance later
- meal-prep image adapted from the BIDS Starter Kit (DOI 10.5281/zenodo.5872274, CC-BY)

## 3 — grounding: code and literature  *(~2 min · split: code schematic left, literature schematic right · footer Docling/OpenAlex/GROBID)*

**On slide:**
- left **code** · ground in your libraries — *schematic: from-scratch naive vs relevant libraries + your verified code*
- right **literature** · ground in your papers — *schematic: PDFs → Docling → corpus → agent (RAG)*

**Speaker:**
- code: from scratch = naive, reinvents, fragile; grounded = libraries relevant to your analysis + your own verified code; a skill says search first, write only what is missing
- literature: Docling → structured text + cropped figures → project corpus (50–1000 papers) → agent retrieves (RAG); from prepping slides to driving analysis

## 4 — the moment it earned my trust  *(~2.5 min · centerpiece · trust + pipeline merged · DAG right · footer Snakemake/DataLad)*

**On slide (sequential reveal, left column; DAG on right):**
1. a processing chain built by several people; run order **forgotten**
2. the agent reconstructed it and **numerically verified** the chain
3. I locked it into a **Snakemake** rule *(code block)*
4. **DataLad + git** version it, roll back

**Speaker:**
- we needed to change one step; provenance was gone
- gave the agent final files, some intermediates, loose scripts; it inferred script → file → dependency; numerically verified by re-running vs intermediates
- the colleague who wrote it was surprised; a chat tab cannot do this
- then locked in: a Snakemake rule (wildcard {s} generalizes; Snakemake infers the DAG from filenames, reruns only what is stale)
- DataLad + git version data and code; rebuilt a years-old analysis into a reproducible repo, published with the paper
- syntax after Köster: snakemake.readthedocs.io, slides.com/johanneskoester

## 6 — exploration needs a shared surface  *(~90s · explore-loop · footer Marimo)*

**On slide:**
- *visual (hero): turn-based loop (minutes) vs pair on Marimo (seconds)*
- caption: rebuilding a notebook per prompt is too slow; Marimo = live joint editing

**Speaker:**
- Jupyter reruns everything for one change; turn-based sync still slow
- Marimo = reactive notebook, joint live editing, not turn-taking
- the loop: explore in Marimo, promote to a Snakemake rule, save the routine as a skill

## 7 — reporting, with a hand on the brake  *(~75s · text only · footer Quarto)*

**On slide:**
- **Quarto**: reports and slides, fast
- the risk: it over-generates
- so I prune hard

**Speaker:**
- failure mode is not hallucination, it is volume and emphasis
- every detail can be true and it still says too much, or buries the point
- I use this daily and still keep a hand on the brake

## 8 — what I still do not fully trust  *(~75s · text only)*

**On slide:**
- verification: I re-run key analyses by hand
- report volume: judgment stays with me
- single-author fragility

**Speaker:**
- don't apologize, don't deflect; naming this earns the room
- the value is in the conventions, which outlive any one tool

## 9 — what carried over  *(~75s · FULL-BLEED 16:9 animated spotlight recap, no title)*

**On slide:**
- *visual (hero, animated): the full stack; each click lights one component, dims the rest, in a bottom-up flow (BIDS → DataLad → code → bibliography → Marimo → Snakemake → Quarto → the agent, shown as the robot mascot on top), last click lights all*

**Speaker (name each piece as it lights):**
- every hand-built thing from slide 1 now has an agent-legible standard
- BIDS (data) · DataLad + git (versioning) · code libraries · bibliography · Marimo (explore) · Snakemake (pipelines) · Quarto (publish)
- the agent (robot mascot) on top; you need the conventions, not any one package (projio deliberately unnamed on-slide)

## 10 — the agent's two handles: MCP and skills  *(~50s · mcp-skills)*

**On slide:**
- *visual: MCP tools (rag_query, codio_get, pipeio_run) + skills (explore, promote, report)*

**Speaker:**
- MCP tools = what the agent can call (scoped, permissioned); skills = saved routines it follows
- permissions decide which tools it sees; skills capture how I like the work done

## 11 — why it is worth the discipline  *(~45s · goals · footer Köster)*

**On slide:**
- *visual: reproducible · adaptable · transparent → sustainable*

**Speaker:**
- the payoff of specs + grounding; sustainable science that outlives the project and the person
- the open-science goal; the stack is only how I get there

## 12 — the agentic research workflow  *(~60s · workshop close · footer logos)*

**On slide:**
- 4-day hands-on workshop · 5–8 Oct 2026 · LMU Martinsried
- day table (explore / code / organize / build) using the same stack as the talk
- LSF 19877 · 3 ECTS · English · A.Shahidi@bio.lmu.de

**Speaker:**
- same tools you just saw; we start from the payoff (Day 1 use it) and work back to building it
- 3 ECTS, English, LSF course 19877; questions to my email
- stop, open for discussion
- (replaces the earlier starter-repo "try it" slide; content from the workshop index.qmd)
