# Repository Analysis: open_deep_research

## 1. System Overview

The `open_deep_research` repository is an experimental, fully open-source automated research assistant built on LangGraph. It generates comprehensive, well-sourced markdown reports on arbitrary topics through LLM-driven multi-step research pipelines. The repository contains **three distinct implementations** spanning two architectural eras:

### 1.1 Current System (`src/open_deep_research/`)
A supervisor-researcher LangGraph architecture with the following components:

| Component | File | Purpose |
|-----------|------|---------|
| `deep_researcher.py` | Main graph builder | Defines the full research pipeline: clarification → research brief → supervisor delegation → final report |
| `state.py` | State definitions | TypedDict/BaseModel states: `AgentState`, `SupervisorState`, `ResearcherState`, `ResearcherOutputState` |
| `prompts.py` | 8 prompt templates | Instructions for clarification, research brief, supervisor, researcher, compression, final report, webpage summarization |
| `configuration.py` | Config schema | `Configuration` BaseModel with search API enum, model defaults, token limits, MCP config |
| `utils.py` | 925-line utility module | Search tools (Tavily), MCP auth, token limit checking, model token limit dictionary (50+ entries), webpage summarization |

**Graph flow:**
```
clarify_with_user → write_research_brief → research_supervisor → final_report_generation
```

- **Supervisor node**: Binds `ConductResearch`/`ResearchComplete`/`think_tool` tools. Delegates to up to `max_concurrent_research_units` (default 5) researcher subgraphs in parallel. Aggregates `raw_notes`.
- **Researcher subgraph**: `researcher` → `researcher_tools` → `compress_research`. Binds search/MCP/think tools. Checks `tool_call_iterations` against `max_react_tool_calls` (default 10).
- **Compression**: Uses `compression_model` with retry/truncation loop on token limit errors.
- **Final report**: Uses `final_report_model` with retry/truncation using `get_model_token_limit * 4` character approximation.

### 1.2 Legacy Graph Workflow (`src/legacy/graph.py`)
A plan-and-execute workflow with human-in-the-loop:
- **Planning**: Planner model generates structured `Sections` outline
- **Human feedback**: `interrupt`-based approval loop; routes to section writing or plan regeneration
- **Section writing**: Subgraph per section (`generate_queries` → `search_web` → `write_section`) with `Feedback` grading loop (pass/fail + follow-up queries)
- **Final assembly**: `gather_completed_sections` → `write_final_sections` → `compile_final_report`

### 1.3 Legacy Multi-Agent (`src/legacy/multi_agent.py`)
Tool-based supervisor-researcher architecture:
- **Supervisor**: Binds `Sections`, `Introduction`, `Conclusion`, `FinishReport`, `Question`, `search` tools (`parallel_tool_calls=False`, `tool_choice="any"`)
- **Research team**: Spawned via `Send()` per section
- **Research agent**: Binds `Section`, `FinishResearch`, `search` tools
- **Search support**: Tavily and DuckDuckGo only; other APIs raise `NotImplementedError`

### 1.4 Legacy Test & Evaluation (`src/legacy/tests/`)
- `run_test.py`: Rich console runner for pytest with CLI model selection
- `test_report_quality.py`: 9-dimension `CriteriaGrade` evaluation (bool + justification) on both graph and multi_agent agents
- `conftest.py`: pytest CLI options for models, search APIs, depth

### 1.5 Current Evaluation (`tests/`)
- `evaluators.py`: 6 evaluators using hardcoded `ChatOpenAI(model="gpt-4.1")`
- `run_evaluate.py`: Async LangSmith evaluation target; hardcodes `dataset_name="Deep Research Bench"`, `research_model="openai:gpt-5"`, `max_concurrent_research_units=10`
- `pairwise_evaluation.py`: Head-to-head / free-for-all comparative evaluators using `claude-opus-4-20250514` with thinking enabled. Contains **active `evaluate_comparative` call at module level** (executes on import).
- `supervisor_parallel_evaluation.py`: Checks parallelism via fragile nested attribute access: `outputs["output"].values["supervisor_messages"][-1].tool_calls`
- `extract_langsmith_data.py`: Extracts LangSmith runs to JSONL with schema `{id, prompt, article}`

