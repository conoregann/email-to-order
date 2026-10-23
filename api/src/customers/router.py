from fastapi import APIRouter

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("")
def list_customers() -> list[dict]:
    return []
