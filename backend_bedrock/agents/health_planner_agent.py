import sys
from pathlib import Path
from strands import Agent, tool
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for imports when running directly
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import with flexible import system
try:
    from backend_bedrock.tools import health_planner_tools
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from tools import health_planner_tools
    except ImportError:
        # Last resort - direct import
        import health_planner_tools

HEALTH_PLANNER_PROMPT = """
You are a health and nutrition planner agent. You maintain a per-day calendar of meals
and nutrition totals (calories, protein, carbs, fat). You can:
- Create/update a day plan when the user provides meals for a day
- Append a meal to a day
- Report remaining calories given a daily target
- Fetch the current plan for a day

Always ask for and use an explicit date (YYYY-MM-DD) and user id. If a date is
missing, request clarification. Keep updates idempotent by re-writing the full day
plan after changes.
"""

@tool
def health_planner(user_id: str, date: str, action: str, payload: dict = None, daily_target: int = None) -> str:
    """
    High-level tool to delegate to specific calendar operations.
    - action: one of ["upsert", "append", "get", "remaining_calories"]
    - payload: for upsert/append, includes meals or a single meal
    - daily_target: required for remaining_calories
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


@tool
def health_planner_agent(user_id: str, query: str) -> str:
    """
    Use this agent to update/query the nutrition calendar per day.
    Examples:
    - "Log breakfast 400 kcal on 2025-10-17"
    - "How many calories left today if my target is 1800?"
    """
    planner = Agent(
        system_prompt=HEALTH_PLANNER_PROMPT,
        tools=[
            health_planner,
            health_planner_tools.upsert_day_plan,
            health_planner_tools.get_day_plan,
            health_planner_tools.append_meal,
            health_planner_tools.calories_remaining,
        ]
    )
    response = planner(f"User ID: {user_id}. Request: {query}")
    return str(response)


def main():
    """Quick manual test for the health planner agent"""
    user_id = "test-user-123"
    query = "Add lunch 600 calories for 2025-10-17 and show remaining with target 2000"
    result = health_planner_agent(user_id, query)
    print(result)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=str, default="test-user-123", help="User ID")
    parser.add_argument("--query", type=str, default="How many calories left for 2025-10-17 if target 1800?", help="Query")
    args = parser.parse_args()
    print(health_planner_agent(args.user_id, args.query))


