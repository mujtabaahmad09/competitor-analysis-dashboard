"""
tabs/competitors_tab.py
CRUD interface for managing competitor profiles.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils import BG_DARK, BG_PANEL, BG_CARD, ACCENT, TEXT_LIGHT, TEXT_MUTED, FONT_HEADER, FONT_NORMAL


class CompetitorsTab(ttk.Frame):
    def __init__(self, parent, db, on_change=None):
        super().__init__(parent, style="Panel.TFrame")
        self.db = db
        self.on_change = on_change
        self.selected_id = None
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        # Left: form
        form = tk.Frame(self, bg=BG_PANEL)
        form.pack(side="left", fill="y", padx=(15, 10), pady=15)

        tk.Label(form, text="Competitor Profile", font=FONT_HEADER, bg=BG_PANEL, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

        self.name_var = tk.StringVar()
        self.website_var = tk.StringVar()
        self.category_var = tk.StringVar()

        self._field(form, "Name *", self.name_var)
        self._field(form, "Website", self.website_var)
        self._field(form, "Category", self.category_var)

        tk.Label(form, text="Notes", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        self.notes_text = tk.Text(form, width=32, height=6, bg=BG_CARD, fg=TEXT_LIGHT,
                                   insertbackground=TEXT_LIGHT, relief="flat", font=FONT_NORMAL)
        self.notes_text.pack(pady=(0, 10))

        btn_frame = tk.Frame(form, bg=BG_PANEL)
        btn_frame.pack(fill="x", pady=5)

        tk.Button(btn_frame, text="Add", command=self.add_competitor, bg=ACCENT, fg="#1a202c",
                   relief="flat", font=FONT_NORMAL, width=8).grid(row=0, column=0, padx=2, pady=2)
        tk.Button(btn_frame, text="Update", command=self.update_competitor, bg=BG_CARD, fg=TEXT_LIGHT,
                   relief="flat", font=FONT_NORMAL, width=8).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(btn_frame, text="Delete", command=self.delete_competitor, bg="#e53e3e", fg="white",
                   relief="flat", font=FONT_NORMAL, width=8).grid(row=0, column=2, padx=2, pady=2)
        tk.Button(btn_frame, text="Clear", command=self.clear_form, bg=BG_CARD, fg=TEXT_LIGHT,
                   relief="flat", font=FONT_NORMAL, width=8).grid(row=1, column=0, padx=2, pady=2, columnspan=3, sticky="ew")

        # Right: table
        table_frame = tk.Frame(self, bg=BG_DARK)
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)

        tk.Label(table_frame, text="All Competitors", font=FONT_HEADER, bg=BG_DARK, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 8))

        columns = ("id", "name", "website", "category", "notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18, style="Custom.Treeview")
        headers = {"id": "ID", "name": "Name", "website": "Website", "category": "Category", "notes": "Notes"}
        widths = {"id": 40, "name": 140, "website": 160, "category": 110, "notes": 220}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

    def _field(self, parent, label, var):
        tk.Label(parent, text=label, font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        tk.Entry(parent, textvariable=var, width=34, bg=BG_CARD, fg=TEXT_LIGHT,
                  insertbackground=TEXT_LIGHT, relief="flat", font=FONT_NORMAL).pack(ipady=4)

    # ------------------------------------------------------------------
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.db.get_competitors():
            comp_id, name, website, category, notes, created_at = row
            short_notes = (notes[:40] + "...") if notes and len(notes) > 40 else (notes or "")
            self.tree.insert("", "end", values=(comp_id, name, website or "", category or "", short_notes))
        if self.on_change:
            self.on_change()

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.selected_id = int(values[0])
        # fetch full record (notes may be truncated in tree)
        for row in self.db.get_competitors():
            if row[0] == self.selected_id:
                self.name_var.set(row[1])
                self.website_var.set(row[2] or "")
                self.category_var.set(row[3] or "")
                self.notes_text.delete("1.0", "end")
                self.notes_text.insert("1.0", row[4] or "")
                break

    def clear_form(self):
        self.selected_id = None
        self.name_var.set("")
        self.website_var.set("")
        self.category_var.set("")
        self.notes_text.delete("1.0", "end")
        self.tree.selection_remove(self.tree.selection())

    # ------------------------------------------------------------------
    def add_competitor(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Competitor name is required.")
            return
        try:
            self.db.add_competitor(
                name, self.website_var.get().strip(), self.category_var.get().strip(),
                self.notes_text.get("1.0", "end").strip()
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not add competitor:\n{e}")
            return
        self.clear_form()
        self.refresh()

    def update_competitor(self):
        if not self.selected_id:
            messagebox.showinfo("Select a competitor", "Select a row from the table to update.")
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Competitor name is required.")
            return
        self.db.update_competitor(
            self.selected_id, name, self.website_var.get().strip(),
            self.category_var.get().strip(), self.notes_text.get("1.0", "end").strip()
        )
        self.clear_form()
        self.refresh()

    def delete_competitor(self):
        if not self.selected_id:
            messagebox.showinfo("Select a competitor", "Select a row from the table to delete.")
            return
        if messagebox.askyesno("Confirm delete", "Delete this competitor and all related pricing/promotion data?"):
            self.db.delete_competitor(self.selected_id)
            self.clear_form()
            self.refresh()

    def get_competitor_map(self):
        """name -> id map, used by other tabs"""
        return {name: cid for cid, name in self.db.get_competitor_names()}
