---
name: pre-proof
description: >
  Pre-proof (final proofreading / anomaly hunt) a manuscript PDF or Word file before
  submission or publication. This is a 100%-thoroughness, anomaly-detection pass — NOT a
  scientific-content review. It hunts typos, LLM-pasted unicode subscripts/superscripts and
  hidden characters, caption errors, broken citations and references, figure/table/equation
  cross-reference gaps, and consistency problems, then verifies the author block and
  affiliation against the canonical strings. Runs 10 fixed passes and writes a single markdown
  report into a dedicated folder next to the file. Use this whenever the user mentions
  pre-proof, preproof, "pre proof", proofread/proofreading a paper, final check before
  submission, galley/proof check, "오타 찾아줘" on a manuscript, "교정 봐줘", anomaly check on a
  PDF/Word manuscript, or hands over a PDF/docx and asks for a careful error sweep — even if
  they don't say the word "pre-proof".
---

# Pre-proof

You are doing a **pre-proof**: the last-line defense before a manuscript is submitted or goes
to press. The mindset is adversarial and obsessive — assume errors are hiding and it is your
job to find every one. This pass is about **mechanical correctness and anomalies**, not about
whether the science is good. When unsure whether something is an error, **flag it** and let the
author decide; a false positive costs a glance, a missed error reaches print.

## Canonical author / affiliation (verify against these EXACTLY)

The skill verifies the manuscript's author block against `authors.json` (next to this SKILL.md)
character-for-character.

**First-run setup:** if `authors.json` does not exist yet, ASK the user before doing anything
else: "처음 사용하시네요. 논문에 항상 들어가는 본인(및 고정 공저자)의 영문 이름, ORCID,
소속(affiliation) 문자열을 알려주세요 — 이후 모든 pre-proof에서 이 값과 글자 단위로
대조합니다." Then save their answer as `authors.json` and confirm it's stored locally only.

```json
{
  "authors": [
    {"name": "Your Name", "orcid": "0000-0000-0000-0000"},
    {"name": "Co-Author Name", "orcid": "0000-0000-0000-0000"}
  ],
  "affiliation": "Your Department, Your University, City, Country"
}
```

Compare character-for-character and flag *any* deviation (spelling, word order, missing comma,
postal code, etc.).

When the proof lists an ORCID for any of the canonical authors, verify it digit-for-digit against
the value in `authors.json` and flag any mismatch (a wrong ORCID delays publication). If no ORCID
is shown for them, note it so the author can add it.

If the manuscript has *other* co-authors or affiliations, that is fine — do not flag them as
wrong, but do report the author/affiliation block verbatim so the user can eyeball it. Your job
is to guarantee the canonical names and affiliation are present and perfect.

## Workflow

### 1. Locate the file and build the workspace

The user supplies a PDF or `.docx` path (ask for it if missing).

**Name the folder so a human can recognize it later — never leave it as the raw filename.**
Manuscript files often arrive with opaque names (`ViewPageProof_EE_d6ee01604a.pdf`,
`manuscript_R2_final.docx`), and a folder called `ViewPageProof..._preproof` tells the user
nothing. So first peek at page 1–2 (or the extracted text) to grab the **journal abbreviation +
a short title slug + the year**, then name the folder `<Journal>_<short-title>_<year>_preproof`.
Keep it short — no DOI/ID. Examples:

- `Energy & Environmental Science`, Ru-cluster alkaline HER paper, 2026
  → `EES_Ru-cluster-alkaline-HER_2026_preproof`
- `JACS`, MOF CO2 capture, 2025 → `JACS_MOF-CO2-capture_2025_preproof`

If you genuinely cannot determine title/journal yet (e.g. before extraction), it's fine to do a
quick extract first, read the title, then create the folder. Use a `FOLDER` variable for it:

```bash
cd "<directory of the file>"
FOLDER="<Journal>_<short-title>_<year>_preproof"   # human-recognizable, no DOI
mkdir -p "$FOLDER"
mv "<the file>" "$FOLDER/"
```

