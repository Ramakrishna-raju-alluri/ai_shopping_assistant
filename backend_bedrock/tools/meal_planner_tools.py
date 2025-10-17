import json
import sys
from pathlib import Path
from strands import tool
from typing import List, Dict, Any
from decimal import Decimal

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import direct database functions instead of making HTTP calls
try:
    from backend_bedrock.dynamo.queries import get_user_profile, get_all_products
except ImportError:
    from dynamo.queries import get_user_profile, get_all_products

def convert_decimal_to_float(obj):
    """Convert DynamoDB Decimal types to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj

@tool
def fetch_user_profile(user_id: str) -> str:
    """
    Fetches the user's dietary and budget preferences.
    
    Args:
        user_id (str): The unique identifier for the user
        
    Returns:
        str: JSON string containing user preferences including diet, allergies, budget_limit, meal_goal, etc.
    """
    try:
        # Direct database call instead of HTTP request
        user_profile = get_user_profile(user_id)
        if not user_profile:
            return json.dumps({"error": "User profile not found"})
        
        # Return complete profile data matching the /user-preferences endpoint
        profile_data = {
            "user_id": user_id,
            "diet": user_profile.get("diet"),
            "allergies": user_profile.get("allergies", []),
            "restrictions": user_profile.get("restrictions", []),
            "preferred_cuisines": user_profile.get("preferred_cuisines", []),
            "disliked_cuisines": user_profile.get("disliked_cuisines", []),
            "cooking_skill": user_profile.get("cooking_skill"),
            "cooking_time_preference": user_profile.get("cooking_time_preference"),
            "kitchen_equipment": user_profile.get("kitchen_equipment", []),
            "budget_limit": float(user_profile.get("budget_limit", 0)) if user_profile.get("budget_limit") else 0,
            "meal_budget": float(user_profile.get("meal_budget", 0)) if user_profile.get("meal_budget") else None,
            "shopping_frequency": user_profile.get("shopping_frequency"),
            "meal_goal": user_profile.get("meal_goal"),
            "profile_setup_complete": user_profile.get("profile_setup_complete", False),
        }
        
        # Convert any remaining Decimal types
        profile_data = convert_decimal_to_float(profile_data)
        return json.dumps(profile_data)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch user profile: {str(e)}"})

@tool
def fetch_available_items(category: str = None, in_stock: bool = True, limit: int = 25) -> str:
    """
    Fetches available grocery items from the product catalog.
    
    Args:
        category (str, optional): Filter by product category (e.g., 'fruits', 'vegetables'). Defaults to None.
        in_stock (bool, optional): Filter by stock status. Defaults to True.
        limit (int, optional): Maximum number of products to return. Defaults to 25.
        
    Returns:
        str: JSON string containing list of available products with essential fields only
    """
    try:
        # Direct database call instead of HTTP request
        products = get_all_products()
        
        # Apply filters and limit
        filtered_products = []
        for product in products:
            # Filter by stock status
            if in_stock and not product.get("in_stock", True):
                continue
            
            # Filter by category if specified
            if category and product.get("category", "").lower() != category.lower():
                continue
            
            # Only include essential fields for meal planning
            essential_product = {
                "name": product.get("name"),
                "price": float(product.get("price", 0)) if product.get("price") else 0,
                "calories": int(product.get("calories", 0)) if product.get("calories") else 0,
                "category": product.get("category"),
                "tags": product.get("tags", []),
                "in_stock": product.get("in_stock", True),
            }
            
            # Convert any Decimal types
            essential_product = convert_decimal_to_float(essential_product)
            filtered_products.append(essential_product)
            
            # Apply limit
            if len(filtered_products) >= limit:
                break
        
        result = {
            "products": filtered_products,
            "count": len(filtered_products),
            "limited_to": limit
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch products: {str(e)}", "products": []})

@tool
def calculate_calories(product_names: List[str]) -> str:
    """
    Calculates total calories for a list of product names using actual product data.
    
    Args:
        product_names (List[str]): List of product names to calculate calories for
        
    Returns:
        str: JSON string with total calories and per-product breakdown
    """
    try:
        # Direct database call instead of HTTP request
        products_data = get_all_products()
        
        # Create a mapping of product names to calories
        product_calories = {}
        for product in products_data:
            name = product.get("name", "").lower()
            calories = int(product.get("calories", 0)) if product.get("calories") else 0
            product_calories[name] = calories
        
        # Calculate calories for requested products
        total_calories = 0
        product_breakdown = []
        
        for product_name in product_names:
            name_lower = product_name.lower()
            # Try exact match first, then partial match
            calories = 0
            for prod_name, prod_calories in product_calories.items():
                if name_lower == prod_name or name_lower in prod_name:
                    calories = prod_calories
                    break
            
            total_calories += calories
            product_breakdown.append({
                "product_name": product_name,
                "calories": calories
            })
        
        result = {
            "total_calories": total_calories,
            "product_breakdown": product_breakdown,
            "products_found": len([p for p in product_breakdown if p["calories"] > 0])
        }
        
        # Convert any Decimal types
        result = convert_decimal_to_float(result)
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to calculate calories: {str(e)}", "total_calories": 0})

@tool
def calculate_cost(product_names: List[str]) -> str:
    """
    Calculates the total cost of a list of grocery items by product names.
    
    Args:
        product_names (List[str]): List of product names to calculate cost for
        
    Returns:
        str: JSON string with total cost and per-product breakdown
    """
    try:
        # Direct database call instead of HTTP request
        products_data = get_all_products()
        
        # Create a mapping of product names to prices
        product_prices = {}
        for product in products_data:
            name = product.get("name", "").lower()
            price = float(product.get("price", 0)) if product.get("price") else 0.0
            product_prices[name] = price
        
        # Calculate cost for requested products
        total_cost = 0.0
        product_breakdown = []
        
        for product_name in product_names:
            name_lower = product_name.lower()
            # Try exact match first, then partial match
            price = 0.0
            for prod_name, prod_price in product_prices.items():
                if name_lower == prod_name or name_lower in prod_name:
                    price = prod_price
                    break
            
            total_cost += price
            product_breakdown.append({
                "product_name": product_name,
                "price": price
            })
        
        result = {
            "total_cost": round(total_cost, 2),
            "product_breakdown": product_breakdown,
            "products_found": len([p for p in product_breakdown if p["price"] > 0])
        }
        
        # Convert any Decimal types
        result = convert_decimal_to_float(result)
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to calculate cost: {str(e)}", "total_cost": 0.0})