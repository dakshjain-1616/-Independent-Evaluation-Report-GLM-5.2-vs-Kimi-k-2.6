# Phase 2: Dataset Inventory — Open Deep Research

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** Direct inspection of all data files, schema validation, cross-file consistency checks.

---

## 1. Data Asset Overview

| # | Asset | Location | Type | Records/Size | Purpose |
|---|-------|----------|------|-------------|---------|
| 1 | GPT-4.1 Results | `tests/expt_results/deep_research_bench_gpt-4.1.jsonl` | JSONL | 100 records / 1.35 MB | Experiment output for GPT-4.1 model |
| 2 | GPT-5 Results | `tests/expt_results/deep_research_bench_gpt-5.jsonl` | JSONL | 100 records / 2.11 MB | Experiment output for GPT-5 model |
| 3 | Claude4-Sonnet Results | `tests/expt_results/deep_research_bench_claude4-sonnet.jsonl` | JSONL | 98 records / 1.57 MB | Experiment output for Claude Sonnet 4 model |
| 4 | Deep Research Bench | LangSmith (external) | Dataset | 100 examples | PhD-level research tasks benchmark |
| 5 | Supervisor Parallelism | LangSmith (external) | Dataset | UNVERIFIED | Tests supervisor parallelization |
| 6 | Example Reports | `examples/` | Markdown | 3 files | Reference examples (arxiv, pubmed, inference-market) |
| 7 | Legacy Test Data | `src/legacy/tests/` | Python | 1 test case | Legacy report quality test |

---

## 2. JSONL Experiment Result Files

### 2.1 Schema

All three JSONL files share an identical schema:

```json
{
  "id": <integer>,
  "prompt": <string>,
  "article": <string>
}
```

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | int | Sequential task identifier (1-100) | From LangSmith example metadata `metadata["id"]` |
| `prompt` | str | User's research question/task | From LangSmith run input `inputs["inputs"]["messages"][0]["content"]` |
| `article` | str | Generated research report (final_report) | From LangSmith run output `outputs["final_report"]` |

**Schema consistency:** ✅ Verified — all records across all 3 files contain exactly these 3 keys. No additional fields, no missing fields.

### 2.2 File: `deep_research_bench_gpt-4.1.jsonl`

| Property | Value |
|----------|-------|
| Records | 100 |
| File size | 1,347,545 bytes (1.35 MB) |
| ID range | 1-100 (complete, no gaps) |
| Unique IDs | 100 |
| Exact duplicates | 0 |
| Model | openai:gpt-4.1 (research model) |
| Compression model | openai:gpt-4.1 |
| Final report model | openai:gpt-4.1 |
| Search API | tavily |

**Article length statistics:**
| Metric | Value (chars) |
|--------|---------------|
| Min | 3,062 |
| Max | 26,473 |
| Average | 10,387 |
| Median | 11,026 |

**Citation coverage:**
- 76/100 articles have a "Sources" section (76%)
- 24/100 articles lack a "Sources" section (24%)
- 99/100 articles use `[N]` bracket citations
- 36/100 articles use `[Title](URL)` markdown citations
- 0 articles have zero URLs

### 2.3 File: `deep_research_bench_gpt-5.jsonl`

| Property | Value |
|----------|-------|
| Records | 100 |
| File size | 2,105,328 bytes (2.11 MB) |
| ID range | 1-100 (complete, no gaps) |
| Unique IDs | 100 |
| Exact duplicates | 0 |
| Model | openai:gpt-5 (research model) |
| Compression model | openai:gpt-4.1 |
| Final report model | openai:gpt-4.1 |
| Search API | tavily |

**Article length statistics:**
| Metric | Value (chars) |
|--------|---------------|
| Min | 3,573 |
| Max | 35,896 |
| Average | 16,455 |
| Median | 15,825 |

**Citation coverage:**
- 89/100 articles have a "Sources" section (89%)
- 11/100 articles lack a "Sources" section (11%)
- 99/100 articles use `[N]` bracket citations
- 40/100 articles use `[Title](URL)` markdown citations
- 0 articles have zero URLs

