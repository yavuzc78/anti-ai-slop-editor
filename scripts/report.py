#!/usr/bin/env python3
"""Build the user-facing report from scan + compare output.

Usage: python3 report.py scan.json [compare.json] [--after scan_after.json] [--changes changes.json] [--edited edited.txt] [--format md|json]

changes.json (written by Claude): [{"original","edited","severity","reason","category"}]
"""
import argparse
import json

L = {
    "tr": {"title": "Anlatım Raporu", "words": "kelime", "score": "Slop Yoğunluğu", "lower": "düşük daha iyi", "changes": "Değişiklikler",
           "orig": "Orijinal", "edit": "Düzenleme", "sev": "Şiddet", "why": "Gerekçe", "struct": "Yapısal bulgular",
           "drift": "Anlam kayması adayları", "drift_note": "Kaynakta karşılığı olmayan kelimeler. Yeni bilgi ekleniyorsa geri al.",
           "prot": "Koruma denetimi", "ok": "Tüm korunan ifadeler yerinde", "fail": "Korunan ifade kayboldu veya değişti",
           "final": "Son metin", "hits": "Tespit edilen kalıplar", "note": "Bu skor metnin yapay zekâ tarafından yazıldığını göstermez; basmakalıp ve mekanik anlatım yoğunluğunu ölçer.",
           "sevs": {"low": "Düşük", "medium": "Orta", "high": "Yüksek"}},
    "en": {"title": "Writing Report", "words": "words", "score": "Slop Density", "lower": "lower is better", "changes": "Changes",
           "orig": "Original", "edit": "Edit", "sev": "Severity", "why": "Reason", "struct": "Structural findings",
           "drift": "Meaning-drift candidates", "drift_note": "Words with no source in the original. Revert if they add new information.",
           "prot": "Protection check", "ok": "All protected spans intact", "fail": "Protected span lost or altered",
           "final": "Final text", "hits": "Detected patterns", "note": "This score does not indicate AI authorship; it measures formulaic and mechanical phrasing.",
           "sevs": {"low": "Low", "medium": "Medium", "high": "High"}},
}


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def build_md(scan, comp=None, after=None, changes=None, edited=None):
    t = L.get(scan["lang"], L["en"])
    out = [f"## {t['title']}", ""]
    score = f"**{t['score']}: {scan['score']}"
    if after:
        score += f" → {after['score']}"
    out += [score + f"** ({t['lower']}) · {scan['words']} {t['words']} · {scan['genre']}", "", f"_{t['note']}_", ""]

    if changes:
        out += [f"### {t['changes']}", "", f"| {t['orig']} | {t['edit']} | {t['sev']} | {t['why']} |", "|---|---|---|---|"]
        for c in changes:
            out.append(f"| {esc(c.get('original',''))} | {esc(c.get('edited','') or '—')} | "
                       f"{t['sevs'].get(c.get('severity','medium'), c.get('severity',''))} | {esc(c.get('reason',''))} |")
        out.append("")
    elif scan["hits"]:
        out += [f"### {t['hits']}", "", f"| ID | {t['orig']} | {t['sev']} | {t['why']} |", "|---|---|---|---|"]
        for h in scan["hits"]:
            out.append(f"| {h['id']} | {esc(h['match'])} | {t['sevs'][h['severity']]} | {esc(h['hint'])} |")
        out.append("")

    if scan["structure"]:
        out += [f"### {t['struct']}", ""]
        out += [f"- **{s['id']}** {s['description']}" for s in scan["structure"]]
        out.append("")

    if comp:
        out += [f"### {t['prot']}", ""]
        if comp["protection_ok"]:
            out.append(f"✓ {t['ok']} ({comp['protected_count']})")
        else:
            out.append(f"✗ {t['fail']}:")
            out += [f"- `{v['text']}` ({v['type']})" for v in comp["protection_violations"]]
        out.append("")
        if comp["drift_candidates"]:
            out += [f"### {t['drift']}", "", t["drift_note"], ""]
            out.append(", ".join(f"`{d['word']}`" for d in comp["drift_candidates"]))
            out.append("")

    if edited:
        out += [f"### {t['final']}", "", edited.strip(), ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scan")
    ap.add_argument("compare", nargs="?")
    ap.add_argument("--after")
    ap.add_argument("--changes")
    ap.add_argument("--edited")
    ap.add_argument("--format", default="md", choices=["md", "json"])
    a = ap.parse_args()
    ld = lambda p: json.load(open(p, encoding="utf-8")) if p else None
    scan, comp, after, changes = ld(a.scan), ld(a.compare), ld(a.after), ld(a.changes)
    edited = open(a.edited, encoding="utf-8").read() if a.edited else None
    if a.format == "json":
        print(json.dumps({"before": scan["score"], "after": after["score"] if after else None,
                          "changes": changes or [], "protection_ok": comp["protection_ok"] if comp else None,
                          "drift_candidates": comp["drift_candidates"] if comp else [],
                          "structure": scan["structure"], "final_text": edited}, ensure_ascii=False, indent=1))
    else:
        print(build_md(scan, comp, after, changes, edited))


if __name__ == "__main__":
    main()
