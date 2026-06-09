#!/usr/bin/env python
"""Deterministic anomaly scanner for pre-proof.

This is the mechanical backbone of the pre-proof. Humans and LLMs reliably miss
single invisible characters and stray unicode; a regex/codepoint scan never
does. Run this FIRST, then do the judgment-based passes on top of its output.

It scans an extracted text file line-by-line and reports, with exact line:col
locations and surrounding context:

  [SUBSUP]   unicode subscript/superscript chars (e.g. CO₂, m³) -- the classic
             LLM-pasted-text artifact that should be real formatting instead
  [QUOTE]    curly/smart quotes and prime marks (' ' " " ′ ″)
  [DASH]     en dash, em dash, minus sign, figure dash (vs plain hyphen)
  [SPACE]    non-breaking / thin / zero-width / other exotic spaces
  [INVIS]    zero-width joiners, BOM, soft hyphen, other invisible controls
  [LIGAT]    typographic ligatures (ﬁ ﬂ ﬀ ...) from bad PDF extraction
  [HYPHEN]   line-end hyphenation artifacts ("cata-\nlysis" / "cata- lysis")
  [REPEAT]   doubled words ("the the", "is is")
  [DBLSPACE] runs of 2+ spaces inside a line
  [SPACEPUNCT] space before , . ; : ) or after (
  [NONASCII] any other non-ASCII codepoint (Greek, math, accented) -- reported
             so a human can confirm each is intentional, not a corruption

The scanner FLAGS, it does not judge. A μ in "μmol" is fine; a μ where the
author meant "u" is not. The point is to surface every candidate so nothing
slips through silently.

Usage:
    python scan_anomalies.py <extracted.txt> [report.md]
"""
import sys
import os
import re
import unicodedata

SUBSUP = set(
    # superscripts
    "⁰¹²³⁴⁵⁶⁷⁸⁹"
    "⁺⁻⁼⁽⁾ⁿ"
    # subscripts
    "₀₁₂₃₄₅₆₇₈₉"
    "₊₋₌₍₎"
    "ₐₑₒₓₔₕₖₗₘₙ"
    "ₚₛₜ"
)
QUOTES = set("‘’“”′″‚„‹›«»")
DASHES = set("‐‑‒–—―−⁃")  # excludes plain -
EXOTIC_SPACE = set(
    "          "
    "    　 "
)
INVIS = set("​‌‍⁠﻿­᠎‎‏")
LIGATURES = set("ﬀﬁﬂﬃﬄﬅﬆ")

CHARNAME = {
    " ": "NO-BREAK SPACE", " ": "THIN SPACE", " ": "NARROW NBSP",
    "​": "ZERO WIDTH SPACE", "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER", "﻿": "BOM/ZWNBSP", "­": "SOFT HYPHEN",
    "–": "EN DASH", "—": "EM DASH", "−": "MINUS SIGN",
    "‘": "LEFT SINGLE QUOTE", "’": "RIGHT SINGLE QUOTE/APOSTROPHE",
    "“": "LEFT DOUBLE QUOTE", "”": "RIGHT DOUBLE QUOTE",
    "ﬁ": " fi LIGATURE", "ﬂ": "fl LIGATURE",
}


def cname(ch):
    if ch in CHARNAME:
        return CHARNAME[ch]
    try:
        return unicodedata.name(ch)
    except ValueError:
        return f"U+{ord(ch):04X}"


def ctx(line, col, width=32):
    a = max(0, col - width)
    b = min(len(line), col + width)
    s = line[a:b].replace("\t", " ")
    return ("…" if a > 0 else "") + s + ("…" if b < len(line) else "")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    findings = []  # (category, lineno, col, char/desc, context)

    def add(cat, ln, col, desc, line):
        findings.append((cat, ln, col, desc, ctx(line, col)))

    repeat_re = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)
    dblspace_re = re.compile(r"\S(  +)\S")
    spacepunct_re = re.compile(r"\s[,.;:!?]|\(\s|\s\)")

    for i, line in enumerate(lines, 1):
        for col, ch in enumerate(line):
            if ch in SUBSUP:
                add("SUBSUP", i, col, f"{repr(ch)} {cname(ch)}", line)
            elif ch in QUOTES:
                add("QUOTE", i, col, f"{repr(ch)} {cname(ch)}", line)
            elif ch in DASHES:
                add("DASH", i, col, f"{repr(ch)} {cname(ch)}", line)
            elif ch in EXOTIC_SPACE:
                add("SPACE", i, col, f"{repr(ch)} {cname(ch)}", line)
            elif ch in INVIS:
                add("INVIS", i, col, f"{repr(ch)} {cname(ch)}", line)
            elif ch in LIGATURES:
                add("LIGAT", i, col, f"{repr(ch)} {cname(ch)}", line)
            elif ord(ch) > 127:
                add("NONASCII", i, col, f"{repr(ch)} {cname(ch)}", line)
        # line-end hyphenation artifact
        if re.search(r"[A-Za-z]-\s*$", line):
            add("HYPHEN", i, len(line) - 1, "line-end hyphen (possible split word)", line)
        if re.search(r"[A-Za-z]-\s+[a-z]", line):
            m = re.search(r"[A-Za-z]-\s+[a-z]", line)
            add("HYPHEN", i, m.start(), "mid-line 'word- word' (extraction artifact?)", line)
        for m in repeat_re.finditer(line):
            add("REPEAT", i, m.start(), f"doubled word: '{m.group(0)}'", line)
        for m in dblspace_re.finditer(line):
            add("DBLSPACE", i, m.start(1), f"{len(m.group(1))} consecutive spaces", line)
        for m in spacepunct_re.finditer(line):
            add("SPACEPUNCT", i, m.start(), f"spacing near punctuation: {repr(m.group(0))}", line)

    # group + report
    cats = {}
    for f in findings:
        cats.setdefault(f[0], []).append(f)

    order = ["SUBSUP", "INVIS", "SPACE", "QUOTE", "DASH", "LIGAT",
             "HYPHEN", "REPEAT", "DBLSPACE", "SPACEPUNCT", "NONASCII"]

    md = []
    md.append("# Deterministic anomaly scan\n")
    md.append(f"Source: `{os.path.basename(path)}`  ")
    md.append(f"Total flags: **{len(findings)}**\n")
    md.append("| category | count |")
    md.append("|---|---|")
    for c in order:
        if c in cats:
            md.append(f"| {c} | {len(cats[c])} |")
    md.append("")

    for c in order:
        if c not in cats:
            continue
        md.append(f"\n## {c}  ({len(cats[c])})\n")
        md.append("| line | col | detail | context |")
        md.append("|---|---|---|---|")
        for (_, ln, col, desc, context) in cats[c]:
            safe = context.replace("|", "\\|")
            md.append(f"| {ln} | {col} | {desc} | `{safe}` |")

    report = "\n".join(md)
    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(report)
        print(f"OK: {len(findings)} flags -> {sys.argv[2]}")
    else:
        print(report)


if __name__ == "__main__":
    main()
