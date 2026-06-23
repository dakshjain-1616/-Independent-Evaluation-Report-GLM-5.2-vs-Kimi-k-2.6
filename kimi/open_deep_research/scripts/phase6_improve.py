"""
Phase 6: Dataset Improvement Script
Implements deduplication, metadata enrichment, categorization improvements,
and new benchmark dimensions (hallucination risk score, source traceability score).
"""
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

# Configuration
PROJECT_ROOT = Path("/home/azureuser/ModelsEval/kimi/open_deep_research")
INPUT_DIR = PROJECT_ROOT / "tests" / "expt_results"
OUTPUT_DIR = PROJECT_ROOT / "tests" / "expt_results" / "enriched"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "gpt-4.1": INPUT_DIR / "deep_research_bench_gpt-4.1.jsonl",
    "gpt-5": INPUT_DIR / "deep_research_bench_gpt-5.jsonl",
    "claude4-sonnet": INPUT_DIR / "deep_research_bench_claude4-sonnet.jsonl",
}

# Regex patterns
CITATION_RE = re.compile(r"\[(\d+)\]")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
SOURCES_RE = re.compile(r"#{1,3}\s*Sources", re.IGNORECASE)
COUNTER_RE = re.compile(
    r"\b(however|but\b|on the other hand|conversely|in contrast|critics argue|limitations|challenges|drawbacks|nevertheless|yet|although|though|despite|while|whereas)\b",
    re.IGNORECASE,
)
VAGUE_RE = re.compile(
    r"\b(many|several|some|various|numerous|often|frequently|generally|typically|largely|mostly|commonly|usually|probably|likely|may|might|could|would|should)\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?|\b\d+\.?\d*\b")


