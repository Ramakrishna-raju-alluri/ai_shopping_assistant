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
    from backend_bedrock.tools import meal_planner_tools
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from tools import meal_planner_tools
    except ImportError:
        # Last resort - direct import
        import meal_planner_tools

MEAL_PLANNER_PROMPT = """
You are a specialized meal planning assistant. Your goal is to generate a meal plan.
To do this, you must follow these steps:
1. Fetch the user's profile to understand their preferences and constraints using `fetch_user_profile`.
2. Fetch available items from the store using `fetch_available_items`.
3. Generate a list of three distinct meal recipes (breakfast, lunch, dinner) based on the user's preferences and available items.
4. For each recipe, calculate the estimated cost and calories using the provided tools.
"""

@tool
def meal_planner_agent(user_id: str, query: str) -> str:
    """
    Agent for meal planning, recipe creation, grocery lists, and food cost/nutrition calculations.
    
    Args:
        user_id (str): User identifier
        query (str): Meal planning request
    
    Returns:
        str: Meal plan with recipes, ingredients, costs, and nutrition info
    """
    planner = Agent(
        system_prompt=MEAL_PLANNER_PROMPT,
        tools=[
            meal_planner_tools.fetch_user_profile,
            meal_planner_tools.fetch_available_items,
            meal_planner_tools.calculate_calories,
            meal_planner_tools.calculate_cost,
        ]
    )
    # The combined prompt provides context for the specialized agent
    combined_prompt = f"User ID: {user_id}. Request: {query}"
    response = planner(combined_prompt)
    return str(response)

# def main():
#     """Test the meal planner agent"""
#     user_id = "user_99"
#     query = "I need a healthy meal plan for today"
#     result = meal_planner_agent(user_id, query)
#     print(result)

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--user-id", type=str, default="user_99", help="User ID")
#     parser.add_argument("--query", type=str, default="I need a healthy meal plan for today", help="Query")
#     args = parser.parse_args()
    
#     result = meal_planner_agent(args.user_id, args.query)
#     print(result)