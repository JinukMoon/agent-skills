"""PPT pre-proof 검수기. ppt_dump.sh 가 뽑은 JSON(PowerPoint가 실제 적용한 서식)을 읽어 보고서(md)를 쓴다.

    python ppt_audit.py <fmt.json> [--before orig.json] [--ea 나눔스퀘어] [-o report.md]

검사 항목 (고치지 않고 보고만 한다):
  A. 글꼴      영문·숫자가 Arial이 아닌 곳 / 한글이 덱 대표 글꼴(--ea, 없으면 최다 글꼴)이 아닌 곳
  B. 크기      같은 계층인데 글씨 크기가 다른 곳
               - 여러 슬라이드 같은 자리에 반복되는 상자(제목 등)의 크기가 다수와 다름
               - 한 상자 안에서 같은 수준(lvl) 문단끼리 크기가 다름
               - 한 슬라이드에서 같은 스타일(굵기·색·글꼴)의 상자인데 크기가 0.5~2pt 차이 (실수 의심)
  C. 정렬      한 슬라이드에서 왼쪽·위·가운데 기준선이 0.5~3pt 어긋난 상자 쌍 / 반복 상자 위치가 다수와 다름
  D. 줄바꿈    단어 중간에서 끊김(영문·한글) / 마지막 줄에 1~2글자·짧은 한 단어만 남음 /
               --before 대비 줄 수가 바뀐 문단
  E. 넘침      글자가 상자 아래로 넘침(자동 맞춤 없음) / 슬라이드 밖으로 나감
"""
import argparse
import collections
import json
import re

HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z0-9]")
SYMBOL_FONTS = re.compile(r"^(Symbol|Wingdings.*|Webdings|Cambria Math)$")


def load(p):
    return json.load(open(p, encoding="utf-8-sig"))


def text_of(sh):
    return "".join(r["t"] for p in sh.get("paras") or [] for r in p["runs"])


def short(t, n=28):
    t = t.strip()
    return t if len(t) <= n else t[:n] + "…"


def first_run(sh):
    for p in sh.get("paras") or []:
        for r in p["runs"]:
            if r["t"].strip():
                return r
    return None


def mode(xs):
    return collections.Counter(xs).most_common(1)[0][0]


