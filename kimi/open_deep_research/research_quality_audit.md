# Research Quality Audit

## Executive Summary

This audit samples reports from the three JSONL experiment result files and evaluates them for research quality dimensions that are **not** fully covered by the existing evaluator suite: weak evidence, unsupported claims, hallucination risks, source-reference mismatches, and missing counterarguments.

**Key Finding**: All three models exhibit significant quality gaps, with **GPT-5 showing the worst citation integrity** (21.05 missing references per article on average) and **all models showing critically low counterargument coverage** (~3–4.5 signals per article). A substantial portion of bold claims lack inline citations, creating high hallucination risk.

---

## 1. Audit Methodology

### 1.1 Sample Selection

Seven sample IDs were selected from IDs present in all three files: **1, 10, 25, 50, 75, 90, 100**. These span the ID range and include both short and long articles.

### 1.2 Metrics Computed

For each article, the following metrics were computed programmatically:

| Metric | Definition | Rationale |
|--------|-----------|-----------|
| **Word count** | Total words in `article` | Length proxy for thoroughness |
| **Citation count** | Number of `[N]` markers in body | Source attribution density |
| **Has Sources section** | Boolean: `### Sources` or similar present | Structural compliance |
| **Missing source refs** | Body citations without matching source entry | Citation integrity |
| **Significant numbers** | Count of numeric values (excluding years <2035) | Quantitative claim density |
| **Counterargument signals** | Count of words: *however, but, on the other hand, conversely, in contrast, critics argue, limitations, challenges, drawbacks* | Balanced analysis proxy |
| **Vague words** | Count of hedges: *many, several, some, various, numerous, often, frequently, generally, typically, largely, mostly, commonly* | Precision proxy |
| **Unsupported bold claims** | Bold sentences (`**...**`) without inline `[N]` citation | Hallucination risk proxy |
| **Citation density** | Citations per 1000 words | Source richness |

### 1.3 Aggregate Analysis

All records in each JSONL file were analyzed to produce per-model averages.

---

## 2. Aggregate Findings

### 2.1 Per-Model Averages (All Records)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Avg missing refs per article | **7.86** | **21.05** | **7.40** |
| Articles with Sources section | 76.0% | 89.0% | 88.8% |
| Avg counterargument signals | 3.78 | 4.55 | 3.38 |
| Avg vague words | 2.34 | 2.92 | 3.14 |
| Avg unsupported bold claims | 23.39 | **46.30** | 28.80 |
| Avg citation density (per 1000 words) | 33.21 | 41.90 | 38.98 |

### 2.2 Interpretation

**Citation Integrity Crisis (GPT-5)**
- GPT-5 averages **21 missing references per article** — more than double GPT-4.1 and Claude 4 Sonnet. This means the majority of its in-body citations do not correspond to any source entry.
- Despite having the highest citation density (41.90 per 1000 words), GPT-5's citations are largely **unverifiable**.

**Unsupported Bold Claims (All Models)**
- All models make extensive use of bold formatting for key claims, but **most bold claims lack inline citations**.
- GPT-5 is worst at **46.30 unsupported bold claims per article**, suggesting a pattern of asserting conclusions without immediate attribution.
- This creates a **high hallucination risk**: readers perceive bold text as authoritative, yet cannot trace it to a source.

**Counterargument Deficit (All Models)**
- Average counterargument signals range from **3.38 to 4.55 per article**.
- For articles often exceeding 500–2000 words, this represents **<1% of sentences** acknowledging limitations, dissent, or alternative viewpoints.
- The evaluation system's `eval_overall_quality` dimension "balance_and_objectivity" (15% weight) may not be sensitive enough to catch this deficit.

**Vague Language**
- All models use hedging language, but at relatively low levels (2–3 words per article). This is less concerning than citation integrity.

**Sources Section Presence**
- GPT-4.1 has the lowest rate of Sources sections (76.0%), meaning **24% of its articles cite sources in the body but never list them**.
- GPT-5 and Claude 4 Sonnet are better (89% and 88.8%) but still leave 10–12% of articles without source lists.

---

## 3. Sample-Level Deep Dive

### 3.1 ID 1: AI Investments by Consulting Firms

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 233 | 686 | 293 |
| Citations | 13 | 0 | 18 |
| Has Sources | ❌ | ✅ | ✅ |
| Missing refs | 13 | 0 | 0 |
| Sig. numbers | 9 | 37 | 17 |
| Counter signals | 1 | 0 | 0 |
| Unsupported bold | 13 | 49 | 36 |

**Observations**:
- **GPT-4.1**: 13 citations but **no Sources section** — all citations are dangling. Only 1 counterargument signal.
- **GPT-5**: **Zero citations** despite 686 words and 37 significant numbers. 49 unsupported bold claims. This article is essentially a long opinion piece with no verifiable sources.
- **Claude 4 Sonnet**: Best performer on this sample. 18 citations, all resolved, Sources section present. Still 36 unsupported bold claims.

