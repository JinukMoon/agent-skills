#!/usr/bin/env python
"""Generate high-resolution QR code PNGs in the house style, then verify by decoding.

House style:
  version 5, ERROR_CORRECT_H, box_size 20, border 2, plus a 20 px white margin
  and a 20 px black frame -> 860x860 px for a typical URL.

Usage:
  make_qr.py "https://catbench.org/"                       # -> ./qr_catbench_org.png
  make_qr.py "https://x.y" -o out.png                        # explicit filename
  make_qr.py "tel:01012345678" -o phone.png                  # phone number (tel: scheme)
  make_qr.py --batch links.txt -d outdir/                    # one per line: [name<TAB>]url
  make_qr.py "https://x.y" --no-frame                        # plain (no black frame)
  make_qr.py "https://x.y" --box 10                          # smaller image

Every generated file is decoded back and compared to the input; a mismatch
exits non-zero so a broken QR never ships silently.
"""
import argparse
import os
import re
import sys

import qrcode
from PIL import Image, ImageDraw


def slug(text):
    """Short readable name: repo URLs -> last path part(s); domains -> domain; else sanitized text.
    https://github.com/JinukMoon/oh-my-mlip -> oh_my_mlip ; https://catbench.org/ -> catbench_org ;
    tel:0101234 -> tel_0101234"""
    t = text.strip()
    if t.startswith(("tel:", "mailto:")):
        return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")[:60]
    m = re.match(r"^https?://([^/]+)(/.*)?$", t)
    if m:
        host, path = m.group(1), (m.group(2) or "").strip("/")
        base = path.split("/")[-1] if path else host
        return re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")[:60] or "qr"
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")[:60] or "qr"


def build(data, box=20, frame=True):
    qr = qrcode.QRCode(version=5, error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=box, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    if not frame:
        return img
    b = box  # margin scales with box size (20 px at default)
    w, h = img.size
    out = Image.new("RGB", (w + 2 * b, h + 2 * b), "white")
    out.paste(img, (b, b))
    ImageDraw.Draw(out).rectangle([(0, 0), (out.width - 1, out.height - 1)], outline="black", width=b)
    return out


def decode(path):
    try:
        from pyzbar.pyzbar import decode as zdecode
        r = zdecode(Image.open(path))
        return r[0].data.decode() if r else ""
    except ImportError:
        pass
    try:
        import cv2
        val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(path))
        return val
    except ImportError:
        return None  # no decoder available


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", nargs="?", help="URL / text / tel:number to encode")
    ap.add_argument("-o", "--out", help="output PNG path (single mode)")
    ap.add_argument("--batch", help="text file: one entry per line, optional 'name<TAB>data'")
    ap.add_argument("-d", "--outdir", default=".", help="output directory (batch mode or when -o omitted)")
    ap.add_argument("--box", type=int, default=20, help="module size in px (default 20)")
    ap.add_argument("--no-frame", action="store_true", help="omit the black frame")
    a = ap.parse_args()

    jobs = []
    if a.batch:
        with open(a.batch) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "\t" in line:
                    name, data = line.split("\t", 1)
                    fname = name.strip() + ("" if name.strip().endswith(".png") else ".png")
                else:
                    data = line
                    fname = f"qr_{slug(data)}.png"
                jobs.append((os.path.join(a.outdir, fname), data.strip()))
    elif a.data:
        out = a.out or os.path.join(a.outdir, f"qr_{slug(a.data)}.png")
        jobs.append((out, a.data))
    else:
        ap.error("give DATA or --batch FILE")

    os.makedirs(a.outdir, exist_ok=True)
    bad = 0
    for path, data in jobs:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        img = build(data, box=a.box, frame=not a.no_frame)
        img.save(path)
        got = decode(path)
        if got is None:
            status = "saved (no decoder installed; not verified)"
        elif got == data:
            status = "OK verified"
        else:
            status = f"MISMATCH decoded={got!r}"
            bad += 1
        print(f"{path}  {img.size[0]}x{img.size[1]}  -> {data}  [{status}]")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
