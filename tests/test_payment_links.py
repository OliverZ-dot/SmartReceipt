from smartreceipt.utils.payment_links import paypal_link, venmo_link, zelle_instructions


def test_payment_links():
    venmo = venmo_link("alice", 12.5, note="Dinner")
    assert "venmo.com/alice" in venmo
    assert "12.50" in venmo

    paypal = paypal_link("bob", 20)
    assert paypal.endswith("/20.00")

    zelle = zelle_instructions("Charlie", 33.33)
    assert "Charlie" in zelle

