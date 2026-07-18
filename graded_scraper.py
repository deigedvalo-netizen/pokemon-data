#!/usr/bin/env python3
"""
PSA-graded price collector (free-tier watchlist).

Tracks the raw -> PSA 10 price jump for the most valuable cards in the DB
using the PokemonPriceTracker API (https://www.pokemonpricetracker.com).

Free tier budget: 100 credits/day, 60 calls/minute.
Costs: search/basic card = 1 credit per card returned,
       card + eBay graded data = 2 credits.
So one daily run tracks roughly 40-45 cards. The watchlist is the top-N cards
by latest raw TCGplayer market price (the only ones worth grading anyway).

Phases per run:
  1. Build watchlist: top --watchlist cards by latest tcgplayer market price.
  2. Resolve: for watchlist cards with no cached tcgPlayerId, search by
     "<name> <set> <number>" (1 credit each, capped by --resolve-cap).
  3. Fetch: for mapped cards, GET ?tcgPlayerId=X&includeEbay=true (2 credits)
     and store every grade found (psa10, psa9, ...) in graded_prices.
  4. Report: refresh the raw_vs_psa10 view (premium = psa10 / raw) and write
     graded-premiums.json for the site.

Env vars:
  PPT_API_KEY   Required. Free key from
                https://www.pokemonpricetracker.com/api-keys

Never raises on API weirdness: unparsed payloads are stored raw in
graded_prices.raw_json so no credit is ever wasted.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import date, datetime, timezone

import requests

API_BASE = "https://www.pokemonpricetracker.com/api/v2"

SCHEMA = """
CREATE TABLE IF NOT EXISTS ppt_map (
    card_id        TEXT PRIMARY KEY,      -- our pokemontcg.io id
    tcg_player_id  TEXT,                  -- PokemonPriceTracker / TCGplayer id
    matched_name   TEXT,
    matched_set    TEXT,
    resolved_at    TEXT,
    failed_tries   INTEGER DEFAULT 0      -- skip cards that repeatedly fail to match
);

CREATE TABLE IF NOT EXISTS graded_prices (
    card_id        TEXT,
    tcg_player_id  TEXT,
    captured_date  TEXT,   -- YYYY-MM-DD
    grader         TEXT,   -- 'PSA' | 'CGC' | 'BGS' | 'SGC'
    grade          TEXT,   -- '10', '9', ...
    sales_count    INTEGER,
    avg_price      REAL,
    median_price   REAL,
    smart_price    REAL,   -- their outlier-resistant market estimate, if given
    price_7day     REAL,
    trend          TEXT,
    raw_json       TEXT,   -- untouched payload for this grade (safety net)
    PRIMARY KEY (card_id, captured_date, grader, grade)
);
CREATE INDEX IF NOT EXISTS idx_graded_card ON graded_prices(card_id);
CREATE INDEX IF NOT EXISTS idx_graded_date ON graded_prices(captured_date);

CREATE TABLE IF NOT EXISTS graded_run_log (
    run_at         TEXT,
    captured_date  TEXT,
    resolved       INTEGER,
    fetched        INTEGER,
    credits_left   TEXT,
    ok             INTEGER,
    note           TEXT
);

-- Biggest raw -> PSA 10 jumps, latest data per card.
DROP VIEW IF EXISTS raw_vs_psa10;
CREATE VIEW raw_vs_psa10 AS
WITH latest_raw AS (
    SELECT ps.card_id, MAX(ps.market) AS raw_market
    FROM price_snapshots ps
    WHERE ps.source = 'tcgplayer'
      AND ps.captured_date = (SELECT MAX(captured_date) FROM price_snapshots
                              WHERE card_id = ps.card_id AND source = 'tcgplayer')
    GROUP BY ps.card_id
),
latest_psa10 AS (
    SELECT g.card_id, g.avg_price, g.median_price, g.smart_price, g.sales_count,
           g.captured_date
    FROM graded_prices g
    WHERE g.grader = 'PSA' AND g.grade = '10'
      AND g.captured_date = (SELECT MAX(captured_date) FROM graded_prices
                             WHERE card_id = g.card_id
                               AND grader = 'PSA' AND grade = '10')
)
SELECT c.id AS card_id, c.name, c.set_name, c.number, c.rarity,
       r.raw_market,
       COALESCE(p.smart_price, p.median_price, p.avg_price) AS psa10_price,
       p.sales_count AS psa10_sales,
       ROUND(COALESCE(p.smart_price, p.median_price, p.avg_price) / r.raw_market, 2)
           AS premium_ratio,
       p.captured_date AS psa10_date
