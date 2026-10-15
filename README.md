# anti-ai-slop-editor

A Claude skill that removes formulaic, "AI-sounding" prose from Turkish and English text, shows every change with a reason, and refuses to touch your numbers, names or quotes.

```
Slop Density: 10 → 0 (lower is better)

| Original                                                  | Edit                                   | Severity | Reason                                   |
|-----------------------------------------------------------|----------------------------------------|----------|------------------------------------------|
| Günümüzün hızla değişen dijital dünyasında yapay zekâ     | Yapay zekâ dijital dünyada önemli bir  | Medium   | Stock opener removed, -maktadır → -yor.  |
| önemli bir rol oynamaktadır.                              | rol oynuyor.                           |          | No new information added.                |
```

**This is not an AI detector.** The score measures how much stock phrasing and mechanical structure a text contains. People write like this too.

## What it does

- **Phrase catalog** — 100 Turkish and 86 English patterns: stock openers, inflated significance, buzzwords, filler, stacked hedges, chatbot residue, robotic closings.
- **Structure analysis** — repeated sentence starts, uniform sentence length, triplet lists, "not X but Y" frames, connector stacking, mechanical conclusions, and `-mektedir/-maktadır` density for Turkish.
- **Genre-aware** — `blog`, `seo`, `email`, `review`, `formal`, `social`. Official Turkish correspondence keeps its formulas; a blog post doesn't.
- **Change table** — original, edit, severity and a one-line reason for every change.
- **Protection mode** — numbers, dates, URLs, quotes, code and proper names must survive the edit byte-identical. `compare.py` fails the edit if they don't. Add your own terms with `--protect`.
- **Meaning-drift check** — words in the edit with no source in the original are flagged, so the editor can't quietly add claims.

It will never add typos or fake "human" quirks to fool detectors.

## Install

**Claude apps (claude.ai / desktop):** download the latest release zip and upload it in the Skills section of your settings.

**Claude Code:**
```bash
git clone https://github.com/yavyzc78/anti-ai-slop-editor ~/.claude/skills/anti-ai-slop-editor
```

**Claude API:** upload the folder as a custom skill (see Anthropic's Agent Skills docs).

Then ask Claude: *"Clean up the AI slop in this text"* or *"Bu metindeki yapay zekâ kokan ifadeleri temizle"*.

## Use the scripts directly

Python 3.9+, no dependencies.

```bash
python3 scripts/scan.py post.txt --genre blog --out scan.json
python3 scripts/compare.py post.txt post-edited.txt --out compare.json   # exits 1 if protection fails
python3 scripts/report.py scan.json compare.json --changes changes.json --edited post-edited.txt
python3 tests/run_tests.py
```

## Score bands

| Genre | Clean | Moderate | Heavy |
|---|---|---|---|
| blog | < 15 | 15–35 | > 35 |
| seo | < 18 | 18–40 | > 40 |
| email | < 10 | 10–25 | > 25 |
| review | < 15 | 15–35 | > 35 |
| formal | < 25 | 25–50 | > 50 |
| social | < 12 | 12–30 | > 30 |

## Limitations

- Regex finds candidates; Claude decides in context. Expect some false positives on single hits.
- Turkish drift detection uses crude stemming, not full morphological analysis.
- Proper-name protection is a capitalization heuristic. Use `--protect` for lowercase brand names.

## Roadmap

- 100+ patterns per language, validated on 100 real texts
- More languages: German, French, Spanish, Italian, Portuguese, Arabic, Russian, Ukrainian (native-speaker contributions welcome)

## Contributing

Found a pattern we miss, or a false positive? Open an issue with the sentence, the language and the genre. New patterns go in `references/patterns-{lang}.json` with a test sample in `tests/`.

## License

MIT. Built by [Yavuz Çetinkaya](https://aiflowmatrix.com).
