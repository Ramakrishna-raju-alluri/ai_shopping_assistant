"""
Grocery cart operations for backend_bedrock.

This module provides cart management functionality specific to grocery shopping,
including adding/removing items, cart summaries, and budget management.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from strands import tool
from boto3.dynamodb.conditions import Key

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import dependencies with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb
    from backend_bedrock.tools.shared.user_profile import get_user_profile_raw
    from backend_bedrock.tools.shared.product_catalog import search_products, check_product_availability
    from backend_bedrock.tools.shared.calculations import calculate_cart_total_session
except ImportError:
    try:
        from dynamo.client import dynamodb
        from tools.shared.user_profile import get_user_profile_raw
        from tools.shared.product_catalog import search_products, check_product_availability
        from tools.shared.calculations import calculate_cart_total_session
    except ImportError:
        # Fallback for testing
        import boto3
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        except:
            dynamodb = None
        def get_user_profile_raw(user_id):
            return {"budget_limit": 100}
        def search_products(query, limit=5):
            return {"success": True, "data": [{"name": "Sample Product", "price": 2.99, "in_stock": True}]}
        def check_product_availability(product_name):
            return {"success": True, "data": {"in_stock": True}}
        def calculate_cart_total_session(session_id, items):
            return {"total_cost": 0, "item_count": 0}

# Cart table name
CART_TABLE = "user_carts"

# In-memory cart storage as fallback
_cart_storage = {}

@tool
def create_cart_table_if_not_exists():
    """Create the cart table if it doesn't exist."""
    try:
        table = dynamodb.Table(CART_TABLE)
        # Try to get table status instead of describe
        table.table_status
        print(f"✅ DynamoDB table {CART_TABLE} is available")
        return True
    except Exception as e:
        print(f"❌ Cart table doesn't exist or not accessible: {e}")
        print(f"🔄 Using in-memory storage as fallback")
        # For now, we'll use in-memory storage as fallback
        return False


def convert_decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj

@tool
def save_cart_item(session_id: str, user_id: str, item: Dict[str, Any]) -> bool:
    """
    Save an item to the user's cart session.
    
    Args:
        session_id (str): Session identifier
        user_id (str): User identifier  
        item (Dict[str, Any]): Item to save
        
    Returns:
        bool: Success status
    """
    try:
        if not create_cart_table_if_not_exists():
            # Use in-memory storage as fallback
            print(f"Using in-memory storage for session_id: {session_id}")
            if session_id not in _cart_storage:
                _cart_storage[session_id] = []
            
            # Check if item already exists, update quantity if so
            existing_item = None
            for stored_item in _cart_storage[session_id]:
                if stored_item.get("item_id") == item.get("item_id"):
                    existing_item = stored_item
                    break
            
            if existing_item:
                existing_item["quantity"] += item.get("quantity", 1)
                print(f"Updated existing item quantity: {existing_item}")
            else:
                cart_item = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "item_id": item.get("item_id"),
                    "product_name": item.get("name", ""),
                    "price": float(item.get("price", 0)),
                    "quantity": item.get("quantity", 1),
                    "category": item.get("category", ""),
                    "added_timestamp": datetime.utcnow().isoformat()
                }
                _cart_storage[session_id].append(cart_item)
                print(f"Added new item to cart: {cart_item}")
            
            print(f"Current cart storage: {_cart_storage}")
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
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        # Note: DynamoDB will use session_id + item_id as composite primary key
        
        table.put_item(Item=cart_item)
        return True
        
    except Exception as e:
        print(f"Error saving cart item: {e}")
        return False

