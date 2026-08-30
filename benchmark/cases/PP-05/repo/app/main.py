from fastapi import FastAPI, HTTPException
from .service import PRODUCTS, is_available

app = FastAPI()


@app.get("/products/{product_id}")
async def get_product(product_id: int, include_availability: bool = False) -> dict:
    product = PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    result = {"id": product["id"], "name": product["name"]}
    if include_availability:
        result["available"] = is_available(product_id)
    return result
