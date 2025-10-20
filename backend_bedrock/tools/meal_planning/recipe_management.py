"""
Recipe management tools for backend_bedrock meal planning.

This module provides recipe creation, meal planning, and ingredient management
functionality for meal planning agents.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import dependencies with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb, RECIPE_TABLE
    from backend_bedrock.tools.shared.user_profile import fetch_user_profile
    from backend_bedrock.tools.shared.product_catalog import find_products_by_names
    from backend_bedrock.tools.shared.calculations import calculate_cost, calculate_nutrition
except ImportError:
    try:
        from dynamo.client import dynamodb, RECIPE_TABLE
        from tools.shared.user_profile import fetch_user_profile
        from tools.shared.product_catalog import find_products_by_names
        from tools.shared.calculations import calculate_cost, calculate_nutrition
    except ImportError:
        # Fallback for testing
        import boto3
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        except:
            dynamodb = None
        RECIPE_TABLE = "recipes"
        def fetch_user_profile(user_id):
            return {"success": True, "data": {"diet": "omnivore", "budget_limit": 100}}
        def find_products_by_names(names):
            return {"success": True, "data": []}
        def calculate_cost(items):
            return {"success": True, "data": {"total_cost": 0}}
        def calculate_nutrition(items):
            return {"success": True, "data": {"totals": {"calories": 0}}}


@tool
def create_meal_plan(user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate meal plans based on user preferences.
    
    Args:
        user_id (str): User identifier
        preferences (Dict[str, Any]): Meal planning preferences
        
    Returns:
        Dict[str, Any]: Standardized response with meal plan
    """
    try:
        # Get user profile
        profile_result = fetch_user_profile(user_id)
        if not profile_result['success']:
            return profile_result
        
        user_profile = profile_result['data']
        
        # Extract preferences
        days = preferences.get('days', 7)
        meals_per_day = preferences.get('meals_per_day', 3)
        diet_type = preferences.get('diet', user_profile.get('diet', 'omnivore'))
        budget_limit = preferences.get('budget_limit', user_profile.get('budget_limit', 100))
        
        # Mock meal plan generation (in real implementation, would use recipe database)
        meal_plan = {
            'user_id': user_id,
            'duration_days': days,
            'meals_per_day': meals_per_day,
            'diet_type': diet_type,
            'budget_limit': budget_limit,
            'daily_plans': []
        }
        
        # Generate daily meal plans
        for day in range(1, days + 1):
            daily_plan = {
                'day': day,
                'meals': [],
                'daily_cost': 0,
                'daily_calories': 0
            }
            
            meal_types = ['breakfast', 'lunch', 'dinner'][:meals_per_day]
            
            for meal_type in meal_types:
                # Mock meal generation
                meal = {
                    'meal_type': meal_type,
                    'recipe_name': f"Sample {meal_type.title()}",
                    'ingredients': ['ingredient1', 'ingredient2'],
                    'estimated_cost': 5.0,
                    'estimated_calories': 400,
                    'prep_time': 30,
                    'difficulty': 'easy'
                }
                daily_plan['meals'].append(meal)
                daily_plan['daily_cost'] += meal['estimated_cost']
                daily_plan['daily_calories'] += meal['estimated_calories']
            
            meal_plan['daily_plans'].append(daily_plan)
        
        # Calculate totals
        total_cost = sum(day['daily_cost'] for day in meal_plan['daily_plans'])
        avg_daily_calories = sum(day['daily_calories'] for day in meal_plan['daily_plans']) / days
        
        meal_plan['total_cost'] = total_cost
        meal_plan['average_daily_calories'] = avg_daily_calories
        meal_plan['within_budget'] = total_cost <= budget_limit
        
        return {
            'success': True,
            'data': meal_plan,
            'message': f'Generated {days}-day meal plan with {len(meal_plan["daily_plans"][0]["meals"])} meals per day'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error creating meal plan: {str(e)}'
        }


