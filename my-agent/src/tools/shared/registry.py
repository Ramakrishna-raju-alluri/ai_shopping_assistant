"""
Shared tools registry for backend_bedrock.

This module provides the registry for shared tools that can be used
by multiple agents across different domains.
"""

from typing import Dict, Any, List
from .user_profile import (
    fetch_user_profile, update_user_profile, get_user_preferences, 
    get_user_budget_info, create_user_profile,
    # Legacy compatibility functions
    fetch_user_profile_json, get_user_profile_raw
)
from .product_catalog import (
    fetch_all_products, get_products_by_category, search_products,
    find_products_by_names, check_product_availability,
    # Legacy compatibility functions
    fetch_all_products_legacy, search_products_legacy, get_all_products_raw
)
from .calculations import (
    calculate_cost, calculate_calories, calculate_nutrition, calculate_cart_total,
    # Legacy compatibility functions
    calculate_cost_json, calculate_calories_json, calculate_cart_total_legacy,
    calculate_cart_total_session
)
from .smart_food_matcher import (
    get_full_product_table_for_matching, find_best_food_match
)

# Tool metadata for documentation and agent registration
SHARED_TOOLS = [
    # User Profile Tools
    {
        "name": "fetch_user_profile",
        "description": "Fetch user profile data including dietary preferences and budget information",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "update_user_profile",
        "description": "Update user profile data in the database",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "profile_data": {"type": "object", "description": "Profile data to update"}
            },
            "required": ["user_id", "profile_data"]
        }
    },
    {
        "name": "get_user_preferences",
        "description": "Get user dietary preferences and restrictions",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_user_budget_info",
        "description": "Get user budget information and shopping preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "create_user_profile",
        "description": "Create a new user profile with initial data",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "profile_data": {"type": "object", "description": "Initial profile data"}
            },
            "required": ["user_id", "profile_data"]
        }
    },
    
    # Product Catalog Tools
    {
        "name": "fetch_all_products",
        "description": "Fetch all products from catalog with optional category filtering",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum number of products to return", "default": 100},
                "category": {"type": "string", "description": "Optional category filter"}
            }
        }
    },
    {
        "name": "get_products_by_category",
        "description": "Get all products in a specific category",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Product category"},
                "limit": {"type": "integer", "description": "Maximum results", "default": 50}
            },
            "required": ["category"]
        }
    },
    {
        "name": "search_products",
        "description": "Search products by name, description, or tags",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "limit": {"type": "integer", "description": "Maximum results to return", "default": 20}
            },
            "required": ["query"]
        }
    },
    {
        "name": "find_products_by_names",
        "description": "Find products by a list of names using fuzzy matching",
        "parameters": {
            "type": "object",
            "properties": {
                "product_names": {"type": "array", "items": {"type": "string"}, "description": "List of product names to search for"}
            },
            "required": ["product_names"]
        }
    },
    {
        "name": "check_product_availability",
        "description": "Check product availability and stock status with fuzzy name matching",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "Product name to search for"}
            },
            "required": ["product_name"]
        }
    },
    
    # Calculation Tools
    {
        "name": "calculate_cost",
        "description": "Calculate total cost for a list of items (supports multiple input formats)",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "description": "Items to calculate cost for - can be list of product names, list of item objects, or item_id->quantity mapping",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "array", "items": {"type": "object"}},
                        {"type": "object"}
                    ]
                }
            },
            "required": ["items"]
        }
    },
    {
        "name": "calculate_calories",
        "description": "Calculate total calories for a list of items with product matching",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "description": "Items to calculate calories for - can be list of product names or list of item objects",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "array", "items": {"type": "object"}}
                    ]
                }
            },
            "required": ["items"]
        }
    },
    {
        "name": "calculate_nutrition",
        "description": "Calculate comprehensive nutritional values (calories, protein, carbs, fat) for a list of items",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "description": "Items to calculate nutrition for - can be list of product names or list of item objects",
                    "oneOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "array", "items": {"type": "object"}}
                    ]
                }
            },
            "required": ["items"]
        }
    },
    {
        "name": "calculate_cart_total",
        "description": "Calculate total cost and item count for cart session items",
        "parameters": {
            "type": "object",
            "properties": {
                "session_items": {"type": "array", "items": {"type": "object"}, "description": "List of cart items with price and quantity"}
            },
            "required": ["session_items"]
        }
    },
    
    # Smart Food Matching Tools
    {
        "name": "get_full_product_table_for_matching",
        "description": "Get complete product table data for LLM-based intelligent food matching when exact matches fail",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "find_best_food_match",
        "description": "Use LLM reasoning to find the best matching food item from product table data",
        "parameters": {
            "type": "object",
            "properties": {
                "food_query": {"type": "string", "description": "The food item to find matches for"},
                "product_table_data": {"type": "array", "items": {"type": "object"}, "description": "Complete product table data"}
            },
            "required": ["food_query", "product_table_data"]
        }
    }
]


