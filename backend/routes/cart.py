# routes/cart.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from decimal import Decimal
from services.cart_service import cart_service
from routes.auth import get_current_user

router = APIRouter()

# Pydantic models for request/response
class CartItem(BaseModel):
    item_id: str = Field(..., description="Product item ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    quantity: int = Field(1, description="Quantity to add")

class AddToCartRequest(BaseModel):
    items: List[CartItem] = Field(..., description="Items to add to cart")

class UpdateQuantityRequest(BaseModel):
    item_id: str = Field(..., description="Product item ID")
    quantity: int = Field(..., description="New quantity")

class CartResponse(BaseModel):
    success: bool
    message: str
    cart: Optional[Dict[str, Any]] = None

@router.get("/cart", response_model=CartResponse)
async def get_cart(current_user: dict = Depends(get_current_user)):
    """Get user's current cart"""
    try:
        user_id = current_user.get("user_id")
        cart_data = cart_service.get_user_cart(user_id)
        
        return CartResponse(
            success=True,
            message="Cart retrieved successfully",
            cart=cart_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cart: {str(e)}")

@router.post("/cart/add", response_model=CartResponse)
async def add_to_cart(request: AddToCartRequest, current_user: dict = Depends(get_current_user)):
    """Add items to user's cart"""
    try:
        user_id = current_user.get("user_id")
        
        # Convert to list of dictionaries
        items = [item.dict() for item in request.items]
        
        result = cart_service.add_items_to_cart(user_id, items)
        
        if result["success"]:
            return CartResponse(
                success=True,
                message=result["message"],
                cart=result["cart"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to cart: {str(e)}")

@router.put("/cart/update", response_model=CartResponse)
async def update_cart_quantity(request: UpdateQuantityRequest, current_user: dict = Depends(get_current_user)):
    """Update item quantity in cart"""
    try:
        user_id = current_user.get("user_id")
        
        result = cart_service.update_item_quantity(user_id, request.item_id, request.quantity)
        
        if result["success"]:
            return CartResponse(
                success=True,
                message=result["message"],
                cart=result["cart"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cart: {str(e)}")

@router.delete("/cart/remove/{item_id}", response_model=CartResponse)
async def remove_from_cart(item_id: str, current_user: dict = Depends(get_current_user)):
    """Remove item from cart"""
    try:
        user_id = current_user.get("user_id")
        
        result = cart_service.remove_item_from_cart(user_id, item_id)
        
        if result["success"]:
            return CartResponse(
                success=True,
                message=result["message"],
                cart=result["cart"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing from cart: {str(e)}")

@router.delete("/cart/clear", response_model=CartResponse)
async def clear_cart(current_user: dict = Depends(get_current_user)):
    """Clear user's cart"""
    try:
        user_id = current_user.get("user_id")
        
        result = cart_service.clear_cart(user_id)
        
        if result["success"]:
            return CartResponse(
                success=True,
                message=result["message"],
                cart=result["cart"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cart: {str(e)}")

# Special endpoint for adding final cart from chatbot
@router.post("/cart/add-final", response_model=CartResponse)
async def add_final_cart_to_user_cart(items: List[Dict[str, Any]], current_user: dict = Depends(get_current_user)):
    """Add final cart items from chatbot to user's cart"""
    try:
        user_id = current_user.get("user_id")
        
        # Convert items to cart format
        cart_items = []
        for item in items:
            cart_item = {
                "item_id": item.get("item_id"),
                "name": item.get("name"),
                "price": item.get("price", item.get("discounted_price", 0)),
                "quantity": 1  # Default quantity
            }
            cart_items.append(cart_item)
        
        result = cart_service.add_items_to_cart(user_id, cart_items)
        
        if result["success"]:
            return CartResponse(
                success=True,
                message=f"Added {len(cart_items)} items from final cart to your shopping cart!",
                cart=result["cart"]
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding final cart: {str(e)}") 