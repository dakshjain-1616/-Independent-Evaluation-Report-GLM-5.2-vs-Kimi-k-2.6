# Evaluation Audit

## Executive Summary

This audit analyzes the six primary evaluators in `tests/evaluators.py`, the evaluation prompts in `tests/prompts.py`, and the supplementary evaluation scripts (`pairwise_evaluation.py`, `supervisor_parallel_evaluation.py`). It identifies coverage gaps, silent fake success modes, missing dimensions, and structural risks that allow low-quality or hallucinated outputs to receive high scores.

**Critical Finding**: The evaluation system has **no hallucination-specific dimension**, **no source traceability validator**, and **no counterargument coverage check**. The `eval_groundedness` evaluator has a **silent failure mode** when `raw_notes` is missing. The `eval_correctness` evaluator has a **silent skip mode** when reference answers are absent. All evaluators share a **single-judge bias** from hardcoded `gpt-4.1`.

---

## 1. Evaluator Inventory

### 1.1 Primary Evaluators (`tests/evaluators.py`)

| Evaluator | Function | Scale | Inputs Required | Weight (in overall) |
|-----------|----------|-------|-----------------|---------------------|
| `eval_overall_quality` | 6-dimension weighted scoring | 1–5 per dimension | `outputs["final_report"]` | N/A (standalone) |
| `eval_relevance` | Section-by-section relevance | 1–5 + reasoning | `outputs["final_report"]` | N/A |
| `eval_structure` | Format, flow, citations | 1–5 + reasoning | `outputs["final_report"]` | N/A |
| `eval_correctness` | Accuracy vs authority | 1–5 + reasoning | `outputs["final_report"]` + `reference_outputs["answer"]` | N/A |
| `eval_groundedness` | Claims vs raw_notes | Ratio (grounded/total) | `outputs["final_report"]` + `outputs["raw_notes"]` | N/A |
| `eval_completeness` | Coverage of research_brief | 1–5 + reasoning | `outputs["final_report"]` + `outputs["research_brief"]` | N/A |

### 1.2 Supplementary Evaluators

| Evaluator | File | Purpose | Risk |
|-----------|------|---------|------|
| Head-to-head ranking | `pairwise_evaluation.py` | Compares two experiments on source quality and comprehensiveness | **Executes on module import** (active `evaluate_comparative` call) |
| Free-for-all ranking | `pairwise_evaluation.py` | Ranks multiple experiments | Same import-time execution risk |
| Parallelism check | `supervisor_parallel_evaluation.py` | Verifies `max_concurrent_research_units` tool call count | **Fragile attribute access**: `outputs["output"].values["supervisor_messages"][-1].tool_calls` |

### 1.3 Legacy Evaluators

| Evaluator | File | Purpose | Scale |
|-----------|------|---------|-------|
| `test_response_criteria_evaluation` | `src/legacy/tests/test_report_quality.py` | 9-dimension binary pass/fail | Boolean (`CriteriaGrade`) |

---

## 2. Coverage Analysis

### 2.1 Dimensions Covered

```
Evaluated Dimensions:
├── Research depth (overall_quality)
├── Source quality (overall_quality)
├── Analytical rigor (overall_quality)
├── Practical value (overall_quality)
├── Balance and objectivity (overall_quality)
├── Writing quality (overall_quality)
├── Relevance (eval_relevance)
├── Structure (eval_structure)
├── Correctness (eval_correctness)
├── Groundedness (eval_groundedness)
└── Completeness (eval_completeness)
```

### 2.2 Dimensions NOT Covered

| Missing Dimension | Why It Matters | Impact |
|-------------------|----------------|--------|
| **Hallucination risk** | No explicit check for fabricated facts, fake citations, or invented statistics | High-scoring reports may contain entirely fabricated content |
| **Source traceability** | No validation that every claim can be traced to a source URL | Readers cannot verify claims; undermines trust |
| **Citation-source correspondence** | `eval_structure` checks formatting, not whether `[N]` maps to a real source entry | Dangling citations receive no penalty |
| **Counterargument coverage** | `balance_and_objectivity` is a broad 1–5 dimension with no explicit counterargument requirement | Reports can score well while presenting one-sided narratives |
| **Quantitative claim verification** | No check that numbers, percentages, or dates are sourced | Hallucinated statistics go undetected |
| **Recency of sources** | No check on publication dates or temporal relevance | Outdated information may receive high scores |
| **Cross-lingual consistency** | No evaluator for Chinese prompt/English report mismatches | 50% of benchmark is Chinese; quality may vary |
| **Token/cost efficiency** | No evaluation of research efficiency | High scores may come from excessive token usage |
| **Reproducibility** | No check that rerunning the same prompt yields similar results | Non-determinism is invisible to evaluators |
| **Adversarial robustness** | No check for performance on misleading or ambiguous prompts | System may fail silently on edge cases |