def compute_record_hash(record: dict) -> str:
    """Stable hash of prompt + article for deduplication."""
    payload = json.dumps({"prompt": record.get("prompt", ""), "article": record.get("article", "")}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def extract_citations(article: str) -> list:
    return [int(m) for m in CITATION_RE.findall(article)]


def extract_source_numbers(article: str) -> set:
    """Extract numbers appearing after URLs or in Sources section lines."""
    sources_section_match = SOURCES_RE.search(article)
    if not sources_section_match:
        return set()
    sources_text = article[sources_section_match.start():]
    # Find numbers that look like citation indices in the sources section
    nums = set()
    for line in sources_text.splitlines():
        # Match patterns like "1. https://..." or "[1] https://..." or "1) ..."
        m = re.match(r"^\s*(?:\[(\d+)\]|(\d+)[\.\)])", line.strip())
        if m:
            nums.add(int(m.group(1) or m.group(2)))
    return nums


def count_words(text: str) -> int:
    return len(text.split())


def count_bold_claims(article: str) -> int:
    return len(BOLD_RE.findall(article))


def count_unsupported_bold(article: str) -> int:
    """Bold spans that do not contain a citation marker inside or immediately after."""
    unsupported = 0
    for m in BOLD_RE.finditer(article):
        start, end = m.start(), m.end()
        # Check inside the bold text
        if CITATION_RE.search(m.group(1)):
            continue
        # Check immediately after the closing **
        after = article[end:end + 30]
        if not CITATION_RE.search(after):
            unsupported += 1
    return unsupported


def count_counter_signals(article: str) -> int:
    return len(COUNTER_RE.findall(article))


def count_vague_words(article: str) -> int:
    return len(VAGUE_RE.findall(article))


def compute_hallucination_risk_score(record: dict) -> float:
    """
    Composite score 0.0 (low risk) to 1.0 (high risk).
    Factors:
    - missing_ref_ratio: citations without source entries / total citations
    - unsupported_bold_ratio: unsupported bold claims / total bold claims (or words if no bold)
    - no_sources_penalty: absence of Sources section
    - low_citation_density: very few citations per 1000 words
    """
    article = record.get("article", "")
    words = count_words(article)
    citations = extract_citations(article)
    source_nums = extract_source_numbers(article)
    has_sources = bool(SOURCES_RE.search(article))
    missing_refs = sum(1 for c in citations if c not in source_nums) if has_sources else len(citations)
    total_citations = len(citations) if citations else 1

    missing_ref_ratio = missing_refs / total_citations
    unsupported_bold = count_unsupported_bold(article)
    total_bold = count_bold_claims(article)
    unsupported_bold_ratio = unsupported_bold / total_bold if total_bold else 0.0

    no_sources_penalty = 0.3 if not has_sources else 0.0

    citation_density = (total_citations / words * 1000) if words else 0.0
    low_citation_penalty = 0.2 if citation_density < 5.0 else 0.0

    # Weighted average
    score = (
        missing_ref_ratio * 0.35
        + unsupported_bold_ratio * 0.25
        + no_sources_penalty
        + low_citation_penalty
    )
    return min(1.0, max(0.0, round(score, 4)))


def compute_source_traceability_score(record: dict) -> float:
    """
    Score 0.0 (untraceable) to 1.0 (fully traceable).
    Measures what fraction of claims (approximated by sentences) have inline citations
    and whether those citations resolve to source entries.
    """
    article = record.get("article", "")
    sentences = [s.strip() for s in re.split(r"[.!?\n]", article) if len(s.strip()) > 20]
    total_sentences = len(sentences) if sentences else 1
    cited_sentences = sum(1 for s in sentences if CITATION_RE.search(s))

    citations = extract_citations(article)
    source_nums = extract_source_numbers(article)
    has_sources = bool(SOURCES_RE.search(article))

    if not has_sources:
        # No sources section = untraceable
        return 0.0

    if not citations:
        return 0.0

    resolved_citations = sum(1 for c in citations if c in source_nums)
    citation_resolution_ratio = resolved_citations / len(citations)

    sentence_citation_ratio = cited_sentences / total_sentences

    score = (
        citation_resolution_ratio * 0.6
        + sentence_citation_ratio * 0.4
    )
    return min(1.0, max(0.0, round(score, 4)))


def enrich_record(record: dict, model_name: str, source_file: str) -> dict:
    article = record.get("article", "")
    words = count_words(article)
    citations = extract_citations(article)
    source_nums = extract_source_numbers(article)
    has_sources = bool(SOURCES_RE.search(article))
    missing_refs = sum(1 for c in citations if c not in source_nums) if has_sources else len(citations)

    enriched = dict(record)
    enriched["_metadata"] = {
        "model_name": model_name,
        "source_file": source_file,
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "record_hash": compute_record_hash(record),
        "word_count": words,
        "citation_count": len(citations),
        "has_sources_section": has_sources,
        "missing_ref_count": missing_refs,
        "bold_claim_count": count_bold_claims(article),
        "unsupported_bold_count": count_unsupported_bold(article),
        "counterargument_signal_count": count_counter_signals(article),
        "vague_word_count": count_vague_words(article),
        "citation_density": round(len(citations) / words * 1000, 2) if words else 0.0,
        "hallucination_risk_score": compute_hallucination_risk_score(record),
        "source_traceability_score": compute_source_traceability_score(record),
    }
    return enriched


def process_file(model_name: str, filepath: Path) -> dict:
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    # Deduplication (exact by hash)
    seen_hashes = set()
    deduped = []
    duplicates = 0
    for r in records:
        h = compute_record_hash(r)
        if h in seen_hashes:
            duplicates += 1
            continue
        seen_hashes.add(h)
        deduped.append(r)

    enriched = [enrich_record(r, model_name, filepath.name) for r in deduped]

    return {
        "model_name": model_name,
        "input_records": len(records),
        "duplicates_removed": duplicates,
        "output_records": len(enriched),
        "records": enriched,
    }


def main():
    summary = {}
    for model_name, filepath in FILES.items():
        result = process_file(model_name, filepath)
        summary[model_name] = {
            "input_records": result["input_records"],
            "duplicates_removed": result["duplicates_removed"],
            "output_records": result["output_records"],
        }
        out_path = OUTPUT_DIR / f"deep_research_bench_{model_name}_enriched.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for r in result["records"]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Wrote {result['output_records']} records to {out_path}")

    summary_path = OUTPUT_DIR / "enrichment_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote summary to {summary_path}")

    # Also write a CSV-style summary for easy inspection
    csv_path = OUTPUT_DIR / "enrichment_summary.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("model_name,input_records,duplicates_removed,output_records\n")
        for model_name, stats in summary.items():
            f.write(f"{model_name},{stats['input_records']},{stats['duplicates_removed']},{stats['output_records']}\n")
    print(f"Wrote CSV summary to {csv_path}")


if __name__ == "__main__":
    main()
