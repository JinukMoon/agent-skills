# Problems met while formatting decks — cause and fix

Add a dated row every time a new one shows up. Every row was confirmed on a real deck,
not guessed.

| date | symptom | cause | fix |
|---|---|---|---|
| 2026-11-03 | PowerPoint warns on open: "remove restricted fonts" (제한된 글꼴 제거) | An embedded font has the print/preview-only permission (EOT header fsType = 4 at bytes 32-34 of `ppt/fonts/*.fntdata`). Korean NanumSquare files are like this | `ppt_fontfix.py --drop-embedded`. Trade-off: on a PC without that font PowerPoint substitutes another |
| 2026-11-03 | After changing the Korean font, the line count stays the same but the breaks land elsewhere ("…기반 Large ⏎ Scale…") | The new font has different glyph widths (NanumSquare is narrower than Malgun Gothic). A line-count check misses this | Compare line **content** with `ppt_audit.py --before`. Put the old break back with `ppt_break.py` |
| 2026-11-03 | Merging "NanumSquareOTF Bold" into the family "나눔스퀘어" + b=1 made only the Korean bold; the Latin in the same line stayed regular | That face name was not installed, so the original never rendered bold. Adding b=1 made it bold for real | `ppt_fontfix.py` adds b=1 only when the Latin runs of the same paragraph are bold too. Otherwise it keeps regular weight. Compare with the original render |
| 2026-11-03 | Korean word split mid-word ("에\|너지", "대\|비") | The run has **no `lang` attribute**, so PowerPoint breaks Hangul at any character. Changing `eaLnBrk` (0, 1 or removed) had **no effect** (measured) | Add `lang="ko-KR"` to Hangul runs (`ppt_wrap.py … wordwrap`) |
| 2026-11-03 | English word split mid-word ("migratio\|n") | Master default `latinLnBrk="1"` (allow Latin words to break) | Set `latinLnBrk="0"` on the paragraph (`ppt_wrap.py … wordwrap`) |
| 2026-11-03 | After switching to word wrap, a lone word drops to an extra last line | Whole words now wrap and the line is a few points short | Tighten tracking: `spc=-30` to `-50` (-0.3 to -0.5 pt) restores the line count. Otherwise break before a meaning unit with `ppt_break.py` |
| 2026-11-03 | Hyphenated word split across lines ("Dy-\|doped") | A hyphen is a legal break point | Break before the whole word with `ppt_break.py` |
| 2026-11-03 | Shapes look overlapped in the render | Animated shapes that appear or disappear in turn. A static render shows all of them | Do not "fix" it. Compare with the original render: if the original overlaps too, it is the animation. Only confirm with `ppt_diff.py` |
| 2026-11-03 | The audit flagged a manual line break as a mid-word split, and a narrow 2-line label ("Fold ⏎ 1") as an orphan | Wrapping and Shift+Enter looked the same in the dump | The dump marks Shift+Enter line ends `<BR>`. The orphan check skips boxes narrower than 60 pt |
| 2026-11-03 | Every title box reported "overflows by 2.4 pt" | Template trait (text bounds a bit taller than the box), invisible | The overflow threshold is > 3 pt |

## Notes
- lxml re-serialisation of a slide is safe for animations as long as `<p:timing>` is
  c14n-identical, which `ppt_diff.py` checks.
- Theme fonts: `+mn-lt` / `+mj-lt` resolve through `ppt/theme/theme1.xml`. If the theme's Latin font
  is a Korean face, every "inherited" Latin run uses it. Fix the theme, not just the runs.
- The East Asian theme font is often empty (`<a:ea typeface=""/>`). Korean then comes from
  `<a:font script="Hang" …/>`, and `ppt_fontfix.py` sets that one as well.
