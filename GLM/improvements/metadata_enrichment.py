#!/usr/bin/env python3
"""
metadata_enrichment.py — Adds provenance metadata to JSONL experiment result files.

This script reads the 3 JSONL experiment result files in tests/expt_results/,
analyzes each record for quality signals, and produces enriched versions in
improvements/enriched/ with the following additional fields:

  - model: The research model used
  - search_api: The search API used
  - language: Detected language of the article (en/zh)
  - article_length: Character count of the article
  - has_sources_section: Boolean indicating presence of Sources section
  - citation_count: Number of [N] bracket citations in body
  - broken_citation_count: Number of body citations missing from Sources section
  - url_count: Number of URLs in the article
  - unique_source_domains: Count of unique URL domains
  - has_self_referential_language: Boolean for self-referential violations
  - has_error_markers: Boolean for error messages in article
  - enrichment_timestamp: ISO timestamp of enrichment

Usage:
    python3 improvements/metadata_enrichment.py

Input:  tests/expt_results/deep_research_bench_*.jsonl
Output: improvements/enriched/deep_research_bench_*.enriched.jsonl
"""

import json
import re
import os
from datetime import datetime, timezone
from collections import Counter

# ─── Configuration ───────────────────────────────────────────────────────────

INPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "expt_results")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "enriched")

FILES = {
    "gpt-4.1": {
        "path": "deep_research_bench_gpt-4.1.jsonl",
        "model": "openai:gpt-4.1",
        "search_api": "tavily",
    },
    "gpt-5": {
        "path": "deep_research_bench_gpt-5.jsonl",
        "model": "openai:gpt-5",
        "search_api": "tavily",
    },
    "claude4-sonnet": {
        "path": "deep_research_bench_claude4-sonnet.jsonl",
        "model": "anthropic:claude-sonnet-4",
        "search_api": "tavily",
    },
}

# ─── Analysis Functions ──────────────────────────────────────────────────────

SELF_REF_PATTERNS = [
    r"[Ii] conducted (the )?research",
    r"[Ii] (have )?gathered",
    r"[Ii] (have )?found",
    r"[Mm]y research",
    r"[Ii] searched",
    r"[Ii] will (now )?(present|write|provide)",
    r"[Aa]s (an? )?(AI|researcher|assistant)",
    r"[Ii] used (various|multiple|several) (sources|tools)",
    r"[Ii]n this report,? I",
    r"Let me",
    r"[Ii] compiled",
]

ERROR_MARKERS = [
    "Error generating",
    "Maximum retries exceeded",
    "Error synthesizing",
    "An error occurred",
    "Failed to generate",
]


def detect_language(text: str) -> str:
    """Detect if text is primarily Chinese or English."""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total_chars = len(text)
    if total_chars == 0:
        return "unknown"
    chinese_ratio = chinese_chars / total_chars
    if chinese_ratio > 0.05:
        return "zh"
    return "en"


def has_sources_section(article: str) -> bool:
    """Check if article has a Sources section."""
    return bool(
        "### Sources" in article
        or "## Sources" in article
        or "Sources" in article[-500:]
    )


def count_citations(article: str) -> int:
    """Count [N] bracket citations in the article body (before Sources section)."""
    sources_match = re.search(r"(?:###|##)\s*Sources.*", article, re.DOTALL)
    if sources_match:
        body = article[: sources_match.start()]
    else:
        body = article
    citations = re.findall(r"\[(\d+)\]", body)
    return len(citations)


def count_broken_citations(article: str) -> int:
    """Count body [N] citations that are missing from the Sources section."""
    sources_match = re.search(r"(?:###|##)\s*Sources.*", article, re.DOTALL)
    if not sources_match:
        return 0  # No sources section — handled by has_sources_section
    body = article[: sources_match.start()]
    body_nums = set(int(x) for x in re.findall(r"\[(\d+)\]", body))
    source_nums = set(int(x) for x in re.findall(r"\[(\d+)\]", sources_match.group()))
    missing = body_nums - source_nums
    return len(missing)


def count_urls(article: str) -> int:
    """Count URLs in the article."""
    return len(re.findall(r"https?://[^\s\)]+", article))


def count_unique_domains(article: str) -> int:
    """Count unique URL domains in the article."""
    urls = re.findall(r"https?://([^\s\)]+)", article)
    domains = set(u.split("/")[0] for u in urls)
    return len(domains)


def has_self_referential(article: str) -> bool:
    """Check if article contains self-referential language."""
    for pattern in SELF_REF_PATTERNS:
        if re.search(pattern, article):
            return True
    return False


def has_error_markers(article: str) -> bool:
    """Check if article contains error markers."""
    for marker in ERROR_MARKERS:
        if marker in article:
            return True
    return False


def get_top_domains(article: str, n: int = 5) -> list:
    """Get top N URL domains in the article."""
    urls = re.findall(r"https?://([^\s\)]+)", article)
    domains = [u.split("/")[0] for u in urls]
    return [d for d, _ in Counter(domains).most_common(n)]


# ─── Enrichment ──────────────────────────────────────────────────────────────


