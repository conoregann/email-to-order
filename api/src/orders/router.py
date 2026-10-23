from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.auth.models import GuestSession
from src.auth.service import current_guest, require_browser_header
from src.database import get_db
from src.orders.drafts import create_draft, draft_response, owned_draft, save_draft, apply_saved_example
from src.orders.models import Draft, ExtractionAttempt
from src.orders.schemas import CreateDraft, SampleEmail, UpdateDraft, ConfirmDraft
from src.orders.confirmation import confirm_draft
from src.orders.service import list_samples
from src.integrations.gemini import available
from src.orders.extraction import ExtractDraft, extract_draft

router = APIRouter(prefix="/orders", tags=["orders"])
router.add_api_route("/samples", list_samples, response_model=list[SampleEmail], methods=["GET"])

@router.get("/extraction-config")
def extraction_config():
    return {"enabled": available()}

@router.post("/{draft_id}/extract", dependencies=[Depends(require_browser_header)])
async def extract_order(draft_id: str, payload: ExtractDraft, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    draft = await extract_draft(db, guest.id, draft_id, payload)
    result = draft_response(db, draft)
    attempt = db.get(ExtractionAttempt, str(payload.attempt_id))
    result["requested_attempt"] = {"id": attempt.id, "status": attempt.status, "error": attempt.error}
    return result

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

@router.post("/{draft_id}/confirm", dependencies=[Depends(require_browser_header)])
def confirm_order(draft_id: str, payload: ConfirmDraft, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    draft = owned_draft(db, guest.id, draft_id)
    confirm_draft(db, draft, payload.version)
    return draft_response(db, draft)


@router.post("/{draft_id}/saved-example", dependencies=[Depends(require_browser_header)])
def saved_example(draft_id: str, payload: ConfirmDraft, guest: GuestSession = Depends(current_guest), db: Session = Depends(get_db)):
    return draft_response(db, apply_saved_example(db, owned_draft(db, guest.id, draft_id), payload.version))
