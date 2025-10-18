"""
Cart management tools for the Grocery List Agent
"""

from typing import Dict, List, Any, Optional
from strands import tool

try:
    from backend_bedrock.tools.product_tools.registry import execute_catalog_tool
    from backend_bedrock.dynamo.queries import get_user_profile
    from backend_bedrock.tools.cart_tools.session_storage import (
        save_cart_item, get_cart_items, remove_cart_item, calculate_cart_total as calc_cart_total
    )
    from backend_bedrock.tools.cart_tools.llm_parser import parse_grocery_request_with_llm
    from backend_bedrock.tools.cart_tools.error_handler import (
        handle_cart_errors, validate_session_id, validate_item_name, validate_quantity,
        ProductNotFoundError, BudgetExceededError, AvailabilityError
    )
except ImportError:
    from tools.product_tools.registry import execute_catalog_tool
    from dynamo.queries import get_user_profile
    from tools.cart_tools.session_storage import (
        save_cart_item, get_cart_items, remove_cart_item, calculate_cart_total as calc_cart_total
    )
    from tools.cart_tools.llm_parser import parse_grocery_request_with_llm
    from tools.cart_tools.error_handler import (
        handle_cart_errors, validate_session_id, validate_item_name, validate_quantity,
        ProductNotFoundError, BudgetExceededError, AvailabilityError
    )


