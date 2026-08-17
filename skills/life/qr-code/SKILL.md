---
name: qr-code
description: Generate QR code PNG images from a URL, link, phone number, or short text — in a fixed print/slide-ready house style (version 5, high error correction, 20 px modules, black frame; 860×860 px) — and verify each one by decoding it back. Use this whenever the user asks for a QR code in any phrasing — "QR 만들어줘", "QR 코드", "큐알", "make a QR for this link", "링크를 QR로", "발표자료에 넣을 QR", "명함/포스터용 QR", "전화번호 QR" — including when they hand over one or several links and want images for a slide, poster, README, or business card. Do not use for reading/scanning an existing QR image (that is decoding, not generation) unless the user also wants a new one made.
---

# QR code generation

Bundled script: `scripts/make_qr.py`. It produces one consistent style so every QR in a deck,
poster, or README looks the same, and it decodes every output back to catch broken codes
before they land on a slide.

## First-run setup

Ask once which Python interpreter to use (any env with `qrcode[pil]`; `pyzbar` or
`opencv-python` optional for verification). Remember it as `{PY}` below.

```bash
pip install "qrcode[pil]" pyzbar     # or: pip install "qrcode[pil]" opencv-python
```

## Run

```bash
PY={PY}
S=~/.claude/skills/qr-code/scripts/make_qr.py

$PY $S "https://catbench.org/"                          # -> ./qr_catbench_org.png
$PY $S "https://github.com/JinukMoon/CatBench" -o qr_catbench_github.png
$PY $S "tel:01012345678" -o qr_phone.png                 # phone numbers use tel:
$PY $S --batch links.txt -d assets/qr/                   # many at once
```

`links.txt` for batch mode — one per line, optional `name<TAB>url` (name becomes the filename):

```
qr_leaderboard	https://catbench.org/
qr_catbench_github	https://github.com/JinukMoon/CatBench
https://github.com/JinukMoon/oh-my-mlip
```

Options: `--box N` (module px, default 20 → 860 px image; use 10 for ~430 px), `--no-frame`
(drop the black border), `-d DIR` (output folder).

## Why these choices (so you can deviate sensibly)

- **version 5 + ERROR_CORRECT_H**: H-level correction survives partial occlusion (logo
  overlays, glare on a projector, a phone camera at an angle) — the situation a conference
  QR actually lives in. Version 5 comfortably holds any URL up to ~80 chars at H.
- **box 20 + black frame**: the frame gives a clean quiet-zone boundary on white slides and
  posters. Keep it unless the user asks for a borderless one.
- **Decode verification**: the script re-reads each PNG (pyzbar or OpenCV, whichever is
  installed) and exits non-zero on mismatch. Report the `[OK verified]` line to the user;
  if it prints `no decoder installed`, say so — don't claim verification you didn't get.

## Workflow

1. Confirm the exact target strings. URLs: include the scheme (`https://`); phone: `tel:` +
   digits, no hyphens; plain text is fine too. If a URL is ambiguous (repo vs. website), ask
   once — a QR to the wrong page is worse than no QR.
2. Pick filenames that say what they point to (`qr_leaderboard.png`, not `qr1.png`) — decks
   accumulate many QRs and nobody can tell them apart visually.
3. Run the script; save into the project's asset folder (e.g. `assets/qr/`), not `/tmp`.
4. Paste the verification lines back to the user. If the QR is going on a slide, mention the
   size: 860 px renders crisp at 1.2–1.5 in; below ~1 in the modules get too fine for phones
   across a room.
5. If several QRs go on one slide, a caption under each (site name / repo name) is worth
   more than the URL text — people scan the one they want.

## Dependencies

`qrcode[pil]` (required). Decoding uses `pyzbar` or `opencv-python` if present; absence only
disables verification, not generation.
