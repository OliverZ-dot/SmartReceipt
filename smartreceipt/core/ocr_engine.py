"""OCR wrapper around Tesseract with graceful fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None
    Image = None


@dataclass(slots=True)
class OCRResult:
    store: str
    date: datetime
    total: float
    items_detected: int
    payment_method: Optional[str] = None


STORE_REGEX = re.compile(r"^[A-Z][A-Za-z0-9 &'\\-]{2,}$", re.MULTILINE)
TOTAL_REGEX = re.compile(r"(?:total|amount|sum)[^0-9]*([0-9]+\\.[0-9]{2})", re.IGNORECASE)
DATE_REGEX = re.compile(
    r"((?:19|20)\\d{2})[-/](\\d{1,2})[-/](\\d{1,2})|((\\d{1,2})[/.-](\\d{1,2})[/.-]((?:19|20)\\d{2}))"
)


def extract_details(image_path: Path) -> OCRResult:
    """Extract structured info from a scanned receipt image."""
    text = image_path.stem
    if pytesseract and Image:
        text = pytesseract.image_to_string(Image.open(image_path))

    store = _detect_store(text) or "Unknown Store"
    total = float(_detect_total(text) or 0.0)
    date_value = _detect_date(text) or datetime.now()
    items = text.lower().count("$")
    payment = _detect_payment(text)
    return OCRResult(
        store=store,
        date=date_value,
        total=total,
        items_detected=max(items, 1),
        payment_method=payment,
    )


def _detect_store(text: str) -> Optional[str]:
    match = STORE_REGEX.search(text)
    return match.group(0).strip() if match else None


def _detect_total(text: str) -> Optional[str]:
    match = TOTAL_REGEX.search(text)
    return match.group(1) if match else None


def _detect_date(text: str) -> Optional[datetime]:
    match = DATE_REGEX.search(text)
    if not match:
        return None
    groups = match.groups()
    if groups[0]:
        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
    else:
        month, day, year = int(groups[4]), int(groups[5]), int(groups[6])
    return datetime(year=year, month=month, day=day)


def _detect_payment(text: str) -> Optional[str]:
    lowered = text.lower()
    for keyword in ("visa", "mastercard", "amex", "cash", "paypal"):
        if keyword in lowered:
            return keyword.title()
    return None

