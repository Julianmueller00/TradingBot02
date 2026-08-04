# Bot02 – News-getriebener Trading-Advisor

Entscheidungshilfe (kein automatischer Handel). Crawlt alle 5 Stunden Kurse
(Yahoo Finance) und News (mehrere RSS-Feeds) zur Watchlist, verrechnet News-
Sentiment mit der Kurshistorie und gibt BUY/SELL/HOLD-Empfehlungen über vier
Horizonte (4h, 1d, 5d, 20d).

## Was anders ist als beim Vorgänger-Bot
- **News ist echter Input**, nicht nur Beiwerk: das Sentiment verschiebt die
  Prognose (kurzer Horizont stark, langer Horizont abklingend).
- **Kalibrierte Konfidenz**: Streuung wächst mit √Zeit; P(auf) und Sicherheit
  sind begrenzt – keine unrealistischen 100 %/1 %-Werte auf 20 Tagen.
- **HOLD-Gating**: ohne klares News-Signal wird nicht gehandelt.

## Installation (in der VM, einmalig)
```bat
cd C:\Bot02
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Falls keine requirements.txt vorhanden:
`pip install yfinance feedparser requests pandas numpy python-dateutil`

## Manueller Lauf
```bat
cd C:\Bot02
.venv\Scripts\activate
python src\run.py
```
Ergebnis: Tabelle in der Konsole + Anhängen an `logs\recommendations.jsonl`.
Fällige frühere Prognosen werden gegen den Ist-Kurs aufgelöst
(`logs\outcomes.jsonl`, „Trefferkontrolle").

## Automatik alle 5 Stunden (Task Scheduler)
PowerShell als Admin (Benutzer/Passwort anpassen):
```powershell
$action  = New-ScheduledTaskAction -Execute "C:\Bot02\run_bot.bat"
$trigger = New-ScheduledTaskTrigger -Once -At 6:00AM -RepetitionInterval (New-TimeSpan -Hours 5)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "Bot02_Crawl" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -User "DEIN-VM-USER" -Password "PASSWORT"
```

## Watchlist erweitern
Einfach eine Zeile in `config\watchlist.txt` anhängen:
```
SYMBOL | Anzeigename | optionale,News,Suchbegriffe
```
Kein Code-Eingriff nötig. Europäische Werte mit Börsensuffix (.DE .AS .PA .SW .L).

## Stellschrauben
Alles Wichtige in `src\config.py`:
- `HORIZONS` – Prognosehorizonte
- `ROUND_TRIP_COST`, `MIN_NET_EDGE`, `MIN_CONFIDENCE` – Handelsschwellen
- `NEWS_IMPACT`, `NEWS_DECAY_DAYS` – Stärke/Abklingen des News-Effekts
- `PUP_CLAMP`, `CONF_CLAMP` – Begrenzung gegen Überkonfidenz

## Dateien
```
Bot02\
├─ config\watchlist.txt      Symbole (erweiterbar)
├─ src\config.py             zentrale Einstellungen
├─ src\lexicon.py            Finanz-Sentiment-Wortschatz
├─ src\crawl.py              Kurse + News holen
├─ src\signals.py            Prognose-/Signal-Logik
├─ src\run.py                Einstiegspunkt
├─ run_bot.bat               Starter (auch für Scheduler)
└─ logs\                     recommendations.jsonl, outcomes.jsonl, run.log
```

## Hinweis
Verzögerte Kursdaten (je nach Börse 15–20 Min), Quelle Yahoo Finance über
yfinance (inoffiziell). Keine Handelsanweisung, keine Finanzberatung – die
Ausführung machst du manuell.