### 2.4 File: `deep_research_bench_claude4-sonnet.jsonl`

| Property | Value |
|----------|-------|
| Records | 98 |
| File size | 1,574,634 bytes (1.57 MB) |
| ID range | 1-100 (**missing IDs 57 and 98**) |
| Unique IDs | 98 |
| Exact duplicates | 0 |
| Model | anthropic:claude-sonnet-4 (research model) |
| Compression model | openai:gpt-4.1 |
| Final report model | openai:gpt-4.1 |
| Search API | tavily |

**Article length statistics:**
| Metric | Value (chars) |
|--------|---------------|
| Min | 4,235 |
| Max | 24,297 |
| Average | 12,358 |
| Median | 12,306 |

**Citation coverage:**
- 87/98 articles have a "Sources" section (88.8%)
- 11/98 articles lack a "Sources" section (11.2%)
- 96/98 articles use `[N]` bracket citations
- 23/98 articles use `[Title](URL)` markdown citations
- 0 articles have zero URLs

### 2.5 Cross-File Consistency

| Check | Result |
|-------|--------|
| Prompt consistency (same ID across files) | ✅ 0 mismatches — all prompts identical |
| Schema consistency | ✅ All files use `{id, prompt, article}` |
| Cross-file near-duplicates (>50% article similarity) | ✅ 0 found (expected — different models produce different outputs) |
| ID completeness | ⚠️ gpt-4.1: complete (100/100), gpt-5: complete (100/100), claude4-sonnet: incomplete (98/100) |

---

## 3. LangSmith Datasets

### 3.1 Deep Research Bench

| Property | Value |
|----------|-------|
| Name | "Deep Research Bench" |
| URL | https://smith.langchain.com/public/c5e7a6ad-fdba-478c-88e6-3a388459ce8b/d |
| Size | 100 examples |
| Languages | 50 English, 50 Chinese |
| Domains | 22 fields (Science & Tech, Business & Finance, etc.) |
| Golden answers | Expert-compiled reference reports |
| Evaluation | RACE score (Gemini LLM-as-judge) |
| Used in | `tests/run_evaluate.py` (`dataset_name = "Deep Research Bench"`) |

**Dependencies:** Requires LangSmith API key (`LANGSMITH_API_KEY`), OpenAI API key, Tavily API key.

**Quality concerns:**
- The dataset is hosted externally on LangSmith — local copy not available in repository
- The 50/50 English/Chinese split was verified by checking prompts in JSONL files (50 Chinese prompts confirmed in each file)
- Golden answers are used only by the `eval_correctness` evaluator; the RACE score is computed externally

### 3.2 ODR: First Supervisor Parallelism

| Property | Value |
|----------|-------|
| Name | "ODR: First Supervisor Parallelism" |
| Size | UNVERIFIED (not accessible without LangSmith API) |
| Used in | `tests/supervisor_parallel_evaluation.py` |
| Schema | `{messages: [...], parallel: int}` (reference output has `parallel` field) |
| Purpose | Tests that supervisor correctly parallelizes research tasks |

**Quality concerns:**
- Dataset size and contents UNVERIFIED — not accessible without LangSmith credentials
- The evaluator checks `len(outputs["output"].values["supervisor_messages"][-1].tool_calls) == reference_outputs["parallel"]` — this verifies the count of tool calls, not the quality of parallelization

---

## 4. Example Reports

Located in `examples/` directory (referenced in CLAUDE.md):

| File | Topic | Purpose |
|------|-------|---------|
| `arxiv.md` | ArXiv research | Example research report output |
| `pubmed.md` | PubMed research | Example research report output |
| `inference-market.md` | Inference market analysis | Example research report output |

**Quality concerns:**
- These are static example files, not part of the evaluation pipeline
- UNVERIFIED: Whether these examples were generated by the current system or are manually curated
- Not used by any evaluator or test script

---

## 5. Legacy Test Data

### 5.1 `src/legacy/tests/test_report_quality.py`

