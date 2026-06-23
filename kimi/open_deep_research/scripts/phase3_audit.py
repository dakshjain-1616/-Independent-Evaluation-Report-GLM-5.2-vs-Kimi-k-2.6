import json
import os
import re
from collections import Counter, defaultdict

BASE = "/home/azureuser/ModelsEval/kimi/open_deep_research/tests/expt_results"
files = {
    "gpt-4.1": os.path.join(BASE, "deep_research_bench_gpt-4.1.jsonl"),
    "gpt-5": os.path.join(BASE, "deep_research_bench_gpt-5.jsonl"),
    "claude4-sonnet": os.path.join(BASE, "deep_research_bench_claude4-sonnet.jsonl"),
}

def load_records(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                records.append(rec)
            except json.JSONDecodeError as e:
                records.append({"__parse_error__": True, "line": i, "error": str(e)})
    return records

results = {}
for name, path in files.items():
    results[name] = load_records(path)

# Schema validation
schema_issues = defaultdict(list)
for name, recs in results.items():
    for i, rec in enumerate(recs):
        if "__parse_error__" in rec:
            schema_issues[name].append(f"Line {i+1}: JSON parse error: {rec['error']}")
            continue
        missing = []
        for key in ["id", "prompt", "article"]:
            if key not in rec:
                missing.append(key)
        if missing:
            schema_issues[name].append(f"Line {i+1}: missing keys {missing}")
        else:
            if not isinstance(rec["id"], int):
                schema_issues[name].append(f"Line {i+1}: id is not int ({type(rec['id'])})")
            if not isinstance(rec["prompt"], str):
                schema_issues[name].append(f"Line {i+1}: prompt is not str")
            if not isinstance(rec["article"], str):
                schema_issues[name].append(f"Line {i+1}: article is not str")

# ID sequences
id_sets = {}
id_gaps = {}
for name, recs in results.items():
    ids = [r["id"] for r in recs if "id" in r and isinstance(r["id"], int)]
    id_sets[name] = set(ids)
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    id_gaps[name] = {
        "count": len(ids),
        "unique": len(set(ids)),
        "duplicates": duplicates,
        "min": min(ids) if ids else None,
        "max": max(ids) if ids else None,
        "missing_from_1_100": sorted(set(range(1, 101)) - set(ids)),
    }

# Cross-file prompt consistency
prompt_by_id = defaultdict(dict)
for name, recs in results.items():
    for r in recs:
        if "id" in r and "prompt" in r:
            prompt_by_id[r["id"]][name] = r["prompt"]

prompt_mismatches = []
for rid, prompts in prompt_by_id.items():
    if len(prompts) > 1:
        vals = list(prompts.values())
        if len(set(vals)) > 1:
            prompt_mismatches.append(rid)

# Exact duplicate articles within each file
exact_dupes = {}
for name, recs in results.items():
    articles = [r.get("article", "") for r in recs]
    seen = {}
    dups = []
    for i, art in enumerate(articles):
        if art in seen:
            dups.append((seen[art], i))
        else:
            seen[art] = i
    exact_dupes[name] = dups

# Near-duplicate prompts within each file (simple heuristic: strip whitespace, lowercase)
near_dupes = {}
for name, recs in results.items():
    norm = {}
    dups = []
    for i, r in enumerate(recs):
        p = r.get("prompt", "").strip().lower()
        if p in norm:
            dups.append((norm[p], i))
        else:
            norm[p] = i
    near_dupes[name] = dups

# Check for empty articles or prompts
empty_issues = defaultdict(list)
for name, recs in results.items():
    for i, r in enumerate(recs):
        if r.get("article", "").strip() == "":
            empty_issues[name].append(f"Line {i+1}: empty article")
        if r.get("prompt", "").strip() == "":
            empty_issues[name].append(f"Line {i+1}: empty prompt")

# Broken references: check article for citation markers like [1], [2], etc.
# and see if they appear in a Sources section. Very basic heuristic.
ref_issues = defaultdict(list)
for name, recs in results.items():
    for i, r in enumerate(recs):
        art = r.get("article", "")
        citations = set(re.findall(r'\[(\d+)\]', art))
        has_sources = "### Sources" in art or "## Sources" in art or "Sources" in art
        if citations and not has_sources:
            ref_issues[name].append(f"Line {i+1}: citations found but no Sources section")

# Output summary
print("=== SCHEMA ISSUES ===")
for name, issues in schema_issues.items():
    print(f"{name}: {len(issues)} issues")
    for iss in issues[:5]:
        print("  ", iss)

print("\n=== ID GAPS ===")
for name, info in id_gaps.items():
    print(f"{name}: count={info['count']}, unique={info['unique']}, min={info['min']}, max={info['max']}, missing={info['missing_from_1_100']}")

print("\n=== PROMPT MISMATCHES ACROSS FILES ===")
print(f"Count: {len(prompt_mismatches)}")
if prompt_mismatches:
    print("IDs:", prompt_mismatches[:10])

print("\n=== EXACT DUPLICATE ARTICLES ===")
for name, dups in exact_dupes.items():
    print(f"{name}: {len(dups)} exact duplicate pairs")

print("\n=== NEAR DUPLICATE PROMPTS ===")
for name, dups in near_dupes.items():
    print(f"{name}: {len(dups)} near duplicate pairs")

print("\n=== EMPTY ISSUES ===")
for name, issues in empty_issues.items():
    print(f"{name}: {len(issues)} empty issues")

print("\n=== REFERENCE ISSUES ===")
for name, issues in ref_issues.items():
    print(f"{name}: {len(issues)} reference issues")

# Save detailed results for markdown generation
with open("/home/azureuser/ModelsEval/kimi/open_deep_research/scripts/phase3_results.json", "w") as f:
    json.dump({
        "schema_issues": {k:v for k,v in schema_issues.items()},
        "id_gaps": id_gaps,
        "prompt_mismatches": prompt_mismatches,
        "exact_dupes": {k: [[a,b] for a,b in v] for k,v in exact_dupes.items()},
        "near_dupes": {k: [[a,b] for a,b in v] for k,v in near_dupes.items()},
        "empty_issues": {k:v for k,v in empty_issues.items()},
        "ref_issues": {k:v for k,v in ref_issues.items()},
    }, f, indent=2)
print("\nSaved phase3_results.json")
