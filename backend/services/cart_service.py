# services/cart_service.py
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import uuid
from dynamo.client import dynamodb, USER_TABLE, PRODUCT_TABLE
from boto3.dynamodb.conditions import Attr, Key

class CartService:
    """Service for managing user shopping carts"""
    
    def __init__(self):
        self.user_table = dynamodb.Table(USER_TABLE)
        self.product_table = dynamodb.Table(PRODUCT_TABLE)
    
    def get_user_cart(self, user_id: str) -> Dict[str, Any]:
        """Get user's current cart"""
        try:
            response = self.user_table.get_item(Key={"user_id": user_id})
            user_data = response.get("Item", {})
            
            # Get cart from user profile
            cart = user_data.get("current_cart", [])
            cart_total = sum(Decimal(str(item.get('price', 0))) * item.get('quantity', 1) for item in cart)
            
            return {
                "user_id": user_id,
                "items": cart,
                "total_items": len(cart),
                "total_cost": float(cart_total),
                "last_updated": user_data.get("last_updated", datetime.now().isoformat())
            }
        except Exception as e:
            print(f"Error getting user cart: {e}")
            return {
                "user_id": user_id,
                "items": [],
                "total_items": 0,
                "total_cost": 0.0,
                "last_updated": datetime.now().isoformat()
            }
    
    def add_items_to_cart(self, user_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add items to user's cart"""
        try:
            # Get current user data
            response = self.user_table.get_item(Key={"user_id": user_id})
            user_data = response.get("Item", {})
            
            # Get current cart
            current_cart = user_data.get("current_cart", [])
            
            # Add new items to cart
            for item in items:
                item_id = item.get("item_id")
                quantity = item.get("quantity", 1)
                
                # Check if item already exists in cart
                existing_item = None
                for cart_item in current_cart:
                    if cart_item.get("item_id") == item_id:
                        existing_item = cart_item
                        break
                
                if existing_item:
                    # Update quantity
                    existing_item["quantity"] = existing_item.get("quantity", 1) + quantity
                else:
                    # Add new item
                    cart_item = {
                        "item_id": item_id,
                        "name": item.get("name"),
                        "price": Decimal(str(item.get("price", 0))),
                        "quantity": quantity,
                        "added_at": datetime.now().isoformat()
                    }
                    current_cart.append(cart_item)
            
            # Update user profile with new cart
            user_data["current_cart"] = current_cart
            user_data["last_updated"] = datetime.now().isoformat()
            
            # Save to DynamoDB
            self.user_table.put_item(Item=user_data)
            
            # Calculate new totals
            cart_total = sum(Decimal(str(item.get('price', 0))) * item.get('quantity', 1) for item in current_cart)
            
            return {
                "success": True,
                "message": f"Added {len(items)} items to cart",
                "cart": {
                    "user_id": user_id,
                    "items": current_cart,
                    "total_items": len(current_cart),
                    "total_cost": float(cart_total),
                    "last_updated": user_data["last_updated"]
                }
            }
            
        except Exception as e:
            print(f"Error adding items to cart: {e}")
            return {
                "success": False,
                "message": f"Error adding items to cart: {str(e)}",
                "cart": None
            }
    
    def remove_item_from_cart(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Remove item from user's cart"""
        try:
            # Get current user data
            response = self.user_table.get_item(Key={"user_id": user_id})
            user_data = response.get("Item", {})
            
            # Get current cart
            current_cart = user_data.get("current_cart", [])
            
            # Remove item
            current_cart = [item for item in current_cart if item.get("item_id") != item_id]
            
            # Update user profile
            user_data["current_cart"] = current_cart
            user_data["last_updated"] = datetime.now().isoformat()
            
            # Save to DynamoDB
            self.user_table.put_item(Item=user_data)
            
            # Calculate new totals
            cart_total = sum(Decimal(str(item.get('price', 0))) * item.get('quantity', 1) for item in current_cart)
            
            return {
                "success": True,
                "message": "Item removed from cart",
                "cart": {
                    "user_id": user_id,
                    "items": current_cart,
                    "total_items": len(current_cart),
                    "total_cost": float(cart_total),
                    "last_updated": user_data["last_updated"]
                }
            }
            
        except Exception as e:
            print(f"Error removing item from cart: {e}")
            return {
                "success": False,
                "message": f"Error removing item from cart: {str(e)}",
                "cart": None
            }
    
    def update_item_quantity(self, user_id: str, item_id: str, quantity: int) -> Dict[str, Any]:
        """Update item quantity in cart"""
        try:
            if quantity <= 0:
                return self.remove_item_from_cart(user_id, item_id)
            
            # Get current user data
            response = self.user_table.get_item(Key={"user_id": user_id})
            user_data = response.get("Item", {})
            
            # Get current cart
            current_cart = user_data.get("current_cart", [])
            
            # Update quantity
            for item in current_cart:
                if item.get("item_id") == item_id:
                    item["quantity"] = quantity
                    break
            
            # Update user profile
            user_data["current_cart"] = current_cart
            user_data["last_updated"] = datetime.now().isoformat()
            
            # Save to DynamoDB
            self.user_table.put_item(Item=user_data)
            
            # Calculate new totals
            cart_total = sum(Decimal(str(item.get('price', 0))) * item.get('quantity', 1) for item in current_cart)
            
            return {
                "success": True,
                "message": "Cart updated",
                "cart": {
                    "user_id": user_id,
                    "items": current_cart,
                    "total_items": len(current_cart),
                    "total_cost": float(cart_total),
                    "last_updated": user_data["last_updated"]
                }
            }
            
        except Exception as e:
            print(f"Error updating cart: {e}")
            return {
                "success": False,
                "message": f"Error updating cart: {str(e)}",
                "cart": None
            }
    
    def clear_cart(self, user_id: str) -> Dict[str, Any]:
        """Clear user's cart"""
        try:
            # Get current user data
            response = self.user_table.get_item(Key={"user_id": user_id})
            user_data = response.get("Item", {})
            
            # Clear cart
            user_data["current_cart"] = []
            user_data["last_updated"] = datetime.now().isoformat()
            
            # Save to DynamoDB
            self.user_table.put_item(Item=user_data)
            
            return {
                "success": True,
                "message": "Cart cleared",
                "cart": {
                    "user_id": user_id,
                    "items": [],
                    "total_items": 0,
                    "total_cost": 0.0,
                    "last_updated": user_data["last_updated"]
                }
            }
            
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return {
                "success": False,
                "message": f"Error clearing cart: {str(e)}",
                "cart": None
            }

# Global cart service instance
cart_service = CartService() 