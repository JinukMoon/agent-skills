"""
Plot long-run JCR Impact Factor trends from the database file.

All journals are drawn in light gray; journals whose IF moved by at least
--threshold over the covered period are highlighted in color and labelled.

The year range is read from the database itself, so it never needs editing when a
new year is added -- that hard-coded-year trap is exactly what makes these scripts
rot. Run it again after fetching a new year and the axis extends on its own.

Usage:
    python plot_if_trend.py
    python plot_if_trend.py --db jcr_if_database.json --journals target_journals.json \
        --out if_trend.png --threshold 10
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

HIGHLIGHT_COLORS = [
    "#E63946", "#1D3557", "#E76F51", "#2A9D8F", "#F4A261",
    "#264653", "#D62828", "#457B9D", "#6A0572", "#FF6B6B",
]


def load_journals(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for items in data["categories"].values():
        out.extend(items)
    return out


def jcr_name(j):
    return j.get("jcr_abbr") or j["abbr"].upper().rstrip(".")


def maybe_set_font():
    """Use Helvetica if present; otherwise fall back silently to the default."""
    for p in ("/home/jumoon/fonts/Helvetica.ttf",):
        if Path(p).exists():
            fm.fontManager.addfont(p)
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = ["Helvetica"]
            return


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="jcr_if_database.json")
    ap.add_argument("--journals", default="target_journals.json")
    ap.add_argument("--out", default="if_trend.png")
    ap.add_argument("--threshold", type=float, default=10.0, help="|delta IF| to highlight a journal")
    args = ap.parse_args()

    history = json.loads(Path(args.db).read_text(encoding="utf-8"))
    journals = load_journals(args.journals)

    years = sorted(int(y) for y in history.keys())            # <- dynamic, from data
    if not years:
        raise SystemExit("database is empty")

    series = {}
    for j in journals:
        name = jcr_name(j)
        vals = []
        for y in years:
            entry = history.get(str(y), {}).get(name)
            v = entry.get("IF") if isinstance(entry, dict) else entry
            try:
                vals.append(float(v) if v not in (None, "N/A") else None)
            except (ValueError, TypeError):
                vals.append(None)
        series[j["abbr"]] = vals

    highlight = {}
    for abbr, vals in series.items():
        valid = [v for v in vals if v is not None]
        if len(valid) >= 2 and abs(valid[-1] - valid[0]) >= args.threshold:
            highlight[abbr] = valid[-1] - valid[0]

    maybe_set_font()
    plt.rcParams["axes.linewidth"] = 0.8
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FAFAFA")

    for abbr, vals in series.items():
        if abbr in highlight:
            continue
        xs = [y for y, v in zip(years, vals) if v is not None]
        ys = [v for v in vals if v is not None]
        if len(xs) >= 2:
            ax.plot(xs, ys, color="#D5D5D5", linewidth=0.7, alpha=0.5)

    for idx, (abbr, delta) in enumerate(sorted(highlight.items(), key=lambda x: abs(x[1]), reverse=True)):
        vals = series[abbr]
        xs = [y for y, v in zip(years, vals) if v is not None]
        ys = [v for v in vals if v is not None]
        color = HIGHLIGHT_COLORS[idx % len(HIGHLIGHT_COLORS)]
        ax.plot(xs, ys, color=color, linewidth=2.5, alpha=0.95, zorder=5)
        ax.scatter(xs[-1], ys[-1], color=color, s=30, zorder=6)
        ax.annotate(f" {abbr} ({delta:+.1f})", xy=(xs[-1], ys[-1]), xytext=(8, 0),
                    textcoords="offset points", fontsize=8.5, color=color,
                    fontweight="bold", va="center")

    ax.set_xlabel("Year", fontsize=13, labelpad=8)
    ax.set_ylabel("Impact Factor", fontsize=13, labelpad=8)
    ax.set_title(f"JCR Impact Factor Trends ({years[0]}-{years[-1]})",
                 fontsize=16, fontweight="bold", pad=12)
    ax.text(0.5, 1.02, rf"Highlighted: journals with |$\Delta$IF| $\geq$ {args.threshold:g} over the period",
            transform=ax.transAxes, ha="center", fontsize=11, color="#666666")
    ax.set_xlim(years[0] - 0.5, years[-1] + 3.5)
    ymax = max((v for vals in series.values() for v in vals if v is not None), default=10)
    ax.set_ylim(-1, ymax * 1.08)
    ax.set_xticks([y for y in years if y % 3 == 0])
    ax.tick_params(labelsize=11, length=4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#AAAAAA")

    plt.tight_layout()
    plt.savefig(args.out, dpi=250, bbox_inches="tight", facecolor="white")
    print(f"Saved: {args.out}  ({years[0]}-{years[-1]})")
    for abbr, delta in sorted(highlight.items(), key=lambda x: abs(x[1]), reverse=True):
        valid = [v for v in series[abbr] if v is not None]
        print(f"  {abbr:<28s} {valid[0]:>5.1f} -> {valid[-1]:>5.1f}  (delta: {delta:+.1f})")


if __name__ == "__main__":
    main()
