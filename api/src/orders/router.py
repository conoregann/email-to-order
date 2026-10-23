from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("")
def list_orders() -> list[dict]:
    return []

@router.get("/{order_id}")
def get_order(order_id: str):
    raise HTTPException(404, "Order not found")
