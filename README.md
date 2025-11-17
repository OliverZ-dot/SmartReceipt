# SmartReceipt – Universal Receipt & Expense Manager

SmartReceipt is an offline-first desktop companion that helps you scan receipts, categorize spending, stay on budget, prep for taxes, and guard warranties without sending personal data to the cloud. The project distills the product brief in `SmartReceipt - Universal Receipt & Expense Manager.md` into a working Python/PyQt application you can extend and ship.

## Highlights
- 📸 **Smart Scanner** – Import or snap receipt images, extract store/date/total with OCR, and auto-categorize with a lightweight rules engine.
- 📊 **Visual Dashboard** – View month-to-date totals, category breakdowns, and spend velocity at a glance.
- 🎯 **Budget Copilot** – Define global and per-category limits and monitor progress in real time.
- 📑 **Tax Export Wizard** – Generate audit-ready PDF summaries with embedded receipt references.
- 📦 **Warranty Vault** – Track purchases, serial numbers, and expiration reminders.
- 🤝 **Bill Splitter & Links** – Calculate fair shares and auto-create Venmo/PayPal/Zelle links.
- 🔁 **Subscription Tracker** – Monitor recurring costs, renewal dates, and opportunities to cancel.

## Project Structure
```
smartreceipt/
├── app.py                 # Desktop entry point
├── pyproject.toml         # Project metadata & deps
├── README.md              # This file
├── smartreceipt/
│   ├── __init__.py
│   ├── core/              # OCR, categorizer, database, calculators
│   ├── gui/               # PyQt6 widgets
│   ├── models/            # Dataclasses shared by app layers
│   └── utils/             # PDF/report builders, payment links
└── tests/                 # Pytest-based smoke tests
```

## Requirements
- Python 3.10+
- Tesseract OCR binary installed locally (optional but recommended for full scanning flow)
- OS-specific Qt runtime libraries (PyQt6 handles installation via pip)

Install dependencies:
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
pip install -e ".[dev]"
```

## Running the App
```bash
python -m smartreceipt.app
```
The first launch creates an encrypted SQLite database inside your OS user directory. Demo data seeds automatically so you can explore the UI without scanning receipts.

## Key Modules
- `smartreceipt/core/ocr_engine.py` – Wraps Tesseract/Pillow with graceful degradation when OCR binaries are missing.
- `smartreceipt/core/categorizer.py` – Deterministic heuristics plus user overrides stored in SQLite.
- `smartreceipt/core/calculator.py` – Budget math, bill splitting, and subscription projections.
- `smartreceipt/gui/charts.py` – Matplotlib-backed dashboard canvas plugged into the main window.
- `smartreceipt/utils/pdf_generator.py` – ReportLab-powered export service with fallback plaintext export.

## Tests
```bash
pytest
```
Unit tests cover categorization logic, payment link generation, and calculator utilities. Add regression tests as you expand modules.

## Packaging for Release
Use PyInstaller to create signed installers:
```bash
pyinstaller --name SmartReceipt --windowed --noconfirm smartreceipt/app.py
```
Then follow the launch checklist from the brief for notarization, code signing, and store submissions.

## License
Released under the MIT License. See `LICENSE`.

