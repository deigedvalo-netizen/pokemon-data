#!/usr/bin/env python3
"""
Weekly cards_metadata builder — companion to the daily scraper.py.

Builds/refreshes a `cards_metadata` table (one row per unique card, keyed by
the API's native card id) in the same SQLite DB as price_snapshots, so the two
join directly on card_id.

Guarantees:
  - Manual columns (popularity_tier, reprint_flag, competitive_relevance) are
    NEVER touched on re-run. Only API-sourced columns + last_updated refresh.
  - set_release_date stored as ISO date (YYYY-MM-DD), booleans as 0/1 INTEGER
    with CHECK constraints — clean types for a downstream model.
  - Validation reports card_ids in price_snapshots missing from metadata and
    vice versa, plus data-quality flags (NULL rarity, etc.).

in_print: the API has NO direct "still being printed" flag. Derived here as:
    in_print = 1 if set.legalities.standard == 'Legal' else 0
Standard legality tracks the official rotation and is the closest machine-
readable proxy for "current product". Caveats in METADATA_NOTES.md.

Usage:
    python build_metadata.py --db pokemon_prices.db            # full weekly run
    python build_metadata.py --db pokemon_prices.db --validate-only
    python build_metadata.py --db pokemon_prices.db --max-pages 2   # smoke test

Env: POKEMONTCG_API_KEY (optional, raises rate limit)
"""

import argparse
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from species_normalizer import normalize_species

API_URL = "https://api.pokemontcg.io/v2/cards"
# Trimmed payload: only the fields this job needs (much faster than full cards).
SELECT_FIELDS = "id,name,supertype,number,rarity,set"

MANUAL_COLUMNS = ("popularity_tier", "reprint_flag", "competitive_relevance")

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards_metadata (
    card_id                TEXT PRIMARY KEY,       -- API native id; joins price_snapshots.card_id
    card_name              TEXT NOT NULL,
    set_name               TEXT,
    set_code               TEXT,                   -- API set id (e.g. 'sv1'); always present, prefix of card_id.
                                                   -- (ptcgoCode not used: missing for all SV-era sets)
    card_number            TEXT,                   -- TEXT on purpose: numbers like '181a', 'SV49'
    rarity                 TEXT,                   -- API-native naming, unmodified
    species                TEXT,                   -- normalized; NULL for Trainer/Energy
    set_release_date       DATE,                   -- ISO YYYY-MM-DD
    in_print               BOOLEAN CHECK (in_print IN (0, 1)),
    -- ---- manual fields: filled by hand, never overwritten by this job ----
    popularity_tier        TEXT CHECK (popularity_tier IN ('S','A','B','C') OR popularity_tier IS NULL),
    reprint_flag           BOOLEAN CHECK (reprint_flag IN (0, 1) OR reprint_flag IS NULL),
    competitive_relevance  TEXT,
    -- ---------------------------------------------------------------------
    last_updated           TIMESTAMP               -- UTC ISO; when API fields were last refreshed
);
CREATE INDEX IF NOT EXISTS idx_meta_species ON cards_metadata(species);
CREATE INDEX IF NOT EXISTS idx_meta_set ON cards_metadata(set_code);
"""

UPSERT = """
INSERT INTO cards_metadata
    (card_id, card_name, set_name, set_code, card_number, rarity, species,
     set_release_date, in_print, last_updated)
VALUES (?,?,?,?,?,?,?,?,?,?)
ON CONFLICT(card_id) DO UPDATE SET
    card_name        = excluded.card_name,
    set_name         = excluded.set_name,
    set_code         = excluded.set_code,
    card_number      = excluded.card_number,
    rarity           = excluded.rarity,
    species          = excluded.species,
    set_release_date = excluded.set_release_date,
    in_print         = excluded.in_print,
    last_updated     = excluded.last_updated
