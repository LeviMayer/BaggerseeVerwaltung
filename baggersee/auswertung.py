"""
Tkinter-Oberfläche für die Auswertung der erfassten Betriebsdaten.

Bietet:
- freie Zeitraumauswahl mit Schnellwahl-Buttons
- eine Zusammenfassung (Summen/Durchschnitte) für den gewählten Zeitraum
- Liniendiagramme für Besucher, Temperaturen und Einnahmen
- eine Monatsübersicht und eine Saisonübersicht über alle Daten
"""

from __future__ import annotations

import math
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from . import stil
from .datenhaltung import DatenManager
from .diagramme import (
    zeichne_besucherverlauf,
    zeichne_einnahmenverlauf,
    zeichne_monatsuebersicht,
    zeichne_saisonuebersicht,
    zeichne_temperaturverlauf,
)
from .modelle import ValidierungsFehler, formatiere_datum, parse_datum


class AuswertungFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, datenmanager: DatenManager):
        super().__init__(parent, padding=10)
        self.datenmanager = datenmanager

        self._zeitraum_leiste_aufbauen()

        self.innerer_notebook = ttk.Notebook(self)
        self.innerer_notebook.pack(fill="both", expand=True, pady=(10, 0))

        self._zeitraum_tab_aufbauen()
        self._monats_tab_aufbauen()
        self._saison_tab_aufbauen()

        # Beim Wechsel auf einen Tab die dortigen Diagramme aktualisieren,
        # damit neu erfasste Daten immer aktuell angezeigt werden.
        self.innerer_notebook.bind("<<NotebookTabChanged>>", lambda e: self._aktueller_tab_aktualisieren())

        self._auswerten()
        self._monatsuebersicht_aktualisieren()
        self._saisonuebersicht_aktualisieren()

    # ---------- Zeitraum-Leiste ----------

    def _zeitraum_leiste_aufbauen(self) -> None:
        leiste = ttk.LabelFrame(self, text="Zeitraum", padding=8)
        leiste.pack(fill="x")

        ttk.Label(leiste, text="Von (TT.MM.JJJJ):").pack(side="left")
        self.eingabe_von = ttk.Entry(leiste, width=12)
        self.eingabe_von.pack(side="left", padx=(4, 12))

        ttk.Label(leiste, text="Bis (TT.MM.JJJJ):").pack(side="left")
        self.eingabe_bis = ttk.Entry(leiste, width=12)
        self.eingabe_bis.pack(side="left", padx=(4, 12))

        ttk.Button(leiste, text="Auswerten", command=self._auswerten).pack(side="left", padx=4)

        trenner = ttk.Separator(leiste, orient="vertical")
        trenner.pack(side="left", fill="y", padx=10)

        ttk.Button(leiste, text="Aktueller Monat", command=self._schnellwahl_monat).pack(side="left", padx=2)
        ttk.Button(leiste, text="Gesamte Saison", command=self._schnellwahl_saison).pack(side="left", padx=2)
        ttk.Button(leiste, text="Letztes Jahr", command=self._schnellwahl_letztes_jahr).pack(side="left", padx=2)

        heute = date.today()
        self._setze_zeitraum(heute.replace(day=1), heute)

    def _setze_zeitraum(self, von: date, bis: date) -> None:
        self.eingabe_von.delete(0, tk.END)
        self.eingabe_von.insert(0, formatiere_datum(von))
        self.eingabe_bis.delete(0, tk.END)
        self.eingabe_bis.insert(0, formatiere_datum(bis))

    def _schnellwahl_monat(self) -> None:
        heute = date.today()
        self._setze_zeitraum(heute.replace(day=1), heute)
        self._auswerten()

    def _schnellwahl_saison(self) -> None:
        alle = self.datenmanager.alle_eintraege()
        if not alle:
            messagebox.showinfo("Keine Daten", "Es sind noch keine Datensätze erfasst.")
            return
        self._setze_zeitraum(alle[0].datum, alle[-1].datum)
        self._auswerten()

    def _schnellwahl_letztes_jahr(self) -> None:
        vorjahr = date.today().year - 1
        self._setze_zeitraum(date(vorjahr, 1, 1), date(vorjahr, 12, 31))
        self._auswerten()

    # ---------- Tab: Zeitraum ----------

    def _zeitraum_tab_aufbauen(self) -> None:
        self.tab_zeitraum = ttk.Frame(self.innerer_notebook)
        self.innerer_notebook.add(self.tab_zeitraum, text="Zeitraum")

        self.zusammenfassung_label = ttk.Label(
            self.tab_zeitraum, text="", justify="left", font=("Segoe UI", 9)
        )
        self.zusammenfassung_label.pack(fill="x", pady=(0, 8))

        self.figur_zeitraum = Figure(figsize=(8, 7), dpi=100, facecolor=stil.HINTERGRUND)
        self.achse_besucher = self.figur_zeitraum.add_subplot(3, 1, 1)
        self.achse_temperatur = self.figur_zeitraum.add_subplot(3, 1, 2)
        self.achse_einnahmen = self.figur_zeitraum.add_subplot(3, 1, 3)
        self.figur_zeitraum.tight_layout(pad=3.0)

        self.canvas_zeitraum = FigureCanvasTkAgg(self.figur_zeitraum, master=self.tab_zeitraum)
        self.canvas_zeitraum.get_tk_widget().configure(bg=stil.HINTERGRUND, highlightthickness=0)
        self.canvas_zeitraum.get_tk_widget().pack(fill="both", expand=True)

    def _auswerten(self) -> None:
        try:
            von = parse_datum(self.eingabe_von.get())
            bis = parse_datum(self.eingabe_bis.get())
        except ValidierungsFehler as fehler:
            messagebox.showerror("Ungültiger Zeitraum", str(fehler))
            return
        if von > bis:
            messagebox.showerror("Ungültiger Zeitraum", "Das Startdatum muss vor dem Enddatum liegen.")
            return

        eintraege = self.datenmanager.eintraege_im_zeitraum(von, bis)

        self._zusammenfassung_aktualisieren(eintraege)

        zeichne_besucherverlauf(self.achse_besucher, eintraege)
        zeichne_temperaturverlauf(self.achse_temperatur, eintraege)
        zeichne_einnahmenverlauf(self.achse_einnahmen, eintraege)
        self.figur_zeitraum.tight_layout(pad=3.0)
        self.canvas_zeitraum.draw()

    def _zusammenfassung_aktualisieren(self, eintraege) -> None:
        if not eintraege:
            self.zusammenfassung_label.config(text="Keine Daten im gewählten Zeitraum.")
            return

        anzahl_tage = len(eintraege)
        summe_besucher = sum(e.besucher for e in eintraege)
        summe_einnahmen = sum(e.einnahmen for e in eintraege)
        avg_besucher = summe_besucher / anzahl_tage
        avg_einnahmen = summe_einnahmen / anzahl_tage

        wasser_werte = [e.wassertemperatur for e in eintraege if not math.isnan(e.wassertemperatur)]
        luft_werte = [e.lufttemperatur for e in eintraege if not math.isnan(e.lufttemperatur)]
        avg_wasser = sum(wasser_werte) / len(wasser_werte) if wasser_werte else math.nan
        avg_luft = sum(luft_werte) / len(luft_werte) if luft_werte else math.nan

        wasser_text = f"{avg_wasser:.1f} °C" if wasser_werte else "keine Daten"
        luft_text = f"{avg_luft:.1f} °C" if luft_werte else "keine Daten"

        text = (
            f"Erfasste Tage: {anzahl_tage}    |    "
            f"Besucher gesamt: {summe_besucher} (Ø {avg_besucher:.1f}/Tag)    |    "
            f"Einnahmen gesamt: {summe_einnahmen:.2f} € (Ø {avg_einnahmen:.2f} €/Tag)    |    "
            f"Ø Wassertemperatur: {wasser_text}    |    "
            f"Ø Lufttemperatur: {luft_text}"
        )
        self.zusammenfassung_label.config(text=text)

    # ---------- Tab: Monatsübersicht ----------

    def _monats_tab_aufbauen(self) -> None:
        self.tab_monat = ttk.Frame(self.innerer_notebook)
        self.innerer_notebook.add(self.tab_monat, text="Monatsübersicht")

        self.figur_monat = Figure(figsize=(8, 7), dpi=100, facecolor=stil.HINTERGRUND)
        self.achse_monat_besucher = self.figur_monat.add_subplot(2, 1, 1)
        self.achse_monat_einnahmen = self.figur_monat.add_subplot(2, 1, 2)
        self.figur_monat.tight_layout(pad=3.0)

        self.canvas_monat = FigureCanvasTkAgg(self.figur_monat, master=self.tab_monat)
        self.canvas_monat.get_tk_widget().configure(bg=stil.HINTERGRUND, highlightthickness=0)
        self.canvas_monat.get_tk_widget().pack(fill="both", expand=True)

    def _monatsuebersicht_aktualisieren(self) -> None:
        alle = self.datenmanager.alle_eintraege()
        zeichne_monatsuebersicht(self.achse_monat_besucher, self.achse_monat_einnahmen, alle)
        self.figur_monat.tight_layout(pad=3.0)
        self.canvas_monat.draw()

    # ---------- Tab: Saisonübersicht ----------

    def _saison_tab_aufbauen(self) -> None:
        self.tab_saison = ttk.Frame(self.innerer_notebook)
        self.innerer_notebook.add(self.tab_saison, text="Saisonübersicht")

        self.figur_saison = Figure(figsize=(8, 7), dpi=100, facecolor=stil.HINTERGRUND)
        self.achse_saison_besucher = self.figur_saison.add_subplot(2, 1, 1)
        self.achse_saison_einnahmen = self.figur_saison.add_subplot(2, 1, 2)
        self.figur_saison.tight_layout(pad=3.0)

        self.canvas_saison = FigureCanvasTkAgg(self.figur_saison, master=self.tab_saison)
        self.canvas_saison.get_tk_widget().configure(bg=stil.HINTERGRUND, highlightthickness=0)
        self.canvas_saison.get_tk_widget().pack(fill="both", expand=True)

    def _saisonuebersicht_aktualisieren(self) -> None:
        alle = self.datenmanager.alle_eintraege()
        zeichne_saisonuebersicht(self.achse_saison_besucher, self.achse_saison_einnahmen, alle)
        self.figur_saison.tight_layout(pad=3.0)
        self.canvas_saison.draw()

    # ---------- Öffentliche Aktualisierung ----------

    def aktualisieren(self) -> None:
        """Wird von main.py aufgerufen, wenn der Auswertungs-Tab aktiviert wird."""
        self._auswerten()
        self._monatsuebersicht_aktualisieren()
        self._saisonuebersicht_aktualisieren()

    def _aktueller_tab_aktualisieren(self) -> None:
        aktueller = self.innerer_notebook.index(self.innerer_notebook.select())
        if aktueller == 0:
            self._auswerten()
        elif aktueller == 1:
            self._monatsuebersicht_aktualisieren()
        elif aktueller == 2:
            self._saisonuebersicht_aktualisieren()
