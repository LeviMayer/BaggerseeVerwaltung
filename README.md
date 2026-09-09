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
    auswertung.py                Zeitraumauswahl, Zusammenfassung, Tabs
    diagramme.py                 matplotlib-Diagrammfunktionen
    stil.py                       Dunkles Farbschema (ttk-Style)
    updater.py                    Auto-Update über GitHub Releases
    version.py                    Versionsnummer der Anwendung
  import_daten.py             Einmal-/Nachimport historischer CSV-Exporte
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
pyinstaller --onefile --windowed --name BaggerseeVerwaltung main.py
```

- `--onefile` erzeugt eine einzelne .exe-Datei.
- `--windowed` unterdrückt das Konsolenfenster (reine GUI-Anwendung).
- Das Ergebnis liegt danach unter `dist\BaggerseeVerwaltung.exe`.

Die fertige .exe legt `baggersee_daten.csv` automatisch neben sich selbst an
– die .exe kann also z. B. auf einen USB-Stick oder in einen beliebigen
Ordner kopiert werden, die Daten wandern mit.

### Falls der Build mit einem Fehler zu matplotlib/Tkinter abbricht

Auf manchen Systemen erkennt PyInstaller das Tkinter-Backend von matplotlib
nicht automatisch. In diesem Fall hilft:

```
pyinstaller --onefile --windowed --name BaggerseeVerwaltung ^
    --collect-all matplotlib ^
    main.py
```

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
- **Auswertung**: Zeitraum frei wählen oder Schnellwahl nutzen
  (aktueller Monat / gesamte Saison / letztes Jahr). Die drei Unter-Reiter
  zeigen den gewählten Zeitraum im Detail, eine Monatsübersicht und eine
  Saisonübersicht über alle gespeicherten Daten. Jedes Diagramm hat eine
  Zoom-/Pan-Werkzeugleiste und zeigt beim Überfahren mit der Maus den
  genauen Wert als Tooltip an.

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
