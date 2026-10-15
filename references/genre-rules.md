# Genre rules

Genre changes tolerance, not the goal. `scan.py --genre` applies the multipliers below.

| Genre | Formal suffix (TR) | Intensifiers | Closings | Hedges | Score thresholds (clean / moderate / heavy) |
|---|---|---|---|---|---|
| `blog` | ≤ 20% of sentence endings | low tolerance | cut summary paragraphs | low | < 15 / 15–35 / > 35 |
| `seo` | ≤ 20% | low | allow one short recap if it carries the keyword naturally | low | < 18 / 18–40 / > 40 |
| `email` | ≤ 10% | very low | one-line sign-off only | very low | < 10 / 10–25 / > 25 |
| `review` | ≤ 15% | low; claims need specifics | verdict paragraph is allowed | medium (honest caveats are good) | < 15 / 15–35 / > 35 |
| `formal` | no limit (official TR uses `-mektedir`) | very low | formal closing allowed | medium | < 25 / 25–50 / > 50 |
| `social` | ≤ 10% | medium (voice matters) | cut | low | < 12 / 12–30 / > 30 |

## Genre-specific guidance

**blog / seo** — Openers and meta commentary are the biggest offenders. Keep keywords; never remove the focus keyword while editing. Headings may stay as questions only in FAQ sections.

**email** — Cut chatbot residue first ("I hope this email finds you well", "Umarım iyisinizdir" in excess). Keep greetings and requests.

**review** — Every positive adjective needs a concrete reason (measurement, comparison, use case). If the source has none, soften the adjective; don't invent the reason.

**formal (resmi yazı)** — Turkish official correspondence has fixed formulas ("Bilgilerinize arz ederim", "gereğinin yapılmasını"). These are not slop. Only flag inflated significance, vague benefits and repetition.

**social** — Voice and rhythm matter more than grammar. Remove buzzwords and fake enthusiasm; keep personality.
