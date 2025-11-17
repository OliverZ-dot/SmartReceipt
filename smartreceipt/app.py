"""SmartReceipt desktop entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from smartreceipt.core.database import Database
from smartreceipt.gui.main_window import SmartReceiptWindow
from smartreceipt.utils.paths import ensure_app_dirs


def main(database_path: Path | None = None) -> int:
    """Launch the SmartReceipt desktop application."""
    ensure_app_dirs()
    db = Database(database_path)

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("SmartReceipt")
    qt_app.setOrganizationName("SmartReceipt")

    window = SmartReceiptWindow(db)
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())

