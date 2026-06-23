# Phase 1: Repository Analysis — Open Deep Research

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** Direct inspection of all source files, test files, data assets, and configuration. Every claim is traceable to a specific file and line.

---

## 1. System Overview

Open Deep Research is a configurable, open-source deep research agent built on **LangGraph**. It orchestrates a multi-agent supervisor architecture that decomposes user research questions into sub-tasks, delegates them to parallel researcher sub-agents, compresses findings, and synthesizes a final report. The system is evaluated against the **Deep Research Bench** — a benchmark of 100 PhD-level research tasks (50 English, 50 Chinese) across 22 fields.

**Entry point:** `src/open_deep_research/deep_researcher.py` → compiled graph `deep_researcher`

**Architecture flow:**
```
clarify_with_user → write_research_brief → research_supervisor (subgraph) → final_report_generation → END
```

The `research_supervisor` is itself a subgraph containing:
```
supervisor → supervisor_tools → (loop or END)
```
Where `supervisor_tools` delegates to `researcher_subgraph` instances (executed in parallel via `asyncio.gather`), each containing:
```
researcher → researcher_tools → (loop or compress_research) → END
```

---

## 2. Key Components

### 2.1 `deep_researcher.py` — Main LangGraph Workflow

**File:** `src/open_deep_research/deep_researcher.py` (≈400 lines)

| Node | Function | Purpose |
|------|----------|---------|
| `clarify_with_user` | `clarify_with_user()` | Analyzes user messages; asks clarifying question or proceeds. Skipped if `allow_clarification=False`. |
| `write_research_brief` | `write_research_brief()` | Transforms user messages into a structured `ResearchQuestion` (research brief). Initializes supervisor context. |
| `research_supervisor` | `supervisor()` / `supervisor_tools()` | Lead researcher that plans strategy, delegates via `ConductResearch` tool, and signals completion via `ResearchComplete`. |
| `researcher` (sub) | `researcher()` / `researcher_tools()` | Individual sub-agent that uses search tools (Tavily/OpenAI/Anthropic native) and `think_tool` to gather information. |
| `compress_research` (sub) | `compress_research()` | Synthesizes researcher findings into compressed research with inline citations and Sources section. |
| `final_report_generation` | `final_report_generation()` | Merges all compressed research into a comprehensive final report with retry logic for token limits. |

**Key design patterns:**
- Uses `configurable_model` with `init_chat_model(configurable_fields=("model", "max_tokens", "api_key"))` for runtime model switching.
- Parallel research execution: `asyncio.gather(*research_tasks)` for concurrent `ConductResearch` calls, limited by `max_concurrent_research_units`.
- Token-limit-aware retry: `final_report_generation` truncates findings by 10% per retry when token limits are exceeded.
- `override_reducer` in state allows selective state replacement via `{"type": "override", "value": ...}`.

**⚠️ Critical bug found (Line ~190, `supervisor_tools`):**
```python
except Exception as e:
    if is_token_limit_exceeded(e, configurable.research_model) or True:
        # Token limit exceeded or other error - end research phase
        return Command(goto=END, ...)
```
The `or True` makes this condition **always True**, meaning **ALL exceptions** in the research delegation path silently terminate the research phase and return whatever notes were gathered so far. This masks real errors (network failures, API errors, parsing errors) as successful completions. This is a **silent failure** risk — the system can produce incomplete reports without any error signal.

### 2.2 `configuration.py` — Configuration Management

**File:** `src/open_deep_research/configuration.py`

