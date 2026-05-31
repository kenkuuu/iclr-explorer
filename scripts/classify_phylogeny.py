"""
classify_phylogeny.py — ICLR 2026 Semantic Topic Phylogeny (100% coverage)
CVPR-style: Task/Domain first. All papers get classified.
"""
import argparse, json, re, sys
from pathlib import Path
from collections import defaultdict

DEFAULT_PHYLOGENY = "data/phylogeny.json"
DEFAULT_INPUT     = "data/papers_raw.json"
DEFAULT_OUTPUT    = "data/papers_classified.json"
MAX_TAGS         = 3
DOMAIN_W         = 5.0
TASK_W           = 3.0
METHOD_W         = 1.0
MIN_PRIMARY_SCORE = 0.3   # lowered for better coverage
SECONDARY_RATIO   = 0.30

# ── catch-all genera for unclassified papers ──
CATCH_ALL_GENERA = [
    {"phylum_id":"P10","phylum_name":"Datasets & Evaluation","class_id":"C10.1","class_name":"Benchmarks & Datasets","order_id":"O10.1.1","order_name":"Evaluation","genus_id":"G10.1.1","genus_name":"Benchmark / Dataset",
     "domain_kws":["benchmark","dataset","evaluation","survey","leaderboard","annotation","crowdsourcing","human evaluation","metric","task evaluation","ablation study","standardized benchmark"],
     "task_kws":["baselines","sota","state-of-the-art","comparison","evaluation protocol"],
     "method_kws":["dataset curation","data collection","human annotation"]},
    {"phylum_id":"P10","phylum_name":"Datasets & Evaluation","class_id":"C10.2","class_name":"General ML","order_id":"O10.2.1","order_name":"Machine Learning","genus_id":"G10.2.1","genus_name":"Machine Learning",
     "domain_kws":["deep learning","machine learning","neural network","artificial intelligence"],
     "task_kws":["supervised learning","unsupervised learning","semi-supervised","multi-task","few-shot","zero-shot","generalization"],
     "method_kws":["training objective","loss function","gradient","backpropagation","embedding","latent space"]},
]

def build_genus_index(tree):
    genera = []
    for phylum in tree["children"]:
        for cls in phylum["children"]:
            for order in cls["children"]:
                for genus in order["children"]:
                    genera.append({
                        "phylum_id":   phylum["id"],  "phylum_name": phylum["name"],
                        "class_id":    cls["id"],     "class_name":  cls["name"],
                        "order_id":    order["id"],   "order_name":  order["name"],
                        "genus_id":    genus["id"],   "genus_name":  genus["name"],
                        "domain_kws":  [kw.lower() for kw in genus.get("domain", [])],
                        "task_kws":    [kw.lower() for kw in genus.get("task",   [])],
                        "method_kws":  [kw.lower() for kw in genus.get("method", [])],
                    })
    return genera + CATCH_ALL_GENERA

def kw_hits(text, kws):
    s = 0.0
    for kw in kws:
        n = len(re.findall(r"\b" + re.escape(kw) + r"\b", text))
        if n > 0:
            s += 1.0 + 0.25 * (n - 1)
    return s

def score_genus(g, title, kws_text, abstract):
    front = title + " " + kws_text
    back  = abstract[:600]
    d = kw_hits(front,g["domain_kws"])*DOMAIN_W + kw_hits(back,g["domain_kws"])*(DOMAIN_W*0.5)
    t = kw_hits(front,g["task_kws"])  *TASK_W   + kw_hits(back,g["task_kws"])  *(TASK_W*0.5)
    m = kw_hits(front,g["method_kws"])*METHOD_W + kw_hits(back,g["method_kws"])*(METHOD_W*0.5)
    return d + t + m

