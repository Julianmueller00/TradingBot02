# Bot02 kostenlos & dauerhaft ins Netz – Schritt für Schritt

Ziel: Der Bot läuft **alle 5 Stunden von allein in GitHubs Cloud** (kein PC, keine
VM nötig) und veröffentlicht die Empfehlungen auf einer **passwortgeschützten
Webseite** – so wie die Seite deines Kollegen.

Dein GitHub-Benutzer: **Julianmueller00**
Dashboard-Passwort: **Aktien2026**  (änderbar in `src/build_site.py`, Zeile mit `PASSWORT =`)

---

## Wichtig zuerst: öffentlich vs. privat

- **Kostenloser Plan → Repository muss ÖFFENTLICH sein**, sonst funktioniert die
  Webseite (GitHub Pages) nicht.
- Öffentlich heißt: Der **Code** und die **Log-Dateien** (`recommendations.jsonl`)
  sind für jeden sichtbar, der die Repo-Adresse kennt. Die **Dashboard-Seite
  selbst** ist durch das Passwort geschützt – die Rohdaten im Repo aber nicht.
- Willst du auch die Daten privat halten, brauchst du **GitHub Pro (~4 $/Monat)**;
  dann darf das Repo privat sein (die Webseite bleibt trotzdem per Passwort erreichbar).

Für den Anfang (Hobby-Empfehlungen) ist **öffentlich** völlig okay und 100 % gratis.

---

## Schritt 1 – GitHub Desktop installieren
Ohne Kommandozeile, am einfachsten:
1. Lade **GitHub Desktop** von `desktop.github.com` und installiere es.
2. Melde dich mit deinem Konto (Julianmueller00) an.

## Schritt 2 – Projekt als Repository hinzufügen
1. In GitHub Desktop: **File → Add Local Repository**.
2. Wähle den Ordner `C:\Dev\Claude\TradingBot2`.
3. Kommt der Hinweis „this directory is not a repository", klick auf
   **„create a repository"** → **Create Repository**.
   (Die `.venv` wird dank `.gitignore` automatisch ausgelassen.)

## Schritt 3 – Veröffentlichen (Publish)
1. Klick oben auf **Publish repository**.
2. **Häkchen bei „Keep this code private" ENTFERNEN** → Repo wird öffentlich
   (nötig für den Gratis-Plan, siehe oben).
3. Name z. B. `bot02` → **Publish Repository**.

## Schritt 4 – Schreibrechte für die Automatik freigeben
Auf `github.com` in deinem neuen Repo:
1. **Settings → Actions → General**.
2. Ganz unten **„Workflow permissions"** → **„Read and write permissions"**
   auswählen → **Save**.
   (Damit darf der Bot seine aktualisierten Logs zurückschreiben.)

## Schritt 5 – Webseite (Pages) auf „GitHub Actions" stellen
Weiter in **Settings → Pages**:
- Unter **„Build and deployment" → Source** wähle **„GitHub Actions"**.
  (Nichts weiter einstellen – unser Workflow erledigt den Rest.)

## Schritt 6 – Ersten Lauf starten
1. Oben im Repo auf den Reiter **Actions**.
2. Falls gefragt: Workflows aktivieren (**„I understand… enable"**).
3. Links **„Bot02 – Lauf & Dashboard"** anklicken → rechts **„Run workflow" → Run**.
4. Warte 2–4 Minuten, bis der Lauf grün ist.

## Schritt 7 – Deine Seite aufrufen
- Die Adresse steht danach unter **Settings → Pages** ganz oben, meist:
  **https://julianmueller00.github.io/bot02/**
- Passwort **Aktien2026** eingeben → deine Empfehlungstabelle erscheint.

Ab jetzt aktualisiert sich alles alle 5 Stunden von selbst. Deinen PC und die
VM brauchst du dafür nicht mehr.

---

## Später anpassen
- **Passwort ändern:** in `src/build_site.py` die Zeile `PASSWORT = "Aktien2026"`
  ändern, in GitHub Desktop **Commit** + **Push**.
- **Watchlist erweitern:** `config/watchlist.txt` bearbeiten, committen, pushen.
- **Taktung ändern:** in `.github/workflows/bot.yml` die Zeile `cron:` anpassen
  (`0 */5 * * *` = alle 5 h; `0 6,12,18 * * *` = 6/12/18 Uhr UTC).

## Gut zu wissen
- Öffentliche Repos haben **unbegrenzte** Gratis-Action-Minuten.
- Yahoo Finance kann Cloud-Server gelegentlich bremsen; taucht bei einem Symbol
  mal „keine Kursdaten" auf, ist das meist beim nächsten Lauf wieder weg.
