"""
Diagrammfunktion für die Auswertung: ein einzelnes Vergleichs-Diagramm.

Die Einbettung in Tkinter erfolgt in auswertung.py über FigureCanvasTkAgg;
auswertung.py stellt auch die eigentlichen Kennzahlen zusammen (Auswahl,
Gruppierung nach Tag/Monat/Jahr, ggf. Normierung) und übergibt sie hier
fertig aufbereitet als Liste von ChartReihe.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import mplcursors

from . import stil
from .modelle import Tagesdatensatz, formatiere_datum

MONATSNAMEN = [
    "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
]

FARBE_BESUCHER = stil.AKZENT
FARBE_WASSER = stil.INFO
FARBE_LUFT = stil.WARNUNG
FARBE_EINNAHMEN = stil.ERFOLG

# Kennzahlen, die im Vergleichs-Diagramm wählbar sind.
METRIK_LABEL = {
    "besucher": "Besucher",
    "wasser": "Wassertemperatur",
    "luft": "Lufttemperatur",
    "einnahmen": "Einnahmen",
}
METRIK_EINHEIT = {"besucher": "", "wasser": "°C", "luft": "°C", "einnahmen": "€"}
METRIK_FARBE = {
    "besucher": FARBE_BESUCHER, "wasser": FARBE_WASSER,
    "luft": FARBE_LUFT, "einnahmen": FARBE_EINNAHMEN,
}
# Rotierende Farben für mehrere überlagerte Zeiträume (eine Kennzahl, viele Saisons).
ZEITRAUM_FARBEN = [stil.AKZENT, stil.ERFOLG, stil.WARNUNG, stil.INFO, stil.GELB, stil.FEHLER]


def wert_fuer_metrik(e: Tagesdatensatz, metrik: str) -> float:
    """Liest den Wert einer Kennzahl aus einem Tagesdatensatz."""
    if metrik == "besucher":
        return e.besucher
    if metrik == "wasser":
        return e.wassertemperatur
    if metrik == "luft":
        return e.lufttemperatur
    if metrik == "einnahmen":
        return e.einnahmen
    raise ValueError(f"Unbekannte Kennzahl: {metrik}")


@dataclass
class ChartReihe:
    """Eine Linie/Balkengruppe im Vergleichs-Diagramm.

    `x` ist je nach x_typ (siehe zeichne_vergleich) ein Datum, eine Zahl
    (Tag der Saison) oder eine bereits fertige Kategorie-Beschriftung
    (Monat/Jahr-Gruppierung) – über alle Reihen eines Diagramms hinweg
    einheitlich und gleich lang (fehlende Kategorien = NaN).
    """

    label: str
    x: list
    y: list  # ggf. normierte Werte (0-100), die tatsächlich gezeichnet werden
    y_original: list  # echte Werte, für den Hover-Tooltip
    farbe: str
    einheit: str


def _dunkle_achse(ax, achse: str = "both") -> None:
    """Passt eine bereits bezeichnete Achse an das dunkle Erscheinungsbild an."""
    ax.set_facecolor(stil.PANEL)
    for spine in ax.spines.values():
        spine.set_color(stil.RAHMEN)
    ax.tick_params(colors=stil.SEKUNDAER, labelsize=8)
    ax.xaxis.label.set_color(stil.VORDERGRUND)
    ax.yaxis.label.set_color(stil.VORDERGRUND)
    ax.title.set_color(stil.VORDERGRUND)
    ax.grid(True, axis=achse, color=stil.RAHMEN, alpha=0.6, linewidth=0.6)


def _leerer_hinweis(ax, text: str) -> None:
    ax.set_facecolor(stil.PANEL)
    for spine in ax.spines.values():
        spine.set_color(stil.RAHMEN)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.5, text, ha="center", va="center", color=stil.SEKUNDAER)
    _cursor_entfernen(ax)


def _cursor_entfernen(ax) -> None:
    """Entfernt einen zuvor gesetzten Hover-Tooltip (z.B. vor einem Neuzeichnen)."""
    alter = getattr(ax, "_baggersee_cursor", None)
    if alter is not None:
        alter.remove()
        ax._baggersee_cursor = None


def _cursor_setzen(ax, artists, formatter) -> None:
    """Zeigt beim Überfahren eines Diagramm-Elements mit der Maus einen
    Tooltip mit exaktem Wert an. Ersetzt einen zuvor gesetzten Tooltip."""
    _cursor_entfernen(ax)
    if not artists:
        return
    cursor = mplcursors.cursor(artists, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(formatter(sel)))
    ax._baggersee_cursor = cursor


def _wert_text(wert, einheit: str) -> str:
    if isinstance(wert, float) and math.isnan(wert):
        return "unbekannt"
    if einheit == "€":
        return f"{wert:.2f} €"
    if einheit == "°C":
        return f"{wert:.1f} °C"
    return str(wert)


def zeichne_vergleich(
    ax, reihen: list[ChartReihe], x_typ: str, normiert: bool, diagrammtyp: str = "linie",
) -> None:
    """
    Zeichnet das Vergleichs-Diagramm mit einer oder mehreren Reihen.

    `x_typ` steuert, wie die x-Achse zu lesen und zu beschriften ist:
    - "datum": echtes Kalenderdatum (ein einzelner Zeitraum, Gruppierung "Tag")
    - "zahl": Tag der Saison (mehrere überlagerte Zeiträume, Gruppierung "Tag")
    - "kategorie": fertige Beschriftungen wie "Mai 2026" oder "2026"
      (Gruppierung "Monat"/"Jahr", von auswertung.py bereits aufbereitet)

    `diagrammtyp` ist "linie" oder "balken". Bei "balken" werden alle
    Reihen als gruppierte Balken nebeneinander gezeichnet (hilfreich, wenn
    sich Linien mehrerer Saisons sonst gegenseitig überlagern).
    """
    ax.clear()
    if not reihen:
        _leerer_hinweis(ax, "Keine Daten für die aktuelle Auswahl.")
        return

    kategorisch = x_typ in ("kategorie", "zahl") if diagrammtyp == "balken" else x_typ == "kategorie"
    kunst: list[tuple[object, ChartReihe]] = []

    if diagrammtyp == "balken":
        positionen_basis = list(range(len(reihen[0].x)))
        anzahl = len(reihen)
        breite = 0.8 / max(anzahl, 1)
        for i, reihe in enumerate(reihen):
            positionen = [p + (i - (anzahl - 1) / 2) * breite for p in positionen_basis]
            balken = ax.bar(positionen, reihe.y, width=breite, color=reihe.farbe, label=reihe.label)
            kunst.append((balken, reihe))
        beschriftungen = [
            v if x_typ == "kategorie" else (formatiere_datum(v) if x_typ == "datum" else str(v))
            for v in reihen[0].x
        ]
        ax.set_xticks(positionen_basis)
        ax.set_xticklabels(beschriftungen, rotation=45, ha="right", fontsize=7)
    else:
        for reihe in reihen:
            if kategorisch:
                x_werte = list(range(len(reihe.x)))
            else:
                x_werte = reihe.x
            linie = ax.plot(x_werte, reihe.y, marker="o", markersize=3, color=reihe.farbe, label=reihe.label)[0]
            kunst.append((linie, reihe))
        if kategorisch:
            ax.set_xticks(list(range(len(reihen[0].x))))
            ax.set_xticklabels(reihen[0].x, rotation=45, ha="right", fontsize=7)

    ax.set_title("Vergleich")
    if normiert:
        ax.set_ylabel("% vom Maximum im Zeitraum")
    else:
        einheit = reihen[0].einheit
        ax.set_ylabel(einheit if einheit else "Anzahl")

    if x_typ == "datum" and diagrammtyp == "linie":
        ax.tick_params(axis="x", rotation=45)
    elif x_typ == "zahl" and diagrammtyp == "linie":
        ax.set_xlabel("Tag der Saison")

    _dunkle_achse(ax)
    if len(reihen) > 1:
        ax.legend(loc="best", fontsize=8, facecolor=stil.PANEL, edgecolor=stil.RAHMEN, labelcolor=stil.VORDERGRUND)

    def _tooltip(sel):
        for artefakt, reihe in kunst:
            if sel.artist is not artefakt:
                continue
            idx = int(sel.index)
            wert_text = _wert_text(reihe.y_original[idx], reihe.einheit)
            if x_typ == "kategorie":
                x_text = str(reihe.x[idx])
            elif x_typ == "datum":
                x_text = formatiere_datum(reihe.x[idx])
            else:
                x_text = f"Tag {reihe.x[idx]}"
            return f"{reihe.label}\n{x_text}: {wert_text}"
        return ""

    _cursor_setzen(ax, [k for k, _ in kunst], _tooltip)
