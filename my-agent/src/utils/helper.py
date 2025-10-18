"""
Helper utilities for the agent
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


def extract_user_id(query: str) -> str:
    """Extract user ID from query text"""
    patterns = [
        r"user[_\s]*id[:\s]+([a-zA-Z0-9_-]+)",
        r"I am ([a-zA-Z0-9_-]+)",
        r"my user[_\s]*id is ([a-zA-Z0-9_-]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "default-user"


def extract_date(query: str) -> Optional[str]:
    """Extract date from query text"""
    # Look for YYYY-MM-DD format
    date_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"
    match = re.search(date_pattern, query)
    if match:
        return match.group(1)
    
    # Handle relative dates
    query_lower = query.lower()
    today = datetime.now()
    
    if "today" in query_lower:
        return today.strftime("%Y-%m-%d")
    elif "tomorrow" in query_lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "yesterday" in query_lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    return None


def validate_date_format(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def classify_query_type(query: str) -> str:
    """Classify query into categories"""
    query_lower = query.lower()
    
    # Product/stock related keywords
    product_keywords = [
        "stock", "available", "in stock", "out of stock", "product", 
        "banana", "apple", "milk", "bread", "have", "buy", "price"
    ]
    
    # Nutrition/calorie related keywords
    nutrition_keywords = [
        "calorie", "calories", "meal", "breakfast", "lunch", "dinner",
        "target", "remaining", "log", "track", "nutrition", "diet"
    ]
    
    # Meal planning keywords
    meal_planning_keywords = [
        "suggest", "recommend", "plan", "recipe", "cook", "prepare"
    ]
    
    product_score = sum(1 for keyword in product_keywords if keyword in query_lower)
    nutrition_score = sum(1 for keyword in nutrition_keywords if keyword in query_lower)
    meal_planning_score = sum(1 for keyword in meal_planning_keywords if keyword in query_lower)
    
    if product_score > nutrition_score and product_score > meal_planning_score:
        return "product"
    elif nutrition_score > meal_planning_score:
        return "nutrition"
    elif meal_planning_score > 0:
        return "meal_planning"
    else:
        return "general"


def format_nutrition_response(plan: Dict[str, Any], date: str) -> str:
    """Format nutrition plan data for user display"""
    target = plan.get("target", 0)
    consumed = plan.get("consumed", 0)
    remaining = max(0, target - consumed)
    meals = plan.get("meals", [])
    
    response = f"📊 **Nutrition Summary for {date}**\n\n"
    response += f"🎯 Daily Target: {target} calories\n"
    response += f"🍽️ Consumed: {consumed} calories\n"
    response += f"⚖️ Remaining: {remaining} calories\n\n"
    
    if meals:
        response += "📝 **Meals logged:**\n"
        for i, meal in enumerate(meals, 1):
            name = meal.get("name", f"Meal {i}")
            calories = meal.get("calories", 0)
            response += f"• {name}: {calories} calories\n"
    else:
        response += "No meals logged yet today. 🍽️"
    
    return response


def parse_meal_description(description: str) -> Dict[str, Any]:
    """Parse meal description into structured data"""
    parts = description.lower().split()
    
    # Look for calorie information
    calories = 0
    for i, part in enumerate(parts):
        if part in ["calories", "kcal", "cal"] and i > 0:
            try:
                calories = int(parts[i-1])
                break
            except ValueError:
                pass
    
    # Extract meal name
    name_parts = []
    for part in parts:
        if part in ["calories", "kcal", "cal"]:
            break
        name_parts.append(part)
    
    name = " ".join(name_parts) if name_parts else "meal"
    
    return {
        "name": name,
        "calories": calories,
        "protein": 0,
        "carbs": 0,
        "fat": 0
    }


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    return sanitized.strip()


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()
