"""원본과 고친 PPTX를 비교해 '지적한 곳만 바뀌었고 애니메이션은 그대로인지' 확인한다.

    python ppt_diff.py <원본.pptx> <고친.pptx> [--allow N,M,...]

출력:
  - 추가/삭제/변경된 zip 항목 목록 (docProps/core.xml·app.xml 변경은 정상)
  - 슬라이드별 애니메이션(<p:timing>) 비교: 같음 / 다름
    (다르면 FAIL. 다만 슬라이드의 모양 id(spid)가 그대로면 timing XML은 바이트까지 같아야 정상)
  - 애니메이션이 가리키는 모양 id(spTgt spid)가 고친 슬라이드에 다 있는지
  - --allow 로 준 슬라이드 번호(1부터) 밖의 슬라이드 XML이 바뀌었으면 WARN
종료코드: 애니메이션 문제가 있으면 1, 없으면 0.
"""
import re
import sys
import zipfile

from lxml import etree

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def slide_order(z):
    pres = etree.fromstring(z.read("ppt/presentation.xml"))
    rels = etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    rid2t = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for s in pres.iter(f"{{{P}}}sldId"):
        t = rid2t[s.get(f"{{{R}}}id")]
        out.append("ppt/" + t.lstrip("/").replace("ppt/", "", 1) if not t.startswith("/") else t.lstrip("/"))
    return out


def timing(xml):
    root = etree.fromstring(xml)
    t = root.find(f"{{{P}}}timing")
    return (etree.tostring(t, method="c14n") if t is not None else b""), root


def main():
    args = sys.argv[1:]
    allow = set()
    if "--allow" in args:
        i = args.index("--allow")
        allow = {int(x) for x in args[i + 1].split(",") if x}
        del args[i:i + 2]
    a, b = zipfile.ZipFile(args[0]), zipfile.ZipFile(args[1])
    na, nb = set(a.namelist()), set(b.namelist())
    added, removed = sorted(nb - na), sorted(na - nb)
    changed = sorted(n for n in na & nb if a.read(n) != b.read(n))
    print(f"zip 항목: 추가 {len(added)} / 삭제 {len(removed)} / 변경 {len(changed)}")
    for tag, lst in (("+", added), ("-", removed), ("~", changed)):
        for n in lst:
            print(f"  {tag} {n}")

    oa, ob = slide_order(a), slide_order(b)
    bad = 0
    if len(oa) != len(ob):
        print(f"WARN 슬라이드 수 변경: {len(oa)} -> {len(ob)} (아래 비교는 순서대로 짝지음)")
    for k, (sa, sb) in enumerate(zip(oa, ob), 1):
        ta, _ = timing(a.read(sa))
        tb, rb = timing(b.read(sb))
        ids = {e.get("id") for e in rb.iter(f"{{{P}}}cNvPr")}
        tgt = set(re.findall(rb"spid=\"(\d+)\"", tb))
        missing = sorted(t.decode() for t in tgt if t.decode() not in ids)
        nanim = len(re.findall(rb"presetClass=", tb))
        if ta != tb:
            print(f"FAIL s{k}: 애니메이션 XML이 달라짐 ({len(re.findall(rb'presetClass=', ta))} -> {nanim} 효과)")
            bad += 1
        if missing:
            print(f"FAIL s{k}: 애니메이션 대상 모양 id {missing} 가 슬라이드에 없음")
            bad += 1
        if a.read(sa) != b.read(sb) and k not in allow and allow:
            print(f"WARN s{k}: 지적 안 한 슬라이드가 바뀜")
    total = sum(len(re.findall(rb"presetClass=", timing(b.read(s))[0])) for s in ob)
    print(f"애니메이션 효과 총 {total}개, 문제 {bad}건 -> {'OK' if not bad else 'FAIL'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
