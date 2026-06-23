# Phase 4: Research Quality Audit — Open Deep Research

> **Audit Date:** 2025-06-23  
> **Repository:** `langchain-ai/open_deep_research` at `/home/azureuser/ModelsEval/GLM`  
> **Methodology:** Programmatic analysis of all 297 articles across 3 JSONL files. Pattern-based detection of weak evidence, hallucination risks, and research gaps. Sample article deep-dives for qualitative assessment.

---

## 1. Executive Summary

| Category | Finding | Severity |
|----------|---------|----------|
| Weak evidence (missing Sources) | 24% gpt-4.1, 11% gpt-5, 11.2% claude4-sonnet | 🟡 High |
| Broken citation references | 20% gpt-4.1, 33% gpt-5, 16.3% claude4-sonnet | 🟡 High |
| Self-referential violations | 2% gpt-4.1, 1% gpt-5, 2% claude4-sonnet | 🟢 Low |
| Source-reference mismatches | Systematic: body citations not in Sources section | 🟡 High |
| Counterargument coverage | 13% gpt-4.1, 6% gpt-5, 6% claude4-sonnet | 🟠 Medium |
| Source diversity | avg 14.7–24.2 unique domains per article | ✅ Good |
| Language consistency | 100% match (Chinese prompts → Chinese articles) | ✅ Pass |
| Fabricated URL risk | UNVERIFIED — domains appear legitimate but not validated | 🟠 Medium |

---

## 2. Weak Evidence Analysis

### 2.1 Missing Sources Sections

The `final_report_generation_prompt` explicitly requires: "Includes a Sources section at the end with all referenced links."

| Model | Articles with Sources | Articles without Sources | Missing Rate |
|-------|---------------------|-------------------------|-------------|
| gpt-4.1 | 76/100 | **24/100** | **24.0%** |
| gpt-5 | 89/100 | **11/100** | **11.0%** |
| claude4-sonnet | 87/98 | **11/98** | **11.2%** |

**Key finding:** GPT-4.1 has the highest rate of missing Sources sections at 24%. Nearly 1 in 4 GPT-4.1 articles provides no source attribution, making their claims unverifiable.

**IDs without Sources:**
- gpt-4.1: 1, 2, 7, 9, 11, 18, 25, 26, 28, 30, 31, 33, 34, 36, 40, 41, 44, 45, 48, 49, and 4 more
- gpt-5: 4, 5, 7, 15, 28, 36, 43, 45, 48, 67, 83
- claude4-sonnet: 8, 9, 14, 24, 25, 26, 35, 37, 40, 41, 45

**Overlap analysis:** IDs 7, 9, 25, 26, 28, 36, 40, 41, 45 appear in multiple files' "no sources" lists, suggesting certain research topics consistently fail to produce source attribution regardless of model.

### 2.2 Articles with Citations but No Sources Section

Some articles use `[N]` bracket citations in the body but have no Sources section to define what those citations reference. This is the most severe form of weak evidence — claims appear cited but are completely unverifiable.

**Sample evidence (from broken citation analysis):**
- gpt-4.1 ID 54: body cites [1]–[17], but Sources section has 0 numbered sources (max source=0)
- gpt-4.1 ID 77: body cites [1]–[5], but Sources section has 0 numbered sources
- gpt-4.1 ID 63: body cites [1]–[14], but Sources section has 0 numbered sources
- gpt-5 ID 60: body cites [1]–[52], but Sources section has 0 numbered sources
- gpt-5 ID 55: body cites [1]–[37], but Sources section has 0 numbered sources
- claude4-sonnet ID 93: body cites [1]–[29], but Sources section has 0 numbered sources

**Root cause hypothesis:** The `final_report_generation_prompt` specifies `[Title](URL)` format for inline citations, while `compress_research_system_prompt` specifies `[N]` format. When the final report model inherits compressed research with `[N]` citations but generates its own body text with `[N]` citations without creating a matching Sources section, the references become orphaned. The prompt conflict between `[N]` and `[Title](URL)` formats contributes to this failure.

---

## 3. Hallucination Risks

### 3.1 Source-Reference Mismatches

**Definition:** The article body cites `[N]` but the Sources section does not contain a corresponding entry for source `N`.

| Model | Articles with Mismatches | Rate |
|-------|------------------------|------|
| gpt-4.1 | 20/100 | 20.0% |
| gpt-5 | 33/100 | 33.0% |
| claude4-sonnet | 16/98 | 16.3% |

