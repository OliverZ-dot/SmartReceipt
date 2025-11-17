"""Payment link helpers for bill splitting."""

from __future__ import annotations

from urllib.parse import quote_plus


def venmo_link(handle: str, amount: float, note: str = "SmartReceipt split") -> str:
    return f"https://venmo.com/{handle}?txn=pay&amount={amount:.2f}&note={quote_plus(note)}"


def paypal_link(handle: str, amount: float) -> str:
    return f"https://paypal.me/{handle}/{amount:.2f}"


def zelle_instructions(name: str, amount: float) -> str:
    return f"Send ${amount:.2f} to {name} via Zelle"

