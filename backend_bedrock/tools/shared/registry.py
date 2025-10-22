"""
Shared tools registry for backend_bedrock.

This module provides the registry for shared tools that can be used
by multiple agents across different domains.
"""

from .user_profile import (
    fetch_user_profile, update_user_profile
)
from .product_catalog import (
    search_products, check_product_availability, fetch_available_items, simple_test_tool
)
from .calculations import (
    calculate_cost, calculate_calories, calculate_nutrition, calculate_cart_total
)

# Export callable tools for Strands Agent
SHARED_TOOL_FUNCTIONS = [
    # User Profile Tools
    fetch_user_profile,
    update_user_profile,
    fetch_available_items,
    
    # Product Catalog Tools
    search_products,
    check_product_availability,
    simple_test_tool,
    
    # Calculation Tools
    calculate_cost,
    calculate_calories,
    # calculate_nutrition,
    calculate_cart_total
]