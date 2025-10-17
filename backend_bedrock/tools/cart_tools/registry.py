"""
Cart tools registry for easy import and management
"""

from .cart_manager import (
    add_item_to_cart,
    get_cart_summary,
    remove_item_from_cart,
    find_substitutes_for_item,
    check_budget_status,
    check_item_availability,
    suggest_budget_alternatives,
    process_natural_language_request
)

# List of all cart tool functions for Strands Agent
CART_TOOL_FUNCTIONS = [
    add_item_to_cart,
    get_cart_summary,
    remove_item_from_cart,
    find_substitutes_for_item,
    check_budget_status,
    check_item_availability,
    suggest_budget_alternatives,
    process_natural_language_request
]

# Tool metadata for documentation
CART_TOOLS = [
    {
        "name": "add_item_to_cart",
        "description": "Add an item to the shopping cart with quantity",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "Name of the item to add"},
                "quantity": {"type": "integer", "description": "Quantity to add", "default": 1},
                "session_id": {"type": "string", "description": "Session ID for cart storage"}
            },
            "required": ["item_name"]
        }
    },
    {
        "name": "get_cart_summary",
        "description": "Get current cart contents and total cost",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID for cart retrieval"}
            },
            "required": ["session_id"]
        }
    },
    {
        "name": "remove_item_from_cart",
        "description": "Remove an item from the shopping cart",
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "ID of the item to remove"},
                "session_id": {"type": "string", "description": "Session ID for cart storage"}
            },
            "required": ["item_id", "session_id"]
        }
    },
    {
        "name": "find_substitutes_for_item",
        "description": "Find substitute products for unavailable items",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "Name of the unavailable item"},
                "user_id": {"type": "string", "description": "User ID for personalized suggestions"}
            },
            "required": ["item_name", "user_id"]
        }
    },
    {
        "name": "check_budget_status",
        "description": "Check if cart is within user's budget",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID for cart retrieval"},
                "user_id": {"type": "string", "description": "User ID for budget information"}
            },
            "required": ["session_id", "user_id"]
        }
    },
    {
        "name": "check_item_availability",
        "description": "Check availability status of a specific item",
        "parameters": {
            "type": "object",
            "properties": {
                "item_name": {"type": "string", "description": "Name of the item to check availability for"}
            },
            "required": ["item_name"]
        }
    },
    {
        "name": "suggest_budget_alternatives",
        "description": "Suggest lower-cost alternatives to reduce cart total",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session ID for cart retrieval"},
                "user_id": {"type": "string", "description": "User ID for budget information"},
                "target_savings": {"type": "number", "description": "Target amount to save", "default": 10.0}
            },
            "required": ["session_id", "user_id"]
        }
    },
    {
        "name": "process_natural_language_request",
        "description": "Process natural language requests for cart management including batch operations",
        "parameters": {
            "type": "object",
            "properties": {
                "user_request": {"type": "string", "description": "Natural language request from user"},
                "session_id": {"type": "string", "description": "Session ID for cart operations"},
                "user_id": {"type": "string", "description": "User ID for personalization"}
            },
            "required": ["user_request"]
        }
    }
]