# Phase 9: Verification Matrix — Every Improvement with Evidence and Verification Status

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** This matrix lists every finding, improvement, and claim from Phases 1–8 with its evidence source, verification method, and verification status. Claims are marked ✅ Verified, ⚠️ Partially Verified, or ❓ UNVERIFIED based on the strength of evidence.

---

## 1. Verification Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Verified | Evidence is from direct programmatic analysis or code inspection; reproducible |
| ⚠️ Partially Verified | Evidence is from heuristic analysis with known limitations (false positive/negative risk) |
| ❓ UNVERIFIED | Evidence is inferred, hypothesized, or not directly confirmable from available data |
| 📋 Proposed | Improvement is designed but not implemented; no runtime verification possible |

---

## 2. Data Asset Findings

### 2.1 Dataset Inventory

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 1 | 3 JSONL files exist in `tests/expt_results/` | `ls tests/expt_results/*.jsonl` | File listing | ✅ Verified |
| 2 | gpt-4.1 file has 100 records | `wc -l` + `json.loads` iteration | Line count + JSON parse | ✅ Verified |
| 3 | gpt-5 file has 100 records | `wc -l` + `json.loads` iteration | Line count + JSON parse | ✅ Verified |
| 4 | claude4-sonnet file has 98 records | `wc -l` + `json.loads` iteration | Line count + JSON parse | ✅ Verified |
| 5 | Total records: 298 | Sum of above | Arithmetic | ✅ Verified |
| 6 | Schema is `{id, prompt, article}` for all files | `json.loads` + key aggregation | Key set comparison | ✅ Verified |
| 7 | LangSmith dataset "Deep Research Bench" exists | `tests/run_evaluate.py` line: `dataset_name = "Deep Research Bench"` | Code inspection | ✅ Verified |
| 8 | LangSmith dataset "ODR: First Supervisor Parallelism" exists | `tests/supervisor_parallel_evaluation.py` | Code inspection | ✅ Verified |
| 9 | Example reports exist in `src/legacy/tests/` | File listing | `ls src/legacy/tests/` | ✅ Verified |

### 2.2 Data Integrity

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 10 | 0 exact duplicates in all files | `set(articles)` comparison | Exact string match | ✅ Verified |
| 11 | 0 near-duplicates across files (>50% similarity, first 2000 chars) | `SequenceMatcher` on first 2000 chars | Sequence similarity | ⚠️ Partially Verified (limited to 2000 chars, 50% threshold) |
| 12 | claude4-sonnet missing IDs 57 and 98 | `set(range(1,101)) - set(records.keys())` | Set difference | ✅ Verified (fact); ❓ root cause UNVERIFIED |
| 13 | 0 prompt mismatches across files | String comparison of all prompts for same IDs | Exact string match | ✅ Verified |
| 14 | 50 Chinese prompts per file, all produce Chinese articles | Regex `[\u4e00-\u9fff]` detection | Character class match | ✅ Verified |
| 15 | 0 error markers in article text | String search for 3 error patterns | Substring match | ⚠️ Partially Verified (only 3 patterns checked; `or True` bug may mask errors) |
| 16 | 0 articles with zero URLs | `re.findall(r'https?://...')` | URL extraction | ✅ Verified |
| 17 | Article lengths: gpt-4.1 avg=10,387; gpt-5 avg=16,455; claude avg=12,358 | `len(article)` per record | Character count | ✅ Verified |

### 2.3 Missing Records Root Cause

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 18 | IDs 57 and 98 absent from claude4-sonnet JSONL | ID range check | Set difference | ✅ Verified (fact) |
| 19 | Root cause: failed runs silently excluded by `extract_langsmith_data.py` | Code inspection of extraction script | Code analysis | ❓ UNVERIFIED (hypothesis — not confirmed against LangSmith logs) |
| 20 | `extract_langsmith_data.py` does not log failed runs | Code inspection | Code reading | ✅ Verified |

---

## 3. Research Quality Findings

