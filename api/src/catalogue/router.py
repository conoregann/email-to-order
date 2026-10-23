from fastapi import APIRouter
from src.catalogue.schemas import Product
from src.catalogue.service import list_products

router = APIRouter(prefix="/catalogue", tags=["catalogue"])
router.add_api_route("/products", list_products, response_model=list[Product], methods=["GET"])
