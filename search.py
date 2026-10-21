"""Graduate network-engineering job search using the Adzuna API.

Usage:
  export ADZUNA_APP_ID=...   ADZUNA_APP_KEY=...
  python search.py --grad-year 2028 --countries gb us ch --pages 2

  python search.py --demo     # offline: runs the tagger on built-in examples

Writes results.csv, sorted so the best matches for your graduation year come first.
Always link back to the original posting (the 'url' column) rather than copying listings.
"""
import argparse, csv, json, os, sys, time
import urllib.parse, urllib.request

from tagger import classify

QUERIES = [
    "graduate network engineer",
    "graduate network security",
    "graduate infrastructure engineer",
    "network engineering placement",
    "network engineering internship",
    "early careers network",
]
# Adzuna country codes. Verify against Adzuna's docs that your target countries are supported.
COUNTRIES = {"gb": "UK", "us": "USA", "ch": "Switzerland"}
FIT_ORDER = {"match": 0, "check": 1, "too_early": 2, "too_late": 3, "not_relevant": 4}


def fetch(country, query, page, app_id, app_key):
    params = urllib.parse.urlencode({
        "app_id": app_id, "app_key": app_key, "results_per_page": 50,
        "what": query, "content-type": "application/json",
    })
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?{params}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r).get("results", [])


def run(args):
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        sys.exit("Set ADZUNA_APP_ID and ADZUNA_APP_KEY (free key from developer.adzuna.com).")
    seen, rows = set(), []
    for c in args.countries:
        for q in QUERIES:
            for p in range(1, args.pages + 1):
                try:
                    results = fetch(c, q, p, app_id, app_key)
                except Exception as e:
                    print(f"[{c}] '{q}' page {p}: {e}", file=sys.stderr)
                    break
                if not results:
                    break
                for j in results:
                    key = j.get("redirect_url") or j.get("id")
                    if key in seen:
                        continue
                    seen.add(key)
                    t = classify(j.get("title", ""), j.get("description", ""), args.grad_year)
                    if t.fit == "not_relevant":
                        continue
                    rows.append({
                        "fit": t.fit, "why": t.fit_reason, "title": t.title,
                        "company": (j.get("company") or {}).get("display_name", ""),
                        "location": (j.get("location") or {}).get("display_name", ""),
                        "country": COUNTRIES.get(c, c), "kind": t.kind,
                        "work_pattern": t.work_pattern,
                        "clearance_or_nationality": t.clearance_or_nationality,
                        "visa": t.visa, "posted": j.get("created", "")[:10],
                        "url": j.get("redirect_url", ""),
                    })
                time.sleep(0.5)  # be polite to the API
    rows.sort(key=lambda r: (FIT_ORDER[r["fit"]], r["country"] != "UK", r["posted"]), reverse=False)
    if not rows:
        print("No results."); return
    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"Saved {len(rows)} listings to results.csv")
    for r in rows[:15]:
        print(f"[{r['fit']:<9}] {r['country']:<11} {r['title'][:55]:<55} {r['company'][:25]}")


DEMO = [
    ("Graduate Digital Intelligence Network Engineer (Group DI)",
     "Location: UK Flex - Christchurch/Yeovil. We offer a range of hybrid and flexible working "
     "arrangements, however for this role you will be expected to attend your site 3-5 days per week."),
    ("Network Production Engineer (University Grad) Meta", ""),
]


def demo(grad_year):
    for title, desc in DEMO:
        t = classify(title, desc, grad_year)
        print(json.dumps(t.as_dict(), indent=2), "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grad-year", type=int, default=2028)
    ap.add_argument("--countries", nargs="+", default=["gb", "us", "ch"])
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    demo(a.grad_year) if a.demo else run(a)
