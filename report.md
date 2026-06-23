# Independent Evaluation Report — LLM vs LLM Benchmark (Identical NEO Workflow)

**Auditor:** Independent third-party review (Claude)
**Date:** 2026-06-23
**Task audited:** "Open Deep Research — Dataset Improvement & Optimization Benchmark" (9-phase data-engineering & quality audit of `langchain-ai/open_deep_research`)
**Harness:** NEO VS Code extension, driven through the **NEO MCP BYOK** (bring-your-own-key) integration. Same prompt, same problem statement, same repo, same tools, same environment.
**Only variable:** the underlying LLM (GLM 5.2 vs Kimi K2.6).

- **Model A = GLM 5.2** (referred to as "GLM" below) → `/home/azureuser/ModelsEval/GLM/` (NEO thread `9042f3a6…`)
- **Model B = Kimi K2.6** (referred to as "Kimi" below) → `/home/azureuser/ModelsEval/kimi/open_deep_research/` (NEO thread `9c3e7848…`)

> **Method note.** Both reports were treated as untrusted until verified. Every quantitative
> claim below was independently recomputed by the auditor from the raw artifacts (raw JSONL,
> source code, enriched files, NEO message transcripts, and task plans). Where this report
> states a number as "ground truth," the auditor computed it directly — it is not taken from
> either model's report.

---

## Executive Summary

**Winner:** Model B (**Kimi K2.6**) — by a narrow margin.

**Confidence:** **Low–Medium** (≈2 points on a 100-point scale; 79 vs 81). This is close enough that reasonable reviewers could disagree, and the result is category-dependent rather than a blowout.

