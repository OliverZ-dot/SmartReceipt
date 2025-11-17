"""Primary PyQt window housing all SmartReceipt experiences."""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from smartreceipt.core.calculator import (
    category_progress,
    equal_split,
    project_subscription_cost,
)
from smartreceipt.core.database import Database
from smartreceipt.gui.charts import DashboardView
from smartreceipt.gui.export import ExportWizard
from smartreceipt.gui.scanner import ReceiptScannerView
from smartreceipt.utils.payment_links import paypal_link, venmo_link, zelle_instructions


class SmartReceiptWindow(QMainWindow):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("SmartReceipt")
        self.resize(1100, 720)

        self.tabs = QTabWidget()
        self.dashboard_view = DashboardView(db)
        self.scanner_view = ReceiptScannerView(db, on_receipt_saved=self.refresh_dashboard)
        self.receipts_view = ReceiptsTableView(db)
        self.budget_view = BudgetView(db, on_budget_updated=self.refresh_dashboard)
        self.export_view = ExportWizard(db)
        self.warranty_view = WarrantyView(db)
        self.bill_split_view = BillSplitView(db)
        self.subscription_view = SubscriptionView(db)

        self.tabs.addTab(self.dashboard_view, "Dashboard")
        self.tabs.addTab(self.scanner_view, "Scanner")
        self.tabs.addTab(self.receipts_view, "Receipts")
        self.tabs.addTab(self.budget_view, "Budget")
        self.tabs.addTab(self.export_view, "Tax Export")
        self.tabs.addTab(self.warranty_view, "Warranty Vault")
        self.tabs.addTab(self.bill_split_view, "Bill Splitter")
        self.tabs.addTab(self.subscription_view, "Subscriptions")

        self.setCentralWidget(self.tabs)

    def refresh_dashboard(self) -> None:
        self.dashboard_view.refresh()
        self.receipts_view.refresh()