| Field | Default | Purpose |
|-------|---------|---------|
| `max_structured_output_retries` | 3 | Retries for structured output calls |
| `allow_clarification` | True | Whether to ask clarifying questions |
| `max_concurrent_research_units` | 5 | Max parallel researcher sub-agents |
| `search_api` | TAVILY | Search provider (Tavily/OpenAI/Anthropic/None) |
| `max_researcher_iterations` | 6 | Max supervisor reflection iterations |
| `max_react_tool_calls` | 10 | Max tool calls per researcher |
| `summarization_model` | `openai:gpt-4.1-mini` | Summarizes Tavily search results |
| `summarization_model_max_tokens` | 8192 | Max tokens for summarization |
| `max_content_length` | 50000 | Max chars for webpage content before summarization |
| `research_model` | `openai:gpt-4.1` | Powers search agent and supervisor |
| `research_model_max_tokens` | 10000 | Max tokens for research model |
| `compression_model` | `openai:gpt-4.1` | Compresses research findings |
| `compression_model_max_tokens` | 8192 | Max tokens for compression |
| `final_report_model` | `openai:gpt-4.1` | Writes final report |
| `final_report_model_max_tokens` | 10000 | Max tokens for final report |
| `mcp_config` | None | MCP server configuration |
| `mcp_prompt` | None | Additional MCP instructions |

**⚠️ Issue:** `summarization_model` is configured but **never used** in the main `deep_researcher.py` flow. It is only used in `utils.py`'s `tavily_search` tool. The field's description says "Model for summarizing research results from Tavily search results" — this is accurate but the naming is misleading since it doesn't summarize research findings (that's `compression_model`).

**⚠️ Config mismatch:** `run_evaluate.py` sets `compression_model_max_tokens = 10000` but `configuration.py` default is `8192`. This means evaluation runs use a different configuration than the default, potentially affecting results.

### 2.3 `prompts.py` — System Prompts

**File:** `src/open_deep_research/prompts.py`

| Prompt | Used By | Key Instructions |
|--------|---------|------------------|
| `clarify_with_user_instructions` | `clarify_with_user()` | Assess if clarification needed; return JSON with `need_clarification`, `question`, `verification` |
| `transform_messages_into_research_topic_prompt` | `write_research_brief()` | Translate messages into detailed research question; use first person; prioritize primary sources |
| `lead_researcher_prompt` | `supervisor()` | Research supervisor instructions; delegation budgets; scaling rules for parallelism |
| `research_system_prompt` | `researcher()` | Research assistant instructions; tool call budgets (2-3 simple, 5 complex max) |
| `compress_research_system_prompt` | `compress_research()` | Clean up findings verbatim; include ALL sources; inline citations; Sources section |
| `compress_research_simple_human_message` | `compress_research()` | Trigger compression; "DO NOT summarize" |
| `final_report_generation_prompt` | `final_report_generation()` | Comprehensive report; same language as input; [Title](URL) citations; Sources section; "Do NOT refer to yourself as the writer" |
| `summarize_webpage_prompt` | `summarize_webpage()` | Summarize webpage content; preserve key facts; 25-30% of original length |

**Key prompt constraints:**
- `final_report_generation_prompt` explicitly states: "Do NOT ever refer to yourself as the writer of the report."
- `final_report_generation_prompt` requires: "CRITICAL: Make sure the answer is written in the same language as the human messages!"
- Citation rules specify sequential numbering without gaps (1,2,3,4...) and `### Sources` section format.

### 2.4 `state.py` — Graph State Definitions

**File:** `src/open_deep_research/state.py`

| State Class | Scope | Key Fields |
|-------------|-------|------------|
| `AgentInputState` | Main graph input | `messages` (from `MessagesState`) |
| `AgentState` | Main graph | `supervisor_messages`, `research_brief`, `raw_notes`, `notes`, `final_report` |
| `SupervisorState` | Supervisor subgraph | `supervisor_messages`, `research_brief`, `notes`, `research_iterations`, `raw_notes` |
| `ResearcherState` | Researcher subgraph | `researcher_messages`, `tool_call_iterations`, `research_topic`, `compressed_research`, `raw_notes` |
| `ResearcherOutputState` | Researcher output | `compressed_research`, `raw_notes` |

**Structured output models:** `ConductResearch`, `ResearchComplete`, `Summary`, `ClarifyWithUser`, `ResearchQuestion`

**`override_reducer`** allows selective state replacement — when `new_value` is `{"type": "override", "value": X}`, it replaces rather than appends. Used in `write_research_brief` to reset `supervisor_messages`.