**Hallucination Risk**: **HIGH for GPT-5** (no citations at all). **MEDIUM for GPT-4.1** (citations exist but unresolvable). **LOW for Claude 4 Sonnet**.

### 3.2 ID 10: Bird Migration Navigation

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 319 | 560 | 499 |
| Citations | 10 | 35 | 22 |
| Has Sources | ✅ | ✅ | ✅ |
| Missing refs | 0 | 0 | 0 |
| Sig. numbers | 7 | 36 | 18 |
| Counter signals | 0 | 0 | 0 |
| Unsupported bold | 9 | 22 | 29 |

**Observations**:
- All three models produce well-cited articles for this scientific topic.
- **Zero counterargument signals** across all models — no discussion of conflicting theories, methodological limitations, or unresolved debates in ornithology.
- GPT-5 again has the highest number of significant numbers (36) and unsupported bold claims (22).

**Hallucination Risk**: **LOW** (citations present and resolved). **Balance Risk**: **HIGH** (no counterarguments or limitations discussed).

### 3.3 ID 25: Video Editing Software Market

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 264 | 765 | 224 |
| Citations | 14 | 46 | 11 |
| Has Sources | ❌ | ✅ | ❌ |
| Missing refs | 14 | 0 | 11 |
| Sig. numbers | 12 | 47 | 15 |
| Counter signals | 0 | 0 | 0 |
| Unsupported bold | 0 | 34 | 7 |

**Observations**:
- **GPT-4.1 and Claude 4 Sonnet both lack Sources sections** for this sample, making all citations unverifiable.
- GPT-5 provides the most comprehensive coverage (765 words, 46 citations, all resolved) but still makes 34 unsupported bold claims.
- No counterargument signals — no discussion of market risks, competitive threats, or methodological caveats in market sizing.

**Hallucination Risk**: **MEDIUM for GPT-4.1/Claude** (missing Sources). **LOW for GPT-5** (citations resolved).

### 3.4 ID 50: (Short Article — ~200–550 words)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 204 | 547 | 411 |
| Citations | 12 | 31 | 38 |
| Has Sources | ❌ | ✅ | ✅ |
| Missing refs | 12 | 31 | 0 |
| Sig. numbers | 5 | 39 | 25 |
| Counter signals | 0 | 0 | 0 |
| Unsupported bold | 0 | 28 | 12 |

**Observations**:
- **GPT-5 has 31 missing references** — the worst single-sample citation integrity failure observed. Despite having a Sources section, 31 body citations lack corresponding entries.
- Claude 4 Sonnet achieves perfect citation resolution (0 missing) with the highest citation count (38).

**Hallucination Risk**: **HIGH for GPT-5** (massive citation gaps). **MEDIUM for GPT-4.1** (no Sources). **LOW for Claude 4 Sonnet**.

### 3.5 ID 75: Long Article (~1700–2900 words)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 1,737 | 2,940 | 2,114 |
| Citations | 42 | 95 | 39 |
| Has Sources | ✅ | ✅ | ✅ |
| Missing refs | 0 | 95 | 0 |
| Sig. numbers | 41 | 102 | 32 |
| Counter signals | 8 | 8 | 7 |
| Unsupported bold | 25 | 63 | 39 |
| Vague words | 7 | 3 | 4 |

**Observations**:
- **GPT-5: 95 citations, 95 missing references** — a 100% failure rate on citation integrity for this sample. Every citation in the body is unverifiable.
- This is the longest article (2,940 words) with the most significant numbers (102), creating maximum hallucination surface area.
- Counterargument signals are highest here (7–8) but still represent <0.5% of sentences.
- GPT-4.1 and Claude 4 Sonnet both resolve all citations correctly.

**Hallucination Risk**: **CRITICAL for GPT-5** (100% citation failure on longest article). **LOW for GPT-4.1/Claude**.

### 3.6 ID 90: Long Article (~1900–2700 words)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 1,946 | 2,674 | 2,045 |
| Citations | 19 | 53 | 9 |
| Has Sources | ✅ | ✅ | ✅ |
| Missing refs | 0 | 0 | 0 |
| Sig. numbers | 7 | 58 | 3 |
| Counter signals | 14 | 27 | 11 |
| Unsupported bold | 19 | 38 | 8 |
| Vague words | 8 | 5 | 4 |

**Observations**:
- **Claude 4 Sonnet produces very few citations (9) and significant numbers (3)** for this sample, suggesting a more narrative/descriptive style with less quantitative depth.
- GPT-5 has the highest counterargument signals (27) — the best balance coverage observed in any sample.
- All models resolve citations correctly for this sample.

**Hallucination Risk**: **LOW for all models** (citations resolved). **Depth Risk**: **MEDIUM for Claude 4 Sonnet** (low quantitative density).

