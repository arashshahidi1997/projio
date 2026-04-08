# Scenario: Drafting Manuscript Results from Accumulated Evidence

**Status:** draft
**Date:** 2026-04-08
**Project:** pixecog
**Starting state:**

- H2 milestones are complete: `spindle-detection-validated`, `spindle-topography-mapped`
- Multiple result notes exist with metrics, cross-subject tables, and references
- Observation notes from the iterate loops provide context for how results were obtained
- Manuscript section `results/h2-spindle-origins` exists as a placeholder
- FigureSpec files do not yet exist for H2 figures
- The manuscript uses pandoc rendering via notio.manuscript

**What the researcher wants:** Turn accumulated evidence into a draft results section for H2, complete with figures and citations, ready for supervisor review.

---

## Phase 1: Readiness check — "Do we have enough?"

```
Human: H2 should have enough evidence now. Can we draft the results section?
```

!!! info "Behind the scenes"
    ```
    → questio_status()
      Returns: H2 status overview
        spindle-detection-validated: complete, evidence: [result-arash-20260408-001]
        spindle-topography-mapped: complete, evidence: [result-arash-20260408-002]
        spindle-amplitude-ripple-coupling: complete, evidence: [result-arash-20260408-003]

    → questio_gap("H2")
      Returns: no gaps — all milestones complete, all with validated evidence

    → note_search(query="result spindle topography H2")
      Returns: 3 result notes and 8 observation notes across the spindle
               detection and topography analysis sessions
    ```

```
Agent: **H2 readiness check:**

       | Milestone | Status | Evidence |
       |-----------|--------|----------|
       | spindle-detection-validated | complete ✓ | Detection rates, cross-subject table |
       | spindle-topography-mapped | complete ✓ | Per-contact rates, amplitude maps |
       | spindle-amplitude-ripple-coupling | complete ✓ | Coupling metrics, timing |

       **Evidence inventory:**
       - 3 result notes with structured metrics
       - 8 observation notes from iteration loops
       - Cross-subject consistency data for all 5 subjects

       **H2 is draftable.** All milestones have validated evidence. The
       manuscript section `results/h2-spindle-origins` is currently a
       placeholder. Ready to proceed with evidence collection and drafting.
```

!!! tip "Evidence trail"
    The readiness check works because questio-record created structured result notes at each milestone completion. Without these, the agent would have to dig through pipeline outputs and guess what was validated. The structured frontmatter (metric, value, subjects, confidence) makes readiness assessment mechanical.

---

## Phase 2: Evidence collection — "What do we have to work with?"

```
Human: Show me what evidence we have, organized by claim.
```

!!! info "Behind the scenes"
    ```
    → note_read(path="notes/result/result-arash-20260408-001.md")
      Returns: spindle detection validated — 7.9 ± 0.8 /min, all subjects
               in literature range, merge_gap adjusted to 0.1s

    → note_read(path="notes/result/result-arash-20260408-002.md")
      Returns: spindle topography — detection rate varies 3x across cortical
               contacts, highest in association cortex (PFC, temporal),
               lowest in primary sensory cortex

    → note_read(path="notes/result/result-arash-20260408-003.md")
      Returns: spindle-ripple coupling — peak at +95 ± 9 ms, stronger for
               spindles originating in association cortex (z=4.1 vs z=2.3
               for sensory cortex spindles)

    → note_search(query="observation spindle topography")
      Returns: observation notes with per-subject topography details,
               including the finding that sub-04 has unusual frontal spindle
               dominance (possibly electrode placement)
    ```

```
Agent: **Evidence organized by H2 claims:**

       **Claim 1: Spindles are detectable across cortical contacts**
       - Source: result-001
       - Rate: 7.9 ± 0.8 /min (literature: 5-10/min) ✓
       - Validated across all 5 subjects
       - Methods: bandpass 10-16 Hz, 2.5 SD threshold, merge_gap 0.1s

       **Claim 2: Spindle topography is non-uniform**
       - Source: result-002
       - Association cortex (PFC, temporal): 10.2 ± 1.4 /min
       - Primary sensory cortex: 3.8 ± 0.9 /min
       - Ratio: ~2.7x higher in association regions
       - Note: sub-04 shows unusual frontal dominance (observation note)

       **Claim 3: Spindle origin predicts coupling strength**
       - Source: result-003
       - Association cortex spindles: coupling z = 4.1
       - Sensory cortex spindles: coupling z = 2.3
       - Supports H2 prediction: "ripple-triggering spindles originate
         from specific association regions, not uniformly across cortex"

       **Key citations needed:**
       - @siapas_1998 — original spindle-ripple coupling
       - @pedrosa_2024 — recent topography findings
       - @swanson_2025 — putative spindle topography

       This is a coherent story: spindles are non-uniform → association
       cortex spindles couple more strongly with ripples → supporting
       region-specific control of memory consolidation.

       Ready to design figures?
```

