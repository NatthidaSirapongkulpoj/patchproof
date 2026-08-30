PRODUCTS = {1: {"id": 1, "name": "desk lamp", "stock": 3}, 2: {"id": 2, "name": "wall clock", "stock": 0}}


async def is_available(product_id: int) -> bool:
    return PRODUCTS[product_id]["stock"] > 0
