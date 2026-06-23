# Improvement Scorecard

## Executive Summary

This scorecard compares metrics **before** and **after** the Phase 6 dataset improvements. The "before" state reflects findings from Phases 3 and 4 (integrity and research quality audits). The "after" state reflects the enriched dataset with automated metadata, deduplication, and two new benchmark dimensions: **hallucination risk score** and **source traceability score**.

**Caveat**: The adversarial review (Phase 7) challenged the validity of several new metrics as arbitrary, unvalidated heuristics. This scorecard presents the numerical deltas honestly while noting where the hostile auditor disputes interpretive validity.

---

## 1. Dataset-Level Metrics

### 1.1 Record Counts and Deduplication

| Metric | Before | After | Delta | Notes |
|--------|--------|-------|-------|-------|
| GPT-4.1 records | 100 | 100 | 0 | No duplicates found |
| GPT-5 records | 100 | 100 | 0 | No duplicates found |
| Claude 4 Sonnet records | 98 | 98 | 0 | No duplicates found |
| Total records | 298 | 298 | 0 | Deduplication ran but removed 0 records |

**Assessment**: The dataset was already clean of exact duplicates. The deduplication step confirmed this but produced no reduction.

### 1.2 Metadata Coverage (Per-Record)

| Field | Before | After | Delta |
|-------|--------|-------|-------|
| `id` | 100% | 100% | 0 |
| `prompt` | 100% | 100% | 0 |
| `article` | 100% | 100% | 0 |
| `model_name` | 0% | 100% | **+100%** |
| `source_file` | 0% | 100% | **+100%** |
| `audit_timestamp` | 0% | 100% | **+100%** |
| `record_hash` | 0% | 100% | **+100%** |
| `word_count` | 0% | 100% | **+100%** |
| `citation_count` | 0% | 100% | **+100%** |
| `has_sources_section` | 0% | 100% | **+100%** |
| `missing_ref_count` | 0% | 100% | **+100%** |
| `bold_claim_count` | 0% | 100% | **+100%** |
| `unsupported_bold_count` | 0% | 100% | **+100%** |
| `counterargument_signal_count` | 0% | 100% | **+100%** |
| `vague_word_count` | 0% | 100% | **+100%** |
| `citation_density` | 0% | 100% | **+100%** |
| `hallucination_risk_score` | 0% | 100% | **+100%** |
| `source_traceability_score` | 0% | 100% | **+100%** |

**Assessment**: Every record now carries 15 additional metadata fields enabling programmatic quality filtering and analysis. File size increased by ~30% (e.g., GPT-4.1 from ~1.35MB to ~1.75MB).

---

## 2. Research Quality Metrics (Before vs After Uniform Computation)

### 2.1 Before: Phase 4 Sample-Based Estimates (7 samples per model)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Avg missing refs per article | 7.86 | 21.05 | 7.40 |
| Articles with Sources section | 76.0% | 89.0% | 88.8% |
| Avg counterargument signals | 3.78 | 4.55 | 3.38 |
| Avg vague words | 2.34 | 2.92 | 3.14 |
| Avg unsupported bold claims | 23.39 | 46.30 | 28.80 |
| Avg citation density (per 1000 words) | 33.21 | 41.90 | 38.98 |

### 2.2 After: Phase 6 Full-Population Computation (all records)

| Metric | GPT-4.1 | GPT-5 | Claude 4 Sonnet |
|--------|---------|-------|-----------------|
| Avg missing refs per article | 14.77 | 15.70 | 7.31 |
| Articles with Sources section | 76.0% | 89.0% | 88.8% |
| Avg counterargument signals | 5.17 | 5.55 | 4.66 |
| Avg vague words | 3.67 | 4.66 | 4.53 |
| Avg unsupported bold claims | 22.37 | 44.46 | 28.35 |
| Avg citation density (per 1000 words) | 61.45 | 100.80 | 75.84 |
| Avg word count | 1,004.38 | 1,566.40 | 1,175.28 |
| Avg bold claim count | 22.37 | 44.46 | 28.35 |

### 2.3 Key Discrepancies Between Sample and Population

| Metric | Model | Sample (Before) | Population (After) | Variance | Interpretation |
|--------|-------|-----------------|--------------------|----------|----------------|
| Missing refs | GPT-4.1 | 7.86 | 14.77 | **+87.9%** | Sample under-represented short articles with missing refs |
| Missing refs | GPT-5 | 21.05 | 15.70 | **−25.4%** | Sample over-represented high-failure articles |
| Missing refs | Claude 4 Sonnet | 7.40 | 7.31 | −1.2% | Sample was representative |
| Citation density | GPT-4.1 | 33.21 | 61.45 | **+85.0%** | Sample selected shorter articles with fewer citations |
| Citation density | GPT-5 | 41.90 | 100.80 | **+140.6%** | Massive under-estimation in sample |
| Citation density | Claude 4 Sonnet | 38.98 | 75.84 | **+94.6%** | Sample was not representative of full distribution |

**Assessment**: The Phase 4 sample (7 hand-selected IDs) was **not representative** of the full population. Several metrics diverged by 85–140%. This validates the value of full-population computation but also undermines the reliability of Phase 4's qualitative conclusions.

---

## 3. New Benchmark Dimensions

### 3.1 Hallucination Risk Score (0.0 = low, 1.0 = high)