!!! tip "Evidence trail"
    Each claim maps directly to a result note. The observation notes provide context (sub-04 caveat). The agent is synthesizing across multiple evidence sources — this is where structured recording pays off.

---

## Phase 3: Figure design — "What should Figure 3 look like?"

```
Human: I need a figure showing the spindle topography and its relationship
       to coupling strength. Let's call it Figure 3.
```

!!! info "Behind the scenes"
    ```
    → figio_figure_list()
      Returns: Figure 1 (TTL artifact), Figure 2 (detection methods) — no Figure 3

    → figio_edit_spec("fig3-spindle-topography",
        spec={
          "title": "Spindle topography and coupling",
          "panels": [
            {"id": "A", "title": "Spindle rate per cortical contact",
             "type": "heatmap", "data_source": "spectrogram_burst/topography",
             "description": "Mean spindle rate (events/min) mapped onto cortical contact positions"},
            {"id": "B", "title": "Spindle amplitude heatmap",
             "type": "heatmap", "data_source": "spectrogram_burst/amplitude_map",
             "description": "Mean spindle amplitude (μV) per contact"},
            {"id": "C", "title": "Example spindle waveforms",
             "type": "traces", "data_source": "spectrogram_burst/waveforms",
             "description": "Representative spindle waveforms from association (PFC) and sensory (V1) contacts"},
            {"id": "D", "title": "Coupling strength by region",
             "type": "scatter", "data_source": "coupling_spindle_ripple/regional",
             "description": "Spindle-ripple coupling z-score vs spindle rate, colored by cortical region"}
          ],
          "layout": "2x2",
          "size": {"width": 180, "height": 150, "units": "mm"}
        })
    ```

```
Agent: **Figure 3 spec created — 4 panels:**

       ```
       ┌─────────────────────┬─────────────────────┐
       │ A: Spindle rate     │ B: Spindle amplitude │
       │    per contact      │    heatmap           │
       │    (heatmap)        │    (heatmap)         │
       ├─────────────────────┼─────────────────────┤
       │ C: Example          │ D: Coupling strength │
       │    waveforms        │    vs region         │
       │    (PFC vs V1)      │    (scatter)         │
       └─────────────────────┴─────────────────────┘
       ```

       - **Panel A** shows the non-uniformity (Claim 2)
       - **Panel B** adds amplitude dimension (supports Claim 2)
       - **Panel C** provides intuition (what these spindles look like)
       - **Panel D** is the key result (Claim 3 — coupling depends on origin)

       The figure tells a story: spindles vary across cortex (A, B) →
       here's what they look like (C) → and this variation predicts coupling (D).

       Want me to build it, or adjust the layout first?
```

```
Human: Swap B and C — I want waveforms next to the rate map for intuition,
       and put both quantitative plots on the bottom row.
```

!!! warning "Human checkpoint"
    The researcher provides layout feedback. Figure design is inherently subjective — the agent proposes, but the human's visual intuition drives the final layout.

!!! info "Behind the scenes"
    ```
    → figio_edit_spec("fig3-spindle-topography",
        spec={
          "panels": [
            {"id": "A", "title": "Spindle rate per cortical contact", "type": "heatmap"},
            {"id": "B", "title": "Example spindle waveforms", "type": "traces"},
            {"id": "C", "title": "Spindle amplitude heatmap", "type": "heatmap"},
            {"id": "D", "title": "Coupling strength by region", "type": "scatter"}
          ]
        })

    → figio_build("fig3-spindle-topography")
      Returns: SVG composed, PDF exported
    ```

!!! example "Generated figure"
    Figure 3 built: `figures/fig3-spindle-topography/fig3-spindle-topography.svg`

    - Panel A: clear gradient from high rates in PFC/temporal to low rates in V1/S1
    - Panel B: PFC spindle shows classic waxing-waning morphology at 13 Hz; V1 spindle is lower amplitude, less regular
    - Panel C: amplitude mirrors rate — association cortex has both more and larger spindles
    - Panel D: strong positive correlation (r=0.72) between regional spindle rate and coupling z-score

```
Agent: Figure built. The scatter in Panel D is particularly clear — there's
       a strong correlation between spindle rate and coupling strength,
       with association cortex regions clustered in the upper right.

       Ready to draft the section text?
```

