"""
Signal- und Prognose-Logik fuer Bot02.

Kernidee (bewusst anders als der rein statistische Bot des Kollegen):
  1. BASELINE = Random-Walk mit Drift aus der Kurshistorie.
  2. NEWS ist ein ECHTER Input: das Sentiment verschiebt die Erwartung
     (kurzer Horizont stark, langer Horizont abklingend).
  3. KALIBRIERTE Unsicherheit: Streuung waechst mit sqrt(Zeit); P(auf) und
     Sicherheit werden begrenzt -> keine absurden 100 %/1 %-Werte auf 20 Tagen.

Alles nur Entscheidungshilfe, kein automatischer Handel.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

import config
from crawl import PriceData, NewsData, Symbol

Z_10_90 = 1.2816          # z-Wert fuer das 10 %/90 %-Quantil
SQRT2 = math.sqrt(2.0)

# Zeit-Offsets nur fuer die Anzeige des Zieltermins
_HORIZON_DELTA = {
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
    "5d": timedelta(days=5),
    "20d": timedelta(days=20),
}


@dataclass
class HorizonForecast:
    horizon: str
    days: float
    target_time: str
    expected: float
    p10: float
    p90: float
    ret_gross: float
    ret_net: float
    p_up: float
    baseline: float


@dataclass
class Recommendation:
    ticker: str
    name: str
    action: str                 # BUY / SELL / HOLD
    confidence: float           # 0..1
    price: float
    currency: str
    best_horizon: str
    invalid_from: float
    horizons: list              # list[dict]
    news_count: int
    news_sentiment: float
    news_label: str
    computed_at: str
    data_as_of: str
    strategy: str
    code: str
    model_id: str

    def to_json(self) -> dict:
        return asdict(self)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / SQRT2))


def _daily_stats(closes: list[float]) -> tuple[float, float]:
    """Drift (mu) und Volatilitaet (sigma) der taeglichen Log-Renditen."""
    if len(closes) < 20:
        return 0.0, 0.02
    rets = [math.log(closes[i] / closes[i - 1])
            for i in range(1, len(closes)) if closes[i - 1] > 0]
    n = len(rets)
    mu = sum(rets) / n
    var = sum((r - mu) ** 2 for r in rets) / (n - 1)
    sigma = math.sqrt(var)
    # Drift daempfen: reine historische Drift ueberschaetzt Trends
    mu *= 0.5
    return mu, max(sigma, 1e-4)


def _model_id(ticker: str) -> str:
    h = hashlib.sha1(f"{ticker}|{config.STRATEGY_VERSION}".encode()).hexdigest()
    return h[:12]


def build_recommendation(sym: Symbol, price: PriceData,
                         news: NewsData) -> Recommendation:
    now = datetime.now(timezone.utc)
    mu_d, sigma_d = _daily_stats(price.closes)
    last = price.last
    sentiment = news.avg_sentiment

    horizons: list[HorizonForecast] = []
    for name, days in config.HORIZONS.items():
        # Baseline: Random-Walk mit gedaempfter Drift (Log-Raum)
        base_logret = mu_d * days
        baseline_price = last * math.exp(base_logret)

        # News-Komponente: klingt ueber laengere Horizonte ab
        news_weight = math.exp(-days / config.NEWS_DECAY_DAYS)
        news_logret = config.NEWS_IMPACT * sentiment * news_weight

        model_logret = base_logret + news_logret
        expected = last * math.exp(model_logret)

        # Unsicherheit skaliert mit sqrt(Zeit)
        sigma_h = sigma_d * math.sqrt(days)
        p10 = last * math.exp(model_logret - Z_10_90 * sigma_h)
        p90 = last * math.exp(model_logret + Z_10_90 * sigma_h)

        gross = expected / last - 1.0
        net_mag = abs(gross) - config.ROUND_TRIP_COST
        net = math.copysign(net_mag, gross) if gross != 0 else -config.ROUND_TRIP_COST

        # P(auf): Wahrscheinlichkeit positiver Rendite, begrenzt
        p_up = _norm_cdf(model_logret / sigma_h) if sigma_h > 0 else 0.5
        p_up = min(max(p_up, config.PUP_CLAMP[0]), config.PUP_CLAMP[1])

        horizons.append(HorizonForecast(
            horizon=name, days=days,
            target_time=(now + _HORIZON_DELTA[name]).isoformat(),
            expected=round(expected, 4),
            p10=round(p10, 4), p90=round(p90, 4),
            ret_gross=round(gross, 4), ret_net=round(net, 4),
            p_up=round(p_up, 4), baseline=round(baseline_price, 4),
        ))

    # Bester Horizont = groesster handelbarer Vorsprung, GEWICHTET mit der
    # Richtungssicherheit. So gewinnen news-getriebene kurze Horizonte gegen
    # blosse Drift auf 20 Tagen.
    def tradeability(h: HorizonForecast) -> float:
        edge = max(abs(h.ret_gross) - config.ROUND_TRIP_COST, 0.0)
        dir_conf = 2.0 * abs(h.p_up - 0.5)
        return edge * dir_conf

    best = max(horizons, key=tradeability)
    net_edge = abs(best.ret_gross) - config.ROUND_TRIP_COST

    # Sicherheit direkt aus der (kalibrierten) Richtungswahrscheinlichkeit
    confidence = 2.0 * abs(best.p_up - 0.5)
    confidence = min(max(confidence, config.CONF_CLAMP[0]), config.CONF_CLAMP[1])

    actionable = (net_edge > config.MIN_NET_EDGE
                  and confidence >= config.MIN_CONFIDENCE)
    if actionable and best.ret_gross > 0:
        action = "BUY"
        invalid_from = best.p10          # faellt der Kurs hierunter, ist die These hin
    elif actionable and best.ret_gross < 0:
        action = "SELL"
        invalid_from = best.p90
    else:
        action = "HOLD"
        invalid_from = best.expected

    return Recommendation(
        ticker=sym.ticker, name=sym.name, action=action,
        confidence=round(confidence, 4), price=round(last, 4),
        currency=price.currency, best_horizon=best.horizon,
        invalid_from=round(invalid_from, 4),
        horizons=[asdict(h) for h in horizons],
        news_count=news.count, news_sentiment=round(sentiment, 4),
        news_label=news.label,
        computed_at=now.isoformat(),
        data_as_of=price.data_as_of.isoformat(),
        strategy=config.STRATEGY_VERSION, code=config.CODE_VERSION,
        model_id=_model_id(sym.ticker),
    )
