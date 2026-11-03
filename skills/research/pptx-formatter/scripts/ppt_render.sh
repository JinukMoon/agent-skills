#!/bin/bash
# Render slides with REAL PowerPoint (COM) -> <outdir>/s<N>.png (+ sheet.png contact sheet).
# Usage: ppt_render.sh deck.pptx outdir [N ...]   (N = 1-based slide index in the file; none = all)
# Judge layout ONLY from these PNGs, never LibreOffice (it reflows text and drops some Korean bold faces).
set -e
DECK=$(realpath "$1"); OUT=$(realpath -m "$2"); shift 2; HERE=$(dirname "$(realpath "$0")")
. "$HERE/_win.sh"
mkdir -p "$OUT"
TAG=pprender_$$; W="$WSL_TEMP/$TAG"; WIN="$WIN_TEMP\\$TAG"
mkdir -p "$W"; cp "$DECK" "$W/d.pptx"
LIST=$(IFS=,; echo "$*")
cat > "$W/e.ps1" <<PS1
\$was = @(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count -gt 0
\$ppt = New-Object -ComObject PowerPoint.Application
\$p = \$ppt.Presentations.Open("$WIN\\d.pptx", \$true, \$false, \$false)
Write-Output ("slides=" + \$p.Slides.Count)
\$idx = @($LIST); if (\$idx.Count -eq 0) { \$idx = 1..\$p.Slides.Count }
foreach (\$i in \$idx) { \$p.Slides.Item(\$i).Export("$WIN\\s\$i.png", "PNG", 1600, 900) }
\$p.Close(); if (-not \$was) { \$ppt.Quit() }; Write-Output "exported"
PS1
timeout 600 $PS -NoProfile -ExecutionPolicy Bypass -File "$WIN\\e.ps1" 2>&1 | tr -d '\r'
cp "$W"/s*.png "$OUT"/
python3 - "$OUT" <<'PY' || true
import sys, glob, re
try:
    from PIL import Image
except ImportError:
    sys.exit()
out = sys.argv[1]
fs = sorted([f for f in glob.glob(f"{out}/s*.png") if re.search(r"/s\d+\.png$", f)], key=lambda f: int(re.findall(r"s(\d+)\.png", f)[0]))
ims = [Image.open(f).convert("RGB").resize((800, 450)) for f in fs]
if ims:
    cols = 2 if len(ims) <= 6 else 3
    S = Image.new("RGB", (800 * cols, 450 * ((len(ims) + cols - 1) // cols)), "white")
    for k, im in enumerate(ims):
        S.paste(im, ((k % cols) * 800, (k // cols) * 450))
    S.save(f"{out}/sheet.png"); print(f"{len(ims)} slides -> {out}/sheet.png")
PY
rm -rf "$W"
