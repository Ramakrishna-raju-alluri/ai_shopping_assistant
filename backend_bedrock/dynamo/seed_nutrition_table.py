import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from decimal import Decimal

# Flexible imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend_bedrock.tools.health_planner_tools import set_daily_target, append_meal, get_day_plan
    from backend_bedrock.dynamo.client import NUTRITION_TABLE
except ImportError:
    try:
        sys.path.insert(0, str(parent_dir))
        from tools.health_planner_tools import set_daily_target, append_meal, get_day_plan
        from dynamo.client import NUTRITION_TABLE
    except ImportError:
        # Fallback values; script will still run if PYTHONPATH is set correctly
        NUTRITION_TABLE = os.getenv("NUTRITION_TABLE", "nutrition_calendar")


def parse_meal_arg(meal_str: str) -> Dict[str, Any]:
    """
    Parse a meal string of the form "name,calories,protein,carbs,fat".
    Only name and calories are required. Missing macros default to 0.
    """
    parts = [p.strip() for p in meal_str.split(",")]
    name = parts[0] if parts else "meal"
    def to_int(i, default=0):
        try:
            return int(i)
        except Exception:
            return default
    calories = to_int(parts[1]) if len(parts) > 1 else 0
    protein = to_int(parts[2]) if len(parts) > 2 else 0
    carbs = to_int(parts[3]) if len(parts) > 3 else 0
    fat = to_int(parts[4]) if len(parts) > 4 else 0
    return {"name": name, "calories": calories, "protein": protein, "carbs": carbs, "fat": fat}


def daterange(start_date: datetime, days: int) -> List[str]:
    return [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]


def seed(user_id: str, start_date: str, days: int, target: int, meals: List[Dict[str, Any]]):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    dates = daterange(start, days)
    count = 0
    for date in dates:
        set_daily_target(user_id, date, target)
        for meal in meals:
            append_meal(user_id, date, meal)
        count += 1
    return {"table": NUTRITION_TABLE, "user_id": user_id, "days_written": count, "dates": dates}


def _to_jsonable(obj):
    if isinstance(obj, Decimal):
        # Prefer int if whole number
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed data into the nutrition calendar table")
    parser.add_argument("--user-id", required=True, help="User ID to seed")
    parser.add_argument("--start-date", default=datetime.utcnow().strftime("%Y-%m-%d"), help="YYYY-MM-DD start date")
    parser.add_argument("--days", type=int, default=1, help="Number of consecutive days to seed")
    parser.add_argument("--target", type=int, default=1800, help="Daily calorie target to set")
    parser.add_argument("--meal", action="append", default=[], help="Meal as 'name,calories,protein,carbs,fat'. Can repeat.")
    args = parser.parse_args()

    meals: List[Dict[str, Any]] = [parse_meal_arg(m) for m in args.meal] or [
        {"name": "breakfast", "calories": 400, "protein": 20, "carbs": 30, "fat": 10},
        {"name": "lunch", "calories": 650, "protein": 35, "carbs": 60, "fat": 20},
        {"name": "dinner", "calories": 700, "protein": 40, "carbs": 70, "fat": 25},
    ]

    result = seed(args.user_id, args.start_date, args.days, args.target, meals)
    # Show one sample day
    sample = get_day_plan(args.user_id, result["dates"][0])
    payload = {"result": result, "sample_day": sample}
    print(json.dumps(_to_jsonable(payload), indent=2))


if __name__ == "__main__":
    main()


