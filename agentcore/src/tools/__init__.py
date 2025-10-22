"""
Main tools module for backend_bedrock.

This module provides consolidated access to all tool categories including
shared tools, grocery tools, meal planning tools, and health tools.
"""

from .shared import SHARED_TOOL_FUNCTIONS
from .grocery import GROCERY_TOOL_FUNCTIONS
from .meal_planning import MEAL_PLANNING_TOOL_FUNCTIONS
from .health import HEALTH_TOOL_FUNCTIONS

# Consolidated tool functions for easy agent integration
ALL_TOOL_FUNCTIONS = (
    SHARED_TOOL_FUNCTIONS + 
    GROCERY_TOOL_FUNCTIONS + 
    MEAL_PLANNING_TOOL_FUNCTIONS + 
    HEALTH_TOOL_FUNCTIONS
)

__all__ = [
    'ALL_TOOL_FUNCTIONS',
    'SHARED_TOOL_FUNCTIONS',
    'GROCERY_TOOL_FUNCTIONS', 
    'MEAL_PLANNING_TOOL_FUNCTIONS',
    'HEALTH_TOOL_FUNCTIONS'
]