### 2.3 Coverage Heatmap

| Quality Aspect | overall_quality | relevance | structure | correctness | groundedness | completeness |
|----------------|---------------|-----------|-----------|-------------|--------------|--------------|
| Factual accuracy | Partial | No | No | **Yes** | Partial | No |
| Source attribution | Partial | No | Partial | No | Partial | No |
| Citation integrity | No | No | Partial | No | No | No |
| Balanced perspective | Partial | No | No | No | No | No |
| Logical structure | Partial | No | **Yes** | No | No | No |
| Topic coverage | No | **Yes** | No | No | No | **Yes** |
| Writing clarity | **Yes** | No | Partial | No | No | No |
| Hallucination detection | No | No | No | No | No | No |
| Counterarguments | No | No | No | No | No | No |
| Source traceability | No | No | No | No | No | No |

**Coverage Score**: ~45% of critical quality dimensions are unmeasured.

---

## 3. Silent Fake Success Modes

A "silent fake success" occurs when an evaluator returns a passing or high score despite a critical quality failure, without raising an error or warning.

### 3.1 eval_groundedness: The Missing Context Trap

**Code Pattern** (`tests/evaluators.py`):
```python
def eval_groundedness(inputs, outputs):
    claims = extract_claims(outputs["final_report"])
    context = outputs["raw_notes"]  # ← No validation that key exists
    # ... checks grounding against context
    return {"groundedness_ratio": grounded / total}
```

**Silent Failure Scenarios**:

| Scenario | Behavior | Score Impact |
|----------|----------|--------------|
| `raw_notes` key missing | `KeyError` raised (not silent — crashes evaluator) | Evaluation fails |
| `raw_notes` is empty string `""` | Claims checked against empty context; all claims appear ungrounded | **groundedness_ratio = 0.0** (correctly bad) |
| `raw_notes` is truncated/meaningless | Claims checked against garbage context; random grounding | **Arbitrary ratio** (unreliable) |
| `raw_notes` contains only search result snippets | Claims may be "grounded" in snippets that are themselves unverified | **False confidence** |

**Root Cause**: The evaluator assumes `raw_notes` is a faithful, complete representation of retrieved evidence. It does not:
- Verify that `raw_notes` is non-empty
- Check that `raw_notes` contains actual source content vs. placeholder text
- Validate that sources in `raw_notes` are authoritative

**Fake Success Example**: A report with 50 claims and 30 citations receives `groundedness_ratio = 0.9` because 45 claims match words in `raw_notes`. However, `raw_notes` may be a jumble of unverified search snippets. The score looks good but proves nothing about external validity.

### 3.2 eval_correctness: The Missing Reference Trap

**Code Pattern**:
```python
def eval_correctness(inputs, outputs, reference_outputs):
    answer = reference_outputs["answer"]  # ← Required but not guaranteed present
    # ... compares report to answer
```

**Silent Failure Scenarios**:

| Scenario | Behavior | Score Impact |
|----------|----------|--------------|
| `reference_outputs["answer"]` missing | `KeyError` raised (crashes) | Evaluation fails |
| `reference_outputs["answer"]` is vague or incomplete | Report compared to low-quality reference | **Arbitrary score** |
| `reference_outputs["answer"]` is itself hallucinated | Report compared to fabricated ground truth | **Inverted quality signal** |

**Root Cause**: The Deep Research Bench has 22 fields per task, but it is **unverified** whether all 100 tasks have authoritative reference answers. If the benchmark lacks reference answers for some tasks, `eval_correctness` cannot run, creating a coverage gap.

### 3.3 eval_overall_quality: The Plausible Writing Trap

**Code Pattern**: Six 1–5 dimensions scored by `gpt-4.1` with weighted average.

**Silent Failure Scenarios**:

| Scenario | Behavior | Score Impact |
|----------|----------|--------------|
| Report is well-written but factually wrong | `writing_quality` and `analytical_rigor` may still score 4–5 | **High overall score masks factual errors** |
| Report uses confident tone for fabricated claims | `research_depth` and `source_quality` may score high based on citation count alone | **False confidence** |
| Report omits major counterarguments | `balance_and_objectivity` is a broad dimension; may still score 3–4 | **One-sided narrative passes** |
| Report cites non-existent sources | `source_quality` cannot verify URL accessibility | **Fake sources score well** |

