"""
Datenhaltung für die Baggersee-Verwaltung.

Speichert die Tagesdatensätze in einer lokalen CSV-Datei, die im selben
Verzeichnis wie die .exe (bzw. das Skript) liegt. So kann die Datei einfach
gesichert, kopiert oder in Excel geöffnet werden.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from .modelle import Tagesdatensatz, formatiere_datum, parse_datum

CSV_DATEINAME = "baggersee_daten.csv"
CSV_SPALTEN = [
    "datum",
    "besucher",
    "wassertemperatur",
    "lufttemperatur",
    "einnahmen",
    "oeffnung_von",
    "oeffnung_bis",
]


def basisverzeichnis() -> Path:
    """
    Liefert das Verzeichnis, in dem die Datendatei abgelegt werden soll.

    Bei einer mit PyInstaller gebauten .exe liegt das Datenverzeichnis neben
    der .exe (nicht im temporären Entpackungsordner), im normalen
    Python-Betrieb neben diesem Skript.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


class DatenManager:
    """Verwaltet das Laden, Speichern und Ändern der Tagesdatensätze."""

    def __init__(self, pfad: Optional[Path] = None):
        self.pfad = pfad or (basisverzeichnis() / CSV_DATEINAME)
        self._eintraege: dict[date, Tagesdatensatz] = {}
        self._laden()

    # ---------- Laden / Speichern ----------

    def _laden(self) -> None:
        """Liest alle Datensätze aus der CSV-Datei ein, falls vorhanden."""
        self._eintraege.clear()
        if not self.pfad.exists():
            return

        with self.pfad.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for zeile in reader:
                try:
                    datensatz = Tagesdatensatz(
                        datum=parse_datum(zeile["datum"]),
                        besucher=int(zeile["besucher"]),
                        wassertemperatur=float(zeile["wassertemperatur"]),
                        lufttemperatur=float(zeile["lufttemperatur"]),
                        einnahmen=float(zeile["einnahmen"]),
                        oeffnung_von=zeile["oeffnung_von"],
                        oeffnung_bis=zeile["oeffnung_bis"],
                    )
                except (KeyError, ValueError):
                    # Fehlerhafte Zeile überspringen, damit ein einzelner
                    # kaputter Datensatz nicht den gesamten Import blockiert
                    continue
                self._eintraege[datensatz.datum] = datensatz

    def _schreiben(self) -> None:
        """Schreibt alle Datensätze sortiert nach Datum zurück in die CSV-Datei."""
        with self.pfad.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_SPALTEN, delimiter=";")
            writer.writeheader()
            for d in sorted(self._eintraege.keys()):
                e = self._eintraege[d]
                writer.writerow(
                    {
                        "datum": formatiere_datum(e.datum),
                        "besucher": e.besucher,
                        "wassertemperatur": e.wassertemperatur,
                        "lufttemperatur": e.lufttemperatur,
                        "einnahmen": e.einnahmen,
                        "oeffnung_von": e.oeffnung_von,
                        "oeffnung_bis": e.oeffnung_bis,
                    }
                )

    # ---------- Abfragen ----------

    def alle_eintraege(self) -> list[Tagesdatensatz]:
        """Liefert alle Datensätze, sortiert nach Datum (aufsteigend)."""
        return [self._eintraege[d] for d in sorted(self._eintraege.keys())]

    def eintrag_fuer_datum(self, d: date) -> Optional[Tagesdatensatz]:
        return self._eintraege.get(d)

    def eintraege_im_zeitraum(self, von: date, bis: date) -> list[Tagesdatensatz]:
        """Liefert alle Datensätze im Zeitraum [von, bis] (inklusive)."""
        return [
            self._eintraege[d]
            for d in sorted(self._eintraege.keys())
            if von <= d <= bis
        ]

    # ---------- Ändern ----------

    def speichern(self, datensatz: Tagesdatensatz, ist_neu: bool) -> None:
        """
        Fügt einen neuen Datensatz hinzu oder aktualisiert einen bestehenden.

        Bei einem neuen Datensatz wird geprüft, dass für das Datum noch kein
        Eintrag existiert, um versehentliches Überschreiben zu vermeiden.
        """
        if ist_neu and datensatz.datum in self._eintraege:
            raise ValueError(
                f"Für den {formatiere_datum(datensatz.datum)} existiert bereits "
                "ein Eintrag. Bitte über die Liste bearbeiten."
            )
        self._eintraege[datensatz.datum] = datensatz
        self._schreiben()

    def loeschen(self, d: date) -> None:
        """Entfernt den Datensatz für das angegebene Datum, falls vorhanden."""
        if d in self._eintraege:
            del self._eintraege[d]
            self._schreiben()
