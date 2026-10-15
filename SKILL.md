---
name: anti-ai-slop-editor
description: Edits Turkish and English text to remove formulaic, mechanical "AI-sounding" prose (stock openers, filler, hedges, triplet lists, robotic conclusions) while protecting meaning, numbers, names and quotes. Use when the user asks to de-AI, humanize, clean up, tighten, make more natural, or check text for AI clichés / "AI slop" / yapay zekâ kokan ifadeler / basmakalıp anlatım, in Turkish or English.
---

# Anti-AI-Slop Editor

Finds and removes formulaic, mechanical prose in Turkish (TR) and English (EN) text, then shows exactly what changed and why.

**This is not an AI detector.** The score measures density of stock phrasing and mechanical structure. Humans write slop too, and good AI-assisted text can score clean. Never tell the user a text "was written by AI" based on this tool.

## Workflow

1. **Get the text and settings.** Save the user's text to a file. Determine:
   - Language: `tr`, `en`, or `auto` (default).
   - Genre: `blog`, `seo`, `email`, `review`, `formal`, `social` (default `blog`). Read `references/genre-rules.md` if unsure.
   - Mode: `report` (flag only) or `edit` (flag + rewrite, default).
   - Protection: default protects numbers, dates, URLs, quotes, proper names and code. The user may add terms (`--protect "Rank Math,KGYS"`).

2. **Scan.** Run:
   ```bash
   python3 scripts/scan.py input.txt --lang auto --genre blog --out scan.json
   ```
   It returns every hit (pattern, category, severity, position, sentence), structural findings (repeated sentence starts, sentence-length uniformity, triplet lists, mechanical conclusions), protected spans, and a Slop Density Score.

3. **Judge in context.** Open the matching catalog (`references/patterns-tr.json` or `patterns-en.json`) only for patterns you need to understand. For each hit decide: fix, keep, or soften. Discard false positives. A pattern is a signal, not a verdict. Rules:
   - Density matters more than single hits, especially in Turkish (`-mektedir` is normal in formal writing; five in one paragraph is the problem).
   - Respect the genre thresholds in `references/genre-rules.md`.
   - Read `references/structure.md` for structural issues the regexes only approximate.

4. **Edit (edit mode).** Rewrite only what is flagged. Follow `references/preservation.md`:
   - Remove the formula; keep the claim. Never add facts, figures, examples, sources or opinions that are not in the source.
   - Keep every protected span byte-identical.
   - Do not add deliberate typos, slang or fake "human" quirks. Natural is the goal, not imperfect.
   - Keep the author's register (formal stays formal, "siz" stays "siz").

5. **Verify.** Save your edit and run:
   ```bash
   python3 scripts/compare.py input.txt edited.txt --lang tr --out compare.json
   ```
   It fails if a protected span was lost or altered and flags new content words that have no source in the original (meaning-drift risk). Fix every failure before showing the result. Re-run `scan.py` on the edit to report the new score.

6. **Report.** Run:
   ```bash
   python3 scripts/report.py scan.json compare.json --changes changes.json --format md
   ```
   `changes.json` is a list you write: `[{"original": "...", "edited": "...", "severity": "medium", "reason": "...", "category": "stock_opener"}]`. Output: score before → after, a change table (original / edit / severity / reason), meaning-drift warnings, and the clean text.

## Output format for the user

- Score line: `Slop Density: 42 → 9 (lower is better)`.
- Change list: each with original, edit, severity, one-line reason. Write reasons in the text's language.
- Any drift warning with a safer alternative.
- The final text.

For short texts (under ~150 words) you may skip the scripts and apply the catalogs directly, but still list changes with reasons.

## Files

- `references/patterns-tr.json`, `references/patterns-en.json` — phrase catalogs (regex, category, severity, fix hint, example).
- `references/structure.md` — language-independent structural patterns.
- `references/genre-rules.md` — per-genre tolerance and score thresholds.
- `references/preservation.md` — protection and meaning-preservation rules.
- `scripts/scan.py` — detection + scoring. `scripts/compare.py` — protection and drift check. `scripts/report.py` — Markdown/JSON report.
- `tests/` — sample texts and expected results (`python3 tests/run_tests.py`).