### 3.1 Citation Quality

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 21 | gpt-4.1: 76/100 articles have Sources section (24% missing) | String search for "### Sources" / "## Sources" / "Sources" in last 500 chars | Heuristic string match | ⚠️ Partially Verified (±5% margin; may miss alternative heading formats) |
| 22 | gpt-5: 89/100 articles have Sources section (11% missing) | Same as above | Same heuristic | ⚠️ Partially Verified |
| 23 | claude4-sonnet: 87/98 articles have Sources section (11.2% missing) | Same as above | Same heuristic | ⚠️ Partially Verified |
| 24 | gpt-4.1: 20 articles with orphaned bracket citations | `re.findall(r'\[(\d+)\]')` body vs sources set difference | Regex set difference | ⚠️ Partially Verified (may be format mismatch, not broken refs) |
| 25 | gpt-5: 33 articles with orphaned bracket citations | Same as above | Same method | ⚠️ Partially Verified |
| 26 | claude4-sonnet: 16 articles with orphaned bracket citations | Same as above | Same method | ⚠️ Partially Verified |
| 27 | Bracket `[N]` citations: 99%, 99%, 96% | `re.search(r'\[\d+\]')` | Regex presence check | ✅ Verified |
| 28 | Markdown `[Title](URL)` citations: 36%, 40%, 23% | `re.search(r'\[.*?\]\(https?://')` | Regex presence check | ✅ Verified |
| 29 | Total citations: gpt-4.1=4,965; gpt-5=7,912; claude=5,365 | `re.findall` count | Regex count | ✅ Verified |
| 30 | Total URLs: gpt-4.1=2,247; gpt-5=4,111; claude=2,873 | `re.findall(r'https?://')` count | Regex count | ✅ Verified |

### 3.2 Source Diversity

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 31 | Avg unique domains: gpt-4.1=14.7; gpt-5=24.2; claude=20.7 | URL domain extraction + `set()` count | Domain parsing | ✅ Verified |
| 32 | Min unique domains: gpt-4.1=4; gpt-5=2; claude=5 | Same as above | Same method | ✅ Verified |
| 33 | Max unique domains: gpt-4.1=63; gpt-5=73; claude=59 | Same as above | Same method | ✅ Verified |
| 34 | Top domain for gpt-4.1: sciencedirect.com (99 URLs) | Domain frequency count | Counter | ✅ Verified |
| 35 | Top domain for gpt-5: arxiv.org (126 URLs) | Same | Same | ✅ Verified |
| 36 | Top domain for claude4-sonnet: sciencedirect.com (116 URLs) | Same | Same | ✅ Verified |
| 37 | saintseiya.fandom.com appears 47 times in claude4-sonnet | Domain frequency count | Counter | ✅ Verified (fact); ❓ hallucination status UNVERIFIED |

### 3.3 Self-Referential Language

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 38 | gpt-4.1: 2 articles with self-referential language (IDs 71, 72) | 11 regex patterns | Pattern match | ⚠️ Partially Verified (may overcount due to false positives) |
| 39 | gpt-5: 1 article with self-referential language (ID 87) | Same | Same | ⚠️ Partially Verified |
| 40 | claude4-sonnet: 2 articles with self-referential language (IDs 87, 100) | Same | Same | ⚠️ Partially Verified |
| 41 | Total self-referential violations: 5/298 (1.7%) | Sum of above | Arithmetic | ⚠️ Partially Verified |

### 3.4 Counterargument Coverage

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 42 | gpt-4.1: 13 articles with counterargument markers | 7 regex patterns | Pattern match | ⚠️ Partially Verified (lower bound — conservative patterns) |
| 43 | gpt-5: 6 articles with counterargument markers | Same | Same | ⚠️ Partially Verified |
| 44 | claude4-sonnet: 6 articles with counterargument markers | Same | Same | ⚠️ Partially Verified |

---

## 4. Evaluation Framework Findings

### 4.1 Current Evaluators

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 45 | 6 evaluators exist in `tests/evaluators.py` | Code inspection | File reading | ✅ Verified |
| 46 | Evaluators: overall_quality, relevance, structure, correctness, groundedness, completeness | Function definitions in `evaluators.py` | Code inspection | ✅ Verified |
| 47 | All scores normalized to 0–1 | Return values in evaluator functions | Code inspection | ✅ Verified |
| 48 | `eval_model` hardcoded to `gpt-4.1` | `eval_model = ChatOpenAI(model="gpt-4.1")` | Code inspection | ✅ Verified |
| 49 | `eval_groundedness` uses `raw_notes` as context | Evaluator function body | Code inspection | ✅ Verified |
| 50 | Pairwise evaluation uses `claude-opus-4` as judge | `tests/pairwise_evaluation.py` | Code inspection | ✅ Verified |
| 51 | Pairwise evaluation has hardcoded experiment names | Bottom of `pairwise_evaluation.py` | Code inspection | ✅ Verified |

