"""
Tkinter-Oberfläche für die Auswertung der erfassten Betriebsdaten.

Ein einzelnes Vergleichs-Diagramm, gesteuert über Checkboxen/Auswahlfelder:
- Zeiträume: der Gesamtzeitraum über alle Daten, oder einzelne hinterlegte
  Saisons (siehe Saisonübersicht auf der Erfassungsseite). Mehrere Zeiträume
  gleichzeitig überlagern eine Kennzahl zum Vergleich (X-Achse = Tag/Monat
  der Saison, damit unterschiedliche Startdaten nicht stören).
- Werte: welche Kennzahlen angezeigt werden (bei einem einzelnen Zeitraum
  auch mehrere gleichzeitig, dann auf 0–100 % normiert).
- Gruppierung: Tag / Monat / Jahr (ersetzt die früheren separaten Tabs
  "Monatsübersicht" und "Saisonübersicht").
- Diagrammtyp: Linie oder Balken (Balken hilft, wenn sich Linien mehrerer
  überlagerter Zeiträume gegenseitig verdecken).
"""

from __future__ import annotations

import math
import tkinter as tk
from collections import defaultdict
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import stil
from .datenhaltung import DatenManager
from .diagramme import (
    METRIK_EINHEIT,
    METRIK_FARBE,
    METRIK_LABEL,
    MONATSNAMEN,
    ZEITRAUM_FARBEN,
    ChartReihe,
    wert_fuer_metrik,
    zeichne_vergleich,
)
from .saison import SaisonManager

WERT_REIHENFOLGE = ("besucher", "wasser", "luft", "einnahmen")
# Kennzahlen, die bei Monat/Jahr-Gruppierung gemittelt statt summiert werden.
MITTELWERT_METRIKEN = {"wasser", "luft"}


