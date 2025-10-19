"""
Meal Planning Agent - Handles meal suggestions, recipe generation, and cost calculations
"""
import sys
from pathlib import Path
from strands import Agent, tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from tools.model_tool import calculate_calories, calculate_cost, generate_meal_suggestions
from tools.db_tool import get_user_profile

MEAL_PLANNING_AGENT_PROMPT = """
You are a specialized meal planning assistant. Your role is to help users with:

1. **Meal Suggestions**: Generate meal ideas based on preferences and budget
2. **Recipe Planning**: Create recipes using available ingredients
3. **Cost Calculation**: Calculate total costs for meals and ingredients
4. **Calorie Estimation**: Estimate calories for ingredients and meals
5. **Dietary Preferences**: Consider user dietary restrictions and preferences

Guidelines:
- Always fetch user profile first to understand dietary preferences
- Consider budget constraints when making suggestions
- Provide practical, achievable meal plans
- Include cost and calorie information for transparency
- Suggest meals that use available ingredients efficiently

Available Tools:
- get_user_profile: Fetch user dietary preferences and constraints
- calculate_calories: Estimate calories for ingredients
- calculate_cost: Calculate meal and ingredient costs
- generate_meal_suggestions: AI-powered meal recommendations
"""

@tool
def meal_planning_agent(user_id: str, query: str) -> str:
    """
    Use this agent for meal planning queries like recipe suggestions, meal planning, and cost calculations.
    Args:
        user_id: The ID of the user making the request
        query: The user's meal planning query, e.g., "Suggest healthy meals under $20"
    """
    agent = Agent(
        model="amazon.nova-pro-v1:0",
        system_prompt=MEAL_PLANNING_AGENT_PROMPT,
        tools=[
            get_user_profile,
            calculate_calories,
            calculate_cost,
            generate_meal_suggestions
        ]
    )
    
    # Combine user context with query
    combined_prompt = f"User ID: {user_id}. Meal Planning Query: {query}"
    response = agent(combined_prompt)
    return str(response)

def main():
    """Test the meal planning agent"""
    user_id = "test-user-123"
    query = "Suggest healthy meals under $20 for dinner"
    result = meal_planning_agent(user_id, query)
    print(result)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=str, default="test-user-123", help="User ID")
    parser.add_argument("--query", type=str, default="Suggest healthy meals under $20", help="Meal planning query")
    args = parser.parse_args()
    
    result = meal_planning_agent(args.user_id, args.query)
    print(result)