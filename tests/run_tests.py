#!/usr/bin/env python3
"""Run sample texts through scan.py and compare with expected-results.json,
plus protection/drift checks for compare.py. Exit 1 on any failure."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from scan import scan  # noqa: E402
from compare import check  # noqa: E402

fails = 0
expected = json.load(open(os.path.join(HERE, "expected-results.json"), encoding="utf-8"))

for lang in ("tr", "en"):
    for s in json.load(open(os.path.join(HERE, f"samples-{lang}.json"), encoding="utf-8")):
        exp = expected.get(s["id"])
        if not exp:
            continue
        r = scan(s["text"], lang, s["genre"])
        fired = {h["id"] for h in r["hits"]} | {x["id"] for x in r["structure"]}
        errs = []
        if "min_score" in exp and r["score"] < exp["min_score"]:
            errs.append(f"score {r['score']} < {exp['min_score']}")
        if "max_score" in exp and r["score"] > exp["max_score"]:
            errs.append(f"score {r['score']} > {exp['max_score']}")
        miss = set(exp.get("must_hit", [])) - fired
        if miss:
            errs.append(f"missing {sorted(miss)}")
        fp = set(exp.get("must_not_hit", [])) & fired
        if fp:
            errs.append(f"false positive {sorted(fp)}")
        print(f"{'PASS' if not errs else 'FAIL'}  {s['id']:<26} score={r['score']:<3} {'; '.join(errs)}")
        fails += bool(errs)

# compare.py checks
src = "Günümüzün hızla değişen dijital dünyasında yapay zekâ önemli bir rol oynamaktadır. Rank Math 2025'te %35 büyüdü."
good = "Yapay zekâ dijital dünyada önemli bir rol oynuyor. Rank Math 2025'te %35 büyüdü."
drift = "Yapay zekâ, dijital teknolojilerin gelişiminde önemli bir rol oynuyor. Rank Math 2024'te %35 büyüdü."
g, d = check(src, good, "tr"), check(src, drift, "tr")
cases = [
    ("compare: safe edit passes protection", g["protection_ok"]),
    ("compare: safe edit has no drift", not g["drift_candidates"]),
    ("compare: changed year fails protection", not d["protection_ok"]),
    ("compare: 'gelişiminde' flagged as drift", any(x["word"] == "gelişiminde" for x in d["drift_candidates"])),
]
for name, ok in cases:
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    fails += not ok

print(f"\n{'All tests passed' if not fails else f'{fails} failing'}")
sys.exit(1 if fails else 0)