def audit(d, before=None, ea_main=None):
    out = collections.defaultdict(list)
    slides = d["slides"]
    W, H = d["w"], d["h"]

    # ---- A. 글꼴
    ea_count = collections.Counter()
    for s in slides:
        for sh in s["shapes"]:
            for p in sh.get("paras") or []:
                for r in p["runs"]:
                    ea_count[r["fe"]] += len(HANGUL.findall(r["t"]))
    ea_main = ea_main or (ea_count.most_common(1)[0][0] if ea_count else None)
    for s in slides:
        for sh in s["shapes"]:
            bad = collections.defaultdict(list)
            for p in sh.get("paras") or []:
                for r in p["runs"]:
                    if LATIN.search(r["t"]) and r["f"] != "Arial" and not SYMBOL_FONTS.match(r["f"] or ""):
                        bad[f"영문 {r['f']}"].append(r["t"])
                    if HANGUL.search(r["t"]) and r["fe"] != ea_main:
                        bad[f"한글 {r['fe']}"].append(r["t"])
            for k, v in bad.items():
                out["A"].append(f"s{s['n']} `{sh['name']}`: {k} — \"{short(''.join(v))}\"")

    # ---- B/C. 반복 상자(같은 자리, 3장 이상)
    def key(sh):
        return (round(sh["x"] / 6), round(sh["y"] / 6), round(sh["w"] / 6), round(sh["h"] / 6))
    rep = collections.defaultdict(list)
    for s in slides:
        for sh in s["shapes"]:
            if sh["grp"] is None and first_run(sh):
                rep[key(sh)].append((s["n"], sh))
    for k, items in rep.items():
        if len({n for n, _ in items}) < 3:
            continue
        sizes = [first_run(sh)["sz"] for _, sh in items]
        m = mode(sizes)
        for (n, sh), sz in zip(items, sizes):
            if sz != m:
                out["B"].append(f"s{n} `{sh['name']}` \"{short(text_of(sh))}\": {sz}pt (같은 자리 상자 {len(items)}개는 대부분 {m}pt)")
        for attr in ("x", "y"):
            vals = [round(sh[attr], 1) for _, sh in items]
            mv = mode(vals)
            for (n, sh), v in zip(items, vals):
                if 0.3 < abs(v - mv) <= 12:
                    out["C"].append(f"s{n} `{sh['name']}` \"{short(text_of(sh))}\": {'왼쪽' if attr == 'x' else '위'} {v}pt (같은 자리 상자들은 {mv}pt, {v - mv:+.1f})")

    repkeys = {k for k, items in rep.items() if len({n for n, _ in items}) >= 3}
    seen = set()
    for s in slides:
        tops = [sh for sh in s["shapes"] if sh["grp"] is None and sh["type"] not in ("cell", 6)
                and sh["w"] >= 15 and sh["h"] >= 15]
        # B. 한 상자 안 같은 lvl 문단 크기 차이
        for sh in s["shapes"]:
            bylvl = collections.defaultdict(set)
            for p in (sh.get("paras") or [])[1:]:
                szs = {r["sz"] for r in p["runs"] if r["t"].strip()}
                if len(szs) == 1:
                    bylvl[p["lvl"]].add(next(iter(szs)))
            for lvl, szs in bylvl.items():
                if len(szs) > 1:
                    out["B"].append(f"s{s['n']} `{sh['name']}`: 같은 수준(lvl {lvl}) 문단 크기가 {sorted(szs)}pt로 섞임")
        # B. 같은 스타일 상자끼리 0.5~2pt 차이
        sig = collections.defaultdict(list)
        for sh in s["shapes"]:
            r = first_run(sh)
            if r and len(text_of(sh)) > 1 and sh["grp"] is None:
                sig[(r["b"], r["c"], r["f"], sh["paras"][0]["bullet"])].append((r["sz"], sh))
        for k, lst in sig.items():
            szs = sorted({sz for sz, _ in lst})
            for a, b in zip(szs, szs[1:]):
                if 0.5 <= b - a <= 2:
                    na = [f"`{sh['name']}`" for sz, sh in lst if sz == a][:3]
                    nb = [f"`{sh['name']}`" for sz, sh in lst if sz == b][:3]
                    out["B"].append(f"s{s['n']}: 같은 스타일인데 {a}pt({', '.join(na)}) vs {b}pt({', '.join(nb)}) — 의도한 차이인지 확인")
        # C. 기준선 어긋남: 비슷한 크기 상자들의 같은 기준선 값을 묶어, 묶음 안이 0.5~3pt로 흩어져 있으면 한 줄로 보고
        cand = [sh for sh in tops if key(sh) not in repkeys]
        for name, fn in (("왼쪽", lambda z: z["x"]), ("위", lambda z: z["y"]),
                         ("가로 가운데", lambda z: z["x"] + z["w"] / 2), ("오른쪽", lambda z: z["x"] + z["w"])):
            for dim in ("w", "h"):
                grp = collections.defaultdict(list)          # 크기(폭 또는 높이)가 5% 안인 상자끼리
                for sh in cand:
                    grp[round(sh[dim] / max(4, 0.05 * sh[dim]))].append(sh)
                for members in grp.values():
                    vals = sorted(members, key=fn)
                    clus, cur = [], [vals[0]] if vals else []
                    for z in vals[1:]:
                        if fn(z) - fn(cur[-1]) <= 3:
                            cur.append(z)
                        else:
                            clus.append(cur); cur = [z]
                    if cur:
                        clus.append(cur)
                    for c in clus:
                        spread = fn(c[-1]) - fn(c[0])
                        if len(c) >= 2 and 1.0 <= spread <= 3:
                            sig_ = (s["n"], name, tuple(sorted(z["id"] for z in c)))
                            if sig_ in seen:
                                continue
                            seen.add(sig_)
                            ref = mode([round(fn(z), 1) for z in c])
                            off = [f"`{z['name']}` {fn(z) - ref:+.1f}" for z in c if abs(fn(z) - ref) >= 1.0]
                            out["C"].append(f"s{s['n']}: {name} 기준선이 어긋난 상자 {len(c)}개 (최대 {spread:.1f}pt) — " + ", ".join(off[:5]))

    # ---- D. 줄바꿈 / E. 넘침
    bidx = {}
    if before:
        for s in before["slides"]:
            for sh in s["shapes"]:
                bidx[(s["n"], str(sh["id"]))] = sh
    for s in slides:
        for sh in s["shapes"]:
            paras = sh.get("paras") or []
            for pi, p in enumerate(paras):
                raw = [ln for ln in p.get("lines", []) if ln.strip()]
                manual = [ln.endswith("<BR>") for ln in raw]          # Shift+Enter로 직접 끊은 줄
                lines = [ln.replace("<BR>", "") for ln in raw]
                for a, b, man in zip(lines, lines[1:], manual):
                    if a and b and not man and not a.endswith(" ") and not b.startswith(" "):
                        if a[-1] == "-" and LATIN.match(b[0]) and len(a) > 1 and LATIN.match(a[-2]):
                            out["D"].append(f"s{s['n']} `{sh['name']}`: 하이픈 단어가 줄에서 갈림 \"…{a[-12:]}|{b[:12]}…\"")
                        elif LATIN.match(a[-1]) and LATIN.match(b[0]):
                            out["D"].append(f"s{s['n']} `{sh['name']}`: 영문 단어 중간에서 끊김 \"…{a[-12:]}|{b[:12]}…\"")
                        elif HANGUL.match(a[-1]) and HANGUL.match(b[0]):
                            out["D"].append(f"s{s['n']} `{sh['name']}`: 한글 단어 중간에서 끊김 \"…{a[-10:]}|{b[:10]}…\"")
                if len(lines) >= 2 and sh["w"] >= 60 and not manual[-2]:   # 좁은 라벨·직접 끊은 줄은 제외
                    last = lines[-1].strip()
                    if (len(last) <= 2) or (" " not in last and len(last) <= 4 and len(lines[-2]) >= 12):
                        out["D"].append(f"s{s['n']} `{sh['name']}`: 마지막 줄에 \"{last}\"만 남음 (\"…{lines[-2][-14:]}\")")
            if before:
                ob = bidx.get((s["n"], str(sh["id"])))
                if ob and len(ob.get("paras") or []) == len(paras):
                    for p0, p1 in zip(ob["paras"], paras):
                        l0 = [x.replace("<BR>", "").strip() for x in p0.get("lines", []) if x.strip()]
                        l1 = [x.replace("<BR>", "").strip() for x in p1.get("lines", []) if x.strip()]
                        if l0 and l1 and l0 != l1:
                            out["D"].append(f"s{s['n']} `{sh['name']}`: 줄바꿈 위치 바뀜 (줄 {len(l0)}→{len(l1)})\n    - 전: " + " ⏎ ".join(l0) + "\n    - 후: " + " ⏎ ".join(l1))
            if "bh" in sh and sh["type"] != "cell":
                if sh["by"] + sh["bh"] > sh["y"] + sh["h"] + 3 and sh.get("autosize") != 1:
                    out["E"].append(f"s{s['n']} `{sh['name']}`: 글자가 상자 아래로 {sh['by'] + sh['bh'] - sh['y'] - sh['h']:.1f}pt 넘침")
                if sh["bx"] < -1 or sh["by"] < -1 or sh["bx"] + sh["bw"] > W + 1 or sh["by"] + sh["bh"] > H + 1:
                    out["E"].append(f"s{s['n']} `{sh['name']}`: 글자가 슬라이드 밖으로 나감")
    return out, ea_main


TITLES = {"A": "글꼴 통일", "B": "같은 계층 글씨 크기", "C": "정렬", "D": "줄바꿈", "E": "상자 넘침"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump"); ap.add_argument("--before"); ap.add_argument("--ea"); ap.add_argument("-o")
    a = ap.parse_args()
    d = load(a.dump)
    out, ea = audit(d, load(a.before) if a.before else None, a.ea)
    lines = [f"# PPT pre-proof 검수 — {len(d['slides'])}장", "",
             f"기준: 영문·숫자 = Arial, 한글 = {ea}. 슬라이드 번호 sN = 파일 안 순서(1부터, 표지 포함).", ""]
    for k in "ABCDE":
        items = list(dict.fromkeys(out.get(k, [])))
        lines.append(f"## {k}. {TITLES[k]} — {len(items)}건")
        lines += [f"- {x}" for x in items] or ["- 없음"]
        lines.append("")
    md = "\n".join(lines)
    if a.o:
        open(a.o, "w", encoding="utf-8").write(md)
    print(md)


if __name__ == "__main__":
    main()
