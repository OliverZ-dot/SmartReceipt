"""Tax export wizard widget."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from smartreceipt.core.database import Database
from smartreceipt.utils.pdf_generator import build_tax_report


class ExportWizard(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.year_select = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year, current_year - 5, -1):
            self.year_select.addItem(str(year))

        self.generate_button = QPushButton("Generate Tax Report")
        self.generate_button.clicked.connect(self._generate_report)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        form = QFormLayout()
        form.addRow("Tax year", self.year_select)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.generate_button)
        layout.addWidget(QLabel("Preview"))
        layout.addWidget(self.preview)
        self.setLayout(layout)

    def _generate_report(self) -> None:
        year = int(self.year_select.currentText())
        receipts = [
            dict(row)
            for row in self.db.list_receipts(limit=500)
            if row["purchase_date"].startswith(str(year))
        ]
        category_totals = {}
        for entry in receipts:
            category_totals.setdefault(entry["category"], 0.0)
            category_totals[entry["category"]] += entry["total"]

        path = build_tax_report(year, category_totals, receipts)
        lines = [
            f"Year: {year}",
            f"Generated file: {path}",
            "",
            "Category totals:",
        ]
        for category, amount in category_totals.items():
            lines.append(f" - {category}: ${amount:.2f}")
        self.preview.setPlainText("\n".join(lines))

