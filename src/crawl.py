"""
Datenbeschaffung fuer Bot02:
  - Kurshistorie + aktueller Kurs ueber yfinance
  - News ueber mehrere RSS-Feeds (Yahoo Finance je Ticker + Google News je Name)

Bewusst tolerant: faellt eine Quelle aus, laeuft der Rest weiter.
"""
from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

import feedparser
import yfinance as yf

import config
from lexicon import score_text, label


# ----------------------------------------------------------------------
# Watchlist
# ----------------------------------------------------------------------
@dataclass
class Symbol:
    ticker: str
    name: str
    keywords: list[str] = field(default_factory=list)


def load_watchlist(path=config.WATCHLIST_FILE) -> list[Symbol]:
    """Liest config/watchlist.txt im Format  SYMBOL | Name | begriff,begriff."""
    out: list[Symbol] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        ticker = parts[0]
        name = parts[1] if len(parts) > 1 and parts[1] else ticker
        keywords = []
        if len(parts) > 2 and parts[2]:
            keywords = [k.strip() for k in parts[2].split(",") if k.strip()]
        out.append(Symbol(ticker=ticker, name=name, keywords=keywords))
    return out


# ----------------------------------------------------------------------
# Kursdaten
# ----------------------------------------------------------------------
@dataclass
class PriceData:
    ticker: str
    last: float
    currency: str
    closes: list[float]           # taegliche Schlusskurse (aelteste zuerst)
    data_as_of: datetime          # Zeitstempel des letzten Datenpunkts (UTC)
    ok: bool = True
    error: str = ""


def fetch_prices(ticker: str) -> PriceData:
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period=config.HISTORY_PERIOD,
                          interval=config.HISTORY_INTERVAL,
                          auto_adjust=True)
        if hist is None or hist.empty:
            return PriceData(ticker, 0.0, "", [], _now(), ok=False,
                             error="keine Historie")
        closes = [float(x) for x in hist["Close"].dropna().tolist()]
        last = closes[-1]
        # aktuellsten Kurs versuchen (fast_info), sonst letzter Close
        try:
            fi = tk.fast_info
            lp = float(fi.get("last_price") or fi.get("lastPrice") or last)
            if lp > 0:
                last = lp
            currency = str(fi.get("currency") or "")
        except Exception:
            currency = ""
        idx = hist.index[-1]
        as_of = idx.to_pydatetime()
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        else:
            as_of = as_of.astimezone(timezone.utc)
        return PriceData(ticker, last, currency, closes, as_of, ok=True)
    except Exception as e:  # noqa: BLE001
        return PriceData(ticker, 0.0, "", [], _now(), ok=False, error=str(e))


# ----------------------------------------------------------------------
# News
# ----------------------------------------------------------------------
@dataclass
class NewsItem:
    title: str
    published: datetime
    source: str
    sentiment: float


@dataclass
class NewsData:
    items: list[NewsItem]
    count: int
    avg_sentiment: float

    @property
    def label(self) -> str:
        return label(self.avg_sentiment)


def _yahoo_feed(ticker: str) -> str:
    q = urllib.parse.quote(ticker)
    return (f"https://feeds.finance.yahoo.com/rss/2.0/headline"
            f"?s={q}&region=US&lang=en-US")


def _google_news_feed(query: str) -> str:
    q = urllib.parse.quote_plus(query + " stock")
    return (f"https://news.google.com/rss/search?q={q}"
            f"&hl=en-US&gl=US&ceid=US:en")


def _parse_entry_time(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        t = getattr(entry, key, None) or entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return _now()


def fetch_news(sym: Symbol) -> NewsData:
    """Mehrere RSS-Feeds zusammenfuehren, deduplizieren, Sentiment werten."""
    feeds = [_yahoo_feed(sym.ticker), _google_news_feed(sym.name)]
    for kw in sym.keywords:
        feeds.append(_google_news_feed(kw))

    cutoff = _now() - timedelta(hours=config.NEWS_LOOKBACK_HOURS)
    seen: set[str] = set()
    items: list[NewsItem] = []

    for url in feeds:
        try:
            parsed = feedparser.parse(url, agent=config.USER_AGENT)
        except Exception:
            continue
        for e in parsed.entries:
            title = (getattr(e, "title", "") or "").strip()
            if not title:
                continue
            key = title.lower()[:120]
            if key in seen:
                continue
            published = _parse_entry_time(e)
            if published < cutoff:
                continue
            seen.add(key)
            src = ""
            try:
                src = (e.get("source", {}) or {}).get("title", "") or parsed.feed.get("title", "")
            except Exception:
                src = ""
            items.append(NewsItem(title=title, published=published,
                                  source=src, sentiment=score_text(title)))
        time.sleep(0.2)   # hoeflich bleiben

    items.sort(key=lambda x: x.published, reverse=True)
    items = items[: config.NEWS_MAX_ITEMS]
    if items:
        avg = sum(i.sentiment for i in items) / len(items)
    else:
        avg = 0.0
    return NewsData(items=items, count=len(items), avg_sentiment=avg)


# ----------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)
