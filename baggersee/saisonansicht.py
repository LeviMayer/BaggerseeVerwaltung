"""
Saisonübersicht für ein Kalenderjahr.

Zeigt auf der Erfassungsseite unterhalb des Kalenders den hinterlegten
Saisonzeitraum eines Jahres (z.B. 09.05.–15.09.) an, erlaubt dessen
Bearbeitung und fasst die Kennzahlen (Besucher, Einnahmen, Ø Wassertemperatur)
für diesen Zeitraum zusammen.
"""

from __future__ import annotations

import math
import tkinter as tk
from datetime import date
from tkinter import ttk
from typing import Optional

from . import stil
from .datenhaltung import DatenManager
from .modelle import ValidierungsFehler, formatiere_datum, parse_datum
from .saison import SaisonManager, Saisonzeitraum


class SaisonAnsicht(tk.Frame):
    def __init__(self, parent: tk.Widget, datenmanager: DatenManager, saisonmanager: SaisonManager):
        super().__init__(parent, bg=stil.HINTERGRUND)
        self.datenmanager = datenmanager
        self.saisonmanager = saisonmanager
        self.jahr = date.today().year

        self._aufbauen()
        self.jahr_anzeigen(self.jahr)

    # ---------- Aufbau ----------

    def _aufbauen(self) -> None:
        self.titel_label = tk.Label(
            self, text="", bg=stil.HINTERGRUND, fg=stil.VORDERGRUND, font=stil.SCHRIFT_FETT,
        )
        self.titel_label.pack(anchor="w")

        zeitraum_zeile = tk.Frame(self, bg=stil.HINTERGRUND)
        zeitraum_zeile.pack(anchor="w", pady=(4, 0))

        tk.Label(
            zeitraum_zeile, text="Von:", bg=stil.HINTERGRUND, fg=stil.SEKUNDAER, font=("Segoe UI", 9),
        ).pack(side="left")
        self.eingabe_von = ttk.Entry(zeitraum_zeile, width=10)
        self.eingabe_von.pack(side="left", padx=(4, 10))

        tk.Label(
            zeitraum_zeile, text="Bis:", bg=stil.HINTERGRUND, fg=stil.SEKUNDAER, font=("Segoe UI", 9),
        ).pack(side="left")
        self.eingabe_bis = ttk.Entry(zeitraum_zeile, width=10)
        self.eingabe_bis.pack(side="left", padx=(4, 10))

        ttk.Button(zeitraum_zeile, text="Speichern", command=self._speichern).pack(side="left")

        self.kennzahlen_label = tk.Label(
            self, text="", bg=stil.HINTERGRUND, fg=stil.VORDERGRUND,
            font=("Segoe UI", 9), justify="left", wraplength=340,
        )
        self.kennzahlen_label.pack(anchor="w", pady=(6, 0))

        self.status_label = tk.Label(
            self, text="", bg=stil.HINTERGRUND, fg=stil.FEHLER, font=("Segoe UI", 8),
        )
        self.status_label.pack(anchor="w", pady=(2, 0))

    # ---------- Verhalten ----------

    def jahr_anzeigen(self, jahr: int) -> None:
        """Zeigt den Saisonzeitraum und die Kennzahlen für ein anderes Jahr an."""
        self.jahr = jahr
        self.titel_label.config(text=f"Saison {jahr}")

        zeitraum = self.saisonmanager.fuer_jahr(jahr)
        self.eingabe_von.delete(0, tk.END)
        self.eingabe_bis.delete(0, tk.END)
        if zeitraum:
            self.eingabe_von.insert(0, formatiere_datum(zeitraum.von))
            self.eingabe_bis.insert(0, formatiere_datum(zeitraum.bis))

        self.status_label.config(text="")
        self._kennzahlen_aktualisieren(zeitraum)

    def aktualisieren(self) -> None:
        """Berechnet die Kennzahlen neu, z.B. nachdem ein Tagesdatensatz geändert wurde."""
        self._kennzahlen_aktualisieren(self.saisonmanager.fuer_jahr(self.jahr))

    def _kennzahlen_aktualisieren(self, zeitraum: Optional[Saisonzeitraum]) -> None:
        if zeitraum is None:
            self.kennzahlen_label.config(
                text="Noch kein Saisonzeitraum für dieses Jahr hinterlegt."
            )
            return

        eintraege = self.datenmanager.eintraege_im_zeitraum(zeitraum.von, zeitraum.bis)
        kopf = f"Zeitraum: {formatiere_datum(zeitraum.von)} – {formatiere_datum(zeitraum.bis)}"
        if not eintraege:
            self.kennzahlen_label.config(text=f"{kopf}\nKeine Tagesdaten in diesem Zeitraum erfasst.")
            return

        besucher = sum(e.besucher for e in eintraege)
        einnahmen = sum(0.0 if math.isnan(e.einnahmen) else e.einnahmen for e in eintraege)
        wasser_werte = [e.wassertemperatur for e in eintraege if not math.isnan(e.wassertemperatur)]

        text = (
            f"{kopf}  ({len(eintraege)} Tage erfasst)\n"
            f"Besucher gesamt: {besucher}    Einnahmen gesamt: {einnahmen:.2f} €"
        )
        if wasser_werte:
            avg_wasser = sum(wasser_werte) / len(wasser_werte)
            text += f"    Ø Wassertemperatur: {avg_wasser:.1f} °C"
        self.kennzahlen_label.config(text=text)

    def _speichern(self) -> None:
        try:
            von = parse_datum(self.eingabe_von.get())
            bis = parse_datum(self.eingabe_bis.get())
        except ValidierungsFehler as fehler:
            self.status_label.config(text=str(fehler))
            return
        if von > bis:
            self.status_label.config(text="'Von' muss vor 'Bis' liegen.")
            return

        zeitraum = Saisonzeitraum(jahr=self.jahr, von=von, bis=bis)
        self.saisonmanager.speichern(zeitraum)
        self.status_label.config(text="")
        self._kennzahlen_aktualisieren(zeitraum)
