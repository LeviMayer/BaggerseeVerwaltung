"""
Moderne Monatskalender-Ansicht für die Tageserfassung.

Zeigt einen Monat als Raster mit einem Kreis je Tag: ausgefüllt mit Häkchen,
wenn für den Tag bereits ein Datensatz erfasst wurde, sonst leer. Ein Klick
auf einen Tag wählt ihn zur Bearbeitung bzw. Neuanlage aus.
"""

from __future__ import annotations

import calendar
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk
from typing import Callable, Optional

from . import stil
from .datenhaltung import DatenManager
from .modelle import ist_unvollstaendig

MONATSNAMEN = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]
WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


class MonatsKalender(tk.Frame):
    """Kompakte, dunkel gehaltene Kalenderkachel mit Monatsnavigation."""

    HINTERGRUND = stil.HINTERGRUND
    VORDERGRUND = stil.VORDERGRUND
    GEDIMMT = stil.GEDIMMT
    AKZENT = stil.AKZENT
    GELB = stil.GELB
    KREIS_LEER = stil.PANEL_HELL
    WOCHENTAG_FARBE = stil.SEKUNDAER

    ZELLEN_BREITE = 62
    ZELLEN_HOEHE = 54
    KREIS_RADIUS = 15

    def __init__(
        self,
        parent: tk.Widget,
        datenmanager: DatenManager,
        on_tag_ausgewaehlt: Callable[[date], None],
        on_ansicht_geaendert: Optional[Callable[[int, int], None]] = None,
    ):
        super().__init__(parent, bg=self.HINTERGRUND)
        self.datenmanager = datenmanager
        self.on_tag_ausgewaehlt = on_tag_ausgewaehlt
        self.on_ansicht_geaendert = on_ansicht_geaendert

        heute = date.today()
        self.jahr = heute.year
        self.monat = heute.month
        self.ausgewaehlter_tag: Optional[date] = None
        self.tage: list[list[date]] = []
        self.zellen: list[list[tk.Canvas]] = []

        self._kopf_aufbauen()
        self._wochentage_aufbauen()
        self._raster_aufbauen()
        self.aktualisieren()

    # ---------- Hilfsfunktionen ----------

    def _jahresbereich(self) -> list[int]:
        """Jahre für die Jahresauswahl: alle Jahre mit Daten, plus etwas Rand."""
        jahre_in_daten = {e.datum.year for e in self.datenmanager.alle_eintraege()}
        heute_jahr = date.today().year
        jahr_min = min(jahre_in_daten, default=heute_jahr) - 1
        jahr_max = max(jahre_in_daten, default=heute_jahr) + 3
        jahr_min = min(jahr_min, heute_jahr)
        return list(range(jahr_min, jahr_max + 1))

    # ---------- Aufbau ----------

    def _kopf_aufbauen(self) -> None:
        kopf = tk.Frame(self, bg=self.HINTERGRUND)
        kopf.pack(fill="x", pady=(0, 6))
        kopf.columnconfigure(0, weight=1)
        kopf.columnconfigure(3, weight=1)

        zurueck = tk.Label(
            kopf, text="‹", bg=self.HINTERGRUND, fg=self.VORDERGRUND,
            font=("Segoe UI", 14), cursor="hand2",
        )
        zurueck.grid(row=0, column=0, sticky="e", padx=6)
        zurueck.bind("<Button-1>", lambda _e: self._monat_wechseln(-1))

        self.monat_var = tk.StringVar()
        monat_auswahl = ttk.Combobox(
            kopf, textvariable=self.monat_var, values=MONATSNAMEN,
            width=10, state="readonly", font=("Segoe UI", 10, "bold"),
        )
        monat_auswahl.grid(row=0, column=1, padx=(0, 4))
        monat_auswahl.bind("<<ComboboxSelected>>", self._auswahl_geaendert)

        self.jahr_var = tk.StringVar()
        self.jahr_auswahl = ttk.Combobox(
            kopf, textvariable=self.jahr_var, width=6,
            state="readonly", font=("Segoe UI", 10, "bold"),
        )
        self.jahr_auswahl.grid(row=0, column=2, padx=(4, 0))
        self.jahr_auswahl.bind("<<ComboboxSelected>>", self._auswahl_geaendert)

        vor = tk.Label(
            kopf, text="›", bg=self.HINTERGRUND, fg=self.VORDERGRUND,
            font=("Segoe UI", 14), cursor="hand2",
        )
        vor.grid(row=0, column=3, sticky="w", padx=6)
        vor.bind("<Button-1>", lambda _e: self._monat_wechseln(1))

    def _wochentage_aufbauen(self) -> None:
        zeile = tk.Frame(self, bg=self.HINTERGRUND)
        zeile.pack()
        for c, name in enumerate(WOCHENTAGE):
            tk.Label(
                zeile, text=name, width=4, bg=self.HINTERGRUND,
                fg=self.WOCHENTAG_FARBE, font=("Segoe UI", 9, "bold"),
            ).grid(row=0, column=c)

    def _raster_aufbauen(self) -> None:
        raster = tk.Frame(self, bg=self.HINTERGRUND)
        raster.pack()
        for r in range(6):
            zeile: list[tk.Canvas] = []
            for c in range(7):
                canvas = tk.Canvas(
                    raster, width=self.ZELLEN_BREITE, height=self.ZELLEN_HOEHE,
                    bg=self.HINTERGRUND, highlightthickness=0, cursor="hand2",
                )
                canvas.grid(row=r, column=c)
                canvas.bind("<Button-1>", lambda _e, rr=r, cc=c: self._zelle_geklickt(rr, cc))
                zeile.append(canvas)
            self.zellen.append(zeile)

    # ---------- Datenermittlung ----------

    def _wochen_holen(self) -> list[list[date]]:
        wochen = calendar.Calendar(firstweekday=0).monthdatescalendar(self.jahr, self.monat)
        while len(wochen) < 6:
            letzter_tag = wochen[-1][-1]
            wochen.append([letzter_tag + timedelta(days=i) for i in range(1, 8)])
        return wochen

    # ---------- Zeichnen ----------

    def aktualisieren(self) -> None:
        """Zeichnet den aktuell gewählten Monat neu (z.B. nach Datenänderung)."""
        self.jahr_auswahl.configure(values=[str(j) for j in self._jahresbereich()])
        self.monat_var.set(MONATSNAMEN[self.monat - 1])
        self.jahr_var.set(str(self.jahr))

        self.tage = self._wochen_holen()
        heute = date.today()
        for r, woche in enumerate(self.tage):
            for c, tag in enumerate(woche):
                self._zelle_zeichnen(r, c, tag, heute)

        if self.on_ansicht_geaendert is not None:
            self.on_ansicht_geaendert(self.jahr, self.monat)

    def _zelle_zeichnen(self, r: int, c: int, tag: date, heute: date) -> None:
        canvas = self.zellen[r][c]
        canvas.delete("all")

        im_monat = tag.month == self.monat
        eintrag = self.datenmanager.eintrag_fuer_datum(tag)
        hat_eintrag = eintrag is not None
        unvollstaendig = hat_eintrag and ist_unvollstaendig(eintrag)
        ist_heute = tag == heute

        if ist_heute:
            zahl_farbe = self.AKZENT
        elif im_monat:
            zahl_farbe = self.VORDERGRUND
        else:
            zahl_farbe = self.GEDIMMT
        zahl_font = ("Segoe UI", 10, "bold" if ist_heute else "normal")
        canvas.create_text(
            self.ZELLEN_BREITE / 2, 12, text=str(tag.day), fill=zahl_farbe, font=zahl_font,
        )

        cx, cy, rad = self.ZELLEN_BREITE / 2, 36, self.KREIS_RADIUS
        if unvollstaendig:
            kreis_farbe = self.GELB
        elif hat_eintrag:
            kreis_farbe = self.AKZENT
        else:
            kreis_farbe = self.KREIS_LEER
        canvas.create_oval(cx - rad, cy - rad, cx + rad, cy + rad, fill=kreis_farbe, outline="")

        if hat_eintrag:
            canvas.create_line(cx - 6, cy, cx - 2, cy + 5, fill="white", width=2, capstyle="round")
            canvas.create_line(cx - 2, cy + 5, cx + 7, cy - 6, fill="white", width=2, capstyle="round")

    # ---------- Interaktion ----------

    def _zelle_geklickt(self, r: int, c: int) -> None:
        tag = self.tage[r][c]
        self.ausgewaehlter_tag = tag
        if tag.month != self.monat:
            self.jahr, self.monat = tag.year, tag.month
            self.aktualisieren()
        self.on_tag_ausgewaehlt(tag)

    def _auswahl_geaendert(self, _event=None) -> None:
        """Reagiert auf die Monats-/Jahresauswahl über die Dropdowns."""
        try:
            self.monat = MONATSNAMEN.index(self.monat_var.get()) + 1
            self.jahr = int(self.jahr_var.get())
        except (ValueError, IndexError):
            return
        self.aktualisieren()

    def _monat_wechseln(self, delta: int) -> None:
        monatsindex = self.monat - 1 + delta
        self.jahr += monatsindex // 12
        self.monat = monatsindex % 12 + 1
        self.aktualisieren()

    def zu_monat_springen(self, tag: date) -> None:
        """Wechselt die Ansicht zu dem Monat, in dem `tag` liegt, und zeichnet neu."""
        self.jahr, self.monat = tag.year, tag.month
        self.aktualisieren()