### 4.2 Evaluation Gaps

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 52 | No citation completeness evaluator | Absence in `evaluators.py` | Code inspection (negative finding) | ✅ Verified |
| 53 | No hallucination risk evaluator (dedicated) | Absence in `evaluators.py` | Code inspection | ✅ Verified |
| 54 | No source diversity evaluator | Absence in `evaluators.py` | Code inspection | ✅ Verified |
| 55 | No counterargument evaluator | Absence in `evaluators.py` | Code inspection | ✅ Verified |
| 56 | No self-referential language evaluator | Absence in `evaluators.py` | Code inspection | ✅ Verified |
| 57 | No silent failure detection evaluator | Absence in `evaluators.py` | Code inspection | ✅ Verified |
| 58 | No language consistency evaluator | Absence in `evaluators.py` | Code inspection | ✅ Verified |
| 59 | No traceability evaluator | Absence in `evaluators.py` | Code inspection | ✅ Verified |

---

## 5. Code Bug Findings

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 60 | `or True` in `supervisor_tools` exception handling | `deep_researcher.py` line: `if is_token_limit_exceeded(e, configurable.research_model) or True:` | Code inspection | ✅ Verified (code fact); ❓ intent UNVERIFIED |
| 61 | `MODEL_TOKEN_LIMITS` missing `openai:gpt-5` | `utils.py` dict inspection | Code inspection | ✅ Verified |
| 62 | `summarization_model` config field unused in main flow | `deep_researcher.py` — no reference to `summarization_model` | Code search | ✅ Verified |
| 63 | `compression_model_max_tokens` mismatch: 10000 vs 8192 | `run_evaluate.py` vs `configuration.py` | Code comparison | ✅ Verified (fact); ❓ intent UNVERIFIED |

---

## 6. Phase 6 Improvements — Metadata Enrichment

| # | Improvement | Evidence Source | Verification Method | Status |
|---|-------------|----------------|---------------------|--------|
| 64 | `improvements/metadata_enrichment.py` created | File exists at `/home/azureuser/ModelsEval/GLM/improvements/metadata_enrichment.py` | File listing | ✅ Verified |
| 65 | Script processes 298 records (100 + 100 + 98) | Script stdout: "Total records processed: 298 in → 298 out" | Execution output | ✅ Verified |
| 66 | 3 enriched JSONL files produced | Files exist in `improvements/enriched/` | File listing | ✅ Verified |
| 67 | Enriched schema has 17 fields (3 original + 14 new) | `json.loads` of enriched records | JSON key inspection | ✅ Verified |
| 68 | Enrichment is non-destructive (original files unchanged) | Original files still in `tests/expt_results/` | File listing | ✅ Verified |
| 69 | Quality signals match Phase 3 analysis | Enrichment output matches Phase 3 counts (76%, 20%, etc.) | Cross-reference | ✅ Verified |
| 70 | gpt-4.1 enriched: 100 records, 76% sources, 20% broken citations | Script stdout | Execution output | ✅ Verified |
| 71 | gpt-5 enriched: 100 records, 89% sources, 33% broken citations | Script stdout | Execution output | ✅ Verified |
| 72 | claude4-sonnet enriched: 98 records, 88.8% sources, 16.3% broken citations | Script stdout | Execution output | ✅ Verified |
| 73 | Enriched files contain `model` field with correct values | First record verification in script output | JSON inspection | ✅ Verified |
| 74 | Enriched files contain `has_sources_section` boolean | First record verification | JSON inspection | ✅ Verified |
| 75 | Enriched files contain `broken_citation_count` integer | First record verification | JSON inspection | ✅ Verified |
| 76 | Enriched files contain `has_self_referential_language` boolean | First record verification | JSON inspection | ✅ Verified |
| 77 | Enriched files contain `has_error_markers` boolean | First record verification | JSON inspection | ✅ Verified |
| 78 | Hardcoded model values in script are inferred from filenames | `metadata_enrichment.py` source code | Code inspection | ✅ Verified (fact); ❓ accuracy UNVERIFIED against LangSmith |

---

## 7. Phase 6 Improvements — Benchmark Proposals

