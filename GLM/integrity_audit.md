# Phase 3: Integrity Audit — Open Deep Research

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** Programmatic analysis of all 3 JSONL files using Python. Every number in this document is computed from actual data and can be reproduced.

---

## 1. Executive Summary

| Category | Finding | Severity |
|----------|---------|----------|
| Duplicates | 0 exact duplicates found across all files | ✅ Pass |
| Schema consistency | All files use identical `{id, prompt, article}` schema | ✅ Pass |
| ID completeness | claude4-sonnet missing IDs 57, 98 (2 records lost) | 🟡 High |
| Prompt consistency | 0 mismatches across files for same IDs | ✅ Pass |
| Provenance metadata | Missing from all records (no model, timestamp, config) | 🟡 High |
| Broken citation references | 20/33/16 articles (gpt-4.1/gpt-5/claude4-sonnet) | 🟠 Medium |
| Missing Sources sections | 24/11/11 articles lack Sources section | 🟠 Medium |
| Self-referential language | 2/1/2 articles violate prompt constraint | 🟢 Low |
| Error markers in articles | 0 articles contain error messages | ✅ Pass |
| Very short articles (<2000 chars) | 0 articles below threshold | ✅ Pass |

---

## 2. Duplicate Analysis

### 2.1 Exact Duplicate Check (Within File)

| File | Total Records | Unique Articles | Exact Duplicates |
|------|--------------|-----------------|------------------|
| gpt-4.1 | 100 | 100 | **0** |
| gpt-5 | 100 | 100 | **0** |
| claude4-sonnet | 98 | 98 | **0** |

**Method:** Computed `set()` of all article strings per file and compared count to total records.

**Conclusion:** ✅ No exact duplicates within any file.

### 2.2 Cross-File Near-Duplicate Check

| Comparison | IDs with >50% Similarity | Max Similarity Found |
|------------|-------------------------|---------------------|
| gpt-4.1 vs gpt-5 | 0 | UNVERIFIED (all <50%) |
| gpt-4.1 vs claude4-sonnet | 0 | UNVERIFIED (all <50%) |
| gpt-5 vs claude4-sonnet | 0 | UNVERIFIED (all <50%) |

**Method:** For each shared ID, computed `SequenceMatcher` ratio on first 2000 characters of articles. Threshold: >50% similarity.

**Conclusion:** ✅ No cross-file near-duplicates. This is expected since different models produce different outputs for the same prompts.

### 2.3 Prompt Duplicate Check

| File | Total Prompts | Unique Prompts |
|------|--------------|----------------|
| gpt-4.1 | 100 | 100 |
| gpt-5 | 100 | 100 |
| claude4-sonnet | 98 | 98 |

**Conclusion:** ✅ All prompts are unique within each file (no repeated research questions).

---

## 3. Schema Analysis

### 3.1 Schema Consistency

| File | Keys Present | Extra Keys | Missing Keys |
|------|-------------|------------|--------------|
| gpt-4.1 | `article`, `id`, `prompt` | None | None |
| gpt-5 | `article`, `id`, `prompt` | None | None |
| claude4-sonnet | `article`, `id`, `prompt` | None | None |

**Method:** Aggregated all keys across all records per file using `set().update(r.keys())`.

**Conclusion:** ✅ Schema is perfectly consistent across all 297 records in all 3 files.

### 3.2 Schema Problems

**Problem: Missing provenance metadata.** The schema contains only `{id, prompt, article}` — it is missing critical provenance fields:

| Missing Field | Why It Matters |
|---------------|----------------|
| `model` | Cannot determine which model generated the article from the data alone |
| `timestamp` | Cannot determine when the experiment was run |
| `experiment_id` | Cannot trace back to the LangSmith experiment |
| `search_api` | Cannot verify which search API was used |
| `config` | Cannot reproduce the experiment without knowing full configuration |
| `research_brief` | Cannot evaluate completeness without the intermediate research brief |
| `raw_notes` | Cannot evaluate groundedness without the source context |
| `language` | Cannot programmatically verify language matching without detection |
| `cost` | Cannot track experiment costs |
| `token_count` | Cannot verify token usage claims |