@tool
@handle_cart_errors
def process_natural_language_request(user_request: str, session_id: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    Process natural language requests for cart management
    
    Args:
        user_request: Natural language request from user
        session_id: Session ID for cart operations
        user_id: User ID for personalization
        
    Returns:
        Dict with processed results
    """
    try:
        # Generate default session_id if none provided
        if not session_id:
            session_id = "default_session"
        # Use LLM to intelligently parse the request
        parsed_request = parse_grocery_request_with_llm(user_request)
        action = parsed_request.get("action", "add")
        items = parsed_request.get("items", [])
        confidence = parsed_request.get("intent_confidence", 0.8)
        special_requests = parsed_request.get("special_requests", [])
        
        if action == "add":
            if not items:
                return {
                    "success": False,
                    "message": "I couldn't identify any items to add. Please specify what you'd like to add to your cart.",
                    "parsing_confidence": confidence
                }
            
            results = []
            total_added = 0
            
            for item_info in items:
                item_name = item_info["name"]
                quantity = int(item_info["quantity"])
                
                # Include special requests in the search
                if special_requests:
                    item_name = f"{' '.join(special_requests)} {item_name}"
                
                # Add each item
                add_result = add_item_to_cart(item_name, quantity, session_id)
                results.append({
                    "item": item_name,
                    "quantity": quantity,
                    "unit": item_info.get("unit", "items"),
                    "special_requests": special_requests,
                    "result": add_result
                })
                
                if add_result.get("success"):
                    total_added += 1
            
            if total_added == len(items):
                message = f"Successfully added all {total_added} items to your cart!"
            elif total_added > 0:
                message = f"Added {total_added} out of {len(items)} items to your cart. Check the details below."
            else:
                message = "I couldn't add any items to your cart. Please check the details below."
            
            return {
                "success": total_added > 0,
                "message": message,
                "action": "intelligent_batch_add",
                "items_processed": len(items),
                "items_added": total_added,
                "parsing_confidence": confidence,
                "special_requests": special_requests,
                "results": results
            }
        
        elif action == "view":
            return get_cart_summary(session_id)
        
        elif action == "budget":
            if user_id:
                return check_budget_status(session_id, user_id)
            else:
                return {
                    "success": False,
                    "message": "I need your user ID to check budget status."
                }
        
        elif action == "check_availability":
            # Use LLM-parsed items for availability check
            if items:
                item_name = items[0]["name"]
                if special_requests:
                    item_name = f"{' '.join(special_requests)} {item_name}"
                return check_item_availability(item_name)
            else:
                return {
                    "success": False,
                    "message": "Please specify which item you'd like me to check availability for.",
                    "parsing_confidence": confidence
                }
        
        else:
            return {
                "success": False,
                "message": f"I detected you want to '{action}' but I'm not sure how to help with that yet. Try being more specific."
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I had trouble understanding your request. Please try rephrasing it."
        }


@tool
def check_item_availability(item_name: str) -> Dict[str, Any]:
    """
    Check availability of a specific item
    
    Args:
        item_name: Name of the item to check
        
    Returns:
        Dict with availability status and details
    """
    try:
        # Search for the product first
        search_result = execute_catalog_tool("search_products", {"query": item_name, "limit": 5})
        
        if not search_result.get("success") or not search_result.get("products"):
            return {
                "success": False,
                "message": f"Could not find '{item_name}' in our catalog.",
                "available": False,
                "alternatives_suggested": False
            }
        
        products = search_result["products"]
        available_products = []
        out_of_stock_products = []
        
        for product in products:
            # Check stock status:
            # - If in_stock field is missing: assume available (default True)
            # - If in_stock is explicitly False: mark as out of stock
            # - If in_stock is True: mark as available
            in_stock_status = product.get("in_stock", True)  # Default to True if field missing
            
            if in_stock_status is True:
                available_products.append({
                    "name": product.get("name"),
                    "price": product.get("price", 0),
                    "item_id": product.get("item_id"),
                    "category": product.get("category", "")
                })
            else:  # in_stock_status is False
                out_of_stock_products.append({
                    "name": product.get("name"),
                    "price": product.get("price", 0),
                    "item_id": product.get("item_id")
                })
        
        if available_products:
            return {
                "success": True,
                "available": True,
                "message": f"Found {len(available_products)} available options for '{item_name}'",
                "available_products": available_products,
                "out_of_stock_products": out_of_stock_products
            }
        else:
            return {
                "success": True,
                "available": False,
                "message": f"'{item_name}' is currently out of stock. Would you like me to suggest alternatives?",
                "available_products": [],
                "out_of_stock_products": out_of_stock_products,
                "suggest_alternatives": True
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I couldn't check availability right now. Please try again."
        }


@tool
@handle_cart_errors
def add_item_to_cart(item_name: str, quantity: int = 1, session_id: str = None) -> Dict[str, Any]:
    """
    Add an item to the shopping cart
    
    Args:
        item_name: Name of the item to add
        quantity: Quantity to add (default: 1)
        session_id: Session ID for cart storage
        
    Returns:
        Dict with success status and item details
    """
    print(f"DEBUG - add_item_to_cart called with item_name='{item_name}', quantity={quantity}, session_id='{session_id}'")
    try:
        # Generate default session_id if none provided
        if not session_id:
            session_id = "default_session"
        # First check availability
        availability_result = check_item_availability(item_name)
        
        if not availability_result.get("success"):
            return availability_result
        
        if not availability_result.get("available"):
            # Item is out of stock, suggest alternatives
            return {
                "success": False,
                "message": availability_result.get("message"),
                "suggest_alternatives": True,
                "out_of_stock_products": availability_result.get("out_of_stock_products", [])
            }
        
        available_products = availability_result.get("available_products", [])
        
        # If multiple available options, let user choose
        if len(available_products) > 1:
            product_options = []
            for i, product in enumerate(available_products[:3]):
                product_options.append(f"{i+1}. {product.get('name', 'Unknown')} - ${product.get('price', 0):.2f}")
            
            return {
                "success": True,
                "requires_selection": True,
                "message": f"I found multiple available options for '{item_name}'. Please specify which one:",
                "options": product_options,
                "products": available_products
            }
        
        # Single available product - add to cart
        product = available_products[0]
        
        # Check budget impact before adding
        user_profile = get_user_profile("user_id") if "user_id" else {}  # TODO: get actual user_id
        user_profile = user_profile or {}  # Handle None case
        budget_limit = float(user_profile.get("budget_limit", 100))
        
        # Get current cart total
        current_cart = calc_cart_total(session_id)
        current_total = current_cart.get("total_cost", 0.0)
        
        item_cost = product.get("price", 0) * quantity
        new_total = current_total + item_cost
        
        # Check if adding this item would exceed budget
        budget_warning = ""
        if new_total > budget_limit:
            overage = new_total - budget_limit
            budget_warning = f" ⚠️ This will put you ${overage:.2f} over your ${budget_limit:.2f} budget."
        elif new_total > budget_limit * 0.9:  # 90% of budget
            remaining = budget_limit - new_total
            budget_warning = f" ⚠️ You'll have only ${remaining:.2f} left in your budget."
        
        # Store in DynamoDB cart table
        item_data = {
            "item_id": product.get("item_id"),
            "name": product.get("name"),
            "price": product.get("price", 0),
            "quantity": quantity,
            "category": product.get("category", "")
        }
        
        # Try to save to session storage
        saved = save_cart_item(session_id, "user_id", item_data)  # TODO: get actual user_id
        
        total_price = product.get("price", 0) * quantity
        
        message = f"Added {quantity}x {product.get('name', item_name)} to your cart for ${total_price:.2f}"
        if budget_warning:
            message += budget_warning
        
        return {
            "success": True,
            "message": message,
            "item": item_data,
            "session_id": session_id,
            "saved_to_storage": saved,
            "budget_status": {
                "current_total": current_total,
                "new_total": new_total,
                "budget_limit": budget_limit,
                "over_budget": new_total > budget_limit,
                "budget_warning": budget_warning
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I encountered an error while adding the item to your cart. Please try again."
        }


@tool
def get_cart_summary(session_id: str = None) -> Dict[str, Any]:
    """
    Get current cart contents and total
    
    Args:
        session_id: Session ID for cart retrieval
        
    Returns:
        Dict with cart contents and total
    """
    try:
        # Generate default session_id if none provided
        if not session_id:
            session_id = "default_session"
        # Get cart summary from session storage
        cart_summary = calc_cart_total(session_id)
        
        if not cart_summary.get("success"):
            return {
                "success": False,
                "message": "Could not retrieve your cart.",
                "error": cart_summary.get("error")
            }
        
        items = cart_summary.get("items", [])
        total_cost = cart_summary.get("total_cost", 0.0)
        item_count = cart_summary.get("item_count", 0)
        
        if item_count == 0:
            message = "Your cart is currently empty. Add some items to get started!"
        else:
            message = f"Your cart has {item_count} items totaling ${total_cost:.2f}"
        
        return {
            "success": True,
            "message": message,
            "items": items,
            "total_cost": total_cost,
            "item_count": item_count,
            "session_id": session_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I couldn't retrieve your cart. Please try again."
        }


@tool
def remove_item_from_cart(item_id: str, session_id: str) -> Dict[str, Any]:
    """
    Remove an item from the shopping cart
    
    Args:
        item_id: ID of the item to remove
        session_id: Session ID for cart storage
        
    Returns:
        Dict with success status
    """
    try:
        # Remove from DynamoDB cart table
        removed = remove_cart_item(session_id, item_id)
        
        if removed:
            return {
                "success": True,
                "message": f"Item removed from your cart.",
                "session_id": session_id
            }
        else:
            return {
                "success": False,
                "message": f"Could not remove item from cart. It may not exist.",
                "session_id": session_id
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I couldn't remove the item from your cart. Please try again."
        }


@tool
def find_substitutes_for_item(item_name: str, user_id: str) -> Dict[str, Any]:
    """
    Find substitute products for unavailable items
    
    Args:
        item_name: Name of the unavailable item
        user_id: User ID for personalized suggestions
        
    Returns:
        Dict with substitute suggestions
    """
    try:
        # First search for the original item to get its ID
        search_result = execute_catalog_tool("search_products", {"query": item_name, "limit": 1})
        
        if not search_result.get("success") or not search_result.get("products"):
            return {
                "success": False,
                "message": f"Could not find '{item_name}' to suggest substitutes.",
            }
        
        product = search_result["products"][0]
        item_id = product.get("item_id")
        
        if not item_id:
            return {
                "success": False,
                "message": f"Could not find product ID for '{item_name}'.",
            }
        
        # Find substitutes using existing tool
        substitute_result = execute_catalog_tool("find_product_substitutes", {"item_id": item_id})
        
        if not substitute_result.get("success"):
            return {
                "success": False,
                "message": f"Could not find substitutes for '{item_name}'. You might want to try a different product.",
            }
        
        substitutes = substitute_result.get("substitutes", [])
        if not substitutes:
            return {
                "success": True,
                "message": f"No direct substitutes found for '{item_name}', but you could try browsing the {product.get('category', 'same')} category.",
                "substitutes": []
            }
        
        # Format substitute suggestions
        substitute_list = []
        for sub in substitutes[:3]:  # Top 3 substitutes
            availability = "✅ Available" if sub.get("in_stock", False) else "❌ Out of Stock"
            substitute_list.append(f"• {sub.get('name', 'Unknown')} - ${sub.get('price', 0):.2f} ({availability})")
        
        return {
            "success": True,
            "message": f"Here are some alternatives to '{item_name}':",
            "substitutes": substitute_list,
            "substitute_products": substitutes[:3]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I couldn't find substitutes right now. Please try again."
        }


@tool
def suggest_budget_alternatives(session_id: str, user_id: str, target_savings: float = 10.0) -> Dict[str, Any]:
    """
    Suggest lower-cost alternatives to reduce cart total
    
    Args:
        session_id: Session ID for cart retrieval
        user_id: User ID for budget information
        target_savings: Target amount to save
        
    Returns:
        Dict with alternative suggestions
    """
    try:
        # Get current cart
        cart_summary = calc_cart_total(session_id)
        if not cart_summary.get("success"):
            return {
                "success": False,
                "message": "Could not analyze your cart for budget alternatives."
            }
        
        items = cart_summary.get("items", [])
        if not items:
            return {
                "success": True,
                "message": "Your cart is empty, so you're already within any budget!",
                "alternatives": []
            }
        
        # Find most expensive items that could be replaced
        expensive_items = sorted(items, key=lambda x: x.get("price", 0) * x.get("quantity", 1), reverse=True)
        alternatives = []
        
        for item in expensive_items[:3]:  # Top 3 most expensive
            item_name = item.get("product_name", "")
            if item_name:
                # Find cheaper alternatives in same category
                search_result = execute_catalog_tool("search_products", {"query": item_name, "limit": 5})
                if search_result.get("success") and search_result.get("products"):
                    current_price = item.get("price", 0)
                    cheaper_options = [
                        p for p in search_result["products"] 
                        if p.get("price", 0) < current_price and p.get("in_stock", False)
                    ]
                    
                    if cheaper_options:
                        best_alternative = min(cheaper_options, key=lambda x: x.get("price", 0))
                        savings = current_price - best_alternative.get("price", 0)
                        
                        alternatives.append({
                            "current_item": item_name,
                            "current_price": current_price,
                            "alternative": best_alternative.get("name"),
                            "alternative_price": best_alternative.get("price", 0),
                            "savings": savings,
                            "item_id": best_alternative.get("item_id")
                        })
        
        total_potential_savings = sum(alt["savings"] for alt in alternatives)
        
        if alternatives:
            return {
                "success": True,
                "message": f"I found {len(alternatives)} ways to save up to ${total_potential_savings:.2f}:",
                "alternatives": alternatives,
                "total_potential_savings": total_potential_savings
            }
        else:
            return {
                "success": True,
                "message": "Your cart already has good value items. Consider removing some items to reduce the total.",
                "alternatives": []
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I couldn't find budget alternatives right now."
        }


@tool
def check_budget_status(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Check if cart is within user's budget
    
    Args:
        session_id: Session ID for cart retrieval
        user_id: User ID for budget information
        
    Returns:
        Dict with budget status
    """
    try:
        # Get user profile for budget limit
        user_profile = get_user_profile(user_id) if user_id else {}
        budget_limit = float(user_profile.get("budget_limit", 100))
        
        # Get current cart total from session storage
        cart_summary = calc_cart_total(session_id)
        cart_total = cart_summary.get("total_cost", 0.0)
        
        remaining_budget = budget_limit - cart_total
        budget_percentage = (cart_total / budget_limit) * 100 if budget_limit > 0 else 0
        
        if budget_percentage >= 90:
            status = "⚠️ Over Budget"
            message = f"Your cart total (${cart_total:.2f}) exceeds your budget of ${budget_limit:.2f}!"
        elif budget_percentage >= 75:
            status = "⚠️ Near Budget Limit"
            message = f"You're close to your budget limit. ${remaining_budget:.2f} remaining."
        else:
            status = "✅ Within Budget"
            message = f"You have ${remaining_budget:.2f} remaining in your ${budget_limit:.2f} budget."
        
        return {
            "success": True,
            "status": status,
            "message": message,
            "cart_total": cart_total,
            "budget_limit": budget_limit,
            "remaining_budget": remaining_budget,
            "budget_percentage": budget_percentage
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "I couldn't check your budget status right now."
        }