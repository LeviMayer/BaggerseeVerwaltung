"""
Prüft auf GitHub Releases nach einer neueren Version der Anwendung und
installiert sie automatisch, wenn die Anwendung als eigenständige .exe läuft.

Ablauf: die neue .exe wird in einen temporären Ordner heruntergeladen, dann
übernimmt ein kleines Batch-Skript den Austausch (die laufende .exe kann sich
nicht selbst überschreiben) und startet die Anwendung anschließend neu.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .version import VERSION

GITHUB_REPO = "LeviMayer/BaggerseeVerwaltung"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


@dataclass
class UpdateInfo:
    version: str
    download_url: str
    notizen: str
    groesse: int


def _version_tuple(text: str) -> tuple[int, ...]:
    text = text.strip().lstrip("vV")
    teile = []
    for teil in text.split("."):
        ziffern = "".join(c for c in teil if c.isdigit())
        teile.append(int(ziffern) if ziffern else 0)
    return tuple(teile)


def neueste_version_pruefen() -> Optional[UpdateInfo]:
    """
    Fragt die neueste GitHub-Release ab.

    Gibt None zurück, wenn kein Update verfügbar ist, die Release keine .exe
    als Anhang hat, oder die Abfrage fehlschlägt (z.B. ohne Internetverbindung).
    """
    try:
        anfrage = urllib.request.Request(
            API_URL, headers={"Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(anfrage, timeout=5) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
    except Exception:
        return None

    tag = daten.get("tag_name", "")
    if not tag or _version_tuple(tag) <= _version_tuple(VERSION):
        return None

    exe_asset = next(
        (a for a in daten.get("assets", []) if a.get("name", "").lower().endswith(".exe")),
        None,
    )
    if exe_asset is None:
        return None

    return UpdateInfo(
        version=tag.lstrip("vV"),
        download_url=exe_asset["browser_download_url"],
        notizen=daten.get("body", "") or "",
        groesse=exe_asset.get("size", 0),
    )


def update_installieren(info: UpdateInfo) -> None:
    """
    Lädt die neue .exe herunter und ersetzt die laufende Anwendung.

    Funktioniert nur in der gebauten .exe (PyInstaller-Build mit sys.frozen).
    Beendet den aktuellen Prozess über sys.exit(), sobald das Austausch-Skript
    gestartet wurde.
    """
    if not getattr(sys, "frozen", False):
        raise RuntimeError(
            "Automatisches Update ist nur in der gebauten .exe verfügbar, "
            "nicht beim Start aus dem Quellcode."
        )

    aktuelle_exe = Path(sys.executable)
    temp_verzeichnis = Path(tempfile.gettempdir())
    # Erst unter .part herunterladen, damit nie eine unvollständige Datei
    # unter dem finalen Namen liegt, falls der Download abbricht.
    download_teil = temp_verzeichnis / f"BaggerseeVerwaltung_{info.version}.exe.part"
    neue_exe = temp_verzeichnis / f"BaggerseeVerwaltung_{info.version}.exe"

    with urllib.request.urlopen(info.download_url, timeout=60) as antwort:
        daten = antwort.read()

    if info.groesse and len(daten) != info.groesse:
        raise RuntimeError(
            f"Download unvollständig ({len(daten)} von {info.groesse} Bytes). "
            "Bitte erneut versuchen."
        )
    download_teil.write_bytes(daten)
    download_teil.replace(neue_exe)

    update_skript = temp_verzeichnis / "baggersee_update.bat"
    update_skript.write_text(
        "@echo off\r\n"
        "set versuche=0\r\n"
        ":warten\r\n"
        f'move /y "{neue_exe}" "{aktuelle_exe}" >nul 2>&1\r\n'
        "if errorlevel 1 (\r\n"
        "    set /a versuche+=1\r\n"
        "    if %versuche% geq 30 goto ende\r\n"
        "    timeout /t 1 /nobreak >nul\r\n"
        "    goto warten\r\n"
        ")\r\n"
        # Kurze Pause, damit z.B. der Virenschutz die frisch geschriebene
        # .exe fertig prüfen kann, bevor sie gestartet wird (sonst kann
        # das ansonsten kryptische "Failed to load Python DLL" auftreten).
        "timeout /t 2 /nobreak >nul\r\n"
        f'start "" "{aktuelle_exe}"\r\n'
        ":ende\r\n"
        'del "%~f0"\r\n',
        encoding="utf-8",
    )

    subprocess.Popen(
        ["cmd", "/c", str(update_skript)],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    sys.exit(0)
