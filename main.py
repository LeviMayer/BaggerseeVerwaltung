"""
Baggersee-Verwaltung
====================

Einstiegspunkt der Anwendung. Startet die Tkinter-Oberfläche mit zwei
Bereichen: Erfassung der Tagesdaten und Auswertung/Visualisierung.

Build zu einer eigenständigen .exe siehe README.md.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from baggersee import stil, updater
from baggersee.auswertung import AuswertungFrame
from baggersee.datenhaltung import DatenManager
from baggersee.eingabe import EingabeFrame
from baggersee.version import VERSION


class BaggerseeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Baggersee-Verwaltung")
        self.geometry("1150x750")
        self.minsize(950, 650)
        stil.anwenden(self)

        self.datenmanager = DatenManager()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.eingabe_frame = EingabeFrame(notebook, self.datenmanager)
        self.auswertung_frame = AuswertungFrame(notebook, self.datenmanager)

        notebook.add(self.eingabe_frame, text="Erfassung")
        notebook.add(self.auswertung_frame, text="Auswertung")

        # Beim Wechsel zur Auswertung die Diagramme mit den neuesten Daten
        # aktualisieren, falls in der Erfassung zwischenzeitlich etwas
        # geändert wurde.
        notebook.bind("<<NotebookTabChanged>>", self._tab_gewechselt)
        self._notebook = notebook

        self._statusleiste_aufbauen()
        self.after(1500, lambda: self._update_pruefen(manuell=False))

    def _tab_gewechselt(self, _event=None) -> None:
        aktueller_tab = self._notebook.index(self._notebook.select())
        if aktueller_tab == 1:  # Auswertung
            self.auswertung_frame.aktualisieren()

    # ---------- Statusleiste & Auto-Update ----------

    def _statusleiste_aufbauen(self) -> None:
        leiste = tk.Frame(self, bg=stil.PANEL)
        leiste.pack(side="bottom", fill="x")

        tk.Label(
            leiste, text=f"Version {VERSION}", bg=stil.PANEL, fg=stil.GEDIMMT,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=10, pady=4)

        ttk.Button(
            leiste, text="Nach Updates suchen", command=lambda: self._update_pruefen(manuell=True),
        ).pack(side="right", padx=10, pady=3)

    def _update_pruefen(self, manuell: bool) -> None:
        threading.Thread(target=self._update_pruefen_hintergrund, args=(manuell,), daemon=True).start()

    def _update_pruefen_hintergrund(self, manuell: bool) -> None:
        info = updater.neueste_version_pruefen()
        self.after(0, lambda: self._update_ergebnis_anzeigen(info, manuell))

    def _update_ergebnis_anzeigen(self, info, manuell: bool) -> None:
        if info is None:
            if manuell:
                messagebox.showinfo(
                    "Kein Update verfügbar", f"Du verwendest bereits die aktuelle Version ({VERSION})."
                )
            return

        will_update = messagebox.askyesno(
            "Update verfügbar",
            f"Version {info.version} ist verfügbar (aktuell installiert: {VERSION}).\n\n"
            f"{info.notizen}\n\n"
            "Jetzt herunterladen und installieren? Das Programm wird dazu neu gestartet.",
        )
        if not will_update:
            return
        try:
            updater.update_installieren(info)
        except Exception as fehler:
            messagebox.showerror("Update fehlgeschlagen", str(fehler))


def main() -> None:
    app = BaggerseeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
