# Baggersee-Verwaltung

Tkinter-Anwendung zur täglichen Erfassung und Auswertung der Betriebsdaten
eines Baggersees.

Repository: https://github.com/LeviMayer/BaggerseeVerwaltung

## Projektstruktur

```
BaggerseeVerwaltung/
  main.py                    Einstiegspunkt
  baggersee/
    modelle.py                Datenmodell (Tagesdatensatz) + Validierung
    datenhaltung.py            CSV-Persistenz, CRUD (DatenManager)
    eingabe.py                  Eingabemaske (Erfassen/Bearbeiten/Löschen)
    kalender.py                  Monatskalender-Widget
    saison.py                     Saisonzeiträume je Jahr (Persistenz)
    saisonansicht.py               Saisonübersicht-Widget (Erfassungsseite)
    auswertung.py                Zeitraumauswahl, Zusammenfassung, Tabs
    diagramme.py                 matplotlib-Diagrammfunktionen
    stil.py                       Dunkles Farbschema (ttk-Style) + Icon
    updater.py                    Auto-Update über GitHub Releases
    version.py                    Versionsnummer der Anwendung
  import_daten.py             Einmal-/Nachimport historischer CSV-Exporte
  icon.ico                    Anwendungs-Icon (Fenster + .exe)
  requirements.txt
```

## Datenhaltung

Die Daten werden in `baggersee_daten.csv` gespeichert (Semikolon-getrennt,
`utf-8-sig`-Kodierung), die im selben Verzeichnis wie `main.py` bzw. die
gebaute `.exe` liegt. Die Datei wird beim ersten Speichern automatisch
angelegt und kann bei Bedarf direkt in Excel geöffnet oder gesichert werden.

## Lokal starten (mit installiertem Python)

```
pip install -r requirements.txt
python main.py
```

## Als eigenständige .exe bauen

```
pip install -r requirements.txt
pyinstaller --onefile --windowed --name BaggerseeVerwaltung ^
    --icon=icon.ico --add-data "icon.ico;." ^
    --collect-all matplotlib --collect-all mplcursors ^
    main.py
```

- `--onefile` erzeugt eine einzelne .exe-Datei.
- `--windowed` unterdrückt das Konsolenfenster (reine GUI-Anwendung).
- `--icon` setzt das Datei-/Taskleisten-Icon der .exe, `--add-data` bündelt
  `icon.ico` zusätzlich mit, damit die Anwendung es zur Laufzeit auch als
  Fenster-Icon setzen kann (siehe `stil.fenstericon_setzen`).
- `--collect-all matplotlib` und `--collect-all mplcursors` stellen sicher,
  dass PyInstaller das Tkinter-Backend und alle Zusatzdateien dieser beiden
  Pakete findet (wird auf manchen Systemen sonst nicht automatisch erkannt).
- Das Ergebnis liegt danach unter `dist\BaggerseeVerwaltung.exe`.

Die fertige .exe legt `baggersee_daten.csv` automatisch neben sich selbst an
– die .exe kann also z. B. auf einen USB-Stick oder in einen beliebigen
Ordner kopiert werden, die Daten wandern mit.

### Empfehlung für Windows-Kompatibilität

Baue die .exe idealerweise auf der gleichen oder einer älteren
Windows-Version, auf der sie später laufen soll (PyInstaller bündelt
Systembibliotheken der Build-Maschine).

## Bedienung

