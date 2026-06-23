import json
import re
import random
from collections import Counter

paths = {
    "gpt-4.1": "/home/azureuser/ModelsEval/kimi/open_deep_research/tests/expt_results/deep_research_bench_gpt-4.1.jsonl",
    "gpt-5": "/home/azureuser/ModelsEval/kimi/open_deep_research/tests/expt_results/deep_research_bench_gpt-5.jsonl",
    "claude4-sonnet": "/home/azureuser/ModelsEval/kimi/open_deep_research/tests/expt_results/deep_research_bench_claude4-sonnet.jsonl",
}

def load(path):
    recs = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            recs[r["id"]] = r
    return recs

data = {name: load(path) for name, path in paths.items()}

# Select sample IDs present in all three files
common_ids = sorted(set(data["gpt-4.1"]) & set(data["gpt-5"]) & set(data["claude4-sonnet"]))
sample_ids = [1, 10, 25, 50, 75, 90, 100]
sample_ids = [i for i in sample_ids if i in common_ids]
if len(sample_ids) < 5:
    sample_ids = common_ids[:7]

print("Sample IDs:", sample_ids)

# Analysis functions
def analyze_article(text):
    # Citations
    citations = set(re.findall(r'\[(\d+)\]', text))
    has_sources = bool(re.search(r'#{1,3}\s*Sources', text, re.IGNORECASE))
    # Extract sources section text
    sources_match = re.search(r'#{1,3}\s*Sources\s*\n(.*?)(?:\n#{1,3}|\Z)', text, re.DOTALL | re.IGNORECASE)
    source_nums = set()
    source_urls = []
    if sources_match:
        src_text = sources_match.group(1)
        source_nums = set(re.findall(r'\[(\d+)\]', src_text))
        source_urls = re.findall(r'https?://[^\s\)\]]+', src_text)
    
    # Specific numbers (potential hallucination risk if uncited)
    numbers = re.findall(r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d+\b|\b\d+\b', text)
    # Filter out small numbers and years
    significant_numbers = [n for n in numbers if len(n.replace(",","").replace(".","")) >= 3 and not (1900 <= int(n.replace(",","").split(".")[0]) <= 2035)]
    
    # Counterargument signals
    counter_signals = len(re.findall(r'\b(however|but|on the other hand|conversely|in contrast|critics? argue|limitations?|challenges?|drawbacks?)\b', text, re.IGNORECASE))
    
    # Vague language
    vague_words = len(re.findall(r'\b(many|several|some|various|numerous|a lot of|often|frequently|generally|typically|largely|mostly|commonly)\b', text, re.IGNORECASE))
    
    # Unsupported claims: bold sentences without nearby citation
    bold_claims = re.findall(r'\*\*(.+?)\*\*', text)
    unsupported_bold = 0
    for claim in bold_claims:
        # Check if claim contains a citation
        if not re.search(r'\[\d+\]', claim):
            unsupported_bold += 1
    
    # Word count
    words = len(text.split())
    
    return {
        "citations": sorted(citations),
        "has_sources": has_sources,
        "source_nums": sorted(source_nums),
        "source_urls": len(source_urls),
        "missing_source_refs": sorted(citations - source_nums),
        "significant_numbers": len(significant_numbers),
        "counter_signals": counter_signals,
        "vague_words": vague_words,
        "unsupported_bold_claims": unsupported_bold,
        "word_count": words,
        "citation_density": len(citations) / (words/1000) if words > 0 else 0,
    }

results = {}
for sid in sample_ids:
    results[sid] = {}
    for model in ["gpt-4.1", "gpt-5", "claude4-sonnet"]:
        rec = data[model].get(sid)
        if rec:
            results[sid][model] = analyze_article(rec["article"])

# Print summary
for sid in sample_ids:
    print(f"\n=== ID {sid} ===")
    for model in ["gpt-4.1", "gpt-5", "claude4-sonnet"]:
        if model in results[sid]:
            a = results[sid][model]
            print(f"{model}: words={a['word_count']}, citations={len(a['citations'])}, has_sources={a['has_sources']}, missing_refs={len(a['missing_source_refs'])}, sig_numbers={a['significant_numbers']}, counter_signals={a['counter_signals']}, vague={a['vague_words']}, unsupported_bold={a['unsupported_bold_claims']}, citation_density={a['citation_density']:.2f}")

# Aggregate stats across all records for each model
print("\n=== AGGREGATE STATS ===")
for model in ["gpt-4.1", "gpt-5", "claude4-sonnet"]:
    all_missing = []
    all_counters = []
    all_vague = []
    all_unsupported = []
    all_has_sources = []
    all_citation_density = []
    for rec in data[model].values():
        a = analyze_article(rec["article"])
        all_missing.append(len(a["missing_source_refs"]))
        all_counters.append(a["counter_signals"])
        all_vague.append(a["vague_words"])
        all_unsupported.append(a["unsupported_bold_claims"])
        all_has_sources.append(a["has_sources"])
        all_citation_density.append(a["citation_density"])
    print(f"{model}:")
    print(f"  avg missing refs per article: {sum(all_missing)/len(all_missing):.2f}")
    print(f"  articles with sources section: {sum(all_has_sources)}/{len(all_has_sources)} ({sum(all_has_sources)/len(all_has_sources)*100:.1f}%)")
    print(f"  avg counterargument signals: {sum(all_counters)/len(all_counters):.2f}")
    print(f"  avg vague words: {sum(all_vague)/len(all_vague):.2f}")
    print(f"  avg unsupported bold claims: {sum(all_unsupported)/len(all_unsupported):.2f}")
    print(f"  avg citation density (citations per 1000 words): {sum(all_citation_density)/len(all_citation_density):.2f}")

# Save detailed sample data
with open("/home/azureuser/ModelsEval/kimi/open_deep_research/scripts/phase4_results.json", "w") as f:
    json.dump({"sample_ids": sample_ids, "results": results}, f, indent=2)
print("\nSaved phase4_results.json")