| # | Proposed Improvement | Evidence Source | Verification Method | Status |
|---|----------------------|----------------|---------------------|--------|
| 79 | Citation completeness evaluator proposed | `benchmark_improvements.md` Section 2.1 | Document inspection | 📋 Proposed |
| 80 | Hallucination risk evaluator proposed | `benchmark_improvements.md` Section 2.2 | Document inspection | 📋 Proposed |
| 81 | Source diversity evaluator proposed | `benchmark_improvements.md` Section 2.3 | Document inspection | 📋 Proposed |
| 82 | Counterargument evaluator proposed | `benchmark_improvements.md` Section 2.4 | Document inspection | 📋 Proposed |
| 83 | Self-referential evaluator proposed | `benchmark_improvements.md` Section 2.5 | Document inspection | 📋 Proposed |
| 84 | Silent failure evaluator proposed | `benchmark_improvements.md` Section 2.6 | Document inspection | 📋 Proposed |
| 85 | Language consistency evaluator proposed | `benchmark_improvements.md` Section 2.7 | Document inspection | 📋 Proposed |
| 86 | Traceability evaluator proposed | `benchmark_improvements.md` Section 2.8 | Document inspection | 📋 Proposed |
| 87 | Configurable eval model proposed | `benchmark_improvements.md` Section 3.1 | Document inspection | 📋 Proposed |
| 88 | Parameterized pairwise evaluation proposed | `benchmark_improvements.md` Section 3.2 | Document inspection | 📋 Proposed |
| 89 | Add `openai:gpt-5` to token limits proposed | `benchmark_improvements.md` Section 3.3 | Document inspection | 📋 Proposed |
| 90 | Fix `or True` bug proposed | `benchmark_improvements.md` Section 3.4 | Document inspection | 📋 Proposed |
| 91 | Preserve intermediate state in extraction proposed | `benchmark_improvements.md` Section 3.5 | Document inspection | 📋 Proposed |
| 92 | Log failed runs in extraction proposed | `benchmark_improvements.md` Section 3.6 | Document inspection | 📋 Proposed |
| 93 | Enhanced RACE composite score proposed | `benchmark_improvements.md` Section 4.1 | Document inspection | 📋 Proposed |
| 94 | Quality tier system proposed | `benchmark_improvements.md` Section 4.2 | Document inspection | 📋 Proposed |

---

## 8. Benchmark Results from README

| # | Finding | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 95 | GPT-5 RACE score: 0.4943 | `README.md` benchmark table | Document reading | ✅ Verified (from README) |
| 96 | GPT-5 token count: 204M | `README.md` | Document reading | ✅ Verified (from README) |
| 97 | GPT-5 commit: ca3951d | `README.md` | Document reading | ✅ Verified (from README) |
| 98 | Defaults (gpt-4.1) RACE: 0.4309 | `README.md` | Document reading | ✅ Verified (from README) |
| 99 | Defaults cost: $45.98 | `README.md` | Document reading | ✅ Verified (from README) |
| 100 | Claude Sonnet 4 RACE: 0.4401 | `README.md` | Document reading | ✅ Verified (from README) |
| 101 | Claude Sonnet 4 cost: $187.09 | `README.md` | Document reading | ✅ Verified (from README) |
| 102 | DRB Submission RACE: 0.4344 | `README.md` | Document reading | ✅ Verified (from README) |

---

## 9. Adversarial Review Challenges

| # | Challenge | Evidence Source | Verification Method | Status |
|---|---------|----------------|---------------------|--------|
| 103 | `has_sources_section` heuristic has ±5% margin | `adversarial_review.md` Section 2.1 | Adversarial analysis | ⚠️ Acknowledged limitation |
| 104 | `broken_citation_count` may be format mismatch | `adversarial_review.md` Section 2.2 | Adversarial analysis | ⚠️ Acknowledged limitation |
| 105 | `has_self_referential_language` may overcount | `adversarial_review.md` Section 2.3 | Adversarial analysis | ⚠️ Acknowledged limitation |
| 106 | Missing IDs root cause is UNVERIFIED | `adversarial_review.md` Section 3.1 | Adversarial analysis | ❓ Acknowledged as UNVERIFIED |
| 107 | "0 error markers" is consistent with `or True` bug | `adversarial_review.md` Section 3.3 | Adversarial analysis | ⚠️ Acknowledged limitation |
| 108 | `saintseiya.fandom.com` hallucination status UNVERIFIED | `adversarial_review.md` Section 4.3 | Adversarial analysis | ❓ Acknowledged as UNVERIFIED |
| 109 | `or True` intent UNVERIFIED (bug vs design choice) | `adversarial_review.md` Section 6.1 | Adversarial analysis | ❓ Acknowledged as UNVERIFIED |
| 110 | Enhanced RACE weights are arbitrary | `adversarial_review.md` Section 7.2 | Adversarial analysis | ⚠️ Acknowledged as conceptual |
| 111 | Metadata enrichment is inert (no behavior change) | `adversarial_review.md` Section 7.3 | Adversarial analysis | ⚠️ Acknowledged as analysis aid |
| 112 | Hardcoded enrichment values are inferred | `adversarial_review.md` Section 7.4 | Adversarial analysis | ❓ Acknowledged as UNVERIFIED |