**Detailed samples:**

| Model | ID | Body Citations Missing from Sources | Max Body Citation | Max Source Citation |
|-------|-----|--------------------------------------|-------------------|---------------------|
| gpt-4.1 | 54 | [1,2,3,4,5,6,8,9,10,11,12,13,14,17] | 17 | 0 |
| gpt-4.1 | 77 | [1,2,3,4,5] | 5 | 0 |
| gpt-4.1 | 63 | [1–14] | 14 | 0 |
| gpt-5 | 60 | [1–52] (33 missing) | 52 | 0 |
| gpt-5 | 62 | [9,10,16–23,33,45,47,48,52,56] | 56 | 0 |
| gpt-5 | 55 | [1–37] | 37 | 0 |
| claude4-sonnet | 93 | [1–29] | 29 | 0 |
| claude4-sonnet | 97 | [1–24] | 24 | 0 |
| claude4-sonnet | 95 | [1–19] | 19 | 0 |

**Critical observation:** In all sampled cases, `max source = 0`, meaning the Sources section contains **zero numbered citations**. This indicates the Sources section uses a different format (likely `[Title](URL)` markdown links without `[N]` numbering) while the body uses `[N]` bracket citations. The two numbering systems are completely disconnected.

**Hallucination risk:** When a body cites `[15]` but source 15 does not exist in the Sources section, the reader cannot verify the claim. The citation may reference:
1. A real source that was improperly formatted (low hallucination risk)
2. A fabricated source number with no underlying reference (high hallucination risk)

Without access to the intermediate `raw_notes` or `compressed_research` for these articles, we cannot determine which case applies. **Status: UNVERIFIED** — would require cross-referencing with LangSmith run traces.

### 3.2 Self-Referential Violations

The `final_report_generation_prompt` explicitly states: "Do NOT ever refer to yourself as the writer of the report."

| Model | Violation Count | IDs |
|-------|----------------|-----|
| gpt-4.1 | 2 | 71, 72 |
| gpt-5 | 1 | 87 |
| claude4-sonnet | 2 | 87, 100 |

**Patterns detected:** "I conducted research", "I gathered", "I found", "my research", "I searched", "I will present", "As an AI", "I used various sources", "In this report, I", "Let me", "I compiled".

**Impact:** Low frequency (5 total across 297 articles, 1.7%). The `OVERALL_QUALITY_PROMPT` evaluator mentions "Does not refer to itself as the writer" as a scoring criterion, but this is buried in a 6-dimension rubric and unlikely to significantly impact scores.

### 3.3 Fabricated URL Risk

**URL domain analysis:**

| Model | Total URLs | Top Domains |
|-------|-----------|-------------|
| gpt-4.1 | 2,247 | sciencedirect.com (99), pmc.ncbi.nlm.nih.gov (91), researchgate.net (67), nature.com (60), arxiv.org (40) |
| gpt-5 | 4,111 | arxiv.org (126), github.com (90), pmc.ncbi.nlm.nih.gov (77), researchgate.net (75), pubmed.ncbi.nlm.nih.gov (74) |
| claude4-sonnet | 2,873 | sciencedirect.com (116), pmc.ncbi.nlm.nih.gov (116), nature.com (90), arxiv.org (55), saintseiya.fandom.com (47) |

**Observations:**
- Domains are predominantly legitimate academic/scientific sources (arxiv.org, pubmed, nature.com, sciencedirect.com)
- ⚠️ **claude4-sonnet has `saintseiya.fandom.com` (47 URLs)** — a fandom wiki for anime. This is suspicious for a PhD-level research benchmark and may indicate:
  - A research topic about anime/pop culture (possible but unlikely for "PhD-level" tasks)
  - Hallucinated URLs from an irrelevant domain
  - **Status: UNVERIFIED** — would need to check which article(s) contain these URLs
- ⚠️ **gpt-5 has `spring.io` (29 URLs)** — Spring is a Java/framework site, possibly relevant for CS topics but could also be hallucinated
- ⚠️ **gpt-5 has `www.gov.cn` (32) and `www.moe.gov.cn` (30)** — Chinese government sites, likely legitimate for Chinese-language research tasks

