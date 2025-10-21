"""
Grocery cart operations for backend_bedrock.

This module provides cart management functionality specific to grocery shopping,
including adding/removing items, cart summaries, and budget management.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from strands import tool
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import dependencies with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb, CART_TABLE
    from backend_bedrock.tools.shared.user_profile import get_user_profile_raw
    from backend_bedrock.tools.shared.product_catalog import search_products, check_product_availability
    from backend_bedrock.tools.shared.calculations import calculate_cart_total_session
except ImportError:
    try:
        from dynamo.client import dynamodb, CART_TABLE
        from tools.shared.user_profile import get_user_profile_raw
        from tools.shared.product_catalog import search_products, check_product_availability
        from tools.shared.calculations import calculate_cart_total_session
    except ImportError:
        # Fallback - create DynamoDB resource with explicit credentials from environment
        import boto3
        try:
            # Try to create DynamoDB resource with environment credentials
            dynamodb = boto3.resource(
                "dynamodb", 
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            print(f"✅ DynamoDB resource created with explicit credentials")
        except Exception as e:
            print(f"❌ Failed to create DynamoDB resource: {e}")
            dynamodb = None
        
        # Fallback cart table name
        CART_TABLE = os.getenv("CART_TABLE", "user_carts")
        
        def get_user_profile_raw(user_id):
            return {"budget_limit": 100}
        def search_products(query, limit=5):
            return {"success": True, "data": [{"name": "Sample Product", "price": 2.99, "in_stock": True}]}
        def check_product_availability(product_name):
            return {"success": True, "data": {"in_stock": True}}
        def calculate_cart_total_session(session_id, items):
            return {"total_cost": 0, "item_count": 0}

# In-memory cart storage as fallback
_cart_storage = {}

@tool
def create_cart_table_if_not_exists():
    """Create the cart table if it doesn't exist."""
    try:
        if dynamodb is None:
            print(f"❌ DynamoDB resource not available")
            print(f"🔄 Using in-memory storage as fallback")
            return False
            
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
        
        # Try different key structures based on table schema
        try:
            # First try with session_id as partition key
            response = table.query(
                KeyConditionExpression=Key('session_id').eq(session_id)
            )
        except Exception as e:
            if "cart_key" in str(e):
                # If cart_key is required, try using session_id as cart_key
                try:
                    response = table.query(
                        KeyConditionExpression=Key('cart_key').eq(session_id)
                    )
                except Exception as e2:
                    # If that fails, try scanning with filter (less efficient but works)
                    print(f"⚠️ Query failed, falling back to scan: {e2}")
                    response = table.scan(
                        FilterExpression=Key('session_id').eq(session_id) | Key('cart_key').eq(session_id)
                    )
            else:
                raise e
        
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
        # Use provided session_id, but default to user_id if none provided
        # This ensures consistency between frontend and agent cart operations
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
        # Use provided session_id, but default to user_id if none provided
        # This ensures consistency between frontend and agent cart operations
        if not session_id:
            session_id = user_id
        
        print(f"🗑️ REMOVE_FROM_CART called: user_id={user_id}, product_id={product_id}, session_id={session_id}")
        
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
        # Use provided session_id, but default to user_id if none provided
        # This ensures consistency between frontend and agent cart operations
        if not session_id:
            session_id = user_id
        
        print(f"📋 GET_CART_SUMMARY called: user_id={user_id}, session_id={session_id}")
        
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
def update_cart_item_quantity(session_id: str, item_id: str, new_quantity: int) -> bool:
    """
    Update the quantity of an item in the cart without removing and re-adding.
    
    Args:
        session_id (str): Session identifier
        item_id (str): Item identifier to update
        new_quantity (int): New quantity for the item
        
    Returns:
        bool: Success status
    """
    try:
        if not create_cart_table_if_not_exists():
            # Use in-memory storage as fallback
            print(f"🔄 UPDATE_QUANTITY: Updating item {item_id} to quantity {new_quantity} in session {session_id}")
            if session_id in _cart_storage:
                for item in _cart_storage[session_id]:
                    if item.get("item_id") == item_id:
                        item["quantity"] = new_quantity
                        print(f"✅ Updated item quantity: {item}")
                        return True
                print(f"❌ Item {item_id} not found in cart")
                return False
            return False
            
        table = dynamodb.Table(CART_TABLE)
        
        # Update the item quantity directly using DynamoDB update_item
        response = table.update_item(
            Key={
                "session_id": session_id,
                "item_id": item_id
            },
            UpdateExpression="SET quantity = :new_quantity",
            ExpressionAttributeValues={
                ":new_quantity": new_quantity
            },
            ReturnValues="UPDATED_NEW"
        )
        
        print(f"✅ Updated item {item_id} quantity to {new_quantity}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating cart item quantity: {e}")
        return False


