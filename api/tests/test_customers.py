from fastapi.testclient import TestClient
import pytest
from src.customers.service import workspace_customers
from src.integrations.matching import normalize
from src.integrations.schemas import Extraction
from test_drafts import HEADERS, create_sample, save
from test_confirmation import confirm
from test_gemini import FACTS


def create_customer(client, **fields):
    return client.post('/api/customers', json={'name': 'Example Supplies', 'email': 'orders@example.test', **fields}, headers=HEADERS)


def test_customer_persists_and_can_confirm_order(guest, app):
    response = create_customer(guest)
    assert response.status_code == 201
    customer = response.json()
    assert customer['addresses'] == []
    assert customer in guest.get('/api/customers').json()
    with TestClient(app) as reopened:
        reopened.cookies.update(guest.cookies)
        assert customer in reopened.get('/api/customers').json()
    draft = save(guest, create_sample(guest), customer_id=customer['id'], delivery_confirmed=True).json()
    assert draft['validation']['can_confirm']
    result = confirm(guest, draft)
    assert result.status_code == 200, result.text
    assert result.json()['confirmed']['customer'] == customer
    assert 'orders@example.test' in result.json()['confirmed']['confirmation_preview']
    assert guest.get(f"/api/orders/{draft['id']}").json()['confirmed'] == result.json()['confirmed']


def test_customer_is_private_and_requires_workspace_and_header(guest, app):
    customer = create_customer(guest).json()
    assert guest.post('/api/customers', json={'name': 'Example', 'email': 'a@example.test'}).status_code == 403
    with TestClient(app) as stranger:
        assert create_customer(stranger).status_code == 401
        assert customer not in stranger.get('/api/customers').json()
        stranger.post('/api/auth/guest', headers=HEADERS)
        assert customer not in stranger.get('/api/customers').json()
        draft = save(stranger, create_sample(stranger), customer_id=customer['id'], delivery_confirmed=True).json()
        assert not draft['validation']['can_confirm']
        assert confirm(stranger, draft).status_code == 422
    assert guest.get('/api/customers').headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('fields', [{'name': '   '}, {'name': 'x' * 201}, {'email': 'invalid'}, {'email': 'a@b.test\nInjected'}, {'email': 'x' * 321}])
def test_customer_validation(guest, fields):
    assert create_customer(guest, **fields).status_code == 422


def test_created_customer_is_matched_only_in_own_workspace(guest, app):
    customer = create_customer(guest, name='  Example Supplies  ').json()
    assert customer['name'] == 'Example Supplies'
    facts = Extraction(**{**FACTS, 'customer_name': customer['name'], 'customer_email': customer['email']})
    with app.state.sessions() as db:
        from src.auth.models import GuestSession
        from sqlalchemy import select
        owner = db.scalar(select(GuestSession))
        assert normalize(facts, workspace_customers(db, owner.id)).customer_id == customer['id']
        assert normalize(facts, workspace_customers(db, 'other-workspace')).customer_id is None
