"""
Nutrition Tracking Agent - Handles calorie tracking, meal logging, and nutrition goals
"""
import sys
from pathlib import Path
from strands import Agent, tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from tools.db_tool import (
    get_nutrition_plan, 
    set_nutrition_target, 
    append_meal, 
    get_calories_remaining
)
from tools.custom_tool import (
    get_current_date, 
    format_nutrition_summary, 
    validate_date_format, 
    parse_meal_input
)

NUTRITION_AGENT_PROMPT = """
You are a specialized nutrition tracking assistant. Your role is to help users with:

1. **Calorie Tracking**: Log meals and track daily calorie consumption
2. **Nutrition Goals**: Set and manage daily calorie targets
3. **Progress Monitoring**: Check remaining calories and daily progress
4. **Meal Logging**: Parse and log meal information with nutritional data

Guidelines:
- Always ask for user_id when accessing personal nutrition data
- Use YYYY-MM-DD format for dates, default to today if not specified
- Provide clear, actionable nutrition information
- Help users stay on track with their nutrition goals
- Parse natural language meal descriptions into structured data

Available Tools:
- get_nutrition_plan: Get daily nutrition data for a user
- set_nutrition_target: Set daily calorie targets
- append_meal: Log meals to nutrition tracker
- get_calories_remaining: Calculate remaining calories for the day
- get_current_date: Get today's date
- format_nutrition_summary: Format nutrition data for display
- validate_date_format: Validate date strings
- parse_meal_input: Parse meal descriptions
"""

@tool
def nutrition_agent(user_id: str, query: str) -> str:
    """
    Use this agent for nutrition tracking queries like calorie logging, meal tracking, and nutrition goals.
    Args:
        user_id: The ID of the user making the request
        query: The user's nutrition-related query, e.g., "Log breakfast with 400 calories"
    """
    agent = Agent(
        model="amazon.nova-lite-v1:0",
        system_prompt=NUTRITION_AGENT_PROMPT,
        tools=[
            get_nutrition_plan,
            set_nutrition_target,
            append_meal,
            get_calories_remaining,
            get_current_date,
            format_nutrition_summary,
            validate_date_format,
            parse_meal_input
        ]
    )
    
    # Combine user context with query
    combined_prompt = f"User ID: {user_id}. Nutrition Query: {query}"
    response = agent(combined_prompt)
    return str(response)

def main():
    """Test the nutrition agent"""
    user_id = "test-user-123"
    query = "Set my daily calorie target to 1800 for today"
    result = nutrition_agent(user_id, query)
    print(result)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=str, default="test-user-123", help="User ID")
    parser.add_argument("--query", type=str, default="Set my daily calorie target to 1800", help="Nutrition query")
    args = parser.parse_args()
    
    result = nutrition_agent(args.user_id, args.query)
    print(result)