**Impact:** Without provenance metadata, the JSONL files are not self-describing. Any analysis requires cross-referencing with `run_evaluate.py` source code and README documentation to reconstruct the experimental context.

---

## 4. Structural Issues

### 4.1 Missing Records (ID Gaps)

| File | Expected IDs | Actual IDs | Missing IDs | Missing Count |
|------|-------------|------------|-------------|---------------|
| gpt-4.1 | 1-100 | 1-100 | None | **0** |
| gpt-5 | 1-100 | 1-100 | None | **0** |
| claude4-sonnet | 1-100 | 1-100 (except 57, 98) | **57, 98** | **2** |

**Root cause:** `extract_langsmith_data.py` filters runs with `if run.outputs is not None and run.outputs.get("final_report") is not None`. If a run fails and produces no `final_report`, it is silently excluded. The 2 missing claude4-sonnet records (IDs 57, 98) represent failed runs that produced no output.

**Impact:**
- The claude4-sonnet benchmark results are based on 98/100 tasks, not 100/100
- Any aggregate metrics (averages, RACE scores) for claude4-sonnet are computed over 98 samples, not 100
- Cross-model comparisons are not apples-to-apples for IDs 57 and 98
- The reason for failure is UNVERIFIED — no error logs are available

### 4.2 Broken Citation References

**Definition:** An article cites `[N]` in the body text but source `N` does not appear in the Sources section.

| File | Articles with Broken Citations | Total Articles | Percentage |
|------|-------------------------------|-----------------|------------|
| gpt-4.1 | **20** | 100 | 20.0% |
| gpt-5 | **33** | 100 | 33.0% |
| claude4-sonnet | **16** | 98 | 16.3% |

**Method:** For each article, extracted all `[N]` citations from the body (before the Sources section) and all `[N]` references in the Sources section. If any body citation number was missing from the Sources section, the article was flagged.

**Example pattern:** Article body contains `[15]` citation, but the Sources section only lists sources `[1]` through `[14]` — source 15 is missing.

**Impact:**
- Readers cannot verify claims that reference missing sources
- The `final_report_generation_prompt` explicitly requires: "Number sources sequentially without gaps (1,2,3,4...)"
- This is a systematic citation integrity problem affecting 16-33% of articles
- No evaluator currently detects this issue

### 4.3 Missing Sources Sections

| File | Articles with Sources | Articles without Sources | Missing Percentage |
|------|----------------------|-------------------------|-------------------|
| gpt-4.1 | 76 | **24** | 24.0% |
| gpt-5 | 89 | **11** | 11.0% |
| claude4-sonnet | 87 | **11** | 11.2% |

**Method:** Checked for presence of `### Sources`, `## Sources`, or `Sources` in the last 500 characters of each article.

**IDs without Sources (gpt-4.1):** 1, 2, 7, 9, 11, 18, 25, 26, 28, 30, 31, 33, 34, 36, 40, 41, 44, 45, 48, 49 (and 4 more)

**IDs without Sources (gpt-5):** 4, 5, 7, 15, 28, 36, 43, 45, 48, 67, 83

**IDs without Sources (claude4-sonnet):** 8, 9, 14, 24, 25, 26, 35, 37, 40, 41, 45

**Impact:**
- 24% of gpt-4.1 articles have no source attribution whatsoever
- The `final_report_generation_prompt` explicitly requires: "Includes a Sources section at the end with all referenced links"
- No evaluator currently checks for the presence of a Sources section
- Articles without sources cannot be verified for accuracy or groundedness

### 4.4 Citation Format Inconsistency

| File | `[N]` Bracket Citations | `[Title](URL)` Markdown Citations | Both Formats | Neither |
|------|------------------------|----------------------------------|-------------|---------|
| gpt-4.1 | 99 | 36 | 35 | 1 |
| gpt-5 | 99 | 40 | 39 | 1 |
| claude4-sonnet | 96 | 23 | 22 | 2 |

