# Phase 6: Benchmark Improvements — Proposed New Evaluation Dimensions

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** Based on gaps identified in Phases 3–5, this document proposes new evaluation dimensions and documents the metadata enrichment implementation.

---

## 1. Metadata Enrichment Implementation

### 1.1 Script: `improvements/metadata_enrichment.py`

**Purpose:** Adds provenance and quality-signal metadata to the 3 JSONL experiment result files.

**Input:** `tests/expt_results/deep_research_bench_*.jsonl` (original files with `{id, prompt, article}`)

**Output:** `improvements/enriched/deep_research_bench_*.enriched.jsonl` (enriched files with 14 additional fields)

### 1.2 Enriched Schema

Each enriched record contains the original 3 fields plus 14 new metadata fields:

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `id` | int | Original | Task identifier |
| `prompt` | str | Original | User research question |
| `article` | str | Original | Generated report |
| `model` | str | **Added** | Research model used (e.g., `openai:gpt-4.1`) |
| `search_api` | str | **Added** | Search API used (e.g., `tavily`) |
| `enrichment_timestamp` | str | **Added** | ISO timestamp of enrichment |
| `language` | str | **Added** | Detected article language (`en`/`zh`) |
| `prompt_language` | str | **Added** | Detected prompt language |
| `article_length` | int | **Added** | Character count of article |
| `has_sources_section` | bool | **Added** | Whether Sources section is present |
| `citation_count` | int | **Added** | Number of `[N]` citations in body |
| `broken_citation_count` | int | **Added** | Body citations missing from Sources |
| `url_count` | int | **Added** | Total URLs in article |
| `unique_source_domains` | int | **Added** | Count of unique URL domains |
| `top_domains` | list | **Added** | Top 5 URL domains |
| `has_self_referential_language` | bool | **Added** | Self-referential violation flag |
| `has_error_markers` | bool | **Added** | Error message presence flag |

### 1.3 Enrichment Results

| File | Records In | Records Out | Has Sources | Broken Citations | Self-Ref | Errors |
|------|-----------|-------------|-------------|-----------------|----------|--------|
| gpt-4.1 | 100 | 100 | 76 (76%) | 20 (20%) | 2 (2%) | 0 |
| gpt-5 | 100 | 100 | 89 (89%) | 33 (33%) | 1 (1%) | 0 |
| claude4-sonnet | 98 | 98 | 87 (88.8%) | 16 (16.3%) | 2 (2%) | 0 |
| **Total** | **298** | **298** | **252 (84.6%)** | **69 (23.2%)** | **5 (1.7%)** | **0** |

**Verification:** All 298 records were successfully enriched. Quality signal counts match the Phase 3 integrity audit exactly, confirming the enrichment script's correctness.

### 1.4 Files Produced

```
improvements/
├── metadata_enrichment.py                              (enrichment script)
├── benchmark_improvements.md                           (this document)
└── enriched/
    ├── deep_research_bench_gpt-4.1.enriched.jsonl      (100 records)
    ├── deep_research_bench_gpt-5.enriched.jsonl        (100 records)
    └── deep_research_bench_claude4-sonnet.enriched.jsonl (98 records)
```

---

## 2. Proposed New Evaluation Dimensions

Based on the coverage gaps identified in Phase 5, the following 8 new evaluation dimensions are proposed. Each is designed to address a specific, measurable gap in the current evaluation framework.

### 2.1 Citation Completeness Evaluator

**Gap addressed:** 11–24% of articles lack Sources sections; 16–33% have broken citation references.

**What it measures:**
- Presence of a Sources section (binary: 0 or 1)
- Fraction of body `[N]` citations that have corresponding source entries (0.0–1.0)
- Citation numbering sequentiality (no gaps in [1,2,3,...N])

