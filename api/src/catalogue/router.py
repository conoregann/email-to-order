from fastapi import APIRouter

router = APIRouter(prefix="/catalogue", tags=["catalogue"])

@router.get("/products")
def list_products() -> list[dict]:
    return []