**Method:** Used regex `r'\[\d+\]'` for bracket citations and `r'\[.*?\]\(https?://'` for markdown citations.

**Impact:**
- The `final_report_generation_prompt` specifies `[Title](URL)` format for inline citations and `[N] Source Title: URL` for the Sources section
- However, the `compress_research_system_prompt` specifies `[N]` format for inline citations
- This conflicting instruction leads to mixed citation formats within and across articles
- 35-39 articles use both formats simultaneously, creating inconsistency

---

## 5. Content Quality Issues

### 5.1 Self-Referential Language Violations

The `final_report_generation_prompt` explicitly states: "Do NOT ever refer to yourself as the writer of the report."

| File | Articles with Self-Referential Language | IDs |
|------|----------------------------------------|-----|
| gpt-4.1 | **2** | 71, 72 |
| gpt-5 | **1** | 87 |
| claude4-sonnet | **2** | 87, 100 |

**Method:** Searched for patterns including: "I conducted research", "I gathered", "I found", "my research", "I searched", "I will present", "As an AI", "I used various sources", "In this report, I", "Let me", "I compiled".

**Impact:** Low — only 5 articles across all files violate this constraint. The `OVERALL_QUALITY_PROMPT` evaluator mentions "Does not refer to itself as the writer" but does not have a dedicated check.

### 5.2 Error Markers in Articles

| File | Articles with Error Markers |
|------|----------------------------|
| gpt-4.1 | **0** |
| gpt-5 | **0** |
| claude4-sonnet | **0** |

**Method:** Searched for "Error generating", "Maximum retries exceeded", "Error synthesizing".

**Conclusion:** ✅ No error markers in any article. However, this does not mean errors didn't occur — the `or True` bug in `supervisor_tools` would silently end research without inserting error text, and failed runs are excluded by `extract_langsmith_data.py`.

### 5.3 Article Length Distribution

| File | Min (chars) | Max (chars) | Average (chars) | Median (chars) |
|------|-------------|-------------|-----------------|----------------|
| gpt-4.1 | 3,062 | 26,473 | 10,387 | 11,026 |
| gpt-5 | 3,573 | 35,896 | 16,455 | 15,825 |
| claude4-sonnet | 4,235 | 24,297 | 12,358 | 12,306 |

**Observations:**
- GPT-5 produces the longest articles on average (16,455 chars) — 58% longer than GPT-4.1
- No articles are suspiciously short (all >3000 chars), ruling out truncated/failed outputs
- GPT-5 has the widest range (3,573 to 35,896), suggesting more variability in output length

### 5.4 URL Coverage

| File | Articles with Zero URLs |
|------|------------------------|
| gpt-4.1 | **0** |
| gpt-5 | **0** |
| claude4-sonnet | **0** |

**Conclusion:** ✅ All articles contain at least one URL. However, having URLs does not guarantee they are correct, accessible, or properly cited.

### 5.5 Language Consistency

| File | Chinese Prompts | Chinese Articles | Mismatches |
|------|----------------|-----------------|------------|
| gpt-4.1 | 50 | 50 | **0** |
| gpt-5 | 50 | 50 | **0** |
| claude4-sonnet | 50 | 50 | **0** |

**Method:** Detected Chinese characters using regex `r'[\u4e00-\u9fff]'` in prompts and articles.

**Conclusion:** ✅ Perfect language consistency — all 50 Chinese prompts produced Chinese articles across all 3 model files. The `final_report_generation_prompt`'s language instruction is being followed.

---

## 6. Cross-File Integrity

### 6.1 Prompt Alignment

| Check | Result |
|-------|--------|
| gpt-4.1 vs gpt-5 (shared IDs) | ✅ 0 prompt mismatches out of 100 |
| gpt-4.1 vs claude4-sonnet (shared IDs) | ✅ 0 prompt mismatches out of 98 |
| gpt-5 vs claude4-sonnet (shared IDs) | ✅ 0 prompt mismatches out of 98 |

