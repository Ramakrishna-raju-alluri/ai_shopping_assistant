"""
Main tools module for backend_bedrock.

This module provides consolidated access to all tool categories including
shared tools, grocery tools, meal planning tools, and health tools.
"""

from .shared import (
    SHARED_TOOL_FUNCTIONS, SHARED_TOOLS, execute_shared_tool,
    get_legacy_tool_function, get_tools_by_category as get_shared_tools_by_category,
    TOOL_CATEGORIES as SHARED_CATEGORIES
)
from .grocery import (
    GROCERY_TOOL_FUNCTIONS, GROCERY_TOOLS, execute_grocery_tool,
    get_legacy_grocery_tool_function, get_grocery_tools_by_category,
    TOOL_CATEGORIES as GROCERY_CATEGORIES
)
from .meal_planning import (
    MEAL_PLANNING_TOOL_FUNCTIONS, MEAL_PLANNING_TOOLS, execute_meal_planning_tool,
    get_legacy_meal_planning_tool_function, get_meal_planning_tools_by_category,
    TOOL_CATEGORIES as MEAL_PLANNING_CATEGORIES
)
from .health import (
    HEALTH_TOOL_FUNCTIONS, HEALTH_TOOLS, execute_health_tool,
    get_legacy_health_tool_function, get_health_tools_by_category,
    TOOL_CATEGORIES as HEALTH_CATEGORIES
)

# Consolidated tool functions for easy agent integration
ALL_TOOL_FUNCTIONS = (
    SHARED_TOOL_FUNCTIONS + 
    GROCERY_TOOL_FUNCTIONS + 
    MEAL_PLANNING_TOOL_FUNCTIONS + 
    HEALTH_TOOL_FUNCTIONS
)

# Consolidated tool metadata
ALL_TOOLS = SHARED_TOOLS + GROCERY_TOOLS + MEAL_PLANNING_TOOLS + HEALTH_TOOLS

# Tool categories mapping
TOOL_CATEGORIES = {
    'shared': SHARED_CATEGORIES,
    'grocery': GROCERY_CATEGORIES,
    'meal_planning': MEAL_PLANNING_CATEGORIES,
    'health': HEALTH_CATEGORIES
}

# Tool execution dispatcher
def execute_tool(domain: str, tool_name: str, parameters: dict):
    """
    Execute a tool from any domain.
    
    Args:
        domain (str): Tool domain ('shared', 'grocery', 'meal_planning', 'health')
        tool_name (str): Name of the tool to execute
        parameters (dict): Tool parameters
        
    Returns:
        dict: Tool execution result
    """
    executors = {
        'shared': execute_shared_tool,
        'grocery': execute_grocery_tool,
        'meal_planning': execute_meal_planning_tool,
        'health': execute_health_tool
    }
    
    if domain not in executors:
        return {
            'success': False,
            'data': None,
            'message': f'Unknown tool domain: {domain}'
        }
    
    return executors[domain](tool_name, parameters)

# Tool discovery functions
def get_all_tools_by_category(domain: str, category: str):
    """Get tools by domain and category."""
    category_getters = {
        'shared': get_shared_tools_by_category,
        'grocery': get_grocery_tools_by_category,
        'meal_planning': get_meal_planning_tools_by_category,
        'health': get_health_tools_by_category
    }
    
    if domain in category_getters:
        return category_getters[domain](category)
    return []

# Legacy tool access
def get_legacy_tool(domain: str, function_name: str):
    """Get legacy tool function from any domain."""
    legacy_getters = {
        'shared': get_legacy_tool_function,
        'grocery': get_legacy_grocery_tool_function,
        'meal_planning': get_legacy_meal_planning_tool_function,
        'health': get_legacy_health_tool_function
    }
    
    if domain in legacy_getters:
        return legacy_getters[domain](function_name)
    return None

# Summary statistics
TOOLS_SUMMARY = {
    'total_tools': len(ALL_TOOL_FUNCTIONS),
    'shared_tools': len(SHARED_TOOL_FUNCTIONS),
    'grocery_tools': len(GROCERY_TOOL_FUNCTIONS),
    'meal_planning_tools': len(MEAL_PLANNING_TOOL_FUNCTIONS),
    'health_tools': len(HEALTH_TOOL_FUNCTIONS),
    'domains': list(TOOL_CATEGORIES.keys()),
    'total_categories': sum(len(cats) for cats in TOOL_CATEGORIES.values())
}

__all__ = [
    'ALL_TOOL_FUNCTIONS',
    'ALL_TOOLS',
    'TOOL_CATEGORIES',
    'execute_tool',
    'get_all_tools_by_category',
    'get_legacy_tool',
    'TOOLS_SUMMARY',
    # Re-export domain-specific items
    'SHARED_TOOL_FUNCTIONS',
    'GROCERY_TOOL_FUNCTIONS', 
    'MEAL_PLANNING_TOOL_FUNCTIONS',
    'HEALTH_TOOL_FUNCTIONS'
]