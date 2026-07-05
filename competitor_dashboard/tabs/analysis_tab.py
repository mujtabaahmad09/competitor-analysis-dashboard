"""
tabs/analysis_tab.py
Visual analysis: price trends, price comparisons, and promotion frequency,
rendered with matplotlib embedded inside Tkinter.
"""

import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils import BG_DARK, BG_PANEL, BG_CARD, ACCENT, TEXT_LIGHT, TEXT_MUTED, FONT_HEADER, FONT_NORMAL

CHART_COLORS = ["#4fd1c5", "#f6ad55", "#fc8181", "#63b3ed", "#b794f4", "#68d391", "#f687b3"]


class AnalysisTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, style="Panel.TFrame")
        self.db = db
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self):
        controls = tk.Frame(self, bg=BG_PANEL)
        controls.pack(side="left", fill="y", padx=(15, 10), pady=15)

        tk.Label(controls, text="Analysis Controls", font=FONT_HEADER, bg=BG_PANEL, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 10))

        tk.Label(controls, text="Chart Type", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(4, 2))
        self.chart_type = ttk.Combobox(controls, state="readonly", width=27,
                                        values=["Price Trend Over Time", "Average Price Comparison", "Promotion Frequency"])
        self.chart_type.current(0)
        self.chart_type.pack(ipady=3)
        self.chart_type.bind("<<ComboboxSelected>>", lambda e: self.draw_chart())

        tk.Label(controls, text="Product", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", pady=(12, 2))
        self.product_combo = ttk.Combobox(controls, state="readonly", width=27)
        self.product_combo.pack(ipady=3)
        self.product_combo.bind("<<ComboboxSelected>>", lambda e: self.draw_chart())

        tk.Button(controls, text="Refresh", command=self.refresh, bg=ACCENT, fg="#1a202c",
                   relief="flat", font=FONT_NORMAL).pack(fill="x", pady=(20, 4))

        self.insight_label = tk.Label(controls, text="", font=FONT_NORMAL, bg=BG_PANEL, fg=TEXT_MUTED,
                                       wraplength=230, justify="left")
        self.insight_label.pack(anchor="w", pady=(20, 0))

        # Chart canvas area
        chart_frame = tk.Frame(self, bg=BG_DARK)
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)

        self.fig = plt.Figure(figsize=(7.5, 5.5), dpi=100)
        self.fig.patch.set_facecolor(BG_DARK)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def refresh(self):
        products = self.db.get_all_product_names()
        self.product_combo["values"] = products
        if products and not self.product_combo.get():
            self.product_combo.current(0)
        self.draw_chart()

    def _style_axes(self):
        self.ax.clear()
        self.ax.set_facecolor(BG_PANEL)
        self.ax.tick_params(colors=TEXT_LIGHT, labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(TEXT_MUTED)
        self.ax.title.set_color(TEXT_LIGHT)
        self.ax.xaxis.label.set_color(TEXT_MUTED)
        self.ax.yaxis.label.set_color(TEXT_MUTED)

    def draw_chart(self):
        chart = self.chart_type.get()
        self._style_axes()
        if chart == "Price Trend Over Time":
            self._draw_price_trend()
        elif chart == "Average Price Comparison":
            self._draw_price_comparison()
        elif chart == "Promotion Frequency":
            self._draw_promo_frequency()
        self.fig.tight_layout()
        self.canvas.draw()

    # ------------------------------------------------------------------
    def _draw_price_trend(self):
        product = self.product_combo.get()
        if not product:
            self.ax.set_title("No product data yet — add price entries first")
            self.insight_label.config(text="")
            return
        history = self.db.get_price_history_for_product(product)
        by_competitor = defaultdict(list)
        for comp_name, price, date_str in history:
            by_competitor[comp_name].append((date_str, price))

        for i, (comp_name, points) in enumerate(by_competitor.items()):
            points.sort(key=lambda p: p[0])
            dates = [datetime.strptime(p[0], "%Y-%m-%d") for p in points]
            prices = [p[1] for p in points]
            color = CHART_COLORS[i % len(CHART_COLORS)]
            self.ax.plot(dates, prices, marker="o", label=comp_name, color=color, linewidth=2)

        self.ax.set_title(f"Price Trend: {product}")
        self.ax.set_ylabel("Price")
        self.ax.legend(facecolor=BG_PANEL, labelcolor=TEXT_LIGHT, fontsize=8, loc="best")
        self.fig.autofmt_xdate(rotation=30)

        # Insight: cheapest competitor currently
        if by_competitor:
            latest_prices = {c: pts[-1][1] for c, pts in by_competitor.items()}
            cheapest = min(latest_prices, key=latest_prices.get)
            priciest = max(latest_prices, key=latest_prices.get)
            self.insight_label.config(
                text=f"Cheapest for '{product}': {cheapest} ({latest_prices[cheapest]:,.2f})\n"
                     f"Most expensive: {priciest} ({latest_prices[priciest]:,.2f})"
            )

    def _draw_price_comparison(self):
        product = self.product_combo.get()
        if not product:
            self.ax.set_title("No product data yet — add price entries first")
            self.insight_label.config(text="")
            return
        history = self.db.get_price_history_for_product(product)
        totals = defaultdict(list)
        for comp_name, price, _ in history:
            totals[comp_name].append(price)

        names = list(totals.keys())
        averages = [sum(v) / len(v) for v in totals.values()]
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(names))]

        self.ax.bar(names, averages, color=colors)
        self.ax.set_title(f"Average Price by Competitor: {product}")
        self.ax.set_ylabel("Average Price")
        self.ax.tick_params(axis="x", rotation=20)

        if averages:
            lowest_idx = averages.index(min(averages))
            self.insight_label.config(
                text=f"{names[lowest_idx]} offers the lowest average price for '{product}' "
                     f"at {averages[lowest_idx]:,.2f}."
            )

    def _draw_promo_frequency(self):
        promotions = self.db.get_promotions()
        counts = defaultdict(int)
        for row in promotions:
            comp_name = row[1]
            counts[comp_name] += 1

        names = list(counts.keys())
        values = list(counts.values())
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(names))]

        if not names:
            self.ax.set_title("No promotions logged yet")
            self.insight_label.config(text="")
            return

        self.ax.bar(names, values, color=colors)
        self.ax.set_title("Promotion Frequency by Competitor")
        self.ax.set_ylabel("Number of Promotions")
        self.ax.tick_params(axis="x", rotation=20)

        most_active = names[values.index(max(values))]
        self.insight_label.config(
            text=f"{most_active} runs the most promotions ({max(values)} logged) — "
                 f"worth watching their campaign cadence."
        )
