"""
Shared calculation tools for backend_bedrock.

This module provides centralized calculation functionality for costs, calories,
and nutritional values that can be used by multiple agents across different domains.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import database functions with flexible import system
try:
    from dynamo.client import dynamodb, PRODUCT_TABLE
    from dynamo.queries import get_all_products
    from tools.shared.product_catalog import search_products
except ImportError:
    try:
        from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE
        from backend_bedrock.dynamo.queries import get_all_products
        from backend_bedrock.tools.shared.product_catalog import search_products
    except ImportError:
        print("⚠️ Error importing database modules in calculations.py")
        # Fallback implementations
        # dynamodb = None
        # PRODUCT_TABLE = "mock-products2_with_calories"
        
        # def get_all_products():
        #     return []
        
        # def search_products(query: str, limit: int = 20) -> Dict[str, Any]:
        #     """Fallback search_products function"""
        #     return {
        #         'success': False,
        #         'data': [],
        #         'count': 0,
        #         'query': query,
        #         'message': f"Database not available - no products found for '{query}'"
        #     }


def convert_decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    import decimal
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj





@tool
def calculate_cost(items) -> Dict[str, Any]:
    """
    Calculate total cost for a list of items.
    
    Args:
        items: Can be:
            - List[str]: Product names like ["eggs", "milk", "bread"]
            - List[Dict]: Items with 'name' and optional 'quantity' keys
            - Dict[str, int]: item_id -> quantity mapping
            
    Returns:
        Dict[str, Any]: Standardized response with cost calculation
    """
    try:
        print(f"🔍 CALCULATE_COST called with items: {items}")
        print(f"🔍 Items type: {type(items)}")
        
        # Validate input
        if not items:
            return {
                'success': False,
                'data': None,
                'message': 'No items provided for cost calculation'
            }
        
        # Convert string to list if needed
        if isinstance(items, str):
            items = [items]
        
        # Get product data
        products_data = get_all_products()
        
        # if not products_data:
        #     # Fallback to mock data
        #     products_data = [
        #         {"name": "Large Eggs", "price": 3.99, "item_id": "eggs_001"},
        #         {"name": "Whole Milk", "price": 4.29, "item_id": "milk_001"},
        #         {"name": "White Bread", "price": 2.49, "item_id": "bread_001"},
        #         {"name": "Chicken Breast", "price": 6.99, "item_id": "chicken_001"},
        #         {"name": "Organic Tomatoes", "price": 2.99, "item_id": "tomatoes_001"},
        #         {"name": "Organic Spinach", "price": 3.99, "item_id": "spinach_001"},
        #         {"name": "Organic Onions", "price": 1.99, "item_id": "onions_001"},
        #         {"name": "Organic Carrots", "price": 2.49, "item_id": "carrots_001"}
        #     ]
        
        total_cost = 0.0
        item_breakdown = []
        
        # Handle different input formats
        if isinstance(items, dict):
            # Handle item_id -> quantity mapping
            table = dynamodb.Table(PRODUCT_TABLE)
            
            for item_id, quantity in items.items():
                try:
                    response = table.get_item(Key={"item_id": item_id})
                    if "Item" in response:
                        product = response["Item"]
                        price = float(product.get("price", 0))
                        item_total = price * quantity
                        total_cost += item_total
                        
                        item_breakdown.append({
                            "item_id": item_id,
                            "name": product.get("name", ""),
                            "price": price,
                            "quantity": quantity,
                            "item_total": item_total
                        })
                    else:
                        item_breakdown.append({
                            "item_id": item_id,
                            "name": "Unknown Item",
                            "price": 0.0,
                            "quantity": quantity,
                            "item_total": 0.0,
                            "error": "Item not found"
                        })
                except Exception as e:
                    item_breakdown.append({
                        "item_id": item_id,
                        "name": "Error",
                        "price": 0.0,
                        "quantity": quantity,
                        "item_total": 0.0,
                        "error": str(e)
                    })
        
        else:
            # Handle list of product names or item dictionaries
            for item in items:
                if isinstance(item, str):
                    # Simple product name
                    product_name = item
                    quantity = 1
                elif isinstance(item, dict):
                    # Item dictionary with name and optional quantity
                    product_name = item.get("name", "")
                    quantity = item.get("quantity", 1)
                else:
                    continue
                
                # Find product by name using search_products
                search_result = search_products(product_name, limit=1)
                
                if search_result['success'] and search_result['data']:
                    product_data = search_result['data'][0]
                    price = float(product_data.get("price", 0))
                    item_total = price * quantity
                    total_cost += item_total
                    
                    item_breakdown.append({
                        "product_name": product_name,
                        "matched_name": product_data.get("name", product_name),
                        "price": price,
                        "quantity": quantity,
                        "item_total": item_total
                    })
                else:
                    item_breakdown.append({
                        "product_name": product_name,
                        "matched_name": None,
                        "price": 0.0,
                        "quantity": quantity,
                        "item_total": 0.0,
                        "error": "Product not found"
                    })
        
        # Convert any Decimal types
        result = convert_decimal_to_float({
            "total_cost": total_cost,
            "item_breakdown": item_breakdown,
            "items_found": len([item for item in item_breakdown if item.get("price", 0) > 0]),
            "total_items": len(item_breakdown)
        })
        
        return {
            'success': True,
            'data': result,
            'message': f'Calculated cost for {len(item_breakdown)} items: ${total_cost:.2f}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error calculating cost: {str(e)}'
        }


@tool
def calculate_calories(items) -> Dict[str, Any]:
    """
    Calculate total calories for a list of items, showing all relevant product matches.
    
    Args:
        items: Can be:
            - List[str]: Product names
            - List[Dict]: Items with 'name' and optional 'quantity' keys
            - str: Single product name
            - Dict: Single item with name and quantity
            
    Returns:
        Dict[str, Any]: Standardized response with calorie calculation for all matching products
    """
    try:
        print(f"==================================================")
        print(f"🚨 LOOK FOR THIS MESSAGE IN YOUR LOGS! 🚨")
        print(f"==================================================")
        print(f"🔍 CALCULATE_CALORIES called with items: {items}")
        print(f"🔍 Items type: {type(items)}")
        print(f"🔍 Items repr: {repr(items)}")
        print(f"==================================================")
        
        # Handle different input formats that Nova Pro might send
        if isinstance(items, str):
            # If it's a string, try to parse it as a single product name
            print(f"🔄 Converting string to list: {items}")
            items = [items]
        elif isinstance(items, dict):
            # If it's a dict, convert to list format
            print(f"🔄 Converting dict to list: {items}")
            if 'name' in items or 'product_name' in items:
                items = [items]
            else:
                # Handle other dict formats
                items = [{'name': k, 'quantity': v} for k, v in items.items()]
        elif not isinstance(items, list):
            print(f"❌ Invalid items format: expected list, string, or dict, got {type(items)}")
            return {
                'success': False,
                'data': None,
                'message': f'Invalid items format: expected list, string, or dict, got {type(items)}'
            }
        
        print(f"🔍 Processed items: {items}")
        all_products_breakdown = []
        
        for i, item in enumerate(items):
            print(f"🔍 Processing item {i+1}: {item} (type: {type(item)})")
            
            if isinstance(item, str):
                # Simple product name
                product_name = item
                quantity = 1
                print(f"🔍 String item - name: '{product_name}', quantity: {quantity}")
            elif isinstance(item, dict):
                # Item dictionary with name and optional quantity
                product_name = (
                    item.get("name", "") or 
                    item.get("product_name", "") or 
                    item.get("item_name", "") or
                    str(item)
                )
                quantity = item.get("quantity", 1)
                print(f"🔍 Dict item - name: '{product_name}', quantity: {quantity}")
            else:
                print(f"⚠️ Skipping unknown item type: {type(item)}")
                continue
            
            if not product_name:
                print(f"⚠️ Skipping item with empty product name: {item}")
                all_products_breakdown.append({
                    "search_term": str(item),
                    "matched_products": [],
                    "error": "Empty product name"
                })
                continue
            
            print(f"🔍 Searching for products matching: '{product_name}'")
            
            # Search for products matching the product name
            print(f"🔍 Searching for products matching: '{product_name}'")
            search_result = search_products(product_name, limit=5)
            print(f"🔍 Search result success: {search_result.get('success', False)}")
            print(f"🔍 Search result data count: {len(search_result.get('data', []))}")
            
            all_matched_products = []
            
            if search_result.get('success') and search_result.get('data'):
                for product_data in search_result['data']:
                    product_name_found = product_data.get('name', 'Unknown')
                    
                    print(f"🔍 Found product: {product_name_found}")
                    
                    # Try different calorie fields
                    calories_per_unit = (
                        product_data.get("calories_per_unit") or 
                        product_data.get("calories") or 
                        0
                    )
                    calories_per_unit = int(calories_per_unit) if calories_per_unit else 0
                    item_calories = calories_per_unit * quantity
                    
                    print(f"🔍 Calories per unit: {calories_per_unit}, Total for {quantity}x: {item_calories}")
                    
                    all_matched_products.append({
                        "product_name": product_name_found,
                        "calories_per_unit": calories_per_unit,
                        "quantity": quantity,
                        "total_calories": item_calories,
                        "price": product_data.get("price", 0),
                        "category": product_data.get("category", ""),
                        "in_stock": product_data.get("in_stock", True)
                    })
            
            if all_matched_products:
                all_products_breakdown.append({
                    "search_term": product_name,
                    "matched_products": all_matched_products,
                    "products_found": len(all_matched_products)
                })
            else:
                print(f"❌ No products found for: '{product_name}'")
                all_products_breakdown.append({
                    "search_term": product_name,
                    "matched_products": [],
                    "products_found": 0,
                    "error": "No products found",
                    "suggestion": f"Try searching for more specific terms like 'whole {product_name}' or '{product_name} brand'"
                })
        
        # Calculate summary statistics
        total_searches = len(all_products_breakdown)
        total_products_found = sum(item.get("products_found", 0) for item in all_products_breakdown)
        
        result = {
            "search_results": all_products_breakdown,
            "summary": {
                "total_searches": total_searches,
                "total_products_found": total_products_found,
                "searches_with_results": len([item for item in all_products_breakdown if item.get("products_found", 0) > 0])
            }
        }
        
        print(f"🔍 Final result: {result}")
        print(f"==================================================")
        
        return {
            'success': True,
            'data': result,
            'message': f'Found {total_products_found} products across {total_searches} searches'
        }
        
    except Exception as e:
        print(f"❌ Exception in calculate_calories: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'data': None,
            'message': f'Error calculating calories: {str(e)}'
        }


@tool
def calculate_nutrition(items: Union[List[str], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate comprehensive nutritional values for a list of items.
    
    Args:
        items: Can be:
            - List[str]: Product names
            - List[Dict]: Items with 'name' and optional 'quantity' keys
            
    Returns:
        Dict[str, Any]: Standardized response with nutritional calculation
    """
    try:
        # Get product data
        products_data = get_all_products_raw()
        
        # if not products_data:
        #     # Fallback to mock data with nutrition info
        #     products_data = [
        #         {"name": "Large Eggs", "calories": 70, "protein": 6, "carbs": 1, "fat": 5},
        #         {"name": "Whole Milk", "calories": 150, "protein": 8, "carbs": 12, "fat": 8},
        #         {"name": "White Bread", "calories": 80, "protein": 3, "carbs": 15, "fat": 1},
        #         {"name": "Chicken Breast", "calories": 165, "protein": 31, "carbs": 0, "fat": 4},
        #         {"name": "Organic Tomatoes", "calories": 18, "protein": 1, "carbs": 4, "fat": 0},
        #         {"name": "Organic Spinach", "calories": 7, "protein": 1, "carbs": 1, "fat": 0},
        #         {"name": "Organic Onions", "calories": 40, "protein": 1, "carbs": 9, "fat": 0},
        #         {"name": "Organic Carrots", "calories": 41, "protein": 1, "carbs": 10, "fat": 0}
        #     ]
        
        totals = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0
        }
        
        item_breakdown = []
        
        for item in items:
            if isinstance(item, str):
                # Simple product name
                product_name = item
                quantity = 1
            elif isinstance(item, dict):
                # Item dictionary with name and optional quantity
                product_name = item.get("name", "")
                quantity = item.get("quantity", 1)
            else:
                continue
            
            # Find product by name using search_products
            search_result = search_products(product_name, limit=1)
            
            if search_result['success'] and search_result['data']:
                product_data = search_result['data'][0]
                # Extract nutritional values
                calories = int(product_data.get("calories", 0)) * quantity
                protein = float(product_data.get("protein", 0)) * quantity
                carbs = float(product_data.get("carbs", 0)) * quantity
                fat = float(product_data.get("fat", 0)) * quantity
                
                # Add to totals
                totals["calories"] += calories
                totals["protein"] += protein
                totals["carbs"] += carbs
                totals["fat"] += fat
                
                item_breakdown.append({
                    "product_name": product_name,
                    "matched_name": product_data.get("name", product_name),
                    "quantity": quantity,
                    "nutrition": {
                        "calories": calories,
                        "protein": protein,
                        "carbs": carbs,
                        "fat": fat
                    }
                })
            else:
                item_breakdown.append({
                    "product_name": product_name,
                    "matched_name": None,
                    "quantity": quantity,
                    "nutrition": {
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    },
                    "error": "Product not found"
                })
        
        result = {
            "totals": totals,
            "item_breakdown": item_breakdown,
            "items_found": len([item for item in item_breakdown if item.get("nutrition", {}).get("calories", 0) > 0]),
            "total_items": len(item_breakdown)
        }
        
        return {
            'success': True,
            'data': result,
            'message': f'Calculated nutrition for {len(item_breakdown)} items: {totals["calories"]} calories'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error calculating nutrition: {str(e)}'
        }