@tool
def update_cart_item(user_id: str, item_id: str, new_quantity: int, session_id: str = None) -> Dict[str, Any]:
    """
    Update the quantity of an item in the shopping cart.
    
    Args:
        user_id (str): User identifier
        item_id (str): Item identifier to update
        new_quantity (int): New quantity for the item
        session_id (str): Session ID for cart storage
        
    Returns:
        Dict[str, Any]: Standardized response with operation result
    """
    try:
        # Use provided session_id, but default to user_id if none provided
        # This ensures consistency between frontend and agent cart operations
        if not session_id:
            session_id = user_id
        
        print(f"🔄 UPDATE_CART_ITEM: user_id={user_id}, item_id={item_id}, new_quantity={new_quantity}, session_id={session_id}")
        
        # If quantity is 0 or negative, remove the item
        if new_quantity <= 0:
            return remove_from_cart(user_id, item_id, session_id)
        
        # Check if item exists in cart first
        current_items = get_cart_items(session_id)
        item_exists = any(item.get("item_id") == item_id for item in current_items)
        
        if not item_exists:
            return {
                'success': False,
                'data': None,
                'message': f"Item {item_id} not found in cart"
            }
        
        # Check budget impact with new quantity
        user_profile = get_user_profile_raw(user_id) or {}
        budget_limit = float(user_profile.get("budget_limit", 100))
        
        # Calculate new total cost
        current_total = 0
        item_price = 0
        for item in current_items:
            if item.get("item_id") == item_id:
                item_price = float(item.get("price", 0))
                # Calculate total without this item's current contribution
                current_total += sum(float(other_item.get("price", 0)) * int(other_item.get("quantity", 0)) 
                                   for other_item in current_items 
                                   if other_item.get("item_id") != item_id)
            else:
                current_total += float(item.get("price", 0)) * int(item.get("quantity", 0))
        
        # Add the new quantity cost
        new_item_cost = item_price * new_quantity
        projected_total = current_total + new_item_cost
        
        # Check budget
        if projected_total > budget_limit:
            return {
                'success': False,
                'data': {
                    'current_total': current_total,
                    'item_cost': new_item_cost,
                    'projected_total': projected_total,
                    'budget_limit': budget_limit,
                    'over_budget': projected_total - budget_limit
                },
                'message': f"Updating to {new_quantity} would exceed your budget by ${projected_total - budget_limit:.2f}"
            }
        
        # Update the quantity directly
        success = update_cart_item_quantity(session_id, item_id, new_quantity)
        
        if success:
            # Get updated cart summary
            updated_items = get_cart_items(session_id)
            cart_total = calculate_cart_total_session(session_id, updated_items)
            
            return {
                'success': True,
                'data': {
                    'updated_item_id': item_id,
                    'new_quantity': new_quantity,
                    'cart_total': cart_total.get("total_cost", 0),
                    'budget_remaining': budget_limit - cart_total.get("total_cost", 0)
                },
                'message': f"Updated {item_id} quantity to {new_quantity}"
            }
        else:
            return {
                'success': False,
                'data': None,
                'message': f"Failed to update item {item_id} quantity"
            }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error updating cart item: {str(e)}'
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
        # Use provided session_id, but default to user_id if none provided
        # This ensures consistency between frontend and agent cart operations
        if not session_id:
            session_id = user_id
        
        print(f"🧹 CLEAR_CART called: user_id={user_id}, session_id={session_id}")
        
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