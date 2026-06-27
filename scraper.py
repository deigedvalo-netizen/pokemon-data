#!/usr/bin/env python3
"""
Pokemon card price collector.

Pulls every card from the free Pokemon TCG API (pokemontcg.io / Scrydex) in
bulk (250 cards per request) and records a dated price snapshot for each card
from both TCGplayer and Cardmarket into a local SQLite database.

Design notes:
- This script uses ZERO LLM calls. It is plain HTTP + SQLite, so it is free to
  run forever on GitHub Actions, a free VM, or your own PC.
- One full snapshot of all ~20,000 cards is ~80 requests (250/page) and takes a
  couple of minutes -- nowhere near any rate limit.
- Re-running on the same day overwrites that day's row, so it is safe to run
  multiple times. Each (card, date, source, variant) is one row = a clean daily
  time series for charts and price prediction.

Env vars:
  POKEMONTCG_API_KEY   Optional. A free key from https://dev.pokemontcg.io
                       raises your rate limit. Works without one, just slower.
"""

import argparse
import os
import sqlite3
import sys
import time
from datetime import date, datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://api.pokemontcg.io/v2/cards"


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #
SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id                TEXT PRIMARY KEY,
    name              TEXT,
    supertype         TEXT,
    subtypes          TEXT,
    rarity            TEXT,
    set_id            TEXT,
    set_name          TEXT,
    set_series        TEXT,
    set_release_date  TEXT,
    number            TEXT,
    artist            TEXT,
    national_pokedex  TEXT,
    image_small       TEXT,
    image_large       TEXT,
    first_seen        TEXT,
    last_updated      TEXT
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    card_id        TEXT,
    captured_date  TEXT,   -- YYYY-MM-DD
    source         TEXT,   -- 'tcgplayer' | 'cardmarket' | historical tags
    variant        TEXT,   -- e.g. holofoil, normal, reverseHolofoil, or 'cardmarket'
    currency       TEXT,   -- 'USD' | 'EUR'
    low            REAL,
    mid            REAL,
    high           REAL,
    market         REAL,
    direct_low     REAL,
    avg1           REAL,
    avg7           REAL,
    avg30          REAL,
    PRIMARY KEY (card_id, captured_date, source, variant)
);

CREATE INDEX IF NOT EXISTS idx_snap_card ON price_snapshots(card_id);
CREATE INDEX IF NOT EXISTS idx_snap_date ON price_snapshots(captured_date);

-- Prioritized list for the Hermes backfill agent: every card with its latest
-- known TCGplayer market value (highest value = work on these first).
CREATE VIEW IF NOT EXISTS backfill_targets AS
SELECT c.id            AS card_id,
       c.name          AS name,
       c.set_name      AS set_name,
       c.rarity        AS rarity,
       MAX(ps.market)  AS latest_market,
       MAX(ps.captured_date) AS latest_date
FROM cards c
LEFT JOIN price_snapshots ps
       ON ps.card_id = c.id AND ps.source = 'tcgplayer'
GROUP BY c.id;

