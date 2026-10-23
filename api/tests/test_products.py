import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from src.auth.models import GuestSession
from src.catalogue.service import workspace_products
from src.integrations.matching import normalize
from src.integrations.schemas import Extraction
from test_confirmation import confirm
from test_drafts import HEADERS, create_sample, save
from test_gemini import FACTS


def create_product(client, **fields):
    return client.post('/api/catalogue/products', headers=HEADERS, json={
        'sku': 'TOWEL-BLUE-12', 'name': 'Blue paper towels', 'pack_size': 12,
        'price': '18.50', 'stock_cases': 10, **fields,
    })


def product_line(product, **fields):
    return {'requested_product': 'Blue paper towels', 'sku': product['sku'], 'quantity': '3',
            'quantity_unit': 'case', 'match_confirmed': True, **fields}


def test_product_persists_and_can_confirm_order(guest, app):
    response = create_product(guest, sku='towel-blue-12')
    assert response.status_code == 201, response.text
    product = response.json()
    assert product['sku'] == 'TOWEL-BLUE-12'
    assert product['price'] == '18.50'
    with TestClient(app) as reopened:
        reopened.cookies.update(guest.cookies)
        assert product in reopened.get('/api/catalogue/products').json()
    draft = save(guest, create_sample(guest), lines=[product_line(product)], delivery_confirmed=True).json()
    assert draft['validation']['can_confirm']
    assert draft['validation']['total'] == '55.50'
    result = confirm(guest, draft)
    assert result.status_code == 200, result.text
    snapshot = result.json()['confirmed']
    assert snapshot['validation']['lines'][0]['name'] == 'Blue paper towels'
    assert snapshot['validation']['lines'][0]['pack_size'] == 12
    assert snapshot['validation']['lines'][0]['unit_price'] == '18.50'
    assert guest.get(f"/api/orders/{draft['id']}").json()['confirmed'] == snapshot


def test_product_scope_and_creation_authorization(guest, app):
    product = create_product(guest).json()
    assert guest.post('/api/catalogue/products', json={}).status_code == 403
    with TestClient(app) as stranger:
        assert create_product(stranger).status_code == 401
        assert product not in stranger.get('/api/catalogue/products').json()
        stranger.post('/api/auth/guest', headers=HEADERS)
        assert product not in stranger.get('/api/catalogue/products').json()
        draft = save(stranger, create_sample(stranger), lines=[product_line(product)], delivery_confirmed=True).json()
        assert confirm(stranger, draft).status_code == 422
        # Each workspace can use the same SKU with its own trusted catalogue values.
        assert create_product(stranger, price='99.00').status_code == 201
        draft = save(stranger, draft, lines=[product_line(product)]).json()
        assert draft['validation']['total'] == '297.00'
    assert guest.get('/api/catalogue/products').headers['cache-control'] == 'no-store'


def test_duplicate_sku_does_not_replace_existing_product(guest):
    original = create_product(guest).json()
    assert create_product(guest, sku='towel-blue-12', price='1.00').status_code == 409
    assert create_product(guest, sku='oat-1l-06').status_code == 409
    assert [p for p in guest.get('/api/catalogue/products').json() if p['sku'] == original['sku']] == [original]


@pytest.mark.parametrize('fields', [
    {'sku': ' '}, {'sku': 'bad sku'}, {'sku': 'x' * 81}, {'name': ' '}, {'name': 'x' * 301},
    {'pack_size': 0}, {'pack_size': 1.5}, {'pack_size': True}, {'pack_size': 1000001},
    {'price': '0'}, {'price': '-1'}, {'price': '1.001'}, {'price': 'NaN'}, {'price': '10000000000'},
    {'stock_cases': -1}, {'stock_cases': 0.5}, {'stock_cases': True}, {'stock_cases': 1000001},
    {'currency': 'USD'},
])
def test_product_validation(guest, fields):
    assert create_product(guest, **fields).status_code == 422


def test_new_product_pack_size_stock_and_approval_are_enforced(guest):
    product = create_product(guest, stock_cases=3).json()
    draft = create_sample(guest)
    def checked(lines):
        nonlocal draft
        draft = save(guest, draft, lines=lines, delivery_confirmed=True).json()
        return {i['code'] for i in draft['validation']['issues']}
    assert 'product_review' in checked([product_line(product, match_confirmed=False)])
    assert 'pack_size' in checked([product_line(product, quantity='13', quantity_unit='unit')])
    assert 'stock' in checked([product_line(product, quantity='2'), product_line(product, quantity='2')])
    assert confirm(guest, draft).status_code == 422
    options = guest.post(f"/api/orders/{draft['id']}/quantity-options", headers=HEADERS,
                         json=product_line(product, quantity='13', quantity_unit='unit')).json()['suggestion']
    assert options['cases'] == 2
    assert options['supplied_units'] == 24
    assert not checked([product_line(product)])
    assert confirm(guest, draft).status_code == 200
    assert create_product(guest, sku='NO-STOCK', stock_cases=0).status_code == 201


def test_new_product_is_available_for_extraction_matching_only_in_own_workspace(guest, app):
    product = create_product(guest).json()
    facts = Extraction(**{**FACTS, 'lines': [{
        'description': product['name'], 'explicit_sku': product['sku'], 'quantity': '3', 'unit': 'case',
    }]})
    with app.state.sessions() as db:
        owner = db.scalar(select(GuestSession))
        assert normalize(facts, catalogue=workspace_products(db, owner.id)).lines[0].sku == product['sku']
        assert normalize(facts, catalogue=workspace_products(db, 'other-workspace')).lines[0].sku is None
