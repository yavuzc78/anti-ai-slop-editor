# Structural patterns (language-independent)

`scan.py` approximates these with heuristics. Confirm each one by reading the text; structure is where context matters most.

| ID | Pattern | How scan.py detects it | What to do |
|---|---|---|---|
| S01 | Repeated sentence starts | Same first word (or first 2 words) opens ≥3 sentences in a paragraph or ≥25% of all sentences | Vary or merge sentences. Don't swap in synonyms mechanically. |
| S02 | Uniform sentence length | Coefficient of variation of sentence length < 0.25 over ≥6 sentences | Combine some, split others. Rhythm should follow meaning. |
| S03 | Triplet lists | "A, B and C" / "A, B ve C" constructions; flagged when ≥3 per 300 words | Keep the items that matter. Two or four is fine. |
| S04 | Mechanical conclusion | Final paragraph opens with a closing marker or repeats ≥40% of content words from earlier paragraphs | Delete or replace with a real takeaway, next step or open question. |
| S05 | "Not X, but Y" overuse | ≥2 contrast frames per 300 words | Keep at most one. State the claim directly. |
| S06 | Uniform paragraphs | Every paragraph has the same sentence count (±1) over ≥4 paragraphs | Let paragraph length follow content. |
| S07 | Colon/em-dash reveal | ≥3 "X: Y" or "X — Y" reveals per 300 words in prose | Rewrite as plain sentences. |
| S08 | Rhetorical question chains | ≥2 consecutive question sentences in prose | Keep one or answer directly. |
| S09 | Heading-per-paragraph | Markdown heading before nearly every short paragraph | Merge sections. |
| S10 | Bold-label bullets | ≥4 bullets of form "**Label:** text" | Use prose when items are related. |
| S11 | Formal suffix density (TR) | `-mektedir/-maktadır` share of sentence endings above genre limit | Convert most to `-iyor/-ır`; keep in formal genre. |
| S12 | Passive density (TR) | `-ılmaktadır/-ilmektedir/-ılmıştır` > 30% of verbs | Use active voice where the agent is known. |
| S13 | Connector stacking | ≥3 consecutive sentences start with a connector (Moreover / Ayrıca / Bunun yanı sıra) | Drop most connectors. |
| S14 | Hedge stacking | ≥2 hedges in one sentence | Keep one or none. |
| S15 | Emoji/bullet decoration | Emoji used as bullet markers in non-social genre | Remove. |
| S16 | Generic examples | "for example, a business" / "örneğin bir işletme" without specifics | Use a real example from the source or cut. Never invent one. |
| S17 | Symmetric pros/cons | Pros and cons lists of identical length | Check if balance is real. |
| S18 | Restated title | First sentence repeats the title/heading words | Start with new information. |
| S19 | Question-headings | ≥3 headings phrased as questions in non-FAQ text | Use statements. |
| S20 | Over-signposting | "First... Second... Finally..." / "İlk olarak... İkinci olarak... Son olarak..." in short text | Remove signposts under ~400 words. |

## Turkish notes

- Turkish is agglutinative. Word-repetition counts on surface forms undercount. `scan.py` uses a crude stem (first 5 letters) for repetition checks.
- `-mektedir` is not wrong. Density is what makes text mechanical. Formal genre allows far more.
- Watch "olarak" chains: "önemli bir araç olarak öne çıkmaktadır" → "öne çıkıyor".

## English notes

- Em dashes are not slop by themselves. Frequency is the signal.
- Triplets are a natural rhetorical device. Flag only when they appear in nearly every paragraph.
