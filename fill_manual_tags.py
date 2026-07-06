#!/usr/bin/env python3
"""
Seeds the "manual" columns of cards_metadata with defensible, data-driven
defaults. Safe by design: only ever fills NULLs — anything you've set by hand
is never overwritten (use --retier to force tier recompute).

What it fills:
  popularity_tier        S/A/B/C from latest market price in YOUR price data:
                           S >= $200   (~530 cards, top ~3%)
                           A $50-200   B $10-50   C < $10 or unpriced
  competitive_relevance  'meta-core YYYY-MM' / 'meta-support YYYY-MM' for cards
                         in the current Standard tournament meta (METB list
                         below — update it when the meta shifts; source:
                         justinbasil.com/guide/meta + limitlesstcg.com/decks).
                         Matches by card_name, so every printing of a meta card
                         is tagged (any printing is tournament-legal).

  reprint_flag           Defaults NULL -> 0 ('no known reprint' — true for the
                         vast majority). No honest auto-rule for detecting real
                         reprints exists (same name != same card), so flip the
                         exceptions to 1 by hand; --shortlist writes the
                         top-value cards as a review worksheet. Your edits are
                         permanent (script only ever touches NULLs).

Usage:
  python fill_manual_tags.py --db pokemon_prices.db              # fill NULLs
  python fill_manual_tags.py --db pokemon_prices.db --retier     # recompute all tiers
  python fill_manual_tags.py --db pokemon_prices.db --shortlist reprint_check.csv
"""

import argparse
import csv
import sqlite3
from datetime import date

TIER_CUTOFFS = [(200.0, "S"), (50.0, "A"), (10.0, "B")]  # else "C"

# Standard meta, July 2026. Deck cores vs support/tech staples.
META_CORE = [
    "Marnie's Grimmsnarl ex", "Raging Bolt ex", "Dragapult ex", "Gardevoir ex",
    "Charizard ex", "Gholdengo ex", "Miraidon ex", "Pikachu ex", "Terapagos ex",
    "Archaludon ex", "N's Zoroark ex", "Crustle", "Ethan's Ho-Oh ex",
    "Cynthia's Garchomp ex", "Ceruledge ex", "Umbreon ex",
]
META_SUPPORT = [
    "Froslass", "Munkidori", "Fezandipiti ex", "Pidgeot ex",
    "Lillie's Clefairy ex", "Maractus", "Joltik", "Galvantula",
    "Dusknoir", "Dusclops", "Duskull", "Kirlia", "Genesect ex", "Lunatone",
    "Teal Mask Ogerpon ex", "Wellspring Mask Ogerpon ex",
    "Hearthflame Mask Ogerpon ex", "Cornerstone Mask Ogerpon ex",
    "Jellicent ex", "Mega Diancie ex",
]

LATEST_VALUE_SQL = """
WITH latest_date AS (SELECT MAX(captured_date) d FROM price_snapshots),
tcg AS (SELECT card_id, MAX(COALESCE(market, mid, low)) mkt
        FROM price_snapshots, latest_date
        WHERE source='tcgplayer' AND captured_date=d GROUP BY card_id),
cm  AS (SELECT card_id, MAX(COALESCE(market, mid, low)) mkt
        FROM price_snapshots, latest_date
        WHERE source='cardmarket' AND captured_date=d GROUP BY card_id)
SELECT m.card_id, COALESCE(tcg.mkt, cm.mkt * 1.1) AS value
FROM cards_metadata m
LEFT JOIN tcg ON tcg.card_id = m.card_id
LEFT JOIN cm  ON cm.card_id  = m.card_id
"""


def tier_for(value):
    if value is None:
        return "C"
    for cutoff, tier in TIER_CUTOFFS:
        if value >= cutoff:
            return tier
    return "C"


def main():
    ap = argparse.ArgumentParser(description="Seed manual metadata columns.")
    ap.add_argument("--db", default="pokemon_prices.db")
    ap.add_argument("--retier", action="store_true",
                    help="recompute popularity_tier for ALL rows (overwrites)")
    ap.add_argument("--shortlist", metavar="CSV",
                    help="write top-value cards to CSV for manual reprint_flag review")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")

    # ---- popularity_tier ----
    values = dict(conn.execute(LATEST_VALUE_SQL).fetchall())
    where = "" if args.retier else "AND popularity_tier IS NULL"
    updated = 0
    for cid, val in values.items():
        cur = conn.execute(
            f"UPDATE cards_metadata SET popularity_tier=? WHERE card_id=? {where}",
            (tier_for(val), cid))
        updated += cur.rowcount
    print(f"popularity_tier: set {updated} rows "
          f"({'all recomputed' if args.retier else 'NULLs only'})")

    # ---- competitive_relevance ----
    stamp = date.today().strftime("%Y-%m")
    comp = 0
    for names, label in ((META_CORE, "meta-core"), (META_SUPPORT, "meta-support")):
        for name in names:
            # Refreshable: overwrites NULL, 'none', and old meta-* stamps —
            # but never custom text you wrote yourself.
            cur = conn.execute(
                """UPDATE cards_metadata SET competitive_relevance=?
                   WHERE card_name=? AND (competitive_relevance IS NULL
                         OR competitive_relevance='none'
                         OR competitive_relevance LIKE 'meta-%')""",
                (f"{label} {stamp}", name))
            comp += cur.rowcount
    print(f"competitive_relevance: tagged {comp} meta rows")

    # No holes: everything not in the meta is explicitly 'none'.
    n = conn.execute("""UPDATE cards_metadata SET competitive_relevance='none'
                        WHERE competitive_relevance IS NULL""").rowcount
    print(f"competitive_relevance: {n} non-meta rows set to 'none'")

    # reprint_flag default: 0 = 'no known reprint' (true for the vast majority).
    # Flip to 1 by hand for known reprints — this only touches NULLs, so your
    # 1s (and deliberate 0s) are permanent.
    n = conn.execute("""UPDATE cards_metadata SET reprint_flag=0
                        WHERE reprint_flag IS NULL""").rowcount
    print(f"reprint_flag: defaulted {n} NULL rows to 0 (no known reprint)")

    # ---- reprint worksheet ----
    if args.shortlist:
        rows = conn.execute("""
            SELECT m.card_id, m.card_name, m.set_name, m.set_release_date,
                   m.rarity, ROUND(v.value, 2), m.reprint_flag
            FROM cards_metadata m
            JOIN (""" + LATEST_VALUE_SQL + """) v ON v.card_id = m.card_id
            WHERE v.value IS NOT NULL
            ORDER BY v.value DESC LIMIT 300""").fetchall()
        with open(args.shortlist, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["card_id", "card_name", "set_name", "released",
                        "rarity", "market_usd", "reprint_flag (fill 0/1)"])
            w.writerows(rows)
        print(f"shortlist: wrote top {len(rows)} cards to {args.shortlist}")

    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()


if __name__ == "__main__":
    main()
