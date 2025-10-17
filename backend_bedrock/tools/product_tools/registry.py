from typing import Dict, Any
from .fetch import fetch_all_products, get_products_by_category
from .search import search_products
from .pricing import get_product_price, calculate_cart_total, check_promo_offers
from .availability import check_product_availability
from .substitutes import find_product_substitutes
 
# Tool registry for Bedrock agents
PRODUCT_TOOLS = [
    {
        "name": "fetch_all_products",
        "description": "Fetch products from catalog with optional category filtering",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum number of products to return", "default": 100},
                "category": {"type": "string", "description": "Optional category filter"}
            }
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
        "name": "check_product_availability",
        "description": "Check if a specific product is available and get stock info",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Product ID to check"}
            },
            "required": ["item_id"]
        }
    },
    {
        "name": "get_product_price",
        "description": "Get the current price of a specific product",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Product ID"}
            },
            "required": ["item_id"]
        }
    },
    {
        "name": "find_product_substitutes",
        "description": "Find substitute products for a given item",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Original product ID"},
                "max_price": {"type": "number", "description": "Optional maximum price for substitutes"}
            },
            "required": ["item_id"]
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
        "name": "check_promo_offers",
        "description": "Check for promotional offers on specific products",
        "parameters": {
            "type": "object",
            "properties": {
                "item_ids": {"type": "array", "items": {"type": "string"}, "description": "List of product IDs to check"}
            },
            "required": ["item_ids"]
        }
    },
    {
        "name": "calculate_cart_total",
        "description": "Calculate total cost for a cart of items",
        "parameters": {
            "type": "object",
            "properties": {
                "item_quantities": {"type": "object", "description": "Dict of item_id -> quantity"}
            },
            "required": ["item_quantities"]
        }
    }
]


def execute_catalog_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a catalog tool by name with given parameters.
    
    Args:
        tool_name: Name of the tool to execute
        parameters: Tool parameters
        
    Returns:
        Tool execution result
    """
    tool_functions = {
        "fetch_all_products": fetch_all_products,
        "search_products": search_products,
        "check_product_availability": check_product_availability,
        "get_product_price": get_product_price,
        "find_product_substitutes": find_product_substitutes,
        "get_products_by_category": get_products_by_category,
        "check_promo_offers": check_promo_offers,
        "calculate_cart_total": calculate_cart_total
    }
    
    if tool_name not in tool_functions:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    try:
        return tool_functions[tool_name](**parameters)
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }

# Export callable tools for Strands Agent
PRODUCT_TOOL_FUNCTIONS = [
    fetch_all_products,
    search_products,
    check_product_availability,
    get_product_price,
    find_product_substitutes,
    get_products_by_category,
    calculate_cart_total,
]
