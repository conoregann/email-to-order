import time
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.customers.service import workspace_customers
from src.orders.drafts import draft_values
from src.orders.models import ConfirmedOrder, Draft
from src.orders.validation import validate


def confirm_draft(db: Session, draft: Draft, version: int) -> None:
    existing = db.scalar(select(ConfirmedOrder).where(ConfirmedOrder.draft_id == draft.id))
    if existing:
        db.refresh(draft)
        return
    if version != draft.version:
        raise HTTPException(409, "Draft changed. Reload and review the latest version before confirming.")
    values = draft_values(draft)
    customers = workspace_customers(db, draft.guest_id)
    validation = validate(values, customers)
    if not validation["can_confirm"]:
        raise HTTPException(422, {"message": "Resolve all blocking issues before confirmation.", "validation": validation})
    now = int(time.time())
    # This conditional write serializes confirmation with saves and competing confirmations.
    changed = db.execute(update(Draft).where(Draft.id == draft.id, Draft.version == version,
                         Draft.status == "draft").values(status="confirmed", version=version + 1, updated_at=now),
                         execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        if db.scalar(select(ConfirmedOrder).where(ConfirmedOrder.draft_id == draft.id)):
            db.refresh(draft)
            return
        raise HTTPException(409, "Draft changed. Reload and review before confirming.")
    customer = next(customer for customer in customers if customer.id == values.customer_id)
    order_id = str(uuid4())
    number = f"ORD-{datetime.fromtimestamp(now, timezone.utc):%Y}-{order_id[:13].replace('-', '').upper()}"
    details = [f"{line['cases']} case(s) of {line['name']} ({line['pack_size']} units per case): EUR {line['line_total']}"
               for line in validation["lines"]]
    preview = (f"SIMULATED CONFIRMATION — no email sent\nTo: {customer.email}\nSubject: Order {number}\n\n"
               f"Hello {customer.name},\n\nYour order {number} has been recorded in this demo.\n"
               + "\n".join(details) + f"\nTotal: EUR {validation['total']}\nDelivery address: {values.delivery_address}\n"
               + (f"Delivery instructions: {values.delivery_instructions}\n" if values.delivery_instructions else "")
               + (f"Requested delivery: {values.requested_delivery_date} (not guaranteed).\n" if values.requested_delivery_date else "")
               + "Stock is simulated; no inventory is reserved.")
    snapshot = {"id": order_id, "number": number, "confirmed_at": now,
                "customer": customer.model_dump(mode="json"), "values": values.model_dump(mode="json"),
                "validation": validation, "original_email": draft.original_email,
                "extraction": draft.extraction, "initial_values": draft.initial_values, "source": draft.source, "confirmation_preview": preview}
    db.add(ConfirmedOrder(id=order_id, draft_id=draft.id, guest_id=draft.guest_id,
                          number=number, snapshot=snapshot, confirmed_at=now))
    db.commit()
    db.refresh(draft)
