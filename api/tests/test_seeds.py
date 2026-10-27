from collections import Counter
from fastapi.testclient import TestClient
from src.catalogue.service import PRODUCTS
from src.customers.service import CUSTOMERS
from src.orders.service import SAMPLES


def test_seed_relationships_and_scenarios():
    assert len({p.sku for p in PRODUCTS}) == len(PRODUCTS)
    address_ids = [a.id for c in CUSTOMERS for a in c.addresses]
    assert len(set(address_ids)) == len(address_ids)
    assert len({c.id for c in CUSTOMERS}) == len(CUSTOMERS)
    assert all(c.addresses for c in CUSTOMERS)
    aliases = Counter(a for p in PRODUCTS for a in p.aliases)
    assert aliases["oat milk"] == 2
    assert {s.id for s in SAMPLES} == {"straightforward", "ambiguous", "missing-address", "quantity", "stock"}
    assert all(c.email.endswith(".example") for c in CUSTOMERS)


def test_seed_api_serialization_and_static_route_priority(app):
    with TestClient(app) as client:
        samples = client.get("/api/orders/samples")
        assert samples.status_code == 200
        assert len(samples.json()) == 5
        products = client.get("/api/catalogue/products").json()
        assert products[0]["price"] == "13.80"
        assert all(p["currency"] == "EUR" for p in products)
        assert client.get("/api/customers").json()[0]["addresses"]
