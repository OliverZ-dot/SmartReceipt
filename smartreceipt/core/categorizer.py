"""Keyword-based categorizer with feedback loop."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict

CATEGORY_HINTS = {
    "walmart": "Groceries",
    "target": "Groceries",
    "whole foods": "Groceries",
    "shell": "Transport",
    "chevron": "Transport",
    "uber": "Transport",
    "lyft": "Transport",
    "amazon": "Shopping",
    "best buy": "Electronics",
    "apple": "Electronics",
    "olive garden": "Dining",
    "starbucks": "Dining",
}


class Categorizer:
    def __init__(self) -> None:
        self.user_overrides: Dict[str, str] = {}

    def categorize(self, store: str) -> str:
        key = store.lower().strip()
        if key in self.user_overrides:
            return self.user_overrides[key]
        for hint, category in CATEGORY_HINTS.items():
            if hint in key:
                return category
        return "Other"

    def learn(self, store: str, category: str) -> None:
        self.user_overrides[store.lower().strip()] = category

    def export_mapping(self) -> Dict[str, str]:
        data = defaultdict(str)
        data.update(CATEGORY_HINTS)
        data.update(self.user_overrides)
        return dict(data)

