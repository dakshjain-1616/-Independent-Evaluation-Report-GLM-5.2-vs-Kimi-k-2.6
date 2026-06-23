# GLM 5.2 vs Kimi K2.6 — Same Agent Workflow, One Variable

[![NEO for VS Code](https://img.shields.io/badge/NEO-VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)](https://marketplace.visualstudio.com/items?itemName=NeoResearchInc.heyneo)
[![NEO for Cursor](https://img.shields.io/badge/NEO-Cursor-0098FF?style=for-the-badge&logo=cursor&logoColor=white)](https://marketplace.cursorapi.com/items/?itemName=NeoResearchInc.heyneo)
[![Website](https://img.shields.io/badge/heyneo.com-6E56CF?style=for-the-badge&logo=googlechrome&logoColor=white)](https://heyneo.com)

An independent, evidence-first comparison of two frontier LLMs running the **exact same engineering task** inside the **same agent workflow**. The only thing that changed between the two runs was the underlying model.

![Experiment overview](assets/experiment-overview.svg)

---

## What this is

We took one real data-engineering assignment — audit, deduplicate, enrich, and quality-score the benchmark datasets of an open-source research agent ([`langchain-ai/open_deep_research`](https://github.com/langchain-ai/open_deep_research)) — and ran it twice. Same repository, same prompt, same tools, same environment, same multi-phase workflow. We then **independently verified every claim** each model made by re-reading and re-running the code it wrote, and we wrote up what the differences teach us about evaluating AI agents in production.

- **Model A — GLM 5.2**
- **Model B — Kimi K2.6**

The headline isn't "which model won" (the scores were close, both passed, neither is merge-ready as-is). It's that **both runs looked like complete successes from the outside while both shipped the same wrong answer about one record** — one loudly, one silently — and the only way to tell was to inspect the *process*, not the output.

---

## How it was run: NEO + BYOK

The comparison was only possible because of how the work was executed. Both runs used the **NEO VS Code extension**, driven through NEO's **MCP BYOK (bring-your-own-key)** feature — which lets you point the same agent workflow at *any* model you choose. That's what made this an apples-to-apples test: BYOK holds the entire harness constant and swaps only the model behind the key.

NEO is the **evaluation platform** here, not a contestant in the benchmark — the wind tunnel in which you change one airfoil and trust nothing else moved. Get it via the badges at the top of this README ([VS Code](https://marketplace.visualstudio.com/items?itemName=NeoResearchInc.heyneo) · [Cursor](https://marketplace.cursorapi.com/items/?itemName=NeoResearchInc.heyneo) · [heyneo.com](https://heyneo.com)).

---

## The finding that matters

In the benchmark dataset, one report (**Article 75**) cites 95 sources correctly — the Sources section lists them as a numbered list (`1.`, `2.`, … `95.`). Both models' pipelines flagged it as broken anyway, because of a citation parser that only understood bracketed `[N]` references.

![Article 75 fork](assets/article-75-fork.svg)

- **Kimi K2.6** raised a false **"100% citation failure — CRITICAL"** in an early stage (`phase4`) — but its *final* enrichment stage (`phase6`) had a better 3-format parser and recorded the **correct** answer (`missing_ref_count: 0`). The pipeline held both answers and shipped the wrong one, because no stage reconciled them.
- **GLM 5.2** wrote the wrong value (`broken_citation_count: 95`) straight into its final dataset and **never surfaced it** — a silent data error, invisible to any output-level review.

The model that raised the false alarm had already written the correct parser. The model that stayed quiet shipped wrong data and never noticed. That inversion is the whole point.

---

## The scorecard

![Engineering scorecard](assets/engineering-scorecard.svg)

| | Winner |
|---|---|
| **Engineering capability** | **Kimi K2.6** — staged pipeline, real dedup, robust parser, reproducible artifacts |
| **Code craftsmanship** | **GLM 5.2** — portable, documented, memory-efficient, never overstated |
| **Production trust** | **Depends** — visibility of failure (Kimi) vs simplicity of implementation (GLM) |

Two engineering archetypes emerged: **The Systems Builder** (Kimi — instrumented, multi-stage, self-correcting, more seams to get wrong) and **The Craftsman** (GLM — simpler, cleaner, lower-complexity, inspects itself less). Neither is universally right; the trade-off is the lesson.

---

## What's in this repo

```
.
├── README.md                  ← you are here
├── report.md                  ← full independent audit: scores, evidence, hallucination analysis, verdict
├── blog.md                    ← the engineering narrative / write-up (publish-ready)
├── social-kit.md              ← promotion collateral (LinkedIn, X thread, pull quotes)
├── assets/                    ← SVG infographics
│   ├── experiment-overview.svg
│   ├── article-75-fork.svg
│   └── engineering-scorecard.svg
├── GLM/                       ← GLM 5.2 run: 10 deliverable reports + improvements/ (enrichment script + enriched data)
│   └── improvements/metadata_enrichment.py
└── kimi/open_deep_research/   ← Kimi K2.6 run: 10 deliverable reports + scripts/ (phase3/4/6 + persisted results JSON)
    └── scripts/{phase3_audit,phase4_audit,phase6_improve}.py
```

Each model's run produced the same 10 deliverables: `repository_analysis.md`, `dataset_inventory.md`, `integrity_audit.md`, `research_quality_audit.md`, `evaluation_audit.md`, `adversarial_review.md`, `improvement_scorecard.md`, `verification_matrix.md`, `final_recommendations.md`, plus enriched datasets.

---

## Start here

| If you want… | Read |
|---|---|
| The full evidence-backed audit and category scores | [`report.md`](report.md) |
| The engineering story and lessons for deploying agents | [`blog.md`](blog.md) |
| GLM's actual code | [`GLM/improvements/metadata_enrichment.py`](GLM/improvements/metadata_enrichment.py) |
| Kimi's actual code + persisted intermediate artifacts | [`kimi/open_deep_research/scripts/`](kimi/open_deep_research/scripts/) |

---

## The takeaway

Both outputs would have passed a superficial review. The differences that matter — validation, intermediate artifacts, reconciliation between stages, provenance — only appear when you evaluate the **process** that produced the output, not just the output itself.

> If you're evaluating agents, require intermediate artifacts, independent recomputation of every metric, and reconciliation checks between stages. Otherwise both of these runs would have looked successful.

As AI agents move into production engineering workflows, the question that matters is no longer *"is the answer right?"* — it's *"can I tell when it's wrong?"*

---

*Evaluation harness: [NEO](https://heyneo.com) (VS Code / Cursor) · MCP BYOK. Subject repo: [`langchain-ai/open_deep_research`](https://github.com/langchain-ai/open_deep_research). All quantitative claims independently recomputed from the raw artifacts.*
