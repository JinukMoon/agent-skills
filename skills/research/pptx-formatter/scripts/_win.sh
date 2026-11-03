# shared: Windows %TEMP% as WSL path + Windows path (PowerPoint must see the file there)
PS=powershell.exe
command -v $PS >/dev/null || PS=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
WIN_TEMP=$($PS -NoProfile -Command '$env:TEMP' | tr -d '\r')
[ -n "$WIN_TEMP" ] || { echo "cannot read Windows %TEMP% (needs WSL + desktop PowerPoint)" >&2; exit 2; }
WSL_TEMP=$(wslpath -u "$WIN_TEMP")