---

## 2. Data Flow

### 2.1 Runtime Data Flow (Current System)

```
User Input (messages)
    ↓
clarify_with_user — optional structured clarification (ClarifyWithUser)
    ↓
write_research_brief — generates ResearchQuestion, stores in state
    ↓
research_supervisor — binds tools, decides ConductResearch or ResearchComplete
    ↓ (parallel, up to max_concurrent_research_units)
    ├─→ researcher_subgraph[topic_1]
    │       researcher → researcher_tools (search/MCP/think)
    │       ↓
    │       compress_research (compression_model, retry on token limit)
    │       ↓
    │       ResearcherOutputState: {compressed_research, raw_notes}
    │
    ├─→ researcher_subgraph[topic_2]
    │       ...
    └─→ researcher_subgraph[topic_n]
            ...
    ↓ (aggregation)
supervisor aggregates all raw_notes into state.raw_notes
    ↓
final_report_generation — final_report_model with retry/truncation
    ↓
Output: state.final_report (markdown)
```

### 2.2 Evaluation Data Flow

```
LangSmith Dataset: "Deep Research Bench"
    ↓
run_evaluate.py invokes deep_researcher_builder with MemorySaver
    ↓
client.aevaluate with 6 evaluators:
    - eval_overall_quality (6 dimensions, 1-5)
    - eval_relevance (1-5 + reasoning)
    - eval_structure (1-5 + reasoning)
    - eval_correctness (1-5 + reasoning, needs reference_outputs["answer"])
    - eval_groundedness (claim extraction vs outputs["raw_notes"], ratio)
    - eval_completeness (1-5, uses outputs["research_brief"])
    ↓
Results logged to LangSmith experiments
    ↓
extract_langsmith_data.py exports to JSONL: {id, prompt, article}
```

### 2.3 Legacy Data Flow

**Graph workflow:**
```
Topic → generate_report_plan (Queries → search → Sections)
    ↓
human_feedback (interrupt; Command to regenerate or accept)
    ↓
build_section_with_web_research (per section subgraph)
    ├─→ generate_queries
    ├─→ search_web (select_and_execute_search from legacy utils)
    ├─→ write_section
    └─→ Feedback grading loop (pass/fail, follow_up_queries)
    ↓
gather_completed_sections → write_final_sections → compile_final_report
```

**Multi-agent workflow:**
```
MessagesState → supervisor (tool calls: Question/Sections/Introduction/Conclusion/FinishReport)
    ↓
supervisor_tools → Send() to research_team subgraph per section
    ↓
research_agent (Section/FinishResearch/search tools)
    ↓
research_agent_tools → conditional edges → END or continue
    ↓
Final report assembled by supervisor
```

---

## 3. Evaluation Flow

### 3.1 Deep Research Bench
The primary benchmark consists of **100 PhD-level research tasks** (50 English / 50 Chinese) with 22 fields per task. Evaluation uses **LLM-as-a-judge via Gemini** producing a **RACE score**.

Published results from README:

| Model | RACE Score | Cost | Tokens |
|-------|-----------|------|--------|
| GPT-5 | 0.4943 | — | 204,640,896 |
| Defaults | 0.4309 | $45.98 | 58,015,332 |
| Claude Sonnet 4 | 0.4401 | $187.09 | 138,917,050 |
| Deep Research Bench Submission | 0.4344 | $87.83 | 207,005,549 |

### 3.2 Evaluator Details

| Evaluator | Dimensions | Scale | Dependencies | Critical Notes |
|-----------|-----------|-------|--------------|----------------|
| `eval_overall_quality` | 6 weighted criteria | 1-5 | final_report | research_depth(20%), source_quality(20%), analytical_rigor(15%), practical_value(10%), balance_and_objectivity(15%), writing_quality(10%) |
| `eval_relevance` | Section relevance | 1-5 | final_report | Strict criteria |
| `eval_structure` | Format, logical flow | 1-5 | final_report | — |
| `eval_correctness` | Accuracy vs authority | 1-5 | final_report + reference_outputs["answer"] | Requires reference answer |
| `eval_groundedness` | Claims vs raw_notes | ratio | final_report + outputs["raw_notes"] | **Fragile: fails if raw_notes missing** |
| `eval_completeness` | Coverage of brief | 1-5 | final_report + outputs["research_brief"] | — |

