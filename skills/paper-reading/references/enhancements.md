# Optional Enhancements

These extend the base translation + review workflow. Apply when the user asks for "더 자세히",
"그림도 보여줘", or explicitly requests one of these. Keep them optional — the core value is the
faithful translation plus the critical review, and bolting on every extra makes the output bloated.

> Note: TL;DR (review 맨 위 3–5줄 요약) and the key-term glossary (translation 맨 위 용어집) are
> **part of the default workflow** — see SKILL.md Steps 1–2. They are not optional.

## 1. Prior-work comparison table

When the paper positions itself against named prior methods, a compact table (method · what it does ·
its limitation · how this paper differs) makes the contribution legible at a glance. Put it in the
core-logic section of the review.

## 2. Reproducibility checklist

A quick yes/no/partial scan, useful for methods-heavy or ML papers:
- Code released? (link)
- Trained weights / model released?
- Dataset public?
- Hyperparameters fully specified?
- Hardware + training cost reported?
- Random seeds / variance reported?

Feeds directly into the 추가 비판 section — gaps here are legitimate criticisms.

## 3. Figure extraction (시각 자료)

The translation only renders captions, because extracted PDF text cannot convey the figures
themselves. When the user wants to actually see the figures alongside the translation, extract them
as images (the `pdf` skill can render pages or extract embedded images) into a `figures/` subfolder
and reference them inline in the translation:

```markdown
![Figure 1](figures/fig1.png)

> Figure 1. ...caption original...

그림 1. ...캡션 번역...
```

This helps when a figure is central to the argument and the caption alone is not enough to critique
it fairly.
