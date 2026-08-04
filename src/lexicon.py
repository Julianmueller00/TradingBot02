"""
Kompaktes Finanz-Sentiment-Lexikon (Loughran-McDonald-Stil).

Bewertet Schlagzeilen/Teaser mit einem simplen, aber finanzspezifischen
Wortschatz. Bewusst schlank gehalten und leicht erweiterbar - fuer eine
groessere Abdeckung koennen die vollstaendigen Loughran-McDonald-Wortlisten
eingehaengt werden (Spalten 'Positive'/'Negative' aus der LM Master Dictionary
CSV in die Sets unten uebernehmen).
"""
import re

POSITIVE = {
    "beat", "beats", "beat expectations", "surge", "surges", "surged", "soar",
    "soars", "jump", "jumps", "record", "records", "strong", "growth", "grow",
    "grows", "profit", "profits", "gain", "gains", "gained", "upgrade",
    "upgrades", "outperform", "outperforms", "bullish", "rally", "rallies",
    "rebound", "rebounds", "expansion", "expand", "boost", "boosts", "boosted",
    "wins", "win", "won", "award", "awarded", "contract", "contracts",
    "raise", "raises", "raised", "buyback", "dividend", "positive", "optimistic",
    "breakthrough", "approval", "approved", "milestone", "exceed", "exceeds",
    "exceeded", "robust", "accelerate", "accelerates", "momentum", "demand",
    # deutsch
    "steigt", "steigen", "gewinn", "gewinne", "wachstum", "rekord", "stark",
    "starke", "positiv", "hochgestuft", "kaufen", "erholung", "auftrag",
    "auftraege", "milliarde", "milliarden", "uebertrifft", "prognose angehoben",
    "dividende", "durchbruch", "zulassung", "nachfrage",
}

NEGATIVE = {
    "miss", "misses", "missed", "plunge", "plunges", "plunged", "drop", "drops",
    "dropped", "fall", "falls", "fell", "slump", "slumps", "decline", "declines",
    "declined", "loss", "losses", "weak", "weakness", "cut", "cuts", "downgrade",
    "downgrades", "bearish", "warn", "warns", "warning", "warned", "lawsuit",
    "sue", "sued", "probe", "investigation", "recall", "recalls", "layoff",
    "layoffs", "bankruptcy", "default", "fraud", "scandal", "sell-off",
    "selloff", "concern", "concerns", "risk", "risks", "slowdown", "delay",
    "delays", "delayed", "halt", "halts", "shortfall", "disappointing",
    "disappoint", "disappoints", "guidance cut", "profit warning", "crash",
    # deutsch
    "faellt", "fallen", "verlust", "verluste", "schwach", "schwaeche", "warnt",
    "warnung", "gewinnwarnung", "abgestuft", "verkaufen", "klage", "ermittlung",
    "rueckruf", "entlassung", "entlassungen", "insolvenz", "betrug", "skandal",
    "einbruch", "sorgen", "risiko", "verzoegerung", "enttaeuschend", "abschwung",
}

_WORD_RE = re.compile(r"[a-zA-ZaeoeueAEOEUEss\-]+")


def score_text(text: str) -> float:
    """
    Sentiment eines einzelnen Textes in [-1, 1].
    (pos - neg) / (pos + neg).  0.0 wenn keine Treffer.
    """
    if not text:
        return 0.0
    low = text.lower()
    # zuerst Mehrwort-Phrasen zaehlen
    pos = sum(low.count(p) for p in POSITIVE if " " in p)
    neg = sum(low.count(n) for n in NEGATIVE if " " in n)
    # dann Einzelwoerter
    tokens = _WORD_RE.findall(low)
    pos += sum(1 for t in tokens if t in POSITIVE)
    neg += sum(1 for t in tokens if t in NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def label(score: float) -> str:
    if score > 0.15:
        return "positiv"
    if score < -0.15:
        return "negativ"
    return "neutral"