**Root Cause**: `gpt-4.1` as a judge evaluates surface features (writing style, structure, citation density) more reliably than deep factual accuracy. It has no access to external search or ground truth databases during evaluation.

### 3.4 eval_structure: The Format-Over-Substance Trap

**Code Pattern**: Checks logical flow, formatting, and citation practices.

**Silent Failure Scenario**:
- Report has perfect markdown structure, proper headers, and a `### Sources` section.
- `eval_structure` scores 5/5.
- However, the Sources section contains **404 URLs** or **URLs that do not support the claims**.
- The evaluator has no mechanism to verify URL accessibility or claim-source alignment.

**Root Cause**: Structure evaluation is syntactic, not semantic.

### 3.5 eval_relevance: The Section-Level Blind Spot

**Code Pattern**: Section-by-section relevance analysis.

**Silent Failure Scenario**:
- Report contains 10 sections, all superficially related to the topic.
- `eval_relevance` scores 4/5 per section.
- However, 3 sections are **generic filler** (e.g., "Market Overview" for any industry report) with no specific connection to the prompt.
- The evaluator cannot distinguish between *specific* relevance and *generic* relevance.

### 3.6 eval_completeness: The Brief-Dependent Trap

**Code Pattern**: Compares report against `outputs["research_brief"]`.

**Silent Failure Scenario**:
- `research_brief` is generated by the model itself (`write_research_brief` node).
- If the brief is **incomplete or misaligned** with the user's true intent, `eval_completeness` measures adherence to a flawed plan.
- A report that perfectly follows a bad brief scores 5/5 on completeness while failing the user.

**Root Cause**: Circular dependency — the brief is both input to research and reference for evaluation.

### 3.7 pairwise_evaluation.py: The Import-Time Execution Trap

**Code Pattern**:
```python
# At module level, NOT guarded by if __name__ == "__main__"
results = evaluate_comparative(...)
```

**Silent Failure Scenario**:
- Any import of `pairwise_evaluation.py` (e.g., by an IDE, test runner, or dependency scanner) triggers a live LangSmith evaluation.
- This consumes API credits, creates unwanted experiment entries, and may fail if credentials are missing.
- The failure is "silent" in the sense that it is unexpected and unlogged by the importing process.

### 3.8 supervisor_parallel_evaluation.py: The Fragile Attribute Trap

**Code Pattern**:
```python
tool_calls = outputs["output"].values["supervisor_messages"][-1].tool_calls
```

**Silent Failure Scenario**:
- If `outputs["output"]` changes from a dict to a Pydantic model, `.values` may become a method or property, breaking the chain.
- If `supervisor_messages` is empty, `[-1]` raises `IndexError`.
- If the schema version changes, the nested path may no longer exist.
- These failures crash the evaluator rather than returning a graceful "unable to evaluate" score.

---

## 4. Missing Evaluation Dimensions

### 4.1 Critical Missing Dimensions

| Dimension | Description | Proposed Implementation |
|-----------|-------------|------------------------|
| **Hallucination Risk Score** | Probability that a claim is fabricated | Extract claims → verify against retrieved sources → flag unsupported claims |
| **Source Traceability Score** | Percentage of claims with resolvable source URLs | Parse citations → check URL accessibility → verify claim-source alignment |
| **Counterargument Coverage** | Presence and depth of limitations, dissent, or alternative views | Detect signal words + require dedicated subsection |
| **Quantitative Claim Verification** | Percentage of numbers/dates with citations | Regex extract numbers → check for adjacent `[N]` citation |
| **Temporal Relevance** | Average age of cited sources | Extract dates from URLs/source text → compute recency |
| **Cross-Lingual Fidelity** | For Chinese prompts: assess report language match and cultural accuracy | Detect language of report vs. prompt → flag mismatches |
| **Adversarial Robustness** | Performance on intentionally ambiguous or misleading prompts | Add adversarial test cases to benchmark |
| **Cost-Efficiency Score** | Quality per token / per dollar | Divide RACE score by token count or cost |
| **Reproducibility Score** | Variance across multiple runs of same prompt | Run N times → compute report similarity / score variance |
| **Cognitive Bias Detection** | Presence of anchoring, confirmation bias, or availability heuristic | Analyze claim ordering, source diversity, counterargument presence |

### 4.2 Why These Matter

**Hallucination Risk**: The most dangerous failure mode in research agents. Current evaluators measure *style* and *structure* but not *truth*. A report with perfect structure and zero factual accuracy could score 4.5/5 on overall_quality.