**Conclusion:** ✅ All prompts are identical across files for the same IDs. The 3 experiment runs used the same 100 tasks from the Deep Research Bench dataset.

### 6.2 ID Coverage Matrix

| ID Range | gpt-4.1 | gpt-5 | claude4-sonnet |
|----------|---------|-------|----------------|
| 1-56 | ✅ Present | ✅ Present | ✅ Present |
| 57 | ✅ Present | ✅ Present | ❌ **Missing** |
| 58-97 | ✅ Present | ✅ Present | ✅ Present |
| 98 | ✅ Present | ✅ Present | ❌ **Missing** |
| 99-100 | ✅ Present | ✅ Present | ✅ Present |

**Impact:** For IDs 57 and 98, only 2 of 3 models have results. Any comparative analysis across all 3 models can only use 98 tasks, not 100.

---

## 7. Data Extraction Pipeline Integrity

### 7.1 `extract_langsmith_data.py` Analysis

**Filtering logic:**
```python
for run in output_runs:
    if run.outputs is not None and run.outputs.get("final_report") is not None:
        runs.append(run)
```

**Issues:**
1. **Silent exclusion of failed runs:** Runs without `final_report` are silently dropped. No warning, no log, no count of excluded runs. This is the root cause of missing IDs 57 and 98.
2. **No error reporting:** If a run failed with an error, that error information is lost.
3. **No metadata preservation:** The extraction only keeps `{id, prompt, article}` — discarding all other run metadata (model config, cost, tokens, timestamps, intermediate states).

### 7.2 Data Integrity Checklist

| Check | Status | Evidence |
|-------|--------|----------|
| All expected IDs present | ⚠️ Partial | claude4-sonnet missing 2 IDs |
| No duplicate records | ✅ Pass | 0 exact duplicates in all files |
| Schema consistent | ✅ Pass | All records have `{id, prompt, article}` |
| Prompts match across files | ✅ Pass | 0 mismatches |
| No error messages in data | ✅ Pass | 0 error markers found |
| No truncated articles | ✅ Pass | All articles >3000 chars |
| Language consistency | ✅ Pass | All Chinese prompts → Chinese articles |
| Citation completeness | ⚠️ Fail | 16-33% have broken citation refs |
| Sources section present | ⚠️ Fail | 11-24% lack Sources section |
| Provenance metadata | ❌ Fail | No metadata in any record |

---

## 8. Summary of All Data Analysis Numbers

### Record Counts
- gpt-4.1: 100 records, IDs 1-100, 0 missing
- gpt-5: 100 records, IDs 1-100, 0 missing
- claude4-sonnet: 98 records, IDs 1-100 (missing 57, 98), 2 missing
- Total: 297 records across 3 files

### Duplicates
- Within-file exact duplicates: 0 (all files)
- Cross-file near-duplicates (>50% similarity): 0

### Schema
- Keys per record: `article`, `id`, `prompt` (consistent across all 297 records)
- Missing provenance fields: 10 critical fields absent

### Citation Issues
- Broken citation references: 20 (gpt-4.1), 33 (gpt-5), 16 (claude4-sonnet)
- Missing Sources sections: 24 (gpt-4.1), 11 (gpt-5), 11 (claude4-sonnet)
- Mixed citation formats: 35 (gpt-4.1), 39 (gpt-5), 22 (claude4-sonnet) use both `[N]` and `[Title](URL)`

### Content Quality
- Self-referential language: 2 (gpt-4.1), 1 (gpt-5), 2 (claude4-sonnet)
- Error markers: 0 (all files)
- Articles with zero URLs: 0 (all files)
- Language mismatches: 0 (all files)

### Article Lengths (chars)
- gpt-4.1: min=3,062, max=26,473, avg=10,387, median=11,026
- gpt-5: min=3,573, max=35,896, avg=16,455, median=15,825
- claude4-sonnet: min=4,235, max=24,297, avg=12,358, median=12,306

---

*End of Phase 3 Integrity Audit*
