"""Shared helpers: language detection, Turkish-safe lowercasing, sentence splitting, protected spans."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "references")

TR_CHARS = set("ğşıİĞŞçÇöÖüÜ")
TR_WORDS = {"ve", "bir", "bu", "için", "ile", "da", "de", "olarak", "çok", "daha", "gibi", "olan", "ama"}
EN_WORDS = {"the", "and", "of", "to", "is", "in", "that", "for", "with", "it", "this", "are", "be"}


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def detect_lang(text):
    words = re.findall(r"\w+", text.lower())
    if not words:
        return "en"
    tr = sum(w in TR_WORDS for w in words) + 2 * sum(c in TR_CHARS for c in text)
    en = sum(w in EN_WORDS for w in words)
    return "tr" if tr > en else "en"


def lower_keep_len(text, lang):
    """Lowercase without changing string length (Python turns 'İ' into 2 chars)."""
    if lang == "tr":
        text = text.replace("I", "ı").replace("İ", "i")
    else:
        text = text.replace("İ", "i")
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in text)


def load_patterns(lang):
    with open(os.path.join(REF, f"patterns-{lang}.json"), encoding="utf-8") as f:
        data = json.load(f)
    for p in data["patterns"]:
        p["_re"] = re.compile(p["regex"], re.IGNORECASE | re.MULTILINE)
    return data["patterns"]


_SENT = re.compile(r"[^.!?…\n]+(?:[.!?…]+[\"'”’)]*|$)", re.MULTILINE)


def paragraphs(text):
    out, pos = [], 0
    for block in re.split(r"(\n\s*\n)", text):
        if block.strip() and not re.fullmatch(r"\n\s*\n", block):
            out.append((pos, block))
        pos += len(block)
    return out


def sentences(text, base=0):
    out = []
    for m in _SENT.finditer(text):
        s = m.group(0)
        stripped = s.strip()
        if len(re.findall(r"\w+", stripped)) >= 2:
            lead = len(s) - len(s.lstrip())
            out.append((base + m.start() + lead, stripped))
    return out


def words(text):
    return re.findall(r"[^\W\d_]+(?:['’][^\W\d_]+)?", text)


PROTECT_RES = [
    ("url", r"https?://\S+|www\.\S+"),
    ("email", r"[\w.+-]+@[\w-]+\.[\w.]+"),
    ("handle", r"(?<!\w)@\w{2,}"),
    ("code", r"```.*?```|`[^`\n]+`"),
    ("quote", r"[\"“«][^\"”»\n]{8,}?[\"”»]"),
    ("date", r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b|\b\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık|January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{4})?\b|\bQ[1-4]\s?\d{4}\b|\b\d{1,2}:\d{2}\b"),
    ("number", r"(?<!\w)[%$€£₺]?\s?\d+(?:[.,]\d+)*(?:\s?(?:%|kg|km|cm|mm|ml|lt|TL|USD|EUR|GB|MB|TB|GHz|MHz|ms|sn|dk|mg|milyon|milyar|bin|million|billion)\b|%)?"),
]


def protected_spans(text, extra=None):
    spans = []
    taken = [False] * len(text)

    def add(kind, s, e):
        if any(taken[s:e]):
            return
        val = text[s:e].strip()
        if not val:
            return
        for i in range(s, e):
            taken[i] = True
        spans.append({"type": kind, "text": val, "start": s, "end": e})

    for term in (extra or []):
        term = term.strip()
        if term:
            for m in re.finditer(re.escape(term), text):
                add("user", m.start(), m.end())
    for kind, rx in PROTECT_RES:
        for m in re.finditer(rx, text, re.DOTALL):
            add(kind, m.start(), m.end())
    # proper names (heuristic): capitalized words not at sentence start; at sentence start only
    # when followed by another capitalized word. Skip title-case headings and pronouns.
    PRON = {"I", "It", "We", "You", "They", "He", "She", "This", "That", "These", "Those", "There",
            "Bu", "Şu", "O", "Biz", "Siz", "Onlar", "Ben", "Sen", "The", "A", "An", "Bir"}
    for start, sent in sentences(text):
        toks = list(re.finditer(r"[^\s\-–—:;,.!?()“”\"«»]+", sent))
        caps = [t for t in toks if t.group(0)[:1].isupper()]
        if toks and not re.search(r"[.!?…]$", sent) and len(caps) / len(toks) > 0.5:
            continue  # title-case heading
        for i, t in enumerate(toks):
            w = t.group(0)
            if not w[:1].isupper():
                continue
            core = re.split(r"['’]", w)[0]
            if core in PRON or not core:
                continue
            if i == 0:
                nxt = toks[1].group(0) if len(toks) > 1 else ""
                if not nxt[:1].isupper():
                    continue
            s0 = start + t.start()
            add("name", s0, s0 + len(core))
    spans.sort(key=lambda x: x["start"])
    return spans
