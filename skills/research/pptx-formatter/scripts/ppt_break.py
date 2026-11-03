"""지정한 글자 앞에 줄바꿈(Shift+Enter = <a:br/>)을 넣는다. 같은 문단·서식은 유지, 다른 XML은 바이트 그대로.

    python ppt_break.py <in.pptx> <out.pptx> <슬라이드번호> "<도형 이름>" "<이 글자 앞에서>" [...]

  슬라이드번호 = 파일 안 순서(1부터, 표지 포함). 마지막 세 인자는 여러 번 반복 가능
  (예: 2 "TextBox 14" "Core-Shell" 2 "TextBox 31" "Large"). 끊는 자리 앞의 공백은 지운다.
  대상 글자가 한 run 안에 있어야 한다(없으면 에러).
"""
import re
import sys
import zipfile

from lxml import etree

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def slide_paths(z):
    pres = etree.fromstring(z.read("ppt/presentation.xml"))
    rels = {r.get("Id"): r.get("Target") for r in etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))}
    return ["ppt/" + rels[s.get(f"{{{R}}}id")] for s in pres.iter(f"{{{P}}}sldId")]


def insert_break(xml: bytes, shape: str, before: str) -> bytes:
    root = etree.fromstring(xml)
    sps = [e for e in root.iter() if e.tag.endswith("}cNvPr") and e.get("name") == shape]
    if len(sps) != 1:
        raise SystemExit(f"도형 '{shape}' 이(가) {len(sps)}개")
    sp = sps[0].getparent().getparent()
    for r in sp.iter(f"{{{A}}}r"):
        t = r.find(f"{{{A}}}t")
        if t is not None and t.text and before in t.text:
            i = t.text.index(before)
            head, tail = t.text[:i].rstrip(" "), t.text[i:]
            rpr = r.find(f"{{{A}}}rPr")
            br = etree.Element(f"{{{A}}}br")
            if rpr is not None:
                br.append(etree.fromstring(etree.tostring(rpr)))
            r2 = etree.fromstring(etree.tostring(r))
            r2.find(f"{{{A}}}t").text = tail
            if head:
                t.text = head
                r.addnext(br)
            else:                       # 끊을 글자가 run 맨 앞: 앞 run 끝 공백 정리
                prev = r.getprevious()
                pt = prev.find(f"{{{A}}}t") if prev is not None and prev.tag == f"{{{A}}}r" else None
                if pt is not None and pt.text:
                    pt.text = pt.text.rstrip(" ")
                r.addprevious(br)
                return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            br.addnext(r2)
            return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    raise SystemExit(f"'{shape}' 안에 '{before}' 가 든 run 없음")


def main():
    src, dst, *rest = sys.argv[1:]
    if not rest or len(rest) % 3:
        sys.exit(__doc__)
    jobs = [(int(rest[i]), rest[i + 1], rest[i + 2]) for i in range(0, len(rest), 3)]
    with zipfile.ZipFile(src) as zi:
        paths = slide_paths(zi)
        targets = {}
        for n, shape, before in jobs:
            targets.setdefault(paths[n - 1], []).append((shape, before))
        with zipfile.ZipFile(dst, "w") as zo:
            for info in zi.infolist():
                d = zi.read(info.filename)
                for shape, before in targets.get(info.filename, []):
                    d = insert_break(d, shape, before)
                    print(f"{info.filename}: '{shape}' 의 '{before}' 앞에 줄바꿈")
                zo.writestr(info, d)


if __name__ == "__main__":
    main()
