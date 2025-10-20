"""
Grocery tools registry for backend_bedrock.

This module provides the registry for grocery-specific tools including
cart operations and product search functionality.
"""

from typing import Dict, Any, List
from .cart_operations import (
    add_to_cart, remove_from_cart, get_cart_summary, clear_cart, check_budget_status,
    # Legacy compatibility functions
    add_item_to_cart_legacy, get_cart_summary_legacy, remove_item_from_cart_legacy
)
from .product_search import (
    check_availability, find_substitutes, get_pricing_info, 
    search_grocery_products, check_item_availability_by_name,
    # Legacy compatibility functions
    check_product_availability_legacy, find_product_substitutes_legacy, 
    check_item_availability_legacy
)

# Tool metadata for documentation and agent registration
GROCERY_TOOLS = [
    # Cart Operations
    {
        "name": "add_to_cart",
        "description": "Add an item to the shopping cart with budget checking and availability validation",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "product_id": {"type": "string", "description": "Product ID or name to add"},
                "quantity": {"type": "integer", "description": "Quantity to add", "default": 1},
                "session_id": {"type": "string", "description": "Session ID for cart storage (optional)"}
            },
            "required": ["user_id", "product_id"]
        }
    },
    {
        "name": "remove_from_cart",
        "description": "Remove an item from the shopping cart",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "product_id": {"type": "string", "description": "Product ID to remove"},
                "session_id": {"type": "string", "description": "Session ID for cart storage (optional)"}
            },
            "required": ["user_id", "product_id"]
        }
    },
    {
        "name": "get_cart_summary",
        "description": "Get current cart contents, totals, and budget information",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "session_id": {"type": "string", "description": "Session ID for cart retrieval (optional)"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "clear_cart",
        "description": "Clear all items from the shopping cart",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "session_id": {"type": "string", "description": "Session ID for cart storage (optional)"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "check_budget_status",
        "description": "Check if cart is within user's budget and get budget details",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "session_id": {"type": "string", "description": "Session ID for cart retrieval (optional)"}
            },
            "required": ["user_id"]
        }
    },
    
    # Product Search Tools
    {
        "name": "check_availability",
        "description": "Check if a specific product is available and get stock information",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to check"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "find_substitutes",
        "description": "Find substitute products for a given item with personalized recommendations",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Original product ID"},
                "max_price": {"type": "number", "description": "Optional maximum price for substitutes"},
                "user_id": {"type": "string", "description": "User ID for personalized suggestions (optional)"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "get_pricing_info",
        "description": "Get detailed pricing information including promotions for a product",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "search_grocery_products",
        "description": "Enhanced grocery product search with filtering options",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term"},
                "category": {"type": "string", "description": "Filter by category (optional)"},
                "max_price": {"type": "number", "description": "Maximum price filter (optional)"},
                "in_stock_only": {"type": "boolean", "description": "Only return in-stock items", "default": True},
                "limit": {"type": "integer", "description": "Maximum results to return", "default": 20}
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_item_availability_by_name",
        "description": "Check availability of a product by name with fuzzy matching",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "Product name to check"}
            },
            "required": ["item_name"]
        }
    }
]


