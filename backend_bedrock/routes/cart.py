from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from backend_bedrock.routes.auth import get_current_user


router = APIRouter()


class CartItem(BaseModel):
    item_id: str
    quantity: int


@router.get("/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    return {"items": []}


@router.post("/cart")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    return {"status": "added"}


@router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, current_user: dict = Depends(get_current_user)):
    return {"status": "removed"}


