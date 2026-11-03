"""도형 하나의 줄바꿈 관련 서식을 바꾼다. 내용은 그대로, 다른 XML은 바이트 그대로.

    python ppt_wrap.py <in.pptx> <out.pptx> <슬라이드번호> "<도형 이름>" <동작> [<슬라이드> "<도형>" <동작> ...]

동작:
  wordwrap     영문·한글 단어 중간에서 안 끊기게.
               ① 문단 pPr latinLnBrk="0" ('영문 단어 잘림 허용' 끔)
               ② 한글이 든 run에 lang 이 없으면 lang="ko-KR" 추가 — lang 없는 한글은 PowerPoint가 글자 단위로 끊는다
                  (2026-11-03 실측: eaLnBrk 0/1/삭제 모두 효과 없음, lang="ko-KR"만 효과 있음)
  spc=<n>      자간을 n(1/100 pt, 예 -30 = -0.3pt)으로. 마지막 줄에 한두 단어만 남을 때 한 줄로 당기는 용도
  sz=<pt>      글씨 크기(pt, 예 12 또는 11.5) — 지적받은 크기 통일용
"""
import re
import sys
import zipfile

from lxml import etree

sys.path.insert(0, __import__("os").path.dirname(__file__))
from ppt_break import slide_paths  # noqa: E402

A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def apply(xml: bytes, shape: str, action: str) -> bytes:
    root = etree.fromstring(xml)
    hits = [e for e in root.iter() if e.tag.endswith("}cNvPr") and e.get("name") == shape]
    if len(hits) != 1:
        raise SystemExit(f"도형 '{shape}' 이(가) {len(hits)}개")
    sp = hits[0].getparent().getparent()
    for p in sp.iter(f"{{{A}}}p"):
        if action == "wordwrap":
            ppr = p.find(f"{{{A}}}pPr")
            if ppr is None:
                ppr = etree.Element(f"{{{A}}}pPr")
                p.insert(0, ppr)
            ppr.set("latinLnBrk", "0")
            for r in p.findall(f"{{{A}}}r"):
                t = r.findtext(f"{{{A}}}t") or ""
                rpr = r.find(f"{{{A}}}rPr")
                if re.search("[가-힣]", t) and (rpr is None or rpr.get("lang") is None):
                    if rpr is None:
                        rpr = etree.Element(f"{{{A}}}rPr")
                        r.insert(0, rpr)
                    rpr.set("lang", "ko-KR")
                    rpr.set("altLang", "en-US")
        else:
            key, val = action.split("=")
            if key == "sz":
                val = str(round(float(val) * 100))
            for tag in ("r", "br"):
                for r in p.findall(f"{{{A}}}{tag}"):
                    rpr = r.find(f"{{{A}}}rPr")
                    if rpr is None:
                        rpr = etree.Element(f"{{{A}}}rPr")
                        r.insert(0, rpr)
                    rpr.set(key, val)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def main():
    src, dst, *rest = sys.argv[1:]
    if not rest or len(rest) % 3:
        sys.exit(__doc__)
    with zipfile.ZipFile(src) as zi:
        paths = slide_paths(zi)
        jobs = {}
        for i in range(0, len(rest), 3):
            jobs.setdefault(paths[int(rest[i]) - 1], []).append((rest[i + 1], rest[i + 2]))
        with zipfile.ZipFile(dst, "w") as zo:
            for info in zi.infolist():
                d = zi.read(info.filename)
                for shape, action in jobs.get(info.filename, []):
                    d = apply(d, shape, action)
                    print(f"{info.filename}: '{shape}' {action}")
                zo.writestr(info, d)


if __name__ == "__main__":
    main()
