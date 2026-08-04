"""
Bot02 - Einstiegspunkt.
Ablauf pro Lauf:
  1. Faellige Prognosen aufloesen (Trefferkontrolle -> outcomes.jsonl)
  2. Watchlist crawlen (Kurse + News), Empfehlungen rechnen
  3. Empfehlungen in recommendations.jsonl schreiben und als Tabelle ausgeben

Aufruf:  python src\run.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import config
from crawl import load_watchlist, fetch_prices, fetch_news
from signals import build_recommendation


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _append_jsonl(path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


# ----------------------------------------------------------------------
# Schritt 1: Trefferkontrolle
# ----------------------------------------------------------------------
def resolve_outcomes() -> int:
    recs = _read_jsonl(config.REC_LOG)
    if not recs:
        return 0
    resolved = {
        (o["ticker"], o["computed_at"], o["horizon"])
        for o in _read_jsonl(config.OUTCOMES_LOG)
    }
    now = _now()
    price_cache: dict[str, float] = {}
    n_new = 0

    for rec in recs:
        ticker = rec.get("ticker")
        computed_at = rec.get("computed_at")
        for h in rec.get("horizons", []):
            key = (ticker, computed_at, h["horizon"])
            if key in resolved:
                continue
            try:
                target = datetime.fromisoformat(h["target_time"])
            except (ValueError, KeyError):
                continue
            if target > now:
                continue  # noch nicht faellig
            if ticker not in price_cache:
                pd = fetch_prices(ticker)
                price_cache[ticker] = pd.last if pd.ok else 0.0
            actual = price_cache[ticker]
            if actual <= 0:
                continue
            predicted = h["expected"]
            entry_price = rec.get("price", 0.0)
            actual_ret = (actual / entry_price - 1.0) if entry_price else 0.0
            pred_ret = h.get("ret_gross", 0.0)
            hit = (actual_ret > 0) == (pred_ret > 0)
            _append_jsonl(config.OUTCOMES_LOG, {
                "ticker": ticker,
                "computed_at": computed_at,
                "horizon": h["horizon"],
                "target_time": h["target_time"],
                "resolved_at": now.isoformat(),
                "entry_price": entry_price,
                "predicted": predicted,
                "actual": round(actual, 4),
                "predicted_return": round(pred_ret, 4),
                "actual_return": round(actual_ret, 4),
                "direction_hit": hit,
            })
            resolved.add(key)
            n_new += 1
    return n_new


# ----------------------------------------------------------------------
# Schritt 2+3: Empfehlungen
# ----------------------------------------------------------------------
def run() -> None:
    symbols = load_watchlist()
    print(f"[{_now().strftime('%Y-%m-%d %H:%M:%S')} UTC] Bot02 - "
          f"Strategie {config.STRATEGY_VERSION} - {len(symbols)} Symbole")

    n_resolved = resolve_outcomes()
    if n_resolved:
        print(f"  Trefferkontrolle: {n_resolved} Prognose(n) aufgeloest "
              f"-> {config.OUTCOMES_LOG.name}")

    recs = []
    for sym in symbols:
        try:
            price = fetch_prices(sym.ticker)
            if not price.ok:
                print(f"  ! {sym.ticker:9s} keine Kursdaten ({price.error})")
                continue
            news = fetch_news(sym)
            rec = build_recommendation(sym, price, news)
            _append_jsonl(config.REC_LOG, rec.to_json())
            recs.append(rec)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {sym.ticker:9s} Fehler: {e}")

    _print_table(recs)
    print(f"\n  {len(recs)} Empfehlungen -> {config.REC_LOG}")


def _fmt_pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def _print_table(recs: list) -> None:
    if not recs:
        print("  (keine Empfehlungen)")
        return
    print()
    header = (f"{'Symbol':9s} {'Akt.':5s} {'Sich.':6s} {'Kurs':>10s} "
              f"{'Horiz':6s} {'Erwartet':>10s} {'Netto':>8s} {'P(auf)':>6s} "
              f"{'News':>5s} {'Sent.':>6s}")
    print(header)
    print("-" * len(header))
    # BUY/SELL zuerst, nach Nettovorsprung sortiert
    order = {"BUY": 0, "SELL": 0, "HOLD": 1}
    recs_sorted = sorted(
        recs,
        key=lambda r: (order.get(r.action, 2),
                       -max(abs(h["ret_gross"]) for h in r.horizons)))
    for r in recs_sorted:
        best = next(h for h in r.horizons if h["horizon"] == r.best_horizon)
        print(f"{r.ticker:9s} {r.action:5s} {r.confidence * 100:4.0f}% "
              f"{r.price:10.2f} {r.best_horizon:6s} {best['expected']:10.2f} "
              f"{_fmt_pct(best['ret_net']):>8s} {best['p_up'] * 100:5.0f}% "
              f"{r.news_count:5d} {r.news_sentiment:+6.2f}")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        sys.exit(130)
