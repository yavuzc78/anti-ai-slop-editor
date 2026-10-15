#!/usr/bin/env python3
"""Scan text for formulaic phrasing and mechanical structure.

Outputs JSON: phrase hits, structural findings, protected spans and a
Slop Density Score (0-100, lower is better). The score measures stock
phrasing density. It is NOT a probability that the text was AI-generated.

Usage: python3 scan.py input.txt [--lang auto|tr|en] [--genre blog] [--protect "a,b"] [--out scan.json]
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter

from common import (detect_lang, load_patterns, lower_keep_len, paragraphs,
                    protected_spans, read_text, sentences, words)

SEV_W = {"low": 1, "medium": 2, "high": 3}

# per-genre category multipliers and limits
GENRES = {
    "blog":   {"mult": {}, "formal_limit": 0.20, "bands": (15, 35)},
    "seo":    {"mult": {"closing": 0.7}, "formal_limit": 0.20, "bands": (18, 40)},
    "email":  {"mult": {"chatbot_residue": 1.5, "intensifier": 1.3}, "formal_limit": 0.10, "bands": (10, 25)},
    "review": {"mult": {"hedge": 0.6, "closing": 0.6, "buzzword": 1.3}, "formal_limit": 0.15, "bands": (15, 35)},
    "formal": {"mult": {"formal_overload": 0.0, "transition": 0.5, "hedge": 0.7}, "formal_limit": 1.0, "bands": (25, 50)},
    "social": {"mult": {"intensifier": 0.6}, "formal_limit": 0.10, "bands": (12, 30)},
}

CONNECTORS = {
    "tr": ["ayrıca", "bunun yanı sıra", "buna ek olarak", "öte yandan", "diğer taraftan", "bununla birlikte", "dahası", "üstelik"],
    "en": ["moreover", "furthermore", "additionally", "in addition", "however", "consequently", "nevertheless", "also"],
}
CLOSING_RE = {
    "tr": r"^(sonuç olarak|özetle|kısacası|toparlamak gerekirse|son olarak|tüm bu)",
    "en": r"^(in conclusion|to sum up|in summary|ultimately|all in all|overall|in short)",
}
TRIPLET_RE = {
    "tr": r"\b[\wçğıöşü]+(?: [\wçğıöşü]+)?, [\wçğıöşü]+(?: [\wçğıöşü]+)? ve [\wçğıöşü]+",
    "en": r"\b\w+(?: \w+)?, \w+(?: \w+)?,? and \w+",
}
CONTRAST_RE = {
    "tr": r"(sadece|yalnızca)[^.]{1,50}(değil|değildir)[^.]{0,20}(aynı zamanda|ayrıca|da|de)\b|\bdeğil,? (aksine|bilakis)",
    "en": r"\bnot (just|only|merely)\b[^.]{1,50}\bbut\b|\bit'?s not [^.]{1,40}[,;—–-]+ ?it'?s\b",
}
HEDGE_WORDS = {
    "tr": ["olabilir", "genellikle", "bazı durumlarda", "bir ölçüde", "muhtemelen", "kısmen"],
    "en": ["may", "might", "could", "perhaps", "possibly", "potentially", "arguably", "generally"],
}
FORMAL_END = re.compile(r"(mektedir|maktadır|mektedirler|maktadırlar|mıştır|miştir|muştur|müştür|dır|dir|dur|dür|tır|tir|tur|tür)[.!?…\"”’)]*$")
STRONG_FORMAL_END = re.compile(r"(mektedir|maktadır)(ler|lar)?[.!?…\"”’)]*$")
PASSIVE = re.compile(r"\w+(ılmaktadır|ilmektedir|ulmaktadır|ülmektedir|ılmıştır|ilmiştir|ulmuştur|ülmüştür|ınmaktadır|inmektedir)")


def scan(text, lang="auto", genre="blog", protect=None):
    if lang == "auto":
        lang = detect_lang(text)
    g = GENRES.get(genre, GENRES["blog"])
    low = lower_keep_len(text, lang)
    pats = load_patterns(lang)
    sents = sentences(text)
    n_words = len(words(text))

    hits = []
    for start, sent in sents:
        lsent = low[start:start + len(sent)]
        for p in pats:
            if p["id"] == "tr040":  # handled as density (S11), not per hit
                continue
            for m in p["_re"].finditer(lsent):
                hits.append({
                    "id": p["id"], "category": p["category"], "severity": p["severity"],
                    "match": sent[m.start():m.end()], "start": start + m.start(), "end": start + m.end(),
                    "sentence": sent, "hint": p["hint"],
                })
    # dedupe overlapping hits: keep higher severity
    hits.sort(key=lambda h: (h["start"], -SEV_W[h["severity"]]))
    kept, last_end = [], -1
    for h in hits:
        if h["start"] < last_end:
            if SEV_W[h["severity"]] > SEV_W[kept[-1]["severity"]]:
                kept[-1] = h
                last_end = h["end"]
            continue
        kept.append(h)
        last_end = h["end"]
    hits = kept

    struct = structural(text, low, lang, sents, n_words, g)

    phrase_pts = sum(SEV_W[h["severity"]] * g["mult"].get(h["category"], 1.0) for h in hits)
    struct_pts = sum(s["points"] for s in struct)
    denom = max(n_words, 60)
    score = min(100, round((phrase_pts + struct_pts) / denom * 100 * 1.2))
    lo, hi = g["bands"]
    band = "clean" if score < lo else "moderate" if score <= hi else "heavy"

    cats = Counter(h["category"] for h in hits)
    return {
        "lang": lang, "genre": genre, "words": n_words, "sentences": len(sents),
        "score": score, "band": band,
        "note": "Slop Density Score measures formulaic phrasing and mechanical structure. It is not an AI-detection probability.",
        "category_counts": dict(cats),
        "hits": hits, "structure": struct,
        "protected": protected_spans(text, protect),
    }


def structural(text, low, lang, sents, n_words, g):
    out = []
    per300 = max(n_words, 1) / 300

    def add(sid, desc, points, evidence=None):
        out.append({"id": sid, "description": desc, "points": round(points, 1), "evidence": evidence or []})

    # S01 repeated sentence starts
    firsts = [lower_keep_len(s, lang).split()[0].strip(",.;:\"'“”") for _, s in sents if s.split()]
    c = Counter(firsts)
    if len(firsts) >= 6:
        for w, k in c.most_common(3):
            if k >= 3 and k / len(firsts) >= 0.25 and len(w) > 1:
                add("S01", f"{k} of {len(firsts)} sentences start with '{w}'", 2 + k)
    for pstart, ptext in paragraphs(text):
        ps = sentences(ptext, pstart)
        pf = Counter(lower_keep_len(s, lang).split()[0] for _, s in ps if s.split())
        for w, k in pf.items():
            if k >= 3:
                add("S01", f"'{w}' opens {k} sentences in one paragraph", 2 + k, [ptext[:80]])

    # S02 uniform sentence length
    lens = [len(s.split()) for _, s in sents]
    if len(lens) >= 6:
        mean = statistics.mean(lens)
        cv = statistics.pstdev(lens) / mean if mean else 0
        if cv < 0.25:
            add("S02", f"Sentence lengths are very uniform (CV={cv:.2f}, mean {mean:.0f} words)", 4)

    # S03 triplets
    trip = re.findall(TRIPLET_RE[lang], low)
    if len(trip) >= 3 and len(trip) / per300 >= 3:
        add("S03", f"{len(trip)} triplet lists (A, B and C)", len(trip) * 1.5, trip[:5])

    # S04 mechanical conclusion
    paras = paragraphs(text)
    if len(paras) >= 3:
        last = lower_keep_len(paras[-1][1].strip(), lang)
        if re.match(CLOSING_RE[lang], last):
            add("S04", "Final paragraph opens with a closing formula", 4, [paras[-1][1][:100]])
        else:
            stem = lambda w: w[:5]
            prev = {stem(w) for _, p in paras[:-1] for w in words(lower_keep_len(p, lang)) if len(w) > 4}
            lastw = [stem(w) for w in words(last) if len(w) > 4]
            if len(lastw) >= 8 and sum(w in prev for w in lastw) / len(lastw) >= 0.7:
                add("S04", "Final paragraph mostly restates earlier content", 3, [paras[-1][1][:100]])

    # S05 contrast frames
    con = re.findall(CONTRAST_RE[lang], low)
    if len(con) >= 2 and len(con) / per300 >= 2:
        add("S05", f"{len(con)} 'not X but Y' frames", len(con) * 2)

    # S07 colon / dash reveals in prose
    reveals = [s for _, s in sents if re.search(r"\w[:—–]\s+\w", s) and not s.startswith(("-", "*", "#"))]
    if len(reveals) >= 3 and len(reveals) / per300 >= 3:
        add("S07", f"{len(reveals)} colon/dash reveals", len(reveals))

    # S08 question chains
    qs = [s.endswith("?") for _, s in sents]
    chains = sum(1 for i in range(1, len(qs)) if qs[i] and qs[i - 1])
    if chains:
        add("S08", f"{chains} consecutive rhetorical questions", chains * 2)

    # S11 / S12 Turkish formal density
    if lang == "tr" and sents:
        strong = [s for _, s in sents if STRONG_FORMAL_END.search(s)]
        share = len(strong) / len(sents)
        if share > g["formal_limit"] and len(strong) >= 2:
            add("S11", f"{len(strong)}/{len(sents)} sentences end in -mektedir/-maktadır ({share:.0%}, limit {g['formal_limit']:.0%})",
                (share - g["formal_limit"]) * 30, strong[:3])
        verbs = len([s for _, s in sents if FORMAL_END.search(s)]) or 1
        passive = len(PASSIVE.findall(low))
        if passive >= 3 and passive / max(len(sents), 1) > 0.3 and g["formal_limit"] < 1.0:
            add("S12", f"High passive density ({passive} passive formal verbs)", passive)

    # S13 connector stacking
    cons = CONNECTORS[lang]
    starts = [any(lower_keep_len(s, lang).startswith(c) for c in cons) for _, s in sents]
    run = best = 0
    for b in starts:
        run = run + 1 if b else 0
        best = max(best, run)
    total_con = sum(starts)
    if best >= 3 or (len(sents) >= 6 and total_con / len(sents) > 0.3):
        add("S13", f"Connector-led sentences: {total_con} (longest run {best})", total_con)

    # S14 hedge stacking
    hw = HEDGE_WORDS[lang]
    stacked = [s for _, s in sents if sum(len(re.findall(r"\b" + re.escape(h) + r"\b", lower_keep_len(s, lang))) for h in hw) >= 2]
    if stacked:
        add("S14", f"{len(stacked)} sentences with stacked hedges", len(stacked) * 2 * g["mult"].get("hedge", 1.0), stacked[:3])

    # S20 over-signposting in short text
    sign = {"tr": r"\b(ilk olarak|ikinci olarak|üçüncü olarak|son olarak)\b", "en": r"\b(first(ly)?|second(ly)?|third(ly)?|finally|lastly),"}[lang]
    sp = re.findall(sign, low)
    if len(sp) >= 3 and n_words < 400:
        add("S20", f"{len(sp)} signposts in a short text", 3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--lang", default="auto", choices=["auto", "tr", "en"])
    ap.add_argument("--genre", default="blog", choices=list(GENRES))
    ap.add_argument("--protect", default="")
    ap.add_argument("--out")
    a = ap.parse_args()
    res = scan(read_text(a.input), a.lang, a.genre, [t for t in a.protect.split(",") if t.strip()])
    js = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"Slop Density: {res['score']} ({res['band']}) | {len(res['hits'])} phrase hits | "
              f"{len(res['structure'])} structural findings | {len(res['protected'])} protected spans -> {a.out}")
    else:
        sys.stdout.write(js + "\n")


if __name__ == "__main__":
    main()
