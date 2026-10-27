from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.auth.models import GuestSession
from src.auth.service import current_guest, find_guest, require_browser_header
from src.database import get_db
from src.config import settings
from src.safeguards import check_capacity
from src.catalogue.models import WorkspaceProduct
from src.catalogue.schemas import CreateProduct, Product
from src.catalogue.service import list_products, workspace_products

router = APIRouter(prefix="/catalogue", tags=["catalogue"])

@router.get("/products", response_model=list[Product])
def products(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    guest = find_guest(request, db)
    return workspace_products(db, guest.id) if guest else list_products()


@router.post("/products", response_model=Product, status_code=201, dependencies=[Depends(require_browser_header)])
def create_product(payload: CreateProduct, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    check_capacity(db, WorkspaceProduct, settings.workspace_product_limit, "Product", guest.id)
    if any(p.sku == payload.sku for p in workspace_products(db, guest.id)):
        raise HTTPException(409, "This SKU already exists. Select the existing product or use a different SKU.")
    record = WorkspaceProduct(id=str(uuid4()), guest_id=guest.id, **payload.model_dump())
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This SKU already exists. Select the existing product or use a different SKU.") from None
    return Product(**payload.model_dump(), aliases=())
