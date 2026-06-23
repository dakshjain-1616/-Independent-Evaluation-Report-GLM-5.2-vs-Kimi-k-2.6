# Phase 5: Evaluation Audit — Open Deep Research

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** Direct inspection of `tests/evaluators.py`, `tests/prompts.py`, `tests/run_evaluate.py`, `tests/pairwise_evaluation.py`, `tests/supervisor_parallel_evaluation.py`, and `tests/extract_langsmith_data.py`.

---

## 1. Executive Summary

The evaluation framework consists of **6 LLM-as-a-judge evaluators**, **1 pairwise evaluator** (2-way and 3-way), and **1 supervisor parallelism evaluator**. The framework measures report quality across multiple dimensions but has significant coverage gaps — it does not detect hallucinations, broken citations, missing sources, self-referential language, or silent failures.

---

## 2. What IS Measured

### 2.1 The Six Evaluators (`tests/evaluators.py`)

| # | Evaluator | Function | Score Model | Scale | Uses Reference? | What It Measures |
|---|----------|----------|------------|-------|-----------------|------------------|
| 1 | Overall Quality | `eval_overall_quality` | `OverallQualityScore` (6 sub-scores) | 0.0–1.0 | No | research_depth, source_quality, analytical_rigor, practical_value, balance_and_objectivity, writing_quality |
| 2 | Relevance | `eval_relevance` | `RelevanceScore` | 0.0–1.0 | No | Section-by-section relevance to user question |
| 3 | Structure | `eval_structure` | `StructureScore` | 0.0–1.0 | No | Format, flow, structural elements |
| 4 | Correctness | `eval_correctness` | `CorrectnessScore` | 0.0–1.0 | **Yes** (answer) | Accuracy vs. golden answer |
| 5 | Groundedness | `eval_groundedness` | `GroundednessScore` (claim-level) | 0.0–1.0 | No (uses `raw_notes`) | Claims grounded in research notes |
| 6 | Completeness | `eval_completeness` | `CompletenessScore` | 0.0–1.0 | No (uses `research_brief`) | Coverage of user question and research brief |

**Scoring normalization:** All scores are normalized to 0.0–1.0 by dividing the raw score (1–5) by 5.

### 2.2 Overall Quality Sub-Dimensions

The `OverallQualityScore` model produces 6 sub-scores, each on a 1–5 scale:

| Sub-Dimension | What It Evaluates |
|---------------|-------------------|
| research_depth | Depth of research, multiple sources, thoroughness |
| source_quality | Quality and credibility of sources |
| analytical_rigor | Quality of analysis, synthesis, reasoning |
| practical_value | Actionable insights, practical recommendations |
| balance_and_objectivity | Balanced presentation, multiple viewpoints |
| writing_quality | Clarity, coherence, grammar, formatting |

**Note:** The `OVERALL_QUALITY_PROMPT` mentions "Does not refer to itself as the writer" in 2 of the 6 dimensions (writing_quality and balance_and_objectivity), but this is a soft criterion buried in a rubric, not a dedicated check.

### 2.3 Pairwise Evaluation (`tests/pairwise_evaluation.py`)

| Evaluator | Function | Comparison | Judge Model | Output |
|-----------|----------|------------|-------------|--------|
| Head-to-head | `head_to_head_evaluator` | 2 implementations | `claude-opus-4-20250514` (thinking, 16000 budget) | `HeadToHeadRanking` (1st/2nd) |
| Three-way | `free_for_all_evaluator` | 3 implementations | `claude-opus-4-20250514` (thinking, 16000 budget) | `Rankings` (1st=1.0, 2nd=0.5, 3rd=0.0) |

**Purpose:** Relative comparison of different agent architectures (single_agent, multi_agent_supervisor, multi_agent_workflow, etc.).

### 2.4 Supervisor Parallelism (`tests/supervisor_parallel_evaluation.py`)

| Evaluator | Function | What It Checks |
|-----------|----------|----------------|
| Right Parallelism | `right_parallelism_evaluator` | `len(outputs["output"].values["supervisor_messages"][-1].tool_calls) == reference_outputs["parallel"]` |

**Purpose:** Verifies the supervisor delegates the correct number of parallel research tasks.

---

## 3. What is NOT Measured

### 3.1 Critical Coverage Gaps

| Gap | Impact | Evidence |
|-----|--------|---------|
| **No hallucination evaluator** | Fabricated sources, URLs, or claims are undetected | No evaluator checks if cited URLs are real or if sources exist |
| **No citation completeness check** | 11–24% of articles lack Sources section; undetected | No evaluator verifies Sources section presence |
| **No broken citation detection** | 16–33% have orphaned [N] citations; undetected | No evaluator checks body citations against Sources section |
| **No source traceability** | Claims cannot be traced to specific sources | Groundedness uses `raw_notes` (bulk context), not per-claim source mapping |
| **No self-referential language check** | 1.7% of articles violate "do not refer to yourself" | Mentioned in quality rubric but no dedicated evaluator |
| **No silent failure detection** | Failed runs silently excluded from data | `extract_langsmith_data.py` drops runs without `final_report` |
| **No source diversity check** | Reports may cite from narrow set of sources | No evaluator counts unique source domains |
| **No counterargument check** | 6–13% contain counterargument language | No evaluator checks for opposing viewpoints |
| **No language consistency check** | UNVERIFIED if evaluator catches language mismatches | No evaluator explicitly checks prompt language vs. article language |
| **No URL validity check** | URLs may be broken or fabricated | No evaluator performs HTTP checks on cited URLs |
| **No bias detection** | One-sided reports undetected | No evaluator checks for viewpoint balance |
| **No cost/efficiency evaluation** | Cost and token usage not scored | Reported in README but not part of evaluation framework |

