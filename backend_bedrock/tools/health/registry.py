"""
Health tools registry for backend_bedrock.

This module provides the registry for health tracking tools including
calorie tracking and goal management functionality.
"""

from typing import Dict, Any, List
from .calorie_tracking import (
    log_daily_calories, get_calorie_history, calculate_calorie_deficit,
    get_day_plan, set_daily_calorie_target,
    # Legacy compatibility functions
    calories_remaining_legacy
)
from .goal_management import (
    set_health_goals, track_goal_progress, update_goal_status,
    get_goal_recommendations, get_user_goals
)

# Tool metadata for documentation and agent registration
HEALTH_TOOLS = [
    # Calorie Tracking Tools
    {
        "name": "log_daily_calories",
        "description": "Log daily calorie intake with optional meal type",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "calories": {"type": "integer", "description": "Calories to log"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "meal_type": {"type": "string", "description": "Type of meal (breakfast, lunch, dinner, snack) - optional"}
            },
            "required": ["user_id", "calories", "date"]
        }
    },
    {
        "name": "get_calorie_history",
        "description": "Get calorie tracking history for a specified date range",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "date_range": {"type": "integer", "description": "Number of days to retrieve", "default": 7}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "calculate_calorie_deficit",
        "description": "Calculate calorie deficit or surplus for a specific day",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "daily_target": {"type": "integer", "description": "Override target; uses stored if None"}
            },
            "required": ["user_id", "date"]
        }
    },
    {
        "name": "set_daily_calorie_target",
        "description": "Set daily calorie target for a specific date",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                "target": {"type": "integer", "description": "Daily calorie goal"}
            },
            "required": ["user_id", "date", "target"]
        }
    },
    {
        "name": "get_day_plan",
        "description": "Get nutrition plan for a specific day",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
            },
            "required": ["user_id", "date"]
        }
    },
    
    # Goal Management Tools
    {
        "name": "set_health_goals",
        "description": "Set user health goals for various metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "goals": {
                    "type": "object",
                    "description": "Health goals to set",
                    "properties": {
                        "daily_calories": {"type": "integer", "description": "Daily calorie target"},
                        "weekly_exercise": {"type": "integer", "description": "Weekly exercise sessions"},
                        "weight_target": {"type": "number", "description": "Target weight"},
                        "water_intake": {"type": "integer", "description": "Daily water glasses"},
                        "sleep_hours": {"type": "number", "description": "Daily sleep hours"},
                        "steps_daily": {"type": "integer", "description": "Daily step target"}
                    }
                }
            },
            "required": ["user_id", "goals"]
        }
    },
    {
        "name": "track_goal_progress",
        "description": "Track progress toward health goals",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "goal_type": {"type": "string", "description": "Specific goal type to track (optional)"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "update_goal_status",
        "description": "Update goal status and add notes",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "goal_id": {"type": "string", "description": "Goal identifier"},
                "status": {"type": "string", "description": "New status (active, paused, completed, cancelled)"},
                "notes": {"type": "string", "description": "Optional notes about the status change"}
            },
            "required": ["user_id", "goal_id", "status"]
        }
    },
    {
        "name": "get_goal_recommendations",
        "description": "Get personalized goal recommendations based on user progress",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_user_goals",
        "description": "Get all health goals for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"}
            },
            "required": ["user_id"]
        }
    }
]


