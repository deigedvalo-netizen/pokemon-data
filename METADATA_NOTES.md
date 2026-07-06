# cards_metadata — how it works and what to double-check

New table `cards_metadata` (one row per card, key = `card_id`) lives in
`pokemon_prices.db` alongside `price_snapshots`. Join: `price_snapshots.card_id = cards_metadata.card_id`.
Already populated: 20,359 rows, zero join gaps as of 2026-07-04.

## Files

| File | Purpose |
|---|---|
| `build_metadata.py` | Weekly job. Creates/refreshes the table. `--from-local` = offline bootstrap from the `cards` table; default = live API (fills `in_print` too). `--validate-only` = just the join-gap report. |
| `species_normalizer.py` | Reusable `normalize_species(name, supertype)` — import it in your prediction code too. Running it directly regenerates `species_map.csv`. |
| `species_map.csv` | All 2,947 distinct Pokémon names → species, for manual audit. Fix mistakes by adding entries to `SPECIES_OVERRIDES` in `species_normalizer.py`. |
| `.github/workflows/metadata.yml` | Weekly GitHub Actions run (Sundays), same commit flow as the daily scraper. |

## Column types (for the prediction pipeline)

- `set_release_date` — ISO `YYYY-MM-DD` text with DATE affinity; SQLite date functions work on it (`WHERE set_release_date >= date('2024-01-01')` verified).
- `in_print`, `reprint_flag` — INTEGER 0/1 with CHECK constraints (2 or 'yes' is rejected). In pandas: `df['in_print'].astype('boolean')`.
- `popularity_tier` — CHECK constraint allows only S/A/B/C or NULL.
- `card_number` stays TEXT on purpose: numbers like `181a`, `SV49`, `TG12` aren't integers.
- `last_updated` — UTC ISO timestamp, refreshed whenever API fields are re-synced. If it's >30 days old, `validate()` warns you; treat `in_print`/`reprint_flag` from stale rows with suspicion.

Manual columns (`popularity_tier`, `reprint_flag`, `competitive_relevance`) are **never
touched by re-runs** — verified by test: filled values survived both `--from-local` and
API-mode upserts.

## in_print — derived, not native

The API has **no** "still being printed" flag. Rule used:
`in_print = 1 iff set.legalities.standard == 'Legal'`.
Standard rotation is the best machine-readable proxy, but it's imperfect:
special products (McDonald's promos, Celebrations-style reprints) can be
out of print while standard-legal, and evergreen products can outlive rotation.
Treat it as "current-era card", and use your manual `reprint_flag` for the
supply-side signal the model actually cares about.
`--from-local` can't compute it (no legalities in the `cards` table), so it stays
NULL until the first API run and is never overwritten with NULL afterwards.

## API inconsistencies found in YOUR data — verify before modeling

1. **Rarity naming drift across eras** — same concept, different strings.
   If rarity is a model feature, map these to canonical buckets first:
   - `Rare Ultra` (798) vs `Ultra Rare` (338)
   - `Rare Shiny` (149) vs `Shiny Rare` (120)
   - `Rare Rainbow` (324) vs `Hyper Rare` (74) — same slot, pre/post-SV naming
   - `Rare Secret` (325) overlaps both of the above conceptually
   - `MEGA_ATTACK_RARE` (7) — raw enum leak, clearly unclean; vs `Mega Hyper Rare` (7)
   - `Black White Rare` (2) — new 2025+ naming, watch for more drift in new sets
2. **303 cards have NULL rarity** — mostly promo/side sets (Kalos Starter Set,
   McDonald's Collections, Southern Islands, Pokémon Rumble). Decide a fill-in
   (e.g. 'Promo') before using rarity as a feature.
3. **`ptcgoCode` is dead** — missing for every Scarlet & Violet-era set, so
   `set_code` uses the API set id (`sv1`, `base1`), which is always present and
   is the prefix of `card_id`.
4. **666 cards have metadata but no price rows** — the API returns no
   TCGplayer/Cardmarket prices for them. Expected; excluded via the join.
5. **Species edge cases** — deliberate choices, flip flags in `species_normalizer.py` to change:
   - Regional forms kept distinct (`Alolan Vulpix` ≠ `Vulpix`) — the market prices them differently.
   - Tag Teams keep the pair (`Reshiram & Charizard`) — their prices behave like their own product.
   - Skim `species_map.csv` once; add any misses to `SPECIES_OVERRIDES`.

## Scheduling

Runs Sundays 14:07 UTC via `metadata.yml`, fully independent of the daily scrape
(shares the `scrape` concurrency group so the two never write the DB simultaneously).
Note: your local folder isn't a git clone — after adding these files to the repo,
`sync_db` pulls the metadata down with the DB as usual. Local `--from-local` runs
are fine for testing but will be overwritten by the next sync.
