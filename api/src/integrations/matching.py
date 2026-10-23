"""Deterministic catalogue suggestions. Every suggestion still requires review."""
from src.catalogue.service import PRODUCTS
from src.customers.service import CUSTOMERS
from src.customers.schemas import Customer
from src.integrations.schemas import Extraction
from src.orders.schemas import DraftValues, LineValues


def normalized(value: str) -> str:
    return value.strip().casefold()


def normalize(extraction: Extraction, customers: tuple[Customer, ...] = CUSTOMERS) -> DraftValues:
    identities = []
    for field, value in (("name", extraction.customer_name), ("email", extraction.customer_email)):
        if value.strip():
            identities.append({c.id for c in customers if normalized(getattr(c, field)) == normalized(value)})
    customer_ids = set.intersection(*identities) if identities else set()
    lines = []
    for fact in extraction.lines:
        candidates = {p.sku for p in PRODUCTS if normalized(fact.description) in
                      {normalized(p.sku), normalized(p.name), *(normalized(alias) for alias in p.aliases)}}
        explicit = next((p.sku for p in PRODUCTS if normalized(p.sku) == normalized(fact.explicit_sku or "")), None)
        if fact.explicit_sku:
            sku = explicit if explicit and (not candidates or explicit in candidates) else None
        else:
            sku = next(iter(candidates)) if len(candidates) == 1 else None
        lines.append(LineValues(requested_product=fact.description or fact.explicit_sku or "", sku=sku,
                                quantity=fact.quantity, quantity_unit=fact.unit))
    return DraftValues(customer_id=next(iter(customer_ids)) if len(customer_ids) == 1 else None,
                       delivery_address=extraction.delivery_address,
                       delivery_instructions=extraction.delivery_instructions,
                       requested_delivery_date=extraction.requested_delivery_date, lines=lines)