**Reason:** Both models did genuinely good, honest work — neither fabricated files, faked executions, or invented data; both ran real code and both performed a real adversarial self-review. Kimi wins on the dimensions this rubric most rewards for a *data-engineering* task: **evidence traceability** (it persisted reproducible script outputs — `phase3_results.json`, `phase4_results.json`, `enrichment_summary.{json,csv}` — whereas GLM saved no intermediate analysis artifacts), **engineering quality** (Kimi's enrichment nests metadata under a single non-destructive `_metadata` key, preserving the original `{id,prompt,article}` schema; GLM flattens 14 fields into the record root), and **self-correction** (Kimi caught and openly corrected its own Phase-4 sampling bias). GLM's offsetting strengths are real and important: it is **more epistemically calibrated** (it explicitly downgraded the citation issue to a "format mismatch" and attached per-finding confidence levels), it caught **additional real code defects** Kimi missed (the missing `openai:gpt-5` token limit), and it produced **no overstatements**. Kimi's one notable epistemic failure — a "100% citation failure (CRITICAL)" headline that the auditor disproved — keeps the margin thin and the confidence low.

---

## Detailed Category Scores

| Category                    | Model A (GLM 5.2) | Model B (Kimi K2.6) |
| --------------------------- | :-----------: | :------------: |
| Repository Understanding    | 9             | 8              |
| Solution Quality            | 7             | 8              |
| Evidence Quality            | 7             | 9              |
| Hallucination Resistance    | 9             | 6              |
| Failure Transparency        | 8             | 9              |
| Debugging Ability           | 7             | 8              |
| Research Quality            | 8             | 8              |
| Completeness                | 9             | 9              |
| Efficiency                  | 7             | 8              |
| Senior Engineer Confidence  | 8             | 8              |
| **Total (/100)**            | **79**        | **81**         |

---

## Strengths of Model A (GLM 5.2)

1. **Genuine, accurate up-front data analysis (verified).** The NEO transcript shows GLM ran interactive Phase 1–5 analysis before writing any deliverable, and its research summary reported concrete numbers — *24% of GPT-4.1 articles lack a Sources section; missing IDs 57 & 98; self-referential IDs 71/72/87/100*. The auditor independently recomputed the 24% no-sources rate and the missing-ID set `{57, 98}` and both are **correct**.

2. **Caught real code defects Kimi missed.** GLM uniquely flagged that `MODEL_TOKEN_LIMITS` (`src/open_deep_research/utils.py:788+`) is **missing `openai:gpt-5`**, while `tests/run_evaluate.py:25` sets `research_model = "openai:gpt-5"`. The auditor confirmed both facts — `openai:gpt-5` is genuinely absent from the dict. GLM also noted the unused `summarization_model` config field and a `compression_model_max_tokens` 10000-vs-8192 default mismatch.

3. **Strong epistemic calibration.** GLM's `final_recommendations.md` attaches an explicit confidence level to every top-10 finding (High/Medium/Low), and its `adversarial_review.md` *proactively downgrades* its own "broken citation" finding to a possible **format mismatch** ("body uses `[N]`, Sources uses `[Title](URL)`") and warns its self-referential regex may over-count. This is exactly the confound that tripped Kimi (see Hallucination Analysis).

4. **Verified real code findings.** The auditor confirmed GLM's headline code findings are true: the `or True` silent-exception bug (`src/open_deep_research/deep_researcher.py:334`) and the hardcoded `eval_model = ChatOpenAI(model="gpt-4.1")` (`tests/evaluators.py:8`).

5. **Non-destructive enrichment.** GLM correctly preserved original article content and produced schema-consistent enriched files (298 records, 100/100/98 — verified by `wc -l`).

---

## Strengths of Model B (Kimi K2.6)

1. **Best-in-class evidence traceability.** Kimi persisted its computation as reproducible artifacts: `scripts/phase3_audit.py → phase3_results.json`, `scripts/phase4_audit.py → phase4_results.json`, and `scripts/phase6_improve.py → enrichment_summary.{json,csv}`. The NEO transcript and the on-disk `__pycache__` confirm these scripts were actually executed. A reviewer can re-run them. GLM's analysis, by contrast, was done inline and **left no intermediate result files** — only the final enriched JSONL.

2. **Cleaner, non-destructive schema design.** Kimi nests all 15 new fields under a single `_metadata` key, leaving the original `{id, prompt, article}` schema untouched (verified by parsing the first enriched record). GLM flattens 14 fields into the record root, mixing provenance with payload. Kimi's design is the one a senior data engineer would prefer.

3. **Citation numbers closest to ground truth.** Kimi's headline broken-reference rate (44% / 44% / 29% for GPT-4.1 / GPT-5 / Claude) matches the auditor's independent computation of **44% / 44% / 26%** (articles with any body `[N]` unresolved against a `[N]`-format Sources section) almost exactly.

4. **Genuine self-correction (failure transparency).** Kimi's `improvement_scorecard.md` openly reports that its Phase-4 **7-sample estimates diverged 85–140%** from the full-population Phase-6 numbers, and it walked the claim back (e.g., GPT-5 missing-refs 21.05 → 15.70). Admitting your own earlier method was unreliable is a strong honesty signal.

5. **Most ambitious deliverable, honestly hedged.** Kimi added composite `hallucination_risk_score` and `source_traceability_score` dimensions, and its `adversarial_review.md` explicitly labels the weights as un-calibrated heuristics rather than presenting them as validated.

6. **Sharp framing.** Kimi's executive conclusion — "without fixes the benchmark risks becoming a *leaderboard of well-formatted hallucinations*" — is the single most useful one-line takeaway either model produced.

---

## Weaknesses of Model A (GLM 5.2)

1. **Weak evidence packaging.** GLM produced no intermediate result files. Its data findings rest on inline `python -c` runs that aren't preserved, so a reviewer must take the enriched output on faith or recompute from scratch. For a "prove every claim" task this is the biggest gap, and it directly lowers its Evidence Quality score.

2. **Schema pollution.** Flattening 14 metadata fields into each record's top level (verified) co-mingles provenance with the original payload — a less clean, mildly more error-prone choice than Kimi's nested `_metadata`.

3. **Conservative citation numbers undersell the issue.** GLM's `broken_citation_count`-based rate (20% / 33% / 16%) is *internally consistent* with its own stricter definition (verified against its enriched artifact) — so it is **not a fabrication** — but it materially undercounts the broad problem relative to ground truth (44/44/26%).

4. **Verbosity / efficiency.** GLM's `adversarial_review.md` is 35.6 KB and total output is the larger of the two; it also ran a redundant interactive-then-background pass. More words, not more verified signal.

---

## Weaknesses of Model B (Kimi K2.6)

1. **Overstated "100% citation failure" (the headline problem).** Kimi's `final_recommendations.md` leads with *"GPT-5 ID 75: 95 body citations, 0 resolved source entries → 100% citation failure (CRITICAL)."* The auditor disproved this: article ID 75 **does** contain a Sources section listing **95 numbered sources** (`1. [Title](URL)` … `95. …`), and the body references `[1]`–`[95]` resolve to them by position. Kimi's regex only matched `[N]`-format entries inside the Sources block, found zero, and reported "0 resolved / 100% failure." The underlying regex output is real, but the *interpretation* is substantively false — and it survived into the executive summary **despite** Kimi's own `adversarial_review.md` noting the broken-reference heuristic was flawed. This is the clearest epistemic miss in either run.

2. **Initial Phase-4 numbers were unreliable.** The 7-ID sample (round-number IDs, no random seed) produced estimates off by 85–140%. Kimi deserves credit for catching this (above) — but it is still a real process misstep that GLM avoided by computing on the full population from the start.

3. **Composite-score weights are arbitrary.** `hallucination_risk_score` / `source_traceability_score` weights are hardcoded with no calibration or sensitivity analysis. Kimi flags this honestly, but the scores should not yet be trusted as benchmark dimensions.

4. **Minor internal inconsistency.** The NEO plan summary states "11 new metadata fields" while the actual artifact and final report use 15 — a small bookkeeping slip.

---

## Code-Level Engineering Comparison

Both models wrote Python to do the work. We read and re-ran all of it: GLM's single `improvements/metadata_enrichment.py` (309 lines) and Kimi's three staged scripts (`scripts/phase3_audit.py`, `phase4_audit.py`, `phase6_improve.py`). The engineering personalities are distinct and verifiable.

| Engineering dimension | GLM 5.2 | Kimi K2.6 | Edge |
|---|---|---|---|
| Pipeline architecture | Single-pass, inline | Staged, JSON-checkpointed (`phase*_results.json`) | **Kimi** |
| Reproducibility | Final output only | Every stage persisted | **Kimi** |
| Citation-resolution parser | `[N]` only | `[N]` / `N.` / `N)` (`extract_source_numbers`) | **Kimi** |
| Deduplication | **Not implemented in code** (asserted only) | SHA-256 content hash of `prompt+article` | **Kimi** |
| Schema design | 14 fields flattened into record root | 15 fields nested under `_metadata` | **Kimi** |
| Metric depth | Counts + booleans | Composite `hallucination_risk` / `source_traceability` scores | **Kimi** |
| Input validation | No `try/except` around `json.loads` | `phase3` try/except + type checks | **Kimi** |
| Path portability | Relative via `os.path.dirname(__file__)` | Hardcoded absolute `/home/azureuser/...` | **GLM** |
| Memory profile | Streaming line-by-line I/O | Loads full file into a list | **GLM** |
| Documentation / readability | Full docstring, type-hinted pure functions | Sparser | **GLM** |
| Self-verification | Re-reads output in `main()` | Summary only | **GLM** |
| Cross-stage consistency | N/A (single stage) | **Failed** — `phase4` claim never reconciled vs `phase6` | **GLM** |

**The decisive correctness test (GPT-5 article 75, verified by re-running both pipelines):**
- **Kimi's final `phase6` enrichment records `missing_ref_count: 0` — correct.** Its 3-format parser resolves the numbered-list sources.
- **GLM's final enrichment records `broken_citation_count: 95` — wrong.** Its `[N]`-only parser cannot read a numbered list, so it silently stores a false value GLM never surfaced.
- The "100% failure" headline came from Kimi's *weaker* `phase4` parser; Kimi's own later code already had the right answer but the report stage shipped the wrong stage's number.

**Engineering net:** Kimi built the more *capable and correct* system (real dedup, robust parser, reproducible staged pipeline, richer metrics, and its final dataset is right on article 75). GLM wrote the more *portable, readable, conservative* artifact (relative paths, streaming, documentation, no false public claims) but skipped a required capability (dedup), used a weaker parser, and shipped a silent data error. **Capability → Kimi; craftsmanship/restraint → GLM.**

---

## Hallucination Analysis

No **invented files, fabricated executions, or faked artifacts** were found in either run. Every deliverable, script, and enriched file each model claimed to produce exists on disk and reproduces (verified by direct file inspection, record counts, and the NEO execution transcripts). The findings below are over-statements / unsupported precision, not fabrications.

| # | Model | Finding | Severity | Evidence |
|---|-------|---------|----------|----------|
| 1 | **Kimi** | "GPT-5 ID 75 = 95 cites, **0 resolved**, **100% citation failure (CRITICAL)**" presented as a top finding. | **Medium** | Disproved: ID 75 has 95 numbered sources (`1.`–`95.`) that resolve body refs `[1..95]`. Came from Kimi's weaker `phase4` parser; **Kimi's own final `phase6` data records `missing_ref_count: 0` (correct)** — a *reporting* error over correct data, surfaced loudly into the exec summary. |
| 1b | **GLM** | Final enriched data records `broken_citation_count: 95` for the same article 75. | **Low–Medium** | Same parsing error as Kimi's phase4 (`[N]`-only parser can't read a numbered list) — but **silent**: never surfaced as a finding, so it reads as a quiet *data* error rather than a loud claim. Lower severity only because no human was misled. |
| 2 | **Kimi** | Composite `hallucination_risk_score` / `source_traceability_score` presented as benchmark dimensions with specific weights. | **Low** | Weights un-calibrated; Kimi *does* disclose this in `adversarial_review.md`, which caps severity. |
| 3 | **Kimi** | Phase-4 per-article metrics (e.g., GPT-5 "21.05 missing refs/article"). | **Low** | Sample-biased by 85–140%; **self-corrected** in Phase 8 — transparency mitigates. |
| 4 | **GLM** | "Broken citation references: 20/33/16" framed as broken refs. | **Low** | Internally consistent with GLM's stricter `broken_citation_count` definition (verified against its own artifact); undersells the broad rate but is not fabricated, and GLM flags the format-mismatch caveat itself. |
| 5 | **GLM** | Self-referential-language counts (e.g., specific IDs). | **Low** | Heuristic regex; GLM explicitly warns of false positives in its adversarial review. |