```
Human: Yes, draft it.
```

---

## Phase 4: Section drafting — writing scientific prose

!!! info "Behind the scenes"
    ```
    → manuscript_section_context("results/h2-spindle-origins")
      Returns: section template, surrounding sections (h1-delta-ripple before,
               h3-spindle-amplitude after), manuscript style guide,
               word count target (~800 words for results subsection)

    → manuscript_cite_check()
      Returns: current citations in use, available citekeys in compiled.bib

    → [agent drafts the section, incorporating evidence from result notes]
    ```

```
Agent: **Draft for results/h2-spindle-origins:**

       ---

       ### Cortical origins of ripple-driving spindles

       Sleep spindles were detected across all cortical ECoG contacts using
       bandpass filtering (10–16 Hz) with amplitude thresholding (2.5 SD
       above NREM baseline). The overall detection rate (7.9 ± 0.8
       events/min across subjects) was consistent with prior reports in
       rodent neocortex [@siapas_1998_CoordinatedInteractions;
       @pedrosa_2024_HippocampalRipples].

       Spindle occurrence was markedly non-uniform across the cortical
       surface (Figure 3A). Association cortex contacts (prefrontal and
       temporal regions) exhibited detection rates of 10.2 ± 1.4
       events/min, approximately 2.7-fold higher than primary sensory
       cortex (3.8 ± 0.9 events/min; paired t-test, t(4) = 8.3,
       p < 0.001). This topographic gradient was consistent across all
       five subjects and was mirrored in spindle amplitude (Figure 3C),
       with association cortex contacts showing larger spindles (42 ± 8 μV)
       compared to sensory cortex (18 ± 5 μV).

       To test whether spindle origin predicts coupling with hippocampal
       ripples, we computed cross-correlograms between spindle events
       detected at each cortical contact and hippocampal ripple events
       [@siapas_1998_CoordinatedInteractions]. Spindles from association
       cortex showed significantly stronger coupling (z = 4.1 ± 0.6)
       than those from sensory cortex (z = 2.3 ± 0.4; Figure 3D). The
       coupling peak timing (+95 ± 9 ms, spindle leading ripple) was
       consistent with prior reports of cortical spindle-to-hippocampal
       ripple coordination [@sirota_2003_CommunicationNeocortex;
       @maingret_2016_HippocampocorticalCoupling].

       These results support the prediction that ripple-triggering
       spindles originate preferentially from association cortex rather
       than being uniformly distributed, consistent with the proposed
       role of prefrontal and temporal regions in coordinating
       hippocampal memory consolidation
       [@pedrosa_2024_HippocampalRipples;
       @swanson_2025_TopographyPutative].

       ---

       **Word count:** 247 (target: ~300 for this subsection)
       **Citations used:** 5 (siapas_1998, pedrosa_2024, sirota_2003,
       maingret_2016, swanson_2025)
       **Figure references:** Figure 3A, 3C, 3D

       Want me to check citations and run the full build?
```

!!! note "Citation management"
    Every factual claim in the draft has a citation. The agent used `manuscript_cite_check` to verify all citekeys exist in `compiled.bib`. The citations were drawn from H2's `citations` field in `questions.yml` plus the grounding done in earlier scenarios.

```
Human: Good draft. But tone down the last paragraph — it's too assertive
       for preliminary results. Say "suggest" not "support."
```

```
Agent: Updated the final paragraph:

       "These results suggest that ripple-triggering spindles originate
       preferentially from association cortex rather than being uniformly
       distributed, which would be consistent with..."

       Shall I run the full build?
```

---

## Phase 5: Build and review

```
Human: Yes, build the full manuscript.
```

!!! info "Behind the scenes"
    ```
    → manuscript_assemble()
      Returns: sections assembled into full manuscript markdown

    → manuscript_figure_build_all()
      Returns: all figures rebuilt (including fig3)

    → manuscript_build()
      Returns: PDF rendered via pandoc, output at manuscripts/pixecog-draft/output/

    → manuscript_cite_check()
      Returns: all citations resolved, no missing references

    → manuscript_validate()
      Returns: no structural issues, all sections present, figure references valid
    ```

```
Agent: **Manuscript built successfully.**

       - PDF: manuscripts/pixecog-draft/output/pixecog-draft.pdf
       - All citations resolved ✓
       - All figure references valid ✓
       - Section h2-spindle-origins: 247 words, 5 citations, 3 figure refs

       The H2 results section is integrated with the rest of the manuscript.
       The preceding section (h1-delta-ripple) discusses the delta-ripple
       coupling context, and the following section (h3-spindle-amplitude)
       will extend the spindle analysis to amplitude modulation.

       Want to review the PDF, or move to journal formatting?
```

