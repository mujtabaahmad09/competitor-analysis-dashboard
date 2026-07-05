"""
utils.py
Shared style constants and small helper functions used across tabs.
"""

from datetime import datetime

# Color palette
BG_DARK = "#1e2530"
BG_PANEL = "#262f3d"
BG_CARD = "#2d3748"
ACCENT = "#4fd1c5"
ACCENT_DARK = "#38b2ac"
TEXT_LIGHT = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
POSITIVE = "#48bb78"
NEGATIVE = "#f56565"
WARNING = "#ed8936"

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def is_promo_active(end_date_str):
    try:
        end = datetime.strptime(end_date_str, "%Y-%m-%d")
        return end.date() >= datetime.now().date()
    except (TypeError, ValueError):
        return False