**Implementation approach:**
```python
def eval_citation_completeness(run, example):
    article = run.outputs["final_report"]
    has_sources = check_sources_section(article)  # bool
    body_citations = extract_body_citations(article)  # set of ints
    source_citations = extract_source_citations(article)  # set of ints
    coverage = len(body_citations & source_citations) / max(len(body_citations), 1)
    return {"score": coverage if has_sources else 0.0, 
            "has_sources": has_sources}
```

**Why it's needed:** No current evaluator detects the 20–33% broken citation rate. This is a programmatic check (not LLM-as-a-judge) — deterministic and reproducible.

### 2.2 Hallucination Risk Evaluator

**Gap addressed:** No evaluator checks for fabricated sources, URLs, or claims.

**What it measures:**
- URL validity (HTTP HEAD check on cited URLs — sample of N URLs per article)
- Source-claim alignment (LLM checks if cited source supports the claim)
- Fabricated reference detection (body cites [N] but no source N exists → hallucination flag)

**Implementation approach:**
```python
def eval_hallucination_risk(run, example):
    article = run.outputs["final_report"]
    # Programmatic: check for orphaned citations
    orphaned = count_broken_citations(article)
    # LLM-based: check if claims match cited sources
    claims = extract_claims(article)
    hallucination_score = llm_check_claims_vs_sources(claims, article)
    return {"score": hallucination_score, "orphaned_citations": orphaned}
```

**Why it's needed:** The groundedness evaluator uses bulk `raw_notes`, not per-claim source verification. This evaluator adds source-level hallucination detection.

### 2.3 Source Diversity Evaluator

**Gap addressed:** No evaluator checks source diversity or perspective balance.

**What it measures:**
- Unique source domains per article (programmatic)
- Domain type distribution (academic, government, news, blog, etc.)
- Source concentration (Herfindahl index of domain usage)

**Implementation approach:**
```python
def eval_source_diversity(run, example):
    article = run.outputs["final_report"]
    domains = extract_unique_domains(article)
    diversity_score = min(len(domains) / 10, 1.0)  # 10+ domains = 1.0
    return {"score": diversity_score, "domain_count": len(domains)}
```

**Why it's needed:** Articles with only 2 unique domains (gpt-5 min) may have narrow sourcing. Diversity is a measurable quality signal.

### 2.4 Counterargument Coverage Evaluator

**Gap addressed:** Only 6–13% of articles contain counterargument language.

**What it measures:**
- Presence of opposing viewpoints (LLM-based detection)
- Engagement with counterarguments (not just mentioning, but addressing)
- Perspective balance score

**Implementation approach:**
```python
def eval_counterargument(run, example):
    article = run.outputs["final_report"]
    score = llm_eval_counterargument_presence(article)  # 0.0–1.0
    return {"score": score}
```

**Why it's needed:** PhD-level research should engage with opposing viewpoints. The current `balance_and_objectivity` sub-score is too soft — a dedicated evaluator provides a specific signal.

### 2.5 Self-Referential Language Evaluator

**Gap addressed:** 1.7% of articles violate the "do not refer to yourself" prompt constraint.

**What it measures:**
- Presence of first-person self-references (programmatic regex check)
- Count of violations per article

**Implementation approach:**
```python
def eval_self_referential(run, example):
    article = run.outputs["final_report"]
    violations = count_self_ref_patterns(article)
    return {"score": 1.0 if violations == 0 else 0.0, "violations": violations}
```

**Why it's needed:** This is a binary, programmatic check — no LLM needed. The prompt explicitly forbids self-referential language, but no evaluator enforces it.

### 2.6 Silent Failure Detection Evaluator

**Gap addressed:** Failed runs are silently excluded; the `or True` bug masks errors.

**What it measures:**
- Article length below threshold (potential truncation)
- Error markers in article text
- Missing required sections (Sources, etc.)
- Article completeness (ends mid-sentence, etc.)