### 2.5 `utils.py` — Utility Functions

**File:** `src/open_deep_research/utils.py` (≈500 lines)

| Utility | Purpose |
|---------|---------|
| `tavily_search` | Search tool with deduplication, parallel summarization, formatted output |
| `tavily_search_async` | Async Tavily search execution |
| `summarize_webpage` | Summarize webpage with 60s timeout; returns original on failure |
| `think_tool` | Strategic reflection tool |
| `get_mcp_access_token` | OAuth token exchange for MCP |
| `get_tokens` / `set_tokens` / `fetch_tokens` | Token management with expiration |
| `wrap_mcp_authenticate_tool` | MCP error handling wrapper |
| `load_mcp_tools` | Load and filter MCP tools |
| `get_search_tool` | Configure search tools by provider |
| `get_all_tools` | Assemble complete toolkit |
| `get_notes_from_tool_calls` | Extract notes from tool messages |
| `anthropic_websearch_called` / `openai_websearch_called` | Detect native web search usage |
| `is_token_limit_exceeded` | Provider-specific token limit detection (OpenAI/Anthropic/Gemini) |
| `get_model_token_limit` | Look up model token limits |
| `remove_up_to_last_ai_message` | Truncate message history for token limit recovery |

**⚠️ Issue:** `MODEL_TOKEN_LIMITS` dictionary is missing `openai:gpt-5`, which is used as `research_model` in `run_evaluate.py`. This means `get_model_token_limit("openai:gpt-5")` returns `None`, causing the token-limit retry logic in `final_report_generation` to fail with: "Token limit exceeded, however, we could not determine the model's maximum context length."

**⚠️ Issue:** `MODEL_TOKEN_LIMITS` has a likely typo: `"anthropic.claude-opus-4-1-20250805-v1:0": 200000` — missing the `bedrock:` prefix that all other Bedrock entries have. This entry would never match since `get_model_token_limit` checks `if model_key in model_string`.

---

## 3. Data Assets

### 3.1 Experiment Result JSONL Files

Located in `tests/expt_results/`:

| File | Records | Size | Model |
|------|---------|------|-------|
| `deep_research_bench_gpt-4.1.jsonl` | 100 | 1.35 MB | openai:gpt-4.1 |
| `deep_research_bench_gpt-5.jsonl` | 100 | 2.11 MB | openai:gpt-5 |
| `deep_research_bench_claude4-sonnet.jsonl` | 98 | 1.57 MB | anthropic:claude-sonnet-4 |

**Schema (consistent across all files):** `{id: int, prompt: str, article: str}`

**ID ranges:** All files use IDs 1-100. Claude4-sonnet is **missing IDs 57 and 98** (98 records instead of 100).

**Prompt consistency:** 0 mismatches across all 3 files for matching IDs — all prompts are identical.

### 3.2 Deep Research Bench Dataset