FROM cards c
JOIN latest_raw r    ON r.card_id = c.id AND r.raw_market > 0
JOIN latest_psa10 p  ON p.card_id = c.id
WHERE COALESCE(p.smart_price, p.median_price, p.avg_price) > 0;
"""


# --------------------------------------------------------------------------- #
# API client with credit + rate-limit accounting
# --------------------------------------------------------------------------- #
class Client:
    def __init__(self, key, budget, base=API_BASE):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {key}"
        self.base = base
        self.budget = budget          # max credits to spend this run
        self.spent = 0
        self.daily_remaining = None   # per API headers, if present

    def can_spend(self, credits):
        if self.spent + credits > self.budget:
            return False
        if self.daily_remaining is not None and self.daily_remaining < credits:
            return False
        return True

    def get(self, path, params, est_credits):
        """One GET. Returns parsed json or None. Tracks credits from headers."""
        try:
            r = self.s.get(f"{self.base}{path}", params=params, timeout=60)
        except Exception as e:  # noqa: BLE001
            print(f"WARN: request failed ({type(e).__name__}: {e})", file=sys.stderr)
            return None
        # header names per their docs; fall back to estimate
        cost = _int_header(r, "X-RateLimit-Cost") or _int_header(r, "X-API-Calls-Consumed")
        self.spent += cost if cost is not None else est_credits
        rem = _int_header(r, "X-RateLimit-Daily-Remaining")
        if rem is not None:
            self.daily_remaining = rem
        if r.status_code == 429:
            print("WARN: rate/credit limit hit (429) — stopping spend", file=sys.stderr)
            self.budget = 0
            return None
        if r.status_code != 200:
            print(f"WARN: HTTP {r.status_code} on {path} {params}", file=sys.stderr)
            return None
        try:
            return r.json()
        except ValueError:
            return None


def _int_header(r, name):
    v = r.headers.get(name)
    if v is None:
        return None
    m = re.search(r"\d+", v)
    return int(m.group()) if m else None


# --------------------------------------------------------------------------- #
# Phase 1: watchlist
# --------------------------------------------------------------------------- #
def build_watchlist(conn, n, min_release="2020/01/01", min_raw=5.0, exploit_frac=0.6):
    """Modern cards only, split between:
    - EXPLOIT (~60%): biggest known raw->PSA10 jumps, re-tracked daily so the
      website's "biggest jump" chart stays current.
    - EXPLORE (~40%): candidates never sampled (or sampled longest ago),
      highest raw value first, to discover new jumpers. Rotates automatically.
    """
    base_cte = """
        WITH latest AS (
            SELECT card_id, MAX(market) AS m
            FROM price_snapshots
            WHERE source = 'tcgplayer'
              AND captured_date = (SELECT MAX(captured_date) FROM price_snapshots
                                   WHERE source = 'tcgplayer')
            GROUP BY card_id
        ),
        candidates AS (
            SELECT c.id, c.name, c.set_name, c.number, l.m
            FROM latest l JOIN cards c ON c.id = l.card_id
            WHERE l.m >= :min_raw
              AND c.set_release_date >= :min_release
        )
    """
    n_exploit = int(n * exploit_frac)
    exploit = conn.execute(
        base_cte + """
        SELECT cd.id, cd.name, cd.set_name, cd.number, cd.m
        FROM candidates cd
        JOIN raw_vs_psa10 v ON v.card_id = cd.id
        ORDER BY v.premium_ratio DESC
        LIMIT :k
        """,
        {"min_raw": min_raw, "min_release": min_release, "k": n_exploit},
    ).fetchall()
    picked = {r[0] for r in exploit}
    explore = conn.execute(
        base_cte + """
        SELECT cd.id, cd.name, cd.set_name, cd.number, cd.m
        FROM candidates cd
        LEFT JOIN (SELECT card_id, MAX(captured_date) AS last_g
                   FROM graded_prices GROUP BY card_id) g ON g.card_id = cd.id
        ORDER BY (g.last_g IS NOT NULL), g.last_g ASC, cd.m DESC
        LIMIT :k
        """,
        {"min_raw": min_raw, "min_release": min_release, "k": n},
    ).fetchall()
    out = list(exploit)
    for r in explore:
        if len(out) >= n:
            break
        if r[0] not in picked:
            out.append(r)
    return out


# --------------------------------------------------------------------------- #
# Phase 2: resolve card_id -> tcgPlayerId
# --------------------------------------------------------------------------- #
def resolve(conn, client, card, sleep):
    cid, name, set_name, number, _ = card
    q = f"{name} {set_name or ''} {number or ''}".strip()
    if not client.can_spend(1):
        return False
    data = client.get("/cards", {"search": q, "limit": 1}, est_credits=1)
    time.sleep(sleep)
    items = (data or {}).get("data") or []
    if not items:
        conn.execute(
            "INSERT INTO ppt_map (card_id, failed_tries) VALUES (?,1) "
            "ON CONFLICT(card_id) DO UPDATE SET failed_tries = failed_tries + 1",
            (cid,),
        )
        return False
    hit = items[0]
    tpid = hit.get("tcgPlayerId") or hit.get("tcgplayerId") or hit.get("id")
    conn.execute(
        "INSERT OR REPLACE INTO ppt_map "
        "(card_id, tcg_player_id, matched_name, matched_set, resolved_at, failed_tries) "
        "VALUES (?,?,?,?,?,0)",
        (cid, str(tpid) if tpid else None, hit.get("name"),
         (hit.get("set") or {}).get("name") if isinstance(hit.get("set"), dict) else hit.get("set"),
         datetime.now(timezone.utc).isoformat()),
    )
    return tpid is not None


# --------------------------------------------------------------------------- #
# Phase 3: fetch graded prices
# --------------------------------------------------------------------------- #
GRADE_KEY = re.compile(r"^(psa|cgc|bgs|sgc)[\s_-]?(\d{1,2}(?:\.5)?)$", re.I)

def parse_ebay_blob(ebay):
    """Yield (grader, grade, fields-dict, raw) from whatever shape they return."""
    if not isinstance(ebay, dict):
        return
    # shape A: {"psa10": {...}, "psa9": {...}}
    # shape B: {"PSA": {"10": {...}}} — handle both defensively
    for k, v in ebay.items():
        m = GRADE_KEY.match(str(k))
        if m and isinstance(v, dict):
            yield m.group(1).upper(), m.group(2), v, v
        elif str(k).upper() in ("PSA", "CGC", "BGS", "SGC") and isinstance(v, dict):
            for g, gv in v.items():
                if isinstance(gv, dict) and re.match(r"^\d{1,2}(\.5)?$", str(g)):
                    yield str(k).upper(), str(g), gv, gv

def num(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return v
    return None

def fetch_graded(conn, client, cid, tpid, today, sleep):
    if not client.can_spend(2):
        return 0
    data = client.get("/cards", {"tcgPlayerId": tpid, "includeEbay": "true"}, est_credits=2)
    time.sleep(sleep)
    items = (data or {}).get("data")
    if isinstance(items, list):
        items = items[0] if items else None
    if not isinstance(items, dict):
        return 0
    ebay = items.get("ebay") or items.get("ebayData") or {}
    n = 0
    for grader, grade, v, raw in parse_ebay_blob(ebay):
        conn.execute(
            """INSERT OR REPLACE INTO graded_prices
               (card_id, tcg_player_id, captured_date, grader, grade,
                sales_count, avg_price, median_price, smart_price, price_7day,
                trend, raw_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, str(tpid), today, grader, grade,
             num(v, "salesCount", "sales", "count"),
             num(v, "avg", "average", "averagePrice"),
             num(v, "median", "medianPrice"),
             num(v, "smartMarketPrice", "smartPrice"),
             num(v, "marketPrice7Day", "avg7"),
             str(v.get("marketTrend") or v.get("trend") or ""),
             json.dumps(raw)),
        )
        n += 1
    if n == 0 and ebay:
        # unknown shape — keep the raw payload so the credit isn't wasted
        conn.execute(
            """INSERT OR REPLACE INTO graded_prices
               (card_id, tcg_player_id, captured_date, grader, grade, raw_json)
               VALUES (?,?,?,'UNPARSED','-',?)""",
            (cid, str(tpid), today, json.dumps(ebay)),
        )
    return n