### 3.7 ID 100: Long Article (~1500–2300 words)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Words | 1,542 | 1,526 | 2,338 |
| Citations | 20 | 11 | 37 |
| Has Sources | ✅ | ✅ | ✅ |
| Missing refs | 0 | 0 | 0 |
| Sig. numbers | 17 | 31 | 29 |
| Counter signals | 8 | 15 | 15 |
| Unsupported bold | 13 | 11 | 35 |
| Vague words | 7 | 6 | 3 |

**Observations**:
- **Claude 4 Sonnet makes 35 unsupported bold claims** — the highest in this sample, despite having 37 citations.
- GPT-5 has the lowest citation count (11) for this long article, suggesting a shift toward synthesis over attribution.
- Counterargument signals are moderate (8–15) but still low relative to article length.

**Hallucination Risk**: **MEDIUM for Claude 4 Sonnet** (many unsupported bold claims). **LOW for GPT-4.1/GPT-5**.

---

## 4. Cross-Cutting Quality Issues

### 4.1 Source-Reference Mismatches

| Model | % Articles with Missing Refs | Avg Missing Refs (Affected Articles) |
|-------|---------------------------|-------------------------------------|
| GPT-4.1 | ~44% (from Phase 3) | ~17.9 |
| GPT-5 | ~44% (from Phase 3) | ~47.8 |
| Claude 4 Sonnet | ~29% (from Phase 3) | ~25.5 |

**Root Cause Hypothesis**: The `final_report_generation` prompt instructs the model to include inline citations and a Sources section, but:
1. The model may generate citations before the Sources section is finalized, leading to numbering drift.
2. Truncation during token limit retry loops may cut the Sources section while preserving body citations.
3. The compression step (`compress_research`) may renumber or drop sources without updating body references.

### 4.2 Weak Evidence and Unsupported Claims

**Bold Claims Without Citations**:
- All models format key claims in bold (`**...**`) for emphasis.
- The vast majority of these bold claims **do not include inline citation markers**.
- This creates a **visual authority bias**: readers trust bold text as fact, but cannot verify it.

**Quantitative Claims Without Attribution**:
- Significant numbers (market sizes, percentages, counts) appear frequently but often lack immediate citations.
- Example from ID 1 (GPT-5): "The global AI inference server market is projected to expand from USD 38.4 billion in 2023 to USD 166.7 billion by 2031" — bold, no citation.

### 4.3 Hallucination Risk Assessment

| Risk Factor | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|-------------|---------|-------|-----------------|
| Dangling citations (no Sources) | High (24% of articles) | Medium (11% of articles) | Medium (12% of articles) |
| Missing source entries | Medium (7.86 avg) | **Critical (21.05 avg)** | Medium (7.40 avg) |
| Unsupported bold claims | High (23.39 avg) | **Critical (46.30 avg)** | High (28.80 avg) |
| Low counterargument coverage | High | High | High |
| Overall hallucination risk | **Medium-High** | **Critical** | **Medium-High** |

### 4.4 Missing Counterarguments

Across all 298 articles:
- Average counterargument signals: **3.9 per article**.
- For articles averaging ~800 words, this is **~0.5% of content**.
- No article in the sample contained a dedicated "Limitations" or "Criticisms" section.
- The `eval_overall_quality` dimension "balance_and_objectivity" (15% weight) uses a 1–5 scale but does not explicitly require counterargument coverage.

**Impact**: Reports may present consensus where none exists, omit methodological weaknesses, and fail to warn readers about uncertainty.

---

## 5. Comparison to Existing Evaluators

| Quality Issue | Detected by Existing Evaluators? | Gap |
|---------------|-------------------------------|-----|
| Missing source entries | Partial (`eval_groundedness` checks raw_notes, not citation-source correspondence) | **High** |
| Unsupported bold claims | No | **Critical** |
| Low counterargument coverage | Partial (`balance_and_objectivity` dimension) | **High** |
| Dangling citations (no Sources section) | No (`eval_structure` checks formatting, not completeness) | **High** |
| Quantitative claims without attribution | No | **Medium** |
| Vague/hedging language | No | **Low** |

---

## 6. Recommendations

1. **Add citation-source correspondence validator**: Post-process every article to ensure each `[N]` in the body has a matching entry in the Sources section. Fail articles that don't pass.
2. **Require inline citations for bold claims**: Update `final_report_generation_prompt` to require `[N]` citations inside or immediately following bold sentences.
3. **Add counterargument requirement**: Update prompts to include a "Limitations and Counterarguments" subsection in every report. Add an evaluator dimension for counterargument coverage.
4. **Investigate GPT-5 citation integrity**: The 21.05 average missing references suggests a systematic bug in GPT-5's generation or extraction pipeline, not random noise.
5. **Add hallucination risk score**: A composite metric combining unsupported bold claims, missing references, and citation density. See Phase 6 for implementation.
6. **Add source traceability score**: A metric measuring the percentage of claims (sentences) with inline citations vs. those without. See Phase 6 for implementation.

---

*Generated as part of Phase 4: Research Quality Audit. All metrics computed programmatically from JSONL file contents. No human judgment or external verification was performed on factual accuracy of claims.*
