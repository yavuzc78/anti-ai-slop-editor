#!/usr/bin/env python3
"""Verify an edit against its source.

1. Protection check (hard): every protected span in the source must appear,
   byte-identical, in the edit. Fails with exit code 1 otherwise.
2. Meaning-drift check (soft): content words in the edit whose stem does not
   occur in the source. Each is a candidate for added scope or new claims.
3. Sentence-level diff for the change table.

Usage: python3 compare.py source.txt edited.txt [--lang auto] [--protect "a,b"] [--out compare.json]
"""
import argparse
import difflib
import json
import re
import sys
from collections import Counter

from common import detect_lang, lower_keep_len, protected_spans, read_text, sentences, words

STOP = {
    "tr": set("ve veya ile için gibi kadar daha çok en bir bu şu o da de ki ise ama fakat ancak her hem ne mi mı mu mü olan olarak "
              "var yok değil oluyor olur olabilir sadece yalnızca ayrıca bunu buna bunun şunu onu onun sizin bizim".split()),
    "en": set("the a an and or but of to in on at for with by from as is are was were be been being it its this that these those "
              "you your we our they their can will would should may might not no so than then there here also just only use uses used "
              "has have had do does did make makes".split()),
}
# common plain replacements that are never drift
SAFE_WORDS = {"tr": "kullanıyor yapılıyor oluyor artıyor bulunuyor gösteriyor sağlıyor şimdi artık".split(),
              "en": "help shows because about using show helps".split()}


TR_VERB = re.compile(r"[aeıioöuü]?(yor(um|sun|uz|sunuz|lar)?|maktadır|mektedir|maktaydı|mekteydi|maktadırlar|mektedirler|mak|mek)$")
TR_ABIL = re.compile(r"[ae]?bil\w*$")
EN_SUF = re.compile(r"(ing|ed|es|s|ly)$")


def stem(w, lang):
    w = lower_keep_len(w, lang)
    if lang == "tr":
        w = TR_ABIL.sub("", TR_VERB.sub("", w)) or w
        return w[:5]
    return (EN_SUF.sub("", w) or w)[:6]


def check(src, edit, lang="auto", protect=None):
    if lang == "auto":
        lang = detect_lang(src)
    spans = protected_spans(src, protect)
    need = Counter(s["text"] for s in spans)
    violations = []
    for t, k in need.items():
        have = edit.count(t)
        if have < k:
            violations.append({"text": t, "expected": k, "found": have,
                               "type": next(s["type"] for s in spans if s["text"] == t)})

    src_stems = {stem(w, lang) for w in words(src)}
    safe = {stem(w, lang) for w in SAFE_WORDS[lang]}
    drift = []
    for w in words(edit):
        lw = lower_keep_len(w, lang)
        if len(lw) < 4 or lw in STOP[lang]:
            continue
        st = stem(w, lang)
        if st not in src_stems and st not in safe and lw not in [d["word"] for d in drift]:
            drift.append({"word": w, "stem": st})

    s_src = [s for _, s in sentences(src)]
    s_edit = [s for _, s in sentences(edit)]
    changes = []
    sm = difflib.SequenceMatcher(a=s_src, b=s_edit, autojunk=False)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            continue
        changes.append({"op": op, "original": " ".join(s_src[a1:a2]), "edited": " ".join(s_edit[b1:b2])})

    ratio = len(words(edit)) / max(len(words(src)), 1)
    return {
        "lang": lang,
        "protection_ok": not violations,
        "protection_violations": violations,
        "protected_count": len(spans),
        "drift_candidates": drift,
        "length_ratio": round(ratio, 2),
        "changes": changes,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("edited")
    ap.add_argument("--lang", default="auto", choices=["auto", "tr", "en"])
    ap.add_argument("--protect", default="")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = check(read_text(a.source), read_text(a.edited), a.lang, [t for t in a.protect.split(",") if t.strip()])
    js = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(js)
    else:
        sys.stdout.write(js + "\n")
    status = "PASS" if res["protection_ok"] else "FAIL"
    print(f"Protection: {status} ({res['protected_count']} spans, {len(res['protection_violations'])} violations) | "
          f"drift candidates: {len(res['drift_candidates'])} | length ratio {res['length_ratio']}", file=sys.stderr)
    sys.exit(0 if res["protection_ok"] else 1)


if __name__ == "__main__":
    main()