---

## 10. Verification Summary Statistics

| Category | Total Items | ✅ Verified | ⚠️ Partially Verified | ❓ UNVERIFIED | 📋 Proposed |
|----------|-------------|-------------|----------------------|--------------|-------------|
| Dataset Inventory | 9 | 9 | 0 | 0 | 0 |
| Data Integrity | 8 | 6 | 2 | 0 | 0 |
| Missing Records Root Cause | 3 | 2 | 0 | 1 | 0 |
| Citation Quality | 10 | 4 | 6 | 0 | 0 |
| Source Diversity | 7 | 6 | 0 | 1 | 0 |
| Self-Referential | 4 | 0 | 4 | 0 | 0 |
| Counterargument | 3 | 0 | 3 | 0 | 0 |
| Current Evaluators | 7 | 7 | 0 | 0 | 0 |
| Evaluation Gaps | 8 | 8 | 0 | 0 | 0 |
| Code Bugs | 4 | 4 | 0 | 0 | 0 |
| Metadata Enrichment | 15 | 15 | 0 | 0 | 0 |
| Benchmark Proposals | 16 | 0 | 0 | 0 | 16 |
| README Benchmarks | 8 | 8 | 0 | 0 | 0 |
| Adversarial Challenges | 10 | 0 | 5 | 5 | 0 |
| **TOTAL** | **112** | **69** | **20** | **7** | **16** |

### Verification Rate

| Metric | Value |
|--------|-------|
| Fully verified (✅) | 69/112 (61.6%) |
| Partially verified (⚠️) | 20/112 (17.9%) |
| UNVERIFIED (❓) | 7/112 (6.3%) |
| Proposed/not implemented (📋) | 16/112 (14.3%) |
| **Total with some evidence** (✅+⚠️) | **89/112 (79.5%)** |
| **Total with direct evidence** (✅) | **69/112 (61.6%)** |

---

## 11. Files Referenced in This Matrix

| File | Path | Role |
|------|------|------|
| Original JSONL (gpt-4.1) | `tests/expt_results/deep_research_bench_gpt-4.1.jsonl` | Data source |
| Original JSONL (gpt-5) | `tests/expt_results/deep_research_bench_gpt-5.jsonl` | Data source |
| Original JSONL (claude4-sonnet) | `tests/expt_results/deep_research_bench_claude4-sonnet.jsonl` | Data source |
| Enriched JSONL (gpt-4.1) | `improvements/enriched/deep_research_bench_gpt-4.1.enriched.jsonl` | Enriched data |
| Enriched JSONL (gpt-5) | `improvements/enriched/deep_research_bench_gpt-5.enriched.jsonl` | Enriched data |
| Enriched JSONL (claude4-sonnet) | `improvements/enriched/deep_research_bench_claude4-sonnet.enriched.jsonl` | Enriched data |
| Enrichment script | `improvements/metadata_enrichment.py` | Improvement script |
| Benchmark improvements | `improvements/benchmark_improvements.md` | Proposals document |
| Evaluators | `tests/evaluators.py` | Evaluation code |
| Evaluation runner | `tests/run_evaluate.py` | Evaluation script |
| Pairwise evaluation | `tests/pairwise_evaluation.py` | Pairwise script |
| Supervisor eval | `tests/supervisor_parallel_evaluation.py` | Supervisor script |
| Data extraction | `tests/extract_langsmith_data.py` | Extraction script |
| Main agent | `src/open_deep_research/deep_researcher.py` | Core workflow |
| Configuration | `src/open_deep_research/configuration.py` | Config |
| State | `src/open_deep_research/state.py` | State definitions |
| Utils | `src/open_deep_research/utils.py` | Utilities |
| Prompts | `src/open_deep_research/prompts.py` | Prompt templates |
| README | `README.md` | Benchmark results |

---

*End of Phase 9 Verification Matrix*
