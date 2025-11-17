"""SQLite-backed persistence layer for SmartReceipt."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from smartreceipt.models.budget import Budget
from smartreceipt.models.receipt import Receipt
from smartreceipt.utils.paths import APP_DIR

DATE_FMT = "%Y-%m-%d"
MONTH_FMT = "%Y-%m"


class Database:
    """Lightweight wrapper over sqlite3 with helper queries."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.path = db_path or APP_DIR / "smartreceipt.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()
        self._maybe_seed()

    # --------------------------------------------------------------------- schema
    def _ensure_schema(self) -> None:
        script = """
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            total REAL NOT NULL,
            category TEXT NOT NULL,
            items_detected INTEGER DEFAULT 0,
            payment_method TEXT,
            notes TEXT,
            warranty_months INTEGER
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT UNIQUE NOT NULL,
            total_limit REAL NOT NULL,
            category_limits TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS warranties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            store TEXT,
            purchase_date TEXT NOT NULL,
            expires_on TEXT NOT NULL,
            serial_number TEXT,
            receipt_id INTEGER,
            FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS bill_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            total REAL NOT NULL,
            created_at TEXT NOT NULL,
            participants TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            cadence TEXT NOT NULL,
            next_renewal TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            platform TEXT,
            notes TEXT
        );
        """
        self.conn.executescript(script)
        self.conn.commit()

    # ---------------------------------------------------------------------- seed
    def _maybe_seed(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM receipts")
        if cur.fetchone()[0]:
            return

        demo_receipts = [
            Receipt(
                store="Walmart",
                purchase_date=datetime.now(),
                total=47.23,
                category="Groceries",
                items_detected=8,
                payment_method="Visa",
            ),
            Receipt(
                store="Shell",
                purchase_date=datetime.now(),
                total=62.41,
                category="Transport",
                items_detected=1,
                payment_method="Mastercard",
            ),
            Receipt(
                store="Best Buy",
                purchase_date=datetime.now(),
                total=899.99,
                category="Electronics",
                items_detected=3,
                payment_method="Amex",
                warranty_months=24,
            ),
        ]

        for receipt in demo_receipts:
            self.add_receipt(receipt)

        budget = Budget(
            month=datetime.now().strftime(MONTH_FMT),
            total_limit=1500.0,
            category_limits={"Groceries": 400, "Transport": 250, "Dining": 200},
        )
        self.upsert_budget(budget)

    # -------------------------------------------------------------------- receipts
    def add_receipt(self, receipt: Receipt) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO receipts (
                store, purchase_date, total, category, items_detected,
                payment_method, notes, warranty_months
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt.store,
                receipt.purchase_date.strftime(DATE_FMT),
                receipt.total,
                receipt.category,
                receipt.items_detected,
                receipt.payment_method,
                receipt.notes,
                receipt.warranty_months,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_receipts(self, limit: int = 100) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM receipts ORDER BY purchase_date DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()

    def monthly_totals(self, month: str | None = None) -> Dict[str, float]:
        month = month or datetime.now().strftime(MONTH_FMT)
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(SUM(total), 0) as total
            FROM receipts
            WHERE substr(purchase_date, 1, 7) = ?
            """,
            (month,),
        )
        total = cur.fetchone()["total"]
        cur.execute(
            """
            SELECT category, SUM(total) as total
            FROM receipts
            WHERE substr(purchase_date, 1, 7) = ?
            GROUP BY category
            ORDER BY total DESC
            """,
            (month,),
        )
        by_category = {row["category"]: row["total"] for row in cur.fetchall()}
        return {"total": total, "by_category": by_category}

    # ---------------------------------------------------------------------- budget
    def upsert_budget(self, budget: Budget) -> None:
        payload = json.dumps(budget.category_limits)
        self.conn.execute(
            """
            INSERT INTO budgets (month, total_limit, category_limits)
            VALUES (:month, :total_limit, :category_limits)
            ON CONFLICT(month)
            DO UPDATE SET total_limit=:total_limit, category_limits=:category_limits
            """,
            {"month": budget.month, "total_limit": budget.total_limit, "category_limits": payload},
        )
        self.conn.commit()

    def get_budget(self, month: str | None = None) -> Budget | None:
        month = month or datetime.now().strftime(MONTH_FMT)
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM budgets WHERE month = ?", (month,))
        row = cur.fetchone()
        if not row:
            return None
        return Budget(
            month=row["month"],
            total_limit=row["total_limit"],
            category_limits=json.loads(row["category_limits"]),
        )

    # ------------------------------------------------------------------ warranties
    def add_warranty(
        self,
        product: str,
        store: str,
        purchase_date: date,
        expires_on: date,
        serial_number: str | None,
        receipt_id: int | None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO warranties (product, store, purchase_date, expires_on, serial_number, receipt_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                product,
                store,
                purchase_date.strftime(DATE_FMT),
                expires_on.strftime(DATE_FMT),
                serial_number,
                receipt_id,
            ),
        )
        self.conn.commit()

    def list_warranties(self) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT w.*, r.store as receipt_store
            FROM warranties w
            LEFT JOIN receipts r ON w.receipt_id = r.id
            ORDER BY expires_on ASC
            """
        )
        return cur.fetchall()

    # -------------------------------------------------------------------- splits
    def save_bill_split(self, description: str, total: float, participants: Dict[str, float]) -> None:
        payload = json.dumps(participants)
        self.conn.execute(
            """
            INSERT INTO bill_splits (description, total, created_at, participants)
            VALUES (?, ?, ?, ?)
            """,
            (description, total, datetime.utcnow().isoformat(), payload),
        )
        self.conn.commit()

    def list_bill_splits(self, limit: int = 20) -> Sequence[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM bill_splits ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()

    # --------------------------------------------------------------- subscriptions
    def upsert_subscription(
        self,
        name: str,
        amount: float,
        cadence: str,
        next_renewal: date,
        active: bool = True,
        platform: str | None = None,
        notes: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO subscriptions (name, amount, cadence, next_renewal, active, platform, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                amount,
                cadence,
                next_renewal.strftime(DATE_FMT),
                int(active),
                platform,
                notes,
            ),
        )
        self.conn.commit()

    def list_subscriptions(self) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM subscriptions ORDER BY next_renewal ASC")
        return cur.fetchall()

    # -------------------------------------------------------------------- helpers
    def close(self) -> None:
        self.conn.close()

