# Data Integrity Audit

## Executive Summary

This audit examines the three JSONL experiment result files exported from LangSmith runs against the Deep Research Bench benchmark. The files contain research prompts and generated articles for three different models: GPT-4.1, GPT-5, and Claude 4 Sonnet.

| File | Records | ID Range | Missing IDs | Schema Valid | Empty Content | Ref Issues |
|------|---------|----------|-------------|--------------|-------------|------------|
| `deep_research_bench_gpt-4.1.jsonl` | 100 | 1–100 | None | ✓ | None | 44 |
| `deep_research_bench_gpt-5.jsonl` | 100 | 1–100 | None | ✓ | None | 44 |
| `deep_research_bench_claude4-sonnet.jsonl` | 98 | 1–100 | **57, 98** | ✓ | None | 28 |

**Critical Finding**: Claude 4 Sonnet is missing **2 records** (IDs 57 and 98), representing a 2% failure rate. GPT-5 file has a trailing newline issue that causes `wc -l` to undercount by 1, but all 100 JSON records are present and valid.

**High Finding**: **44% of GPT-4.1 and GPT-5 articles**, and **29% of Claude 4 Sonnet articles**, have broken or missing citation references — citations in the body do not match entries in the Sources section, or the Sources section is entirely missing despite citation markers existing.

---

## 1. Schema Validation

### 1.1 Expected Schema

Per `tests/extract_langsmith_data.py`, each JSONL record should contain:

```json
{
  "id": int,
  "prompt": str,
  "article": str
}
```

- `id`: sourced from `example.metadata["id"]`
- `prompt`: sourced from `run.inputs["inputs"]["messages"][0]["content"]`
- `article`: sourced from `run.outputs["final_report"]`

### 1.2 Validation Results

| Check | gpt-4.1 | gpt-5 | claude4-sonnet |
|-------|---------|-------|----------------|
| JSON parseable | 100/100 | 100/100 | 98/98 |
| Has `id` field | 100/100 | 100/100 | 98/98 |
| `id` is integer | 100/100 | 100/100 | 98/98 |
| Has `prompt` field | 100/100 | 100/100 | 98/98 |
| `prompt` is string | 100/100 | 100/100 | 98/98 |
| Has `article` field | 100/100 | 100/100 | 98/98 |
| `article` is string | 100/100 | 100/100 | 98/98 |
| Empty `prompt` | 0 | 0 | 0 |
| Empty `article` | 0 | 0 | 0 |

**Verdict**: All records conform to the expected schema. No malformed JSON, no missing fields, no type violations.

---

## 2. ID Sequence Validation

### 2.1 ID Coverage

The Deep Research Bench contains 100 tasks with IDs 1–100. All three JSONL files should cover this range.

| Metric | gpt-4.1 | gpt-5 | claude4-sonnet |
|--------|---------|-------|----------------|
| Record count | 100 | 100 | 98 |
| Unique IDs | 100 | 100 | 98 |
| Min ID | 1 | 1 | 1 |
| Max ID | 100 | 100 | 100 |
| Missing IDs | None | None | **57, 98** |
| Duplicate IDs | None | None | None |

### 2.2 GPT-5 Line Count Discrepancy

`wc -l` reports 99 lines for `deep_research_bench_gpt-5.jsonl`, but parsing yields **100 valid JSON records**. The discrepancy occurs because the final line does **not** end with a newline character (`\n`). While this is a minor file formatting issue, it does not affect data integrity.

### 2.3 Claude 4 Sonnet Missing Records

**Missing IDs: 57 and 98**

These gaps indicate that the LangSmith run for Claude 4 Sonnet failed to produce outputs for two benchmark tasks. Possible causes:
- Runtime errors (timeouts, API failures, token limit exceeded)
- Extraction failures in `extract_langsmith_data.py` (run existed but `final_report` was null)
- Filtering or skipping during dataset iteration

**Impact**: Cross-model comparisons for IDs 57 and 98 are impossible. Any aggregate metrics that assume a complete 100-record dataset for Claude 4 Sonnet are biased.

---

## 3. Duplicate Detection

### 3.1 Exact Duplicate Articles

An exact duplicate would indicate a data extraction error or model outputting identical content for different prompts.

| File | Exact Duplicate Pairs |
|------|----------------------|
| gpt-4.1 | 0 |
| gpt-5 | 0 |
| claude4-sonnet | 0 |

**Verdict**: No exact duplicate articles found within any file.

### 3.2 Near-Duplicate Prompts

Near-duplicate prompts (normalized: lowercase, whitespace-collapsed) within a file would indicate benchmark contamination or duplicate task definitions.

| File | Near-Duplicate Prompt Pairs |
|------|---------------------------|
| gpt-4.1 | 0 |
| gpt-5 | 0 |
| claude4-sonnet | 0 |

**Verdict**: All prompts within each file are unique. No benchmark contamination detected.

### 3.3 Semantic Near-Duplicate Articles

