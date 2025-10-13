#!/usr/bin/env python3
"""
Cart Operation Agent - Handles add to cart, view cart, and cart management requests
"""

import re
from typing import Dict, Any, List, Optional
from services.cart_service import cart_service
from agents.product_lookup_agent import extract_product_name_from_query, lookup_product_info


def extract_cart_request_info(user_query: str) -> Dict[str, Any]:
    """
    Extract product name and quantity from cart operation queries
    Examples:
    - "add bananas to cart" → {"product_name": "bananas", "quantity": 1}
    - "add 2 organic milk to my cart" → {"product_name": "organic milk", "quantity": 2}
    - "put cottage cheese in cart" → {"product_name": "cottage cheese", "quantity": 1}
    - "delete bananas from cart" → {"product_name": "bananas", "quantity": 1, "operation": "delete"}
    """
    query_lower = user_query.lower()

    # Determine operation type
    operation = "add"
    if any(word in query_lower for word in ["delete", "remove", "take out", "take away"]):
        operation = "delete"

    # Extract quantity (default to 1 if not specified)
    quantity = 1
    if operation == "add":
        quantity_match = re.search(r'add\s+(\d+)\s+', query_lower)
        if quantity_match:
            quantity = int(quantity_match.group(1))
    else:
        quantity_match = re.search(r'(?:delete|remove)\s+(\d+)\s+', query_lower)
        if quantity_match:
            quantity = int(quantity_match.group(1))

    # Extract product name by removing cart-related words
    if operation == "add":
        cart_words = ['add', 'put', 'place', 'to', 'in', 'my', 'cart', 'shopping', 'basket']
    else:
        cart_words = ['delete', 'remove', 'take', 'out', 'away', 'from', 'my', 'cart', 'shopping', 'basket']

    product_query = query_lower

    # Remove cart operation words
    for word in cart_words:
        product_query = re.sub(r'\b' + word + r'\b', '', product_query)

    # Clean up extra spaces and numbers
    product_query = re.sub(r'\b\d+\b', '', product_query)
    product_query = re.sub(r'\s+', ' ', product_query).strip()

    # Extract product name using the existing product lookup logic
    product_name = extract_product_name_from_query(product_query)

    return {
        "product_name": product_name,
        "quantity": quantity,
        "operation": operation,
        "original_query": user_query
    }