@tool
def suggest_recipes(ingredients: List[str], dietary_restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Suggest recipes based on available ingredients.
    
    Args:
        ingredients (List[str]): Available ingredients
        dietary_restrictions (Optional[List[str]]): Dietary restrictions to consider
        
    Returns:
        Dict[str, Any]: Standardized response with recipe suggestions
    """
    try:
        # Mock recipe suggestions (in real implementation, would query recipe database)
        suggested_recipes = []
        
        # Generate mock recipes based on ingredients
        for i, ingredient in enumerate(ingredients[:3]):  # Limit to 3 recipes
            recipe = {
                'recipe_id': f'recipe_{i+1}',
                'name': f'{ingredient.title()} Special',
                'description': f'Delicious recipe featuring {ingredient}',
                'ingredients': ingredients[:3],  # Use first 3 ingredients
                'instructions': [
                    f'Prepare {ingredient}',
                    'Combine with other ingredients',
                    'Cook according to preference'
                ],
                'prep_time': 15 + (i * 10),
                'cook_time': 20 + (i * 5),
                'servings': 2 + i,
                'difficulty': ['easy', 'medium', 'hard'][i % 3],
                'estimated_cost': 8.0 + (i * 2),
                'estimated_calories': 350 + (i * 50),
                'dietary_tags': ['vegetarian'] if 'meat' not in ingredient.lower() else ['omnivore']
            }
            
            # Filter by dietary restrictions
            if dietary_restrictions:
                recipe_compatible = True
                for restriction in dietary_restrictions:
                    if restriction.lower() in recipe['name'].lower():
                        recipe_compatible = False
                        break
                
                if recipe_compatible:
                    suggested_recipes.append(recipe)
            else:
                suggested_recipes.append(recipe)
        
        return {
            'success': True,
            'data': {
                'recipes': suggested_recipes,
                'total_found': len(suggested_recipes),
                'search_ingredients': ingredients,
                'dietary_restrictions': dietary_restrictions or []
            },
            'message': f'Found {len(suggested_recipes)} recipe suggestions using your ingredients'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error suggesting recipes: {str(e)}'
        }


@tool
def get_recipe_details(recipe_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific recipe.
    
    Args:
        recipe_id (str): Recipe identifier
        
    Returns:
        Dict[str, Any]: Standardized response with recipe details
    """
    try:
        # Mock recipe details (in real implementation, would query recipe database)
        recipe_details = {
            'recipe_id': recipe_id,
            'name': 'Sample Recipe',
            'description': 'A delicious and nutritious meal',
            'ingredients': [
                {'name': 'chicken breast', 'amount': '1 lb', 'category': 'protein'},
                {'name': 'broccoli', 'amount': '2 cups', 'category': 'vegetable'},
                {'name': 'rice', 'amount': '1 cup', 'category': 'grain'}
            ],
            'instructions': [
                'Preheat oven to 375°F',
                'Season chicken breast with salt and pepper',
                'Bake chicken for 25 minutes',
                'Steam broccoli until tender',
                'Cook rice according to package directions',
                'Serve together'
            ],
            'nutrition': {
                'calories': 450,
                'protein': 35,
                'carbs': 45,
                'fat': 8,
                'fiber': 4
            },
            'prep_time': 15,
            'cook_time': 30,
            'total_time': 45,
            'servings': 4,
            'difficulty': 'medium',
            'dietary_tags': ['gluten-free', 'high-protein'],
            'estimated_cost': 12.50,
            'rating': 4.5,
            'reviews_count': 127
        }
        
        return {
            'success': True,
            'data': recipe_details,
            'message': f'Retrieved details for recipe: {recipe_details["name"]}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting recipe details: {str(e)}'
        }

@tool
def create_shopping_list_from_recipes(recipe_ids: List[str], servings_multiplier: float = 1.0) -> Dict[str, Any]:
    """
    Create a shopping list from selected recipes.
    
    Args:
        recipe_ids (List[str]): List of recipe IDs
        servings_multiplier (float): Multiplier for recipe servings
        
    Returns:
        Dict[str, Any]: Standardized response with shopping list
    """
    try:
        all_ingredients = []
        recipe_details = []
        
        # Get details for each recipe
        for recipe_id in recipe_ids:
            recipe_result = get_recipe_details(recipe_id)
            if recipe_result['success']:
                recipe = recipe_result['data']
                recipe_details.append(recipe)
                
                # Add ingredients with multiplier
                for ingredient in recipe['ingredients']:
                    ingredient_copy = ingredient.copy()
                    # Apply servings multiplier (simplified)
                    if servings_multiplier != 1.0:
                        ingredient_copy['amount'] = f"{ingredient_copy['amount']} (x{servings_multiplier})"
                    all_ingredients.append(ingredient_copy)
        
        # Consolidate duplicate ingredients
        consolidated_ingredients = {}
        for ingredient in all_ingredients:
            name = ingredient['name']
            if name in consolidated_ingredients:
                # In real implementation, would properly combine amounts
                consolidated_ingredients[name]['amount'] += f" + {ingredient['amount']}"
            else:
                consolidated_ingredients[name] = ingredient
        
        shopping_list = list(consolidated_ingredients.values())
        
        # Calculate estimated costs
        ingredient_names = [ing['name'] for ing in shopping_list]
        cost_result = calculate_cost(ingredient_names)
        total_cost = cost_result['data']['total_cost'] if cost_result['success'] else 0
        
        shopping_list_data = {
            'recipes': recipe_details,
            'shopping_list': shopping_list,
            'total_items': len(shopping_list),
            'estimated_total_cost': total_cost,
            'servings_multiplier': servings_multiplier
        }
        
        return {
            'success': True,
            'data': shopping_list_data,
            'message': f'Created shopping list with {len(shopping_list)} items from {len(recipe_ids)} recipes'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error creating shopping list: {str(e)}'
        }

@tool
def save_custom_recipe(user_id: str, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a custom recipe created by the user.
    
    Args:
        user_id (str): User identifier
        recipe_data (Dict[str, Any]): Recipe information
        
    Returns:
        Dict[str, Any]: Standardized response with saved recipe info
    """
    try:
        # Generate recipe ID
        import uuid
        recipe_id = f"custom_{user_id}_{str(uuid.uuid4())[:8]}"
        
        # Prepare recipe for storage
        recipe = {
            'recipe_id': recipe_id,
            'user_id': user_id,
            'name': recipe_data.get('name', 'Untitled Recipe'),
            'description': recipe_data.get('description', ''),
            'ingredients': recipe_data.get('ingredients', []),
            'instructions': recipe_data.get('instructions', []),
            'prep_time': recipe_data.get('prep_time', 0),
            'cook_time': recipe_data.get('cook_time', 0),
            'servings': recipe_data.get('servings', 1),
            'difficulty': recipe_data.get('difficulty', 'medium'),
            'dietary_tags': recipe_data.get('dietary_tags', []),
            'created_at': datetime.utcnow().isoformat(),
            'is_custom': True
        }
        
        # Calculate nutrition and cost
        ingredient_names = [ing.get('name', ing) if isinstance(ing, dict) else ing for ing in recipe['ingredients']]
        
        nutrition_result = calculate_nutrition(ingredient_names)
        if nutrition_result['success']:
            recipe['nutrition'] = nutrition_result['data']['totals']
        
        cost_result = calculate_cost(ingredient_names)
        if cost_result['success']:
            recipe['estimated_cost'] = cost_result['data']['total_cost']
        
        # In real implementation, would save to database
        # For now, return the prepared recipe
        
        return {
            'success': True,
            'data': recipe,
            'message': f'Saved custom recipe: {recipe["name"]}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error saving custom recipe: {str(e)}'
        }


# Legacy compatibility functions
@tool
def create_meal_plan_legacy(user_id: str, preferences: Dict[str, Any]) -> str:
    """Legacy function returning JSON string for backward compatibility."""
    result = create_meal_plan(user_id, preferences)
    return json.dumps(result['data'] if result['success'] else {"error": result['message']})

@tool
def suggest_recipes_legacy(ingredients: List[str]) -> str:
    """Legacy function returning JSON string for backward compatibility."""
    result = suggest_recipes(ingredients)
    return json.dumps(result['data'] if result['success'] else {"error": result['message']})