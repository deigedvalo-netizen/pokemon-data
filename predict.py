#!/usr/bin/env python3
"""
7-day price-move prediction engine (v1).

Predicts the % change in TCGplayer market price over the next 7 days for
every S- and A-tier card (>= $50), using only data already in
pokemon_prices.db. Designed to run daily in GitHub Actions right after the
scraper, writing predictions.json for the website.

v1 is deliberately simple and HONEST about uncertainty:
  - Three baseline models: naive (no change), momentum (recent trend
    continues, damped), and mean-reversion (price drifts back toward its
    Cardmarket 30-day average).
  - A blended model that weights them; weights are chosen by the backtest
    when enough history exists, otherwise sensible defaults.
  - Every prediction ships with a confidence field that is LOW while the
    dataset is young. Do not present these as strong signals yet — the
    real ML model (gradient boosting) replaces the blend once ~60+ days
    of history exist. The backtest harness is how we'll prove it's better.

Usage:
  python predict.py --db pokemon_prices.db --predict --json predictions.json
  python predict.py --db pokemon_prices.db --backtest
"""

import argparse
import json
import math
import sqlite3
import statistics
from datetime import date, datetime, timedelta

HORIZON_DAYS = 7
EUR_USD = 1.10          # rough constant; refine when FX matters
MIN_PRICE = 50.0        # S+A tier scope: cards worth >= $50
DAMP_MOMENTUM = 0.35    # momentum carries ~1/3 of past week into next week
REVERT_WEIGHT = 0.30    # how strongly price pulls back to 30d anchor


# --------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------- #
def load_series(conn):
    """Per card: sorted [(date, usd_value)] using the card's primary variant
    (the variant with the highest average market value — the printing people
    actually chart).

    IMPORTANT: the value FIELD (market / mid / low) is chosen ONCE per card —
    market if the card has market data on most days, else mid, else low.
    Mixing fields day-to-day fabricates phantom price jumps (backtest caught
    a +568% 'move' that was just market->mid switching on a thin card)."""
    rows = conn.execute("""
        WITH v AS (
            SELECT card_id, variant, AVG(COALESCE(market, mid, low)) av
            FROM price_snapshots WHERE source='tcgplayer'
            GROUP BY card_id, variant
        ),
        primary_v AS (
            SELECT card_id, variant FROM v
            WHERE (card_id, av) IN (SELECT card_id, MAX(av) FROM v GROUP BY card_id)
        )
        SELECT ps.card_id, ps.captured_date, ps.market, ps.mid, ps.low
        FROM price_snapshots ps
        JOIN primary_v pv ON pv.card_id = ps.card_id AND pv.variant = ps.variant
        WHERE ps.source='tcgplayer'
        ORDER BY ps.card_id, ps.captured_date""").fetchall()
    raw = {}
    for cid, d, mkt, mid, low in rows:
        raw.setdefault(cid, []).append((d, (mkt, mid, low)))
    series = {}
    for cid, pts in raw.items():
        for i in range(3):                      # 0=market, 1=mid, 2=low
            s = [(d, v[i]) for d, v in pts if v[i] is not None]
            if len(s) >= max(2, int(0.6 * len(pts))):
                series[cid] = s
                break
    return series


def load_cardmarket_anchors(conn, as_of):
    """Cardmarket avg1/avg7/avg30 (EUR->USD) per card, latest row on/before
    as_of. avg30 reaches ~30 days further back than our own history —
    it's the closest thing we have to long memory right now."""
    rows = conn.execute("""
        SELECT card_id, avg1, avg7, avg30 FROM price_snapshots
        WHERE source='cardmarket' AND captured_date =
              (SELECT MAX(captured_date) FROM price_snapshots
               WHERE source='cardmarket' AND captured_date <= ?)""",
        (as_of,)).fetchall()
    return {cid: (a1 and a1 * EUR_USD, a7 and a7 * EUR_USD, a30 and a30 * EUR_USD)
            for cid, a1, a7, a30 in rows}