**Implementation approach:**
```python
def eval_silent_failure(run, example):
    article = run.outputs.get("final_report", "")
    if not article:
        return {"score": 0.0, "reason": "no_final_report"}
    if len(article) < 2000:
        return {"score": 0.0, "reason": "too_short"}
    if has_error_markers(article):
        return {"score": 0.0, "reason": "error_markers"}
    return {"score": 1.0}
```

**Why it's needed:** The `or True` bug and silent exclusion in `extract_langsmith_data.py` mean failures are invisible. This evaluator would catch them at evaluation time.

### 2.7 Language Consistency Evaluator

**Gap addressed:** No evaluator checks if article language matches prompt language.

**What it measures:**
- Prompt language vs. article language match (programmatic)

**Implementation approach:**
```python
def eval_language_consistency(run, example):
    prompt = example.inputs["messages"][0]["content"]
    article = run.outputs["final_report"]
    prompt_lang = detect_language(prompt)
    article_lang = detect_language(article)
    return {"score": 1.0 if prompt_lang == article_lang else 0.0}
```

**Why it's needed:** While current data shows 100% consistency, this is a guardrail evaluator — it would catch regressions if the prompt or model changes.

### 2.8 Traceability Evaluator

**Gap addressed:** No per-claim source traceability.

**What it measures:**
- Fraction of factual claims that have a specific, traceable citation
- Citation-to-source mapping validity

**Implementation approach:**
```python
def eval_traceability(run, example):
    article = run.outputs["final_report"]
    claims = llm_extract_claims(article)
    traceable = sum(1 for c in claims if has_valid_citation(c, article))
    return {"score": traceable / max(len(claims), 1)}
```

**Why it's needed:** The groundedness evaluator checks if claims are in `raw_notes`, but not if they're properly cited. Traceability ensures each claim links to a specific source.

---

## 3. Proposed Evaluation Framework Improvements

### 3.1 Configurable Eval Model

**Current:** `eval_model = ChatOpenAI(model="gpt-4.1")` — hardcoded.

**Proposed:**
```python
eval_model_name = os.environ.get("EVAL_MODEL", "gpt-4.1")
eval_model = ChatOpenAI(model=eval_model_name)
```

**Rationale:** Allows using different judge models, avoiding same-model bias, and matching the RACE score's Gemini judge.

### 3.2 Parameterized Pairwise Evaluation

**Current:** Hardcoded experiment names at bottom of `pairwise_evaluation.py`.

**Proposed:** Move to CLI arguments or environment variables:
```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--experiments", nargs="+", required=True)
parser.add_argument("--mode", choices=["head-to-head", "three-way"], required=True)
```

**Rationale:** Makes the script reusable without editing source code.

### 3.3 Add Missing Model Token Limits

**Current:** `MODEL_TOKEN_LIMITS` missing `openai:gpt-5`.

**Proposed:** Add `"openai:gpt-5": 272000` (or appropriate context window).

**Rationale:** Without this, the retry logic in `final_report_generation` fails for GPT-5 runs.

### 3.4 Fix `or True` Bug

**Current:** `if is_token_limit_exceeded(e, configurable.research_model) or True:`

**Proposed:** `if is_token_limit_exceeded(e, configurable.research_model):`

**Rationale:** The `or True` catches ALL exceptions silently, masking real errors. Removing it restores proper error handling — only token-limit exceptions trigger the graceful degradation path.

### 3.5 Preserve Intermediate State in Data Extraction

**Current:** `extract_langsmith_data.py` only saves `{id, prompt, article}`.

**Proposed:** Also save `raw_notes`, `research_brief`, `compressed_research`, `model_config`, `cost`, `token_count`, `timestamp`.

**Rationale:** Without `raw_notes` and `research_brief`, the groundedness and completeness evaluators cannot be run retrospectively on stored data.

### 3.6 Log Failed Runs in Data Extraction

**Current:** Failed runs silently excluded.

