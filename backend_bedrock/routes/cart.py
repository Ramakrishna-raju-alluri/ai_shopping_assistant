from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from backend_bedrock.routes.auth import get_current_user

# Import cart operations
try:
    from backend_bedrock.tools.grocery.cart_operations import get_cart_summary, add_to_cart, remove_from_cart
except ImportError:
    from tools.grocery.cart_operations import get_cart_summary, add_to_cart, remove_from_cart

router = APIRouter()


class CartItem(BaseModel):
    item_id: str
    quantity: int = 1


class UpdateCartItem(BaseModel):
    item_id: str
    quantity: int


@router.get("/cart")
async def get_cart(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user's cart contents"""
    try:
        user_id = current_user.get("user_id", "default_user")
        session_id = user_id  # Use user_id as session_id for consistency
        print(f"🔍 Frontend GET /cart - user_id: {user_id}, session_id: {session_id}")
        
        # Get cart summary using the same system agents use
        result = get_cart_summary(user_id, session_id)
        
        print(f"🔍 Frontend cart result: {result}")
        
        if result['success']:
            items = result['data']['items']
            
            # Transform items to match frontend expectations
            frontend_items = []
            for item in items:
                frontend_items.append({
                    "item_id": item.get('item_id'),
                    "name": item.get('product_name'),  # Frontend expects 'name', backend has 'product_name'
                    "price": item.get('price'),
                    "quantity": item.get('quantity'),
                    "added_at": item.get('added_timestamp', '')
                })
            
            cart_data = {
                "success": True,
                "cart": {
                    "user_id": user_id,
                    "items": frontend_items,
                    "total_items": result['data']['item_count'],
                    "total_cost": result['data']['total_cost'],
                    "last_updated": "now"
                }
            }
            print(f"🔍 Cart has {len(frontend_items)} items:")
            for item in frontend_items:
                print(f"    - {item.get('name', 'Unknown')} (qty: {item.get('quantity', 0)})")
            print(f"🔍 Returning cart data with {len(frontend_items)} items")
            return cart_data
        else:
            print(f"❌ Cart operation failed: {result.get('message', 'Unknown error')}")
            return {
                "success": True,
                "cart": {
                    "user_id": user_id,
                    "items": [],
                    "total_items": 0,
                    "total_cost": 0,
                    "last_updated": "now"
                }
            }
            
    except Exception as e:
        print(f"Error getting cart: {e}")
        return {"items": [], "total_cost": 0, "item_count": 0, "budget_remaining": 100}


@router.post("/cart/add")
async def add_to_cart_api(item: CartItem, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Add item to cart"""
    try:
        user_id = current_user.get("user_id", "default_user")
        session_id = user_id  # Use user_id as session_id for consistency
        print(f"🔍 Frontend POST /cart/add - user_id: {user_id}, session_id: {session_id}, item: {item.item_id}")
        
        # Add item using the same system agents use
        result = add_to_cart(user_id, item.item_id, item.quantity, session_id)
        
        if result['success']:
            # Get updated cart after adding item
            updated_cart = get_cart_summary(user_id, session_id)
            if updated_cart['success']:
                frontend_items = []
                for item in updated_cart['data']['items']:
                    frontend_items.append({
                        "item_id": item.get('item_id'),
                        "name": item.get('product_name'),
                        "price": item.get('price'),
                        "quantity": item.get('quantity'),
                        "added_at": item.get('added_timestamp', '')
                    })
                
                return {
                    "success": True,
                    "message": result['message'],
                    "cart": {
                        "user_id": user_id,
                        "items": frontend_items,
                        "total_items": updated_cart['data']['item_count'],
                        "total_cost": updated_cart['data']['total_cost'],
                        "last_updated": "now"
                    }
                }
            else:
                return {
                    "success": True,
                    "message": result['message'],
                    "cart": {
                        "user_id": user_id,
                        "items": [],
                        "total_items": 0,
                        "total_cost": 0,
                        "last_updated": "now"
                    }
                }
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        print(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cart/remove/{item_id}")
async def remove_from_cart_api(item_id: str, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Remove item from cart"""
    try:
        user_id = current_user.get("user_id", "default_user")
        session_id = user_id  # Use user_id as session_id for consistency
        print(f"🔍 Frontend DELETE /cart/remove - user_id: {user_id}, session_id: {session_id}, item_id: {item_id}")
        
        # Remove item using the same system agents use
        result = remove_from_cart(user_id, item_id, session_id)
        
        if result['success']:
            # Get updated cart after removing item
            updated_cart = get_cart_summary(user_id, session_id)
            if updated_cart['success']:
                frontend_items = []
                for item in updated_cart['data']['items']:
                    frontend_items.append({
                        "item_id": item.get('item_id'),
                        "name": item.get('product_name'),
                        "price": item.get('price'),
                        "quantity": item.get('quantity'),
                        "added_at": item.get('added_timestamp', '')
                    })
                
                return {
                    "success": True,
                    "message": result['message'],
                    "cart": {
                        "user_id": user_id,
                        "items": frontend_items,
                        "total_items": updated_cart['data']['item_count'],
                        "total_cost": updated_cart['data']['total_cost'],
                        "last_updated": "now"
                    }
                }
            else:
                return {
                    "success": True,
                    "message": result['message'],
                    "cart": {
                        "user_id": user_id,
                        "items": [],
                        "total_items": 0,
                        "total_cost": 0,
                        "last_updated": "now"
                    }
                }
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        print(f"Error removing from cart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Keep legacy endpoints for backward compatibility
@router.post("/cart")
async def add_to_cart_legacy(item: CartItem, current_user: dict = Depends(get_current_user)):
    """Legacy add to cart endpoint"""
    return await add_to_cart_api(item, current_user)


@router.delete("/cart/{item_id}")
async def remove_from_cart_legacy(item_id: str, current_user: dict = Depends(get_current_user)):
    """Legacy remove from cart endpoint"""
    return await remove_from_cart_api(item_id, current_user)


@router.put("/cart/update")
async def update_cart_item_api(item: UpdateCartItem, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Update item quantity in cart"""
    try:
        user_id = current_user.get("user_id", "default_user")
        session_id = user_id
        print(f"🔍 Frontend PUT /cart/update - user_id: {user_id}, item_id: {item.item_id}, quantity: {item.quantity}")
        
        # Import the new update function
        from tools.grocery.cart_operations import update_cart_item
        
        # Use the new direct update function instead of remove-then-add
        result = update_cart_item(user_id, item.item_id, item.quantity, session_id)
        
        if result['success']:
            # Get updated cart
            updated_cart = get_cart_summary(user_id, session_id)
            if updated_cart['success']:
                frontend_items = []
                for cart_item in updated_cart['data']['items']:
                    frontend_items.append({
                        "item_id": cart_item.get('item_id'),
                        "name": cart_item.get('product_name'),
                        "price": cart_item.get('price'),
                        "quantity": cart_item.get('quantity'),
                        "added_at": cart_item.get('added_timestamp', '')
                    })
                
                return {
                    "success": True,
                    "message": result['message'],
                    "cart": {
                        "user_id": user_id,
                        "items": frontend_items,
                        "total_items": updated_cart['data']['item_count'],
                        "total_cost": updated_cart['data']['total_cost'],
                        "last_updated": "now"
                    }
                }
            else:
                return {
                    "success": True,
                    "message": result['message'],
                    "cart": {
                        "user_id": user_id,
                        "items": [],
                        "total_items": 0,
                        "total_cost": 0,
                        "last_updated": "now"
                    }
                }
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        print(f"Error updating cart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cart/clear")
async def clear_cart_api(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Clear all items from cart"""
    try:
        user_id = current_user.get("user_id", "default_user")
        session_id = user_id
        print(f"🔍 Frontend DELETE /cart/clear - user_id: {user_id}")
        
        # Import clear_cart function
        from tools.grocery.cart_operations import clear_cart
        
        result = clear_cart(user_id, session_id)
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "cart": {
                    "user_id": user_id,
                    "items": [],
                    "total_items": 0,
                    "total_cost": 0,
                    "last_updated": "now"
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result['message'])
            
    except Exception as e:
        print(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail=str(e))