### 3.2 Groundedness Evaluator Limitations

The `eval_groundedness` evaluator is the closest to a hallucination check, but it has fundamental limitations:

**How it works:**
1. Extracts claims from the report using an LLM
2. Checks each claim against `raw_notes` (the raw search/tool output context)
3. Scores each claim as grounded (1.0) or not (0.0)
4. Returns the ratio of grounded claims

**Limitations:**
- `raw_notes` is the **entire bulk search output** — not individual sources. A claim can be "grounded" in raw notes without being properly cited or traceable to a specific source.
- Does not verify that the citation `[N]` actually refers to the source that supports the claim.
- Does not check if cited URLs are real or accessible.
- Does not detect fabricated claims that happen to resemble the raw notes text.
- The evaluator requires `raw_notes` in the output — but the JSONL experiment files only contain `{id, prompt, article}`. The `raw_notes` is not preserved, making retrospective groundedness evaluation impossible from the stored data.

### 3.3 Correctness Evaluator Limitations

The `eval_correctness` evaluator compares the report against a golden answer:

**Limitations:**
- Uses `reference_outputs["answer"]` — the golden answer from the Deep Research Bench dataset
- The golden answer is an expert-compiled reference report, not a ground-truth fact set
- LLM-as-a-judge comparison of two long reports is subjective and may not catch factual errors
- Does not check specific factual claims — only overall correctness impression
- Does not verify citations in the report against the golden answer's citations

---

## 4. Evaluation Infrastructure Issues

### 4.1 Hardcoded Eval Model

**File:** `tests/evaluators.py`
```python
eval_model = ChatOpenAI(model="gpt-4.1")
```

**Issue:** The evaluation judge model is hardcoded to `gpt-4.1` with no environment variable or parameter override.

**Impact:**
- Cannot use a different judge model without editing source code
- The same model (gpt-4.1) is used as both the research model (in default config) and the judge — potential self-bias
- The RACE score (external benchmark) uses Gemini as judge, but the internal evaluators use gpt-4.1 — these are different methodologies

### 4.2 Hardcoded Experiment Names in Pairwise

**File:** `tests/pairwise_evaluation.py` (bottom of file)
```python
single_agent = "DR Single Agent - Tavily #-87e8a6c0"
multi_agent_supervisor = "DR Supervisor: Multi Agent - Tavily #-..."
multi_agent_supervisor_v2 = "DR Supervisor: Multi Agent - Tavily (v2) #-40967f53"
multi_agent_workflow = "..."
```

**Issue:** Experiment names are hardcoded at the bottom of the file, and `evaluate_comparative()` is called on import.

**Impact:**
- Script is not reusable without editing source code
- Experiment names include LangSmith run IDs that may change
- Running the script imports and executes the evaluation immediately

### 4.3 Config Mismatch in run_evaluate.py

**File:** `tests/run_evaluate.py`
```python
config = {
    "research_model": "openai:gpt-5",
    "compression_model_max_tokens": 10000,
    ...
}
```

**Issue:** `compression_model_max_tokens` is set to 10000 in the evaluation config, but the `configuration.py` default is 8192.

**Impact:** Evaluation runs use a different configuration than the default, potentially affecting results. The compression model can produce longer outputs during evaluation than in production.

### 4.4 Missing Model Token Limit

**File:** `src/open_deep_research/utils.py`

`MODEL_TOKEN_LIMITS` is missing `openai:gpt-5`, which is used as `research_model` in `run_evaluate.py`.

**Impact:** When GPT-5 hits a token limit, the retry logic in `final_report_generation` fails with: "Token limit exceeded, however, we could not determine the model's maximum context length." The retry cannot truncate messages appropriately.

### 4.5 Data Extraction Silent Failures

**File:** `tests/extract_langsmith_data.py`

```python
for run in output_runs:
    if run.outputs is not None and run.outputs.get("final_report") is not None:
        runs.append(run)
```

**Issue:** Failed runs (no `final_report`) are silently excluded. No count, no warning, no log.

**Impact:** The claude4-sonnet file is missing IDs 57 and 98 — these failed runs were silently dropped. The extraction script provides no visibility into failure rates.

---

## 5. Evaluation Failure Modes

### 5.1 LLM-as-a-Judge Reliability

All 6 evaluators use LLM-as-a-judge with gpt-4.1. Known failure modes:

