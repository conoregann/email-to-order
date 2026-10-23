from decimal import Decimal
import pytest
from src.orders.schemas import DraftValues
from src.orders.validation import validate
from src.orders.drafts import SAMPLE_VALUES


def valid_values():
    return DraftValues(**{**SAMPLE_VALUES["straightforward"], "delivery_confirmed": True})


def test_exact_prices_address_review_and_date_warning():
    values = valid_values()
    result = validate(values)
    assert result["can_confirm"]
    assert result["total"] == "27.60"
    values.delivery_confirmed = False
    assert not validate(values)["can_confirm"]
    values.delivery_confirmed = True
    values.requested_delivery_date = "2026-12-01"
    result = validate(values)
    assert result["can_confirm"]
    assert result["issues"][0]["severity"] == "warning"


@pytest.mark.parametrize("quantity,unit,code", [(None,"case","quantity"),("0","case","quantity"),("-1","case","quantity"),("1.5","case","pack_size"),("75","unit","pack_size"),("2","unknown","unit")])
def test_quantity_and_pack_rules(quantity, unit, code):
    values = valid_values()
    values.lines[0].quantity = Decimal(quantity) if quantity is not None else None
    values.lines[0].quantity_unit = unit
    result = validate(values)
    assert not result["can_confirm"]
    assert code in {issue["code"] for issue in result["issues"]}


def test_ambiguous_alias_and_invalid_customer():
    values = DraftValues(**SAMPLE_VALUES["ambiguous"])
    result = validate(values)
    assert result["lines"][0]["candidates"] == ["OAT-1L-06", "OAT-1L-12"]
    assert not result["can_confirm"]
    values.customer_id = "unknown"
    assert "customer" in {issue["code"] for issue in validate(values)["issues"]}


def test_stock_aggregates_duplicate_lines_and_units():
    values = valid_values()
    values.lines[0].quantity = Decimal("21")
    values.lines.append(values.lines[0].model_copy())
    assert "stock" in {issue["code"] for issue in validate(values)["issues"]}
    values.lines = [values.lines[0]]
    values.lines[0].quantity = Decimal("12")
    values.lines[0].quantity_unit = "unit"
    assert validate(values)["total"] == "27.60"