| Property | Value |
|----------|-------|
| Type | pytest test with `@pytest.mark.langsmith` |
| Test query | Hardcoded MCP overview question |
| Agents tested | `legacy.graph.builder` (plan-execute) and `legacy.multi_agent.supervisor_builder` |
| Evaluator | `CriteriaGrade` (boolean grade + justification) |
| Eval model | `anthropic:claude-3-7-sonnet-latest` (default) |
| Dataset size | 1 (single hardcoded test case) |

**Quality concerns:**
- Single test case — not statistically meaningful
- Hardcoded query about MCP — not representative of diverse research tasks
- Uses legacy implementations, not the current `deep_researcher` graph
- Eval model defaults to Claude 3.7 Sonnet, different from the main eval model (gpt-4.1)

### 5.2 `src/legacy/tests/conftest.py` and `run_test.py`

Supporting files for legacy test configuration and execution. Not data assets per se.

---

## 6. Data Dependencies

```
Deep Research Bench (LangSmith)
    │
    ├── tests/run_evaluate.py
    │   ├── Uses: deep_researcher_builder, 6 evaluators
    │   ├── Requires: OPENAI_API_KEY, TAVILY_API_KEY, LANGSMITH_API_KEY
    │   └── Produces: LangSmith experiment
    │
    ├── tests/extract_langsmith_data.py
    │   ├── Input: LangSmith project name
    │   ├── Requires: LANGSMITH_API_KEY
    │   └── Produces: tests/expt_results/*.jsonl
    │
    └── tests/expt_results/*.jsonl
        ├── deep_research_bench_gpt-4.1.jsonl (100 records)
        ├── deep_research_bench_gpt-5.jsonl (100 records)
        └── deep_research_bench_claude4-sonnet.jsonl (98 records)
```

---

## 7. Quality Concerns Summary

| Concern | Affected Assets | Severity | Details |
|---------|----------------|----------|---------|
| Missing records | claude4-sonnet JSONL | 🟡 High | IDs 57, 98 missing — failed runs silently excluded by `extract_langsmith_data.py` |
| No provenance metadata | All 3 JSONL files | 🟡 High | No model config, timestamp, search API, or experiment metadata in records |
| Missing Sources section | gpt-4.1 (24%), gpt-5 (11%), claude4-sonnet (11.2%) | 🟡 High | Articles without source attribution reduce verifiability |
| Broken citation references | gpt-4.1 (20), gpt-5 (33), claude4-sonnet (16) | 🟠 Medium | Body cites [N] but source N missing from Sources section |
| Mixed citation formats | All 3 JSONL files | 🟠 Medium | Both `[N]` brackets and `[Title](URL)` markdown used inconsistently |
| External dataset dependency | Deep Research Bench, Supervisor Parallelism | 🟠 Medium | Datasets hosted on LangSmith, not version-pinned in repo |
| No data versioning | All JSONL files | 🟢 Low | No version tags, timestamps, or commit hashes in data files |
| Legacy test coverage | Legacy test data | 🟢 Low | Single hardcoded test case, not representative |

---

## 8. Data Provenance

| Data Asset | Origin | Extraction Method | Provenance Metadata Present? |
|------------|--------|-------------------|------------------------------|
| gpt-4.1 JSONL | LangSmith experiment | `extract_langsmith_data.py` | ❌ No model config, timestamp, or experiment ID |
| gpt-5 JSONL | LangSmith experiment | `extract_langsmith_data.py` | ❌ No model config, timestamp, or experiment ID |
| claude4-sonnet JSONL | LangSmith experiment | `extract_langsmith_data.py` | ❌ No model config, timestamp, or experiment ID |
| Deep Research Bench | LangSmith dataset | N/A (external) | ❌ No local copy or version pin |
| Example reports | UNVERIFIED | UNVERIFIED | ❌ No generation metadata |

**Critical gap:** None of the JSONL files contain provenance metadata. There is no way to determine from the data alone:
- Which model configuration was used (research model, compression model, etc.)
- When the experiment was run
- Which LangSmith experiment/project the data came from
- What search API was used
- What the max_concurrent_research_units setting was

This metadata must be reconstructed from `run_evaluate.py` source code and README documentation.

---

*End of Phase 2 Dataset Inventory*