def enrich_record(record: dict, model: str, search_api: str) -> dict:
    """Add provenance and quality metadata to a single record."""
    article = record["article"]
    prompt = record["prompt"]

    enriched = dict(record)  # Copy original fields

    # Provenance metadata
    enriched["model"] = model
    enriched["search_api"] = search_api
    enriched["enrichment_timestamp"] = datetime.now(timezone.utc).isoformat()

    # Quality signal metadata
    enriched["language"] = detect_language(article)
    enriched["prompt_language"] = detect_language(prompt)
    enriched["article_length"] = len(article)
    enriched["has_sources_section"] = has_sources_section(article)
    enriched["citation_count"] = count_citations(article)
    enriched["broken_citation_count"] = count_broken_citations(article)
    enriched["url_count"] = count_urls(article)
    enriched["unique_source_domains"] = count_unique_domains(article)
    enriched["top_domains"] = get_top_domains(article)
    enriched["has_self_referential_language"] = has_self_referential(article)
    enriched["has_error_markers"] = has_error_markers(article)

    return enriched


def process_file(name: str, config: dict) -> dict:
    """Process a single JSONL file and produce enriched output."""
    input_path = os.path.join(INPUT_DIR, config["path"])
    output_filename = config["path"].replace(".jsonl", ".enriched.jsonl")
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    records_in = 0
    records_out = 0
    quality_stats = {
        "has_sources": 0,
        "broken_citations": 0,
        "self_referential": 0,
        "error_markers": 0,
        "total_citations": 0,
        "total_urls": 0,
        "total_domains": 0,
    }

    with open(input_path, "r", encoding="utf-8") as fin, open(
        output_path, "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            records_in += 1

            enriched = enrich_record(record, config["model"], config["search_api"])

            # Accumulate stats
            if enriched["has_sources_section"]:
                quality_stats["has_sources"] += 1
            if enriched["broken_citation_count"] > 0:
                quality_stats["broken_citations"] += 1
            if enriched["has_self_referential_language"]:
                quality_stats["self_referential"] += 1
            if enriched["has_error_markers"]:
                quality_stats["error_markers"] += 1
            quality_stats["total_citations"] += enriched["citation_count"]
            quality_stats["total_urls"] += enriched["url_count"]
            quality_stats["total_domains"] += enriched["unique_source_domains"]

            fout.write(json.dumps(enriched, ensure_ascii=False) + "\n")
            records_out += 1

    return {
        "name": name,
        "input_records": records_in,
        "output_records": records_out,
        "output_path": output_path,
        "quality_stats": quality_stats,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("Metadata Enrichment Script")
    print(f"Input directory:  {os.path.abspath(INPUT_DIR)}")
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 70)

    all_results = []
    for name, config in FILES.items():
        print(f"\nProcessing: {name}")
        result = process_file(name, config)
        all_results.append(result)

        qs = result["quality_stats"]
        n = result["output_records"]
        print(f"  Records: {result['input_records']} in → {result['output_records']} out")
        print(f"  Output:  {result['output_path']}")
        print(f"  Quality signals:")
        print(f"    Has Sources section:     {qs['has_sources']}/{n} ({100*qs['has_sources']/n:.1f}%)")
        print(f"    Broken citations:        {qs['broken_citations']}/{n} ({100*qs['broken_citations']/n:.1f}%)")
        print(f"    Self-referential:        {qs['self_referential']}/{n} ({100*qs['self_referential']/n:.1f}%)")
        print(f"    Error markers:           {qs['error_markers']}/{n}")
        print(f"    Total citations:         {qs['total_citations']}")
        print(f"    Total URLs:              {qs['total_urls']}")
        print(f"    Avg unique domains/art:  {qs['total_domains']/n:.1f}")

    # Summary
    print("\n" + "=" * 70)
    print("ENRICHMENT SUMMARY")
    print("=" * 70)
    total_in = sum(r["input_records"] for r in all_results)
    total_out = sum(r["output_records"] for r in all_results)
    print(f"Total records processed: {total_in} in → {total_out} out")
    print(f"Enriched files written to: {os.path.abspath(OUTPUT_DIR)}")

    # Verify enriched files
    print("\nVerification — first record of each enriched file:")
    for name, config in FILES.items():
        output_filename = config["path"].replace(".jsonl", ".enriched.jsonl")
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, "r", encoding="utf-8") as f:
            first = json.loads(f.readline())
        print(f"\n  {name} (ID {first['id']}):")
        print(f"    model: {first['model']}")
        print(f"    language: {first['language']}")
        print(f"    article_length: {first['article_length']}")
        print(f"    has_sources_section: {first['has_sources_section']}")
        print(f"    citation_count: {first['citation_count']}")
        print(f"    broken_citation_count: {first['broken_citation_count']}")
        print(f"    url_count: {first['url_count']}")
        print(f"    unique_source_domains: {first['unique_source_domains']}")
        print(f"    has_self_referential_language: {first['has_self_referential_language']}")
        print(f"    has_error_markers: {first['has_error_markers']}")

    print("\n✅ Enrichment complete.")


if __name__ == "__main__":
    main()
