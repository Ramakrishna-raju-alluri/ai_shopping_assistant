from strands import tool
from typing import List, Dict, Any


@tool
def calculate_calories(ingredients: List[str]) -> int:
    """Calculate estimated total calories for a list of ingredients"""
    # Placeholder for calorie calculation logic
    return len(ingredients) * 150


@tool
def calculate_cost(items: List[Dict[str, Any]]) -> float:
    """Calculate total cost of a list of grocery items"""
    return sum(item.get("price", 0) for item in items)


@tool
def generate_meal_suggestions(dietary_preferences: str, budget: float, available_ingredients: List[str]) -> List[Dict[str, Any]]:
    """Generate meal suggestions based on preferences, budget, and available ingredients"""
    # Placeholder implementation
    suggestions = [
        {
            "name": "Healthy Breakfast Bowl",
            "ingredients": ["oats", "banana", "almonds"],
            "estimated_calories": 350,
            "estimated_cost": 2.50,
            "prep_time": "5 minutes"
        },
        {
            "name": "Grilled Chicken Salad",
            "ingredients": ["chicken breast", "lettuce", "tomato", "cucumber"],
            "estimated_calories": 450,
            "estimated_cost": 4.20,
            "prep_time": "15 minutes"
        },
        {
            "name": "Vegetable Stir Fry",
            "ingredients": ["broccoli", "carrots", "bell peppers", "soy sauce"],
            "estimated_calories": 300,
            "estimated_cost": 3.80,
            "prep_time": "10 minutes"
        }
    ]
    
    # Filter based on available ingredients
    filtered_suggestions = []
    for suggestion in suggestions:
        if any(ingredient in available_ingredients for ingredient in suggestion["ingredients"]):
            if suggestion["estimated_cost"] <= budget:
                filtered_suggestions.append(suggestion)
    
    return filtered_suggestions[:3]  # Return top 3 suggestions
