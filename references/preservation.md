# Preservation rules

The editor removes formula, not meaning. These rules are hard constraints; `compare.py` checks the mechanical ones.

## Protected by default (checked by compare.py)

| Type | Examples |
|---|---|
| Numbers, percentages, currency | `42`, `%35`, `3,5 milyon`, `$1,299`, `12.5 kg` |
| Dates and times | `15 Ekim 2026`, `2026-10-15`, `Q3 2025`, `14:30` |
| URLs, emails, handles | `https://…`, `info@…`, `@aitooler` |
| Quoted text | anything inside `"…"`, `“…”`, `«…»`, `'…'` (min 3 words) |
| Code | inline `` `code` `` and fenced blocks |
| Proper names (heuristic) | Capitalized words not at sentence start: `Rank Math`, `ASELSAN`, `Kapadokya` |
| User-specified | `--protect "term1,term2"` |

A protected span must appear in the edit byte-identical. It may move within the text, but must not be dropped, reworded, reformatted (`%35` → `35%` is a violation) or split.

If removing a sentence would drop a protected span, keep the span by moving it into a neighboring sentence, or keep the sentence.

## Meaning preservation (checked heuristically, judged by you)

`compare.py` lists content words in the edit whose stem does not appear in the source. Each is a drift candidate. For each one decide:

- **Synonym or grammatical form** (`artmaktadır` → `artıyor`, `utilize` → `use`): fine.
- **New claim, scope or detail** (`dijital teknolojilerin gelişiminde` where the source said only `dijital dünyada`): not allowed. Use the safer alternative.

Never:
- add facts, numbers, examples, names, sources or opinions;
- strengthen or weaken a claim (`may help` → `helps`, `etkili olabilir` → `etkilidir`);
- change who did what;
- remove a caveat that limits a claim (hedges that carry real uncertainty stay; reflexive hedges go);
- insert typos, slang, or "imperfections" to look human.

## Worked example (TR)

Source: *Günümüzün hızla değişen dijital dünyasında yapay zekâ önemli bir rol oynamaktadır.*

| Candidate | Verdict |
|---|---|
| Yapay zekâ, dijital teknolojilerin gelişiminde önemli bir rol oynuyor. | ⚠ "gelişiminde" is new scope. Reject. |
| Yapay zekâ dijital dünyada önemli bir rol oynuyor. | ✓ Opener removed, suffix simplified, no new claim. |

Reason line: *Basmakalıp açılış kaldırıldı, -maktadır → -yor. Yeni bilgi eklenmedi.*
