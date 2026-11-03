#!/bin/bash
# deck.pptx -> out.json via PowerPoint COM (read-only; the deck is never modified).
# Usage: ppt_dump.sh deck.pptx out.json
set -e
DECK=$(realpath "$1"); OUT=$(realpath -m "$2"); HERE=$(dirname "$(realpath "$0")")
. "$HERE/_win.sh"
TAG=pptdump_$$; W="$WSL_TEMP/$TAG"; WIN="$WIN_TEMP\\$TAG"
mkdir -p "$W"; cp "$DECK" "$W/d.pptx"; cp "$HERE/ppt_dump.ps1" "$W/e.ps1"
timeout 900 $PS -NoProfile -ExecutionPolicy Bypass -File "$WIN\\e.ps1" "$WIN\\d.pptx" "$WIN\\o.json" 2>&1 | tr -d '\r'
cp "$W/o.json" "$OUT"; rm -rf "$W"