Using a heuristic of normalized first 300 characters to detect semantically similar article openings:

| File | Semantic Duplicate Pairs |
|------|--------------------------|
| gpt-4.1 | 0 |
| gpt-5 | 0 |
| claude4-sonnet | 0 |

**Verdict**: No articles share identical openings, suggesting diverse topic coverage.

---

## 4. Cross-File Consistency

### 4.1 Prompt Consistency Across Files

For the same `id`, the `prompt` should be identical across all three files since they derive from the same benchmark dataset.

| Check | Result |
|-------|--------|
| Prompt mismatches (same ID, different prompt text) | **0** |

**Verdict**: All shared IDs have identical prompts across files. The benchmark dataset is consistently represented.

### 4.2 Shared ID Coverage

| Comparison | Shared IDs | gpt-4.1 only | gpt-5 only | claude4-sonnet only |
|------------|-----------|--------------|------------|---------------------|
| gpt-4.1 ↔ gpt-5 | 100 | 0 | 0 | — |
| gpt-4.1 ↔ claude4 | 98 | 2 | — | 0 |
| gpt-5 ↔ claude4 | 98 | — | 2 | 0 |

---

## 5. Broken Reference Audit

### 5.1 Methodology

For each article:
1. Extract all citation markers of the form `[N]` from the full article text.
2. Locate the `Sources` section (matching `### Sources`, `## Sources`, or `Sources`).
3. If citations exist but no Sources section is found → **broken reference**.
4. If Sources section exists, extract citation markers within it.
5. If any body citation `[N]` lacks a corresponding source entry → **broken reference**.

### 5.2 Results

| File | Articles with Broken/Missing References | Percentage |
|------|----------------------------------------|------------|
| gpt-4.1 | 44 | **44%** |
| gpt-5 | 44 | **44%** |
| claude4-sonnet | 28 | **29%** |

### 5.3 Analysis

The high rate of broken references is a **critical quality issue**. Possible root causes:

1. **Missing Sources sections**: The model generates citation markers `[1]`, `[2]` in the body but fails to produce a `### Sources` section.
2. **Citation numbering gaps**: The Sources section exists but does not contain entries for all cited numbers.
3. **Format inconsistency**: Sources may be listed without bracketed numbers, or using a different numbering scheme.
4. **Truncation**: Long articles may be truncated before the Sources section is generated.

**Impact**: Broken references undermine the credibility of generated reports. Users cannot verify claims against sources. The `eval_structure` evaluator checks formatting but does not validate citation-source correspondence.

---

## 6. File Format Issues

| Issue | File | Severity | Details |
|-------|------|----------|---------|
| Missing trailing newline | gpt-5.jsonl | Low | `wc -l` undercounts by 1. JSON parsing unaffected. |
| Missing records | claude4-sonnet.jsonl | **High** | 2 records missing (IDs 57, 98). Cause unknown. |

---

## 7. Summary of Findings

| # | Finding | Severity | Evidence |
|---|---------|----------|----------|
| 1 | Claude 4 Sonnet missing 2 records (IDs 57, 98) | **High** | 98 records vs expected 100; missing IDs confirmed programmatically |
| 2 | 44% of GPT-4.1/GPT-5 articles have broken references | **High** | 44/100 articles fail citation-source correspondence check |
| 3 | 29% of Claude 4 Sonnet articles have broken references | **High** | 28/98 articles fail citation-source correspondence check |
| 4 | GPT-5 file lacks trailing newline | Low | `wc -l` reports 99, but 100 JSON records present |
| 5 | No schema violations across all files | Good | 298/298 records conform to `{id, prompt, article}` schema |
| 6 | No duplicate articles or prompts | Good | Zero exact/near/semantic duplicates detected |
| 7 | Cross-file prompt consistency is perfect | Good | Zero mismatches across 98 shared IDs |
| 8 | No empty articles or prompts | Good | All 298 records have non-empty content |

---

## 8. Recommendations

1. **Investigate missing Claude 4 Sonnet records**: Check LangSmith run logs for IDs 57 and 98 to determine if failures were due to model errors, timeouts, or extraction bugs.
2. **Add per-record metadata**: Include `model_name`, `timestamp`, `token_count`, `cost`, `error_reason` (if applicable) in JSONL exports to aid debugging.
3. **Implement citation validation**: Add a post-processing step or evaluator that verifies every `[N]` citation in the body has a corresponding entry in the Sources section.
4. **Standardize file formatting**: Ensure `extract_langsmith_data.py` appends a trailing newline to the final JSONL record.
5. **Add checksums**: Include a content hash (e.g., SHA-256 of article text) to detect tampering or re-generation.
6. **Validate ID completeness**: Add an assertion in `extract_langsmith_data.py` that all expected IDs (1–100) are present, failing loudly on gaps.

---

*Generated as part of Phase 3: Data Integrity Audit. All findings based on programmatic analysis of the three JSONL files. No data was invented; all counts and IDs are derived directly from file contents.*
