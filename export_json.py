#!/usr/bin/env python3
"""
Export pokemon_prices.db into the website's .price-data.json format.

Output shape (matches pokevault/lib/serverHistory.ts):
  { "<cardId>": { "Near Mint": [ {"date": "YYYY-MM-DD", "price": 12.34}, ... ],
                  "CardMarket (EU)": [ ... ] }, ... }

Run in the GitHub Actions workflow right after scraper.py, then commit the file.
The website fetches this public JSON and merges it into its local data.
"""
import json
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "pokemon_prices.db"
out_path = sys.argv[2] if len(sys.argv) > 2 else "price-data.json"

conn = sqlite3.connect(db_path)
data: dict = {}

# Near Mint = TCGplayer market price (highest-value variant per card/day), USD.
for cid, date, price in conn.execute(
    """
    SELECT card_id, captured_date, MAX(market)
    FROM price_snapshots
    WHERE source = 'tcgplayer' AND market IS NOT NULL
    GROUP BY card_id, captured_date
    ORDER BY card_id, captured_date
    """
):
    data.setdefault(cid, {}).setdefault("Near Mint", []).append(
        {"date": date, "price": round(price, 2)}
    )

# CardMarket (EU) = Cardmarket trend price, EUR — kept as a separate stream.
for cid, date, price in conn.execute(
    """
    SELECT card_id, captured_date, market
    FROM price_snapshots
    WHERE source = 'cardmarket' AND market IS NOT NULL
    ORDER BY card_id, captured_date
    """
):
    data.setdefault(cid, {}).setdefault("CardMarket (EU)", []).append(
        {"date": date, "price": round(price, 2)}
    )

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f)

conn.close()
print(f"Exported {len(data)} cards to {out_path}")