"""  # manual columns intentionally absent -> preserved on every re-run

# Local-mode upsert: also leaves in_print untouched (cards table has no
# legalities, so local mode must not clobber an API-derived in_print with NULL).
UPSERT_LOCAL = UPSERT.replace("in_print         = excluded.in_print,\n    ", "")


def make_session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(
        total=5, backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))))
    key = os.environ.get("POKEMONTCG_API_KEY", "").strip()
    if key:
        s.headers["X-Api-Key"] = key
    return s


def to_iso_date(api_date):
    """API dates are 'YYYY/MM/DD' -> 'YYYY-MM-DD' (or None)."""
    if not api_date:
        return None
    return api_date.replace("/", "-")


def rarity_or_default(rarity, supertype):
    """The API leaves rarity NULL for basic Energies and fixed-product sets
    (McDonald's, Trainer Kits, Southern Islands...). Fill deterministically so
    the table has no holes: Energy -> 'Common', anything else -> 'Promo'."""
    if rarity:
        return rarity
    return "Common" if supertype == "Energy" else "Promo"


def card_row(c, now_iso):
    st = c.get("set") or {}
    legal = (st.get("legalities") or {})
    return (
        c["id"],
        c.get("name"),
        st.get("name"),
        st.get("id"),
        c.get("number"),
        rarity_or_default(c.get("rarity"), c.get("supertype")),
        normalize_species(c.get("name"), c.get("supertype")),
        to_iso_date(st.get("releaseDate")),
        1 if legal.get("standard") == "Legal" else 0,
        now_iso,
    )


def sync_from_local(conn):
    """Bootstrap/refresh metadata from the local `cards` table (daily scraper's
    output) — no network. Everything except in_print, which needs the API's
    set legalities and is left NULL until the next online run."""
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for cid, name, supertype, rarity, set_id, set_name, rel, num in conn.execute(
        "SELECT id, name, supertype, rarity, set_id, set_name, set_release_date, number FROM cards"
    ):
        rows.append((cid, name, set_name, set_id, num,
                     rarity_or_default(rarity, supertype),
                     normalize_species(name, supertype), to_iso_date(rel), None, now_iso))
    conn.executemany(UPSERT_LOCAL, rows)
    conn.commit()
    return len(rows)


def sync(conn, args):
    session = make_session()
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def fetch(p):
        r = session.get(API_URL, params={
            "page": p, "pageSize": args.page_size, "select": SELECT_FIELDS,
        }, timeout=60)
        r.raise_for_status()
        return r.json()

    def store(batch):
        conn.executemany(UPSERT, [card_row(c, now_iso) for c in batch])
        conn.commit()

    # Same fault tolerance as scraper.py: a flaky page is skipped, not fatal,
    # and skipped pages get one more attempt at the end of the run.
    page, seen, total = 1, 0, 0
    skipped = []
    while True:
        try:
            data = fetch(page)
        except Exception as e:  # noqa: BLE001
            skipped.append(page)
            print(f"WARN: page {page} failed after retries ({type(e).__name__}: {e}) — skipping",
                  file=sys.stderr)
            if len(skipped) >= 15:
                print("Too many failed pages — API is down; keeping what we have.", file=sys.stderr)
                break
            page += 1
            time.sleep(2.0)
            if total and seen >= total:
                break
            continue
        batch = data.get("data", [])
        total = data.get("totalCount", total)
        if not batch:
            break
        store(batch)
        seen += len(batch)
        print(f"  page {page}: {seen}/{total}")
        if (args.max_pages and page >= args.max_pages) or (total and seen >= total):
            break
        page += 1
        time.sleep(args.sleep)

    if skipped and len(skipped) < 15:
        print(f"Retrying {len(skipped)} skipped page(s): {skipped}")
        for p in skipped:
            time.sleep(3.0)
            try:
                batch = fetch(p).get("data", [])
            except Exception as e:  # noqa: BLE001
                print(f"WARN: page {p} failed again ({type(e).__name__}: {e})", file=sys.stderr)
                continue
            store(batch)
            seen += len(batch)
            print(f"  retry page {p}: recovered {len(batch)} cards")
    return seen


def validate(conn):
    """Join-gap + data-quality report. Returns count of hard problems."""
    problems = 0

    orphan_prices = conn.execute("""
        SELECT COUNT(DISTINCT ps.card_id) FROM price_snapshots ps
        LEFT JOIN cards_metadata m ON m.card_id = ps.card_id
        WHERE m.card_id IS NULL""").fetchone()[0]
    if orphan_prices:
        problems += orphan_prices
        print(f"PROBLEM: {orphan_prices} card_ids have prices but NO metadata row (join gap!). Sample:")
        for (cid,) in conn.execute("""
            SELECT DISTINCT ps.card_id FROM price_snapshots ps
            LEFT JOIN cards_metadata m ON m.card_id = ps.card_id
            WHERE m.card_id IS NULL LIMIT 10"""):
            print(f"    {cid}")
    else:
        print("OK: every priced card_id has a metadata row.")

    meta_no_price = conn.execute("""
        SELECT COUNT(*) FROM cards_metadata m
        LEFT JOIN (SELECT DISTINCT card_id FROM price_snapshots) p ON p.card_id = m.card_id
        WHERE p.card_id IS NULL""").fetchone()[0]
    print(f"INFO: {meta_no_price} metadata rows have no price snapshots yet "
          f"(normal — the API returns no market prices for some cards).")

    null_rarity = conn.execute(
        "SELECT COUNT(*) FROM cards_metadata WHERE rarity IS NULL").fetchone()[0]
    if null_rarity:
        print(f"WARN: {null_rarity} cards have NULL rarity (mostly old promo/basic-energy sets) — "
              f"decide a fill-in value before modeling on rarity.")

    null_species = conn.execute("""
        SELECT COUNT(*) FROM cards_metadata
        WHERE species IS NULL AND card_name IS NOT NULL
          AND card_id IN (SELECT id FROM cards WHERE supertype='Pokémon')""").fetchone()[0]
    if null_species:
        print(f"WARN: {null_species} Pokémon cards got NULL species — check species_normalizer.")

    stale = conn.execute("""
        SELECT COUNT(*) FROM cards_metadata
        WHERE last_updated < datetime('now', '-30 days')""").fetchone()[0]
    if stale:
        print(f"WARN: {stale} rows not refreshed in 30+ days.")

    return problems


def main():
    ap = argparse.ArgumentParser(description="Build/refresh cards_metadata.")
    ap.add_argument("--db", default="pokemon_prices.db")
    ap.add_argument("--page-size", type=int, default=250)
    ap.add_argument("--max-pages", type=int, default=0, help="0 = all (small number to test)")
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--from-local", action="store_true",
                    help="build from the local cards table instead of the API "
                         "(no network; in_print left NULL)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(SCHEMA)

    if not args.validate_only:
        seen = sync_from_local(conn) if args.from_local else sync(conn, args)
        print(f"Synced {seen} cards{' (from local cards table)' if args.from_local else ''}.")

    problems = validate(conn)
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
