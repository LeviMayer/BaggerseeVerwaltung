"""
Datenmodell für die Baggersee-Verwaltung.

Enthält den Tagesdatensatz sowie die Validierungsregeln, die sowohl von der
Eingabemaske als auch von der Datenhaltung (CSV-Import/-Export) genutzt werden.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime


class ValidierungsFehler(Exception):
    """Wird ausgelöst, wenn ein Eingabewert außerhalb des sinnvollen Bereichs liegt."""


# Sinnvolle Wertebereiche für die Plausibilitätsprüfung
MIN_WASSERTEMPERATUR = -5.0
MAX_WASSERTEMPERATUR = 40.0
MIN_LUFTTEMPERATUR = -25.0
MAX_LUFTTEMPERATUR = 50.0
MAX_BESUCHER = 100_000
MAX_EINNAHMEN = 1_000_000.0


@dataclass
class Tagesdatensatz:
    """Ein einzelner Betriebstag am Baggersee."""

    datum: date
    besucher: int
    wassertemperatur: float  # NaN, wenn nicht erfasst
    lufttemperatur: float  # NaN, wenn nicht erfasst
    einnahmen: float  # NaN, wenn nicht erfasst
    # Mehrere Öffnungszeiträume je Tag (z.B. bei Zwangspause wegen Unwetter):
    # [("10:00", "14:00"), ("16:00", "19:00")]. Leere Liste = keine erfasst.
    oeffnungszeiten: list[tuple[str, str]]


def ist_unvollstaendig(e: Tagesdatensatz) -> bool:
    """
    Prüft, ob für einen Tag Kernangaben fehlen: Temperatur oder Einnahmen
    nicht erfasst (dargestellt als NaN), keine Öffnungszeiten hinterlegt,
    oder Einnahmen trotz Besuchern bei 0€ (typisch für ältere Importe ohne
    Einnahmen-Tracking).
    """
    if math.isnan(e.wassertemperatur) or math.isnan(e.lufttemperatur):
        return True
    if math.isnan(e.einnahmen):
        return True
    if not e.oeffnungszeiten:
        return True
    if e.besucher > 0 and e.einnahmen == 0.0:
        return True
    return False


def parse_datum(text: str) -> date:
    """Wandelt einen Text im Format TT.MM.JJJJ oder JJJJ-MM-TT in ein date-Objekt um."""
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValidierungsFehler(
        f"Ungültiges Datumsformat: '{text}'. Bitte TT.MM.JJJJ eingeben."
    )


def formatiere_datum(d: date) -> str:
    """Einheitliche Anzeige im deutschen Format TT.MM.JJJJ."""
    return d.strftime("%d.%m.%Y")


def parse_uhrzeit(text: str) -> str:
    """Prüft ein Zeitformat HH:MM und gibt es normiert zurück."""
    text = text.strip()
    try:
        t = datetime.strptime(text, "%H:%M")
    except ValueError:
        raise ValidierungsFehler(
            f"Ungültige Uhrzeit: '{text}'. Bitte im Format HH:MM eingeben."
        )
    return t.strftime("%H:%M")


def parse_ganzzahl(text: str, feldname: str, minimum: int = 0, maximum: int = MAX_BESUCHER) -> int:
    """Wandelt Text in eine nicht-negative Ganzzahl um und prüft den Wertebereich."""
    text = text.strip().replace(".", "")
    try:
        wert = int(text)
    except ValueError:
        raise ValidierungsFehler(f"{feldname}: Bitte eine ganze Zahl eingeben.")
    if wert < minimum or wert > maximum:
        raise ValidierungsFehler(
            f"{feldname}: Wert muss zwischen {minimum} und {maximum} liegen."
        )
    return wert


def parse_kommazahl(text: str, feldname: str, minimum: float, maximum: float) -> float:
    """Wandelt Text (Komma oder Punkt als Dezimaltrennzeichen) in eine Fließkommazahl um."""
    text = text.strip().replace(",", ".")
    try:
        wert = float(text)
    except ValueError:
        raise ValidierungsFehler(f"{feldname}: Bitte eine Zahl eingeben.")
    if wert < minimum or wert > maximum:
        raise ValidierungsFehler(
            f"{feldname}: Wert muss zwischen {minimum} und {maximum} liegen."
        )
    return wert


def parse_kommazahl_optional(text: str, feldname: str, minimum: float, maximum: float) -> float:
    """Wie parse_kommazahl, erlaubt aber ein leeres Feld (Ergebnis: NaN = nicht erfasst)."""
    if not text.strip():
        return math.nan
    return parse_kommazahl(text, feldname, minimum, maximum)


def validiere_oeffnungszeitraum(von: str, bis: str) -> None:
    """Stellt sicher, dass die Öffnungszeit 'von' vor der Öffnungszeit 'bis' liegt."""
    fmt = "%H:%M"
    if datetime.strptime(von, fmt) >= datetime.strptime(bis, fmt):
        raise ValidierungsFehler("Öffnungszeit 'von' muss vor der Öffnungszeit 'bis' liegen.")


def parse_oeffnungszeiten(zeitraum_texte: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Validiert eine Liste von (von_text, bis_text)-Paaren aus dem Formular.

    Vollständig leere Zeilen werden ignoriert (nicht genutzter Zeitraum).
    Ist nur eine Seite eines Paares ausgefüllt, ist das ein Eingabefehler.
    Innerhalb eines Zeitraums muss 'von' vor 'bis' liegen, und die
    Zeiträume dürfen sich nicht überschneiden (z.B. bei einer Zwangspause
    wegen Unwetter: 10:00–14:00 und 16:00–19:00 ist erlaubt).
    """
    zeitraeume: list[tuple[str, str]] = []
    for von_text, bis_text in zeitraum_texte:
        von_text, bis_text = von_text.strip(), bis_text.strip()
        if not von_text and not bis_text:
            continue
        if not von_text or not bis_text:
            raise ValidierungsFehler(
                "Öffnungszeit: bitte 'von' und 'bis' beide ausfüllen oder beide leer lassen."
            )
        von = parse_uhrzeit(von_text)
        bis = parse_uhrzeit(bis_text)
        validiere_oeffnungszeitraum(von, bis)
        zeitraeume.append((von, bis))

    zeitraeume.sort(key=lambda z: z[0])
    for (_, bis_a), (von_b, _) in zip(zeitraeume, zeitraeume[1:]):
        if bis_a > von_b:
            raise ValidierungsFehler("Öffnungszeiten dürfen sich nicht überschneiden.")
    return zeitraeume


