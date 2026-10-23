from collections import defaultdict
from decimal import Decimal
from src.catalogue.service import PRODUCTS
from src.customers.service import CUSTOMERS
from src.orders.schemas import DraftValues


def validate(values: DraftValues) -> dict:
    issues = []
    lines = []
    stock = defaultdict(Decimal)
    total = Decimal("0.00")
    products = {product.sku: product for product in PRODUCTS}

    def issue(code, field, message, severity="blocker"):
        issues.append({"code": code, "field": field, "message": message, "severity": severity})

    if values.customer_id not in {customer.id for customer in CUSTOMERS}:
        issue("customer", "customer_id", "Select a catalogue customer.")
    if not values.delivery_address.strip():
        issue("address", "delivery_address", "Supply a delivery address.")
    elif not values.delivery_confirmed:
        issue("address_review", "delivery_address", "Compare the address with the email and explicitly confirm it.")
    if not values.lines:
        issue("lines", "lines", "Add at least one product line.")
    for index, line in enumerate(values.lines):
        field = f"lines.{index}"
        product = products.get(line.sku)
        candidates = [p.sku for p in PRODUCTS if line.requested_product.casefold() in
                      {p.sku.casefold(), p.name.casefold(), *(alias.casefold() for alias in p.aliases)}] if line.requested_product else []
        item = {"sku": line.sku, "name": product.name if product else None,
                "candidates": candidates, "pack_size": product.pack_size if product else None,
                "unit_price": str(product.price) if product else None, "cases": None, "line_total": None}
        lines.append(item)
        if product is None:
            issue("product", field + ".sku", "Choose a catalogue product; ambiguous names require staff selection.")
        elif not line.match_confirmed:
            issue("product_review", field + ".sku", "Explicitly review and select the suggested product.")
        quantity = line.quantity
        if quantity is None or quantity <= 0:
            issue("quantity", field + ".quantity", "Enter a positive quantity.")
            continue
        if line.quantity_unit == "unknown":
            issue("unit", field + ".quantity_unit", "Choose cases or individual units.")
            continue
        if product is None:
            continue
        cases = quantity if line.quantity_unit == "case" else quantity / product.pack_size
        if cases != cases.to_integral_value():
            issue("pack_size", field + ".quantity", f"Use whole cases of {product.pack_size} units; partial cases are outside this demo.")
            continue
        stock[product.sku] += cases
        amount = (cases * product.price).quantize(Decimal("0.01"))
        total += amount
        item.update(cases=int(cases), line_total=str(amount))
    for sku, quantity in stock.items():
        if quantity > products[sku].stock_cases:
            issue("stock", "lines", f"{sku}: requested {quantity} cases across all lines; simulated stock is {products[sku].stock_cases}.")
    if values.requested_delivery_date:
        issue("delivery_date", "requested_delivery_date", "Requested delivery dates are preferences, not guaranteed delivery dates.", "warning")
    return {"issues": issues, "lines": lines, "total": str(total.quantize(Decimal("0.01"))),
            "currency": "EUR", "can_confirm": not any(i["severity"] == "blocker" for i in issues)}