All evaluators use hardcoded `ChatOpenAI(model="gpt-4.1")` and `get_today_str()`.

### 3.3 Legacy Evaluation
- `test_report_quality.py`: 9 binary criteria (pass/fail) with `CriteriaGrade` structured output
- Tests both `multi_agent` and `graph` agents via pytest fixture
- Rich console output with report display and evaluation justification

---

## 4. Risks

### 4.1 Architecture Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Legacy code duplication** | Medium | Three implementations (current, legacy graph, legacy multi-agent) with overlapping functionality. Maintenance burden and drift risk. |
| **Active module-level evaluation call** | High | `pairwise_evaluation.py` executes `evaluate_comparative` on import, causing unintended side effects if imported. |
| **Fragile attribute access in parallelism evaluator** | Medium | `supervisor_parallel_evaluation.py` uses `outputs["output"].values["supervisor_messages"][-1].tool_calls` — breaks on schema changes. |
| **Hardcoded model references** | Medium | `evaluators.py` hardcodes `gpt-4.1`; `run_evaluate.py` hardcodes `openai:gpt-5`; limits portability and reproducibility. |
| **Token limit map staleness** | Medium | `MODEL_TOKEN_LIMITS` in `utils.py` maps 50+ models but may become outdated as new models release. |
| **No semantic deduplication** | Medium | `tavily_search` deduplicates only by URL; near-duplicate content from different URLs is retained, inflating context. |
| **Groundedness evaluator dependency** | High | `eval_groundedness` requires `outputs["raw_notes"]`. If missing or empty, evaluator fails silently or produces meaningless ratio. |
| **Interrupt-based human feedback** | Low | Legacy `graph.py` uses `interrupt` which may not be compatible with all deployment environments. |
| **MCP tool name collision** | Low | `multi_agent.py` warns but does not prevent MCP tool name collisions. |
| **Search API inconsistency** | Medium | Current system supports only Tavily/Anthropic/OpenAI/None; legacy supports 9 APIs. Migration gap for users of Exa/ArXiv/PubMed/etc. |

### 4.2 Data Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Record count inconsistency** | High | JSONL files have 100/99/98 records for gpt-4.1/gpt-5/claude4-sonnet. Same benchmark should yield same count. Missing records indicate extraction failures. |
| **Duplicate prompts across JSONL files** | Medium | Same `id` expected across files, but no validation ensures prompt consistency. Divergent prompts invalidate cross-model comparison. |
| **Missing metadata in JSONL** | Medium | Output schema is `{id, prompt, article}` only. No model name, timestamp, cost, token count, or configuration metadata. |
| **Citation format inconsistency** | Low | Examples show `### Sources` with numbered URLs, but no automated validation enforces this format in outputs. |
| **No counterargument coverage** | Medium | Prompts and evaluators do not explicitly require or evaluate presence of counterarguments or conflicting evidence. |

### 4.3 Evaluation Risks

| Risk | Severity | Description |
|------|----------|-------------|
| **Silent fake success modes** | High | Evaluators may score high on well-written but hallucinated content if claims are plausible and format is correct. `eval_groundedness` only checks against `raw_notes`, not external ground truth. |
| **Correctness evaluator requires reference** | Medium | `eval_correctness` needs `reference_outputs["answer"]`. Many benchmark tasks may lack authoritative reference answers, causing silent skips or failures. |
| **Single judge model bias** | Medium | All 6 evaluators use the same `gpt-4.1` model, creating correlated bias. No inter-rater reliability or ensemble judging. |
| **No hallucination-specific dimension** | High | No evaluator explicitly measures hallucination risk or source traceability. |

---

## 5. Unknowns

### 5.1 Unverified / UNVERIFIED Items