def erstelle_tagesdatensatz(
    datum_text: str,
    einnahmen_text: str,
    besucher_text: str,
    lufttemp_text: str,
    wassertemp_text: str,
    zeitraum_texte: list[tuple[str, str]],
) -> Tagesdatensatz:
    """
    Validiert alle Rohtexte aus der Eingabemaske und erzeugt daraus einen
    Tagesdatensatz. Löst bei ungültigen Werten eine ValidierungsFehler aus,
    deren Meldung direkt dem Benutzer angezeigt werden kann.

    Besucherzahl und Datum sind Pflichtfelder; Einnahmen, Temperaturen und
    Öffnungszeiten dürfen leer bleiben, wenn sie noch nicht bekannt sind
    (der Tag gilt dann als unvollständig, siehe ist_unvollstaendig()).
    """
    datum = parse_datum(datum_text)
    besucher = parse_ganzzahl(besucher_text, "Besucherzahl", minimum=0, maximum=MAX_BESUCHER)
    einnahmen = parse_kommazahl_optional(einnahmen_text, "Einnahmen", 0.0, MAX_EINNAHMEN)
    lufttemp = parse_kommazahl_optional(
        lufttemp_text, "Lufttemperatur", MIN_LUFTTEMPERATUR, MAX_LUFTTEMPERATUR
    )
    wassertemp = parse_kommazahl_optional(
        wassertemp_text, "Wassertemperatur", MIN_WASSERTEMPERATUR, MAX_WASSERTEMPERATUR
    )
    zeitraeume = parse_oeffnungszeiten(zeitraum_texte)

    return Tagesdatensatz(
        datum=datum,
        besucher=besucher,
        wassertemperatur=wassertemp,
        lufttemperatur=lufttemp,
        einnahmen=einnahmen,
        oeffnungszeiten=zeitraeume,
    )