**Source Traceability**: Research is only as good as its sources. If readers cannot verify claims, the report is opinion, not research. Current evaluators check that citations *exist* but not that they *work*.

**Counterargument Coverage**: Real research acknowledges uncertainty. The current "balance_and_objectivity" dimension (15% weight) is too broad and too subjective to enforce this.

---

## 5. Structural Risks

### 5.1 Single-Judge Bias

All 6 primary evaluators use the **same model** (`ChatOpenAI(model="gpt-4.1")`) with the **same temperature** (default, likely ~0.7) and **same system prompts**.

**Risks**:
- **Correlated errors**: If `gpt-4.1` systematically misjudges a certain claim type (e.g., medical statistics), all evaluators share that blind spot.
- **No inter-rater reliability**: Cannot compute Cohen's kappa or similar metrics because there is only one judge.
- **Model drift**: As `gpt-4.1` ages or is updated, evaluation behavior may shift without warning.
- **No ensemble**: No majority voting or confidence-weighted aggregation across multiple judges.

### 5.2 Hardcoded Configuration

| Hardcoded Value | Location | Risk |
|-----------------|----------|------|
| `eval_model = ChatOpenAI(model="gpt-4.1")` | `tests/evaluators.py` | Cannot switch to newer/better/cheaper judge models without code edit |
| `research_model = "openai:gpt-5"` | `tests/run_evaluate.py` | Experiment config is not parameterized |
| `max_concurrent_research_units = 10` | `tests/run_evaluate.py` | Overrides default (5) without justification |
| `allow_clarification = False` | `tests/run_evaluate.py` | Disables clarification step, potentially reducing report quality |
| `dataset_name = "Deep Research Bench"` | `tests/run_evaluate.py` | Hardcoded dataset name |

### 5.3 No Calibration Dataset

The 1–5 scales used by evaluators have **no anchor examples**:
- What does a "3" in `research_depth` look like?
- What is the difference between a "4" and a "5" in `analytical_rigor`?
- Without calibration examples, scores are subjective and non-transferable across evaluation runs.

### 5.4 No Statistical Aggregation

Evaluation results are logged per-example to LangSmith but there is **no documented methodology** for:
- Computing confidence intervals on RACE scores
- Handling missing evaluations (e.g., `eval_correctness` skips)
- Weighting dimensions beyond the fixed `overall_quality` weights
- Normalizing across English and Chinese tasks

---

## 6. Recommendations

### 6.1 Immediate Fixes

1. **Guard `eval_groundedness`**: Add explicit check for `outputs.get("raw_notes")` and return `{"error": "raw_notes missing"}` instead of crashing or computing meaningless ratios.
2. **Guard `eval_correctness`**: Return `{"error": "reference answer missing"}` when `reference_outputs["answer"]` is absent, rather than crashing.
3. **Guard `pairwise_evaluation.py`**: Wrap `evaluate_comparative` in `if __name__ == "__main__":` to prevent import-time execution.
4. **Fix `supervisor_parallel_evaluation.py`**: Replace fragile nested attribute access with defensive parsing using `.get()` and `try/except`.

### 6.2 New Evaluators

5. **Add `eval_hallucination_risk`**: Extract claims from report, check against retrieved sources and external knowledge base, return risk score (0–1).
6. **Add `eval_source_traceability`**: Parse all `[N]` citations, verify each has a matching source entry, check URL accessibility (HTTP 200), return traceability percentage.
7. **Add `eval_counterargument_coverage`**: Detect signal words + check for dedicated "Limitations" or "Criticisms" subsection, return coverage score.
8. **Add `eval_quantitative_verification`**: Extract numbers/dates, verify each has adjacent citation, return verification percentage.

### 6.3 Structural Improvements

9. **Parameterize eval_model**: Read judge model from environment variable or config, defaulting to `gpt-4.1` but allowing override.
10. **Add ensemble judging**: Run 3+ judge models (e.g., `gpt-4.1`, `claude-sonnet-4`, `gemini-1.5-pro`) and aggregate scores via median or trimmed mean.
11. **Create calibration dataset**: Curate 20 anchor examples with expert-annotated scores for each dimension to calibrate judge models.
12. **Add statistical reporting**: Compute mean, std, min, max, and 95% CI for each dimension across the benchmark.

---

*Generated as part of Phase 5: Evaluation Audit. Analysis based on direct inspection of `tests/evaluators.py`, `tests/prompts.py`, `tests/pairwise_evaluation.py`, and `tests/supervisor_parallel_evaluation.py`.*
