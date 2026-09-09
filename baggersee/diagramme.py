"""
Diagrammfunktionen für die Auswertung.

Jede Funktion zeichnet auf einer übergebenen matplotlib-Achse; die Einbettung
in Tkinter erfolgt in auswertung.py über FigureCanvasTkAgg.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

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


def zeichne_besucherverlauf(ax, eintraege: Iterable[Tagesdatensatz]) -> None:
    eintraege = list(eintraege)
    ax.clear()
    if not eintraege:
        _leerer_hinweis(ax, "Keine Daten im gewählten Zeitraum")
        return
    x = [e.datum for e in eintraege]
    y = [e.besucher for e in eintraege]
    linie = ax.plot(x, y, marker="o", color=FARBE_BESUCHER)[0]
    ax.set_title("Besucherverlauf")
    ax.set_ylabel("Besucher")
    ax.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax)
    _cursor_setzen(
        ax, [linie],
        lambda sel: f"{formatiere_datum(eintraege[int(sel.index)].datum)}\n{eintraege[int(sel.index)].besucher} Besucher",
    )


def zeichne_temperaturverlauf(ax, eintraege: Iterable[Tagesdatensatz]) -> None:
    eintraege = list(eintraege)
    ax.clear()
    if not eintraege:
        _leerer_hinweis(ax, "Keine Daten im gewählten Zeitraum")
        return
    x = [e.datum for e in eintraege]
    wasser = [e.wassertemperatur for e in eintraege]
    luft = [e.lufttemperatur for e in eintraege]
    linie_wasser = ax.plot(x, wasser, marker="o", color=FARBE_WASSER, label="Wassertemperatur")[0]
    linie_luft = ax.plot(x, luft, marker="o", color=FARBE_LUFT, label="Lufttemperatur")[0]
    ax.set_title("Wasser- und Lufttemperatur")
    ax.set_ylabel("°C")
    ax.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax)
    ax.legend(loc="best", fontsize=8, facecolor=stil.PANEL, edgecolor=stil.RAHMEN, labelcolor=stil.VORDERGRUND)

    def _temperatur_tooltip(sel):
        e = eintraege[int(sel.index)]
        if sel.artist is linie_wasser:
            bezeichnung, wert = "Wassertemperatur", e.wassertemperatur
        else:
            bezeichnung, wert = "Lufttemperatur", e.lufttemperatur
        wert_text = f"{wert:.1f} °C" if not math.isnan(wert) else "unbekannt"
        return f"{formatiere_datum(e.datum)}\n{bezeichnung}: {wert_text}"

    _cursor_setzen(ax, [linie_wasser, linie_luft], _temperatur_tooltip)


def zeichne_einnahmenverlauf(ax, eintraege: Iterable[Tagesdatensatz]) -> None:
    eintraege = list(eintraege)
    ax.clear()
    if not eintraege:
        _leerer_hinweis(ax, "Keine Daten im gewählten Zeitraum")
        return
    x = [e.datum for e in eintraege]
    y = [e.einnahmen for e in eintraege]
    balken = ax.bar(x, y, color=FARBE_EINNAHMEN, width=0.8)
    ax.set_title("Einnahmen")
    ax.set_ylabel("€")
    ax.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax, achse="y")

    def _einnahmen_tooltip(sel):
        e = eintraege[int(sel.index)]
        wert_text = f"{e.einnahmen:.2f} €" if not math.isnan(e.einnahmen) else "unbekannt"
        return f"{formatiere_datum(e.datum)}\n{wert_text}"

    _cursor_setzen(ax, [balken], _einnahmen_tooltip)


def _monatsschluessel(e: Tagesdatensatz) -> tuple[int, int]:
    return (e.datum.year, e.datum.month)


def zeichne_monatsuebersicht(ax_besucher, ax_einnahmen, eintraege: Iterable[Tagesdatensatz]) -> None:
    """Zeichnet zwei Balkendiagramme (Besucher, Einnahmen) je Kalendermonat."""
    eintraege = sorted(eintraege, key=lambda e: e.datum)
    ax_besucher.clear()
    ax_einnahmen.clear()
    if not eintraege:
        _leerer_hinweis(ax_besucher, "Keine Daten im gewählten Zeitraum")
        _leerer_hinweis(ax_einnahmen, "Keine Daten im gewählten Zeitraum")
        return

    monats_besucher: dict[tuple[int, int], int] = defaultdict(int)
    monats_einnahmen: dict[tuple[int, int], float] = defaultdict(float)
    for e in eintraege:
        schluessel = _monatsschluessel(e)
        monats_besucher[schluessel] += e.besucher
        monats_einnahmen[schluessel] += 0.0 if math.isnan(e.einnahmen) else e.einnahmen

    schluessel_sortiert = sorted(monats_besucher.keys())
    beschriftungen = [f"{MONATSNAMEN[m - 1]} {j}" for (j, m) in schluessel_sortiert]
    werte_besucher = [monats_besucher[k] for k in schluessel_sortiert]
    werte_einnahmen = [monats_einnahmen[k] for k in schluessel_sortiert]

    balken_besucher = ax_besucher.bar(beschriftungen, werte_besucher, color=FARBE_BESUCHER)
    ax_besucher.set_title("Besucher pro Monat")
    ax_besucher.set_ylabel("Besucher")
    ax_besucher.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax_besucher, achse="y")
    _cursor_setzen(
        ax_besucher, [balken_besucher],
        lambda sel: f"{beschriftungen[int(sel.index)]}\n{werte_besucher[int(sel.index)]} Besucher",
    )

    balken_einnahmen = ax_einnahmen.bar(beschriftungen, werte_einnahmen, color=FARBE_EINNAHMEN)
    ax_einnahmen.set_title("Einnahmen pro Monat")
    ax_einnahmen.set_ylabel("€")
    ax_einnahmen.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax_einnahmen, achse="y")
    _cursor_setzen(
        ax_einnahmen, [balken_einnahmen],
        lambda sel: f"{beschriftungen[int(sel.index)]}\n{werte_einnahmen[int(sel.index)]:.2f} €",
    )


def zeichne_saisonuebersicht(ax_besucher, ax_einnahmen, eintraege: Iterable[Tagesdatensatz]) -> None:
    """Zeichnet zwei Balkendiagramme (Besucher, Einnahmen) je Saison (Kalenderjahr)."""
    eintraege = sorted(eintraege, key=lambda e: e.datum)
    ax_besucher.clear()
    ax_einnahmen.clear()
    if not eintraege:
        _leerer_hinweis(ax_besucher, "Keine Daten vorhanden")
        _leerer_hinweis(ax_einnahmen, "Keine Daten vorhanden")
        return

    saison_besucher: dict[int, int] = defaultdict(int)
    saison_einnahmen: dict[int, float] = defaultdict(float)
    for e in eintraege:
        saison_besucher[e.datum.year] += e.besucher
        saison_einnahmen[e.datum.year] += 0.0 if math.isnan(e.einnahmen) else e.einnahmen

    jahre = sorted(saison_besucher.keys())
    beschriftungen = [str(j) for j in jahre]
    werte_besucher = [saison_besucher[j] for j in jahre]
    werte_einnahmen = [saison_einnahmen[j] for j in jahre]

    balken_besucher = ax_besucher.bar(beschriftungen, werte_besucher, color=FARBE_BESUCHER)
    ax_besucher.set_title("Besucher pro Saison")
    ax_besucher.set_ylabel("Besucher")
    _dunkle_achse(ax_besucher, achse="y")
    _cursor_setzen(
        ax_besucher, [balken_besucher],
        lambda sel: f"{beschriftungen[int(sel.index)]}\n{werte_besucher[int(sel.index)]} Besucher",
    )

    balken_einnahmen = ax_einnahmen.bar(beschriftungen, werte_einnahmen, color=FARBE_EINNAHMEN)
    ax_einnahmen.set_title("Einnahmen pro Saison")
    ax_einnahmen.set_ylabel("€")
    _dunkle_achse(ax_einnahmen, achse="y")
    _cursor_setzen(
        ax_einnahmen, [balken_einnahmen],
        lambda sel: f"{beschriftungen[int(sel.index)]}\n{werte_einnahmen[int(sel.index)]:.2f} €",
    )
