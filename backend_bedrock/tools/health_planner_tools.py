import sys
from pathlib import Path
from typing import Dict, Any, List
from strands import tool

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb, NUTRITION_TABLE
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from dynamo.client import dynamodb, NUTRITION_TABLE
    except ImportError:
        import boto3
        dynamodb = boto3.resource("dynamodb")
        NUTRITION_TABLE = "nutrition_calendar"


def _table():
    return dynamodb.Table(NUTRITION_TABLE)


@tool
def upsert_day_plan(user_id: str, date: str, meals: List[Dict[str, Any]] = None, target: int = None) -> Dict[str, Any]:
    """
    Create or update a day's nutrition plan with meals and calorie target.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        meals (List[Dict], optional): Meal objects with name, calories, protein, carbs, fat
        target (int, optional): Daily calorie goal
    
    Returns:
        Dict[str, Any]: Day plan with target, consumed calories, and meals
    """
    meals = meals or []
    consumed = sum(int(m.get("calories", 0)) for m in meals)
    existing = get_day_plan(user_id, date)
    item = {
        "user_id": user_id,
        "date": date,
        "target": int(target) if target is not None else existing.get("target", 0),
        "consumed": consumed,
        "meals": meals,
    }
    _table().put_item(Item=item)
    return item


@tool
def get_day_plan(user_id: str, date: str) -> Dict[str, Any]:
    """
    Retrieve nutrition plan for a specific day.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
    
    Returns:
        Dict[str, Any]: Day plan with target, consumed calories, and meals
    """
    resp = _table().get_item(Key={"user_id": user_id, "date": date})
    return resp.get("Item", {"user_id": user_id, "date": date, "target": 0, "consumed": 0, "meals": []})


@tool
def append_meal(user_id: str, date: str, meal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a meal to existing day's nutrition plan.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        meal (Dict[str, Any]): Meal with name, calories, protein, carbs, fat
    
    Returns:
        Dict[str, Any]: Updated day plan with new meal and recalculated totals
    """
    plan = get_day_plan(user_id, date)
    meals = list(plan.get("meals", [])) + [meal]
    consumed = sum(int(m.get("calories", 0)) for m in meals)
    item = {
        "user_id": user_id,
        "date": date,
        "target": int(plan.get("target", 0)),
        "consumed": consumed,
        "meals": meals,
    }
    _table().put_item(Item=item)
    return item


@tool
def set_daily_target(user_id: str, date: str, target: int) -> Dict[str, Any]:
    """
    Set daily calorie target for a date.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        target (int): Daily calorie goal
    
    Returns:
        Dict[str, Any]: Updated day plan with new target
    """
    plan = get_day_plan(user_id, date)
    meals = plan.get("meals", [])
    consumed = sum(int(m.get("calories", 0)) for m in meals)
    item = {
        "user_id": user_id,
        "date": date,
        "target": int(target),
        "consumed": consumed,
        "meals": meals,
    }
    _table().put_item(Item=item)
    return item

@tool
def calories_remaining(user_id: str, date: str, daily_target: int = None) -> int:
    """
    Calculate remaining calories for the day.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        daily_target (int, optional): Override target; uses stored if None
    
    Returns:
        int: Remaining calories (target - consumed), minimum 0
    """
    plan = get_day_plan(user_id, date)
    consumed = int(plan.get("consumed", 0))
    target = int(daily_target) if daily_target is not None else int(plan.get("target", 0))
    return max(0, target - consumed)


@tool
def health_planner(user_id: str, date: str, action: str, payload: dict = None, daily_target: int = None) -> str:
    """
    High-level tool for nutrition calendar operations.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        action (str): "upsert", "append", "get", or "remaining_calories"
        payload (dict, optional): Data for upsert/append operations
        daily_target (int, optional): Required for remaining_calories
    
    Returns:
        str: Operation result or data summary
    """
    if action == "upsert":
        meals = (payload or {}).get("meals", [])
        totals = (payload or {}).get("totals", {})
        item = health_planner_tools.upsert_day_plan(user_id, date, meals, totals)
        return f"Saved plan for {date}: {item}"
    if action == "append":
        meal = (payload or {}).get("meal", {})
        item = health_planner_tools.append_meal(user_id, date, meal)
        return f"Updated plan for {date}: {item}"
    if action == "get":
        item = health_planner_tools.get_day_plan(user_id, date)
        return str(item)
    if action == "remaining_calories":
        if daily_target is None:
            return "daily_target is required"
        remaining = health_planner_tools.calories_remaining(user_id, date, daily_target)
        return str(remaining)
    return "Unknown action"