| Failure Mode | Risk | Mitigation Present? |
|--------------|------|---------------------|
| Judge bias toward same-model outputs | 🟠 Medium | No — gpt-4.1 judges gpt-4.1 outputs |
| Judge inconsistency across runs | 🟠 Medium | No — no repeated runs or variance checks |
| Judge position bias (in pairwise) | 🟢 Low | Yes — pairwise uses position swapping |
| Judge length bias (longer = better) | 🟠 Medium | No — no length normalization |
| Judge verbosity bias | 🟠 Medium | No — no verbosity controls |

### 5.2 Score Interpretation Issues

- All scores are normalized to 0.0–1.0 but represent 1–5 Likert scales divided by 5
- A score of 0.2 means "1/5" (very poor) but appears as a low number, potentially misleading
- No standard deviation or confidence intervals reported
- No inter-rater reliability (IRR) checks — only one judge per evaluation

### 5.3 Missing Intermediate State Evaluation

The evaluators score only the **final report** (`outputs["final_report"]`). They do not evaluate:
- Quality of the research brief (`research_brief`)
- Quality of individual researcher outputs (`compressed_research`)
- Quality of the supervisor's delegation strategy
- Efficiency of the research process (token usage, cost, time)

**Exception:** The `eval_groundedness` evaluator uses `raw_notes` and `eval_completeness` uses `research_brief`, but these are inputs to the final report evaluation, not standalone evaluations of intermediate quality.

---

## 6. Coverage Gap Matrix

| Quality Dimension | Measured? | Evaluator | Gap |
|-------------------|-----------|-----------|-----|
| Research depth | ✅ Yes | overall_quality (sub-score) | Soft LLM judgment |
| Source quality | ✅ Yes | overall_quality (sub-score) | No programmatic verification |
| Analytical rigor | ✅ Yes | overall_quality (sub-score) | Soft LLM judgment |
| Practical value | ✅ Yes | overall_quality (sub-score) | Soft LLM judgment |
| Balance/objectivity | ✅ Yes | overall_quality (sub-score) | No counterargument check |
| Writing quality | ✅ Yes | overall_quality (sub-score) | Soft LLM judgment |
| Relevance | ✅ Yes | eval_relevance | Section-level only |
| Structure | ✅ Yes | eval_structure | Format only, not logical structure |
| Correctness | ✅ Yes | eval_correctness | vs. golden answer, not fact-checking |
| Groundedness | ✅ Yes | eval_groundedness | Uses bulk raw_notes, not per-claim |
| Completeness | ✅ Yes | eval_completeness | vs. research_brief, not user intent |
| Hallucination | ❌ No | — | No evaluator |
| Citation completeness | ❌ No | — | No evaluator |
| Citation traceability | ❌ No | — | No evaluator |
| Source diversity | ❌ No | — | No evaluator |
| Counterargument presence | ❌ No | — | No evaluator |
| Self-referential language | ❌ No | — | Mentioned in rubric, no dedicated check |
| Silent failure detection | ❌ No | — | No evaluator |
| URL validity | ❌ No | — | No evaluator |
| Language consistency | ❌ No | — | No evaluator |
| Cost/efficiency | ❌ No | — | Reported in README, not scored |
| Bias detection | ❌ No | — | No evaluator |

---

## 7. Evaluation vs. RACE Score Comparison

| Aspect | Internal Evaluators | RACE Score (External) |
|--------|---------------------|----------------------|
| Judge model | gpt-4.1 | Gemini |
| Dataset | Deep Research Bench (100 tasks) | Deep Research Bench (100 tasks) |
| Methodology | 6 LLM-as-a-judge evaluators | UNVERIFIED — external implementation |
| Scores | 0.0–1.0 per dimension | Single RACE score |
| Golden answers | Used by correctness evaluator | Used as reference |
| Citation checking | ❌ No | UNVERIFIED |
| Hallucination check | ❌ No | UNVERIFIED |

**⚠️ Critical note:** The RACE score and the internal evaluators are **different evaluation methodologies** using different judge models. They should not be conflated. The README reports RACE scores; the internal evaluators are a separate framework.

---

## 8. Recommendations for New Evaluators

Based on the coverage gaps identified, the following new evaluators are needed:

| Proposed Evaluator | What It Would Check | Priority |
|--------------------|---------------------|----------|
| `eval_citation_completeness` | Sources section present; all body [N] citations have source entries | 🔴 High |
| `eval_hallucination_risk` | Cited URLs are valid; sources support claims; no fabricated references | 🔴 High |
| `eval_source_diversity` | Unique source domains; perspective diversity | 🟡 High |
| `eval_counterargument` | Presence of opposing viewpoints | 🟠 Medium |
| `eval_self_referential` | No "I/me/my" self-references | 🟠 Medium |
| `eval_language_consistency` | Article language matches prompt language | 🟠 Medium |
| `eval_silent_failure` | No error markers; article length above threshold | 🟡 High |
| `eval_traceability` | Each claim traceable to a specific source | 🟡 High |

---

*End of Phase 5 Evaluation Audit*
