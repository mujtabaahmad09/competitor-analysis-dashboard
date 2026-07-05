"""
tabs/promotions_tab.py
Log and browse competitor promotions/campaigns.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import (BG_DARK, BG_PANEL, BG_CARD, ACCENT, TEXT_LIGHT, TEXT_MUTED, POSITIVE, NEGATIVE,
                    FONT_HEADER, FONT_NORMAL, today_str, parse_float, validate_date, is_promo_active)


class PromotionsTab(ttk.Frame):
    def __init__(self, parent, db, get_competitor_map, on_change=None):
        super().__init__(parent, style="Panel.TFrame")
        self.db = db
        self.get_competitor_map = get_competitor_map
        self.on_change = on_change
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        form = tk.Frame(self, bg=BG_PANEL)
        form.pack(side="left", fill="y", padx=(15, 10), pady=15)

        tk.Label(form, text="Log a Promotion", font=FONT_HEADER, bg=BG_PANEL, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

        tk.Label(form, text="Competitor *", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        self.competitor_combo = ttk.Combobox(form, state="readonly", width=31)
        self.competitor_combo.pack(ipady=3)

        self.title_var = tk.StringVar()
        self.discount_var = tk.StringVar()
        self.channel_var = tk.StringVar()
        self.start_var = tk.StringVar(value=today_str())
        self.end_var = tk.StringVar()

        self._field(form, "Promotion Title *", self.title_var)
        self._field(form, "Discount % ", self.discount_var)
        self._field(form, "Channel (e.g. Instagram, Store)", self.channel_var)
        self._field(form, "Start Date (YYYY-MM-DD)", self.start_var)
        self._field(form, "End Date (YYYY-MM-DD) *", self.end_var)

        tk.Label(form, text="Notes", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        self.notes_text = tk.Text(form, width=32, height=4, bg=BG_CARD, fg=TEXT_LIGHT,
                                   insertbackground=TEXT_LIGHT, relief="flat", font=FONT_NORMAL)
        self.notes_text.pack(pady=(0, 10))

        btn_frame = tk.Frame(form, bg=BG_PANEL)
        btn_frame.pack(fill="x", pady=5)
        tk.Button(btn_frame, text="Add Promotion", command=self.add_promotion, bg=ACCENT, fg="#1a202c",
                   relief="flat", font=FONT_NORMAL).pack(fill="x", pady=2)
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_promotion, bg="#e53e3e", fg="white",
                   relief="flat", font=FONT_NORMAL).pack(fill="x", pady=2)

        # Right: table
        table_frame = tk.Frame(self, bg=BG_DARK)
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)

        tk.Label(table_frame, text="All Promotions", font=FONT_HEADER, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 8))

        columns = ("id", "competitor", "title", "discount", "channel", "start", "end", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=17, style="Custom.Treeview")
        headers = {"id": "ID", "competitor": "Competitor", "title": "Title", "discount": "Disc.%",
                   "channel": "Channel", "start": "Start", "end": "End", "status": "Status"}
        widths = {"id": 35, "competitor": 110, "title": 150, "discount": 55, "channel": 100, "start": 85, "end": 85, "status": 70}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("active", foreground=POSITIVE)
        self.tree.tag_configure("expired", foreground=TEXT_MUTED)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

    def _field(self, parent, label, var):
        tk.Label(parent, text=label, font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        tk.Entry(parent, textvariable=var, width=34, bg=BG_CARD, fg=TEXT_LIGHT,
                  insertbackground=TEXT_LIGHT, relief="flat", font=FONT_NORMAL).pack(ipady=4)

    # ------------------------------------------------------------------
    def refresh_competitor_list(self):
        names = list(self.get_competitor_map().keys())
        self.competitor_combo["values"] = names
        if names and not self.competitor_combo.get():
            self.competitor_combo.current(0)

    def refresh(self):
        self.refresh_competitor_list()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.db.get_promotions():
            promo_id, comp_name, title, discount, channel, start, end, notes, comp_id = row
            active = is_promo_active(end)
            status = "Active" if active else "Expired"
            tag = "active" if active else "expired"
            disc_display = f"{discount:g}" if discount is not None else ""
            self.tree.insert("", "end", values=(promo_id, comp_name, title, disc_display, channel or "", start or "", end or "", status), tags=(tag,))
        if self.on_change:
            self.on_change()

    # ------------------------------------------------------------------
    def add_promotion(self):
        comp_name = self.competitor_combo.get()
        comp_map = self.get_competitor_map()
        if comp_name not in comp_map:
            messagebox.showwarning("Missing competitor", "Add a competitor first (Competitors tab), then select it here.")
            return
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Promotion title is required.")
            return
        discount = parse_float(self.discount_var.get(), default=None)
        start_date = self.start_var.get().strip() or today_str()
        end_date = self.end_var.get().strip()

        if not validate_date(start_date):
            messagebox.showwarning("Invalid date", "Start date must be YYYY-MM-DD.")
            return
        if not end_date or not validate_date(end_date):
            messagebox.showwarning("Invalid date", "End date is required and must be YYYY-MM-DD.")
            return

        self.db.add_promotion(
            comp_map[comp_name], title, discount, self.channel_var.get().strip(),
            start_date, end_date, self.notes_text.get("1.0", "end").strip()
        )
        self.title_var.set("")
        self.discount_var.set("")
        self.channel_var.set("")
        self.end_var.set("")
        self.notes_text.delete("1.0", "end")
        self.refresh()

    def delete_promotion(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select a row", "Select a promotion to delete.")
            return
        promo_id = self.tree.item(selection[0], "values")[0]
        if messagebox.askyesno("Confirm delete", "Delete this promotion?"):
            self.db.delete_promotion(promo_id)
            self.refresh()
