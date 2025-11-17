"""Utility helpers for working with SmartReceipt directories."""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(os.getenv("SMARTRECEIPT_HOME", Path.home() / ".smartreceipt"))
MEDIA_DIR = APP_DIR / "media"
EXPORT_DIR = APP_DIR / "exports"


def ensure_app_dirs() -> None:
    """Ensure required directories exist."""
    for path in (APP_DIR, MEDIA_DIR, EXPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)

