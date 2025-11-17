"""Budget, bill split, and subscription math helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Tuple


def budget_progress(total_limit: float, spent: float) -> float:
    if total_limit <= 0:
        return 0.0
    return min(spent / total_limit, 1.5)  # allow slight exceed for UI indicators


def category_progress(category_limits: Dict[str, float], spent_by_category: Dict[str, float]) -> Dict[str, float]:
    progress = {}
    for category, limit in category_limits.items():
        spent = spent_by_category.get(category, 0.0)
        progress[category] = budget_progress(limit, spent)
    return progress


def equal_split(total: float, participants: List[str]) -> Dict[str, float]:
    share = round(total / max(len(participants), 1), 2)
    return {person: share for person in participants}


def custom_split(shares: Dict[str, float]) -> Dict[str, float]:
    total = sum(shares.values())
    return {person: round(amount, 2) for person, amount in shares.items() if amount >= 0}


def project_subscription_cost(subscriptions: List[Tuple[str, float, str]]) -> Dict[str, float]:
    monthly = 0.0
    yearly = 0.0
    for _, amount, cadence in subscriptions:
        cadence = cadence.lower()
        if cadence.startswith("month"):
            monthly += amount
            yearly += amount * 12
        elif cadence.startswith("year"):
            yearly += amount
            monthly += amount / 12
    return {"monthly": round(monthly, 2), "yearly": round(yearly, 2)}

