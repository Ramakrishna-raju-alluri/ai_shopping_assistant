"""
Meal planning tools registry for backend_bedrock.

This module provides the registry for meal planning tools including
recipe management and nutrition analysis functionality.
"""

from .recipe_management import (
    get_recipe_details,
    create_shopping_list_from_recipes, save_custom_recipe
)
from .nutrition_analysis import (
    analyze_meal_nutrition, apply_dietary_filters, calculate_daily_nutrition,
    get_nutrition_recommendations
)

# Export callable tools for Strands Agent
MEAL_PLANNING_TOOL_FUNCTIONS = [
    # Recipe Management Tools
    # suggest_recipes,
    # get_recipe_details,
    # create_shopping_list_from_recipes,
    # save_custom_recipe,
    
    # Nutrition Analysis Tools
    analyze_meal_nutrition,
    apply_dietary_filters,
    calculate_daily_nutrition,
    get_nutrition_recommendations
]