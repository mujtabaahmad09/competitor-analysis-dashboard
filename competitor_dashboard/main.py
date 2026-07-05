"""
main.py
Competitor Analysis Dashboard
A Tkinter desktop application for tracking competitor pricing, promotions,
and strategy over time.

Run with:  python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import shutil
from datetime import datetime

from database import Database, DB_PATH
from utils import BG_DARK, BG_PANEL, BG_CARD, ACCENT, TEXT_LIGHT, TEXT_MUTED, FONT_NORMAL
from tabs.overview_tab import OverviewTab
from tabs.competitors_tab import CompetitorsTab
from tabs.pricing_tab import PricingTab
from tabs.promotions_tab import PromotionsTab
from tabs.analysis_tab import AnalysisTab


class CompetitorDashboardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Competitor Analysis Dashboard")
        self.geometry("1200x720")
        self.minsize(1000, 650)
        self.configure(bg=BG_DARK)

        self.db = Database()

        self._configure_styles()
        self._build_menu()
        self._build_notebook()

    # ------------------------------------------------------------------
    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=TEXT_LIGHT,
                         padding=(16, 8), font=FONT_NORMAL)
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#1a202c")])

        style.configure("Panel.TFrame", background=BG_DARK)

        style.configure("Custom.Treeview", background=BG_CARD, fieldbackground=BG_CARD,
                         foreground=TEXT_LIGHT, rowheight=26, font=FONT_NORMAL, borderwidth=0)
        style.configure("Custom.Treeview.Heading", background=BG_PANEL, foreground=TEXT_LIGHT,
                         font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Custom.Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#1a202c")])

        style.configure("TCombobox", fieldbackground=BG_CARD, background=BG_CARD, foreground=TEXT_LIGHT)

    # ------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Summary Report (CSV)", command=self.export_report)
        file_menu.add_command(label="Backup Database...", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.overview_tab = OverviewTab(self.notebook, self.db)
        # Build without the on_change callback first — pricing_tab/promotions_tab
        # don't exist yet, so wiring it up too early would crash on the first refresh.
        self.competitors_tab = CompetitorsTab(self.notebook, self.db, on_change=None)
        self.pricing_tab = PricingTab(self.notebook, self.db, self.competitors_tab.get_competitor_map, on_change=self._refresh_all)
        self.promotions_tab = PromotionsTab(self.notebook, self.db, self.competitors_tab.get_competitor_map, on_change=self._refresh_all)
        self.analysis_tab = AnalysisTab(self.notebook, self.db)

        # Now that every tab exists, it's safe to let the Competitors tab trigger a full refresh.
        self.competitors_tab.on_change = self._refresh_all

        self.notebook.add(self.overview_tab, text="  Overview  ")
        self.notebook.add(self.competitors_tab, text="  Competitors  ")
        self.notebook.add(self.pricing_tab, text="  Price Tracking  ")
        self.notebook.add(self.promotions_tab, text="  Promotions  ")
        self.notebook.add(self.analysis_tab, text="  Analysis  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        current = self.notebook.select()
        widget = self.nametowidget(current)
        if widget is self.overview_tab:
            self.overview_tab.refresh()
        elif widget is self.analysis_tab:
            self.analysis_tab.refresh()
        elif widget is self.pricing_tab:
            self.pricing_tab.refresh_competitor_list()
        elif widget is self.promotions_tab:
            self.promotions_tab.refresh_competitor_list()

    def _refresh_all(self):
        # Keep other tabs' competitor dropdowns and stats in sync after any change.
        # Guarded with hasattr in case this fires before every tab has been built.
        if hasattr(self, "overview_tab"):
            self.overview_tab.refresh()
        if hasattr(self, "pricing_tab"):
            self.pricing_tab.refresh_competitor_list()
        if hasattr(self, "promotions_tab"):
            self.promotions_tab.refresh_competitor_list()

    # ------------------------------------------------------------------
    def export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")],
            initialfile=f"competitor_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                stats = self.db.get_summary_stats()
                writer.writerow(["Competitor Analysis Dashboard - Summary Report"])
                writer.writerow(["Generated on", datetime.now().strftime("%Y-%m-%d %H:%M")])
                writer.writerow([])
                writer.writerow(["Total Competitors", stats["total_competitors"]])
                writer.writerow(["Total Products Monitored", stats["total_products"]])
                writer.writerow(["Total Price Points Logged", stats["total_prices"]])
                writer.writerow(["Active Promotions", stats["active_promos"]])
                writer.writerow([])

                writer.writerow(["-- Competitors --"])
                writer.writerow(["ID", "Name", "Website", "Category", "Notes"])
                for row in self.db.get_competitors():
                    writer.writerow([row[0], row[1], row[2], row[3], row[4]])
                writer.writerow([])

                writer.writerow(["-- Price History --"])
                writer.writerow(["Competitor", "Product", "Price", "Currency", "Date"])
                for row in self.db.get_prices():
                    writer.writerow([row[1], row[2], row[3], row[4], row[5]])
                writer.writerow([])

                writer.writerow(["-- Promotions --"])
                writer.writerow(["Competitor", "Title", "Discount %", "Channel", "Start", "End", "Notes"])
                for row in self.db.get_promotions():
                    writer.writerow([row[1], row[2], row[3], row[4], row[5], row[6], row[7]])

            messagebox.showinfo("Export complete", f"Report saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export failed", f"Could not save report:\n{e}")

    def backup_database(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite database", "*.db")],
            initialfile=f"competitor_data_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
        )
        if not path:
            return
        try:
            self.db.conn.commit()
            shutil.copy(DB_PATH, path)
            messagebox.showinfo("Backup complete", f"Database backed up to:\n{path}")
        except Exception as e:
            messagebox.showerror("Backup failed", f"Could not back up database:\n{e}")

    def show_about(self):
        messagebox.showinfo(
            "About",
            "Competitor Analysis Dashboard\n\n"
            "Track competitor pricing, promotions, and strategy in one place.\n"
            "Built with Python, Tkinter, SQLite, and Matplotlib.\n\n"
            "AI (Claude) was used to help plan the architecture, generate\n"
            "boilerplate GUI code, and debug — logic and design decisions\n"
            "were reviewed and understood before use."
        )

    def on_closing(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = CompetitorDashboardApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
