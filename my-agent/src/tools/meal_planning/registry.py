"""
Meal planning tools registry for backend_bedrock.

This module provides the registry for meal planning tools including
recipe management and nutrition analysis functionality.
"""

from typing import Dict, Any, List
from .recipe_management import (
    create_meal_plan, suggest_recipes, get_recipe_details,
    create_shopping_list_from_recipes, save_custom_recipe,
    # Legacy compatibility functions
    create_meal_plan_legacy, suggest_recipes_legacy
)
from .nutrition_analysis import (
    analyze_meal_nutrition, apply_dietary_filters, calculate_daily_nutrition,
    get_nutrition_recommendations,
    # Legacy compatibility functions
    analyze_meal_nutrition_legacy, apply_dietary_filters_legacy
)

# Tool metadata for documentation and agent registration
MEAL_PLANNING_TOOLS = [
    # Recipe Management Tools
    {
        "name": "create_meal_plan",
        "description": "Generate meal plans based on user preferences and dietary requirements",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "preferences": {
                    "type": "object",
                    "description": "Meal planning preferences",
                    "properties": {
                        "days": {"type": "integer", "description": "Number of days to plan", "default": 7},
                        "meals_per_day": {"type": "integer", "description": "Meals per day", "default": 3},
                        "diet": {"type": "string", "description": "Diet type (optional)"},
                        "budget_limit": {"type": "number", "description": "Budget limit (optional)"}
                    }
                }
            },
            "required": ["user_id", "preferences"]
        }
    },
    {
        "name": "suggest_recipes",
        "description": "Suggest recipes based on available ingredients and dietary restrictions",
        "parameters": {
            "type": "object",
            "properties": {
                "ingredients": {"type": "array", "items": {"type": "string"}, "description": "Available ingredients"},
                "dietary_restrictions": {"type": "array", "items": {"type": "string"}, "description": "Dietary restrictions (optional)"}
            },
            "required": ["ingredients"]
        }
    },
    {
        "name": "get_recipe_details",
        "description": "Get detailed information about a specific recipe",
        "parameters": {
            "type": "object",
            "properties": {
                "recipe_id": {"type": "string", "description": "Recipe identifier"}
            },
            "required": ["recipe_id"]
        }
    },
    {
        "name": "create_shopping_list_from_recipes",
        "description": "Create a shopping list from selected recipes",
        "parameters": {
            "type": "object",
            "properties": {
                "recipe_ids": {"type": "array", "items": {"type": "string"}, "description": "List of recipe IDs"},
                "servings_multiplier": {"type": "number", "description": "Multiplier for recipe servings", "default": 1.0}
            },
            "required": ["recipe_ids"]
        }
    },
    {
        "name": "save_custom_recipe",
        "description": "Save a custom recipe created by the user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "recipe_data": {
                    "type": "object",
                    "description": "Recipe information",
                    "properties": {
                        "name": {"type": "string", "description": "Recipe name"},
                        "description": {"type": "string", "description": "Recipe description"},
                        "ingredients": {"type": "array", "description": "Recipe ingredients"},
                        "instructions": {"type": "array", "description": "Cooking instructions"},
                        "prep_time": {"type": "integer", "description": "Preparation time in minutes"},
                        "cook_time": {"type": "integer", "description": "Cooking time in minutes"},
                        "servings": {"type": "integer", "description": "Number of servings"},
                        "difficulty": {"type": "string", "description": "Difficulty level"},
                        "dietary_tags": {"type": "array", "description": "Dietary tags"}
                    }
                }
            },
            "required": ["user_id", "recipe_data"]
        }
    },
    
    # Nutrition Analysis Tools
    {
        "name": "analyze_meal_nutrition",
        "description": "Analyze nutritional content of a meal with macronutrient breakdown",
        "parameters": {
            "type": "object",
            "properties": {
                "meal_items": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of meal items with names and quantities"
                }
            },
            "required": ["meal_items"]
        }
    },
    {
        "name": "apply_dietary_filters",
        "description": "Filter items based on dietary restrictions and allergies",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "object"}, "description": "List of food items"},
                "restrictions": {"type": "array", "items": {"type": "string"}, "description": "List of dietary restrictions"}
            },
            "required": ["items", "restrictions"]
        }
    },
    {
        "name": "calculate_daily_nutrition",
        "description": "Calculate daily nutritional totals from multiple meals",
        "parameters": {
            "type": "object",
            "properties": {
                "meals": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of meals with their items"
                }
            },
            "required": ["meals"]
        }
    },
    {
        "name": "get_nutrition_recommendations",
        "description": "Get personalized nutrition recommendations based on user profile",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "current_nutrition": {"type": "object", "description": "Current nutritional intake"}
            },
            "required": ["user_id", "current_nutrition"]
        }
    }
]