def execute_shared_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a shared tool by name with given parameters.
    
    Args:
        tool_name (str): Name of the tool to execute
        parameters (Dict[str, Any]): Tool parameters
        
    Returns:
        Dict[str, Any]: Tool execution result
    """
    tool_functions = {
        # User Profile Tools
        "fetch_user_profile": fetch_user_profile,
        "update_user_profile": update_user_profile,
        "get_user_preferences": get_user_preferences,
        "get_user_budget_info": get_user_budget_info,
        "create_user_profile": create_user_profile,
        
        # Product Catalog Tools
        "fetch_all_products": fetch_all_products,
        "get_products_by_category": get_products_by_category,
        "search_products": search_products,
        "find_products_by_names": find_products_by_names,
        "check_product_availability": check_product_availability,
        
        # Calculation Tools
        "calculate_cost": calculate_cost,
        "calculate_calories": calculate_calories,
        "calculate_nutrition": calculate_nutrition,
        "calculate_cart_total": calculate_cart_total,
        
        # Smart Food Matching Tools
        "get_full_product_table_for_matching": get_full_product_table_for_matching,
        "find_best_food_match": find_best_food_match
    }
    
    if tool_name not in tool_functions:
        return {
            "success": False,
            "data": None,
            "message": f"Unknown shared tool: {tool_name}"
        }
    
    try:
        return tool_functions[tool_name](**parameters)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"Shared tool execution failed: {str(e)}"
        }


# Export callable tools for Strands Agent
SHARED_TOOL_FUNCTIONS = [
    # User Profile Tools
    fetch_user_profile,
    update_user_profile,
    get_user_preferences,
    get_user_budget_info,
    create_user_profile,
    
    # Product Catalog Tools
    fetch_all_products,
    get_products_by_category,
    search_products,
    find_products_by_names,
    check_product_availability,
    
    # Calculation Tools
    calculate_cost,
    calculate_calories,
    calculate_nutrition,
    calculate_cart_total,
    
    # Smart Food Matching Tools
    get_full_product_table_for_matching,
    find_best_food_match
]


# Legacy compatibility functions for existing code
LEGACY_TOOL_FUNCTIONS = {
    # User Profile Legacy
    "fetch_user_profile_json": fetch_user_profile_json,
    "get_user_profile_raw": get_user_profile_raw,
    
    # Product Catalog Legacy
    "fetch_all_products_legacy": fetch_all_products_legacy,
    "search_products_legacy": search_products_legacy,
    "get_all_products_raw": get_all_products_raw,
    
    # Calculation Legacy
    "calculate_cost_json": calculate_cost_json,
    "calculate_calories_json": calculate_calories_json,
    "calculate_cart_total_legacy": calculate_cart_total_legacy,
    "calculate_cart_total_session": calculate_cart_total_session
}


def get_legacy_tool_function(function_name: str):
    """
    Get a legacy tool function by name for backward compatibility.
    
    Args:
        function_name (str): Name of the legacy function
        
    Returns:
        Callable or None: The legacy function if found, None otherwise
    """
    return LEGACY_TOOL_FUNCTIONS.get(function_name)


# Tool categories for organized access
TOOL_CATEGORIES = {
    "user_profile": [
        fetch_user_profile,
        update_user_profile,
        get_user_preferences,
        get_user_budget_info,
        create_user_profile
    ],
    "product_catalog": [
        fetch_all_products,
        get_products_by_category,
        search_products,
        find_products_by_names,
        check_product_availability
    ],
    "calculations": [
        calculate_cost,
        calculate_calories,
        calculate_nutrition,
        calculate_cart_total
    ],
    "smart_matching": [
        get_full_product_table_for_matching,
        find_best_food_match
    ]
}


def get_tools_by_category(category: str) -> List:
    """
    Get all tools in a specific category.
    
    Args:
        category (str): Tool category ('user_profile', 'product_catalog', 'calculations')
        
    Returns:
        List: List of tool functions in the category
    """
    return TOOL_CATEGORIES.get(category, [])