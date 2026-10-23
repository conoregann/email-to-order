import pytest
from src.integrations.matching import normalize
from src.integrations.schemas import Extraction
from src.orders.validation import validate


def extracted(description="oat milk", sku=None, quantity="2", unit="case", **patch):
    return Extraction.model_validate(dict(customer_name="Harbour Cafe", customer_email="orders@harbour.example",
        delivery_address="", delivery_instructions="Leave at side door", requested_date_text="",
        requested_delivery_date=None, lines=[dict(description=description, explicit_sku=sku, quantity=quantity, unit=unit)]) | patch)


@pytest.mark.parametrize("description,sku,expected", [
    ("", " oat-1l-06 ", "OAT-1L-06"), ("  BARISTA OAT  ", None, "OAT-1L-06"),
    ("House coffee beans 1kg", None, "COF-1KG-06"), ("oat milk", None, None),
    ("unlisted juice", None, None), ("coffee", "OAT-1L-06", None),
    ("coffee", "UNKNOWN", None), ("oat milk", "OAT-1L-06", "OAT-1L-06"),
])
def test_product_evidence(description, sku, expected):
    values = normalize(extracted(description, sku))
    assert values.lines[0].sku == expected
    assert not values.lines[0].match_confirmed
    assert not values.delivery_confirmed
    assert not validate(values)["can_confirm"]


@pytest.mark.parametrize("name,email,expected", [
    (" harbour cafe ", "", "harbour-cafe"), ("", "ORDERS@HARBOUR.EXAMPLE", "harbour-cafe"),
    ("Harbour Cafe", "orders@meadow.example", None), ("Unknown", "orders@harbour.example", None),
    ("", "", None), ("Unknown", "", None),
])
def test_customer_evidence(name, email, expected):
    assert normalize(extracted(customer_name=name, customer_email=email)).customer_id == expected


def test_address_units_and_quantities_are_never_guessed():
    values = normalize(extracted("cups", quantity="75", unit="unit"))
    assert values.delivery_address == ""
    assert values.delivery_instructions == "Leave at side door"
    assert values.lines[0].quantity == 75
    assert "pack_size" in {i["code"] for i in validate(values)["issues"]}
    assert normalize(extracted(unit="unknown")).lines[0].quantity_unit == "unknown"
    assert normalize(extracted(quantity="1.5")).lines[0].quantity.as_tuple().exponent == -1
    assert normalize(extracted(delivery_address="Use A, or possibly B")).delivery_address == "Use A, or possibly B"


def test_duplicate_stock_and_ambiguous_candidates():
    facts = extracted("cups", quantity="5")
    facts.lines *= 2
    assert "stock" in {i["code"] for i in validate(normalize(facts))["issues"]}
    assert validate(normalize(extracted()))["lines"][0]["candidates"] == ["OAT-1L-06", "OAT-1L-12"]
