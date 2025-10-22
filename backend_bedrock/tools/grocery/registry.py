"""
Grocery tools registry for backend_bedrock.

This module provides the registry for grocery-specific tools including
cart operations and product search functionality.
"""

from .cart_operations import (
    add_to_cart, remove_from_cart, get_cart_summary, clear_cart, check_budget_status
)
from .product_search import (
    find_substitutes, get_pricing_info, search_grocery_products
)

# Export callable tools for Strands Agent
GROCERY_TOOL_FUNCTIONS = [
    # Cart Operations
    add_to_cart,
    remove_from_cart,
    get_cart_summary,
    clear_cart,
    check_budget_status,
    
    # Product Search Tools
    find_substitutes,
    get_pricing_info,
    search_grocery_products
]