class ReceiptsTableView(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.table = QTableWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()

    def refresh(self) -> None:
        rows = self.db.list_receipts()
        headers = ["Store", "Date", "Total", "Category", "Payment"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["store"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row["purchase_date"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"${row['total']:.2f}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row["category"]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row["payment_method"] or "-"))
        self.table.resizeColumnsToContents()


class BudgetView(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None, on_budget_updated=None) -> None:
        super().__init__(parent)
        self.db = db
        self.on_budget_updated = on_budget_updated
        self.total_limit_input = QLineEdit()
        self.category_limits_input = QTextEdit()
        self.save_button = QPushButton("Save Budget")
        self.save_button.clicked.connect(self._save_budget)
        self.status_label = QLabel()

        layout = QVBoxLayout()
        form = QFormLayout()
        form.addRow("Monthly total limit ($)", self.total_limit_input)
        form.addRow("Category limits (e.g., Groceries:400)", self.category_limits_input)
        layout.addLayout(form)
        layout.addWidget(self.save_button)
        layout.addWidget(self.status_label)

        self.progress_label = QLabel()
        layout.addWidget(self.progress_label)
        layout.addStretch()
        self.setLayout(layout)

        self._load_budget()

    def _load_budget(self) -> None:
        budget = self.db.get_budget()
        if not budget:
            self.total_limit_input.setText("1500")
            self.category_limits_input.setPlainText("Groceries:400\nTransport:250\nDining:200")
            return
        self.total_limit_input.setText(str(budget.total_limit))
        lines = "\n".join(f"{k}:{v}" for k, v in budget.category_limits.items())
        self.category_limits_input.setPlainText(lines)
        summary = self.db.monthly_totals()
        progress = category_progress(budget.category_limits, summary["by_category"])
        progress_line = "\n".join(f"{cat}: {int(val * 100)}%" for cat, val in progress.items())
        self.progress_label.setText(f"Progress\n{progress_line}")

    def _save_budget(self) -> None:
        from smartreceipt.models.budget import Budget

        try:
            total = float(self.total_limit_input.text())
        except ValueError:
            self.status_label.setText("⚠️ Invalid total limit")
            return
        category_lines = self.category_limits_input.toPlainText().splitlines()
        categories: Dict[str, float] = {}
        for line in category_lines:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            try:
                categories[key.strip()] = float(value.strip())
            except ValueError:
                continue
        budget = Budget(month=datetime.now().strftime("%Y-%m"), total_limit=total, category_limits=categories)
        self.db.upsert_budget(budget)
        self.status_label.setText("✅ Budget saved")
        if callable(self.on_budget_updated):
            self.on_budget_updated()


class WarrantyView(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.list_widget = QListWidget()
        self.product_input = QLineEdit()
        self.store_input = QLineEdit()
        self.purchase_input = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.expire_input = QLineEdit((date.today().replace(year=date.today().year + 1)).strftime("%Y-%m-%d"))
        self.serial_input = QLineEdit()
        self.save_button = QPushButton("Store Warranty")
        self.save_button.clicked.connect(self._save_warranty)
        self.status_label = QLabel()

        form = QFormLayout()
        form.addRow("Product", self.product_input)
        form.addRow("Store", self.store_input)
        form.addRow("Purchase date", self.purchase_input)
        form.addRow("Warranty expires", self.expire_input)
        form.addRow("Serial #", self.serial_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.save_button)
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Saved warranties"))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self._refresh()

    def _refresh(self) -> None:
        self.list_widget.clear()
        for entry in self.db.list_warranties():
            item = QListWidgetItem(
                f"{entry['product']} • Expires {entry['expires_on']} • Serial {entry['serial_number'] or '-'}"
            )
            self.list_widget.addItem(item)

    def _save_warranty(self) -> None:
        try:
            purchase = datetime.strptime(self.purchase_input.text(), "%Y-%m-%d").date()
            expires = datetime.strptime(self.expire_input.text(), "%Y-%m-%d").date()
        except ValueError:
            self.status_label.setText("⚠️ Invalid dates")
            return
        self.db.add_warranty(
            product=self.product_input.text(),
            store=self.store_input.text(),
            purchase_date=purchase,
            expires_on=expires,
            serial_number=self.serial_input.text() or None,
            receipt_id=None,
        )
        self.status_label.setText("📦 Warranty saved")
        self._refresh()


class BillSplitView(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.description_input = QLineEdit("Dinner at Olive Garden")
        self.total_input = QLineEdit("87.50")
        self.participants_input = QLineEdit("You,Sarah,Mike")
        self.calculate_button = QPushButton("Calculate Split")
        self.calculate_button.clicked.connect(self._calculate)
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)

        layout = QVBoxLayout()
        form = QFormLayout()
        form.addRow("Description", self.description_input)
        form.addRow("Total ($)", self.total_input)
        form.addRow("Participants (comma separated)", self.participants_input)
        layout.addLayout(form)
        layout.addWidget(self.calculate_button)
        layout.addWidget(self.result_box)
        self.setLayout(layout)

    def _calculate(self) -> None:
        try:
            total = float(self.total_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid total", "Enter a valid total amount.")
            return
        participants = [p.strip() for p in self.participants_input.text().split(",") if p.strip()]
        shares = equal_split(total, participants)
        self.db.save_bill_split(self.description_input.text(), total, shares)
        lines = ["Share results:"]
        for person, amount in shares.items():
            venmo = venmo_link(person.lower(), amount, note=self.description_input.text())
            paypal = paypal_link(person.lower(), amount)
            zelle = zelle_instructions(person, amount)
            lines.append(f"{person}: ${amount:.2f}")
            lines.append(f"  Venmo: {venmo}")
            lines.append(f"  PayPal: {paypal}")
            lines.append(f"  Zelle: {zelle}")
        self.result_box.setPlainText("\n".join(lines))


class SubscriptionView(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.name_input = QLineEdit("Netflix")
        self.amount_input = QLineEdit("15.99")
        self.cadence_input = QLineEdit("Monthly")
        self.next_input = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.save_button = QPushButton("Save Subscription")
        self.save_button.clicked.connect(self._save_sub)
        self.list_widget = QListWidget()
        self.summary_label = QLabel()

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("Amount ($)", self.amount_input)
        form.addRow("Cadence", self.cadence_input)
        form.addRow("Next renewal", self.next_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.save_button)
        layout.addWidget(self.summary_label)
        layout.addWidget(QLabel("Active subscriptions"))
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self._refresh()

    def _save_sub(self) -> None:
        try:
            amount = float(self.amount_input.text())
            next_renewal = datetime.strptime(self.next_input.text(), "%Y-%m-%d").date()
        except ValueError:
            QMessageBox.warning(self, "Invalid input", "Check amount and renewal date.")
            return
        self.db.upsert_subscription(
            name=self.name_input.text(),
            amount=amount,
            cadence=self.cadence_input.text(),
            next_renewal=next_renewal,
        )
        self._refresh()

    def _refresh(self) -> None:
        self.list_widget.clear()
        subs = self.db.list_subscriptions()
        summary = project_subscription_cost(
            [(row["name"], row["amount"], row["cadence"]) for row in subs]
        )
        self.summary_label.setText(
            f"Monthly: ${summary['monthly']:.2f} | Yearly: ${summary['yearly']:.2f}"
        )
        for row in subs:
            text = f"{row['name']} • ${row['amount']:.2f}/{row['cadence']} • Next {row['next_renewal']}"
            self.list_widget.addItem(QListWidgetItem(text))

