from collections import defaultdict
from decimal import Decimal, ROUND_CEILING
from src.catalogue.service import PRODUCTS
from src.catalogue.schemas import Product
from src.customers.service import CUSTOMERS
from src.customers.schemas import Customer
from src.orders.schemas import DraftValues, LineValues


def quantity_options(line: LineValues, catalogue: tuple[Product, ...] | None = None) -> dict | None:
    product = next((product for product in (PRODUCTS if catalogue is None else catalogue) if product.sku == line.sku), None)
    if product is None or line.quantity is None or line.quantity <= 0 or line.quantity_unit == "unknown":
        return None
    units = line.quantity * product.pack_size if line.quantity_unit == "case" else line.quantity
    cases = units / product.pack_size
    if cases == cases.to_integral_value():
        return None
    whole_cases = int(cases.to_integral_value(rounding=ROUND_CEILING))
    supplied_units = whole_cases * product.pack_size
    return {"requested_units": str(units), "pack_size": product.pack_size, "cases": whole_cases,
            "supplied_units": supplied_units, "extra_units": str(supplied_units - units)}


def validate(values: DraftValues, customers: tuple[Customer, ...] = CUSTOMERS, catalogue: tuple[Product, ...] | None = None) -> dict:
    issues = []
    lines = []
    stock = defaultdict(Decimal)
    total = Decimal("0.00")
    catalogue = PRODUCTS if catalogue is None else catalogue
    products = {product.sku: product for product in catalogue}

    def issue(code, field, message, severity="blocker"):
        issues.append({"code": code, "field": field, "message": message, "severity": severity})

    if values.customer_id not in {customer.id for customer in customers}:
        issue("customer", "customer_id", "Select an existing customer or add a new customer.")
    if not values.delivery_address.strip():
        issue("address", "delivery_address", "Supply a delivery address.")
    elif not values.delivery_confirmed:
        issue("address_review", "delivery_address", "Compare the address with the email and explicitly confirm it.")
    if not values.lines:
        issue("lines", "lines", "Add at least one product line.")
    for index, line in enumerate(values.lines):
        field = f"lines.{index}"
        product = products.get(line.sku)
        resolution = line.quantity_resolution
        if resolution and resolution.status != "adjusted":
            issue("quantity_clarification", field + ".quantity", "Quantity needs customer clarification." if resolution.status == "needs_clarification" else "Review and approve the quantity change.")
        elif resolution and (resolution.approved_quantity != line.quantity or resolution.approved_unit != line.quantity_unit or resolution.approved_sku != line.sku):
            issue("quantity_resolution_stale", field + ".quantity", "Product or quantity changed. Review the quantity decision again.")
        elif resolution and not resolution.reason:
            issue("quantity_reason", field + ".quantity", "Record a reason for the approved quantity change.")
        candidates = [p.sku for p in catalogue if line.requested_product.casefold() in
                      {p.sku.casefold(), p.name.casefold(), *(alias.casefold() for alias in p.aliases)}] if line.requested_product else []
        item = {"sku": line.sku, "name": product.name if product else None,
                "candidates": candidates, "pack_size": product.pack_size if product else None,
                "unit_price": str(product.price) if product else None, "cases": None, "line_total": None,
                "quantity_suggestion": quantity_options(line, catalogue)}
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
            issue("pack_size", field + ".quantity", f"Sold in whole cases of {product.pack_size} units. Approve a whole-case quantity or mark this line for customer clarification.")
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
