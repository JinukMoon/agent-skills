---
name: paper-reading
description: >-
  Deeply read a scientific paper (PDF) and produce two Korean markdown deliverables — a full
  line-by-line English↔Korean translation, and a critical review (claimed strengths, core logic,
  limitations, self-review). Use this whenever the user hands over a paper PDF and wants it
  translated, summarized, deeply read, reviewed, critiqued, or "정독"; whenever they say things
  like "이 논문 정리해줘", "논문 번역해줘", "논문 리뷰", "논문 읽고 분석", "비판적으로 봐줘",
  "강점/한계 정리", "paper reading", "translate this paper", or drop a .pdf into the
  paper-reading workspace. Trigger even if the user only says "이 논문 봐줘" with a PDF attached.
---

# Paper Reading — Translation + Critical Review

This skill turns a scientific paper PDF into two Korean markdown files following a fixed, repeatable
workflow. The goal is a faithful full translation plus a genuinely critical review — not a shallow
summary. LLMs reliably capture contributions and methods but tend to *under-produce* substantive
criticism, so the review steps below are scaffolded deliberately to force real weakness-finding.

## Output: two files in a dedicated folder

For every paper, create one folder and two markdown files. Never leave the source PDF loose in the
parent directory.

**Naming**
- ID: `{firstAuthorLastname}{year}{keyword}` (lowercase), e.g. `yang2024boron`
- Folder: `{ID}_{journalAbbrev}`, journal abbreviation in CamelCase, hyphens allowed, no spaces,
  e.g. `yang2024boron_ACSAppliedMat-Inter`

```
17_paper_reading/
└── yang2024boron_ACSAppliedMat-Inter/
    ├── yang2024boron.pdf              # source PDF, moved + renamed here (mv, not cp)
    ├── yang2024boron_translation.md   # Step 1
    └── yang2024boron_review.md        # Steps 2–5
```

Move and rename the PDF into the folder so no original copy remains in the parent.

**First-run setup:** the default working root is stored in `config.local.json` next to this
SKILL.md (`{"workspace": "/path/to/paper_reading_root"}`). If that file does not exist yet, ask
the user once: "논문 정독 폴더들을 모아둘 기본 경로를 알려주세요 (예: ~/papers). 앞으로 PDF를
주시면 그 아래에 폴더를 만들어 정리합니다." Save the answer and don't ask again. If the user is
clearly working in a specific directory for this paper, that takes precedence.

## Before you start: read the PDF properly

Use the `pdf` skill (or the user's available PDF tooling) to extract text — do not guess at content.
Read the **entire** paper including Methods/SI prose, not just the abstract and figure captions.

PDF text extraction routinely mangles equations and multi-column layouts. When you hit a broken
equation or garbled table, flag it rather than inventing content, and note it in the Step-5
self-review. Figure/Table **captions** must still be translated in full; the figures themselves are
images you cannot read from extracted text, so reason from the caption + surrounding prose.

## Step 1 — Full line-by-line translation (`*_translation.md`)

Translate **every sentence** of the paper, English original and Korean rendering in parallel.
Preserve the paper's exact section/subsection structure. Include every figure and table caption.

Open the file with a short metadata block and a **key-term glossary**, then proceed section by
section. The glossary locks one Korean rendering per recurring technical term so terminology stays
consistent across a long paper (and doubles as a study aid). Build it as you translate; keep
established acronyms in English (MLIP, DFT, NEB, …).

```markdown
# {Paper title}

**Authors**: ...
**Journal**: {name} {vol}, {pages} ({year})
**DOI**: https://doi.org/...

---

## 용어집 (Key Terms)

| English | 한국어 | 비고 |
|---------|--------|------|
| adsorption energy | 흡착 에너지 | |
| selective task regularization | 선택적 태스크 정규화 | 본 논문 핵심 개념 |

---

## {Section Title} / {섹션 제목}

> Original English sentence.

한국어 번역 문장.

> Next English sentence.

다음 한국어 번역 문장.
```

Translation quality matters more than speed:
- Keep technical terms accurate and **consistent** across the whole paper (pick one Korean rendering
  per term and stick to it; keep established English acronyms as-is, e.g. MLIP, DFT, NEB).
- Translate faithfully, not loosely — this is a study aid, the user will compare against the original.
- For a very long paper (30+ pages), translating dense Methods detail (full loss-function
  derivations, exhaustive DFT settings) can be compressed to its core, but say so explicitly in the
  self-review. Main-text prose is always translated in full.

## Step 2 — TL;DR + claimed strengths (`*_review.md`)

Open `*_review.md` with a **TL;DR** — a 3–5 line Korean digest a reader can skim instead of the whole
review. Answer: what problem, what method, the headline result (with the single most important
number), and the one caveat worth knowing.

```markdown
## TL;DR

- **문제**: ...
- **방법**: ...
- **핵심 결과**: ... (가장 중요한 수치 1개)
- **주의할 점**: ...
```

### Section 1 — Claimed strengths

List the contributions and strengths **the authors themselves claim**. For each item, cite the
backing experiment / number / figure or table. This is the part LLMs do easily — keep it tight and
evidence-anchored, no padding. Bullet list.

## Step 3 — Core logic / key arguments (`*_review.md`, section 2)

Reconstruct the paper's reasoning chain: hypothesis → method → experimental design → conclusion.
Write it as "why this method → what it showed → what they concluded." Anchor each logical step to its
Figure/Table number and key numbers. A short text-based flow diagram is encouraged when the argument
has a clear pipeline.

## Step 4 — Limitations & critical notes (`*_review.md`, section 3)

This is the highest-value section and the one models tend to shortchange. Push hard here. Separate
into two categories:

- **저자 인정 한계 (author-acknowledged)**: limitations explicitly stated in the paper, quoted or
  paraphrased with location.
- **추가 비판 (additional critique)**: weaknesses *you* find by reading critically. Probe each of:
  experimental design and fair-comparison concerns; missing baselines or ablations; hyperparameter
  arbitrariness and reproducibility; generalization beyond the tested architecture/dataset;
  unreported training/compute cost; data-quality issues; scope gaps (what the stated motivation
  promised vs. what was actually delivered); over-claims where reported gains ≠ physical/real-world
  significance.

Be specific and grounded — "no compute cost reported despite a 250M-structure model" beats "could be
more efficient." Aim for a substantial list; a paper with only one or two critiques usually means you
did not look hard enough.

A short overall assessment (contribution, predicted impact, one-line verdict) is a good closer but
optional.

## Step 5 — Self-review (`*_review.md`, final section)

After Steps 1–4, re-read the paper from start to finish against what you wrote and verify:
- No missing or mistranslated passages.
- No claims in the strengths/logic/limitations that contradict the source.
- Every Figure/Table number cited is correct.
- Every performance number (accuracy, error, dataset size, hyperparameter value) matches the original.

Fix errors immediately, then record what you checked, any potential errors found, and what was
intentionally compressed. Save both files as final.

## Worked examples

If the user's workspace already contains finished paper-reading folders from previous runs, read
one before starting when you need a concrete target for depth and format.

## Optional enhancements

TL;DR and the key-term glossary are now part of the default workflow (Steps 1–2). The following
remain off by default to keep output focused; offer or apply them when the user wants more. See
`references/enhancements.md` for details on each:
- Prior-work comparison table
- Reproducibility checklist
- Extracting figures as image files for visual reference
