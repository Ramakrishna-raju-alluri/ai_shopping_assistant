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
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE
    from backend_bedrock.tools.shared.product_catalog import get_all_products_raw
except ImportError:
    try:
        from dynamo.client import dynamodb, PRODUCT_TABLE
        from tools.shared.product_catalog import get_all_products_raw
    except ImportError:
        # Fallback for testing
        import boto3
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        except:
            dynamodb = None
        PRODUCT_TABLE = "mock-products2_with_calories"
        def get_all_products_raw():
            return []


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
def get_product_mapping(products_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Create a mapping of product names to product data for efficient lookups.
    
    Args:
        products_data (List[Dict[str, Any]]): List of product data
        
    Returns:
        Dict[str, Dict[str, Any]]: Mapping of lowercase product names to product data
    """
    product_mapping = {}
    
    for product in products_data:
        name = product.get("name", "").lower()
        if name:
            product_mapping[name] = product
    
    return product_mapping

@tool
def find_product_by_name(product_name: str, product_mapping: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find a product by name using fuzzy matching.
    
    Args:
        product_name (str): Product name to search for
        product_mapping (Dict[str, Dict[str, Any]]): Product mapping
        
    Returns:
        Optional[Dict[str, Any]]: Product data if found, None otherwise
    """
    name_lower = product_name.lower()
    
    # Try exact match first
    if name_lower in product_mapping:
        return product_mapping[name_lower]
    
    # Try partial match (product name contains search term)
    for prod_name, product_data in product_mapping.items():
        if name_lower in prod_name:
            return product_data
    
    # Try reverse partial match (search term contains product name)
    for prod_name, product_data in product_mapping.items():
        if prod_name in name_lower:
            return product_data
    
    # Try word-based matching
    search_words = name_lower.split()
    for prod_name, product_data in product_mapping.items():
        if any(word in prod_name for word in search_words if len(word) > 2):
            return product_data
    
    return None


@tool
def calculate_cost(items: Union[List[str], List[Dict[str, Any]], Dict[str, int]]) -> Dict[str, Any]:
    """
    Calculate total cost for a list of items.
    
    Args:
        items: Can be:
            - List[str]: Product names
            - List[Dict]: Items with 'name' and optional 'quantity' keys
            - Dict[str, int]: item_id -> quantity mapping
            
    Returns:
        Dict[str, Any]: Standardized response with cost calculation
    """
    try:
        # Get product data
        products_data = get_all_products_raw()
        
        if not products_data:
            # Fallback to mock data
            products_data = [
                {"name": "Large Eggs", "price": 3.99, "item_id": "eggs_001"},
                {"name": "Whole Milk", "price": 4.29, "item_id": "milk_001"},
                {"name": "White Bread", "price": 2.49, "item_id": "bread_001"},
                {"name": "Chicken Breast", "price": 6.99, "item_id": "chicken_001"},
                {"name": "Organic Tomatoes", "price": 2.99, "item_id": "tomatoes_001"},
                {"name": "Organic Spinach", "price": 3.99, "item_id": "spinach_001"},
                {"name": "Organic Onions", "price": 1.99, "item_id": "onions_001"},
                {"name": "Organic Carrots", "price": 2.49, "item_id": "carrots_001"}
            ]
        
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
            product_mapping = get_product_mapping(products_data)
            
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
                
                # Find product by name
                product_data = find_product_by_name(product_name, product_mapping)
                
                if product_data:
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
def calculate_calories(items: Union[List[str], List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate total calories for a list of items.
    
    Args:
        items: Can be:
            - List[str]: Product names
            - List[Dict]: Items with 'name' and optional 'quantity' keys
            
    Returns:
        Dict[str, Any]: Standardized response with calorie calculation
    """
    try:
        # Input validation to prevent infinite loops
        if not items:
            return {
                'success': False,
                'data': None,
                'message': 'No items provided for calorie calculation'
            }
        
        if not isinstance(items, (list, tuple)):
            return {
                'success': False,
                'data': None,
                'message': f'Items must be a list, got {type(items).__name__}'
            }
        # Get product data
        products_data = get_all_products_raw()
        
        if not products_data:
            return {
                'success': False,
                'data': None,
                'message': 'No product data available from database. Please use smart food matching.',
                'requires_smart_matching': True,
                'original_query': items
            }
        product_mapping = get_product_mapping(products_data)
        
        total_calories = 0
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
            
            # Find product by name
            product_data = find_product_by_name(product_name, product_mapping)
            
            if product_data:
                # Try different calorie fields
                calories_per_unit = (
                    product_data.get("calories_per_unit") or 
                    product_data.get("calories") or 
                    0
                )
                calories_per_unit = int(calories_per_unit) if calories_per_unit else 0
                item_calories = calories_per_unit * quantity
                total_calories += item_calories
                
                item_breakdown.append({
                    "product_name": product_name,
                    "matched_name": product_data.get("name", product_name),
                    "calories_per_unit": calories_per_unit,
                    "quantity": quantity,
                    "total_calories": item_calories
                })
            else:
                item_breakdown.append({
                    "product_name": product_name,
                    "matched_name": None,
                    "calories_per_unit": 0,
                    "quantity": quantity,
                    "total_calories": 0,
                    "error": "Product not found"
                })
        
        # Check if any items were not found and trigger smart matching
        unfound_items = [item for item in item_breakdown if item.get("error") == "Product not found"]
        items_found = len([item for item in item_breakdown if item.get("calories_per_unit", 0) > 0])
        
        result = {
            "total_calories": total_calories,
            "item_breakdown": item_breakdown,
            "items_found": items_found,
            "total_items": len(item_breakdown),
            "unfound_items": unfound_items
        }
        
        # If some items weren't found, suggest smart matching
        if unfound_items:
            unfound_names = [item["product_name"] for item in unfound_items]
            result["requires_smart_matching"] = True
            result["unfound_item_names"] = unfound_names
            result["smart_matching_message"] = f"Could not find exact matches for: {', '.join(unfound_names)}. Consider using smart food matching to find similar items in the database."
        
        return {
            'success': True,
            'data': result,
            'message': f'Calculated calories for {len(item_breakdown)} items: {total_calories} calories' + 
                      (f'. {len(unfound_items)} items need smart matching.' if unfound_items else '')
        }
        
    except Exception as e:
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
        
        if not products_data:
            # Fallback to mock data with nutrition info
            products_data = [
                {"name": "Large Eggs", "calories": 70, "protein": 6, "carbs": 1, "fat": 5},
                {"name": "Whole Milk", "calories": 150, "protein": 8, "carbs": 12, "fat": 8},
                {"name": "White Bread", "calories": 80, "protein": 3, "carbs": 15, "fat": 1},
                {"name": "Chicken Breast", "calories": 165, "protein": 31, "carbs": 0, "fat": 4},
                {"name": "Organic Tomatoes", "calories": 18, "protein": 1, "carbs": 4, "fat": 0},
                {"name": "Organic Spinach", "calories": 7, "protein": 1, "carbs": 1, "fat": 0},
                {"name": "Organic Onions", "calories": 40, "protein": 1, "carbs": 9, "fat": 0},
                {"name": "Organic Carrots", "calories": 41, "protein": 1, "carbs": 10, "fat": 0}
            ]
        
        product_mapping = get_product_mapping(products_data)
        
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
            
            # Find product by name
            product_data = find_product_by_name(product_name, product_mapping)
            
            if product_data:
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