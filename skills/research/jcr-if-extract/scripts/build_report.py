"""
Build a single-file HTML report for one JCR year.

Contents: headline numbers, top year-over-year gainers/losers (vs the previous year
in the database), an optional embedded trend plot, and per-category IF tables.
Everything is inlined (the plot is base64-embedded) so the .html is portable.

Usage:
    python build_report.py --year 2025
    python build_report.py --year 2025 --plot if_trend.png --author "Jane Doe"
"""
import argparse
import base64
import json
import time
from pathlib import Path

CSS = """:root{--ink:#1a1a17;--paper:#fafaf7;--muted:#6b6b63;--rule:#d4d4cd;--mark:#ffe14d;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--paper);color:var(--ink);font-family:'IBM Plex Sans KR',sans-serif;font-weight:300;font-size:15px;line-height:1.75;padding:3rem;max-width:920px;margin:0 auto;}
mark{background:var(--mark);padding:0 2px;font-weight:400;}
.mono{font-family:'JetBrains Mono',monospace;}
h1{font-family:'DM Serif Display',serif;font-size:2.8rem;font-weight:400;line-height:1.15;letter-spacing:-1px;margin-bottom:.25rem;}
.date{font-size:.8rem;color:var(--muted);margin-bottom:2.5rem;}
h2{font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:3px;color:var(--muted);margin:2.5rem 0 1rem;padding-bottom:6px;border-bottom:1px solid var(--rule);}
h3{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:2px;color:var(--muted);margin:1.5rem 0 .5rem;}
p{margin-bottom:1rem;}
strong{font-weight:600;}
.num-row{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);margin:1.5rem 0;}
.num-cell{padding:.75rem 1rem;border-right:1px solid var(--rule);}
.num-cell:last-child{border-right:none;}
.num-cell .v{font-family:'JetBrains Mono',monospace;font-size:1.6rem;line-height:1.2;}
.num-cell .l{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-top:.25rem;}
.two{display:grid;grid-template-columns:1fr 1fr;gap:2rem;}
.entry{display:grid;grid-template-columns:2rem 1fr auto;align-items:baseline;padding:.5rem 0;border-bottom:1px solid var(--rule);}
.entry .rank{font-family:'JetBrains Mono',monospace;font-size:.82rem;color:var(--muted);}
.entry .figure{font-family:'JetBrains Mono',monospace;font-size:.82rem;}
.entry .desc{font-size:.82rem;color:var(--muted);}
table{width:100%;border-collapse:collapse;margin:.5rem 0 1.5rem;}
th{font-size:.7rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:var(--muted);text-align:left;padding:.5rem 0;border-bottom:1px solid var(--ink);}
td{padding:.45rem 0;border-bottom:1px solid var(--rule);font-size:.82rem;}
img.trend{width:100%;border:1px solid var(--rule);margin:1rem 0;}
.foot{display:grid;grid-template-columns:1fr auto;border-top:1px solid var(--rule);padding-top:.75rem;margin-top:3rem;font-size:.7rem;color:var(--muted);}
"""


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--detailed", default=None, help="jcr_if_<year>.json (default: derived from --year)")
    ap.add_argument("--db", default="jcr_if_database.json")
    ap.add_argument("--plot", default=None, help="trend PNG to embed (optional)")
    ap.add_argument("--out", default=None, help="output html (default: jcr_<year>_report.html)")
    ap.add_argument("--author", default="", help="optional byline next to the date")
    args = ap.parse_args()

    detailed_path = Path(args.detailed) if args.detailed else Path(f"jcr_if_{args.year}.json")
    cur = json.loads(detailed_path.read_text(encoding="utf-8"))
    db = json.loads(Path(args.db).read_text(encoding="utf-8")) if Path(args.db).exists() else {}
    prev = db.get(str(args.year - 1), {})

    rows = []
    for j in cur["journals"]:
        if_cur = fnum(j["IF"])
        pe = prev.get(j["jcr_abbr"])
        if_prev = fnum(pe["IF"]) if isinstance(pe, dict) else fnum(pe)
        delta = (if_cur - if_prev) if (if_cur is not None and if_prev is not None) else None
        rows.append({"abbr": j["abbr"], "cat": j["category_group"], "cur": if_cur,
                     "prev": if_prev, "delta": delta, "q": j.get("quartile", ""),
                     "rank": j.get("jif_rank", "")})

    cat_order = []
    for r in rows:
        if r["cat"] not in cat_order:
            cat_order.append(r["cat"])

    movers = [r for r in rows if r["delta"] is not None]
    gainers = sorted(movers, key=lambda r: r["delta"], reverse=True)[:8]
    losers = sorted(movers, key=lambda r: r["delta"])[:8]

    n = len(rows)
    n_q1 = sum(1 for r in rows if r["q"] == "Q1")
    vals = [r["cur"] for r in rows if r["cur"] is not None]
    avg = sum(vals) / len(vals) if vals else 0
    top = max(rows, key=lambda r: r["cur"] or 0)

    def cat_table(cat):
        items = sorted([r for r in rows if r["cat"] == cat], key=lambda r: r["cur"] or 0, reverse=True)
        head = (f'<h3>{cat}</h3><table><tr><th>Journal</th><th>{args.year} IF</th>'
                f'<th>{args.year-1}</th><th>delta</th><th>Q</th><th>Rank</th></tr>')
        body = ""
        for r in items:
            dtxt = f'{r["delta"]:+.1f}' if r["delta"] is not None else "&mdash;"
            ptxt = f'{r["prev"]:.1f}' if r["prev"] is not None else "&mdash;"
            ctxt = f'{r["cur"]:.1f}' if r["cur"] is not None else "&mdash;"
            body += (f'<tr><td style="width:32%">{r["abbr"]}</td><td class="mono">{ctxt}</td>'
                     f'<td class="mono">{ptxt}</td><td class="mono">{dtxt}</td>'
                     f'<td>{r["q"]}</td><td class="mono">{r["rank"]}</td></tr>')
        return head + body + "</table>"

    def movers_list(items):
        out = ""
        for i, r in enumerate(items, 1):
            out += (f'<div class="entry"><span class="rank">{i:02d}</span>'
                    f'<span class="name">{r["abbr"]} <span class="desc">{r["prev"]:.1f} &rarr; {r["cur"]:.1f}</span></span>'
                    f'<span class="figure">{r["delta"]:+.1f}</span></div>')
        return out

    plot_html = ""
    if args.plot and Path(args.plot).exists():
        b64 = base64.b64encode(Path(args.plot).read_bytes()).decode()
        plot_html = (f'<h2>Long-run trend</h2><img class="trend" '
                     f'src="data:image/png;base64,{b64}" alt="IF trend">')

    byline = time.strftime("%Y.%m.%d") + (f" &middot; {args.author}" if args.author else "")
    movers_block = ""
    if movers:
        movers_block = (f'<h2>{args.year-1} &rarr; {args.year} movers</h2><div class="two">'
                        f'<div><h3>Top gainers</h3>{movers_list(gainers)}</div>'
                        f'<div><h3>Top losers</h3>{movers_list(losers)}</div></div>')

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{args.year} JCR Impact Factor</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Sans+KR:wght@300;400;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<h1>{args.year} JCR Impact Factor</h1>
<p class="date">{byline}</p>
<p>Impact Factors for <strong>{n}</strong> tracked journals from the {args.year} JCR release.
Year-over-year comparison is against <strong>{args.year-1}</strong>.</p>
<div class="num-row">
  <div class="num-cell"><div class="v">{n}</div><div class="l">journals</div></div>
  <div class="num-cell"><div class="v">{n_q1}</div><div class="l">Q1</div></div>
  <div class="num-cell"><div class="v">{avg:.1f}</div><div class="l">mean IF</div></div>
  <div class="num-cell"><div class="v">{top['cur']:.1f}</div><div class="l">top &middot; {top['abbr']}</div></div>
</div>
{movers_block}
{plot_html}
<h2>By category</h2>
{"".join(cat_table(c) for c in cat_order)}
<div class="foot"><span>Source: Clarivate JCR {args.year}</span><span>{time.strftime("%Y.%m")}</span></div>
</body></html>"""

    out = Path(args.out) if args.out else Path(f"jcr_{args.year}_report.html")
    out.write_text(html, encoding="utf-8")
    print(f"Saved: {out}")
    print(f"Journals: {n} | Q1: {n_q1} | mean IF: {avg:.2f}")
    if gainers:
        print(f"Top gainer: {gainers[0]['abbr']} {gainers[0]['delta']:+.1f}")
    if losers:
        print(f"Top loser:  {losers[0]['abbr']} {losers[0]['delta']:+.1f}")


if __name__ == "__main__":
    main()