def classify_paper(paper, genera):
    title    = paper.get("title",    "").lower()
    kws_text = " ".join(paper.get("keywords", [])).lower()
    abstract = paper.get("abstract", "").lower()

    scored = [(score_genus(g, title, kws_text, abstract), g) for g in genera]
    scored = [(s, g) for s, g in scored if s > 0]
    scored.sort(key=lambda x: -x[0])

    if not scored:
        # absolute fallback: "Machine Learning" catch-all
        fallback = CATCH_ALL_GENERA[-1]
        return [{"phylum": fallback["phylum_name"], "class": fallback["class_name"],
                 "order": fallback["order_name"], "genus": fallback["genus_name"],
                 "phylum_id": fallback["phylum_id"], "score": 0.01}]

    best = scored[0][0]
    if best < MIN_PRIMARY_SCORE:
        # still below threshold → use highest scorer as primary
        s, g = scored[0]
        return [{"phylum": g["phylum_name"], "class": g["class_name"],
                 "order": g["order_name"], "genus": g["genus_name"],
                 "phylum_id": g["phylum_id"], "score": round(s, 2)}]

    threshold = best * SECONDARY_RATIO
    results, used_phyla = [], set()
    for s, g in scored:
        if len(results) >= MAX_TAGS: break
        if s < threshold: break
        if g["phylum_id"] in used_phyla: continue
        results.append({"phylum": g["phylum_name"], "class": g["class_name"],
                        "order": g["order_name"], "genus": g["genus_name"],
                        "phylum_id": g["phylum_id"], "score": round(s, 2)})
        used_phyla.add(g["phylum_id"])
    return results

def classify_all(papers, genera):
    n = len(papers)
    results = []
    for i, paper in enumerate(papers):
        topics = classify_paper(paper, genera)
        results.append({**paper, "topics": topics,
            "primary_phylum": topics[0]["phylum"]    if topics else None,
            "primary_class":  topics[0]["class"]     if topics else None,
            "primary_order":  topics[0]["order"]     if topics else None,
            "primary_genus":  topics[0]["genus"]     if topics else None,
            "primary_topic":    topics[0]["phylum_id"] if topics else None,
            "secondary_topics": [t["phylum_id"] for t in topics[1:]] if topics else [],
        })
        if (i+1) % 500 == 0 or (i+1) == n:
            print(f"  {i+1:,}/{n:,}", flush=True)
    return results

def print_stats(classified):
    total = len(classified)
    tagged = sum(1 for p in classified if p.get("topics"))
    multi  = sum(1 for p in classified if len(p.get("topics",[])) > 1)
    null   = total - tagged
    from collections import Counter
    ph = Counter(t["phylum"] for p in classified for t in p.get("topics",[]))
    ge = Counter(t["genus"]  for p in classified for t in p.get("topics",[]))

    print(f"\n{'='*65}")
    print(f"ICLR 2026 Phylogeny  |  {total:,} papers  |  {tagged/total*100:.1f}% tagged  |  avg {sum(len(p.get('topics',[])) for p in classified)/total:.2f} tags")
    print(f"{'='*65}")
    for name, cnt in ph.most_common():
        bar = "█"*int(cnt/total*40)
        print(f"  {cnt:5d} ({cnt/total*100:4.1f}%)  {name:<45} {bar}")
    print(f"\nTop genera:")
    for name, cnt in ge.most_common(20):
        print(f"  {cnt:5d}  {name}")
    print(f"{'='*65}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phylogeny", default=DEFAULT_PHYLOGENY)
    p.add_argument("--input",     default=DEFAULT_INPUT)
    p.add_argument("--output",    default=DEFAULT_OUTPUT)
    p.add_argument("--stats",     action="store_true")
    args = p.parse_args()
    for f in [args.phylogeny, args.input]:
        if not Path(f).exists():
            print(f"Error: {f} not found", file=sys.stderr); sys.exit(1)
    with open(args.phylogeny, encoding="utf-8") as f: tree = json.load(f)
    with open(args.input,     encoding="utf-8") as f: papers = json.load(f)
    genera = build_genus_index(tree)
    print(f"[phylogeny] {len(papers):,} papers / {len(genera)} genera (incl. catch-all)")
    classified = classify_all(papers, genera)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)
    tagged = sum(1 for p in classified if p.get("topics"))
    print(f"[phylogeny] Done: {tagged:,}/{len(classified):,} tagged ({tagged/len(classified)*100:.1f}%)")
    if args.stats: print_stats(classified)

if __name__ == "__main__": main()