**Net:** Neither model fabricated files or executions. The article-75 error exists in *both* pipelines (same `[N]`-only parsing limitation) — but they fail differently: **Kimi made it loud and over a base of otherwise-correct final data; GLM made it silent and left it in the shipped data.** GLM still leads on *public* calibration (it raised no false alarms), but the engineering reframe narrows that lead: a silent wrong value in a delivered dataset is its own production hazard. Both are reporting/parsing errors, not fabrications.

---

## Trustworthiness Assessment

| Model | Grade | Rationale |
|-------|:-----:|-----------|
| **A — GLM 5.2** | **B** (Mostly Trustworthy) | Calibrated, conservative, no overstatements, extra real findings. Held back from A by weak evidence packaging (no persisted intermediate artifacts) — for a "prove everything" task, reproducibility is part of trust. |
| **B — Kimi K2.6** | **B** (Mostly Trustworthy) | Best evidence trail, clean engineering, transparent self-correction. Held back from A by the ID-75 "100% failure" overstatement reaching the executive summary unqualified. |

Both are **Grade B**: deploy their findings, but **spot-validate before merge** — specifically re-check Kimi's severity labels and recompute GLM's citation rates under a shared definition.

---

## Final Recommendation

**If forced to choose one model for future NEO workflows: Model B (Kimi K2.6)** — with a stated caveat.

