#!/usr/bin/env python3
"""
verify_article_75.py — Independently reproduce the central finding of this repo.

No dependencies, no hardcoded paths: run it from anywhere after cloning.

    python3 verify_article_75.py

It does three things for GPT-5 benchmark record #75 (a correctly-sourced report
whose 95 references are formatted as a numbered Markdown list):

  1. Recomputes the GROUND TRUTH straight from the raw article — how many body
     [N] citations there are, and whether the numbered Sources list resolves them.
  2. Reads what each model's FINAL enriched dataset recorded for the same record.
  3. Reads what Kimi's early `phase4` stage recorded (the source of the false alarm).

Expected output: ground truth = 0 broken; Kimi phase6 = 0 (correct);
GLM = 95 (wrong, silent); Kimi phase4 = 95 missing (wrong, loud).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

RAW_GPT5 = ROOT / "kimi/open_deep_research/tests/expt_results/deep_research_bench_gpt-5.jsonl"
KIMI_ENRICHED = ROOT / "kimi/open_deep_research/tests/expt_results/enriched/deep_research_bench_gpt-5_enriched.jsonl"
GLM_ENRICHED = ROOT / "GLM/improvements/enriched/deep_research_bench_gpt-5.enriched.jsonl"
KIMI_PHASE4 = ROOT / "kimi/open_deep_research/scripts/phase4_results.json"

TARGET_ID = 75


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def find(path, rec_id):
    for r in load_jsonl(path):
        if r.get("id") == rec_id:
            return r
    return None


def ground_truth(article):
    """Recompute from the raw article, independent of any model's code."""
    m = re.search(r"(?is)\n#+\s*sources\b", article)
    body = article[: m.start()] if m else article
    src = article[m.start():] if m else ""
    body_refs = set(int(x) for x in re.findall(r"\[(\d{1,3})\]", body))
    # Numbered-list sources: lines like "1. [Title](url)"
    numbered = set(int(x) for x in re.findall(r"(?m)^\s*(\d{1,3})\.\s+\[", src))
    unresolved = sorted(n for n in body_refs if n not in numbered)
    return {
        "has_sources_section": bool(m),
        "body_citations": len(body_refs),
        "numbered_sources": len(numbered),
        "unresolved": len(unresolved),
    }


def main():
    print("=" * 72)
    print(f"Independent verification — GPT-5 benchmark record #{TARGET_ID}")
    print("=" * 72)

    raw = find(RAW_GPT5, TARGET_ID)
    if raw is None:
        raise SystemExit(f"Could not find record {TARGET_ID} in {RAW_GPT5}")

    gt = ground_truth(raw["article"])
    print("\n[1] GROUND TRUTH (recomputed from the raw article)")
    print(f"      sources section present : {gt['has_sources_section']}")
    print(f"      body [N] citations      : {gt['body_citations']}")
    print(f"      numbered sources (1. …) : {gt['numbered_sources']}")
    print(f"      genuinely unresolved    : {gt['unresolved']}   <-- the correct answer is 0")

    print("\n[2] WHAT EACH MODEL'S FINAL DATASET RECORDED")
    glm = find(GLM_ENRICHED, TARGET_ID) or {}
    glm_val = glm.get("broken_citation_count", "?")
    print(f"      GLM 5.2   broken_citation_count = {glm_val}   "
          f"{'WRONG (silent)' if glm_val != 0 else 'correct'}")

    kimi = find(KIMI_ENRICHED, TARGET_ID) or {}
    kimi_val = kimi.get("_metadata", {}).get("missing_ref_count", "?")
    print(f"      Kimi K2.6 missing_ref_count     = {kimi_val}   "
          f"{'correct' if kimi_val == 0 else 'WRONG'}   (phase6, robust parser)")

    print("\n[3] KIMI'S EARLY STAGE (source of the 'CRITICAL' headline)")
    try:
        p4 = json.load(open(KIMI_PHASE4, encoding="utf-8"))
        rec = p4.get("results", {}).get(str(TARGET_ID), {}).get("gpt-5", {})
        missing = len(rec.get("missing_source_refs", []))
        cites = len(rec.get("citations", []))
        print(f"      phase4_audit.py: citations={cites}, missing_source_refs={missing}   "
              f"-> reported '100% FAILURE (CRITICAL)'  WRONG (loud)")
    except FileNotFoundError:
        print(f"      {KIMI_PHASE4} not found (skipped)")

    print("\n" + "-" * 72)
    ok = gt["unresolved"] == 0 and kimi_val == 0 and glm_val == 95
    print("RESULT: " + (
        "reproduced — one correct record, three different answers."
        if ok else "values differ from the writeup; inspect above."))
    print("-" * 72)


if __name__ == "__main__":
    main()
