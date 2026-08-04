"""
build_site.py - erzeugt die Dashboard-Seite fuer GitHub Pages.

Liest die Empfehlungen (recommendations.jsonl) und die Trefferkontrolle
(outcomes.jsonl), nimmt je Symbol die NEUESTE Empfehlung und schreibt eine
fertige, in sich geschlossene Seite nach  <repo>/site/index.html .

Aufruf:  python src/build_site.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import config

# ----------------------------------------------------------------------
# HIER DAS PASSWORT AENDERN  (so wie Silber/Gold beim Kollegen)
# ----------------------------------------------------------------------
PASSWORT = "Aktien2026"
# ----------------------------------------------------------------------

SITE_DIR = config.BASE_DIR / "site"


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


def _latest_per_ticker(recs: list[dict]) -> list[dict]:
    """Je Symbol nur die zuletzt berechnete Empfehlung behalten."""
    newest: dict[str, dict] = {}
    for r in recs:
        t = r.get("ticker")
        if not t:
            continue
        if t not in newest or r.get("computed_at", "") > newest[t].get("computed_at", ""):
            newest[t] = r
    return list(newest.values())


def _compact(rec: dict) -> dict:
    """Auf die Felder reduzieren, die das Dashboard anzeigt."""
    best = None
    for h in rec.get("horizons", []):
        if h.get("horizon") == rec.get("best_horizon"):
            best = h
            break
    if best is None and rec.get("horizons"):
        best = rec["horizons"][0]
    best = best or {}
    return {
        "ticker": rec.get("ticker", ""),
        "name": rec.get("name", ""),
        "action": rec.get("action", "HOLD"),
        "confidence": rec.get("confidence", 0.0),
        "price": rec.get("price", 0.0),
        "currency": rec.get("currency", ""),
        "horizon": rec.get("best_horizon", ""),
        "expected": best.get("expected", 0.0),
        "ret_net": best.get("ret_net", 0.0),
        "p_up": best.get("p_up", 0.0),
        "news_count": rec.get("news_count", 0),
        "news_sentiment": rec.get("news_sentiment", 0.0),
        "news_label": rec.get("news_label", ""),
        "computed_at": rec.get("computed_at", ""),
    }


def _hitrate(outcomes: list[dict]) -> dict:
    total = len(outcomes)
    hits = sum(1 for o in outcomes if o.get("direction_hit"))
    rate = (hits / total) if total else 0.0
    return {"total": total, "hits": hits, "rate": rate}


def build() -> None:
    recs = _latest_per_ticker(_read_jsonl(config.REC_LOG))
    data = [_compact(r) for r in recs]

    # Reihenfolge: BUY/SELL zuerst, dann nach Netto-Vorsprung
    order = {"BUY": 0, "SELL": 0, "HOLD": 1}
    data.sort(key=lambda d: (order.get(d["action"], 2), -abs(d["ret_net"])))

    stats = _hitrate(_read_jsonl(config.OUTCOMES_LOG))
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    payload = {
        "updated": updated,
        "strategy": config.STRATEGY_VERSION,
        "stats": stats,
        "rows": data,
    }

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "index.html").write_text(
        _render(payload, PASSWORT), encoding="utf-8"
    )
    # zusaetzlich als Rohdaten, falls du sie woanders brauchst
    (SITE_DIR / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Dashboard geschrieben: {SITE_DIR / 'index.html'} "
          f"({len(data)} Symbole, Trefferquote {stats['rate']*100:.0f}%)")


def _render(payload: dict, passwort: str) -> str:
    import hashlib
    pw_hash = hashlib.sha256(passwort.encode("utf-8")).hexdigest()
    data_json = json.dumps(payload, ensure_ascii=False)
    # doppelte geschweifte Klammern im CSS/JS, damit .format nicht stoert -> wir
    # nutzen bewusst kein .format, sondern Ersetzung per Platzhalter:
    html = _TEMPLATE
    html = html.replace("__PW_HASH__", pw_hash)
    html = html.replace("__DATA_JSON__", data_json)
    return html


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bot02 - Aktien-Empfehlungen</title>
<style>
  :root{
    --bg:#0f1420; --card:#171e2e; --line:#26304a; --txt:#e8edf7;
    --muted:#93a0bd; --buy:#25c281; --sell:#ff5c6c; --hold:#8b97b3;
    --accent:#5b8cff;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
    font:15px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
  .wrap{max-width:1040px;margin:0 auto;padding:22px 16px 60px}
  header{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px;margin-bottom:6px}
  h1{font-size:20px;margin:0;font-weight:650}
  .sub{color:var(--muted);font-size:13px}
  .bar{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 18px}
  .pill{background:var(--card);border:1px solid var(--line);border-radius:10px;
    padding:10px 14px;font-size:13px;color:var(--muted)}
  .pill b{color:var(--txt);font-size:15px}
  table{width:100%;border-collapse:collapse;background:var(--card);
    border:1px solid var(--line);border-radius:12px;overflow:hidden}
  th,td{padding:11px 12px;text-align:right;border-bottom:1px solid var(--line);
    white-space:nowrap}
  th{font-size:11px;letter-spacing:.04em;text-transform:uppercase;
    color:var(--muted);font-weight:600;background:#131a29}
  th:first-child,td:first-child{text-align:left}
  tr:last-child td{border-bottom:none}
  .tk{font-weight:650}.nm{color:var(--muted);font-size:12px}
  .tag{display:inline-block;min-width:52px;text-align:center;padding:3px 8px;
    border-radius:6px;font-weight:700;font-size:12px}
  .BUY{background:rgba(37,194,129,.16);color:var(--buy)}
  .SELL{background:rgba(255,92,108,.16);color:var(--sell)}
  .HOLD{background:rgba(139,151,179,.14);color:var(--hold)}
  .pos{color:var(--buy)}.neg{color:var(--sell)}
  .foot{color:var(--muted);font-size:12px;margin-top:16px;line-height:1.6}
  /* Login */
  #gate{position:fixed;inset:0;background:var(--bg);display:flex;
    align-items:center;justify-content:center;padding:20px}
  .box{background:var(--card);border:1px solid var(--line);border-radius:14px;
    padding:26px;width:100%;max-width:320px;text-align:center}
  .box h2{margin:0 0 4px;font-size:17px}
  .box p{margin:0 0 16px;color:var(--muted);font-size:13px}
  input{width:100%;padding:11px 12px;border-radius:9px;border:1px solid var(--line);
    background:#0f1626;color:var(--txt);font-size:15px}
  button{width:100%;margin-top:10px;padding:11px;border:0;border-radius:9px;
    background:var(--accent);color:#fff;font-size:15px;font-weight:600;cursor:pointer}
  .err{color:var(--sell);font-size:13px;min-height:18px;margin-top:8px}
  #app{display:none}
  @media(max-width:640px){
    .nm{display:none}
    th:nth-child(6),td:nth-child(6),th:nth-child(8),td:nth-child(8){display:none}
  }
</style>
</head>
<body>

<div id="gate">
  <div class="box">
    <h2>Bot02</h2>
    <p>Bitte Passwort eingeben</p>
    <input id="pw" type="password" autofocus placeholder="Passwort"
      onkeydown="if(event.key==='Enter')check()">
    <button onclick="check()">Ansehen</button>
    <div class="err" id="err"></div>
  </div>
</div>

<div id="app">
  <div class="wrap">
    <header>
      <h1>Bot02 &middot; Aktien-Empfehlungen</h1>
      <span class="sub" id="sub"></span>
    </header>
    <div class="bar" id="bar"></div>
    <table>
      <thead><tr>
        <th>Symbol</th><th>Signal</th><th>Sicherheit</th><th>Kurs</th>
        <th>Horizont</th><th>Erwartet</th><th>Netto</th><th>P(auf)</th>
        <th>News</th><th>Sentiment</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
    <div class="foot">
      Entscheidungshilfe, keine Finanzberatung &middot; Kursdaten 15&ndash;20&nbsp;Min
      verzoegert (Yahoo Finance) &middot; die Ausfuehrung machst du manuell.
    </div>
  </div>
</div>

<script>
const PW_HASH = "__PW_HASH__";
const DATA = __DATA_JSON__;

async function sha256(s){
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function check(){
  const v = document.getElementById("pw").value;
  if(await sha256(v) === PW_HASH){ open_app(); }
  else { document.getElementById("err").textContent = "Falsches Passwort"; }
}
function open_app(){
  document.getElementById("gate").style.display="none";
  document.getElementById("app").style.display="block";
  render();
}
function pct(x){ return (x*100).toFixed(2).replace("-","−") + "%"; }
function signed(x){ const s=(x*100); return (s>=0?"+":"−")+Math.abs(s).toFixed(2)+"%"; }
function render(){
  document.getElementById("sub").textContent =
    "Stand: " + DATA.updated + "  ·  Strategie " + DATA.strategy;
  const s = DATA.stats;
  const buys = DATA.rows.filter(r=>r.action!=="HOLD").length;
  document.getElementById("bar").innerHTML =
    pill(DATA.rows.length, "Symbole") +
    pill(buys, "aktive Signale") +
    pill(s.total ? (s.rate*100).toFixed(0)+"%" : "–",
         "Trefferquote" + (s.total? " ("+s.total+" geprüft)":""));
  const tb = document.getElementById("rows");
  tb.innerHTML = DATA.rows.map(r=>{
    const net = r.ret_net>=0 ? "pos":"neg";
    const cur = r.currency || "";
    return `<tr>
      <td><span class="tk">${r.ticker}</span> <span class="nm">${r.name||""}</span></td>
      <td><span class="tag ${r.action}">${r.action}</span></td>
      <td>${(r.confidence*100).toFixed(0)}%</td>
      <td>${r.price.toFixed(2)} ${cur}</td>
      <td>${r.horizon}</td>
      <td>${r.expected.toFixed(2)}</td>
      <td class="${net}">${signed(r.ret_net)}</td>
      <td>${(r.p_up*100).toFixed(0)}%</td>
      <td>${r.news_count}</td>
      <td>${(r.news_sentiment>=0?"+":"−")+Math.abs(r.news_sentiment).toFixed(2)}</td>
    </tr>`;
  }).join("");
}
function pill(v,l){ return `<div class="pill"><b>${v}</b> ${l}</div>`; }
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