- **Erfassung**: links der Monatskalender mit allen erfassten Tagen
  (● vollständig, ● gelb = unvollständig, ○ kein Eintrag), rechts das
  Eingabeformular. Ein Klick auf einen Tag im Kalender lädt ihn zum
  Bearbeiten oder bereitet einen neuen Eintrag für diesen Tag vor.
  - Feldreihenfolge: Datum, Betrag/Einnahmen, Besucherzahl, Lufttemperatur,
    Wassertemperatur, Öffnungszeiten.
  - Betrag, Temperaturen und Öffnungszeiten dürfen leer bleiben, wenn sie
    noch nicht bekannt sind – der Tag gilt dann als unvollständig (gelb im
    Kalender). Nur Datum und Besucherzahl sind Pflichtfelder.
  - Über "+ Zeitraum hinzufügen" lassen sich mehrere Öffnungszeiträume je
    Tag erfassen, z.B. bei einer Zwangspause wegen schlechten Wetters
    (10:00–14:00 und 16:00–19:00).
  - Monat und Jahr lassen sich über Dropdowns direkt auswählen, um schneller
    durch den Kalender zu springen, statt einzeln über ‹ / › zu blättern.
  - Unterhalb des Kalenders zeigt die **Saisonübersicht** pro Jahr den
    hinterlegten Saisonzeitraum (von–bis) inkl. Bearbeiten sowie die
    Kennzahlen (Besucher gesamt, Einnahmen gesamt, Ø Wassertemperatur) für
    genau diesen Zeitraum. Der Zeitraum wird separat je Jahr gespeichert
    (`baggersee_saisons.csv`) und ist unabhängig von den Tagesdatensätzen.
- **Auswertung**: ein einzelnes Vergleichs-Diagramm, gesteuert über Checkboxen/
  Auswahlfelder:
  - **Zeiträume**: der Gesamtzeitraum über alle Daten, oder einzelne
    hinterlegte Saisons. Mehrere Zeiträume gleichzeitig überlagern eine
    Kennzahl zum Vergleich (X-Achse = Tag/Monat der Saison, damit
    unterschiedliche Startdaten nicht stören).
  - **Werte**: welche Kennzahl(en) angezeigt werden – bei einem einzelnen
    Zeitraum auch mehrere gleichzeitig (dann auf 0–100 % normiert, Tooltip
    zeigt trotzdem den echten Wert). Bei mehreren Zeiträumen ist nur eine
    Kennzahl gleichzeitig möglich (und umgekehrt).
  - **Gruppierung**: Tag / Monat / Jahr – fasst die Werte entsprechend
    zusammen (ersetzt die früheren separaten Tabs "Monatsübersicht" und
    "Saisonübersicht").
  - **Diagrammtyp**: Linie oder Balken – Balken helfen, wenn sich Linien
    mehrerer überlagerter Zeiträume gegenseitig verdecken.

  Das Diagramm hat außerdem eine Zoom-/Pan-Werkzeugleiste und zeigt beim
  Überfahren mit der Maus den genauen Wert als Tooltip an.

## Automatisches Update

Die Anwendung prüft beim Start automatisch (und über den Knopf
"Nach Updates suchen" in der Statusleiste) die
[GitHub Releases](https://github.com/LeviMayer/BaggerseeVerwaltung/releases)
dieses Repositories auf eine neuere Version. Ist eine .exe-Datei in der
neuesten Release als Anhang vorhanden und ihre Versionsnummer höher als die
aktuell installierte, wird gefragt, ob sie heruntergeladen und installiert
werden soll. Der Austausch der laufenden .exe erfolgt über ein kleines
Batch-Skript im Temp-Verzeichnis, das nach dem Beenden der Anwendung die
neue Version an die Stelle der alten kopiert und sie neu startet.

Das automatische Update funktioniert nur in der gebauten `.exe`, nicht beim
Start aus dem Quellcode (`python main.py`).

## Neues Release veröffentlichen

1. Versionsnummer in `baggersee/version.py` erhöhen (z. B. `"1.1.0"`).
2. Änderungen committen und pushen.
3. .exe bauen (siehe oben, mit `--collect-all matplotlib`).
4. Release mit der GitHub CLI veröffentlichen:

   ```
   gh release create v1.1.0 dist/BaggerseeVerwaltung.exe --title "v1.1.0" --notes "Was ist neu..."
   ```

Die Versionsnummer im Tag/Release (`v1.1.0`) muss zur `VERSION` in
`baggersee/version.py` passen, damit der Auto-Updater sie korrekt erkennt.
