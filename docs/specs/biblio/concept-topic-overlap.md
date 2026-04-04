# Biblio Concept Tagging vs OpenAlex Topic Classification — Overlap Analysis

**Date:** 2026-04-03
**Status:** Analysis complete — recommendations ready for implementation

## Executive Summary

Biblio has two LLM-based classification systems (`concepts.py` and `autotag.py`) that overlap with — but are not redundant to — OpenAlex's free topic/keyword metadata. **Recommendation: complement, not replace.** Use OpenAlex topics as a free baseline layer and retain LLM extraction for project-specific enrichment that OpenAlex cannot provide.

---

## 1. OpenAlex Classification System

OpenAlex provides three classification layers per work, all assigned automatically and available at no cost via the API:

### 1a. Topics (current, ~4,500 topics)

- **Hierarchy:** 4 levels — Domain → Field → Subfield → Topic
- **Assignment:** ML model using title, abstract, journal name, and citations
- **Coverage:** Up to 3 topics per work, with confidence scores (0–1)
- **Fields returned:** `primary_topic`, `topics[]` (each with `id`, `display_name`, `score`, `subfield`, `field`, `domain`)
- **Granularity:** Moderate — "Analysis of Cardiac and Respiratory Sounds", "Artificial Intelligence in Medicine"
- **Strengths:** Hierarchical structure enables filtering at any level; consistent across all works; free

### 1b. Keywords (current, ~4,500 keywords)

- **Derived from:** Topics (not independently assigned)
- **Coverage:** Up to 5 per work, with similarity scores
- **Granularity:** Short phrases — "Cardiac Imaging", "Climate Change Impacts", "Ecosystem Resilience"
- **Strengths:** More specific than topics; good for discovery

### 1c. Concepts (deprecated, ~65,000 concepts)

- **Hierarchy:** 6 levels (tree), 19 root concepts, all Wikidata-linked
- **Assignment:** ML classifier (trained on MAG corpus), score ≥ 0.3 + ancestor propagation
- **Coverage:** ~85% of works tagged with ≥ 1 concept; multiple concepts per work
- **Status:** **Deprecated in favor of Topics.** Still returned but no longer maintained
- **Strengths:** Very granular; Wikidata IDs enable cross-system linking

---

## 2. Biblio Classification Systems

### 2a. Concept extraction (`concepts.py`)

- **Method:** LLM prompt (Claude Haiku) → structured JSON
- **Categories:** 5 fixed types — `methods`, `datasets`, `metrics`, `domains`, `techniques`
- **Input:** Title + abstract + GROBID header + existing summary (up to 2000 chars)
- **Output:** Per-citekey YAML in `bib/derivatives/concepts/{citekey}.yml`
- **Index:** Cross-paper concept index at `bib/derivatives/concepts/_index.yml` (concept → citekeys)
- **Granularity:** High — specific method names ("attention mechanism"), dataset names ("ImageNet"), metric names ("F1 score")
- **Cost:** 1 LLM call per paper (~$0.001/paper with Haiku)

### 2b. Auto-tagging (`autotag.py`)

- **Method:** Two tiers — LLM classification + reference propagation
- **LLM tier:** Constrained to controlled vocabulary (`tag_vocab.yml`), returns namespaced tags with confidence
- **Propagation tier:** Inherits tags from frequently-cited papers (threshold ≥ 3)
- **Vocabulary:** Project-specific namespaces — `domain:`, `method:`, `task:`, `corpus:` (currently ~35 values)
- **Output:** Per-citekey YAML in `bib/derivatives/autotag/{citekey}.yml`
- **Cost:** 1 LLM call per paper for LLM tier; 0 for propagation tier

---

## 3. Side-by-Side Comparison

| Dimension | OpenAlex Topics | OpenAlex Keywords | Biblio Concepts | Biblio Autotag |
|-----------|----------------|-------------------|-----------------|----------------|
| **Cost** | Free | Free | ~$0.001/paper | ~$0.001/paper |
| **Coverage** | All works in OA | All works in OA | Only local papers | Only local papers |
| **Granularity** | Moderate (4,500) | Moderate (4,500) | High (open-ended) | Low (controlled, ~35) |
| **Categories** | Domain hierarchy | Phrases | methods/datasets/metrics/domains/techniques | domain/method/task/corpus |
| **Consistency** | High (ML model) | High (derived) | Variable (LLM) | High (constrained vocab) |
| **Customizability** | None | None | Full (prompt) | Full (vocab file) |
| **Hierarchy** | 4-level tree | Flat | Flat per category | Flat, namespaced |
| **Cross-paper index** | Via API filters | Via API filters | Local `_index.yml` | Via library tags |
| **Dataset specificity** | No | No | **Yes** (named datasets) | Via `corpus:` namespace |
| **Metric specificity** | No | No | **Yes** (named metrics) | No |
| **Method specificity** | Low | Low | **High** (specific algorithms) | Medium (controlled list) |

