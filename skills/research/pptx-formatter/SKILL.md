---
name: pptx-formatter
description: >-
  PPT formatter + pre-proof for an existing PowerPoint deck. It fixes ONLY what
  the user points out and leaves animations, transitions and content untouched,
  proving it with a byte-level animation diff. It also writes a pre-proof style
  audit of the whole deck: mixed fonts, same-level text with different sizes,
  1-3 pt misalignment, bad line breaks (word split mid-word, a lone word on the
  last line, breaks that moved after a font change) and text overflowing its
  box. It reads the EFFECTIVE formatting from real Windows PowerPoint (COM)
  instead of guessing from XML. Use it whenever the user hands over a .pptx
  (local path or a cloud-drive path) and wants it cleaned up, checked or fixed
  in any phrasing: "PPT 다듬어줘", "PPT 서식 고쳐줘", "폰트 통일해줘", "글씨체 통일",
  "페이지 번호 고쳐줘", "줄바꿈 이상한 거 봐줘", "정렬 맞춰줘", "PPT 검수해줘",
  "PPT pre-proof", "제한된 글꼴 경고 떠", "이 슬라이드 3번 제목 크기 맞춰줘",
  "format this deck", "fix the fonts in my slides", "proofread my presentation",
  "check this PPT for layout issues". Do NOT use it to build a new deck from
  scratch, for paper figures (paper-figure-pptx) or to convert PPT to PDF
  (pptx-to-pdf). Requires WSL with desktop PowerPoint on the Windows side.
---

# pptx-formatter — fix only what was pointed out, proof the rest

## First-run setup (once)
1. **WSL + PowerPoint**: `powershell.exe -NoProfile -Command '$env:TEMP'` must print a
   path, and desktop PowerPoint must be installed on Windows. Otherwise stop and say so.
2. **Python**: needs `lxml` and `Pillow` (`pip install lxml Pillow`). Ask which Python
   to use and remember it.
3. **Author name**: ask the user for the name to put in the file's "creator /
   last modified by", then write `config.local.json` next to this SKILL.md:
   `{"author": "Their Name"}`. It is git-ignored and stays on this machine.
4. **House font rule**: ask once. The default this skill was built with is
   "Latin letters and digits = Arial, always. Korean = one font per deck, chosen with
   the user for each deck". Remember the answer.

## Ground rules
- **Fix only what the user points out** (slide number + what to change). Report every other
  problem and fix it only when the user says to ("고칠만한 건 고쳐", "fix what's worth fixing").
- **Never touch animations.** Run `ppt_diff.py` after every change. It must print `OK`.
- Keep the original and save `<name>_fmt.pptx` (a later round on the same original becomes
  `_fmt2`). If the deck came from a cloud drive, put the result back in the same folder.
- **One folder per requested deck**: `<YYMMDD>_<name>/` with `orig/` (as received), `work/`
  (dumps, renders, the job's own step scripts), `out/` (deliverable) and `preproof.md` (report).
- Judge layout **only** from PowerPoint-rendered PNGs (`ppt_render.sh`), never LibreOffice.
- Edit the zip's XML directly (scripts below). Do not open the deck in PowerPoint and re-save
  it: that rewrites every part.

## Workflow
```bash
S=~/.claude/skills/pptx-formatter/scripts; PY=python   # the Python chosen at setup
# 0. fetch: copy the deck into <job>/orig/ (cloud drive: use the user's sync/pull tool)
$S/ppt_dump.sh orig/x.pptx work/orig.json                       # effective formatting, read-only
$PY $S/ppt_audit.py work/orig.json --ea "<Korean font>" -o work/audit_orig.md
$S/ppt_render.sh orig/x.pptx work/render_orig                    # look before touching anything
# 1. fix what was pointed out (tools below, or a small step script in work/ for deck-specific edits)
$PY $S/ppt_meta.py work/fmt.pptx                                 # creator = configured author
# 2. verify — all three, every time
$PY $S/ppt_diff.py orig/x.pptx work/fmt.pptx --allow <slides you meant to change>
$S/ppt_dump.sh work/fmt.pptx work/fmt.json && $PY $S/ppt_audit.py work/fmt.json --before work/orig.json --ea "<font>" -o work/audit.md
$S/ppt_render.sh work/fmt.pptx work/render_fmt                   # compare changed slides side by side
# 3. deliver out/<name>_fmt.pptx + preproof.md: what was fixed, what is reported only, evidence
```
Slide numbers in every tool are the 1-based order in the file (cover included), not the
printed page number.

## Scripts
| script | does |
|---|---|
| `ppt_dump.sh` (+ `ppt_dump.ps1`) | PowerPoint COM, read-only. Per shape: position and size. Per paragraph: level, alignment, bullet, **lines as PowerPoint wrapped them** (`<BR>` = Shift+Enter). Per run: effective Latin and East Asian font, size, bold, color. Also the text bounds. Never quits a PowerPoint the user already has open |
| `ppt_audit.py` | Pre-proof report from a dump. A fonts · B same-level sizes · C alignment (1-3 pt) · D line breaks · E overflow. `--before` also lists every paragraph whose break positions changed |
| `ppt_fontfix.py` | Latin=Arial (or `--latin`) and Korean=`--ea` across slides, layouts, masters, themes and charts. Leaves symbol fonts alone. Merges weight-suffixed names into the family name. `--drop-embedded` removes embedded fonts |
| `ppt_wrap.py` | Per shape: `wordwrap` (no mid-word breaks), `spc=-30` (tracking, in 1/100 pt), `sz=12` |
| `ppt_break.py` | Insert a Shift+Enter line break before a given text inside a shape |
| `ppt_meta.py` | Set creator and lastModifiedBy from `config.local.json` or `--name` |
| `ppt_diff.py` | Changed zip parts, and per slide whether `<p:timing>` (animations) is identical and every animated shape id still exists. Exit 1 on failure |
| `ppt_render.sh` | PowerPoint PNG per slide + `sheet.png` contact sheet |

Common requests:
- Page numbers counted from the cover → add `firstSlideNum="0"` on `<p:presentation>`.
- The page-number box usually lives in a slide **layout**, not on the slides.
- A hard-coded total ("‹#›/30") is a plain run next to the field.

## Problems already solved — read before fixing
`references/troubleshooting.md` holds every problem met so far, with its cause and fix.
Highlights: the "restricted font" warning, Korean words broken mid-word because a run has no
`lang`, line breaks that move after a font change, bold leaking across a run, and shapes that
look overlapped only because of animations. **Whenever a new problem appears while fixing a
deck, add a dated row there** (and in the user's own notes if they keep any).
