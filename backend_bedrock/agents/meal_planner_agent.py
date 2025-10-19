import sys
import os
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
    from backend_bedrock.tools.shared.registry import SHARED_TOOL_FUNCTIONS
    from backend_bedrock.tools.meal_planning.registry import MEAL_PLANNING_TOOL_FUNCTIONS
    from backend_bedrock.models.structured_outputs import MealPlan, Recipe
    from backend_bedrock.utils.output_detector import should_use_structured_output
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from tools.shared.registry import SHARED_TOOL_FUNCTIONS
        from tools.meal_planning.registry import MEAL_PLANNING_TOOL_FUNCTIONS
        from models.structured_outputs import MealPlan, Recipe
        from utils.output_detector import should_use_structured_output
    except ImportError:
        # Fallback
        SHARED_TOOL_FUNCTIONS = []
        MEAL_PLANNING_TOOL_FUNCTIONS = []
        MealPlan = None
        Recipe = None
        should_use_structured_output = None

MEAL_PLANNER_PROMPT = """
You are a specialized meal planning assistant. Your goal is to generate comprehensive meal plans with detailed recipes.

For structured meal plan outputs, provide:
1. Detailed recipes with ingredients, instructions, prep/cook times, and nutritional information
2. Complete shopping lists with quantities needed for all recipes
3. Dietary restriction considerations and ingredient substitutions
4. Nutritional balance analysis and cost estimates

To do this, you must follow these steps:
1. Fetch the user's profile to understand their preferences and constraints using `fetch_user_profile`.
2. Fetch available items from the store using `fetch_available_items`.
3. Generate a list of three distinct meal recipes (breakfast, lunch, dinner) based on the user's preferences and available items.
4. For each recipe, calculate the estimated cost and calories using the provided tools.
5. Create a comprehensive shopping list from all recipe ingredients.
6. Provide ingredient substitutions for dietary restrictions or availability issues.
7. Calculate total nutritional summary and meal balance score.
"""

@tool
def meal_planner_agent(user_id: str, query: str, model_id: str = None, actor_id: str = None, session_id: str = None, memory_client=None, memory_id: str = None) -> str:
    """
    Agent for meal planning, recipe creation, grocery lists, and food cost/nutrition calculations.
    
    Args:
        user_id (str): User identifier
        query (str): Meal planning request
        model_id (str): Model ID for the agent (optional)
        actor_id (str): Actor ID for memory (optional)
        session_id (str): Session ID for memory (optional)
        memory_client: Memory client instance (optional)
        memory_id (str): Memory ID for shared memory (optional)
    
    Returns:
        str: Meal plan with recipes, ingredients, costs, and nutrition info
    """
    # Use provided model_id or default from environment
    model_to_use = model_id or os.getenv("MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    # Create agent with or without memory
    if memory_client and memory_id and actor_id and session_id:
        # Import shared memory hook
        try:
            from backend_bedrock.agents.shared_memory_hook import ShortTermMemoryHook
        except ImportError:
            try:
                from agents.shared_memory_hook import ShortTermMemoryHook
            except ImportError:
                from shared_memory_hook import ShortTermMemoryHook
        
        memory_hooks = ShortTermMemoryHook(memory_client, memory_id)
        
        planner = Agent(
            hooks=[memory_hooks],
            model=model_to_use,
            system_prompt=MEAL_PLANNER_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS + MEAL_PLANNING_TOOL_FUNCTIONS,
            state={"actor_id": actor_id, "session_id": session_id}
        )
    else:
        planner = Agent(
            model=model_to_use,
            system_prompt=MEAL_PLANNER_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS + MEAL_PLANNING_TOOL_FUNCTIONS
        )
    
    # The combined prompt provides context for the specialized agent
    combined_prompt = f"User ID: {user_id}. Request: {query}"
    
    # Check if structured output is needed based on keywords
    if should_use_structured_output and should_use_structured_output(query) and MealPlan:
        try:
            # Use structured output for meal plans and recipe summaries
            structured_response = planner.structured_output(
                output_model=MealPlan,
                prompt=combined_prompt
            )
            # Convert to JSON string for consistent return type
            return structured_response.model_dump_json()
        except Exception as e:
            # Fallback to text response on error
            print(f"Structured output failed: {e}")
            response = planner(combined_prompt)
            return str(response)
    else:
        # Use regular text response for simple queries
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