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
    Create/update a day's plan with schema:
      - target: daily calorie goal (number)
      - consumed: sum of calories from meals (number)
      - meals: list of { name, calories, protein, carbs, fat }
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
    """Fetch the day's nutrition plan for the user."""
    resp = _table().get_item(Key={"user_id": user_id, "date": date})
    return resp.get("Item", {"user_id": user_id, "date": date, "target": 0, "consumed": 0, "meals": []})


@tool
def append_meal(user_id: str, date: str, meal: Dict[str, Any]) -> Dict[str, Any]:
    """Append a single meal to the day's plan; returns the updated item."""
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
    """Set or update the stored daily calorie target for a given date."""
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
    Return remaining calories for the day using stored target when available.
    If daily_target is provided, it overrides the stored target for this calculation.
    """
    plan = get_day_plan(user_id, date)
    consumed = int(plan.get("consumed", 0))
    target = int(daily_target) if daily_target is not None else int(plan.get("target", 0))
    return max(0, target - consumed)