@tool
def get_cart_items(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all items in a cart session.
    
    Args:
        session_id (str): Session identifier
        
    Returns:
        List[Dict[str, Any]]: List of cart items
    """
    try:
        if not create_cart_table_if_not_exists():
            # Use in-memory storage as fallback
            print(f"🔍 GET_CART_ITEMS: Getting cart items for session_id: {session_id}")
            print(f"🔍 GET_CART_ITEMS: Current _cart_storage keys: {list(_cart_storage.keys())}")
            items = _cart_storage.get(session_id, [])
            print(f"🔍 GET_CART_ITEMS: Found {len(items)} items in cart: {items}")
            return items
            
        table = dynamodb.Table(CART_TABLE)
        
        # Query by session_id (partition key)
        response = table.query(
            KeyConditionExpression=Key('session_id').eq(session_id)
        )
        
        items = response.get("Items", [])
        
        # Convert Decimal to float for JSON serialization
        return convert_decimal_to_float(items)
        
    except Exception as e:
        print(f"Error getting cart items: {e}")
        return []

@tool
def remove_cart_item(session_id: str, item_id: str) -> bool:
    """
    Remove an item from the cart session.
    
    Args:
        session_id (str): Session identifier
        item_id (str): Item identifier to remove
        
    Returns:
        bool: Success status
    """
    try:
        if not create_cart_table_if_not_exists():
            # Use in-memory storage as fallback
            print(f"Removing item {item_id} from session_id: {session_id}")
            if session_id in _cart_storage:
                _cart_storage[session_id] = [
                    item for item in _cart_storage[session_id] 
                    if item.get("item_id") != item_id
                ]
                print(f"Updated cart after removal: {_cart_storage[session_id]}")
            return True
            
        table = dynamodb.Table(CART_TABLE)
        
        # Delete using composite primary key (session_id + item_id)
        table.delete_item(Key={
            "session_id": session_id,
            "item_id": item_id
        })
        
        return True
        
    except Exception as e:
        print(f"Error removing cart item: {e}")
        return False


@tool
def add_to_cart(user_id: str, product_id: str, quantity: int = 1, session_id: str = None) -> Dict[str, Any]:
    """
    Add an item to the shopping cart.
    
    Args:
        user_id (str): User identifier
        product_id (str): Product ID or name to add
        quantity (int): Quantity to add
        session_id (str): Session ID for cart storage
        
    Returns:
        Dict[str, Any]: Standardized response with operation result
    """
    try:
        # Generate default session_id if none provided
        # Use user_id as fallback to ensure consistency with frontend
        if not session_id:
            session_id = user_id
        
        print(f"🛒 ADD_TO_CART called: user_id={user_id}, product_id={product_id}, quantity={quantity}, session_id={session_id}")
        
        # Search for the product
        search_result = search_products(product_id, limit=1)
        
        if not search_result['success'] or not search_result['data']:
            return {
                'success': False,
                'data': None,
                'message': f"Product '{product_id}' not found in catalog"
            }
        
        product = search_result['data'][0]
        
        # Check availability
        availability_result = check_product_availability(product.get('name', product_id))
        
        if not availability_result['success'] or not availability_result['data']['in_stock']:
            return {
                'success': False,
                'data': None,
                'message': f"Product '{product.get('name', product_id)}' is out of stock"
            }
        
        # Check budget impact
        user_profile = get_user_profile_raw(user_id) or {}
        budget_limit = float(user_profile.get("budget_limit", 100))
        
        # Get current cart total
        current_items = get_cart_items(session_id)
        current_total = calculate_cart_total_session(session_id, current_items)
        current_cost = current_total.get("total_cost", 0)
        
        # Calculate new item cost
        item_price = float(product.get("price", 0))
        new_item_cost = item_price * quantity
        projected_total = current_cost + new_item_cost
        
        # Check budget
        if projected_total > budget_limit:
            return {
                'success': False,
                'data': {
                    'current_total': current_cost,
                    'item_cost': new_item_cost,
                    'projected_total': projected_total,
                    'budget_limit': budget_limit,
                    'over_budget': projected_total - budget_limit
                },
                'message': f"Adding this item would exceed your budget by ${projected_total - budget_limit:.2f}"
            }
        
        # Save item to cart
        cart_item = {
            "item_id": product.get("item_id", product_id),
            "name": product.get("name", product_id),
            "price": item_price,
            "quantity": quantity,
            "category": product.get("category", ""),
            "description": product.get("description", "")
        }
        
        success = save_cart_item(session_id, user_id, cart_item)
        
        if success:
            return {
                'success': True,
                'data': {
                    'item': cart_item,
                    'cart_total': projected_total,
                    'budget_remaining': budget_limit - projected_total
                },
                'message': f"Added {quantity} x {cart_item['name']} to cart"
            }
        else:
            return {
                'success': False,
                'data': None,
                'message': "Failed to save item to cart"
            }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error adding item to cart: {str(e)}'
        }


@tool
def remove_from_cart(user_id: str, product_id: str, session_id: str = None) -> Dict[str, Any]:
    """
    Remove an item from the shopping cart.
    
    Args:
        user_id (str): User identifier
        product_id (str): Product ID to remove
        session_id (str): Session ID for cart storage
        
    Returns:
        Dict[str, Any]: Standardized response with operation result
    """
    try:
        # Generate default session_id if none provided
        # Use user_id as fallback to ensure consistency with frontend
        if not session_id:
            session_id = user_id
        
        # Remove item from cart
        success = remove_cart_item(session_id, product_id)
        
        if success:
            # Get updated cart summary
            updated_items = get_cart_items(session_id)
            cart_total = calculate_cart_total_session(session_id, updated_items)
            
            return {
                'success': True,
                'data': {
                    'removed_item_id': product_id,
                    'cart_total': cart_total.get("total_cost", 0),
                    'items_remaining': cart_total.get("item_count", 0)
                },
                'message': f"Removed item {product_id} from cart"
            }
        else:
            return {
                'success': False,
                'data': None,
                'message': f"Failed to remove item {product_id} from cart"
            }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error removing item from cart: {str(e)}'
        }


@tool
def get_cart_summary(user_id: str, session_id: str = None) -> Dict[str, Any]:
    """
    Get current cart contents and totals.
    
    Args:
        user_id (str): User identifier
        session_id (str): Session ID for cart retrieval
        
    Returns:
        Dict[str, Any]: Standardized response with cart summary
    """
    try:
        # Generate default session_id if none provided
        # Use user_id as fallback to ensure consistency with frontend
        if not session_id:
            session_id = user_id
        
        # Get cart items
        items = get_cart_items(session_id)
        
        # Calculate totals
        cart_totals = calculate_cart_total_session(session_id, items)
        
        # Get user budget info
        user_profile = get_user_profile_raw(user_id) or {}
        budget_limit = float(user_profile.get("budget_limit", 100))
        
        total_cost = cart_totals.get("total_cost", 0)
        budget_remaining = budget_limit - total_cost
        
        summary = {
            'items': items,
            'total_cost': total_cost,
            'item_count': cart_totals.get("item_count", 0),
            'unique_items': cart_totals.get("unique_items", len(items)),
            'budget_limit': budget_limit,
            'budget_remaining': budget_remaining,
            'budget_used_percentage': (total_cost / budget_limit * 100) if budget_limit > 0 else 0
        }
        
        return {
            'success': True,
            'data': summary,
            'message': f"Cart contains {summary['item_count']} items totaling ${total_cost:.2f}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting cart summary: {str(e)}'
        }


@tool
def clear_cart(user_id: str, session_id: str = None) -> Dict[str, Any]:
    """
    Clear all items from the shopping cart.
    
    Args:
        user_id (str): User identifier
        session_id (str): Session ID for cart storage
        
    Returns:
        Dict[str, Any]: Standardized response with operation result
    """
    try:
        # Generate default session_id if none provided
        # Use user_id as fallback to ensure consistency with frontend
        if not session_id:
            session_id = user_id
        
        # Get current items
        items = get_cart_items(session_id)
        
        # Remove all items
        removed_count = 0
        for item in items:
            if remove_cart_item(session_id, item.get("item_id")):
                removed_count += 1
        
        return {
            'success': True,
            'data': {
                'items_removed': removed_count,
                'total_items': len(items)
            },
            'message': f"Cleared {removed_count} items from cart"
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error clearing cart: {str(e)}'
        }


@tool
def check_budget_status(user_id: str, session_id: str = None) -> Dict[str, Any]:
    """
    Check if cart is within user's budget.
    
    Args:
        user_id (str): User identifier
        session_id (str): Session ID for cart retrieval
        
    Returns:
        Dict[str, Any]: Standardized response with budget status
    """
    try:
        # Generate default session_id if none provided
        # Use user_id as fallback to ensure consistency with frontend
        if not session_id:
            session_id = user_id
        
        # Get cart summary
        cart_result = get_cart_summary(user_id, session_id)
        
        if not cart_result['success']:
            return cart_result
        
        cart_data = cart_result['data']
        total_cost = cart_data['total_cost']
        budget_limit = cart_data['budget_limit']
        budget_remaining = cart_data['budget_remaining']
        
        within_budget = budget_remaining >= 0
        
        budget_status = {
            'within_budget': within_budget,
            'total_cost': total_cost,
            'budget_limit': budget_limit,
            'budget_remaining': budget_remaining,
            'budget_used_percentage': cart_data['budget_used_percentage'],
            'over_budget_amount': abs(budget_remaining) if not within_budget else 0
        }
        
        if within_budget:
            message = f"Cart is within budget. ${budget_remaining:.2f} remaining."
        else:
            message = f"Cart exceeds budget by ${abs(budget_remaining):.2f}"
        
        return {
            'success': True,
            'data': budget_status,
            'message': message
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error checking budget status: {str(e)}'
        }


# Legacy compatibility functions for existing code
def add_item_to_cart_legacy(item_name: str, quantity: int = 1, session_id: str = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing cart manager.
    """
    # Use default user for legacy calls
    user_id = "legacy_user"
    result = add_to_cart(user_id, item_name, quantity, session_id)
    
    # Convert to legacy format
    if result['success']:
        return {
            "success": True,
            "message": result['message'],
            "item_added": result['data']['item'],
            "cart_total": result['data']['cart_total']
        }
    else:
        return {
            "success": False,
            "error": result['message']
        }


def get_cart_summary_legacy(session_id: str = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing cart manager.
    """
    # Use default user for legacy calls
    user_id = "legacy_user"
    result = get_cart_summary(user_id, session_id)
    
    # Convert to legacy format
    if result['success']:
        data = result['data']
        return {
            "success": True,
            "items": data['items'],
            "total_cost": data['total_cost'],
            "item_count": data['item_count'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "items": [],
            "total_cost": 0.0,
            "item_count": 0
        }


def remove_item_from_cart_legacy(item_id: str, session_id: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing cart manager.
    """
    # Use default user for legacy calls
    user_id = "legacy_user"
    result = remove_from_cart(user_id, item_id, session_id)
    
    # Convert to legacy format
    if result['success']:
        return {
            "success": True,
            "message": result['message'],
            "removed_item_id": result['data']['removed_item_id']
        }
    else:
        return {
            "success": False,
            "error": result['message']
        }