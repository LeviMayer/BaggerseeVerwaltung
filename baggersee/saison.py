"""
Verwaltung der Saison-Zeiträume je Kalenderjahr.

Eine Saison ist der Zeitraum, in dem der Baggersee in einem Jahr geöffnet
war (z.B. 09.05.–15.09.). Er wird getrennt von den Tagesdatensätzen in
einer eigenen kleinen CSV-Datei gespeichert, damit er unabhängig von
einzelnen Tageseinträgen gepflegt werden kann.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from .datenhaltung import basisverzeichnis
from .modelle import ValidierungsFehler, formatiere_datum, parse_datum

SAISON_DATEINAME = "baggersee_saisons.csv"
SAISON_SPALTEN = ["jahr", "von", "bis"]


@dataclass
class Saisonzeitraum:
    """Der erfasste Öffnungszeitraum eines Kalenderjahres."""

    jahr: int
    von: date
    bis: date


class SaisonManager:
    """Verwaltet das Laden, Speichern und Abfragen der Saisonzeiträume."""

    def __init__(self, pfad: Optional[Path] = None):
        self.pfad = pfad or (basisverzeichnis() / SAISON_DATEINAME)
        self._zeitraeume: dict[int, Saisonzeitraum] = {}
        self._laden()

    def _laden(self) -> None:
        self._zeitraeume.clear()
        if not self.pfad.exists():
            return
        with self.pfad.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for zeile in reader:
                try:
                    jahr = int(zeile["jahr"])
                    von = parse_datum(zeile["von"])
                    bis = parse_datum(zeile["bis"])
                except (KeyError, ValueError, ValidierungsFehler):
                    continue
                self._zeitraeume[jahr] = Saisonzeitraum(jahr=jahr, von=von, bis=bis)

    def _schreiben(self) -> None:
        with self.pfad.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=SAISON_SPALTEN, delimiter=";")
            writer.writeheader()
            for jahr in sorted(self._zeitraeume):
                z = self._zeitraeume[jahr]
                writer.writerow(
                    {"jahr": z.jahr, "von": formatiere_datum(z.von), "bis": formatiere_datum(z.bis)}
                )

    def fuer_jahr(self, jahr: int) -> Optional[Saisonzeitraum]:
        return self._zeitraeume.get(jahr)

    def speichern(self, zeitraum: Saisonzeitraum) -> None:
        self._zeitraeume[zeitraum.jahr] = zeitraum
        self._schreiben()
