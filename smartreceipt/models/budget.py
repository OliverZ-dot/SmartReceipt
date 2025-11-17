"""Budget data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(slots=True)
class Budget:
    month: str  # YYYY-MM
    total_limit: float
    category_limits: Dict[str, float] = field(default_factory=dict)