Everything below happens inside `$FOLDER/`. The original file now lives there, the extracted
text and the final report go there too. This keeps each pre-proof self-contained and findable.

> Legacy `.doc`: convert first — `libreoffice --headless --convert-to docx <file>.doc`.

### 2. Extract text faithfully

Use the bundled extractor (it preserves every unicode character as-is — do not let any tool
"clean" the text, because the dirt is what we're hunting):

```bash
python ~/.claude/skills/pre-proof/scripts/extract_text.py \
  "<file inside the folder>" \
  "${STEM}_preproof/${STEM}_extracted.txt"
```

> Requires `PyMuPDF` and `python-docx`: `pip install PyMuPDF python-docx`

PDF pages are tagged `===== PAGE n =====`; Word output tags paragraphs `[P0001]` and table
cells `[T<t>.<r>.<c>]`. Use these tags as the **location** in every finding.

**Know what the text layer can and cannot tell you (this decides whether you need OCR):**

- **Digital (born-PDF) vs scanned.** Check extracted length: thousands of characters → digital;
  near-zero → scanned image. For a *digital* PDF the text layer is **character-exact for
  spelling** — a typo in the PDF is a typo in the text, so you do NOT need OCR to find spelling
  errors, and running OCR on a digital PDF only *adds* noise (mis-reads `a`→`&`, scrambles
  2-column reading order). For a *scanned* PDF the text layer is empty/garbage and **OCR is
  required** — render each page and OCR it (e.g. with `easyocr`;
  use `gpu=False` if cuDNN errors).
- **The text layer is glyph-lossy, NOT spelling-lossy.** Digital PDFs routinely carry broken
  font→Unicode mappings: superscripts/subscripts get dropped, and symbols get mis-mapped to
  letters. Watch for these systematic artifacts and do **not** report them as errors — verify
  against the rendered image instead:
  - `cm2` / `dec1` / `Å1` / `mg​NM 1` ← dropped superscript minus (`cm⁻²`, `dec⁻¹`, `Å⁻¹`)
  - `50 1C`, `200 1C` ← `°` mis-mapped to `1` (`50 °C`)
  - `B1 nm`, `B2.4 Å` ← `~` mis-mapped to `B` (`~1 nm`)
  - `DGH*`, `DGOH*` ← `Δ` mis-mapped to `D` (`ΔG_H*`)
  - `oﬀering`, `staﬀwill`, `Chorkendorﬀand` ← ligature glyphs that swallow the following space
  - `Tru¨by`, `Schu¨ler`, `Ayme´` ← accented letters split (`Trüby`, `Schüler`, `Aymé`)
- **Figure-internal text is usually absent from the text layer.** Axis labels, legends, and
  in-figure annotations (e.g. "2.98 A cm⁻²", "×4.5", Tafel slopes, cluster sizes) live inside
  the figure graphics and **can only be checked by looking at the rendered page**. This is where
  many real proof errors and text↔figure number mismatches hide.

### 2b. Visual review of the rendered pages (mandatory for PDFs)

Because of the two points above, a text-only pass is not a real pre-proof. For a PDF you MUST
also *look* at the pages. Read every content page as an image (the Read tool renders PDF pages),
and for any small annotation you can't read confidently, crop-and-zoom with PyMuPDF:

```python
import fitz
doc = fitz.open(PDF); page = doc[N-1]; W,H = page.rect.width, page.rect.height
r = fitz.Rect(x0*W, y0*H, x1*W, y1*H)            # fractional box around the region
page.get_pixmap(clip=r, matrix=fitz.Matrix(6,6)).save("_crop.png")   # 6× zoom
```

You are a far more accurate "OCR" than easyocr for this content, so trust your visual read of
the rendered glyphs over the lossy text layer. Delete any `_crop.png` scratch files when done.

### 3. Run the deterministic scanner

This is the mechanical net that catches what eyes miss — invisible characters, smart quotes,
unicode subscripts, doubled words. Run it before the judgment passes and use its output as the
backbone for passes 3, 4, and 9:

```bash
python ~/.claude/skills/pre-proof/scripts/scan_anomalies.py \
  "${STEM}_preproof/${STEM}_extracted.txt" \
  "${STEM}_preproof/${STEM}_scan.md"
```

Read `${STEM}_scan.md`. Treat every flag as a candidate, then judge: a `NONASCII` Greek μ in
"μmol" is intentional; a `SUBSUP` ₂ in "CO₂" is an LLM artifact that should be a real subscript;
an `INVIS` zero-width space is almost always wrong. The scanner flags, **you** decide.

### 4. The 10 passes

Read the **full extracted text every pass** — do not skim. Each pass wears a different lens, so
re-reading is not wasted: a typo invisible while you hunt citations jumps out while you hunt
spelling. Accumulate findings in a running list; de-duplicate as you go (same line + same issue
= one finding). Run all **10 passes, always** — even if a pass finds nothing, record "Pass N:
no new findings" so the user knows it was done.

1. **Author & affiliation block** — verify canonical author names and affiliation from
   `authors.json` character-for-character. Check superscript affiliation markers and
   corresponding-author symbols/emails resolve correctly.
2. **Spelling / typos** — every word. Misspellings, transposed letters, wrong-word errors
   (its/it's, affect/effect, "an" vs "a"), chemical-formula typos, element symbol case (Co vs
   CO vs cobalt). Read slowly.
3. **Unicode sub/superscript artifacts** — from the scanner's `SUBSUP` list: CO₂→CO2, m³, H₂O,
   exponents typed as ², charge states. These are LLM/copy-paste tells that should be proper
   formatting; flag each with its location and the intended form.
4. **Hidden characters & punctuation** — from `INVIS`/`SPACE`/`QUOTE`/`DASH`/`LIGAT`/`HYPHEN`:
   zero-width chars, non-breaking spaces, smart quotes mixed with straight, en/em dash misuse,
   ligature corruption (ﬁ), and line-break hyphenation joins ("cata- lysis").
5. **Figure / Table / Equation captions AND figure-internal text** — typos in captions; caption
   numbering sequential and unique (no two "Figure 2", no skipped number); panel labels (a), (b)
   referenced exist; units and symbols in captions match the body; legend color/symbol keys
   match what the figure shows. **Then look inside each figure** (rendered image) for typos in
   axis labels, legends, and annotations — these are not in the text layer and must be read
   visually. Cross-check every in-figure number against the body (see pass 8).
6. **Citation ↔ reference cross-check** — every in-text citation has an entry in the reference
   list; every reference is cited at least once (flag orphans and uncited entries); citation
   numbers run in order of appearance; no duplicate or missing reference numbers; "Ref. X" /
   "Eq. X" / "Fig. X" targets all exist.
7. **Consistency** — abbreviations defined at first use then used consistently (DFT, MLIP, OER);
   US vs UK spelling not mixed; unit formatting and spacing uniform (5 nm vs 5nm; °C); hyphen
   and terminology consistency (pre-proof vs preproof; "first-principles").
8. **Numbers & data sanity — cross-section consistency** — the same result is often stated in
   several places (title, graphical abstract, abstract, broader context, introduction, results,
   conclusion, tables, and *inside figures*). Build a small table of each headline quantity and
   confirm it is identical everywhere it appears. This is one of the highest-value pre-proof
   checks because authors update a number in one place and forget another. Concretely:
   - Pick each headline metric (e.g. peak current density, overpotential, Tafel slope, mass/price
     activity, ΔG values, durability hours, temperature, loading, "N-fold" ratios, DOE target).
   - List every location it appears (abstract vs results vs conclusion vs figure annotation vs
     table) and verify they match — including rounding (e.g. text "−0.5 eV" vs figure "−0.51 eV",
     or "2.97" vs "2.98" between body and a figure label are real findings).
   - Re-derive stated ratios/percentages from the underlying numbers ("~10-fold", "5 times
     higher", "increased by 30%") and flag if the arithmetic or the rounding word is off.
   - Also check: totals/percentages add up; significant figures and decimal places consistent;
     ranges ordered (lower–higher); axis/column units present and sensible.
9. **Grammar & mechanics** — subject-verb agreement, articles, doubled words ("the the" from
   the scanner's `REPEAT`), double spaces, space-before-punctuation, stray spacing, bracket and
   parenthesis balance.
10. **Holistic final sweep** — read once more cold for anything the lenses missed (section
    numbering, header/footer leftovers, page-number gaps, mojibake, truncated sentences,
    placeholder text like "TODO"/"XXX"/"[ref]"), and re-confirm earlier findings are real (kill
    false positives). This pass guarantees nothing slips through.

### 5. Write the report (English + Korean)

Always write **two** reports in the workspace folder — same content, two languages:

- `preproof_report.md` — English
- `preproof_report_ko.md` — Korean

Write the Korean version as a genuine translation of the findings, not a separate analysis: keep
the same finding IDs (M1, m3, …), the same tables, and **keep code/quoted strings, file paths,
author names, the affiliation string, journal/DOI, and the Current→Suggested-fix values in their
original form** (do not translate or alter quoted text — the author needs the exact strings to
edit). Translate only the prose, headers, and explanations. Both files use the structure below.

Write `preproof_report.md` using this structure:

```markdown
# Pre-proof report — <filename>

- File: `<path inside folder>`
- Type / length: <PDF, N pages | Word, N paragraphs>
- Date: <today>
- Passes completed: 10/10

## Verdict
<one line: e.g. "12 findings — 2 Critical, 5 Major, 5 Minor. Not ready: fix Critical before submission.">

## Author & affiliation check
- <Author 1>: ✅ / ⚠ <detail>
- <Author 2>: ✅ / ⚠ <detail>
- Affiliation: ✅ exact match / ❌ <show the diff>

## Findings (by severity)

### 🔴 Critical  (wrong info / breaks meaning — must fix)
| # | Location | Issue | Current | Suggested fix |
|---|---|---|---|---|

### 🟠 Major  (clear error, should fix)
| # | Location | Issue | Current | Suggested fix |
|---|---|---|---|---|

### 🟡 Minor  (style / consistency / cosmetic)
| # | Location | Issue | Current | Suggested fix |
|---|---|---|---|---|

## Cross-reference audit
- Citations without references: <list or none>
- References never cited: <list or none>
- Figures/Tables/Eqs not referenced in text: <list or none>
- Numbering gaps/duplicates: <list or none>

## Pass log
Pass 1 … Pass 10 — one line each (count of new findings or "no new findings").
```

**Severity guide:** Critical = wrong data, wrong author/affiliation, broken citation that
misattributes, a missing/duplicated figure number. Major = a real typo, a unicode subscript, an
orphan citation. Minor = double space, inconsistent hyphenation, smart-quote style.

Give every finding an exact **location** (page/paragraph tag + short quoted context) so the
author can jump straight to it. Show **Current → Suggested fix** so each is one action.

### 6. Report back

Tell the user where the folder and both reports (English + Korean) are, the verdict line, and the headline counts
(Critical/Major/Minor). Mention the original file was moved into the folder.

## Notes

- This skill never edits the manuscript; it only reports. The author applies fixes.
- Thoroughness over speed. If the document is long, work through it section by section but still
  complete all 10 passes over the whole thing.
- If text extraction looks garbled (heavy math, scanned PDF), say so — a scanned/image PDF may
  need OCR before a meaningful pre-proof is possible.

## Setup

1. Install dependencies: `pip install PyMuPDF python-docx`
2. On first use, the skill asks for your canonical author/affiliation info and saves it to
   `authors.json` next to this SKILL.md (see the "Canonical author / affiliation" section above).
   It stays on your machine; never commit it.
