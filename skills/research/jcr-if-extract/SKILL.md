---
name: jcr-if-extract
description: >-
  Extract Journal Impact Factor (IF) data from Clarivate JCR for a list of journals, build a
  multi-year IF database, plot long-run IF trends, and generate a single-file HTML report with
  year-over-year movers. Use this skill whenever the user wants JCR Impact Factors, "this year's
  IF", "new JCR came out", "올해 IF 나왔다", "JCR IF 추출/정리", journal impact factor tables,
  IF trend plots, or to add a newly released JCR year to an existing IF analysis. The fetch step
  needs a short-lived session token (X-1P-INC-SID) the user copies from their browser on an
  institution network; this skill explains exactly how to grab it. Also trigger for "compare IF
  across years", "which journals' IF jumped/dropped", or "rank journals by impact factor".
---

# JCR Impact Factor Extractor

Fetch Journal Impact Factors from Clarivate JCR for a curated journal list, accumulate them into
a year-keyed database, and turn that into a trend plot and an HTML report. JCR has no public API,
so the fetch reuses the website's own internal endpoint with a session token the user supplies.

## When to use

- User says a new JCR / IF came out and wants it pulled or added to their analysis
- User wants an IF table for a set of journals, an IF trend plot, or an IF report
- User wants year-over-year IF comparison (which journals jumped or dropped)

## The pipeline

```
target_journals.json ──> fetch_jcr_if.py <SID> --year YYYY ──> jcr_if_YYYY.json (detailed)
                                                          └──> jcr_if_database.json (append)
jcr_if_database.json ──> plot_if_trend.py ──────────────────> if_trend.png
jcr_if_YYYY.json + db ─> build_report.py --year YYYY ───────> jcr_YYYY_report.html
```

Three steps, run in order. Step 1 needs the token; steps 2-3 are offline.

## Step 0 — first-run setup (do once)

1. **Dependencies:** `requests`, `matplotlib` (e.g. `pip install requests matplotlib`).
2. **Journal list:** copy `assets/target_journals.example.json` to a working file
   `target_journals.json` and edit it to the journals the user cares about. Each entry is:
   ```json
   {"abbr": "Nat. Catal.", "full": "Nature Catalysis", "issn": "2520-1158", "jcr_abbr": "NAT CATAL"}
   ```
   The **`jcr_abbr`** field must be the exact abbreviated name JCR uses (all caps, e.g.
   `ANGEW CHEM INT EDIT`, `P NATL ACAD SCI USA`). If unsure, search the journal on
   jcr.clarivate.com and read the abbreviated title off the journal profile. A wrong `jcr_abbr`
   just shows up as "NOT FOUND" in the fetch summary — fix it and re-run.

## Step 1 — get the session token (X-1P-INC-SID)

This is the only manual part, and the easy place to go wrong. The token authorizes one browser
session on jcr.clarivate.com and expires fairly quickly, so grab it right before fetching.

1. On an **institution network** (your library subscription), open **https://jcr.clarivate.com**
   and make sure you're logged in / have access.
2. Open dev tools (**F12**) → **Network** tab. Set the filter to **Fetch/XHR**.
3. In the filter box type **`search-result`**, then **do a journal search / apply a category
   filter** on the page so a request fires.
4. Click the request whose name is **`search-result`** — confirm it is:
   - host (`:authority`) = **`jcr.clarivate.com`**  (NOT `snowplow-...clarivate.net`)
   - method = **`POST`**  (NOT `GET`)
   - path = **`/api/jcr3/bwjournal/v1/search-result`**
5. In **Headers → Request Headers**, find **`x-1p-inc-sid`** and copy its value.

Common traps (all produce `401 Unauthorized`):
- Copying from a **snowplow / analytics** request (`*.clarivate.net`, method GET) — wrong host,
  no token there.
- Copying **`correlation-id`** instead of `x-1p-inc-sid` — different header, not a session token.
- A stale token from a previous session — just re-copy a fresh one.

Then fetch:
```bash
python scripts/fetch_jcr_if.py "<SID>" --year 2025
```
The token is passed as an argument only and is never written to disk. Re-run with a different
`--year` to backfill historical years into the same database.

## Step 2 — plot the trend

```bash
python scripts/plot_if_trend.py --out if_trend.png
```
Reads the year range straight from the database, so it never needs editing when a new year is
added. Journals whose IF moved by `--threshold` (default 10) over the covered span are
highlighted and labelled; everything else is light gray context.

## Step 3 — build the HTML report

```bash
python scripts/build_report.py --year 2025 --plot if_trend.png
```
Produces a portable single-file `jcr_2025_report.html`: headline numbers, top year-over-year
gainers/losers vs the previous year, the embedded trend plot, and per-category IF tables.
Pass `--author "Name"` to add a byline.

## Notes for whoever runs this

- **The JIF lives in a field named `jif2019`** in the JCR response — that is just Clarivate's
  internal field name and holds the headline IF for whatever `jcrYear` you requested. Don't
  "fix" it to match the year.
- **Never hard-code the latest year.** The whole point of reading years from the data is that
  these scripts don't rot each June when a new JCR drops. If you add logic, keep it
  data-driven.
- A journal showing up under "NOT FOUND" almost always means its `jcr_abbr` is slightly off, not
  that JCR lacks the data.
- All scripts take `--journals` and `--db` paths if you keep files somewhere other than the cwd.

## Files

```
jcr-if-extract/
├── SKILL.md
├── scripts/
│   ├── fetch_jcr_if.py     # fetch one JCR year -> detailed JSON + append to database
│   ├── plot_if_trend.py    # long-run trend plot (dynamic year range)
│   └── build_report.py     # single-file HTML report with YoY movers
└── assets/
    └── target_journals.example.json   # 72-journal starter list (catalysis/energy/materials/comp)
```
