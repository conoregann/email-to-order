import pytest
from pydantic import ValidationError
from src.integrations.schemas import Extraction


def facts(**patch):
    return dict(customer_name="", customer_email="", delivery_address="", delivery_instructions="",
                requested_date_text="", requested_delivery_date=None, lines=[], **patch)


def test_empty_unknowns_are_valid():
    assert Extraction(**facts()).lines == []


@pytest.mark.parametrize("patch", [
    {"price": "1"}, {"match_confirmed": True}, {"stock": 100},
    {"requested_delivery_date": "2026-02-30"},
    {"requested_delivery_date": "2026-10-24", "requested_date_text": "tomorrow"},
])
def test_invalid_facts(patch):
    with pytest.raises(ValidationError):
        Extraction(**(facts() | patch))


def test_missing_fields_and_bounds():
    with pytest.raises(ValidationError):
        Extraction.model_validate({})
    line = dict(description="cups", explicit_sku=None, quantity="1", unit="unknown")
    for patch in ({"lines": [line] * 51}, {"delivery_address": "x" * 1501},
                  *({"lines": [line | {"quantity": q}]} for q in ("NaN", "Infinity", "1.0001", "10000000000")),
                  {"lines": [line | {"approved": True}]}):
        with pytest.raises(ValidationError):
            Extraction(**(facts() | patch))
