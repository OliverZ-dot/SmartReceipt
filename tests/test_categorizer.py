from smartreceipt.core.categorizer import Categorizer


def test_categorizer_defaults():
    categorizer = Categorizer()
    assert categorizer.categorize("Walmart Supercenter") == "Groceries"
    assert categorizer.categorize("Random Shop") == "Other"


def test_categorizer_learns_override():
    categorizer = Categorizer()
    categorizer.learn("Random Shop", "Dining")
    assert categorizer.categorize("Random Shop") == "Dining"

