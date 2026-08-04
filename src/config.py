"""
Zentrale Konfiguration fuer Bot02.
Alle Stellschrauben an einem Ort - hier anpassen statt im Code suchen.
"""
from pathlib import Path

# --- Pfade -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent      # C:\Bot02
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
WATCHLIST_FILE = CONFIG_DIR / "watchlist.txt"
REC_LOG = LOGS_DIR / "recommendations.jsonl"           # eine Zeile pro Empfehlung
OUTCOMES_LOG = LOGS_DIR / "outcomes.jsonl"             # aufgeloeste Prognosen (Ist-Werte)

# --- Versionierung (taucht in jeder Empfehlung auf) --------------------
STRATEGY_VERSION = "2.0.0-news"    # News ist echter Input, kalibrierte Konfidenz
CODE_VERSION = "0.1.0"

# --- Horizonte ---------------------------------------------------------
# Name -> Laenge in HANDELSTAGEN (fuer die Volatilitaets-Skalierung).
# 1 Handelstag ~ 6.5 Boersenstunden; 4h entspricht ~0.6 Handelstagen.
HORIZONS = {
    "4h": 0.6,
    "1d": 1.0,
    "5d": 5.0,
    "20d": 20.0,
}

# --- Handelslogik ------------------------------------------------------
ROUND_TRIP_COST = 0.004     # 0.40 % Rundlaufkosten (Kauf+Verkauf), wie beim Kollegen
MIN_NET_EDGE = 0.005        # 0.50 % Mindest-Nettovorsprung fuer ein Signal
MIN_CONFIDENCE = 0.15       # darunter -> HOLD (verhindert schwache Drift-Signale)
PUP_CLAMP = (0.02, 0.98)    # P(auf) nie 0/100 % - verhindert Ueberkonfidenz
CONF_CLAMP = (0.05, 0.95)   # Sicherheit ebenfalls begrenzen

# --- News ---------------------------------------------------------------
NEWS_LOOKBACK_HOURS = 72          # Zeitfenster fuer beruecksichtigte Meldungen
NEWS_MAX_ITEMS = 40               # pro Symbol maximal so viele Meldungen werten
# Wie stark News die Prognose verschiebt (Basis-Ausschlag bei Sentiment=+/-1
# auf 1 Handelstag). Wirkung klingt ueber laengere Horizonte ab (siehe signals.py).
NEWS_IMPACT = 0.02                # 2 % max. Tages-Tilt bei extremem Sentiment
NEWS_DECAY_DAYS = 6.0             # Abklingkonstante des News-Effekts (Tage)

# --- Datenhistorie ------------------------------------------------------
HISTORY_PERIOD = "1y"             # yfinance-Zeitraum fuer Vola/Drift
HISTORY_INTERVAL = "1d"

# --- Netz ---------------------------------------------------------------
HTTP_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (Bot02 news-trading-advisor)"
