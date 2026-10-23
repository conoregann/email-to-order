import time
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.orders.models import Draft, DraftLine, ConfirmedOrder
from src.orders.schemas import CreateDraft, DraftValues, UpdateDraft
from src.orders.service import SAMPLES
from src.orders.validation import validate

# Saved manual values, not AI extraction. Addresses always require staff confirmation.
SAMPLE_VALUES = {
    "straightforward": {"customer_id": "harbour-cafe", "delivery_address": "12 Quay Street, Demo Town, Ireland", "lines": [{"requested_product": "OAT-1L-06", "sku": "OAT-1L-06", "match_confirmed": True, "quantity": "2", "quantity_unit": "case"}]},
    "ambiguous": {"customer_id": "harbour-cafe", "delivery_address": "12 Quay Street, Demo Town, Ireland", "lines": [{"requested_product": "oat milk", "quantity": "3", "quantity_unit": "case"}]},
    "missing-address": {"customer_id": "harbour-cafe", "lines": [{"requested_product": "COF-1KG-06", "sku": "COF-1KG-06", "match_confirmed": True, "quantity": "1", "quantity_unit": "case"}]},
    "quantity": {"customer_id": "meadow-deli", "delivery_address": "8 Meadow Road, Demo Town, Ireland", "lines": [{"requested_product": "CUP-12OZ-50", "sku": "CUP-12OZ-50", "match_confirmed": True, "quantity": "75", "quantity_unit": "unit"}]},
    "stock": {"customer_id": "meadow-deli", "delivery_address": "8 Meadow Road, Demo Town, Ireland", "lines": [{"requested_product": "CUP-12OZ-50", "sku": "CUP-12OZ-50", "match_confirmed": True, "quantity": "20", "quantity_unit": "case"}]},
}


def owned_draft(db: Session, guest_id: str, draft_id: str) -> Draft:
    draft = db.scalar(select(Draft).where(Draft.id == draft_id, Draft.guest_id == guest_id))
    if draft is None:
        raise HTTPException(404, "Order not found")
    return draft


def draft_values(draft: Draft) -> DraftValues:
    return DraftValues(**draft.values, lines=[line.values for line in draft.lines])


def draft_response(db: Session, draft: Draft) -> dict:
    from src.integrations.gemini import MESSAGES
    from src.orders.extraction import expire_attempt
    expire_attempt(db, draft)
    values = draft_values(draft)
    order = db.scalar(select(ConfirmedOrder).where(ConfirmedOrder.draft_id == draft.id))
    return {"id": draft.id, "status": draft.status, "version": draft.version,
            "original_email": draft.original_email, "initial_values": draft.initial_values,
            "source": draft.source, "extraction": draft.extraction,
            "extraction_status": draft.extraction_status, "extraction_attempt_id": draft.extraction_attempt_id,
            "extraction_error": draft.extraction_error, "extraction_message": MESSAGES.get(draft.extraction_error), "values": values.model_dump(mode="json"),
            "validation": order.snapshot["validation"] if order else validate(values), "created_at": draft.created_at, "updated_at": draft.updated_at,
            "confirmed": order.snapshot if order else None}


def create_draft(db: Session, guest_id: str, payload: CreateDraft) -> Draft:
    values = DraftValues()
    source = "manual"
    if payload.sample_id:
        sample = next((sample for sample in SAMPLES if sample.id == payload.sample_id), None)
        if sample is None:
            raise HTTPException(422, "Unknown sample email")
        if payload.email != sample.body:
            raise HTTPException(422, "Edited sample email must start as a blank manual draft.")
        values = DraftValues(**SAMPLE_VALUES[sample.id])
        source = "saved_example"
    now = int(time.time())
    data = values.model_dump(mode="json")
    draft = Draft(id=str(uuid4()), guest_id=guest_id, original_email=payload.email,
                  initial_values=data, source=source, values=values.model_dump(mode="json", exclude={"lines"}),
                  version=1, status="draft", created_at=now, updated_at=now)
    draft.lines = [DraftLine(id=str(uuid4()), position=i, values=line.model_dump(mode="json"))
                   for i, line in enumerate(values.lines)]
    db.add(draft)
    db.commit()
    return draft


def save_draft(db: Session, draft: Draft, payload: UpdateDraft) -> Draft:
    if draft.status != "draft":
        raise HTTPException(409, "Confirmed orders are read-only.")
    values = DraftValues(**payload.model_dump(exclude={"version"}))
    changed = db.execute(update(Draft).where(Draft.id == draft.id, Draft.version == payload.version,
                         Draft.status == "draft").values(values=values.model_dump(mode="json", exclude={"lines"}),
                         version=payload.version + 1, updated_at=int(time.time())),
                         execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Draft changed in another tab. Reload before saving.")
    # Flush deletes before inserts to preserve the unique line-position constraint.
    draft.lines.clear()
    db.flush()
    draft.lines = [DraftLine(id=str(uuid4()), position=i, values=line.model_dump(mode="json"))
                   for i, line in enumerate(values.lines)]
    db.commit()
    db.refresh(draft)
    return draft


def apply_saved_example(db: Session, draft: Draft, version: int) -> Draft:
    sample = next((sample for sample in SAMPLES if sample.body == draft.original_email), None)
    if sample is None or draft.source != "manual" or version != 1:
        raise HTTPException(409, "Saved examples require an unchanged matching sample draft.")
    values = DraftValues(**SAMPLE_VALUES[sample.id])
    changed = db.execute(update(Draft).where(Draft.id == draft.id, Draft.version == version,
        Draft.status == "draft", Draft.source == "manual",
        Draft.extraction_status.in_(["not_started", "failed"])).values(
            source="saved_example", initial_values=values.model_dump(mode="json"),
            values=values.model_dump(mode="json", exclude={"lines"}), version=version + 1,
            updated_at=int(time.time())), execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Draft changed. Reload before using a saved example.")
    draft.lines = [DraftLine(id=str(uuid4()), position=i, values=line.model_dump(mode="json"))
                   for i, line in enumerate(values.lines)]
    db.commit()
    db.refresh(draft)
    return draft
