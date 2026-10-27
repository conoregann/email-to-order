from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from src.orders.schemas import DraftValues, LineValues
from src.orders.validation import quantity_options, validate
from test_drafts import HEADERS, create_sample, save
from test_confirmation import confirm


def resolution(status="adjusted", **patch):
    return {"requested_quantity": "75", "requested_unit": "unit", "status": status,
            "reason": "Customer agreed to two whole cases.", "approved_quantity": "2",
            "approved_unit": "case", "approved_sku": "CUP-12OZ-50", **patch}


@pytest.mark.parametrize("quantity,unit,cases,extra", [
    ("75", "unit", 2, "25"), ("1.5", "case", 2, "25.0"),
    ("399.5", "unit", 8, "0.5"), ("401", "unit", 9, "49"),
])
def test_server_calculates_next_whole_case(quantity, unit, cases, extra):
    suggestion = quantity_options(LineValues(sku="CUP-12OZ-50", quantity=quantity, quantity_unit=unit))
    assert suggestion["cases"] == cases
    assert suggestion["supplied_units"] == cases * 50
    assert Decimal(suggestion["extra_units"]) == Decimal(extra)


@pytest.mark.parametrize("quantity,unit,sku", [
    ("100", "unit", "CUP-12OZ-50"), ("2", "case", "CUP-12OZ-50"),
    ("75", "unknown", "CUP-12OZ-50"), ("0", "unit", "CUP-12OZ-50"),
    (None, "unit", "CUP-12OZ-50"), ("75", "unit", "missing"),
])
def test_no_rounding_suggestion_for_exact_or_unresolved_inputs(quantity, unit, sku):
    assert quantity_options(LineValues(sku=sku, quantity=quantity, quantity_unit=unit)) is None


def test_pending_resolution_blocks_otherwise_valid_quantity():
    values = DraftValues(customer_id="meadow-deli", delivery_address="8 Meadow Road", delivery_confirmed=True,
                         lines=[LineValues(sku="CUP-12OZ-50", quantity="2", quantity_unit="case", match_confirmed=True,
                                           quantity_resolution=resolution("needs_clarification"))])
    assert "quantity_clarification" in {issue["code"] for issue in validate(values)["issues"]}
    values.lines[0].quantity_resolution.status = "adjusted"
    assert validate(values)["can_confirm"]
    values.lines[0].quantity_resolution.reason = ""
    assert not validate(values)["can_confirm"]


@pytest.mark.parametrize("patch", [{"quantity": "3"}, {"quantity_unit": "unit"}, {"sku": "OAT-1L-06"}])
def test_changed_product_or_quantity_invalidates_resolution(patch):
    line = LineValues(sku="CUP-12OZ-50", quantity="2", quantity_unit="case", match_confirmed=True,
                      quantity_resolution=resolution())
    for field, value in patch.items():
        setattr(line, field, Decimal(value) if field == "quantity" else value)
    result = validate(DraftValues(lines=[line]))
    assert "quantity_resolution_stale" in {issue["code"] for issue in result["issues"]}


def test_clarification_survives_save_reload_and_resolution_is_frozen(guest):
    draft = create_sample(guest, "quantity")
    line = {**draft["values"]["lines"][0], "quantity_resolution": resolution("needs_clarification", approved_quantity=None, approved_unit="unknown", approved_sku=None)}
    pending = save(guest, draft, lines=[line], delivery_confirmed=True).json()
    reloaded = guest.get(f"/api/orders/{draft['id']}").json()
    assert reloaded["values"] == pending["values"]
    assert guest.get("/api/orders").json()["items"][0]["values"]["lines"][0]["quantity_resolution"]["status"] == "needs_clarification"
    assert confirm(guest, reloaded).status_code == 422
    line.update(quantity="2", quantity_unit="case", match_confirmed=False, quantity_resolution=resolution())
    adjusted = save(guest, reloaded, lines=[line]).json()
    assert not adjusted["validation"]["can_confirm"]
    line["match_confirmed"] = True
    approved = save(guest, adjusted, lines=[line]).json()
    confirmed = confirm(guest, approved).json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["confirmed"]["values"]["lines"][0]["quantity_resolution"] == resolution()
    assert confirmed["confirmed"]["validation"]["total"] == "11.00"
    assert confirmed["initial_values"] == draft["initial_values"]
    assert confirmed["original_email"] == draft["original_email"]
    assert confirmed["initial_values"]["lines"][0]["quantity"] == "75"


def test_rounding_does_not_bypass_stock_limits(guest):
    draft = create_sample(guest, "quantity")
    line = {**draft["values"]["lines"][0], "quantity": "401"}
    response = guest.post(f"/api/orders/{draft['id']}/quantity-options", json=line, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["suggestion"]["cases"] == 9
    line.update(quantity="9", quantity_unit="case", quantity_resolution=resolution(approved_quantity="9"))
    updated = save(guest, draft, lines=[line], delivery_confirmed=True).json()
    assert "stock" in {issue["code"] for issue in updated["validation"]["issues"]}
    assert confirm(guest, updated).status_code == 422


def test_quantity_preview_is_owned_nonmutating_and_requires_header(guest, app):
    draft = create_sample(guest, "quantity")
    path = f"/api/orders/{draft['id']}/quantity-options"
    line = draft["values"]["lines"][0]
    assert guest.post(path, json=line).status_code == 403
    assert guest.post(path, json=line, headers=HEADERS).json()["suggestion"]["cases"] == 2
    assert guest.get(f"/api/orders/{draft['id']}").json() == draft
    with TestClient(app) as other:
        other.post("/api/auth/guest", headers=HEADERS)
        assert other.post(path, json=line, headers=HEADERS).status_code == 404
