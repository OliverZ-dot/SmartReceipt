"""Receipt scanner view."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from smartreceipt.core.categorizer import Categorizer
from smartreceipt.core.database import Database
from smartreceipt.core.ocr_engine import OCRResult, extract_details
from smartreceipt.models.receipt import Receipt


class ReceiptScannerView(QWidget):
    def __init__(
        self,
        db: Database,
        parent: QWidget | None = None,
        on_receipt_saved=None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.categorizer = Categorizer()
        self.current_result: OCRResult | None = None
        self._on_receipt_saved = on_receipt_saved

        self.instructions = QLabel(
            "Snap or import a receipt image to auto-fill store, date, total, and category."
        )
        self.instructions.setWordWrap(True)

        self.scan_button = QPushButton("Select Receipt Image")
        self.scan_button.clicked.connect(self._on_select_image)

        self.store_input = QLineEdit()
        self.date_input = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.total_input = QLineEdit("0.00")
        self.category_input = QLineEdit("Other")
        self.items_input = QSpinBox()
        self.items_input.setRange(0, 200)
        self.payment_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Store", self.store_input)
        form.addRow("Date (YYYY-MM-DD)", self.date_input)
        form.addRow("Total ($)", self.total_input)
        form.addRow("Category", self.category_input)
        form.addRow("Items detected", self.items_input)
        form.addRow("Payment method", self.payment_input)

        self.save_button = QPushButton("Save Receipt")
        self.save_button.clicked.connect(self._save_receipt)
        self.status_label = QLabel()

        buttons = QHBoxLayout()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.status_label)

        layout = QVBoxLayout()
        layout.addWidget(self.instructions)
        layout.addWidget(self.scan_button)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addStretch()
        self.setLayout(layout)

    def _on_select_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select receipt image", str(Path.home()), "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path:
            return
        result = extract_details(Path(file_path))
        self.current_result = result
        self.store_input.setText(result.store)
        self.date_input.setText(result.date.strftime("%Y-%m-%d"))
        self.total_input.setText(f"{result.total:.2f}")
        category = self.categorizer.categorize(result.store)
        self.category_input.setText(category)
        self.items_input.setValue(result.items_detected)
        if result.payment_method:
            self.payment_input.setText(result.payment_method)
        self.status_label.setText("✅ OCR complete. Review & save.")

    def _save_receipt(self) -> None:
        try:
            receipt = Receipt(
                store=self.store_input.text().strip() or "Unknown Store",
                purchase_date=datetime.strptime(self.date_input.text(), "%Y-%m-%d"),
                total=float(self.total_input.text()),
                category=self.category_input.text().strip() or "Other",
                items_detected=self.items_input.value(),
                payment_method=self.payment_input.text().strip() or None,
            )
        except ValueError as exc:  # invalid date/total
            self.status_label.setText(f"⚠️ {exc}")
            return

        receipt_id = self.db.add_receipt(receipt)
        self.status_label.setText(f"💾 Receipt #{receipt_id} saved.")
        if callable(self._on_receipt_saved):
            self._on_receipt_saved()