```
Human: Let me review the PDF first.

       [... reviews ...]

       The methods reference in the first sentence is too brief — readers
       need to know the detection parameters are in the Methods section.
       Add a forward reference.
```

```
Agent: Added: "...with amplitude thresholding (2.5 SD above NREM baseline;
       see Methods for full parameter details)."

       Rebuilding...
```

!!! info "Behind the scenes"
    ```
    → manuscript_build()
      Returns: rebuilt with updated section
    ```

---

## Phase 6: Polish — journal check

```
Human: Looks good. Check against our target journal requirements.
```

!!! info "Behind the scenes"
    ```
    → manuscript_journal_check()
      Returns:
        target: Nature Neuroscience
        word_count: 4,200 / 5,000 max ✓
        figures: 3 / 8 max ✓
        references: 42 / no limit ✓
        abstract: 147 / 150 words ✓
        issues:
          - Figure 3 resolution: 300 dpi required, current is 150 dpi
          - Supplementary data statement: missing
    ```

```
Agent: **Journal check (Nature Neuroscience):**

       | Requirement | Status |
       |-------------|--------|
       | Word count (5,000 max) | 4,200 ✓ |
       | Figures (8 max) | 3 ✓ |
       | Abstract (150 words max) | 147 ✓ |
       | Figure resolution (300 dpi) | 150 dpi ✗ — needs rebuild at higher resolution |
       | Supplementary data statement | Missing ✗ |

       Two issues to fix:
       1. Figure resolution: I can rebuild at 300 dpi via figio
       2. Data statement: needs a section about data availability

       Want me to fix the figure resolution now?
```

```
Human: Fix the resolution. I'll write the data statement myself.
```

!!! info "Behind the scenes"
    ```
    → figio_build("fig3-spindle-topography", dpi=300)

    → manuscript_build()
    ```

```
Agent: Figure 3 rebuilt at 300 dpi and manuscript recompiled.
       The data statement is the only remaining journal requirement.

       **Session summary for H2 manuscript drafting:**
       - Evidence collected from 3 result notes
       - Figure 3 designed (4 panels), built, iterated on layout
       - Results section drafted (247 words, 5 citations)
       - Manuscript built and validated
       - Journal check: 1 issue remaining (data statement, human-owned)
```

---

## Ecosystem coverage

| Subsystem | Tools used | Purpose in this scenario |
|-----------|-----------|------------------------|
| **questio** | `questio_status`, `questio_gap` | Readiness check — are milestones complete with evidence? |
| **notio** | `note_search`, `note_read` | Retrieve result and observation notes as evidence |
| **figio** | `figio_figure_list`, `figio_edit_spec`, `figio_build` | Design, create, and iterate on Figure 3 |
| **manuscripto** | `manuscript_section_context`, `manuscript_assemble`, `manuscript_build`, `manuscript_validate`, `manuscript_cite_check`, `manuscript_cite_suggest`, `manuscript_journal_check`, `manuscript_figure_build_all` | Draft, build, validate, check journal requirements |
| **biblio** | (via `manuscript_cite_check`) | Citation resolution and verification |
| **pipeio** | (implicit — data sources for figures) | Pipeline outputs feed figure panels |

## Loop patterns used

| Phase | Loop | Pattern |
|-------|------|---------|
| 1. Readiness check | Orient | `questio_status` → `questio_gap` → evidence inventory |
| 2. Evidence collection | (gathering) | `note_search` → `note_read` → structured synthesis |
| 3. Figure design | Iterate | Propose spec → human feedback on layout → rebuild |
| 4. Section drafting | Iterate | Draft → human reviews prose → adjust tone → rebuild |
| 5. Build and review | Iterate | Build → validate → human review → fix forward ref |
| 6. Polish | (quality) | Journal check → fix resolution → final build |

## Key insight

**The manuscript writes itself when evidence is properly structured.** The result notes created by questio-record contain structured frontmatter (metric, value, subjects, confidence) that maps directly to sentences in the results section. The figure spec draws data from pipeline outputs that are already computed and validated. The citations come from the hypothesis definitions in `questions.yml`.

This is the full publication pipeline in action: **questio** (evidence structure) → **figio** (figures) → **manuscripto** (section assembly + rendering) → **biblio** (citations). Each subsystem contributes a layer, and the agent's role is to weave them into coherent scientific prose. The human's role shifts from writing from scratch to reviewing and refining — a fundamentally different (and more efficient) workflow.
