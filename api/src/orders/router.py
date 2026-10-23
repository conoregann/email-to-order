from fastapi import APIRouter, HTTPException
from src.orders.schemas import SampleEmail
from src.orders.service import list_samples

router = APIRouter(prefix="/orders", tags=["orders"])
# Static sample route precedes the dynamic order identifier route.
router.add_api_route("/samples", list_samples, response_model=list[SampleEmail], methods=["GET"])

@router.get("")
def list_orders() -> list[dict]:
    return []

@router.get("/{order_id}")
def get_order(order_id: str):
    raise HTTPException(404, "Order not found")
