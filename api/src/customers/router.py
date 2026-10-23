from fastapi import APIRouter
from src.customers.schemas import Customer
from src.customers.service import list_customers

router = APIRouter(prefix="/customers", tags=["customers"])
router.add_api_route("", list_customers, response_model=list[Customer], methods=["GET"])