**Fabrication assessment:** The domains appear mostly legitimate, but URL validity (whether the URLs actually resolve to real pages) is **UNVERIFIED** — would require HTTP HEAD requests to each URL, which is out of scope for this audit.

---

## 4. Research Gaps

### 4.1 No Counterargument Detection

| Model | Articles with Counterargument Markers | Rate |
|-------|--------------------------------------|------|
| gpt-4.1 | 13/100 | 13.0% |
| gpt-5 | 6/100 | 6.0% |
| claude4-sonnet | 6/98 | 6.1% |

**Patterns searched:** "However, ... argue/claim/contend/assert", "On the other hand", "Critics argue/say/contend", "Despite ... evidence/concerns/criticism", "While some/many/critics/opponents", "In contrast", "Conversely".

**Finding:** Only 6-13% of articles contain counterargument language. For PhD-level research reports, this is low — academic writing should engage with opposing viewpoints. The `final_report_generation_prompt` does not instruct the model to include counterarguments or dissenting perspectives.

**Research gap:** No evaluator checks for:
- Counterargument presence
- Source diversity (are sources from multiple perspectives?)
- Bias detection (does the report present only one side?)
- Viewpoint balance

### 4.2 Source Diversity Analysis

| Model | Avg Unique Domains/Article | Min | Max |
|-------|--------------------------|-----|-----|
| gpt-4.1 | 14.7 | 4 | 63 |
| gpt-5 | 24.2 | 2 | 73 |
| claude4-sonnet | 20.7 | 5 | 59 |

**Finding:** GPT-5 has the highest source diversity (24.2 avg unique domains), followed by claude4-sonnet (20.7) and gpt-4.1 (14.7). This is a positive signal — more unique domains suggests broader source coverage.

**Concerns:**
- gpt-5 min=2: at least one article uses only 2 unique domains — potentially narrow sourcing
- No evaluator checks source diversity as a quality signal
- High domain count doesn't guarantee quality — could include low-quality or irrelevant sources

### 4.3 No Source Quality Verification

**Current state:** The `eval_groundedness` evaluator checks if report claims are grounded in `raw_notes` (the search/tool output context). It does NOT verify:
- Whether cited URLs are accessible/valid
- Whether cited sources actually support the claims they're attached to
- Whether sources are authoritative (peer-reviewed vs. blog posts)
- Whether sources are primary or secondary
- Whether sources are current or outdated

**Research gap:** There is no source quality evaluator. The `source_quality` sub-dimension in `eval_overall_quality` is an LLM judgment, not a programmatic verification.

### 4.4 No Citation Completeness Check

**Current state:** No evaluator checks:
- Whether the Sources section is present
- Whether all body citations have corresponding source entries
- Whether citation numbering is sequential without gaps (as required by the prompt)
- Whether citation format is consistent

**Research gap:** The 20-33% broken citation rate and 11-24% missing Sources rate are invisible to the current evaluation framework.

### 4.5 No Traceability from Claim to Source

**Current state:** The `eval_groundedness` evaluator uses `raw_notes` as context, but this is the entire raw search output, not individual source-to-claim mappings. It cannot verify that a specific claim is supported by a specific source.

**Research gap:** There is no claim-level traceability. For a research report, each factual claim should be traceable to a specific source. The current evaluation framework does not support this.

---

## 5. Sample Article Analysis

### 5.1 Sample: gpt-4.1, ID 54 (Broken Citations)

**Prompt:** (Chinese-language research task, ID 54)

**Issues found:**
- Body contains citations [1]–[17] (14 distinct numbers, missing [7] and [15]–[16] from sequence)
- Sources section has 0 numbered citations — uses a different format
- All 14 body citations are orphaned (no corresponding source entries)
- The article has URLs (part of the 2,247 total), but they are not mapped to the [N] citations

**Qualitative assessment:** The article body appears well-structured with inline citations, but the disconnect between body citations and the Sources section makes verification impossible. A reader seeing `[14]` in the text has no way to find what source 14 references.

### 5.2 Sample: gpt-5, ID 60 (Severe Broken Citations)

**Issues found:**
- Body cites [1]–[52] with 33 missing from Sources section
- Max body citation = 52, but max source citation = 0
- This is the most severe case: 52 inline citations with zero verifiable source references

**Qualitative assessment:** This article has the most extensive citation system (52 references) but the worst traceability. The gap between the body's citation density and the Sources section's format creates a complete verification failure.

