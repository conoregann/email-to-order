from src.orders.schemas import SampleEmail

SAMPLES = (
    SampleEmail(id="straightforward", title="Straightforward order", scenario="Exact SKU and saved address", body="From: orders@harbour.example\nSubject: Stock order\n\nPlease send 2 cases of OAT-1L-06 (6 x 1L per case) to Harbour Cafe, 12 Quay Street, Demo Town, Ireland. Thanks!"),
    SampleEmail(id="ambiguous", title="Ambiguous product", scenario="Two products share an alias", body="From: orders@harbour.example\nSubject: Oat milk\n\nPlease send 3 cases of oat milk to 12 Quay Street, Demo Town, Ireland. Please check which oat milk we need."),
    SampleEmail(id="missing-address", title="Missing delivery address", scenario="Staff must confirm delivery location", body="From: orders@harbour.example\nSubject: Coffee order\n\nPlease order 1 case of COF-1KG-06 (6 x 1kg). I will confirm the delivery address later."),
    SampleEmail(id="quantity", title="Quantity and pack size", scenario="Units need clarification", body="From: orders@meadow.example\nSubject: Cups\n\nWe need 75 CUP-12OZ-50 cups for Meadow Deli, 8 Meadow Road, Demo Town, Ireland. Not sure how many cases that is."),
    SampleEmail(id="stock", title="Insufficient simulated stock", scenario="Quantity exceeds catalogue stock", body="From: orders@meadow.example\nSubject: Large order\n\nPlease send 20 cases of CUP-12OZ-50 (50 cups per case) to 8 Meadow Road, Demo Town, Ireland."),
)

def list_samples() -> tuple[SampleEmail, ...]:
    return SAMPLES