-- Log of every run so the supervisor can see collection health.
CREATE TABLE IF NOT EXISTS run_log (
    run_at         TEXT,
    captured_date  TEXT,
    cards_seen     INTEGER,
    snapshots      INTEGER,
    ok             INTEGER,
    note           TEXT
);
"""


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def make_session():
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    key = os.environ.get("POKEMONTCG_API_KEY", "").strip()
    if key:
        s.headers["X-Api-Key"] = key
    return s


def fetch_page(session, page, page_size, query):
    params = {"page": page, "pageSize": page_size}
    if query:
        params["q"] = query
    r = session.get(API_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def upsert_card(conn, c, today):
    conn.execute(
        """
        INSERT INTO cards (id, name, supertype, subtypes, rarity, set_id,
            set_name, set_series, set_release_date, number, artist,
            national_pokedex, image_small, image_large, first_seen, last_updated)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, rarity=excluded.rarity,
            image_small=excluded.image_small, image_large=excluded.image_large,
            last_updated=excluded.last_updated
        """,
        (
            c.get("id"),
            c.get("name"),
            c.get("supertype"),
            ",".join(c.get("subtypes", []) or []),
            c.get("rarity"),
            (c.get("set") or {}).get("id"),
            (c.get("set") or {}).get("name"),
            (c.get("set") or {}).get("series"),
            (c.get("set") or {}).get("releaseDate"),
            c.get("number"),
            c.get("artist"),
            ",".join(str(n) for n in (c.get("nationalPokedexNumbers") or [])),
            (c.get("images") or {}).get("small"),
            (c.get("images") or {}).get("large"),
            today,
            today,
        ),
    )


def snapshot_rows(c, today):
    """Yield one price_snapshots row tuple per variant/source for a card."""
    cid = c.get("id")

    # --- TCGplayer (USD), one entry per printing variant ---
    tcg = c.get("tcgplayer") or {}
    for variant, p in (tcg.get("prices") or {}).items():
        if not p:
            continue
        yield (
            cid, today, "tcgplayer", variant, "USD",
            p.get("low"), p.get("mid"), p.get("high"),
            p.get("market"), p.get("directLow"),
            None, None, None,
        )

    # --- Cardmarket (EUR), single aggregated entry ---
    cm = c.get("cardmarket") or {}
    p = cm.get("prices") or {}
    if p:
        yield (
            cid, today, "cardmarket", "cardmarket", "EUR",
            p.get("lowPrice"), p.get("averageSellPrice"), None,
            p.get("trendPrice"), None,
            p.get("avg1"), p.get("avg7"), p.get("avg30"),
        )


def save_snapshots(conn, rows):
    conn.executemany(
        """
        INSERT OR REPLACE INTO price_snapshots
        (card_id, captured_date, source, variant, currency,
         low, mid, high, market, direct_low, avg1, avg7, avg30)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Collect Pokemon card prices.")
    ap.add_argument("--db", default="pokemon_prices.db", help="SQLite file path")
    ap.add_argument("--page-size", type=int, default=250, help="cards per request (max 250)")
    ap.add_argument("--max-pages", type=int, default=0, help="0 = all pages (use a small number to test)")
    ap.add_argument("--query", default="", help='optional filter, e.g. "set.id:base1"')
    ap.add_argument("--sleep", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args()

    today = date.today().isoformat()
    conn = connect(args.db)
    session = make_session()

    cards_seen = 0
    snap_count = 0
    page = 1
    ok = True
    note = ""

    print(f"[{datetime.now().isoformat(timespec='seconds')}] Collecting prices for {today}")
    total = 0
    failed_pages = 0
    while True:
        try:
            data = fetch_page(session, page, args.page_size, args.query)
        except Exception as e:  # noqa: BLE001 — skip a bad page, don't abort the whole run
            failed_pages += 1
            print(f"WARN: page {page} failed after retries ({type(e).__name__}: {e}) — skipping", file=sys.stderr)
            if failed_pages >= 15:
                ok = False
                note = f"aborted after {failed_pages} failed pages"
                break
            page += 1
            time.sleep(2.0)
            if total and cards_seen >= total:
                break
            continue

        batch = data.get("data", [])
        total = data.get("totalCount", total)
        if not batch:
            break

        rows = []
        for c in batch:
            upsert_card(conn, c, today)
            rows.extend(snapshot_rows(c, today))
        save_snapshots(conn, rows)
        conn.commit()

        cards_seen += len(batch)
        snap_count += len(rows)
        print(f"  page {page}: +{len(batch)} cards ({cards_seen}/{total}), +{len(rows)} prices")

        if args.max_pages and page >= args.max_pages:
            break
        if total and cards_seen >= total:
            break
        page += 1
        time.sleep(args.sleep)

    # A few skipped pages is fine — keep what we collected. Only fail on zero data.
    if cards_seen == 0:
        ok = False
        note = note or "no cards collected"
    elif failed_pages:
        note = note or f"{failed_pages} pages skipped"

    conn.execute(
        "INSERT INTO run_log (run_at, captured_date, cards_seen, snapshots, ok, note) VALUES (?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), today, cards_seen, snap_count, 1 if ok else 0, note),
    )
    conn.commit()
    conn.close()

    print(f"Done. {cards_seen} cards, {snap_count} price rows for {today}. ok={ok}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