---

## 4. Overlap Analysis

### What OpenAlex covers well
- **Broad domain classification** — the 4-level hierarchy (domain → field → subfield → topic) is richer and more consistent than either biblio system for placing a paper in a research landscape
- **Cross-corpus discovery** — topics/keywords are consistent across all 250M+ OpenAlex works, enabling discovery far beyond the local library
- **Zero-cost baseline** — topics are already fetched by biblio's OpenAlex resolver (`openalex_resolve.py` line 99)

### What biblio covers that OpenAlex cannot
- **Named datasets** — "ImageNet", "COCO", "HCP" — OpenAlex has no dataset-level tagging
- **Named metrics** — "F1 score", "top-1 accuracy", "Dice coefficient" — not in OpenAlex
- **Specific techniques** — "data augmentation", "label smoothing", "curriculum learning" — too fine-grained for OpenAlex topics
- **Project-specific vocabulary** — autotag's controlled vocab can encode project-specific concerns (e.g., `task:segmentation` for a neuroimaging project)
- **Reference-based propagation** — autotag's propagation tier is unique to biblio

### Actual redundancy
- **Domain-level tagging** — OpenAlex topics' domain/field levels overlap with both `concepts.py`'s `domains` category and `autotag.py`'s `domain:` namespace. This is the only significant overlap.
- **High-level methods** — OpenAlex topics sometimes capture method families (e.g., "Deep Learning in Image Analysis"), which partially overlaps with `concepts.py`'s `methods` and `autotag.py`'s `method:` namespace. But biblio is far more specific.

---

## 5. Recommendation: Complement

**Use OpenAlex topics as a free hierarchical baseline; retain LLM extraction for fine-grained enrichment.**

### Integration plan

#### Phase 1: Extract and store OpenAlex topics (no new API calls needed)

Biblio already fetches `topics` in the OpenAlex resolver. Store them alongside existing derivatives:

```
bib/derivatives/openalex/{citekey}.yml
  # or extend the existing openalex cache
```

Each file would contain:
```yaml
citekey: smith2024
primary_topic:
  id: T12419
  name: "Analysis of Cardiac and Respiratory Sounds"
  score: 0.9997
  domain: "Health Sciences"
  field: "Medicine"
  subfield: "Pulmonary and Respiratory Medicine"
topics:
  - {id: T12419, name: "...", score: 0.9997, ...}
  - {id: T11636, name: "...", score: 0.85, ...}
keywords:
  - {name: "Cardiac Imaging", score: 0.56}
  - {name: "Clinical Decision Support", score: 0.52}
```

#### Phase 2: Map OpenAlex topics to autotag vocabulary

Add an `openalex_mappings` section to `tag_vocab.yml`:
```yaml
openalex_mappings:
  # OpenAlex subfield ID → autotag namespace:value
  2740: domain:neuroscience  # Pulmonary and Respiratory Medicine → example
  1702: domain:ml            # Artificial Intelligence
```

This lets autotag's propagation tier use OpenAlex topics as a signal without LLM calls.

#### Phase 3: Layer the systems

1. **Layer 0 (free):** OpenAlex topics/keywords — hierarchical, broad, consistent
2. **Layer 1 (free):** Autotag propagation tier — project-specific vocabulary from citation graph
3. **Layer 2 (cheap):** Autotag LLM tier — constrained to project vocabulary
4. **Layer 3 (cheap):** Concept extraction — open-ended, fine-grained (datasets, metrics, techniques)

Run layers 0–1 for all papers automatically. Run layers 2–3 on demand or for high-priority papers.

### What NOT to do
- Do not replace `concepts.py` with OpenAlex topics — they serve different purposes
- Do not deprecate autotag — its controlled vocabulary and propagation are unique
- Do not fetch OpenAlex concepts (deprecated) — use topics/keywords only

---

## 6. Key Files

| File | Role |
|------|------|
| `packages/biblio/src/biblio/concepts.py` | LLM concept extraction (5 categories) |
| `packages/biblio/src/biblio/autotag.py` | LLM + propagation auto-tagging |
| `packages/biblio/src/biblio/tag_vocab.py` | Controlled vocabulary loader/validator |
| `bib/config/tag_vocab.yml` | Project tag vocabulary definition |
| `packages/biblio/src/biblio/openalex/openalex_resolve.py` | Already fetches `topics` from OpenAlex |
| `packages/biblio/src/biblio/openalex/openalex_client.py` | Includes `topics` in `DEFAULT_SELECT_FIELDS` |
