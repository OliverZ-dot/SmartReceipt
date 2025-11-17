"""Dashboard widgets rendered via Matplotlib inside PyQt."""

from __future__ import annotations

from typing import Dict

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from smartreceipt.core.calculator import budget_progress, category_progress
from smartreceipt.core.database import Database


class DashboardView(QWidget):
    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = db
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.summary_label = QLabel()
        self.progress = QProgressBar()
        self.category_progress_label = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.summary_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.canvas)
        layout.addWidget(self.category_progress_label)
        self.setLayout(layout)

        for label in (self.summary_label, self.category_progress_label):
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.refresh()

    def refresh(self) -> None:
        data = self.db.monthly_totals()
        budget = self.db.get_budget()
        total_spent = data["total"]
        summary = f"This month: ${total_spent:.2f}"
        if budget:
            summary += f" / Budget ${budget.total_limit:.2f}"
            self.progress.setValue(int(budget_progress(budget.total_limit, total_spent) * 100))
        else:
            self.progress.setValue(0)
        self.summary_label.setText(summary)
        self._render_chart(data["by_category"])

        if budget:
            category_prog = category_progress(budget.category_limits, data["by_category"])
            text = "Category Progress:\n" + "\n".join(
                f" - {category}: {int(progress * 100)}%" for category, progress in category_prog.items()
            )
        else:
            text = "Scan receipts to unlock category insights."
        self.category_progress_label.setText(text)

    def _render_chart(self, data: Dict[str, float]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if data:
            labels = list(data.keys())
            values = list(data.values())
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
            ax.set_title("Spending by Category")
        else:
            ax.text(0.5, 0.5, "No receipts yet", ha="center", va="center")
        self.canvas.draw_idle()