**Why.** For an agentic data-engineering / audit task, the qualities that compound over time are *reproducibility* and *engineering hygiene*. Kimi delivered both: it left behind runnable scripts and saved their outputs (so any reviewer can re-derive its numbers), it modified data non-destructively under a clean `_metadata` namespace, and it demonstrated the rarest and most valuable behavior in the whole benchmark — **catching and openly correcting its own mistake** (the Phase-4 sampling bias). Those are the habits you want on a production task you can't personally re-verify line-by-line.

**The caveat.** Kimi must be paired with a severity-calibration check. Its one real lapse — escalating a format-detection artifact into a "100% citation failure / CRITICAL" headline — is exactly the kind of cry-wolf error that erodes trust in an autonomous auditor. GLM did *not* make this error and is the better choice if the priority is conservative, never-overstate reporting; GLM is the model I would trust more to *not* raise a false alarm.

**Strongest evidence supporting the choice (all independently verified):**
1. Kimi persisted reproducible computation (`phase3/4/6_results.json`, `enrichment_summary.csv`); GLM persisted none.
2. Kimi's broken-citation rate (44/44/29%) matched the auditor's ground truth (44/44/26%); GLM's (20/33/16%) did not.
3. Kimi's `_metadata`-nested enrichment preserved the original schema; GLM's flattened it.
4. Kimi self-corrected its 85–140% Phase-4 sampling error in writing.

**Honest bottom line.** This is a 79-vs-81 decision, not a rout. Both models would pass a senior-engineer review with minor revisions; neither would be merged blind. If the deciding value is *reproducible engineering*, choose **Kimi**. If the deciding value is *never overstating a finding*, choose **GLM**. On balance, weighted toward traceability and engineering quality as this rubric directs, **Kimi is the narrow winner.**