def execute_grocery_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a grocery tool by name with given parameters.
    
    Args:
        tool_name (str): Name of the tool to execute
        parameters (Dict[str, Any]): Tool parameters
        
    Returns:
        Dict[str, Any]: Tool execution result
    """
    tool_functions = {
        # Cart Operations
        "add_to_cart": add_to_cart,
        "remove_from_cart": remove_from_cart,
        "get_cart_summary": get_cart_summary,
        "clear_cart": clear_cart,
        "check_budget_status": check_budget_status,
        
        # Product Search Tools
        "check_availability": check_availability,
        "find_substitutes": find_substitutes,
        "get_pricing_info": get_pricing_info,
        "search_grocery_products": search_grocery_products,
        "check_item_availability_by_name": check_item_availability_by_name
    }
    
    if tool_name not in tool_functions:
        return {
            "success": False,
            "data": None,
            "message": f"Unknown grocery tool: {tool_name}"
        }
    
    try:
        return tool_functions[tool_name](**parameters)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"Grocery tool execution failed: {str(e)}"
        }


# Export callable tools for Strands Agent
GROCERY_TOOL_FUNCTIONS = [
    # Cart Operations
    add_to_cart,
    remove_from_cart,
    get_cart_summary,
    clear_cart,
    check_budget_status,
    
    # Product Search Tools
    check_availability,
    find_substitutes,
    get_pricing_info,
    search_grocery_products,
    check_item_availability_by_name
]


# Legacy compatibility functions for existing code
LEGACY_TOOL_FUNCTIONS = {
    # Cart Operations Legacy
    "add_item_to_cart": add_item_to_cart_legacy,
    "get_cart_summary_legacy": get_cart_summary_legacy,
    "remove_item_from_cart": remove_item_from_cart_legacy,
    
    # Product Search Legacy
    "check_product_availability": check_product_availability_legacy,
    "find_product_substitutes": find_product_substitutes_legacy,
    "check_item_availability": check_item_availability_legacy
}


def get_legacy_grocery_tool_function(function_name: str):
    """
    Get a legacy grocery tool function by name for backward compatibility.
    
    Args:
        function_name (str): Name of the legacy function
        
    Returns:
        Callable or None: The legacy function if found, None otherwise
    """
    return LEGACY_TOOL_FUNCTIONS.get(function_name)


# Tool categories for organized access
TOOL_CATEGORIES = {
    "cart_operations": [
        add_to_cart,
        remove_from_cart,
        get_cart_summary,
        clear_cart,
        check_budget_status
    ],
    "product_search": [
        check_availability,
        find_substitutes,
        get_pricing_info,
        search_grocery_products,
        check_item_availability_by_name
    ]
}


def get_grocery_tools_by_category(category: str) -> List:
    """
    Get all grocery tools in a specific category.
    
    Args:
        category (str): Tool category ('cart_operations', 'product_search')
        
    Returns:
        List: List of tool functions in the category
    """
    return TOOL_CATEGORIES.get(category, [])


# Tool metadata organized by category
TOOLS_BY_CATEGORY = {
    "cart_operations": [
        {
            "name": "add_to_cart",
            "description": "Add items to cart with budget and availability checking",
            "key_features": ["Budget validation", "Availability checking", "Session management"]
        },
        {
            "name": "remove_from_cart",
            "description": "Remove items from cart with updated totals",
            "key_features": ["Item removal", "Total recalculation", "Session persistence"]
        },
        {
            "name": "get_cart_summary",
            "description": "Get comprehensive cart summary with budget info",
            "key_features": ["Item listing", "Cost totals", "Budget analysis"]
        },
        {
            "name": "clear_cart",
            "description": "Clear all items from cart",
            "key_features": ["Bulk removal", "Session cleanup", "Confirmation"]
        },
        {
            "name": "check_budget_status",
            "description": "Check budget compliance and get financial summary",
            "key_features": ["Budget validation", "Spending analysis", "Recommendations"]
        }
    ],
    "product_search": [
        {
            "name": "check_availability",
            "description": "Check product stock status by ID",
            "key_features": ["Stock checking", "Product details", "Availability status"]
        },
        {
            "name": "find_substitutes",
            "description": "Find substitute products with personalization",
            "key_features": ["Smart matching", "User preferences", "Price filtering"]
        },
        {
            "name": "get_pricing_info",
            "description": "Get detailed pricing including promotions",
            "key_features": ["Regular pricing", "Promotional offers", "Savings calculation"]
        },
        {
            "name": "search_grocery_products",
            "description": "Enhanced search with multiple filters",
            "key_features": ["Category filtering", "Price filtering", "Stock filtering"]
        },
        {
            "name": "check_item_availability_by_name",
            "description": "Check availability by product name with fuzzy matching",
            "key_features": ["Name matching", "Multiple results", "Stock status"]
        }
    ]
}


def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_name (str): Name of the tool
        
    Returns:
        Dict[str, Any]: Tool information including metadata and features
    """
    # Find tool in metadata
    for tool in GROCERY_TOOLS:
        if tool["name"] == tool_name:
            # Find additional info in categorized tools
            for category, tools in TOOLS_BY_CATEGORY.items():
                for tool_info in tools:
                    if tool_info["name"] == tool_name:
                        return {
                            **tool,
                            "category": category,
                            "key_features": tool_info["key_features"]
                        }
            return tool
    
    return {"error": f"Tool '{tool_name}' not found"}


# Summary statistics
GROCERY_TOOLS_SUMMARY = {
    "total_tools": len(GROCERY_TOOL_FUNCTIONS),
    "cart_operations": len(TOOL_CATEGORIES["cart_operations"]),
    "product_search": len(TOOL_CATEGORIES["product_search"]),
    "legacy_functions": len(LEGACY_TOOL_FUNCTIONS),
    "categories": list(TOOL_CATEGORIES.keys())
}