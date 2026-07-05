"""
tabs/overview_tab.py
At-a-glance dashboard: summary cards + recent price change alerts.
"""

import tkinter as tk
from tkinter import ttk
from utils import (BG_DARK, BG_PANEL, BG_CARD, ACCENT, TEXT_LIGHT, TEXT_MUTED,
                    POSITIVE, NEGATIVE, FONT_TITLE, FONT_HEADER, FONT_NORMAL, FONT_SMALL)


class OverviewTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, style="Panel.TFrame")
        self.db = db
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(header, text="Competitor Analysis Dashboard", font=FONT_TITLE, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w")
        tk.Label(header, text="Track competitor pricing, promotions, and strategy shifts at a glance.",
                 font=FONT_NORMAL, bg=BG_DARK, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Cards row
        self.cards_frame = tk.Frame(self, bg=BG_DARK)
        self.cards_frame.pack(fill="x", padx=20, pady=10)
        self.card_labels = {}
        card_defs = [
            ("total_competitors", "Competitors Tracked"),
            ("total_products", "Products Monitored"),
            ("total_prices", "Price Points Logged"),
            ("active_promos", "Active Promotions"),
        ]
        for i, (key, title) in enumerate(card_defs):
            card = tk.Frame(self.cards_frame, bg=BG_CARD, padx=15, pady=15)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            self.cards_frame.grid_columnconfigure(i, weight=1)
            value_lbl = tk.Label(card, text="0", font=("Segoe UI", 22, "bold"), bg=BG_CARD, fg=ACCENT)
            value_lbl.pack(anchor="w")
            tk.Label(card, text=title, font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")
            self.card_labels[key] = value_lbl

        # Alerts section
        alert_frame = tk.Frame(self, bg=BG_DARK)
        alert_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        tk.Label(alert_frame, text="Recent Price Movements", font=FONT_HEADER, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 8))

        columns = ("competitor", "product", "previous", "latest", "change", "date")
        self.tree = ttk.Treeview(alert_frame, columns=columns, show="headings", height=12, style="Custom.Treeview")
        headers = {"competitor": "Competitor", "product": "Product", "previous": "Previous Price",
                   "latest": "Latest Price", "change": "Change", "date": "Date"}
        widths = {"competitor": 140, "product": 180, "previous": 120, "latest": 120, "change": 100, "date": 100}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("up", foreground=NEGATIVE)
        self.tree.tag_configure("down", foreground=POSITIVE)

    # ------------------------------------------------------------------
    def refresh(self):
        stats = self.db.get_summary_stats()
        self.card_labels["total_competitors"].config(text=str(stats["total_competitors"]))
        self.card_labels["total_products"].config(text=str(stats["total_products"]))
        self.card_labels["total_prices"].config(text=str(stats["total_prices"]))
        self.card_labels["active_promos"].config(text=str(stats["active_promos"]))

        for row in self.tree.get_children():
            self.tree.delete(row)
        changes = self.db.get_recent_price_changes(limit=25)
        if not changes:
            self.tree.insert("", "end", values=("--", "No price changes detected yet", "", "", "", ""))
            return
        for c in changes:
            direction = "up" if c["pct_change"] > 0 else "down"
            arrow = "▲" if c["pct_change"] > 0 else "▼"
            change_str = f"{arrow} {abs(c['pct_change']):.1f}%"
            self.tree.insert("", "end", values=(
                c["competitor"], c["product"], f"{c['previous']:,.2f}",
                f"{c['latest']:,.2f}", change_str, c["date"]
            ), tags=(direction,))