def handle_cart_operation(user_query: str, user_id: str, intent_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle cart operation requests (add to cart, delete from cart, view/clear cart, etc.)
    """
    print(f"🛒 Cart Operation - Processing query: {user_query}")

    # Quick handling for view/clear cart
    query_lower = user_query.lower()
    if any(phrase in query_lower for phrase in ['view cart', 'show cart', 'my cart', "what's in my cart", 'see cart', 'cart contents']):
        return handle_view_cart(user_id)
    if any(phrase in query_lower for phrase in ['clear cart', 'empty cart', 'clear my cart', 'empty my cart']):
        return handle_clear_cart(user_id)

    # Extract cart request information
    cart_info = extract_cart_request_info(user_query)
    product_name = cart_info["product_name"]
    quantity = cart_info["quantity"]
    operation = cart_info["operation"]

    # Use intent data if available
    if intent_data and intent_data.get("cart_operation_type"):
        operation = intent_data["cart_operation_type"]

    if not product_name:
        return {
            "success": False,
            "message": f"I couldn't identify which product you want to {operation}. Please be more specific. For example: 'Add bananas to cart' or 'Delete milk from my cart'"
        }

    print(f"🛒 Cart Operation - Extracted product: {product_name}, quantity: {quantity}, operation: {operation}")

    # Look up product information
    product_info = lookup_product_info(product_name)

    if not product_info.get("found"):
        return {
            "success": False,
            "message": f"I couldn't find '{product_name}' in our product database. Please check the product name and try again."
        }

    if operation == "add":
        return _handle_add(user_id, product_info, quantity)
    elif operation == "delete":
        return _handle_delete(user_id, product_info)
    else:
        return {
            "success": False,
            "message": f"I don't understand the operation '{operation}'. I can help you add, delete, view, or clear your cart."
        }


def _handle_add(user_id: str, product_info: Dict[str, Any], quantity: int) -> Dict[str, Any]:
    # Check if product is in stock
    if not product_info.get("in_stock", True):
        return {
            "success": False,
            "message": f"Sorry, {product_info['name']} is currently out of stock and cannot be added to your cart."
        }

    # Prepare cart item
    cart_item = {
        "item_id": product_info["product"].get("item_id"),
        "name": product_info["name"],
        "price": float(product_info["price"]),
        "quantity": quantity
    }

    try:
        result = cart_service.add_items_to_cart(user_id, [cart_item])
        if result["success"]:
            return {
                "success": True,
                "message": f"Great! I've added {quantity} {product_info['name']} to your cart. Your cart now has {result['cart']['total_items']} items with a total of ${result['cart']['total_cost']:.2f}.",
                "cart_info": result["cart"],
                "product_info": product_info,
                "quantity": quantity
            }
        else:
            return {
                "success": False,
                "message": f"Sorry, I couldn't add {product_info['name']} to your cart: {result['message']}"
            }
    except Exception as e:
        print(f"Error adding to cart: {e}")
        return {
            "success": False,
            "message": f"Sorry, I encountered an error while adding {product_info['name']} to your cart. Please try again."
        }


def _handle_delete(user_id: str, product_info: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Check if item is in the cart first
        cart_data = cart_service.get_user_cart(user_id)
        if cart_data["total_items"] == 0:
            return {
                "success": False,
                "message": "Your cart is empty. There are no items to remove."
            }

        item_id = product_info["product"].get("item_id")
        in_cart = any(item.get("item_id") == item_id for item in cart_data["items"])
        if not in_cart:
            return {
                "success": False,
                "message": f"{product_info['name']} is not in your cart. I can only remove items that are currently in your cart."
            }

        result = cart_service.remove_item_from_cart(user_id, item_id)
        if result["success"]:
            return {
                "success": True,
                "message": f"I've removed {product_info['name']} from your cart. Your cart now has {result['cart']['total_items']} items with a total of ${result['cart']['total_cost']:.2f}.",
                "cart_info": result["cart"],
                "product_info": product_info
            }
        else:
            return {
                "success": False,
                "message": f"Sorry, I couldn't remove {product_info['name']} from your cart: {result['message']}"
            }
    except Exception as e:
        print(f"Error removing from cart: {e}")
        return {
            "success": False,
            "message": f"Sorry, I encountered an error while removing {product_info['name']} from your cart. Please try again."
        }


def handle_view_cart(user_id: str) -> Dict[str, Any]:
    """
    Handle view cart requests
    """
    try:
        cart_data = cart_service.get_user_cart(user_id)

        if cart_data["total_items"] == 0:
            return {
                "success": True,
                "message": "Your cart is currently empty. You can add items by saying 'Add [product name] to cart'.",
                "cart_info": cart_data
            }

        # Format cart items for display
        items_text = []
        for item in cart_data["items"]:
            items_text.append(f"• {item['name']} - ${item['price']:.2f} x {item['quantity']}")

        cart_summary = f"Here's your current cart ({cart_data['total_items']} items, Total: ${cart_data['total_cost']:.2f}):\n\n"
        cart_summary += "\n".join(items_text)

        return {
            "success": True,
            "message": cart_summary,
            "cart_info": cart_data
        }

    except Exception as e:
        print(f"Error viewing cart: {e}")
        return {
            "success": False,
            "message": "Sorry, I encountered an error while retrieving your cart. Please try again."
        }


def handle_clear_cart(user_id: str) -> Dict[str, Any]:
    """
    Handle clear cart requests
    """
    try:
        result = cart_service.clear_cart(user_id)
        if result["success"]:
            return {
                "success": True,
                "message": "Your cart has been cleared successfully.",
                "cart_info": result["cart"]
            }
        else:
            return {
                "success": False,
                "message": f"Sorry, I couldn't clear your cart: {result['message']}"
            }
    except Exception as e:
        print(f"Error clearing cart: {e}")
        return {
            "success": False,
            "message": "Sorry, I encountered an error while clearing your cart. Please try again."
        } 