def load_metadata(conn):
    return {cid: (tier, in_print, comp) for cid, tier, in_print, comp in conn.execute(
        "SELECT card_id, popularity_tier, in_print, competitive_relevance FROM cards_metadata")}


# --------------------------------------------------------------------- #
# Models — each takes the history UP TO a day and predicts % move over
# the next HORIZON_DAYS. Returning None means "not enough data".
# --------------------------------------------------------------------- #
def pts_upto(series, as_of):
    return [(d, v) for d, v in series if d <= as_of]


def pct(a, b):
    return (a - b) / b * 100.0 if b else None


def model_naive(pts, anchors):
    return 0.0


def model_momentum(pts, anchors):
    """Past week's move, damped, projected onto next week."""
    if len(pts) < 2:
        return None
    last_d, last_v = pts[-1]
    week_ago = (datetime.strptime(last_d, "%Y-%m-%d") - timedelta(days=HORIZON_DAYS)).strftime("%Y-%m-%d")
    base = None
    for d, v in pts:
        if d >= week_ago:
            base = v
            break
    if base is None or base == 0:
        return None
    return pct(last_v, base) * DAMP_MOMENTUM


def model_reversion(pts, anchors):
    """If price sits above/below its Cardmarket 30d average, expect a pull
    back toward it (classic for collectibles after hype spikes)."""
    if not pts or not anchors:
        return None
    _, last_v = pts[-1]
    a30 = anchors[2]
    if not a30 or last_v == 0:
        return None
    gap_pct = pct(a30, last_v)          # positive => price below anchor
    # Backtest lesson: Cardmarket (EU) diverges structurally from TCGplayer
    # on many cards — only trust the anchor when the two roughly agree,
    # and never let this model claim a big move on its own.
    if gap_pct is None or abs(gap_pct) > 25:
        return None
    return max(-10.0, min(10.0, gap_pct * REVERT_WEIGHT))


def model_blend(pts, anchors, weights=(0.45, 0.55, 0.0)):
    """Weights reflect backtest evidence (2026-07): momentum slightly beats
    naive; reversion LOSES to both even restricted (Cardmarket EU prices
    diverge structurally from TCGplayer) so it gets 0 weight until the
    backtest proves otherwise. Re-run --backtest monthly and revisit.
    Final output clamped to +/-20% — a v1 baseline has no business predicting
    more than that, whatever the inputs say."""
    preds = [model_naive(pts, anchors), model_momentum(pts, anchors),
             model_reversion(pts, anchors)]
    pairs = [(w, p) for w, p in zip(weights, preds) if p is not None]
    if not pairs:
        return None
    tot = sum(w for w, _ in pairs)
    return max(-20.0, min(20.0, sum(w * p for w, p in pairs) / tot))


MODELS = {
    "naive": model_naive,
    "momentum": model_momentum,
    "reversion": model_reversion,
    "blend": model_blend,
}


