"""
Tkinter-Oberfläche zur täglichen Erfassung der Betriebsdaten.

Zeigt links einen Monatskalender mit allen bisher erfassten Tagen und rechts
eine Eingabemaske zum Anlegen, Bearbeiten und Löschen einzelner Tagesdatensätze.
"""

from __future__ import annotations

import math
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import Optional

from . import stil
from .datenhaltung import DatenManager
from .kalender import MonatsKalender
from .modelle import (
    Tagesdatensatz,
    ValidierungsFehler,
    erstelle_tagesdatensatz,
    formatiere_datum,
)


def _formatiere_zahl(wert: float) -> str:
    """Zeigt fehlende Messwerte (NaN, z.B. aus einem Import) als leeres Feld an."""
    return "" if math.isnan(wert) else str(wert)


class EingabeFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, datenmanager: DatenManager):
        super().__init__(parent, padding=10)
        self.datenmanager = datenmanager
        self.bearbeiteter_tag: Optional[date] = None  # None => neuer Eintrag

        self._aufbauen()
        self.formular_leeren()

    # ---------- Aufbau der Oberfläche ----------

    def _aufbauen(self) -> None:
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._kalender_aufbauen()
        self._formular_aufbauen()

    def _kalender_aufbauen(self) -> None:
        rahmen = tk.Frame(self, bg=stil.HINTERGRUND, padx=6, pady=6)
        rahmen.grid(row=0, column=0, sticky="n", padx=(0, 10))

        tk.Label(
            rahmen, text="Erfasste Tage", bg=stil.HINTERGRUND,
            fg=stil.VORDERGRUND, font=stil.SCHRIFT_TITEL,
        ).pack(anchor="w", padx=4, pady=(0, 6))

        self.kalender = MonatsKalender(rahmen, self.datenmanager, self._tag_ausgewaehlt)
        self.kalender.pack()

        legende = tk.Frame(rahmen, bg=stil.HINTERGRUND)
        legende.pack(anchor="w", padx=4, pady=(6, 0))
        for farbe, text in (
            (stil.AKZENT, "vollständig"),
            (stil.GELB, "unvollständig"),
            (stil.PANEL_HELL, "kein Eintrag"),
        ):
            eintrag = tk.Frame(legende, bg=stil.HINTERGRUND)
            eintrag.pack(side="left", padx=(0, 12))
            tk.Label(
                eintrag, text="●", bg=stil.HINTERGRUND, fg=farbe, font=("Segoe UI", 10)
            ).pack(side="left")
            tk.Label(
                eintrag, text=f" {text}", bg=stil.HINTERGRUND, fg=stil.GEDIMMT, font=("Segoe UI", 8)
            ).pack(side="left")

    def _formular_aufbauen(self) -> None:
        rahmen = ttk.LabelFrame(self, text="Tagesdatensatz", padding=8)
        rahmen.grid(row=0, column=1, sticky="n")

        self.eingabe_datum = self._formularfeld(rahmen, 0, "Datum (TT.MM.JJJJ):")
        self.eingabe_einnahmen = self._formularfeld(rahmen, 1, "Betrag / Einnahmen (€):")
        self.eingabe_besucher = self._formularfeld(rahmen, 2, "Besucherzahl:")
        self.eingabe_lufttemp = self._formularfeld(rahmen, 3, "Lufttemperatur (°C):")
        self.eingabe_wassertemp = self._formularfeld(rahmen, 4, "Wassertemperatur (°C):")

        self._oeffnungszeiten_aufbauen(rahmen, zeile=5)

        knopf_rahmen = ttk.Frame(rahmen)
        knopf_rahmen.grid(row=6, column=0, columnspan=2, pady=(12, 0), sticky="ew")

        ttk.Button(knopf_rahmen, text="Neuer Eintrag", command=self.formular_leeren).pack(
            side="left", padx=2
        )
        ttk.Button(knopf_rahmen, text="Speichern", command=self._speichern).pack(
            side="left", padx=2
        )
        ttk.Button(knopf_rahmen, text="Löschen", command=self._loeschen).pack(
            side="left", padx=2
        )

        self.status_label = ttk.Label(rahmen, style="Fehler.TLabel", text="", wraplength=260)
        self.status_label.grid(row=7, column=0, columnspan=2, pady=(8, 0), sticky="w")

    def _formularfeld(self, parent: tk.Widget, zeile: int, beschriftung: str) -> ttk.Entry:
        ttk.Label(parent, text=beschriftung).grid(row=zeile, column=0, sticky="w", pady=3)
        eingabe = ttk.Entry(parent, width=22)
        eingabe.grid(row=zeile, column=1, sticky="w", pady=3, padx=(6, 0))
        return eingabe

    def _oeffnungszeiten_aufbauen(self, parent: tk.Widget, zeile: int) -> None:
        """Baut den Bereich für (mehrere) Öffnungszeiträume je Tag auf.

        Ermöglicht z.B. bei einer Zwangspause wegen schlechten Wetters, einen
        zweiten Zeitraum (nach der Wiedereröffnung) zu erfassen.
        """
        ttk.Label(parent, text="Öffnungszeiten (HH:MM):").grid(
            row=zeile, column=0, sticky="nw", pady=3
        )

        wrapper = ttk.Frame(parent)
        wrapper.grid(row=zeile, column=1, sticky="w", pady=3, padx=(6, 0))

        self.oeff_container = ttk.Frame(wrapper)
        self.oeff_container.pack(anchor="w")
        self.zeitraum_zeilen: list[tuple[ttk.Frame, ttk.Entry, ttk.Entry]] = []

        ttk.Button(
            wrapper, text="+ Zeitraum hinzufügen", command=lambda: self._zeitraum_zeile_hinzufuegen()
        ).pack(anchor="w", pady=(4, 0))

    def _zeitraum_zeile_hinzufuegen(self, von: str = "", bis: str = "") -> None:
        zeile = ttk.Frame(self.oeff_container)
        zeile.pack(anchor="w", pady=2)

        von_eingabe = ttk.Entry(zeile, width=7)
        von_eingabe.insert(0, von)
        von_eingabe.pack(side="left")

        ttk.Label(zeile, text=" – ").pack(side="left")

        bis_eingabe = ttk.Entry(zeile, width=7)
        bis_eingabe.insert(0, bis)
        bis_eingabe.pack(side="left")

        ttk.Button(
            zeile, text="×", width=2, command=lambda: self._zeitraum_zeile_entfernen(zeile)
        ).pack(side="left", padx=(6, 0))

        self.zeitraum_zeilen.append((zeile, von_eingabe, bis_eingabe))

    def _zeitraum_zeile_entfernen(self, zeile: ttk.Frame) -> None:
        self.zeitraum_zeilen = [z for z in self.zeitraum_zeilen if z[0] is not zeile]
        zeile.destroy()
        if not self.zeitraum_zeilen:
            self._zeitraum_zeile_hinzufuegen()

    def _zeitraeume_zuruecksetzen(self, zeitraeume: list[tuple[str, str]]) -> None:
        for zeile, _, _ in list(self.zeitraum_zeilen):
            zeile.destroy()
        self.zeitraum_zeilen = []
        if zeitraeume:
            for von, bis in zeitraeume:
                self._zeitraum_zeile_hinzufuegen(von, bis)
        else:
            self._zeitraum_zeile_hinzufuegen()

    # ---------- Verhalten ----------

    def formular_leeren(self) -> None:
        """Setzt das Formular für die Eingabe eines neuen Tages zurück."""
        self.bearbeiteter_tag = None
        for feld in (
            self.eingabe_datum,
            self.eingabe_besucher,
            self.eingabe_wassertemp,
            self.eingabe_lufttemp,
            self.eingabe_einnahmen,
        ):
            feld.delete(0, tk.END)
        self.eingabe_datum.insert(0, formatiere_datum(date.today()))
        self._zeitraeume_zuruecksetzen([])
        self.status_label.config(text="")

    def _tag_ausgewaehlt(self, tag: date) -> None:
        """Wird aufgerufen, wenn im Kalender ein Tag angeklickt wurde."""
        e = self.datenmanager.eintrag_fuer_datum(tag)
        if e is None:
            self.formular_leeren()
            self.eingabe_datum.delete(0, tk.END)
            self.eingabe_datum.insert(0, formatiere_datum(tag))
            return
        self.bearbeiteter_tag = e.datum

        felder_werte = [
            (self.eingabe_datum, formatiere_datum(e.datum)),
            (self.eingabe_einnahmen, _formatiere_zahl(e.einnahmen)),
            (self.eingabe_besucher, str(e.besucher)),
            (self.eingabe_lufttemp, _formatiere_zahl(e.lufttemperatur)),
            (self.eingabe_wassertemp, _formatiere_zahl(e.wassertemperatur)),
        ]
        for feld, wert in felder_werte:
            feld.delete(0, tk.END)
            feld.insert(0, wert)
        self._zeitraeume_zuruecksetzen(e.oeffnungszeiten)
        self.status_label.config(text="")

    def _speichern(self) -> None:
        zeitraum_texte = [(v.get(), b.get()) for _, v, b in self.zeitraum_zeilen]
        try:
            datensatz = erstelle_tagesdatensatz(
                self.eingabe_datum.get(),
                self.eingabe_einnahmen.get(),
                self.eingabe_besucher.get(),
                self.eingabe_lufttemp.get(),
                self.eingabe_wassertemp.get(),
                zeitraum_texte,
            )
        except ValidierungsFehler as fehler:
            self.status_label.config(text=str(fehler))
            return

        # Wird ein bestehender Tag bearbeitet, aber das Datum geändert,
        # behandeln wir das wie einen neuen Eintrag unter dem alten Datum entfernen.
        ist_neu = self.bearbeiteter_tag is None
        try:
            if not ist_neu and datensatz.datum != self.bearbeiteter_tag:
                self.datenmanager.loeschen(self.bearbeiteter_tag)
                ist_neu = True
            self.datenmanager.speichern(datensatz, ist_neu=ist_neu)
        except ValueError as fehler:
            self.status_label.config(text=str(fehler))
            return

        self.kalender.zu_monat_springen(datensatz.datum)
        self.formular_leeren()
        messagebox.showinfo("Gespeichert", f"Eintrag für {formatiere_datum(datensatz.datum)} gespeichert.")

    def _loeschen(self) -> None:
        if self.bearbeiteter_tag is None:
            messagebox.showwarning(
                "Kein Eintrag gewählt", "Bitte zuerst einen erfassten Tag im Kalender anklicken."
            )
            return
        d = self.bearbeiteter_tag
        if not messagebox.askyesno(
            "Löschen bestätigen", f"Eintrag für {formatiere_datum(d)} wirklich löschen?"
        ):
            return
        self.datenmanager.loeschen(d)
        self.kalender.aktualisieren()
        self.formular_leeren()
