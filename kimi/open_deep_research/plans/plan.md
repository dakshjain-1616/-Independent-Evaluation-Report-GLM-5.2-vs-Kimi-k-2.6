# Open Deep Research — Data Engineering & Quality Audit Plan

## Goal
Audit, improve, validate, enrich, and optimize the existing data assets, evaluation assets, and benchmark quality in the open_deep_research repository. Produce 9 required deliverable documents plus a final recommendations report.

## Research Summary
- Repository: https://github.com/langchain-ai/open_deep_research
- Main system: LangGraph-based deep research agent with supervisor-researcher architecture
- Legacy system: Two older implementations (graph.py workflow, multi_agent.py) in src/legacy/
- Evaluation: Deep Research Bench (100 PhD-level tasks, 50 EN / 50 CN)
- Experiment results: 3 JSONL files in tests/expt_results/ (gpt-4.1: 100 records, gpt-5: 99 records, claude4-sonnet: 98 records)
- Key evaluators: overall_quality, relevance, structure, correctness, groundedness, completeness

## Key Pre-Discovered Issues
1. **Record count inconsistency**: 100 vs 99 vs 98 records across benchmark files
2. **Duplicate prompts**: Same prompt IDs appear across all 3 JSONL files (expected — same benchmark, different models)
3. **Missing metadata**: No timestamps, commit hashes, provenance in JSONL outputs
4. **Hardcoded model references** in evaluators and run scripts
5. **Citation format inconsistency** between compression and final report prompts
6. **Groundedness evaluator** depends on `raw_notes` which may not be reliably populated
7. **Supervisor parallel evaluation** has suspicious attribute access pattern
8. **Token limit map** missing newer models, contains outdated entries
9. **No deduplication** beyond URL-level in search results
10. **Legacy code duplication** — significant overlap with current system

## Subtasks

### Phase 1 — Repository Discovery
1. Read all core source files, tests, configs, and example outputs
2. Map data flow: user input → clarification → research brief → supervisor → researchers → compression → final report
3. Map evaluation flow: LangSmith dataset → target() → evaluators → scores
4. Identify all data assets, their schemas, dependencies, and quality controls
5. Produce `repository_analysis.md`

### Phase 2 — Dataset Inventory
1. Enumerate all datasets and artifacts: JSONL experiment results, LangSmith dataset (via docs), prompts, configurations
2. For each asset: document purpose, source, schema, dependencies, quality concerns
3. Produce `dataset_inventory.md`

### Phase 3 — Data Integrity Audit
1. Parse all 3 JSONL files, validate schema consistency
2. Check for exact duplicates, near duplicates, semantic duplicates within and across files
3. Validate ID sequences, missing fields, type consistency
4. Check for broken references, missing IDs, invalid relationships
5. Produce `integrity_audit.md`

### Phase 4 — Research Quality Audit
1. Sample reports from each JSONL file for weak evidence, unsupported claims, citation quality
2. Check for hallucination risks: statements lacking sources, source-reference mismatches
3. Identify research gaps: missing counterarguments, competitive analysis, source diversity
4. Produce `research_quality_audit.md`

### Phase 5 — Evaluation Audit
1. Analyze each evaluator's coverage, failure modes, and blind spots
2. Check for silent fake success modes
3. Identify missing evaluation dimensions (hallucination risk, source traceability, provenance)
4. Produce `evaluation_audit.md`

### Phase 6 — Dataset Improvement
1. Deduplicate and document removals
2. Enrich metadata (provenance, timestamps, quality indicators)
3. Improve categorization and taxonomy
4. Add new benchmark dimensions (hallucination risk score, source traceability score)
5. Document every change with rationale

### Phase 7 — Adversarial Review
1. Challenge all improvements: argue they are incorrect, unnecessary, or harmful
2. Produce `adversarial_review.md`

### Phase 8 — Before vs After Comparison
1. Measure all metrics before and after improvements
2. Produce `improvement_scorecard.md`

### Phase 9 — Silent Fake Success Audit
1. Verify every claimed improvement with evidence
2. Produce `verification_matrix.md`

### Final Deliverable
1. Produce `final_recommendations.md` with executive summary

## Deliverables
| File Path | Description |
|-----------|-------------|
| `/home/azureuser/ModelsEval/kimi/open_deep_research/repository_analysis.md` | System overview, components, risks |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/dataset_inventory.md` | All data assets catalogued |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/integrity_audit.md` | Duplicates, schema, structural issues |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/research_quality_audit.md` | Weak evidence, hallucination risks, gaps |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/evaluation_audit.md` | Evaluator coverage, failure modes |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/adversarial_review.md` | Hostile audit of improvements |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/improvement_scorecard.md` | Before/after metrics |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/verification_matrix.md` | Evidence for every improvement |
| `/home/azureuser/ModelsEval/kimi/open_deep_research/final_recommendations.md` | Executive summary + top issues |

## Evaluation Criteria
- All 9 deliverables produced with evidence
- No invented data or findings
- Every claim backed by code/file evidence or explicitly marked UNVERIFIED
- Adversarial review genuinely challenges improvements
- Verification matrix has no unverified improvements claimed as verified
