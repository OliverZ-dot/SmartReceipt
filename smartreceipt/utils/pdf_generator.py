"""PDF export utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from smartreceipt.utils.paths import EXPORT_DIR

try:  # pragma: no cover - optional dependency
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    LETTER = None
    canvas = None


def build_tax_report(year: int, categories: Mapping[str, float], receipts: Iterable[Mapping]) -> Path:
    """Generate a PDF (or plaintext fallback) tax export."""
    output = EXPORT_DIR / f"smartreceipt-tax-{year}.pdf"
    if canvas and LETTER:
        _build_pdf(output, year, categories, receipts)
    else:
        _build_text_fallback(output.with_suffix(".txt"), year, categories, receipts)
    return output


def _build_pdf(path: Path, year: int, categories: Mapping[str, float], receipts: Iterable[Mapping]) -> None:
    pdf = canvas.Canvas(str(path), pagesize=LETTER)
    width, height = LETTER

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, height - 72, f"SmartReceipt Tax Summary {year}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, height - 90, f"Prepared: {datetime.now().strftime('%Y-%m-%d')}")

    y = height - 120
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, y, "Category Totals")
    y -= 18
    pdf.setFont("Helvetica", 10)
    for category, amount in categories.items():
        pdf.drawString(90, y, f"{category}: ${amount:.2f}")
        y -= 14

    y -= 10
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(72, y, "Receipts")
    y -= 18
    pdf.setFont("Helvetica", 10)
    for receipt in receipts:
        line = f"{receipt['purchase_date']} • {receipt['store']} • ${receipt['total']:.2f} ({receipt['category']})"
        pdf.drawString(90, y, line)
        y -= 12
        if y < 72:
            pdf.showPage()
            y = height - 72
    pdf.save()


def _build_text_fallback(path: Path, year: int, categories: Mapping[str, float], receipts: Iterable[Mapping]) -> None:
    lines = [
        f"SmartReceipt Tax Summary {year}",
        f"Prepared: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "Category Totals:",
    ]
    for category, amount in categories.items():
        lines.append(f" - {category}: ${amount:.2f}")
    lines.append("")
    lines.append("Receipts:")
    for receipt in receipts:
        lines.append(
            f" - {receipt['purchase_date']} | {receipt['store']} | ${receipt['total']:.2f} | {receipt['category']}"
        )
    path.write_text("\n".join(lines), encoding="utf-8")