class AuswertungFrame(ttk.Frame):
    def __init__(self, parent: tk.Widget, datenmanager: DatenManager, saisonmanager: SaisonManager):
        super().__init__(parent, padding=10)
        self.datenmanager = datenmanager
        self.saisonmanager = saisonmanager
        self.zeitraum_vars: dict[str, tk.BooleanVar] = {}
        self.wert_vars: dict[str, tk.BooleanVar] = {}
        self.gruppierung_var = tk.StringVar(value="tag")
        self.diagrammtyp_var = tk.StringVar(value="linie")

        self._steuerung_aufbauen()

        self.zusammenfassung_label = ttk.Label(self, text="", justify="left", font=("Segoe UI", 9))
        self.zusammenfassung_label.pack(fill="x", pady=(0, 8))

        self.figur = Figure(figsize=(8, 6), dpi=100, facecolor=stil.HINTERGRUND)
        self.achse = self.figur.add_subplot(1, 1, 1)
        self.figur.tight_layout(pad=3.0)
        self.canvas = self._canvas_mit_toolbar_einbetten(self.figur, self)

        self._zeitraum_checkboxen_aktualisieren()
        self._neu_zeichnen()

    # ---------- Aufbau ----------

    def _canvas_mit_toolbar_einbetten(self, figur: Figure, parent: tk.Widget) -> FigureCanvasTkAgg:
        """Bettet eine Figure inklusive Navigations-Toolbar (Zoom/Pan/Speichern) ein.

        Die Toolbar wird bewusst VOR dem Canvas gepackt: Der Canvas nutzt
        fill="both", expand=True und würde sonst bereits den gesamten Platz
        beanspruchen, sodass für die darunterliegende Toolbar keiner mehr
        übrig bliebe (siehe die Statusleiste in main.py für denselben Fall).
        """
        canvas = FigureCanvasTkAgg(figur, master=parent)
        canvas.get_tk_widget().configure(bg=stil.HINTERGRUND, highlightthickness=0)

        toolbar = NavigationToolbar2Tk(canvas, parent, pack_toolbar=False)
        toolbar.update()
        stil.dunkle_toolbar(toolbar)
        toolbar.pack(side="bottom", fill="x")

        canvas.get_tk_widget().pack(fill="both", expand=True)
        return canvas

    def _steuerung_aufbauen(self) -> None:
        steuerung = ttk.LabelFrame(self, text="Anzeige", padding=8)
        steuerung.pack(fill="x", pady=(0, 8))
        steuerung.columnconfigure(1, weight=1)

        ttk.Label(steuerung, text="Zeiträume:").grid(row=0, column=0, sticky="nw", padx=(0, 10), pady=2)
        self.zeitraum_checkbox_frame = ttk.Frame(steuerung)
        self.zeitraum_checkbox_frame.grid(row=0, column=1, sticky="w", pady=2)

        ttk.Label(steuerung, text="Werte:").grid(row=1, column=0, sticky="nw", padx=(0, 10), pady=2)
        werte_frame = ttk.Frame(steuerung)
        werte_frame.grid(row=1, column=1, sticky="w", pady=2)
        for schluessel in WERT_REIHENFOLGE:
            self.wert_vars[schluessel] = tk.BooleanVar(value=(schluessel == "besucher"))
            ttk.Checkbutton(
                werte_frame, text=METRIK_LABEL[schluessel], variable=self.wert_vars[schluessel],
                command=lambda: self._checkbox_geaendert("wert"),
            ).pack(side="left", padx=(0, 12))

        ttk.Separator(steuerung, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=6)

        ttk.Label(steuerung, text="Gruppierung:").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=2)
        gruppierung_frame = ttk.Frame(steuerung)
        gruppierung_frame.grid(row=3, column=1, sticky="w", pady=2)
        for wert, text in (("tag", "Tag"), ("monat", "Monat"), ("jahr", "Jahr")):
            ttk.Radiobutton(
                gruppierung_frame, text=text, value=wert, variable=self.gruppierung_var,
                command=self._neu_zeichnen,
            ).pack(side="left", padx=(0, 12))

        ttk.Label(steuerung, text="Diagrammtyp:").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=2)
        diagrammtyp_frame = ttk.Frame(steuerung)
        diagrammtyp_frame.grid(row=4, column=1, sticky="w", pady=2)
        for wert, text in (("linie", "Linie"), ("balken", "Balken")):
            ttk.Radiobutton(
                diagrammtyp_frame, text=text, value=wert, variable=self.diagrammtyp_var,
                command=self._neu_zeichnen,
            ).pack(side="left", padx=(0, 12))

        ttk.Label(
            steuerung,
            text="Bei mehreren Zeiträumen ist nur eine Kennzahl gleichzeitig möglich (und umgekehrt). "
                 "Überlagern sich die Linien zu stark, hilft der Diagrammtyp \"Balken\".",
            foreground=stil.SEKUNDAER, font=("Segoe UI", 8), wraplength=900, justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 0))

    # ---------- Zeitraum-Auswahl ----------

    def _verfuegbare_zeitraeume(self):
        """Liefert (key, label, von, bis) für alle wählbaren Zeiträume:
        der Gesamtzeitraum über alle Daten, plus eine Option je hinterlegter
        Saison (siehe Saisonübersicht auf der Erfassungsseite)."""
        ergebnisse = []
        alle = self.datenmanager.alle_eintraege()
        if alle:
            ergebnisse.append(("gesamt", "Gesamter Zeitraum", alle[0].datum, alle[-1].datum))
        for z in self.saisonmanager.alle():
            ergebnisse.append((f"saison_{z.jahr}", f"Saison {z.jahr}", z.von, z.bis))
        return ergebnisse

    def _zeitraum_checkboxen_aktualisieren(self) -> None:
        """Baut die Zeitraum-Checkboxen neu auf (z.B. wenn eine neue Saison
        hinterlegt wurde), ohne die aktuelle Auswahl zu verlieren."""
        verfuegbar = self._verfuegbare_zeitraeume()
        neue_keys = {k for k, _, _, _ in verfuegbar}

        for k in list(self.zeitraum_vars.keys()):
            if k not in neue_keys:
                del self.zeitraum_vars[k]

        for widget in self.zeitraum_checkbox_frame.winfo_children():
            widget.destroy()

        for k, label, _, _ in verfuegbar:
            if k not in self.zeitraum_vars:
                self.zeitraum_vars[k] = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                self.zeitraum_checkbox_frame, text=label, variable=self.zeitraum_vars[k],
                command=lambda: self._checkbox_geaendert("zeitraum"),
            ).pack(side="left", padx=(0, 12))

        if verfuegbar and not any(v.get() for v in self.zeitraum_vars.values()):
            # Sinnvoller Default: die neueste Saison, sonst der Gesamtzeitraum.
            self.zeitraum_vars[verfuegbar[-1][0]].set(True)

    def _checkbox_geaendert(self, geaenderte_gruppe: str) -> None:
        aktive_zeitraeume = [k for k, v in self.zeitraum_vars.items() if v.get()]
        aktive_werte = [k for k in WERT_REIHENFOLGE if self.wert_vars[k].get()]

        if len(aktive_zeitraeume) > 1 and len(aktive_werte) > 1:
            # Beides gleichzeitig mehrfach ergibt kein sinnvolles Diagramm.
            # Die Gruppe, die NICHT gerade geändert wurde, auf eine Auswahl reduzieren.
            if geaenderte_gruppe == "zeitraum":
                for k in aktive_werte[1:]:
                    self.wert_vars[k].set(False)
            else:
                for k in aktive_zeitraeume[1:]:
                    self.zeitraum_vars[k].set(False)

        if not any(v.get() for v in self.zeitraum_vars.values()) and self.zeitraum_vars:
            next(iter(self.zeitraum_vars.values())).set(True)
        if not any(v.get() for v in self.wert_vars.values()):
            self.wert_vars["besucher"].set(True)

        self._neu_zeichnen()

    # ---------- Aggregation ----------

    @staticmethod
    def _auf_gemeinsame_achse(teilreihen, beschriftung=None) -> list[ChartReihe]:
        """Bringt mehrere (label, farbe, einheit, x, werte)-Reihen auf eine
        gemeinsame, sortierte x-Achse (fehlende Werte = NaN).

        Nötig, sobald mehrere Reihen unterschiedlich lang/verschieden
        datiert sein können (z.B. Saisons unterschiedlicher Länge) – vor
        allem für gruppierte Balken, die alle gleich lang sein müssen, aber
        auch für Linien praktisch (ergibt einfach eine Lücke).
        """
        alle_x = sorted({x for _, _, _, xs, _ in teilreihen for x in xs})
        anzeige = [beschriftung(x) for x in alle_x] if beschriftung else list(alle_x)
        ergebnis = []
        for label, farbe, einheit, xs, werte in teilreihen:
            nachschlagen = dict(zip(xs, werte))
            y_original = [nachschlagen.get(x, math.nan) for x in alle_x]
            ergebnis.append(ChartReihe(
                label=label, x=list(anzeige), y=list(y_original), y_original=y_original,
                farbe=farbe, einheit=einheit,
            ))
        return ergebnis

    @staticmethod
    def _bucket_schluessel(datum, gruppierung: str):
        if gruppierung == "monat":
            return (datum.year, datum.month)
        if gruppierung == "jahr":
            return (datum.year,)
        return None

    @staticmethod
    def _bucket_label(schluessel, gruppierung: str) -> str:
        if gruppierung == "monat":
            jahr, monat = schluessel
            return f"{MONATSNAMEN[monat - 1]} {jahr}"
        return str(schluessel[0])

    @classmethod
    def _aggregieren(cls, eintraege, metrik: str, gruppierung: str):
        """Fasst Tagesdatensätze eines Zeitraums nach Monat/Jahr zusammen.

        Besucher/Einnahmen werden je Kategorie summiert, Temperaturen
        gemittelt (NaN-Tage werden dabei übergangen).
        """
        werte_je_schluessel: dict = defaultdict(list)
        for e in eintraege:
            werte_je_schluessel[cls._bucket_schluessel(e.datum, gruppierung)].append(wert_fuer_metrik(e, metrik))

        schluessel_sortiert = sorted(werte_je_schluessel.keys())
        if metrik in MITTELWERT_METRIKEN:
            werte = []
            for s in schluessel_sortiert:
                gueltige = [w for w in werte_je_schluessel[s] if not math.isnan(w)]
                werte.append(sum(gueltige) / len(gueltige) if gueltige else math.nan)
        else:
            werte = [sum(0.0 if math.isnan(w) else w for w in werte_je_schluessel[s]) for s in schluessel_sortiert]

        labels = [cls._bucket_label(s, gruppierung) for s in schluessel_sortiert]
        return schluessel_sortiert, labels, werte

    # ---------- Zeichnen ----------

    def _neu_zeichnen(self) -> None:
        verfuegbar = {k: (label, von, bis) for k, label, von, bis in self._verfuegbare_zeitraeume()}
        aktive_zeitraeume = [k for k, v in self.zeitraum_vars.items() if v.get() and k in verfuegbar]
        aktive_werte = [k for k in WERT_REIHENFOLGE if self.wert_vars[k].get()]
        gruppierung = self.gruppierung_var.get()
        diagrammtyp = self.diagrammtyp_var.get()

        mehrere_zeitraeume = len(aktive_zeitraeume) > 1
        normiert = (not mehrere_zeitraeume) and len(aktive_werte) > 1

        reihen: list[ChartReihe] = []
        zusammenfassungen: list[str] = []

        if gruppierung == "tag":
            x_typ = "zahl" if mehrere_zeitraeume else "datum"
            if mehrere_zeitraeume:
                metrik = aktive_werte[0] if aktive_werte else "besucher"
                teilreihen = []  # (label, farbe, einheit, x, werte)
                for i, k in enumerate(aktive_zeitraeume):
                    label, von, bis = verfuegbar[k]
                    eintraege = self.datenmanager.eintraege_im_zeitraum(von, bis)
                    if not eintraege:
                        continue
                    x = [(e.datum - von).days + 1 for e in eintraege]
                    werte = [wert_fuer_metrik(e, metrik) for e in eintraege]
                    teilreihen.append((label, ZEITRAUM_FARBEN[i % len(ZEITRAUM_FARBEN)], METRIK_EINHEIT[metrik], x, werte))
                    zusammenfassungen.append(self._zusammenfassung_zeile(label, eintraege))
                # Unterschiedlich lange Saisons auf eine gemeinsame x-Achse
                # bringen (fehlende Tage = NaN) – nötig für gruppierte Balken,
                # schadet bei Linien nicht (ergibt dort einfach eine Lücke).
                reihen.extend(self._auf_gemeinsame_achse(teilreihen))
            elif aktive_zeitraeume:
                k = aktive_zeitraeume[0]
                label, von, bis = verfuegbar[k]
                eintraege = self.datenmanager.eintraege_im_zeitraum(von, bis)
                for metrik in aktive_werte:
                    werte = [wert_fuer_metrik(e, metrik) for e in eintraege]
                    y = self._normieren(werte) if normiert else werte
                    reihen.append(ChartReihe(
                        label=METRIK_LABEL[metrik], x=[e.datum for e in eintraege], y=y, y_original=werte,
                        farbe=METRIK_FARBE[metrik], einheit=METRIK_EINHEIT[metrik],
                    ))
                if eintraege:
                    zusammenfassungen.append(self._zusammenfassung_zeile(label, eintraege))
        else:
            # Monat- oder Jahr-Gruppierung: je Reihe aggregieren, dann alle
            # auf eine gemeinsame, chronologisch sortierte Kategorienachse bringen.
            x_typ = "kategorie"
            teilreihen = []  # (label, farbe, einheit, schluessel, labels, werte)
            if mehrere_zeitraeume:
                metrik = aktive_werte[0] if aktive_werte else "besucher"
                for i, k in enumerate(aktive_zeitraeume):
                    label, von, bis = verfuegbar[k]
                    eintraege = self.datenmanager.eintraege_im_zeitraum(von, bis)
                    if not eintraege:
                        continue
                    schluessel, labels, werte = self._aggregieren(eintraege, metrik, gruppierung)
                    teilreihen.append((label, ZEITRAUM_FARBEN[i % len(ZEITRAUM_FARBEN)], METRIK_EINHEIT[metrik], schluessel, labels, werte))
                    zusammenfassungen.append(self._zusammenfassung_zeile(label, eintraege))
            elif aktive_zeitraeume:
                k = aktive_zeitraeume[0]
                label, von, bis = verfuegbar[k]
                eintraege = self.datenmanager.eintraege_im_zeitraum(von, bis)
                for metrik in aktive_werte:
                    schluessel, labels, werte = self._aggregieren(eintraege, metrik, gruppierung)
                    teilreihen.append((METRIK_LABEL[metrik], METRIK_FARBE[metrik], METRIK_EINHEIT[metrik], schluessel, labels, werte))
                if eintraege:
                    zusammenfassungen.append(self._zusammenfassung_zeile(label, eintraege))

            # (label, farbe, einheit, schluessel, werte) – die Rohbeschriftungen
            # je Teilreihe werden verworfen, _auf_gemeinsame_achse leitet sie
            # aus der Vereinigung aller Schlüssel neu her (chronologisch).
            roh = [(label, farbe, einheit, schluessel, werte) for label, farbe, einheit, schluessel, _labels, werte in teilreihen]
            reihen.extend(self._auf_gemeinsame_achse(roh, beschriftung=lambda s: self._bucket_label(s, gruppierung)))
            if normiert:
                for reihe in reihen:
                    reihe.y = self._normieren(reihe.y_original)

        zeichne_vergleich(self.achse, reihen, x_typ, normiert, diagrammtyp)
        self.figur.tight_layout(pad=3.0)
        self.canvas.draw()

        self.zusammenfassung_label.config(
            text="\n".join(zusammenfassungen) if zusammenfassungen else "Keine Daten für die aktuelle Auswahl."
        )

    @staticmethod
    def _normieren(werte: list[float]) -> list[float]:
        """Skaliert Werte auf 0–100 % ihres Maximums (NaN bleibt NaN)."""
        gueltige = [w for w in werte if not math.isnan(w)]
        if not gueltige:
            return werte
        minimum, maximum = min(gueltige), max(gueltige)
        spanne = (maximum - minimum) or 1
        return [((w - minimum) / spanne * 100) if not math.isnan(w) else math.nan for w in werte]

    @staticmethod
    def _zusammenfassung_zeile(label: str, eintraege) -> str:
        anzahl_tage = len(eintraege)
        summe_besucher = sum(e.besucher for e in eintraege)
        summe_einnahmen = sum(0.0 if math.isnan(e.einnahmen) else e.einnahmen for e in eintraege)
        wasser_werte = [e.wassertemperatur for e in eintraege if not math.isnan(e.wassertemperatur)]
        wasser_text = f"{sum(wasser_werte) / len(wasser_werte):.1f} °C" if wasser_werte else "keine Daten"
        return (
            f"{label}: {anzahl_tage} Tage  |  Besucher: {summe_besucher}  |  "
            f"Einnahmen: {summe_einnahmen:.2f} €  |  Ø Wassertemp: {wasser_text}"
        )

    # ---------- Öffentliche Aktualisierung ----------

    def aktualisieren(self) -> None:
        """Wird von main.py aufgerufen, wenn der Auswertungs-Tab aktiviert wird."""
        self._zeitraum_checkboxen_aktualisieren()
        self._neu_zeichnen()
