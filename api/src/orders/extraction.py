import time
from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.integrations import gemini
from src.customers.service import workspace_customers
from src.integrations.matching import normalize
from src.integrations.usage import lock_usage, reserve
from src.orders.drafts import owned_draft
from src.orders.models import Draft, DraftLine, ExtractionAttempt
from src.orders.schemas import InputModel
from pydantic import Field


class ExtractDraft(InputModel):
    version: int = Field(ge=1)
    attempt_id: UUID


def expire_attempt(db: Session, draft: Draft) -> None:
    if draft.extraction_status != "running":
        return
    now = int(time.time())
    attempt = db.get(ExtractionAttempt, draft.extraction_attempt_id)
    if attempt and attempt.status == "running" and attempt.expires_at <= now:
        db.execute(update(ExtractionAttempt).where(ExtractionAttempt.id == attempt.id,
                   ExtractionAttempt.status == "running").values(status="failed", error="timeout"))
        db.execute(update(Draft).where(Draft.id == draft.id, Draft.extraction_attempt_id == attempt.id,
                   Draft.extraction_status == "running").values(extraction_status="failed", extraction_error="timeout"))
        db.commit()
        db.refresh(draft)


async def extract_draft(db: Session, guest_id: str, draft_id: str, payload: ExtractDraft) -> Draft:
    draft = owned_draft(db, guest_id, draft_id)
    expire_attempt(db, draft)
    attempt_id = str(payload.attempt_id)
    try:
        lock_usage(db)
        db.refresh(draft)
        existing = db.get(ExtractionAttempt, attempt_id)
        if existing:
            if existing.draft_id != draft.id or existing.guest_id != guest_id:
                raise HTTPException(409, "Attempt identifier already used. Reload the draft.")
            db.commit()
            return draft
        if (draft.status != "draft" or draft.version != payload.version or draft.version != 1
                or draft.source != "manual" or draft.extraction_status not in ("not_started", "failed")):
            raise HTTPException(409, "Extraction requires an unchanged manual draft. Reload and review this draft.")
        if not gemini.available():
            raise gemini.ExtractionError("unavailable")
        now = int(time.time())
        reserve(db, guest_id, draft.id, attempt_id, now)
        # Serialize with a simultaneous staff save/confirmation, including on PostgreSQL.
        changed = db.execute(update(Draft).where(Draft.id == draft.id, Draft.version == payload.version,
            Draft.status == "draft").values(extraction_status="running", extraction_attempt_id=attempt_id,
            extraction_error=None), execution_options={"synchronize_session": False})
        if changed.rowcount != 1:
            raise HTTPException(409, "Draft changed before extraction. Reload and review.")
        email = draft.original_email
        db.commit()
    except gemini.ExtractionError as error:
        db.rollback()
        raise HTTPException(429 if error.code in ("guest_limit", "daily_limit") else 503,
                            {"code": error.code, "message": str(error)}) from None
    except Exception:
        db.rollback()
        raise

    # No database transaction or lock is held during the network call.
    facts = None
    error_code = None
    model = gemini.settings.gemini_model
    try:
        facts = await gemini.extract(email)
    except gemini.ExtractionError as error:
        error_code = error.code
    now = int(time.time())
    attempt = db.get(ExtractionAttempt, attempt_id)
    if attempt.status != "running" or attempt.expires_at <= now:
        error_code = "timeout"
    values = normalize(facts, workspace_customers(db, guest_id)) if facts is not None and error_code is None else None
    state = {"extraction_status": "failed", "extraction_error": error_code}
    if values is not None:
        data = values.model_dump(mode="json")
        state = dict(extraction_status="succeeded", extraction_error=None, source="ai_suggestion",
                     extraction={"facts": facts.model_dump(mode="json"), "model": model,
                                 "prompt_version": gemini.PROMPT_VERSION, "extracted_at": now, "attempt_id": attempt_id},
                     initial_values=data, values=values.model_dump(mode="json", exclude={"lines"}),
                     version=payload.version + 1, updated_at=now)
    changed = db.execute(update(Draft).where(Draft.id == draft.id, Draft.version == payload.version,
        Draft.status == "draft", Draft.extraction_attempt_id == attempt_id,
        Draft.extraction_status == "running").values(**state), execution_options={"synchronize_session": False})
    if changed.rowcount == 1 and values is not None:
        db.refresh(draft)
        draft.lines = [DraftLine(id=str(uuid4()), position=i, values=line.model_dump(mode="json"))
                       for i, line in enumerate(values.lines)]
    if changed.rowcount != 1:
        error_code = "discarded"
        db.execute(update(Draft).where(Draft.id == draft.id, Draft.extraction_attempt_id == attempt_id,
            Draft.extraction_status == "running").values(extraction_status="failed", extraction_error=error_code))
    db.execute(update(ExtractionAttempt).where(ExtractionAttempt.id == attempt_id,
        ExtractionAttempt.status == "running").values(status="succeeded" if changed.rowcount == 1 and values is not None else "failed",
                                                      error=error_code))
    db.commit()
    db.refresh(draft)
    return draft