- **Source:** [LangSmith public dataset](https://smith.langchain.com/public/c5e7a6ad-fdba-478c-88e6-3a388459ce8b/d)
- **Size:** 100 PhD-level research tasks (50 English, 50 Chinese)
- **Fields:** 22 domains (Science & Tech, Business & Finance, etc.)
- **Evaluation:** RACE score (LLM-as-a-judge with Gemini) + additional metrics
- **Golden answers:** Expert-compiled reference reports

### 3.3 Example Reports

Located in `examples/` (referenced in CLAUDE.md):
- `arxiv.md` — ArXiv research example
- `pubmed.md` — PubMed research example
- `inference-market.md` — Inference market analysis

### 3.4 Legacy Test Data

`src/legacy/tests/test_report_quality.py` contains a hardcoded test query about MCP (Model Context Protocol) with a single test case, not a dataset.

---

## 4. Evaluation Assets

### 4.1 Six Evaluators (`tests/evaluators.py`)

| Evaluator | Function | Score Type | Uses Reference? | Scale |
|-----------|----------|------------|-----------------|-------|
| Overall Quality | `eval_overall_quality` | 6 sub-scores | No | 0.0-1.0 (each /5) |
| Relevance | `eval_relevance` | Single score | No | 0.0-1.0 (/5) |
| Structure | `eval_structure` | Single score | No | 0.0-1.0 (/5) |
| Correctness | `eval_correctness` | Single score | **Yes** (answer) | 0.0-1.0 (/5) |
| Groundedness | `eval_groundedness` | Ratio score | No (uses `raw_notes`) | 0.0-1.0 |
| Completeness | `eval_completeness` | Single score | No (uses `research_brief`) | 0.0-1.0 (/5) |

**Overall Quality sub-dimensions:** research_depth, source_quality, analytical_rigor, practical_value, balance_and_objectivity, writing_quality

**Eval model:** Hardcoded to `ChatOpenAI(model="gpt-4.1")` — not configurable via environment or parameters.

**Groundedness evaluator:** Uses `outputs["raw_notes"]` as context (the raw search/tool notes), NOT the cited sources. It checks if report claims are grounded in the research notes, but does NOT verify URL-level source attribution or citation correctness.

### 4.2 Pairwise Evaluation (`tests/pairwise_evaluation.py`)

- **Head-to-head:** `head_to_head_evaluator` — compares 2 implementations, uses `claude-opus-4-20250514` with thinking enabled (16000 budget tokens)
- **Three-way:** `free_for_all_evaluator` — ranks 3 implementations (1st=1.0, 2nd=0.5, 3rd=0.0)
- **⚠️ Issue:** Experiment names are **hardcoded** at the bottom of the file (not parameterized):
  ```python
  single_agent = "DR Single Agent - Tavily #-87e8a6c0"
  multi_agent_supervisor_v2 = "DR Supervisor: Multi Agent - Tavily (v2) #-40967f53"
  ```
  The `evaluate_comparative()` call at the bottom runs on import, making this script non-reusable without editing source.

### 4.3 Supervisor Parallelism Evaluation (`tests/supervisor_parallel_evaluation.py`)

- **Dataset:** `"ODR: First Supervisor Parallelism"` (LangSmith)
- **Evaluator:** `right_parallelism_evaluator` — checks if the number of tool calls in the last supervisor message matches the expected `parallel` count from reference outputs
- **Config:** Uses `max_concurrency=1` (sequential execution)
- **Purpose:** Verifies the supervisor correctly parallelizes research tasks

### 4.4 Data Extraction (`tests/extract_langsmith_data.py`)

- Extracts experiment results from LangSmith projects to JSONL format
- Maps `reference_example_id` → example metadata `id` → creates `{id, prompt, article}` records
- Filters: only includes runs where `outputs["final_report"]` is not None
- **⚠️ Issue:** If a run fails (no `final_report`), it is silently excluded — this explains the missing IDs 57 and 98 in the claude4-sonnet file

### 4.5 Evaluation Prompts (`tests/prompts.py`)

Six detailed evaluation prompts with rubrics:
- `OVERALL_QUALITY_PROMPT` — 6 dimensions, 1-5 scale, mentions "Does not refer to itself as the writer"
- `CORRECTNESS_PROMPT` — Compares report against authority answer
- `RELEVANCE_PROMPT` — Section-by-section relevance assessment
- `STRUCTURE_PROMPT` — Format, flow, structural elements
- `GROUNDEDNESS_PROMPT` — Claim-by-claim grounding check against context
- `COMPLETENESS_PROMPT` — Coverage of user question and research brief

---

## 5. Quality Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Token limit handling | `is_token_limit_exceeded()` with provider-specific detection | ⚠️ Missing `openai:gpt-5` in `MODEL_TOKEN_LIMITS` |
| Retry logic | `.with_retry(stop_after_attempt=N)` on structured output calls | ✅ Present |
| Compression retry | 3 attempts with progressive message truncation | ✅ Present |
| Final report retry | 3 retries with 10% findings truncation per retry | ⚠️ Fails for unknown token limits |
| Search deduplication | URL-based dedup in `tavily_search` | ✅ Present |
| Summarization timeout | 60s timeout in `summarize_webpage` | ✅ Present |
| MCP auth handling | OAuth token exchange with expiration | ✅ Present |
| Concurrency limits | `max_concurrent_research_units` caps parallel researchers | ✅ Present |
| Overflow handling | Excess `ConductResearch` calls get error messages | ✅ Present |
| Language consistency | Prompt instruction: "same language as human messages" | ✅ Verified: 50/50 Chinese prompts → Chinese articles |

---

## 6. Risks

| Risk | Severity | Evidence |
|------|----------|----------|
| **Silent failure from `or True` bug** | 🔴 Critical | `supervisor_tools` catches ALL exceptions as token-limit-exceeded, terminating research silently |
| **Missing model token limits** | 🟡 High | `openai:gpt-5` not in `MODEL_TOKEN_LIMITS` → retry logic fails for GPT-5 runs |
| **Missing experiment records** | 🟡 High | claude4-sonnet missing IDs 57, 98 — failed runs silently excluded |
| **No hallucination evaluator** | 🟡 High | No evaluator checks for fabricated sources, URLs, or claims |
| **No citation completeness check** | 🟡 High | 24% of gpt-4.1 articles lack Sources section; no evaluator catches this |
| **Hardcoded eval model** | 🟠 Medium | `eval_model = ChatOpenAI(model="gpt-4.1")` — not configurable |
| **Config mismatch** | 🟠 Medium | `compression_model_max_tokens`: 10000 in eval, 8192 in default config |
| **Hardcoded experiment names** | 🟠 Medium | `pairwise_evaluation.py` has non-parameterized experiment names |
| **Broken citation references** | 🟠 Medium | 20/33/16 articles cite [N] in body but source N missing from Sources |
| **Self-referential language** | 🟢 Low | 2/1/2 articles violate "do not refer to yourself" instruction |

---

## 7. Unknowns

| Unknown | Status |
|---------|--------|
| Why IDs 57 and 98 failed for claude4-sonnet | UNVERIFIED — likely API error or token limit, but no error logs available |
| Exact RACE score computation methodology | UNVERIFIED — described as "LLM-as-a-judge (Gemini)" but implementation is in external Deep Research Bench repo |
| Whether `or True` is intentional (debugging leftover) or a bug | UNVERIFIED — no comment or documentation explains it |
| Cost data for GPT-5 run | UNVERIFIED — README shows blank cost field for GPT-5 |
| Whether `summarization_model` was intended for use in main flow | UNVERIFIED — field exists in config but only used in `tavily_search` |

---

## 8. Assumptions

1. The 3 JSONL files represent complete experiment outputs (except where records are missing due to failures).
2. The `Deep Research Bench` dataset on LangSmith contains 100 examples with IDs 1-100.
3. The RACE scores in the README are accurate as reported.
4. The `or True` in `supervisor_tools` is a bug, not an intentional design choice (no documentation supports intentional behavior).
5. The evaluation prompts in `tests/prompts.py` are the ones used for the reported RACE scores (though RACE uses Gemini, not gpt-4.1).
6. The legacy implementations in `src/legacy/` are not part of the current evaluation pipeline.

---

## 9. Reported Benchmark Results (from README.md)

| Configuration | Research Model | RACE Score | Total Cost | Total Tokens |
|--------------|---------------|------------|------------|--------------|
| GPT-5 | openai:gpt-5 | 0.4943 | UNVERIFIED | 204,640,896 |
| Defaults | openai:gpt-4.1 | 0.4309 | $45.98 | 58,015,332 |
| Claude Sonnet 4 | anthropic:claude-sonnet-4 | 0.4401 | $187.09 | 138,917,050 |
| DRB Submission | openai:gpt-4.1 | 0.4344 | $87.83 | 207,005,549 |

**Note:** The RACE score is computed by the external Deep Research Bench using Gemini as judge. The 6 evaluators in `tests/evaluators.py` are a separate evaluation framework using gpt-4.1 as judge. These are **different evaluation methodologies** and should not be conflated.

---

*End of Phase 1 Repository Analysis*
