"""
Einheitliches, dunkles Erscheinungsbild für die gesamte Anwendung.

Definiert die Farbpalette (angelehnt an die Kalenderkachel der Erfassung)
und wendet sie über ttk.Style auf alle Standard-Widgets an, damit Fenster,
Formulare, Tabs und Diagramme wie aus einem Guss wirken.
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

# ---------- Farbpalette ----------

HINTERGRUND = "#1e1e1e"
PANEL = "#262626"
PANEL_HELL = "#333333"
RAHMEN = "#3a3a3a"

VORDERGRUND = "#e8e8e8"
SEKUNDAER = "#8a8a8a"
GEDIMMT = "#5a5a5a"

AKZENT = "#4c6ef5"
AKZENT_DUNKEL = "#3b5bdb"

FEHLER = "#ff6b6b"
ERFOLG = "#51cf66"
WARNUNG = "#ff922b"
INFO = "#22b8cf"
GELB = "#ffd43b"

SCHRIFT = ("Segoe UI", 10)
SCHRIFT_FETT = ("Segoe UI", 10, "bold")
SCHRIFT_TITEL = ("Segoe UI", 13, "bold")


def anwenden(root: tk.Tk) -> None:
    """Wendet das dunkle Farbschema auf das Fenster und alle ttk-Widgets an."""
    root.configure(bg=HINTERGRUND)
    _dunkler_titelbalken(root)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=HINTERGRUND, foreground=VORDERGRUND, font=SCHRIFT)

    style.configure("TFrame", background=HINTERGRUND)
    style.configure("TLabel", background=HINTERGRUND, foreground=VORDERGRUND)
    style.configure("Fehler.TLabel", background=HINTERGRUND, foreground=FEHLER)
    style.configure("Sekundaer.TLabel", background=HINTERGRUND, foreground=SEKUNDAER)

    style.configure(
        "TButton",
        background=PANEL_HELL,
        foreground=VORDERGRUND,
        bordercolor=RAHMEN,
        relief="flat",
        padding=(12, 6),
    )
    style.map(
        "TButton",
        background=[("pressed", AKZENT_DUNKEL), ("active", AKZENT)],
        foreground=[("pressed", "white"), ("active", "white")],
    )

    style.configure(
        "TEntry",
        fieldbackground=PANEL,
        foreground=VORDERGRUND,
        bordercolor=RAHMEN,
        insertcolor=VORDERGRUND,
        padding=4,
    )
    style.map(
        "TEntry",
        fieldbackground=[("focus", PANEL_HELL)],
        bordercolor=[("focus", AKZENT)],
    )

    style.configure(
        "TNotebook", background=HINTERGRUND, bordercolor=HINTERGRUND, tabmargins=(4, 6, 4, 0)
    )
    style.configure(
        "TNotebook.Tab",
        background=PANEL,
        foreground=SEKUNDAER,
        padding=(16, 8),
        font=SCHRIFT,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", AKZENT)],
        foreground=[("selected", "white")],
    )

    style.configure(
        "TLabelframe", background=HINTERGRUND, bordercolor=RAHMEN, relief="solid", borderwidth=1
    )
    style.configure(
        "TLabelframe.Label", background=HINTERGRUND, foreground=VORDERGRUND, font=SCHRIFT_FETT
    )

    style.configure("TSeparator", background=RAHMEN)

    style.configure(
        "TScrollbar",
        background=PANEL_HELL,
        troughcolor=HINTERGRUND,
        bordercolor=HINTERGRUND,
        arrowcolor=VORDERGRUND,
    )
    style.map("TScrollbar", background=[("active", AKZENT)])

    style.configure(
        "Treeview",
        background=PANEL,
        fieldbackground=PANEL,
        foreground=VORDERGRUND,
        bordercolor=RAHMEN,
        rowheight=24,
    )
    style.configure(
        "Treeview.Heading",
        background=PANEL_HELL,
        foreground=VORDERGRUND,
        bordercolor=RAHMEN,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", AKZENT)],
        foreground=[("selected", "white")],
    )


def _dunkler_titelbalken(root: tk.Tk) -> None:
    """Aktiviert unter Windows 10/11 den dunklen Fenstertitelbalken, falls verfügbar."""
    if sys.platform != "win32":
        return

    def _setzen() -> None:
        try:
            import ctypes

            root.update()
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            wert = ctypes.c_int(1)
            for attribut in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (neuere/ältere Windows-Builds)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribut, ctypes.byref(wert), ctypes.sizeof(wert)
                )
        except Exception:
            pass

    root.after(50, _setzen)


def dunkle_toolbar(toolbar: tk.Widget) -> None:
    """Färbt eine matplotlib NavigationToolbar2Tk (klassische Tk-Widgets, kein
    ttk) passend zum dunklen Farbschema ein."""
    toolbar.configure(bg=PANEL)
    for kind in toolbar.winfo_children():
        try:
            kind.configure(bg=PANEL)
        except tk.TclError:
            continue
        if isinstance(kind, tk.Label):
            kind.configure(fg=SEKUNDAER)
