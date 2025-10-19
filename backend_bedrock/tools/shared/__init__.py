"""
Shared tools module for backend_bedrock.

This module contains tools that are used by multiple agents across different domains.
"""

from .user_profile import *
from .product_catalog import *
from .calculations import *
from .registry import (
    SHARED_TOOL_FUNCTIONS, 
    SHARED_TOOLS, 
    execute_shared_tool,
    get_legacy_tool_function,
    get_tools_by_category,
    TOOL_CATEGORIES,
    LEGACY_TOOL_FUNCTIONS
)

__all__ = [
    'SHARED_TOOL_FUNCTIONS', 
    'SHARED_TOOLS', 
    'execute_shared_tool',
    'get_legacy_tool_function',
    'get_tools_by_category',
    'TOOL_CATEGORIES',
    'LEGACY_TOOL_FUNCTIONS'
]