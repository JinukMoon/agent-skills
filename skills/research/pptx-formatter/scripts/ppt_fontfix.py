"""덱 글꼴 통일: 영문·숫자(latin) = Arial, 한글(ea) = 덱마다 정한 글꼴 하나. 다른 XML은 바이트 그대로.

    python ppt_fontfix.py <in.pptx> <out.pptx> --ea "나눔스퀘어" [--drop-embedded]

- 슬라이드·레이아웃·마스터·테마·차트의 <a:latin>, <a:ea> typeface를 바꾼다(테마의 Hang 스크립트 글꼴 포함).
  기호 글꼴(Symbol, Wingdings*, Webdings, Cambria Math, Marlett)은 그대로 둔다. <a:cs>, <a:sym>, 글머리표 <a:buFont>도 그대로.
- 'Bold/ExtraBold' 같은 굵기 붙은 한글 글꼴 이름은 패밀리 이름 하나로 합치고, 굵기는 b="1"로 옮긴다.
  한글만 든 run은 b="1"을 자동으로 넣고, 영문이 섞인 run은 굵게가 영문에도 번지므로 목록만 출력한다(WARN).
- --drop-embedded: 내장 글꼴(ppt/fonts/*.fntdata)을 전부 뺀다. 나눔스퀘어처럼 '인쇄/미리보기 전용' 권한으로
  내장된 글꼴이 있으면 PowerPoint가 열 때 '제한된 글꼴' 경고를 띄우는데, 이 옵션으로 없앤다.
"""
import argparse
import re
import zipfile

KEEP = re.compile(r"^(Symbol|Wingdings.*|Webdings|Cambria Math|Marlett|MT Extra)$")
TARGET = re.compile(r"^ppt/(slides|slideLayouts|slideMasters|theme|charts|notesMasters|diagrams)/[^/]+\.xml$")
FONT_EL = re.compile(rb"<a:(latin|ea)\b([^>]*?)/>")
HANG = re.compile(rb'(<a:font script="Hang" typeface=")[^"]*(")')
RUN = re.compile(rb"<a:r>.*?</a:r>", re.S)
HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z0-9]")
WEIGHT = re.compile(r"(OTF)?\s*(Bold|ExtraBold|Extra Bold|Heavy|Black)$", re.I)


def fix_xml(data: bytes, latin: str, ea: str, warn: list, fixed: list, where: str) -> bytes:
    def font(m):
        kind, attrs = m.group(1), m.group(2)
        tf = re.search(rb'typeface="([^"]*)"', attrs)
        name = tf.group(1).decode() if tf else ""
        if KEEP.match(name):
            return m.group(0)
        new = latin if kind == b"latin" else ea
        return b'<a:%s typeface="%s"/>' % (kind, new.encode())

    paras = [(pm.start(), pm.end(), pm.group(0)) for pm in re.finditer(rb"<a:p>.*?</a:p>", data, re.S)]

    def para_bold(m):
        """이 run이 든 문단에서 영문 run이 하나도 없거나, 영문 run이 모두 b=1 이면 True."""
        for a0, a1, ptxt in paras:
            if a0 <= m.start() < a1:
                lat = [r for r in RUN.findall(ptxt)
                       if LATIN.search("".join(t.decode() for t in re.findall(rb"<a:t>([^<]*)</a:t>", r)))]
                return all(re.search(rb'<a:rPr\b[^>]*\bb="1"', r) for r in lat)
        return True

    def run(m):
        body = m.group(0)
        eam = re.search(rb'<a:ea typeface="([^"]*)"', body)
        rp = re.search(rb"<a:rPr\b([^>]*?)(/?)>", body)
        if eam and WEIGHT.search(eam.group(1).decode()) and not (rp and re.search(rb'\bb="1"', rp.group(1))):
            text = "".join(t.decode() for t in re.findall(rb"<a:t>([^<]*)</a:t>", body))
            if HANGUL.search(text):
                if not LATIN.search(text) and rp and para_bold(m):   # 한글만 있는 run, 문단의 영문도 굵음 -> b=1
                    attrs = re.sub(rb'\s\bb="0"', b"", rp.group(1)) + b' b="1"'
                    body = body[:rp.start(1)] + attrs + body[rp.end(1):]
                    fixed.append(f"{where}: '{text[:20]}' 굵기 b=1로 옮김")
                elif LATIN.search(text):
                    warn.append(f"{where}: '{text[:20]}' 한글 '{eam.group(1).decode()}'(b 없음)+영문 섞임 -> 굵기 확인 필요")
                else:
                    fixed.append(f"{where}: '{text[:20]}' 문단의 영문이 보통 굵기라 한글도 보통으로 둠")
        return FONT_EL.sub(font, body)

    out = RUN.sub(run, data)          # 글자 run (굵기 처리)
    out = FONT_EL.sub(font, out)      # 테마 fontScheme 등 나머지
    out = HANG.sub(lambda m: m.group(1) + ea.encode() + m.group(2), out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--ea", required=True); ap.add_argument("--latin", default="Arial")
    ap.add_argument("--drop-embedded", action="store_true")
    a = ap.parse_args()
    warn, fixed = [], []
    with zipfile.ZipFile(a.src) as zi, zipfile.ZipFile(a.dst, "w") as zo:
        for info in zi.infolist():
            n = info.filename
            d = zi.read(n)
            if a.drop_embedded and n.startswith("ppt/fonts/"):
                continue
            if TARGET.match(n):
                d = fix_xml(d, a.latin, a.ea, warn, fixed, n)
            if a.drop_embedded and n == "ppt/presentation.xml":
                d = re.sub(rb"<p:embeddedFontLst>.*?</p:embeddedFontLst>", b"", d, flags=re.S)
                d = re.sub(rb' (embedTrueTypeFonts|saveSubsetFonts)="1"', b"", d)
            if a.drop_embedded and n == "ppt/_rels/presentation.xml.rels":
                d = re.sub(rb'<Relationship [^>]*Target="fonts/[^"]*"[^>]*/>', b"", d)
            zo.writestr(info, d)
    for f in fixed:
        print("FIX ", f)
    for w in sorted(set(warn)):
        print("WARN", w)
    print(f"done -> {a.dst} (latin={a.latin}, ea={a.ea}, drop_embedded={a.drop_embedded}, warn={len(set(warn))})")


if __name__ == "__main__":
    main()
