from src.customers.schemas import Address, Customer
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.customers.models import WorkspaceCustomer

CUSTOMERS = (
    Customer(id="harbour-cafe", name="Harbour Cafe", email="orders@harbour.example", addresses=(
        Address(id="harbour-main", label="Main cafe", lines=("12 Quay Street", "Demo Town", "Ireland")),
        Address(id="harbour-store", label="Store room", lines=("4 Market Lane", "Demo Town", "Ireland")),
    )),
    Customer(id="meadow-deli", name="Meadow Deli", email="orders@meadow.example", addresses=(
        Address(id="meadow-main", label="Deli", lines=("8 Meadow Road", "Demo Town", "Ireland")),
    )),
)

def list_customers() -> tuple[Customer, ...]:
    return CUSTOMERS


def workspace_customers(db: Session, guest_id: str) -> tuple[Customer, ...]:
    records = db.scalars(select(WorkspaceCustomer).where(WorkspaceCustomer.guest_id == guest_id)
                         .order_by(WorkspaceCustomer.name, WorkspaceCustomer.id)).all()
    return CUSTOMERS + tuple(Customer(id=c.id, name=c.name, email=c.email, addresses=()) for c in records)
