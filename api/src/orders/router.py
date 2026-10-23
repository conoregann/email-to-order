from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.auth.models import GuestSession
from src.auth.service import current_guest, require_browser_header
from src.database import get_db
from src.orders.drafts import create_draft, draft_response, owned_draft, save_draft
from src.orders.models import Draft
from src.orders.schemas import CreateDraft, SampleEmail, UpdateDraft
from src.orders.service import list_samples

router = APIRouter(prefix="/orders", tags=["orders"])
router.add_api_route("/samples", list_samples, response_model=list[SampleEmail], methods=["GET"])

@router.get("")
def list_orders(response: Response, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    drafts = db.scalars(select(Draft).where(Draft.guest_id == guest.id).order_by(Draft.created_at.desc(), Draft.id)).all()
    return [draft_response(db, draft) for draft in drafts]

@router.post("", status_code=201, dependencies=[Depends(require_browser_header)])
def new_order(payload: CreateDraft, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    return draft_response(db, create_draft(db, guest.id, payload))

@router.get("/{draft_id}")
def get_order(draft_id: str, response: Response, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return draft_response(db, owned_draft(db, guest.id, draft_id))

@router.put("/{draft_id}", dependencies=[Depends(require_browser_header)])
def update_order(draft_id: str, payload: UpdateDraft, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    draft = owned_draft(db, guest.id, draft_id)
    return draft_response(db, save_draft(db, draft, payload))
