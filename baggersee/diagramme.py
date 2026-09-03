"""
Diagrammfunktionen für die Auswertung.

Jede Funktion zeichnet auf einer übergebenen matplotlib-Achse; die Einbettung
in Tkinter erfolgt in auswertung.py über FigureCanvasTkAgg.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from . import stil
from .modelle import Tagesdatensatz

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


def zeichne_besucherverlauf(ax, eintraege: Iterable[Tagesdatensatz]) -> None:
    eintraege = list(eintraege)
    ax.clear()
    if not eintraege:
        _leerer_hinweis(ax, "Keine Daten im gewählten Zeitraum")
        return
    x = [e.datum for e in eintraege]
    y = [e.besucher for e in eintraege]
    ax.plot(x, y, marker="o", color=FARBE_BESUCHER)
    ax.set_title("Besucherverlauf")
    ax.set_ylabel("Besucher")
    ax.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax)


def zeichne_temperaturverlauf(ax, eintraege: Iterable[Tagesdatensatz]) -> None:
    eintraege = list(eintraege)
    ax.clear()
    if not eintraege:
        _leerer_hinweis(ax, "Keine Daten im gewählten Zeitraum")
        return
    x = [e.datum for e in eintraege]
    wasser = [e.wassertemperatur for e in eintraege]
    luft = [e.lufttemperatur for e in eintraege]
    ax.plot(x, wasser, marker="o", color=FARBE_WASSER, label="Wassertemperatur")
    ax.plot(x, luft, marker="o", color=FARBE_LUFT, label="Lufttemperatur")
    ax.set_title("Wasser- und Lufttemperatur")
    ax.set_ylabel("°C")
    ax.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax)
    ax.legend(loc="best", fontsize=8, facecolor=stil.PANEL, edgecolor=stil.RAHMEN, labelcolor=stil.VORDERGRUND)


def zeichne_einnahmenverlauf(ax, eintraege: Iterable[Tagesdatensatz]) -> None:
    eintraege = list(eintraege)
    ax.clear()
    if not eintraege:
        _leerer_hinweis(ax, "Keine Daten im gewählten Zeitraum")
        return
    x = [e.datum for e in eintraege]
    y = [e.einnahmen for e in eintraege]
    ax.bar(x, y, color=FARBE_EINNAHMEN, width=0.8)
    ax.set_title("Einnahmen")
    ax.set_ylabel("€")
    ax.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax, achse="y")


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
        monats_einnahmen[schluessel] += e.einnahmen

    schluessel_sortiert = sorted(monats_besucher.keys())
    beschriftungen = [f"{MONATSNAMEN[m - 1]} {j}" for (j, m) in schluessel_sortiert]

    ax_besucher.bar(beschriftungen, [monats_besucher[k] for k in schluessel_sortiert], color=FARBE_BESUCHER)
    ax_besucher.set_title("Besucher pro Monat")
    ax_besucher.set_ylabel("Besucher")
    ax_besucher.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax_besucher, achse="y")

    ax_einnahmen.bar(beschriftungen, [monats_einnahmen[k] for k in schluessel_sortiert], color=FARBE_EINNAHMEN)
    ax_einnahmen.set_title("Einnahmen pro Monat")
    ax_einnahmen.set_ylabel("€")
    ax_einnahmen.tick_params(axis="x", rotation=45)
    _dunkle_achse(ax_einnahmen, achse="y")


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
        saison_einnahmen[e.datum.year] += e.einnahmen

    jahre = sorted(saison_besucher.keys())
    beschriftungen = [str(j) for j in jahre]

    ax_besucher.bar(beschriftungen, [saison_besucher[j] for j in jahre], color=FARBE_BESUCHER)
    ax_besucher.set_title("Besucher pro Saison")
    ax_besucher.set_ylabel("Besucher")
    _dunkle_achse(ax_besucher, achse="y")

    ax_einnahmen.bar(beschriftungen, [saison_einnahmen[j] for j in jahre], color=FARBE_EINNAHMEN)
    ax_einnahmen.set_title("Einnahmen pro Saison")
    ax_einnahmen.set_ylabel("€")
    _dunkle_achse(ax_einnahmen, achse="y")
