"""
Fetch JCR Impact Factor data for a list of journals, for a single JCR year.

Writes two things:
  1. A detailed per-year file  jcr_if_<year>.json   (all metrics, one row per journal)
  2. An append into the long    <db>.json            (compact, keyed by year -> journal)

The JCR site has no public API, so we call the same internal endpoint the website
uses. That endpoint needs a session token (X-1P-INC-SID) that you copy from your
browser while logged in on an institution network. See SKILL.md for how to grab it.
The token is short-lived and is never written to disk -- it is only passed as an arg.

Usage:
    python fetch_jcr_if.py <SID> --year 2025
    python fetch_jcr_if.py <SID> --year 2025 --journals my_journals.json --db jcr_if_database.json
    python fetch_jcr_if.py <SID> --year 2025 --no-db        # detailed file only

The journal list is a JSON file (see assets/target_journals.example.json). Each entry
carries its own "jcr_abbr" -- the exact abbreviated journal name JCR uses -- so there
is no hard-coded name mapping to keep in sync.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

API_URL = "https://jcr.clarivate.com/api/jcr3/bwjournal/v1/search-result"


def load_journals(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    journals = []
    for category, items in data["categories"].items():
        for j in items:
            journals.append({**j, "category_group": category})
    return journals


def jcr_name(j):
    """Exact abbreviated name JCR uses. Prefer the explicit field; fall back to a guess."""
    return j.get("jcr_abbr") or j["abbr"].upper().rstrip(".")


def fetch_year(sid, jcr_names, year):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-1P-INC-SID": sid,
    }
    body = {
        "journalFilterParameters": {
            "query": "",
            "journals": jcr_names,
            "categories": [],
            "publishers": [],
            "countryRegions": [],
            "citationIndexes": ["SCIE", "SSCI", "AHCI", "ESCI"],
            "jcrYear": year,
            "categorySchema": "WOS",
            "openAccess": "N",
            "jifQuartiles": [],
            "jifRanges": [],
            "jifNA": False,
            "jifPercentileRanges": [],
            "jciRanges": [],
            "oaRanges": [],
            "issnJ20s": [],
        },
        "retrievalParameters": {"start": 1, "count": 600, "sortBy": "", "sortOrder": "DESC"},
    }
    for attempt in range(3):
        resp = requests.post(API_URL, headers=headers, json=body, timeout=30)
        if resp.status_code == 401:
            sys.exit(
                "ERROR 401 Unauthorized -- the SID is wrong or expired.\n"
                "Make sure you copied the value of the 'x-1p-inc-sid' header from the\n"
                "POST request to .../bwjournal/v1/search-result (NOT a snowplow/analytics\n"
                "request, and NOT 'correlation-id'). See SKILL.md."
            )
        data = resp.json()
        if "message" in data and "rate limit" in data["message"].lower():
            wait = 30 * (attempt + 1)
            print(f"  rate limited, waiting {wait}s...", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return data
    sys.exit("ERROR: rate limited repeatedly; try again later.")


# JCR's internal field that holds the headline JIF value is literally named "jif2019"
# regardless of the reporting year. Do not be fooled by the name.
JIF_FIELD = "jif2019"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sid", help="X-1P-INC-SID session token from jcr.clarivate.com")
    ap.add_argument("--year", type=int, required=True, help="JCR reporting year, e.g. 2025")
    ap.add_argument("--journals", default="target_journals.json", help="journal list JSON")
    ap.add_argument("--outdir", default=".", help="where to write jcr_if_<year>.json")
    ap.add_argument("--db", default="jcr_if_database.json", help="long database JSON to append into")
    ap.add_argument("--no-db", action="store_true", help="skip the database append")
    args = ap.parse_args()

    journals = load_journals(args.journals)
    names = [jcr_name(j) for j in journals]
    print(f"Journals: {len(journals)} | JCR year: {args.year}")
    print("Fetching from JCR API...")

    result = fetch_year(args.sid, names, args.year)
    if "data" not in result:
        sys.exit(f"ERROR: unexpected response: {result}")

    by_name = {item["abbrJournal"]: item for item in result["data"]}
    print(f"Retrieved: {len(by_name)} journals\n")

    detailed, compact, not_found = [], {}, []
    for j in journals:
        d = by_name.get(jcr_name(j))
        if not d:
            not_found.append({"abbr": j["abbr"], "tried": jcr_name(j)})
            continue
        detailed.append({
            "abbr": j["abbr"], "full": j["full"], "issn": j["issn"],
            "category_group": j["category_group"], "jcr_abbr": d["abbrJournal"],
            "jcr_year": d["jcrYear"], "IF": d[JIF_FIELD], "IF_5year": d.get("jif5Years", "N/A"),
            "IF_without_self": d.get("jifWithoutSelfCites", "N/A"), "quartile": d.get("quartile", "N/A"),
            "jif_rank": d.get("jifRank", ""), "jci": d.get("jci", "N/A"),
            "total_cites": d.get("totalCites", "N/A"), "eigenfactor": d.get("eigenFactor", "N/A"),
            "article_influence": d.get("articleInfluenceScore", "N/A"),
        })
        compact[d["abbrJournal"]] = {
            "IF": d[JIF_FIELD], "IF_5year": d.get("jif5Years", "N/A"),
            "quartile": d.get("quartile", "N/A"), "total_cites": d.get("totalCites", "N/A"),
            "jif_rank": d.get("jifRank", "N/A"),
        }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    detailed_path = outdir / f"jcr_if_{args.year}.json"
    detailed_path.write_text(json.dumps(
        {"year": args.year, "fetched_at": time.strftime("%Y-%m-%d %H:%M"), "journals": detailed},
        indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.no_db:
        db_path = Path(args.db)
        db = json.loads(db_path.read_text(encoding="utf-8")) if db_path.exists() else {}
        db[str(args.year)] = compact
        db_path.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"DB updated: {db_path} now has years {min(db)}..{max(db)} ({len(db)} total)")

    print(f"\n{'Journal':<34s} {'IF':>6s}  {'Q':>3s}  {'Rank':<12s}")
    print("-" * 62)
    for it in sorted(detailed, key=lambda x: float(x["IF"]) if x["IF"] not in ("N/A", None) else 0, reverse=True):
        print(f"{it['abbr']:<34s} {str(it['IF']):>6s}  {it['quartile']:>3s}  {it['jif_rank']:<12s}")

    if not_found:
        print(f"\n--- NOT FOUND ({len(not_found)}) ---")
        for nf in not_found:
            print(f"  {nf['abbr']} (tried: {nf['tried']})")
    print(f"\nSaved: {detailed_path}")
    print(f"Found: {len(detailed)}/{len(journals)}")


if __name__ == "__main__":
    main()