**Proposed:**
```python
failed_count = 0
for run in output_runs:
    if run.outputs is None or run.outputs.get("final_report") is None:
        failed_count += 1
        print(f"WARNING: Run {run.id} failed - no final_report")
        continue
    runs.append(run)
print(f"Total runs: {len(output_runs)}, successful: {len(runs)}, failed: {failed_count}")
```

**Rationale:** Provides visibility into failure rates — the missing IDs 57 and 98 would have been visible.

---

## 4. Proposed Composite Score

### 4.1 Enhanced RACE Score

The current RACE score is a single number from an external Gemini-based judge. We propose an **Enhanced RACE Score** that combines the existing RACE score with the new programmatic evaluators:

| Component | Weight | Source | Type |
|-----------|--------|--------|------|
| RACE score | 50% | External (Gemini) | LLM-as-judge |
| Citation completeness | 15% | New evaluator | Programmatic |
| Hallucination risk | 15% | New evaluator | Hybrid |
| Source diversity | 10% | New evaluator | Programmatic |
| Silent failure check | 10% | New evaluator | Programmatic |

**Rationale:** The programmatic components are deterministic and reproducible, providing a stable baseline. The LLM-as-judge component captures subjective quality. This hybrid approach reduces the variance of pure LLM-as-judge scoring.

### 4.2 Quality Tier System

| Tier | Enhanced RACE Score | Description |
|------|-------------------|-------------|
| A | ≥ 0.85 | Excellent — comprehensive, well-cited, grounded |
| B | 0.70–0.84 | Good — minor citation or completeness issues |
| C | 0.55–0.69 | Fair — notable gaps in citations or sources |
| D | 0.40–0.54 | Poor — significant quality issues |
| F | < 0.40 | Failing — silent failure, no sources, or hallucination |

---

## 5. Implementation Priority

| Improvement | Priority | Effort | Impact |
|-------------|----------|--------|--------|
| Fix `or True` bug | 🔴 Critical | Low | High — stops silent failures |
| Add `openai:gpt-5` to token limits | 🔴 Critical | Low | High — enables GPT-5 retry logic |
| Citation completeness evaluator | 🔴 Critical | Medium | High — detects 20–33% broken citations |
| Silent failure detection | 🔴 Critical | Low | High — catches failed runs |
| Log failed runs in extraction | 🟡 High | Low | Medium — visibility into failures |
| Preserve intermediate state | 🟡 High | Medium | High — enables retrospective evaluation |
| Configurable eval model | 🟡 High | Low | Medium — avoids same-model bias |
| Hallucination risk evaluator | 🟡 High | High | High — detects fabricated sources |
| Source diversity evaluator | 🟠 Medium | Low | Medium — measurable quality signal |
| Counterargument evaluator | 🟠 Medium | Medium | Medium — encourages balanced research |
| Self-referential evaluator | 🟠 Medium | Low | Low — only 1.7% violation rate |
| Language consistency evaluator | 🟠 Medium | Low | Low — guardrail for regressions |
| Traceability evaluator | 🟢 Low | High | High — but complex to implement |
| Parameterized pairwise | 🟢 Low | Low | Low — usability improvement |
| Enhanced RACE composite score | 🟢 Low | Medium | High — but requires all evaluators |

---

## 6. Summary

The metadata enrichment script successfully added 14 provenance and quality-signal fields to all 298 records across 3 JSONL files. The enriched files are self-describing — they no longer require cross-referencing with source code to determine model, search API, or quality signals.

The 8 proposed new evaluation dimensions address the most critical gaps in the current framework: citation completeness, hallucination risk, source diversity, counterargument coverage, self-referential language, silent failure detection, language consistency, and traceability. Combined with the infrastructure improvements (configurable eval model, parameterized pairwise, fixed bugs), these would significantly strengthen the evaluation framework's ability to detect quality issues that are currently invisible.

---

*End of Phase 6 Benchmark Improvements*
