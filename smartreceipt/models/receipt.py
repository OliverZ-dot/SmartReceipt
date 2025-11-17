"""Receipt model shared across layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Receipt:
    store: str
    purchase_date: datetime
    total: float
    category: str
    items_detected: int = 0
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    warranty_months: Optional[int] = None
    id: Optional[int] = field(default=None, repr=False)