# --------------------------------------------------------------------- #
# Backtest — walk forward, never peeking at the future
# --------------------------------------------------------------------- #
def backtest(conn):
    series = load_series(conn)
    days = sorted({d for pts in series.values() for d, _ in pts})
    eval_days = [d for d in days
                 if (datetime.strptime(d, "%Y-%m-%d") + timedelta(days=HORIZON_DAYS)
                     ).strftime("%Y-%m-%d") in days]
    if not eval_days:
        print(f"Not enough history yet: need two days {HORIZON_DAYS} apart. "
              f"Have {days[0]}..{days[-1]} ({len(days)} days). "
              f"The harness is ready — it just needs more collection days.")
        return

    scores = {name: {"err": [], "hit": 0, "n": 0} for name in MODELS}
    for t in eval_days:
        t7 = (datetime.strptime(t, "%Y-%m-%d") + timedelta(days=HORIZON_DAYS)).strftime("%Y-%m-%d")
        anchors_t = load_cardmarket_anchors(conn, t)
        for cid, pts in series.items():
            past = pts_upto(pts, t)
            if not past or past[-1][0] != t or past[-1][1] < MIN_PRICE:
                continue
            future = dict(pts).get(t7)
            if future is None:
                continue
            actual = pct(future, past[-1][1])
            if actual is None:
                continue
            for name, fn in MODELS.items():
                p = fn(past, anchors_t.get(cid))
                if p is None:
                    continue
                s = scores[name]
                s["err"].append(abs(p - actual))
                s["n"] += 1
                if (p > 0.5 and actual > 0) or (p < -0.5 and actual < 0) or \
                   (abs(p) <= 0.5 and abs(actual) <= 2.0):
                    s["hit"] += 1

    print(f"Walk-forward backtest | horizon {HORIZON_DAYS}d | scope >= ${MIN_PRICE:.0f} "
          f"| eval days: {len(eval_days)} ({eval_days[0]}..{eval_days[-1]})")
    print(f"{'model':<12} {'n':>7} {'MAE %':>8} {'direction hit':>14}")
    for name, s in scores.items():
        if not s["n"]:
            print(f"{name:<12} {'0':>7}      —              —")
            continue
        print(f"{name:<12} {s['n']:>7} {statistics.mean(s['err']):>8.2f} "
              f"{s['hit'] / s['n'] * 100:>13.1f}%")
    print("\nRead this honestly: with a young dataset, beating 'naive' is the")
    print("only bar that matters. Small edges over naive are noise until the")
    print("eval window covers several weeks.")


# --------------------------------------------------------------------- #
# Daily prediction output
# --------------------------------------------------------------------- #
def confidence(n_days):
    """Honest confidence label from how much history backs the prediction."""
    if n_days >= 60:
        return "medium"
    if n_days >= 21:
        return "low"
    return "very_low"


def predict(conn, json_path):
    series = load_series(conn)
    meta = load_metadata(conn)
    today = max(d for pts in series.values() for d, _ in pts)
    anchors = load_cardmarket_anchors(conn, today)

    out = []
    for cid, pts in series.items():
        past = pts_upto(pts, today)
        if not past or past[-1][1] < MIN_PRICE:
            continue
        p = model_blend(past, anchors.get(cid))
        if p is None:
            continue
        tier, in_print, comp = meta.get(cid, (None, None, None))
        cur = past[-1][1]
        out.append({
            "card_id": cid,
            "current_price": round(cur, 2),
            "pred_7d_pct": round(p, 2),
            "pred_7d_price": round(cur * (1 + p / 100), 2),
            "direction": "up" if p > 0.5 else ("down" if p < -0.5 else "flat"),
            "confidence": confidence(len(past)),
            "tier": tier,
            "meta_card": bool(comp and str(comp).startswith("meta")),
            "model": "blend-v1",
            "as_of": today,
        })
    out.sort(key=lambda r: -abs(r["pred_7d_pct"]))
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"generated": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                   "horizon_days": HORIZON_DAYS, "count": len(out),
                   "disclaimer": "Early-stage statistical estimates, not financial advice.",
                   "predictions": out}, f, indent=1)
    print(f"Wrote {len(out)} predictions to {json_path} (as of {today}).")
    movers = [r for r in out if r["direction"] != "flat"][:5]
    for r in movers:
        print(f"  {r['card_id']:<22} ${r['current_price']:>8.2f} -> {r['pred_7d_pct']:+.1f}% ({r['confidence']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="pokemon_prices.db")
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--predict", action="store_true")
    ap.add_argument("--json", default="predictions.json")
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    if args.backtest:
        backtest(conn)
    if args.predict:
        predict(conn, args.json)
    if not (args.backtest or args.predict):
        print("Nothing to do: pass --backtest and/or --predict")
    conn.close()


if __name__ == "__main__":
    main()
