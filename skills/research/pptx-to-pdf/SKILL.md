---
name: pptx-to-pdf
description: >-
  Convert a PowerPoint .pptx into a high-fidelity PDF on this WSL machine that
  looks EXACTLY like PowerPoint on screen — fonts never break, line breaks never
  shift, and the glyphs are not the "fatter" rendering you get from a normal PDF
  export. It works by driving the real Windows PowerPoint (via powershell.exe
  COM) to rasterize every slide, then bundling those slide images into one PDF.
  Use this whenever the user wants a .pptx turned into a PDF, mentions
  "PDF로 변환", "PPT를 PDF로", "발표자료 PDF", "슬라이드 PDF로", "convert this deck/
  presentation/slides to PDF", or hands over a .pptx and asks for a PDF — even
  if they don't specify quality. Default output is 7K-resolution, visually
  lossless, saved as plain <name>.pdf with no quality suffix. Prefer this over
  LibreOffice (which reflows text) and over plain vector PDF export (which
  renders fonts fatter than the PowerPoint screen).
---

# pptx → high-fidelity PDF (Windows PowerPoint COM)

## When to use
A user on a WSL machine wants a `.pptx` turned into a PDF and cares that it
matches what PowerPoint shows. This is the default PDF-conversion path for
PowerPoint files here. If the user only needs rough text extraction or a
searchable/editable PDF, this is the wrong tool (see "Trade-off" below).

## First-run setup
On first use, verify the environment and install dependencies — ask the user if anything
is unclear:
1. **WSL + Windows PowerPoint**: `powershell.exe -NoProfile -Command "$env:TEMP"` must work,
   and Microsoft PowerPoint must be installed on the Windows side. If not, tell the user this
   skill requires WSL with desktop PowerPoint and stop.
2. **Python deps**: `pip install Pillow img2pdf` into whatever Python the user wants to use
   (ask once, remember their choice).

## Why this approach (read once, it explains every step)
Three ways exist to make a PDF from a `.pptx`, and only one matches the screen:

1. **LibreOffice `--convert-to pdf`** — different layout engine, so it measures
   glyph widths slightly differently and **re-flows the text**: lines that fit
   on one line in PowerPoint wrap, shoving everything below them. Rejected.
2. **PowerPoint's own vector PDF export** — layout is perfect, text is
   selectable, but a PDF viewer re-rasterizes the font *outlines* with grayscale
   anti-aliasing at screen DPI, so the text looks **heavier / "fatter"** than
   PowerPoint's ClearType screen rendering. Fine for print, but the user
   noticed and disliked the on-screen difference.
3. **Slide images → PDF (this skill)** — PowerPoint itself rasterizes each
   slide to PNG, and those exact pixels go into the PDF. The viewer just shows
   pixels (no font re-rasterization), so it looks **identical to PowerPoint at
   any zoom**. The only cost: text is not selectable (it's an image).

The fonts come from PowerPoint itself, so nothing can "break" — there is no
font substitution or missing-glyph tofu, regardless of what's installed in WSL.

## How to run
Everything is in one script. Requires `Pillow` and `img2pdf` (`pip install Pillow img2pdf`):

```bash
python ~/.claude/skills/pptx-to-pdf/scripts/pptx_to_pdf.py "<path/to/deck.pptx>"
```

That produces `<path/to/deck>.pdf` — **plain basename, no quality suffix** (do
not append `_7K`, `_q95`, `_고화질`; the user asked for clean names).

Defaults (what you get with no flags):
- Export every slide as PNG at **6827×3840 (7K)** via `Slide.Export(path,"PNG",w,h)`.
  Explicit pixel dimensions mean **no Windows registry tweak is needed**.
- Re-encode as **JPEG quality 95, 4:4:4 (subsampling=0)** — visually identical
  to lossless (measured max per-pixel diff ≤5/255; 0% of pixels differ by >5
  levels) at ~⅓ the file size (e.g. ~127 MB vs ~362 MB for a 39-slide deck).
- Page size follows the slide aspect (16:9 → 13.333in × 7.5in; 4:3 → ×10in).

## Flags (only when the user asks)
- `--lossless` — embed exact PNG pixels (byte-perfect, ~3× larger). Use only if
  the user explicitly wants a true-lossless/archival master.
- `--quality N` — JPEG quality (default 95). Lower (e.g. 92) for a smaller file.
- `--width W --height H` — export resolution. Drop to `--width 3840 --height 2160`
  (4K) for a much smaller file that still prints at ~288 DPI.
- `-o OUT.pdf` — explicit output path.

Don't ask the user which quality each time — just run the default (7K q95).
Only reach for flags when they request lossless, smaller, or a specific size.

## Requirements / gotchas
- **Windows PowerPoint must be installed and reachable** via `powershell.exe`
  (checked during first-run setup). The script verifies the COM export succeeded and
  aborts loudly otherwise.
- The script stages the file under the Windows `%TEMP%` dir as ASCII
  `input.pptx`, because **Korean filenames get mangled crossing the WSL↔Windows
  boundary** (the original name is preserved for the *output*, only the staged
  copy is renamed). It auto-detects `%TEMP%` and cleans up after itself.
- A 39-slide deck takes ~1–3 min (PowerPoint renders each slide at 7K).
- Large input decks (200 MB+) and ~360 MB lossless outputs are normal; check
  free disk if doing many.

## Trade-off to surface to the user
The output text is **not selectable/searchable** (it's slide images). If they
need search or copy-paste, mention the options: use PowerPoint's vector PDF
export instead (accepting the slightly heavier on-screen font), or add an
invisible OCR text layer afterward with `ocrmypdf` (Korean OCR is imperfect).

## Verify
After conversion, sanity-check by rendering a text-heavy slide and looking at
it:
```bash
pdftoppm -f 2 -l 2 -r 110 -png "<out>.pdf" /tmp/_chk && # then view /tmp/_chk-02.png
pdfinfo "<out>.pdf" | grep -iE 'pages|page size'
```
Confirm page count matches the deck and a long title sits on the same line as
in PowerPoint (proof that nothing re-flowed).
