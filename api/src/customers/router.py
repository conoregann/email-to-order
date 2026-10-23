from uuid import uuid4
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from src.auth.models import GuestSession
from src.auth.service import current_guest, find_guest, require_browser_header
from src.database import get_db
from src.customers.models import WorkspaceCustomer
from src.customers.schemas import CreateCustomer, Customer
from src.customers.service import list_customers, workspace_customers

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("", response_model=list[Customer])
def customers(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    guest = find_guest(request, db)
    return workspace_customers(db, guest.id) if guest else list_customers()


@router.post("", response_model=Customer, status_code=201, dependencies=[Depends(require_browser_header)])
def create_customer(payload: CreateCustomer, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    record = WorkspaceCustomer(id=str(uuid4()), guest_id=guest.id, name=payload.name, email=payload.email)
    db.add(record)
    db.commit()
    return Customer(id=record.id, name=record.name, email=record.email, addresses=())