| Item | Status | Reason |
|------|--------|--------|
| Exact LangSmith dataset schema (22 fields) | UNVERIFIED | README mentions 22 fields but schema not inspected directly. No local copy of dataset metadata. |
| Content of missing JSONL records (gpt-5: 1 missing, claude4: 2 missing) | UNVERIFIED | IDs of missing records not identified. Could be random failures or systematic bias (e.g., Chinese prompts failing more often). |
| Prompt consistency across JSONL files | UNVERIFIED | Plan claims duplicate prompts across files, but no programmatic comparison performed yet. |
| Whether `raw_notes` is reliably populated in all experiment runs | UNVERIFIED | `eval_groundedness` depends on it, but no audit of run outputs confirms presence. |
| Cost and token metadata for JSONL records | UNVERIFIED | README shows aggregate costs, but per-record metadata absent from JSONL. |
| RACE score calculation methodology | UNVERIFIED | Described as "LLM-as-a-judge via Gemini" but exact prompt and aggregation logic not inspected. |
| Chinese prompt handling quality | UNVERIFIED | 50% of benchmark is Chinese; no Chinese-language examples inspected. |
| MCP tool loading in production | UNVERIFIED | MCP auth and tool wrapping code present but no test coverage or example traces inspected. |
| Security module (`src/security/auth.py`) usage | UNVERIFIED | File exists in tree but not read; purpose and integration points unknown. |
| `.github/workflows/` CI behavior | UNVERIFIED | Workflow files exist but not inspected; no evidence of test execution in CI. |
| `langgraph.json` deployment configuration | UNVERIFIED | File exists but not read. |
| `pyproject.toml` dependency constraints | UNVERIFIED | File exists but not read for exact version pins. |

### 5.2 Open Questions

1. **Why does the current system drop support for 6 search APIs** (Exa, Linkup, Perplexity, ArXiv, PubMed, Google, Azure, DuckDuckGo) that legacy supported? Is this temporary or a permanent architectural decision?
2. **What is the migration path** for users of the legacy graph/multi-agent implementations? Is there deprecation timeline?
3. **How is the RACE score normalized** across English and Chinese tasks? Are there language-specific judge prompts?
4. **What happens when `max_concurrent_research_units` exceeds 5** (default)? `run_evaluate.py` sets it to 10 — does this cause rate limiting or quality degradation?
5. **Is there a deterministic seed or checkpoint** for reproducibility of the Deep Research Bench results?
6. **How are source URLs validated** for accessibility and recency? No link-checking logic observed in code.
7. **What is the fallback** when Tavily returns no results? No explicit error handling for empty search results in `deep_researcher.py`.

---

## 6. Key File Inventory

| Path | Lines | Role |
|------|-------|------|
| `src/open_deep_research/deep_researcher.py` | ~400 | Main graph builder (current) |
| `src/open_deep_research/state.py` | ~80 | State definitions (current) |
| `src/open_deep_research/prompts.py` | ~250 | Prompt templates (current) |
| `src/open_deep_research/configuration.py` | ~60 | Configuration schema (current) |
| `src/open_deep_research/utils.py` | 925 | Utilities, search, token limits, MCP |
| `src/legacy/graph.py` | ~350 | Legacy plan-and-execute workflow |
| `src/legacy/multi_agent.py` | ~300 | Legacy supervisor-researcher multi-agent |
| `src/legacy/utils.py` | 1635 | Legacy search backends, deduplication |
| `tests/evaluators.py` | ~200 | 6 evaluators for LangSmith |
| `tests/run_evaluate.py` | ~80 | Async evaluation runner |
| `tests/pairwise_evaluation.py` | ~150 | Comparative evaluation (module-level execution risk) |
| `tests/supervisor_parallel_evaluation.py` | ~80 | Parallelism evaluator (fragile attribute access) |
| `tests/extract_langsmith_data.py` | ~100 | JSONL exporter |
| `tests/expt_results/deep_research_bench_gpt-4.1.jsonl` | 100 | Experiment results |
| `tests/expt_results/deep_research_bench_gpt-5.jsonl` | 99 | Experiment results |
| `tests/expt_results/deep_research_bench_claude4-sonnet.jsonl` | 98 | Experiment results |

---

*Generated as part of Phase 1: Repository Analysis. All findings based on direct file inspection. Items marked UNVERIFIED indicate claims that could not be validated from available source code.*
