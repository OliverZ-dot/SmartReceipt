"""Recurring subscription model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(slots=True)
class Subscription:
    name: str
    amount: float
    cadence: str  # e.g., monthly, yearly
    next_renewal: date
    active: bool = True
    platform: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = field(default=None, repr=False)

