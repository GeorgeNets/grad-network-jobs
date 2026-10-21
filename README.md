# Graduate network-engineering job finder (prototype)

Finds graduate, placement and entry-level networking roles in the UK, USA and Switzerland,
and ranks them by how well they fit your graduation year (default 2028).

## Setup
1. Register for a free key at https://developer.adzuna.com
2. Run:

    export ADZUNA_APP_ID=your_id
    export ADZUNA_APP_KEY=your_key
    python3 search.py --grad-year 2028 --countries gb us ch --pages 2

Output: `results.csv` (best matches first, UK before other countries) plus a short preview.
Offline check of the tagger: `python3 search.py --demo`. Tests: `python3 -m pytest test_tagger.py`.

## How "fit" works for class of 2028
- **match**: graduate role mentioning 2028, or a placement/internship dated 2027
- **check**: graduate or entry-level role with no year stated; open the listing and confirm the intake
- **too_early / too_late**: aimed at a different graduating class
- Experienced roles and non-networking roles are dropped.

Most graduate schemes for the class of 2028 open around autumn 2027, so right now
placements and internships for 2027 will be the strongest matches.

## Other flags
work pattern (hybrid/remote/on-site), clearance or nationality requirement, visa sponsorship.

## Notes
- Check that Adzuna supports each country code you use (gb, us, ch) in their docs.
- Always link to the original posting rather than copying listing text.
- Keyword rules are a first pass; add terms as you meet new wording.
