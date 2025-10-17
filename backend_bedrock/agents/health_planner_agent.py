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
def health_planner_agent(user_id: str, query: str) -> str:
    """
    Agent for nutrition tracking, calorie management, daily meal logging, and health goal monitoring.
    Requires explicit dates (YYYY-MM-DD format) in queries.
    
    Args:
        user_id (str): User identifier
        query (str): Health/nutrition request with date
    
    Returns:
        str: Nutrition tracking results or calorie calculations
    """
    user_id = "test-user-123"
    planner = Agent(
        system_prompt=HEALTH_PLANNER_PROMPT,
        tools=[
            health_planner_tools.health_planner,
            health_planner_tools.upsert_day_plan,
            health_planner_tools.get_day_plan,
            health_planner_tools.append_meal,
            health_planner_tools.calories_remaining,
        ]
    )
    response = planner(f"User ID: {user_id}. Request: {query}")
    return str(response)


# def main():
#     """Quick manual test for the health planner agent"""
#     user_id = "test-user-123"
#     query = "Add lunch 600 calories for 2025-10-17 and show remaining with target 2000"
#     result = health_planner_agent(user_id, query)
#     print(result)


# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--user-id", type=str, default="test-user-123", help="User ID")
#     parser.add_argument("--query", type=str, default="How many calories left for 2025-10-17 if target 1800?", help="Query")
#     args = parser.parse_args()
#     print(health_planner_agent(args.user_id, args.query))

