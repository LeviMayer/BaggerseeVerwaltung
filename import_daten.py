"""
Einmaliger Import historischer Tagesdaten aus einer CSV-Exportdatei in die
Baggersee-Verwaltung.

Erwartetes Quellformat (Semikolon-getrennt):
Datum;Wochentag;Besucher;Einnahmen_Euro;Wassertemperatur_max_C;
Lufttemperatur_max_C;Oeffnung_von;Oeffnung_bis;Oeffnungsstunden

Die Spalten "Wochentag" und "Oeffnungsstunden" werden nicht übernommen, da sie
sich aus dem Datum bzw. den Öffnungszeiten ergeben.

Aufruf:
    python import_daten.py <pfad_zur_csv>
"""

from __future__ import annotations

import csv
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from baggersee.datenhaltung import DatenManager
from baggersee.modelle import Tagesdatensatz

# Werte, deren Betrag diese Schwelle überschreiten, sind mit hoher
# Wahrscheinlichkeit ein fehlendes Dezimaltrennzeichen (z.B. "212" statt "21.2").
TEMPERATUR_KORREKTUR_SCHWELLE = 45.0


def _text(wert: Optional[str]) -> str:
    return wert.strip() if wert else ""


def _temperatur(rohwert: Optional[str], feldname: str, datum_text: str, warnungen: list[str]) -> float:
    """Fehlende Messwerte werden als NaN gespeichert, damit der Tag im Kalender
    als unvollständig erkennbar bleibt, statt einen erfundenen Wert vorzutäuschen."""
    text = _text(rohwert)
    if not text:
        warnungen.append(f"{datum_text}: {feldname} fehlt.")
        return math.nan

    wert = float(text.replace(",", "."))
    if abs(wert) > TEMPERATUR_KORREKTUR_SCHWELLE:
        korrigiert = wert / 10
        warnungen.append(
            f"{datum_text}: {feldname}={wert} wirkt wie ein fehlendes Komma "
            f"– auf {korrigiert} korrigiert."
        )
        return korrigiert
    return wert


def importiere(pfad: Path) -> None:
    dm = DatenManager()
    warnungen: list[str] = []
    importiert = 0
    uebersprungen = 0

    with pfad.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for zeile in reader:
            datum_text = _text(zeile.get("Datum"))
            if not datum_text:
                continue

            try:
                datum: date = datetime.strptime(datum_text, "%Y-%m-%d").date()
                besucher = int(_text(zeile.get("Besucher")) or 0)
                einnahmen = float(_text(zeile.get("Einnahmen_Euro")).replace(",", ".") or 0.0)
            except ValueError as fehler:
                warnungen.append(f"{datum_text}: Zeile übersprungen ({fehler}).")
                uebersprungen += 1
                continue

            wassertemp = _temperatur(zeile.get("Wassertemperatur_max_C"), "Wassertemperatur", datum_text, warnungen)
            lufttemp = _temperatur(zeile.get("Lufttemperatur_max_C"), "Lufttemperatur", datum_text, warnungen)

            datensatz = Tagesdatensatz(
                datum=datum,
                besucher=besucher,
                wassertemperatur=wassertemp,
                lufttemperatur=lufttemp,
                einnahmen=einnahmen,
                oeffnung_von=_text(zeile.get("Oeffnung_von")),
                oeffnung_bis=_text(zeile.get("Oeffnung_bis")),
            )
            dm.speichern(datensatz, ist_neu=False)
            importiert += 1

    print(f"{importiert} Tagesdatensätze importiert.")
    if uebersprungen:
        print(f"{uebersprungen} Zeilen übersprungen.")
    if warnungen:
        print(f"\n{len(warnungen)} Hinweise:")
        for w in warnungen:
            print(f" - {w}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Aufruf: python import_daten.py <pfad_zur_csv>")
        sys.exit(1)
    importiere(Path(sys.argv[1]))
