# Open Deep Research — Dataset Improvement & Optimization Benchmark

## Goal
Audit, improve, validate, enrich, and optimize the existing data assets, evaluation assets, and benchmark quality of the langchain-ai/open_deep_research repository. Produce 9 deliverable markdown documents plus an Executive Summary, with complete traceability and evidence for every claim.

## Research Summary

### Repository Architecture
- **Main agent** (`src/open_deep_research/`): LangGraph multi-agent supervisor architecture. Flow: `clarify_with_user` → `write_research_brief` → `supervisor` (delegates to parallel `researcher` subgraphs, each with `researcher_tools` + `compress_research`) → `final_report_generation`. Uses `init_chat_model` for configurable model selection.
- **Legacy implementations** (`src/legacy/`): Two older approaches — `graph.py` (plan-execute single-agent) and `multi_agent.py` (supervisor with researcher agents). Has its own `prompts.py`, `state.py`, `utils.py`, `configuration.py`.
- **Evaluation suite** (`tests/`): LangSmith-based evaluation with 6 evaluators (`eval_overall_quality`, `eval_relevance`, `eval_structure`, `eval_correctness`, `eval_groundedness`, `eval_completeness`). Also `pairwise_evaluation.py` (head-to-head using Claude Opus) and `supervisor_parallel_evaluation.py`.
- **Experiment results** (`tests/expt_results/`): 3 JSONL files with benchmark results from gpt-4.1, gpt-5, claude-4-sonnet on "Deep Research Bench" (100 prompts).

### Data Analysis Findings
1. **Missing records**: claude4-sonnet JSONL missing IDs 57, 98 (98/100 records)
2. **Schema consistent**: all files have `{id, prompt, article}` — but no provenance metadata (no model config, search API, date, cost)
3. **No exact or near-duplicates** within or across files
4. **Prompt consistency**: all prompts match across files for same IDs
5. **Citation gaps**: 24% of gpt-4.1 articles lack Sources section; 11% for gpt-5 and claude4-sonnet
6. **Broken citation references**: 20/100 (gpt-4.1), 33/100 (gpt-5), 16/98 (claude4-sonnet) cite [N] in body but source N missing from Sources
7. **Self-referential language** (prompt forbids it): 2 articles gpt-4.1, 1 gpt-5, 2 claude4-sonnet
8. **No hallucination evaluator**, no source traceability evaluator, no broken-citation detector
9. **Code bug**: `supervisor_tools` has `or True` in exception handler — catches ALL exceptions silently
10. **MODEL_TOKEN_LIMITS** missing `openai:gpt-5` entry
11. **Article length variance**: gpt-5 avg 16,455 chars vs gpt-4.1 avg 10,387 — significant disparity
12. **50 Chinese prompts** in dataset — all produced Chinese articles (good language consistency)
13. **eval_model hardcoded** to gpt-4.1 in evaluators.py — not configurable
14. **pairwise_evaluation.py** has hardcoded experiment names at bottom

## Approach
Write all 9 deliverable documents based on verified findings from source code analysis and data analysis. For Phase 6 (Dataset Improvement), create a metadata enrichment script that adds provenance metadata to the JSONL files (model name, search API, record count, missing IDs, language) without altering original article content. Create a benchmark improvements document proposing new evaluation dimensions. All claims backed by evidence (file:line references, data analysis output). No invented data — anything unverifiable marked UNVERIFIED.

## Subtasks

1. **Write repository_analysis.md** — System overview, key components, data assets, evaluation assets, quality controls, risks, unknowns, assumptions. Based on all source files read. Output: `/home/azureuser/ModelsEval/GLM/repository_analysis.md`

2. **Write dataset_inventory.md** — Inventory all datasets, benchmark artifacts, evaluation assets, generated outputs. For each: purpose, source, schema, dependencies, quality concerns. Output: `/home/azureuser/ModelsEval/GLM/dataset_inventory.md`

3. **Write integrity_audit.md** — Duplicates (exact, near, semantic), schema problems (missing fields, type inconsistencies), structural issues (broken references, missing IDs, dead metadata). Include all data analysis results. Output: `/home/azureuser/ModelsEval/GLM/integrity_audit.md`