def execute_meal_planning_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a meal planning tool by name with given parameters.
    
    Args:
        tool_name (str): Name of the tool to execute
        parameters (Dict[str, Any]): Tool parameters
        
    Returns:
        Dict[str, Any]: Tool execution result
    """
    tool_functions = {
        # Recipe Management Tools
        "create_meal_plan": create_meal_plan,
        "suggest_recipes": suggest_recipes,
        "get_recipe_details": get_recipe_details,
        "create_shopping_list_from_recipes": create_shopping_list_from_recipes,
        "save_custom_recipe": save_custom_recipe,
        
        # Nutrition Analysis Tools
        "analyze_meal_nutrition": analyze_meal_nutrition,
        "apply_dietary_filters": apply_dietary_filters,
        "calculate_daily_nutrition": calculate_daily_nutrition,
        "get_nutrition_recommendations": get_nutrition_recommendations
    }
    
    if tool_name not in tool_functions:
        return {
            "success": False,
            "data": None,
            "message": f"Unknown meal planning tool: {tool_name}"
        }
    
    try:
        return tool_functions[tool_name](**parameters)
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"Meal planning tool execution failed: {str(e)}"
        }


# Export callable tools for Strands Agent
MEAL_PLANNING_TOOL_FUNCTIONS = [
    # Recipe Management Tools
    create_meal_plan,
    suggest_recipes,
    get_recipe_details,
    create_shopping_list_from_recipes,
    save_custom_recipe,
    
    # Nutrition Analysis Tools
    analyze_meal_nutrition,
    apply_dietary_filters,
    calculate_daily_nutrition,
    get_nutrition_recommendations
]


# Legacy compatibility functions for existing code
LEGACY_TOOL_FUNCTIONS = {
    # Recipe Management Legacy
    "create_meal_plan_legacy": create_meal_plan_legacy,
    "suggest_recipes_legacy": suggest_recipes_legacy,
    
    # Nutrition Analysis Legacy
    "analyze_meal_nutrition_legacy": analyze_meal_nutrition_legacy,
    "apply_dietary_filters_legacy": apply_dietary_filters_legacy
}


def get_legacy_meal_planning_tool_function(function_name: str):
    """
    Get a legacy meal planning tool function by name for backward compatibility.
    
    Args:
        function_name (str): Name of the legacy function
        
    Returns:
        Callable or None: The legacy function if found, None otherwise
    """
    return LEGACY_TOOL_FUNCTIONS.get(function_name)


# Tool categories for organized access
TOOL_CATEGORIES = {
    "recipe_management": [
        create_meal_plan,
        suggest_recipes,
        get_recipe_details,
        create_shopping_list_from_recipes,
        save_custom_recipe
    ],
    "nutrition_analysis": [
        analyze_meal_nutrition,
        apply_dietary_filters,
        calculate_daily_nutrition,
        get_nutrition_recommendations
    ]
}


def get_meal_planning_tools_by_category(category: str) -> List:
    """
    Get all meal planning tools in a specific category.
    
    Args:
        category (str): Tool category ('recipe_management', 'nutrition_analysis')
        
    Returns:
        List: List of tool functions in the category
    """
    return TOOL_CATEGORIES.get(category, [])


# Tool metadata organized by category
TOOLS_BY_CATEGORY = {
    "recipe_management": [
        {
            "name": "create_meal_plan",
            "description": "Generate comprehensive meal plans with budget and dietary considerations",
            "key_features": ["Multi-day planning", "Budget integration", "Dietary preferences"]
        },
        {
            "name": "suggest_recipes",
            "description": "Smart recipe suggestions based on available ingredients",
            "key_features": ["Ingredient matching", "Dietary filtering", "Difficulty levels"]
        },
        {
            "name": "get_recipe_details",
            "description": "Detailed recipe information with nutrition and cost estimates",
            "key_features": ["Complete instructions", "Nutrition facts", "Cost analysis"]
        },
        {
            "name": "create_shopping_list_from_recipes",
            "description": "Generate shopping lists from selected recipes",
            "key_features": ["Ingredient consolidation", "Quantity scaling", "Cost estimation"]
        },
        {
            "name": "save_custom_recipe",
            "description": "Save and analyze user-created recipes",
            "key_features": ["Custom recipe storage", "Automatic nutrition calculation", "Cost analysis"]
        }
    ],
    "nutrition_analysis": [
        {
            "name": "analyze_meal_nutrition",
            "description": "Comprehensive nutritional analysis with recommendations",
            "key_features": ["Macro breakdown", "Balance analysis", "Health recommendations"]
        },
        {
            "name": "apply_dietary_filters",
            "description": "Filter foods based on dietary restrictions and allergies",
            "key_features": ["Multiple restrictions", "Allergy checking", "Detailed filtering"]
        },
        {
            "name": "calculate_daily_nutrition",
            "description": "Daily nutrition totals from multiple meals",
            "key_features": ["Multi-meal analysis", "Daily targets", "Goal tracking"]
        },
        {
            "name": "get_nutrition_recommendations",
            "description": "Personalized nutrition recommendations",
            "key_features": ["User-specific advice", "Target tracking", "Improvement suggestions"]
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
    for tool in MEAL_PLANNING_TOOLS:
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
MEAL_PLANNING_TOOLS_SUMMARY = {
    "total_tools": len(MEAL_PLANNING_TOOL_FUNCTIONS),
    "recipe_management": len(TOOL_CATEGORIES["recipe_management"]),
    "nutrition_analysis": len(TOOL_CATEGORIES["nutrition_analysis"]),
    "legacy_functions": len(LEGACY_TOOL_FUNCTIONS),
    "categories": list(TOOL_CATEGORIES.keys())
}