# --------------------------------------------------------------------------- #
# Phase 4: report
# --------------------------------------------------------------------------- #
def export_report(conn, path, limit=100):
    rows = conn.execute(
        """SELECT card_id, name, set_name, number, rarity, raw_market,
                  psa10_price, psa10_sales, premium_ratio, psa10_date
           FROM raw_vs_psa10 ORDER BY premium_ratio DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    cols = ["card_id", "name", "set_name", "number", "rarity", "raw_market",
            "psa10_price", "psa10_sales", "premium_ratio", "psa10_date"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"generated": datetime.now(timezone.utc).isoformat(),
                   "cards": [dict(zip(cols, r)) for r in rows]}, f, indent=1)
    return len(rows)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Collect PSA graded prices (watchlist).")
    ap.add_argument("--db", default="pokemon_prices.db")
    ap.add_argument("--watchlist", type=int, default=45, help="cards tracked per run")
    ap.add_argument("--min-release-date", default="2020/01/01",
                    help="modern-only cutoff (matches cards.set_release_date, YYYY/MM/DD)")
    ap.add_argument("--min-raw", type=float, default=5.0,
                    help="ignore cards under this raw market price")
    ap.add_argument("--exploit-frac", type=float, default=0.6,
                    help="share of watchlist reserved for known biggest jumpers")
    ap.add_argument("--budget", type=int, default=95, help="max credits this run")
    ap.add_argument("--resolve-cap", type=int, default=15, help="max ID-resolution credits/run")
    ap.add_argument("--sleep", type=float, default=1.1, help="seconds between calls (60/min limit)")
    ap.add_argument("--json", default="", help="write premium report to this path")
    ap.add_argument("--probe", default="", help="print raw API response for one tcgPlayerId and exit")
    ap.add_argument("--api-base", default=API_BASE, help=argparse.SUPPRESS)
    args = ap.parse_args()

    key = os.environ.get("PPT_API_KEY", "").strip()
    if not key:
        print("PPT_API_KEY not set — skipping graded collection (not an error).")
        return 0

    client = Client(key, args.budget, base=args.api_base)

    if args.probe:
        data = client.get("/cards", {"tcgPlayerId": args.probe, "includeEbay": "true"}, 2)
        print(json.dumps(data, indent=2)[:8000])
        return 0

    today = date.today().isoformat()
    conn = sqlite3.connect(args.db, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(SCHEMA)

    watch = build_watchlist(conn, args.watchlist, min_release=args.min_release_date,
                            min_raw=args.min_raw, exploit_frac=args.exploit_frac)
    print(f"Watchlist: {len(watch)} modern cards "
          f"(release >= {args.min_release_date}, raw >= ${args.min_raw})")

    # resolve missing mappings (skip cards that failed 3+ times)
    mapped = dict(conn.execute(
        "SELECT card_id, tcg_player_id FROM ppt_map WHERE tcg_player_id IS NOT NULL"))
    failed = dict(conn.execute(
        "SELECT card_id, failed_tries FROM ppt_map WHERE tcg_player_id IS NULL"))
    resolved = 0
    spent_before = client.spent
    for card in watch:
        cid = card[0]
        if cid in mapped or failed.get(cid, 0) >= 3:
            continue
        if client.spent - spent_before >= args.resolve_cap:
            break
        if resolve(conn, client, card, args.sleep):
            resolved += 1
    conn.commit()
    mapped = dict(conn.execute(
        "SELECT card_id, tcg_player_id FROM ppt_map WHERE tcg_player_id IS NOT NULL"))

    # fetch graded data for mapped watchlist cards
    fetched = 0
    for card in watch:
        cid = card[0]
        tpid = mapped.get(cid)
        if not tpid:
            continue
        if fetch_graded(conn, client, cid, tpid, today, args.sleep) > 0:
            fetched += 1
        conn.commit()
        if not client.can_spend(2):
            break

    note = ""
    ok = 1
    if fetched == 0 and resolved == 0:
        ok = 0
        note = "nothing resolved or fetched — check API key / credits"

    conn.execute(
        "INSERT INTO graded_run_log (run_at, captured_date, resolved, fetched, credits_left, ok, note) "
        "VALUES (?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), today, resolved, fetched,
         str(client.daily_remaining), ok, note),
    )
    conn.commit()

    if args.json:
        n = export_report(conn, args.json)
        print(f"Premium report: {n} cards -> {args.json}")

    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    print(f"Done. resolved={resolved} fetched={fetched} "
          f"credits_spent~{client.spent} daily_remaining={client.daily_remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
