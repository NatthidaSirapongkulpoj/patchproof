from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class OrderRequest(BaseModel):
    item: str
    quantity: int


class OrderResponse(BaseModel):
    item: str
    quantity: int
    status: str


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(order: OrderRequest) -> OrderResponse:
    return OrderResponse(
        item=order.item,
        quantity=order.quantity,
        status="created",
    )
