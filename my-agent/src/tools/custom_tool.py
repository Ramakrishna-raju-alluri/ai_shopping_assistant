from strands import tool
from typing import Dict, Any, List
from datetime import datetime


@tool
def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")


@tool
def format_nutrition_summary(user_id: str, date: str, plan: Dict[str, Any]) -> str:
    """Format a nutrition summary for display"""
    target = plan.get("target", 0)
    consumed = plan.get("consumed", 0)
    remaining = max(0, target - consumed)
    meals = plan.get("meals", [])
    
    summary = f"Nutrition Summary for {date}:\n"
    summary += f"Daily Target: {target} calories\n"
    summary += f"Consumed: {consumed} calories\n"
    summary += f"Remaining: {remaining} calories\n\n"
    
    if meals:
        summary += "Meals logged:\n"
        for i, meal in enumerate(meals, 1):
            name = meal.get("name", f"Meal {i}")
            calories = meal.get("calories", 0)
            summary += f"- {name}: {calories} calories\n"
    else:
        summary += "No meals logged yet today."
    
    return summary


@tool
def validate_date_format(date_str: str) -> bool:
    """Validate if date string is in YYYY-MM-DD format"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


@tool
def parse_meal_input(meal_description: str) -> Dict[str, Any]:
    """Parse a meal description into structured data"""
    # Simple parsing - can be enhanced
    parts = meal_description.lower().split()
    
    # Look for calorie information
    calories = 0
    for i, part in enumerate(parts):
        if part in ["calories", "kcal", "cal"] and i > 0:
            try:
                calories = int(parts[i-1])
                break
            except ValueError:
                pass
    
    # Extract meal name (everything before calorie info)
    name_parts = []
    for part in parts:
        if part in ["calories", "kcal", "cal"]:
            break
        name_parts.append(part)
    
    name = " ".join(name_parts) if name_parts else "meal"
    
    return {
        "name": name,
        "calories": calories,
        "protein": 0,  # Default values
        "carbs": 0,
        "fat": 0
    }
