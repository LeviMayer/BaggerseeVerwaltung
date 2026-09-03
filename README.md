# Baggersee-Verwaltung

Tkinter-Anwendung zur täglichen Erfassung und Auswertung der Betriebsdaten
eines Baggersees.

## Projektstruktur

```
BaggerseeVerwaltung/
  main.py                    Einstiegspunkt
  baggersee/
    modelle.py                Datenmodell (Tagesdatensatz) + Validierung
    datenhaltung.py            CSV-Persistenz, CRUD (DatenManager)
    eingabe.py                  Eingabemaske (Erfassen/Bearbeiten/Löschen)
    auswertung.py                Zeitraumauswahl, Zusammenfassung, Tabs
    diagramme.py                 matplotlib-Diagrammfunktionen
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

- **Erfassung**: links die Liste aller erfassten Tage, rechts das
  Eingabeformular. "Neuer Eintrag" leert das Formular, ein Klick auf einen
  Eintrag in der Liste lädt ihn zum Bearbeiten, "Löschen" entfernt den
  ausgewählten Tag.
- **Auswertung**: Zeitraum frei wählen oder Schnellwahl nutzen
  (aktueller Monat / gesamte Saison / letztes Jahr). Die drei Unter-Reiter
  zeigen den gewählten Zeitraum im Detail, eine Monatsübersicht und eine
  Saisonübersicht über alle gespeicherten Daten.
