from src.catalogue.schemas import Product

PRODUCTS = (
    Product(sku="OAT-1L-06", name="Barista oat milk 1L", aliases=("oat milk", "barista oat"), pack_size=6, price="13.80", stock_cases=40),
    Product(sku="OAT-1L-12", name="Original oat milk 1L", aliases=("oat milk", "original oat"), pack_size=12, price="24.00", stock_cases=25),
    Product(sku="COF-1KG-06", name="House coffee beans 1kg", aliases=("house beans", "coffee"), pack_size=6, price="96.00", stock_cases=15),
    Product(sku="CUP-12OZ-50", name="Paper cups 12oz", aliases=("cups", "12oz cups"), pack_size=50, price="5.50", stock_cases=8),
)

def list_products() -> tuple[Product, ...]:
    return PRODUCTS
