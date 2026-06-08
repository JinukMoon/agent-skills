#!/usr/bin/env python3
"""
pptx -> high-fidelity PDF on WSL by driving Windows PowerPoint via COM.

Why this exists: LibreOffice re-flows text (line breaks shift), and even
PowerPoint's own *vector* PDF export renders "fatter" than the editing screen
because the PDF viewer re-rasterizes font outlines. The only way to get a PDF
that looks EXACTLY like PowerPoint on screen is to bake PowerPoint's own
rasterized slides into the PDF as images. This script does that:

  1. Stage the .pptx under the Windows TEMP dir as ASCII `input.pptx`
     (Korean filenames get mangled crossing the WSL<->Windows boundary).
  2. Drive Windows PowerPoint via powershell.exe COM to export every slide
     as PNG at a chosen pixel size (default 6827x3840 = "7K"). This uses
     Slide.Export(path,"PNG",w,h) which takes explicit pixel dimensions, so
     NO registry ExportBitmapResolution tweak is needed.
  3. Re-encode each PNG and combine into one PDF with img2pdf, page size in
     the slide's own aspect ratio (13.333in wide).
  4. Default encoding is JPEG quality=95, subsampling=0 (4:4:4): visually
     identical to lossless (measured max per-pixel diff <=5/255, 0% of pixels
     differ by >5 levels) at ~1/3 the size. --lossless keeps exact pixels.

Output: plain `<pptx-basename>.pdf` next to the input, no quality suffix.

Requires: Pillow + img2pdf. On this machine use the toolkit env interpreter:
  /home/jumoon/miniconda3/envs/toolkit/bin/python
"""
import argparse, os, re, shutil, subprocess, sys, tempfile


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def win_temp_dir():
    """Return (wsl_path, win_path) of a fresh work dir under Windows TEMP."""
    r = run(["powershell.exe", "-NoProfile", "-Command", "$env:TEMP"])
    win_temp = r.stdout.strip().strip("\r")
    if not win_temp:
        sys.exit("Could not read Windows %TEMP% via powershell.exe")
    wsl_temp = run(["wslpath", "-u", win_temp]).stdout.strip()
    work_wsl = os.path.join(wsl_temp, "pptx2pdf_work")
    shutil.rmtree(work_wsl, ignore_errors=True)
    os.makedirs(os.path.join(work_wsl, "png"), exist_ok=True)
    work_win = run(["wslpath", "-w", work_wsl]).stdout.strip()
    return work_wsl, work_win


def export_pngs(pptx_path, work_wsl, work_win, width, height):
    """Copy pptx in, run PowerPoint COM export, return sorted PNG paths."""
    shutil.copy(pptx_path, os.path.join(work_wsl, "input.pptx"))
    ps = r'''$ErrorActionPreference = "Stop"
$in  = "{win}\input.pptx"
$dir = "{win}\png"
$ppt = New-Object -ComObject PowerPoint.Application
try {{
    $pres = $ppt.Presentations.Open($in, $true, $false, $false)
    $n = $pres.Slides.Count
    for ($i=1; $i -le $n; $i++) {{
        $fn = "{{0}}\s{{1:D3}}.png" -f $dir, $i
        $pres.Slides.Item($i).Export($fn, "PNG", {w}, {h})
    }}
    $pres.Close()
    Write-Output ("PNG_OK count=" + $n)
}} catch {{
    Write-Output ("PNG_FAIL: " + $_.Exception.Message)
}} finally {{
    $ppt.Quit()
}}
'''.format(win=work_win, w=width, h=height)
    ps_path = os.path.join(work_wsl, "export.ps1")
    with open(ps_path, "w") as f:
        f.write(ps)
    ps_win = run(["wslpath", "-w", ps_path]).stdout.strip()
    r = run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", ps_win], timeout=900)
    out = (r.stdout + r.stderr)
    # decode possible CP949 mojibake just for the message
    print("  PowerPoint:", out.strip().splitlines()[-1] if out.strip() else "(no output)")
    if "PNG_OK" not in out:
        sys.exit(f"PowerPoint export failed:\n{out}")
    pngs = [os.path.join(work_wsl, "png", p)
            for p in os.listdir(os.path.join(work_wsl, "png")) if p.lower().endswith(".png")]
    pngs.sort(key=lambda f: int(re.search(r"(\d+)", os.path.basename(f)).group(1)))
    return pngs


def build_pdf(pngs, out_pdf, lossless, quality):
    from PIL import Image
    import img2pdf
    tmp = tempfile.mkdtemp()
    try:
        srcs = []
        for f in pngs:
            im = Image.open(f)
            if im.mode != "RGB":                 # palette/alpha -> flatten (slides are opaque)
                im = im.convert("RGB")
            if lossless:
                o = os.path.join(tmp, os.path.basename(f))
                im.save(o, "PNG")                 # exact pixels, no alpha/SMask
            else:
                o = os.path.join(tmp, os.path.splitext(os.path.basename(f))[0] + ".jpg")
                im.save(o, "JPEG", quality=quality, subsampling=0, optimize=True)
            srcs.append(o)
        # page size: keep the slide's aspect, 13.333in wide (16:9 -> 7.5in; 4:3 -> 10in)
        w0, h0 = Image.open(srcs[0]).size
        pw = img2pdf.in_to_pt(13.333)
        layout = img2pdf.get_layout_fun((pw, pw * h0 / w0))
        with open(out_pdf, "wb") as fo:
            fo.write(img2pdf.convert(srcs, layout_fun=layout))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="pptx -> high-fidelity PDF via Windows PowerPoint COM")
    ap.add_argument("pptx", help="path to the .pptx file")
    ap.add_argument("-o", "--output", help="output PDF path (default: <basename>.pdf next to input)")
    ap.add_argument("--lossless", action="store_true",
                    help="embed exact PNG pixels (~3x larger); default is visually-lossless JPEG q95")
    ap.add_argument("--quality", type=int, default=95, help="JPEG quality when not --lossless (default 95)")
    ap.add_argument("--width", type=int, default=6827, help="PNG export width in px (default 6827 = 7K)")
    ap.add_argument("--height", type=int, default=3840, help="PNG export height in px (default 3840)")
    a = ap.parse_args()

    pptx = os.path.abspath(a.pptx)
    if not os.path.isfile(pptx):
        sys.exit(f"Not found: {pptx}")
    out_pdf = os.path.abspath(a.output) if a.output else \
        os.path.join(os.path.dirname(pptx), os.path.splitext(os.path.basename(pptx))[0] + ".pdf")

    print(f"-> {os.path.basename(pptx)}")
    print(f"   exporting slides @ {a.width}x{a.height} via PowerPoint COM ...")
    work_wsl, work_win = win_temp_dir()
    try:
        pngs = export_pngs(pptx, work_wsl, work_win, a.width, a.height)
        print(f"   {len(pngs)} slides -> combining ({'lossless PNG' if a.lossless else f'JPEG q{a.quality}'}) ...")
        build_pdf(pngs, out_pdf, a.lossless, a.quality)
    finally:
        shutil.rmtree(work_wsl, ignore_errors=True)
    mb = os.path.getsize(out_pdf) / 1024 / 1024
    print(f"   DONE: {out_pdf}  ({mb:.1f} MB, {len(pngs)} pages)")


if __name__ == "__main__":
    main()