### 5.3 Sample: claude4-sonnet, ID 93 (Broken Citations)

**Issues found:**
- Body cites [1]–[29], all 29 missing from Sources section
- Max body = 29, max source = 0

**Qualitative assessment:** Same pattern as gpt-4.1 and gpt-5 — the body uses [N] format while the Sources section uses a different format, creating a complete disconnect.

### 5.4 Pattern Summary Across Samples

All sampled broken-citation articles share the same root pattern:
1. Body text uses `[N]` bracket citations (inherited from `compress_research_system_prompt` format)
2. Sources section uses `[Title](URL)` markdown format (from `final_report_generation_prompt`)
3. The two numbering systems are never reconciled
4. Result: 100% of body citations are orphaned in these articles

**This is a systematic prompt design flaw**, not a random model error. The `compress_research_system_prompt` and `final_report_generation_prompt` specify incompatible citation formats.

---

## 6. Prompt-Induced Quality Issues

### 6.1 Citation Format Conflict

| Prompt | Citation Format Specified | Used In |
|--------|--------------------------|---------|
| `compress_research_system_prompt` | `[N]` sequential numbering, `### Sources` section | Compressed research (intermediate) |
| `final_report_generation_prompt` | `[Title](URL)` inline, `[N] Source Title: URL` in Sources | Final report (output) |

**Conflict:** The compressed research uses `[N]` citations. The final report is supposed to use `[Title](URL)` citations. When the final report model inherits compressed research with `[N]` citations and either:
- Preserves them in the body → body has `[N]` but Sources uses `[Title](URL)` → broken references
- Regenerates them as `[Title](URL)` → may lose the mapping to the original source

**Result:** 20-33% of articles have broken citation references due to this format conflict.

### 6.2 Missing Counterargument Instruction

The `final_report_generation_prompt` does not instruct the model to:
- Present opposing viewpoints
- Engage with counterarguments
- Include dissenting sources
- Balance perspectives

**Result:** Only 6-13% of articles contain counterargument language.

### 6.3 No Source Verification Instruction

The `final_report_generation_prompt` does not instruct the model to:
- Verify that cited URLs are accessible
- Verify that sources support the claims they're attached to
- Include only authoritative sources

**Result:** Source quality is not verified at generation time or evaluation time.

---

## 7. Quality Assessment by Model

| Dimension | gpt-4.1 | gpt-5 | claude4-sonnet | Best |
|-----------|---------|-------|----------------|------|
| Sources present | 76% | 89% | 88.8% | gpt-5 |
| Broken citations | 20% | 33% | 16.3% | claude4-sonnet (lowest) |
| Self-referential | 2% | 1% | 2% | gpt-5 |
| Counterarguments | 13% | 6% | 6.1% | gpt-4.1 |
| Source diversity (avg domains) | 14.7 | 24.2 | 20.7 | gpt-5 |
| Article length (avg chars) | 10,387 | 16,455 | 12,358 | gpt-5 (longest) |
| Total URLs | 2,247 | 4,111 | 2,873 | gpt-5 |
| Language consistency | 100% | 100% | 100% | Tie |
| Error markers | 0 | 0 | 0 | Tie |

**Key insight:** GPT-5 produces the most comprehensive articles (longest, most URLs, most source diversity, highest Sources presence) but also has the highest broken citation rate (33%). This suggests GPT-5 generates more content but with worse citation discipline. Claude4-sonnet has the lowest broken citation rate (16.3%) but also the lowest counterargument coverage (6.1%).

---

## 8. Risks Summary

| Risk | Evidence | Impact |
|------|----------|--------|
| Unverifiable claims | 11-24% of articles have no Sources section | Claims cannot be fact-checked |
| Orphaned citations | 16-33% of articles cite [N] with no source definition | Readers cannot trace claims to sources |
| Prompt format conflict | compress_research uses [N], final_report uses [Title](URL) | Systematic citation breakage |
| No counterargument check | Only 6-13% contain counterargument language | Reports may be one-sided |
| No source validation | URLs not verified for accessibility | Potential hallucinated sources |
| No claim-to-source traceability | Groundedness evaluator uses raw_notes, not per-claim | Cannot verify individual claims |
| Fandom wiki in academic output | saintseiya.fandom.com (47 URLs in claude4-sonnet) | Possible irrelevant/hallucinated sources |

---

*End of Phase 4 Research Quality Audit*