@tool
def calculate_cart_total(session_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total cost and item count for a cart session.
    
    Args:
        session_items (List[Dict[str, Any]]): List of cart items with price and quantity
        
    Returns:
        Dict[str, Any]: Standardized response with cart totals
    """
    try:
        total_cost = 0.0
        item_count = 0
        
        for item in session_items:
            price = float(item.get("price", 0))
            quantity = int(item.get("quantity", 1))
            total_cost += price * quantity
            item_count += quantity
        
        result = {
            "total_cost": total_cost,
            "item_count": item_count,
            "unique_items": len(session_items),
            "items": session_items
        }
        
        return {
            'success': True,
            'data': result,
            'message': f'Cart total: ${total_cost:.2f} for {item_count} items'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error calculating cart total: {str(e)}'
        }


# Legacy compatibility functions for existing code
@tool
def calculate_cost_json(product_names: List[str]) -> str:
    """
    Legacy function that returns JSON string for backward compatibility.
    Used by meal planner tools.
    """
    result = calculate_cost(product_names)
    
    if result['success']:
        return json.dumps(result['data'])
    else:
        return json.dumps({"error": result['message'], "total_cost": 0})

@tool
def calculate_calories_json(product_names: List[str]) -> str:
    """
    Legacy function that returns JSON string for backward compatibility.
    Used by meal planner tools.
    """
    result = calculate_calories(product_names)
    
    if result['success']:
        return json.dumps(result['data'])
    else:
        return json.dumps({"error": result['message'], "total_calories": 0})

@tool
def calculate_cart_total_legacy(item_quantities: Dict[str, int]) -> Dict[str, Any]:
    """
    Legacy function for product tools compatibility.
    """
    result = calculate_cost(item_quantities)
    
    if result['success']:
        data = result['data']
        return {
            "success": True,
            "total": data['total_cost'],
            "items": data['item_breakdown'],
            "item_count": data['total_items'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "total": 0.0
        }

@tool
def calculate_cart_total_session(session_id: str, session_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Legacy function for session storage compatibility.
    """
    result = calculate_cart_total(session_items)
    
    if result['success']:
        return result['data']
    else:
        return {
            "success": False,
            "error": result['message'],
            "total_cost": 0.0,
            "item_count": 0
        }