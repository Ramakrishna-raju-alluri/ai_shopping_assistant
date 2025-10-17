"""
Cart session storage using DynamoDB
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

try:
    from backend_bedrock.dynamo.client import dynamodb
except ImportError:
    from dynamo.client import dynamodb

# Cart table name - you may need to create this table
CART_TABLE = "user_carts"

def create_cart_table_if_not_exists():
    """Create the cart table if it doesn't exist"""
    try:
        # Check if table exists
        table = dynamodb.Table(CART_TABLE)
        table.load()
        return True
    except Exception:
        # Table doesn't exist, would need to create it
        # For now, we'll use a mock implementation
        return False

def save_cart_item(session_id: str, user_id: str, item: Dict[str, Any]) -> bool:
    """
    Save an item to the user's cart session
    
    Args:
        session_id: Session identifier
        user_id: User identifier  
        item: Item to save
        
    Returns:
        Success status
    """
    try:
        if not create_cart_table_if_not_exists():
            # Mock implementation - in real app, create the table
            return True
            
        table = dynamodb.Table(CART_TABLE)
        
        # Create cart item record
        cart_item = {
            "session_id": session_id,
            "user_id": user_id,
            "item_id": item.get("item_id"),
            "product_name": item.get("name", ""),
            "price": Decimal(str(item.get("price", 0))),
            "quantity": item.get("quantity", 1),
            "category": item.get("category", ""),
            "added_timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()  # 7 day expiry
        }
        
        # Use composite key: session_id + item_id
        cart_item["cart_key"] = f"{session_id}#{item.get('item_id')}"
        
        table.put_item(Item=cart_item)
        return True
        
    except Exception as e:
        print(f"Error saving cart item: {e}")
        return False

def get_cart_items(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all items in a cart session
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of cart items
    """
    try:
        if not create_cart_table_if_not_exists():
            # Mock implementation
            return []
            
        table = dynamodb.Table(CART_TABLE)
        
        # Query by session_id
        response = table.scan(
            FilterExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id}
        )
        
        items = response.get("Items", [])
        
        # Convert Decimal to float for JSON serialization
        for item in items:
            if "price" in item:
                item["price"] = float(item["price"])
                
        return items
        
    except Exception as e:
        print(f"Error getting cart items: {e}")
        return []

def remove_cart_item(session_id: str, item_id: str) -> bool:
    """
    Remove an item from the cart session
    
    Args:
        session_id: Session identifier
        item_id: Item to remove
        
    Returns:
        Success status
    """
    try:
        if not create_cart_table_if_not_exists():
            # Mock implementation
            return True
            
        table = dynamodb.Table(CART_TABLE)
        
        # Delete using composite key
        cart_key = f"{session_id}#{item_id}"
        table.delete_item(Key={"cart_key": cart_key})
        
        return True
        
    except Exception as e:
        print(f"Error removing cart item: {e}")
        return False

def clear_cart(session_id: str) -> bool:
    """
    Clear all items from a cart session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success status
    """
    try:
        items = get_cart_items(session_id)
        
        for item in items:
            remove_cart_item(session_id, item.get("item_id"))
            
        return True
        
    except Exception as e:
        print(f"Error clearing cart: {e}")
        return False

def calculate_cart_total(session_id: str) -> Dict[str, Any]:
    """
    Calculate total cost and item count for a cart
    
    Args:
        session_id: Session identifier
        
    Returns:
        Cart totals and summary
    """
    try:
        items = get_cart_items(session_id)
        
        total_cost = 0.0
        item_count = 0
        
        for item in items:
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 1))
            total_cost += price * quantity
            item_count += quantity
            
        return {
            "success": True,
            "total_cost": total_cost,
            "item_count": item_count,
            "unique_items": len(items),
            "items": items
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_cost": 0.0,
            "item_count": 0
        }

def cleanup_expired_carts():
    """
    Clean up expired cart sessions (utility function)
    """
    try:
        if not create_cart_table_if_not_exists():
            return
            
        table = dynamodb.Table(CART_TABLE)
        current_time = datetime.utcnow().isoformat()
        
        # Scan for expired items
        response = table.scan(
            FilterExpression="expires_at < :now",
            ExpressionAttributeValues={":now": current_time}
        )
        
        expired_items = response.get("Items", [])
        
        # Delete expired items
        for item in expired_items:
            table.delete_item(Key={"cart_key": item["cart_key"]})
            
        print(f"Cleaned up {len(expired_items)} expired cart items")
        
    except Exception as e:
        print(f"Error cleaning up expired carts: {e}")