def execute_health_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a health tool by name with given parameters.
    
    Args:
        tool_name (str): Name of the tool to execute
        parameters (Dict[str, Any]): Tool parameters
        
    Returns:
        Dict[str, Any]: Tool execution result
    """
    tool_functions = {
        # Calorie Tracking Tools
        "log_daily_calories": log_daily_calories,
        "get_calorie_history": get_calorie_history,
        "calculate_calorie_deficit": calculate_calorie_deficit,
        "set_daily_calorie_target": set_daily_calorie_target,
        "get_day_plan": get_day_plan,
        
        # Goal Management Tools
        "set_health_goals": set_health_goals,
        "track_goal_progress": track_goal_progress,
        "update_goal_status": update_goal_status,
        "get_goal_recommendations": get_goal_recommendations,
        "get_user_goals": get_user_goals
    }
    
    if tool_name not in tool_functions:
        return {
            "success": False,
            "data": None,
            "message": f"Unknown health tool: {tool_name}"
        }
    
    try:
        return tool_functions[tool_name](**parameters)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"Health tool execution failed: {str(e)}"
        }


# Export callable tools for Strands Agent
HEALTH_TOOL_FUNCTIONS = [
    # Calorie Tracking Tools
    log_daily_calories,
    get_calorie_history,
    calculate_calorie_deficit,
    set_daily_calorie_target,
    get_day_plan,
    
    # Goal Management Tools
    set_health_goals,
    track_goal_progress,
    update_goal_status,
    get_goal_recommendations,
    get_user_goals
]


# Legacy compatibility functions for existing code
LEGACY_TOOL_FUNCTIONS = {
    "calories_remaining": calories_remaining_legacy
}


def get_legacy_health_tool_function(function_name: str):
    """
    Get a legacy health tool function by name for backward compatibility.
    
    Args:
        function_name (str): Name of the legacy function
        
    Returns:
        Callable or None: The legacy function if found, None otherwise
    """
    return LEGACY_TOOL_FUNCTIONS.get(function_name)


# Tool categories for organized access
TOOL_CATEGORIES = {
    "calorie_tracking": [
        log_daily_calories,
        get_calorie_history,
        calculate_calorie_deficit,
        set_daily_calorie_target,
        get_day_plan
    ],
    "goal_management": [
        set_health_goals,
        track_goal_progress,
        update_goal_status,
        get_goal_recommendations,
        get_user_goals
    ]
}


def get_health_tools_by_category(category: str) -> List:
    """
    Get all health tools in a specific category.
    
    Args:
        category (str): Tool category ('calorie_tracking', 'goal_management')
        
    Returns:
        List: List of tool functions in the category
    """
    return TOOL_CATEGORIES.get(category, [])


# Tool metadata organized by category
TOOLS_BY_CATEGORY = {
    "calorie_tracking": [
        {
            "name": "log_daily_calories",
            "description": "Log calorie intake with meal type tracking",
            "key_features": ["Daily logging", "Meal categorization", "Progress tracking"]
        },
        {
            "name": "get_calorie_history",
            "description": "Historical calorie tracking with averages",
            "key_features": ["Multi-day history", "Average calculations", "Trend analysis"]
        },
        {
            "name": "calculate_calorie_deficit",
            "description": "Deficit/surplus calculation with target comparison",
            "key_features": ["Deficit calculation", "Target comparison", "Progress percentage"]
        },
        {
            "name": "set_daily_calorie_target",
            "description": "Set and manage daily calorie targets",
            "key_features": ["Target setting", "Progress tracking", "Remaining calculations"]
        },
        {
            "name": "get_day_plan",
            "description": "Comprehensive daily nutrition plan",
            "key_features": ["Daily overview", "Meal breakdown", "Target tracking"]
        }
    ],
    "goal_management": [
        {
            "name": "set_health_goals",
            "description": "Set comprehensive health goals",
            "key_features": ["Multiple goal types", "Target setting", "Status tracking"]
        },
        {
            "name": "track_goal_progress",
            "description": "Progress tracking with status analysis",
            "key_features": ["Progress calculation", "Status assessment", "Achievement tracking"]
        },
        {
            "name": "update_goal_status",
            "description": "Goal status management with notes",
            "key_features": ["Status updates", "Note tracking", "History logging"]
        },
        {
            "name": "get_goal_recommendations",
            "description": "Personalized goal recommendations",
            "key_features": ["Smart recommendations", "Priority assessment", "Action suggestions"]
        },
        {
            "name": "get_user_goals",
            "description": "Complete goal overview for users",
            "key_features": ["Goal listing", "Status overview", "Progress summary"]
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
    for tool in HEALTH_TOOLS:
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
HEALTH_TOOLS_SUMMARY = {
    "total_tools": len(HEALTH_TOOL_FUNCTIONS),
    "calorie_tracking": len(TOOL_CATEGORIES["calorie_tracking"]),
    "goal_management": len(TOOL_CATEGORIES["goal_management"]),
    "legacy_functions": len(LEGACY_TOOL_FUNCTIONS),
    "categories": list(TOOL_CATEGORIES.keys())
}