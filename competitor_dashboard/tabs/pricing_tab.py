"""
tabs/pricing_tab.py
Log and browse competitor product prices over time.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import (BG_DARK, BG_PANEL, BG_CARD, ACCENT, TEXT_LIGHT, TEXT_MUTED,
                    FONT_HEADER, FONT_NORMAL, today_str, parse_float, validate_date)


class PricingTab(ttk.Frame):
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

        tk.Label(form, text="Record a Price", font=FONT_HEADER, bg=BG_PANEL, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

        tk.Label(form, text="Competitor *", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        self.competitor_combo = ttk.Combobox(form, state="readonly", width=31)
        self.competitor_combo.pack(ipady=3)

        self.product_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.currency_var = tk.StringVar(value="PKR")
        self.date_var = tk.StringVar(value=today_str())

        self._field(form, "Product Name *", self.product_var)
        self._field(form, "Price *", self.price_var)
        self._field(form, "Currency", self.currency_var)
        self._field(form, "Date (YYYY-MM-DD)", self.date_var)

        btn_frame = tk.Frame(form, bg=BG_PANEL)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="Add Price Entry", command=self.add_price, bg=ACCENT, fg="#1a202c",
                   relief="flat", font=FONT_NORMAL).pack(fill="x", pady=2)
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_price, bg="#e53e3e", fg="white",
                   relief="flat", font=FONT_NORMAL).pack(fill="x", pady=2)

        tk.Label(form, text="Filter by Product", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(15, 2))
        self.filter_var = tk.StringVar()
        filter_entry = tk.Entry(form, textvariable=self.filter_var, width=31, bg=BG_CARD, fg=TEXT_LIGHT,
                                 insertbackground=TEXT_LIGHT, relief="flat", font=FONT_NORMAL)
        filter_entry.pack(ipady=4)
        filter_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # Right: table
        table_frame = tk.Frame(self, bg=BG_DARK)
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)

        tk.Label(table_frame, text="Price History", font=FONT_HEADER, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 8))

        columns = ("id", "competitor", "product", "price", "currency", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18, style="Custom.Treeview")
        headers = {"id": "ID", "competitor": "Competitor", "product": "Product",
                   "price": "Price", "currency": "Cur.", "date": "Date"}
        widths = {"id": 40, "competitor": 130, "product": 160, "price": 90, "currency": 55, "date": 100}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True)

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
        product_filter = self.filter_var.get().strip() or None
        for row in self.db.get_prices(product_name=product_filter):
            price_id, comp_name, product, price, currency, date_recorded, comp_id = row
            self.tree.insert("", "end", values=(price_id, comp_name, product, f"{price:,.2f}", currency, date_recorded))
        if self.on_change:
            self.on_change()

    # ------------------------------------------------------------------
    def add_price(self):
        comp_name = self.competitor_combo.get()
        comp_map = self.get_competitor_map()
        if comp_name not in comp_map:
            messagebox.showwarning("Missing competitor", "Add a competitor first (Competitors tab), then select it here.")
            return
        product = self.product_var.get().strip()
        price = parse_float(self.price_var.get())
        date_str = self.date_var.get().strip() or today_str()

        if not product:
            messagebox.showwarning("Missing product", "Product name is required.")
            return
        if price is None:
            messagebox.showwarning("Invalid price", "Enter a valid numeric price.")
            return
        if not validate_date(date_str):
            messagebox.showwarning("Invalid date", "Date must be in YYYY-MM-DD format.")
            return

        self.db.add_price(comp_map[comp_name], product, price, self.currency_var.get().strip() or "PKR", date_str)
        self.product_var.set("")
        self.price_var.set("")
        self.date_var.set(today_str())
        self.refresh()

    def delete_price(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select a row", "Select a price entry to delete.")
            return
        price_id = self.tree.item(selection[0], "values")[0]
        if messagebox.askyesno("Confirm delete", "Delete this price entry?"):
            self.db.delete_price(price_id)
            self.refresh()