4. **Write research_quality_audit.md** — Weak evidence (unsupported claims, weak citations, missing citations), hallucination risks (statements lacking sources, source-reference mismatches), research gaps (missing counterarguments, source diversity). Analyze sample articles from JSONL files. Output: `/home/azureuser/ModelsEval/GLM/research_quality_audit.md`

5. **Write evaluation_audit.md** — What is measured, what is not measured, coverage gaps, failure modes not represented (silent fake success, hallucinated research, broken tool execution, missing provenance, partial completion as success). Output: `/home/azureuser/ModelsEval/GLM/evaluation_audit.md`

6. **Phase 6: Dataset improvements** — Create metadata enrichment script that adds provenance metadata to JSONL files. Create benchmark improvements document proposing new evaluation dimensions (hallucination risk score, source traceability score, research integrity score, evidence quality score). Document every change. Output: `/home/azureuser/ModelsEval/GLM/improvements/` directory with enriched metadata files and methodology docs.

7. **Write adversarial_review.md** — Act as hostile auditor. Challenge every removal, label change, metadata addition, evaluation addition, quality assessment. Attempt to invalidate own work. Output: `/home/azureuser/ModelsEval/GLM/adversarial_review.md`

8. **Write improvement_scorecard.md** — Before vs after comparison: dataset metrics (record count, duplicate count, missing metadata, invalid records), research metrics (citation coverage, source diversity, provenance coverage, hallucination risk), evaluation metrics (failure mode coverage, benchmark coverage, verification coverage). Output: `/home/azureuser/ModelsEval/GLM/improvement_scorecard.md`

9. **Write verification_matrix.md** — For every claimed improvement, provide evidence with verification status (VERIFIED / PARTIALLY VERIFIED / UNVERIFIED). Table format. Output: `/home/azureuser/ModelsEval/GLM/verification_matrix.md`

10. **Write final_recommendations.md** — Executive summary with top 10 issues, top 10 improvements, highest-risk findings, highest-impact recommendations, confidence level for every major conclusion. Output: `/home/azureuser/ModelsEval/GLM/final_recommendations.md`

## Deliverables
| File Path | Description |
|-----------|-------------|
| /home/azureuser/ModelsEval/GLM/repository_analysis.md | Phase 1: Repository discovery and analysis |
| /home/azureuser/ModelsEval/GLM/dataset_inventory.md | Phase 2: Dataset and asset inventory |
| /home/azureuser/ModelsEval/GLM/integrity_audit.md | Phase 3: Data integrity audit |
| /home/azureuser/ModelsEval/GLM/research_quality_audit.md | Phase 4: Research quality audit |
| /home/azureuser/ModelsEval/GLM/evaluation_audit.md | Phase 5: Evaluation audit |
| /home/azureuser/ModelsEval/GLM/improvements/ | Phase 6: Dataset improvements (metadata enrichment, benchmark proposals) |
| /home/azureuser/ModelsEval/GLM/adversarial_review.md | Phase 7: Adversarial self-review |
| /home/azureuser/ModelsEval/GLM/improvement_scorecard.md | Phase 8: Before vs after comparison |
| /home/azureuser/ModelsEval/GLM/verification_matrix.md | Phase 9: Verification matrix |
| /home/azureuser/ModelsEval/GLM/final_recommendations.md | Final recommendations + executive summary |

## Evaluation Criteria
- Every claim backed by evidence (file:line, data analysis output, or explicit UNVERIFIED label)
- No invented datasets, metadata, citations, or findings
- All 9 deliverable documents produced
- Phase 6 improvements are traceable and documented
- Adversarial review genuinely challenges own work
- Verification matrix has no claims without evidence

## Notes
- No GPU available — all analysis is static (code reading + data analysis)
- No external API calls for verification — all findings based on repository content
- Original JSONL article content must NOT be modified — only metadata enrichment
- The `or True` bug in supervisor_tools is a code finding, not a data finding — document it but don't fix code (task is about data/eval assets)
