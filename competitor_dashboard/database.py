"""
database.py
Handles all SQLite persistence for the Competitor Analysis Dashboard.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "competitor_data.db")


class Database:
    def __init__(self, db_path=DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                website TEXT,
                category TEXT,
                notes TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'PKR',
                date_recorded TEXT NOT NULL,
                FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                discount_percent REAL,
                channel TEXT,
                start_date TEXT,
                end_date TEXT,
                notes TEXT,
                FOREIGN KEY (competitor_id) REFERENCES competitors (id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Competitors
    # ------------------------------------------------------------------
    def add_competitor(self, name, website="", category="", notes=""):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO competitors (name, website, category, notes, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, website, category, notes, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_competitor(self, comp_id, name, website, category, notes):
        self.conn.execute(
            "UPDATE competitors SET name=?, website=?, category=?, notes=? WHERE id=?",
            (name, website, category, notes, comp_id),
        )
        self.conn.commit()

    def delete_competitor(self, comp_id):
        self.conn.execute("DELETE FROM competitors WHERE id=?", (comp_id,))
        self.conn.commit()

    def get_competitors(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, website, category, notes, created_at FROM competitors ORDER BY name")
        return cur.fetchall()

    def get_competitor_names(self):
        return [(row[0], row[1]) for row in self.get_competitors()]

    # ------------------------------------------------------------------
    # Prices
    # ------------------------------------------------------------------
    def add_price(self, competitor_id, product_name, price, currency, date_recorded=None):
        date_recorded = date_recorded or datetime.now().strftime("%Y-%m-%d")
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO prices (competitor_id, product_name, price, currency, date_recorded) VALUES (?, ?, ?, ?, ?)",
            (competitor_id, product_name, price, currency, date_recorded),
        )
        self.conn.commit()
        return cur.lastrowid

    def delete_price(self, price_id):
        self.conn.execute("DELETE FROM prices WHERE id=?", (price_id,))
        self.conn.commit()

    def get_prices(self, competitor_id=None, product_name=None):
        query = """
            SELECT prices.id, competitors.name, prices.product_name, prices.price,
                   prices.currency, prices.date_recorded, prices.competitor_id
            FROM prices JOIN competitors ON prices.competitor_id = competitors.id
        """
        conditions = []
        params = []
        if competitor_id:
            conditions.append("prices.competitor_id = ?")
            params.append(competitor_id)
        if product_name:
            conditions.append("prices.product_name LIKE ?")
            params.append(f"%{product_name}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY prices.date_recorded DESC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def get_all_product_names(self):
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT product_name FROM prices ORDER BY product_name")
        return [row[0] for row in cur.fetchall()]

    def get_price_history_for_product(self, product_name):
        """Returns rows: competitor_name, price, date_recorded for a given product, sorted by date."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT competitors.name, prices.price, prices.date_recorded
            FROM prices JOIN competitors ON prices.competitor_id = competitors.id
            WHERE prices.product_name = ?
            ORDER BY prices.date_recorded ASC
        """, (product_name,))
        return cur.fetchall()

    # ------------------------------------------------------------------
    # Promotions
    # ------------------------------------------------------------------
    def add_promotion(self, competitor_id, title, discount_percent, channel, start_date, end_date, notes=""):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO promotions (competitor_id, title, discount_percent, channel, start_date, end_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (competitor_id, title, discount_percent, channel, start_date, end_date, notes))
        self.conn.commit()
        return cur.lastrowid

    def delete_promotion(self, promo_id):
        self.conn.execute("DELETE FROM promotions WHERE id=?", (promo_id,))
        self.conn.commit()

    def get_promotions(self, competitor_id=None):
        query = """
            SELECT promotions.id, competitors.name, promotions.title, promotions.discount_percent,
                   promotions.channel, promotions.start_date, promotions.end_date, promotions.notes,
                   promotions.competitor_id
            FROM promotions JOIN competitors ON promotions.competitor_id = competitors.id
        """
        params = []
        if competitor_id:
            query += " WHERE promotions.competitor_id = ?"
            params.append(competitor_id)
        query += " ORDER BY promotions.start_date DESC"
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------
    def get_summary_stats(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM competitors")
        total_competitors = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM prices")
        total_prices = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM promotions WHERE date(end_date) >= date('now')")
        active_promos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT product_name) FROM prices")
        total_products = cur.fetchone()[0]

        return {
            "total_competitors": total_competitors,
            "total_prices": total_prices,
            "active_promos": active_promos,
            "total_products": total_products,
        }

    def get_recent_price_changes(self, limit=10):
        """
        Detects the most recent price change per (competitor, product) pair
        by comparing the two latest recorded prices.
        Returns list of dicts with change info.
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT competitor_id, product_name FROM prices
            GROUP BY competitor_id, product_name
            HAVING COUNT(*) >= 2
        """)
        pairs = cur.fetchall()
        changes = []
        for competitor_id, product_name in pairs:
            cur.execute("""
                SELECT price, date_recorded FROM prices
                WHERE competitor_id=? AND product_name=?
                ORDER BY date_recorded DESC LIMIT 2
            """, (competitor_id, product_name))
            rows = cur.fetchall()
            if len(rows) == 2:
                latest, previous = rows[0][0], rows[1][0]
                if previous != 0:
                    pct_change = ((latest - previous) / previous) * 100
                else:
                    pct_change = 0
                if abs(pct_change) > 0.001:
                    cur.execute("SELECT name FROM competitors WHERE id=?", (competitor_id,))
                    comp_name = cur.fetchone()[0]
                    changes.append({
                        "competitor": comp_name,
                        "product": product_name,
                        "previous": previous,
                        "latest": latest,
                        "pct_change": pct_change,
                        "date": rows[0][1],
                    })
        changes.sort(key=lambda x: x["date"], reverse=True)
        return changes[:limit]

    def close(self):
        self.conn.close()