| Model | Mean | Median | Min | Max | Std Dev |
|-------|------|--------|-----|-----|---------|
| GPT-4.1 | 0.35 | 0.35 | 0.00 | 0.70 | 0.14 |
| GPT-5 | 0.31 | 0.30 | 0.00 | 0.65 | 0.13 |
| Claude 4 Sonnet | 0.29 | 0.30 | 0.00 | 0.60 | 0.12 |

**Distribution**: Most records cluster between 0.20 and 0.45. Scores near 0.00 occur when articles have sources sections, resolved citations, and few unsupported bold claims. Scores above 0.60 occur when articles lack sources sections entirely or have high missing-ref ratios.

**Hostile Auditor Note**: The weights (0.35, 0.25, 0.30, 0.20) are unvalidated. The score conflates formatting errors with factual hallucinations. A high score does not prove a claim is false.

### 3.2 Source Traceability Score (0.0 = untraceable, 1.0 = fully traceable)

| Model | Mean | Median | Min | Max | Std Dev |
|-------|------|--------|-----|-----|---------|
| GPT-4.1 | 0.55 | 0.56 | 0.00 | 1.00 | 0.22 |
| GPT-5 | 0.62 | 0.64 | 0.00 | 1.00 | 0.20 |
| Claude 4 Sonnet | 0.66 | 0.68 | 0.00 | 1.00 | 0.19 |

**Distribution**: Scores are bimodal. Articles without Sources sections score 0.00. Articles with dense, resolved citations score >0.80. The middle range (0.40–0.70) represents articles with partial citation resolution.

**Hostile Auditor Note**: The "claims" proxy (sentences >20 chars) is crude. The score rewards citation density over synthesis quality. No URL accessibility check is performed.

---

## 4. Per-Model Quality Profiles (After Enrichment)

### 4.1 GPT-4.1

| Dimension | Value | Rank (1=best, 3=worst) |
|-----------|-------|------------------------|
| Avg word count | 1,004 | 1 (shortest) |
| Avg citation count | 61.45 | 3 (lowest density) |
| Sources section coverage | 76.0% | 3 (worst) |
| Avg missing refs | 14.77 | 2 |
| Avg unsupported bold claims | 22.37 | 1 (best) |
| Hallucination risk score | 0.35 | 3 (worst) |
| Source traceability score | 0.55 | 3 (worst) |

**Profile**: Shortest articles, lowest sources-section coverage, highest hallucination risk. Tends to omit Sources sections more often than other models.

### 4.2 GPT-5

| Dimension | Value | Rank |
|-----------|-------|------|
| Avg word count | 1,566 | 3 (longest) |
| Avg citation count | 100.80 | 1 (highest density) |
| Sources section coverage | 89.0% | 1 (best) |
| Avg missing refs | 15.70 | 3 (worst) |
| Avg unsupported bold claims | 44.46 | 3 (worst) |
| Hallucination risk score | 0.31 | 2 |
| Source traceability score | 0.62 | 2 |

**Profile**: Longest, most verbose articles with the highest citation counts but also the most unsupported bold claims. High citation density does not translate to high traceability due to missing reference resolution.

### 4.3 Claude 4 Sonnet

| Dimension | Value | Rank |
|-----------|-------|------|
| Avg word count | 1,175 | 2 |
| Avg citation count | 75.84 | 2 |
| Sources section coverage | 88.8% | 2 |
| Avg missing refs | 7.31 | 1 (best) |
| Avg unsupported bold claims | 28.35 | 2 |
| Hallucination risk score | 0.29 | 1 (best) |
| Source traceability score | 0.66 | 1 (best) |

**Profile**: Best balance of length, citation integrity, and traceability. Lowest missing-ref rate and best composite scores.

---

## 5. Structural Improvements

| Improvement | Before | After | Evidence |
|-------------|--------|-------|----------|
| **Exact duplicate detection** | Not performed | Performed; 0 duplicates found | `enrichment_summary.json` shows `duplicates_removed: 0` for all models |
| **Per-record provenance** | None | `model_name`, `source_file`, `audit_timestamp`, `record_hash` | Every enriched record contains `_metadata` block |
| **Citation integrity automation** | Manual regex in audit scripts | Automated per-record `missing_ref_count` | All 298 records have computed missing_ref_count |
| **Composite quality scores** | None | `hallucination_risk_score`, `source_traceability_score` | Population statistics computed for all records |
| **Uniform metric computation** | 7-sample heuristic | Full-population exact counts | All metrics now cover 100/100/98 records respectively |

---

## 6. Honest Assessment of Limitations

1. **No ground-truth validation**: The new scores measure formatting and heuristics, not factual accuracy. A record with `hallucination_risk_score: 0.00` may still contain false claims.
2. **No URL accessibility check**: `source_traceability_score` assumes source entries are valid but does not verify HTTP 200 responses.
3. **No semantic deduplication**: Exact deduplication found 0 duplicates, but near-duplicate or paraphrased articles across models were not detected.
4. **No cross-lingual analysis**: 50% of the benchmark is Chinese prompts. The enrichment metrics (counterargument signals, vague words) are English-biased and may misclassify Chinese reports.
5. **Sample vs population divergence**: Phase 4's sample-based conclusions were significantly off for citation density and missing refs. Future audits should use full-population metrics or stratified random sampling.

---

*Generated as part of Phase 8: Before vs After Comparison. "Before" metrics sourced from Phase 3 (integrity_audit.md) and Phase 4 (research_quality_audit.md). "After" metrics computed from enriched JSONL files in tests/expt_results/enriched/.*
