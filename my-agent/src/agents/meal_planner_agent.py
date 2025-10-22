import sys
import os
from pathlib import Path
from strands import Agent, tool
from strands.handlers import PrintingCallbackHandler
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
    # Use local imports first (my-agent structure)
    from ..tools.shared.registry import SHARED_TOOL_FUNCTIONS
    from ..tools.meal_planning.registry import MEAL_PLANNING_TOOL_FUNCTIONS
    from ..models.structured_outputs import MealPlan, Recipe
    from ..utils.output_detector import should_use_structured_output
except ImportError:
    try:
        # Fallback to absolute imports
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

IMPORTANT: When users request multiple recipes (e.g., "2 breakfast options", "3 dinner recipes"), provide DIVERSE and DIFFERENT recipes, not variations of the same dish.

For meal planning requests, provide:
1. Detailed recipes with ingredients, instructions, prep/cook times, and nutritional information
2. Complete shopping lists with quantities needed for all recipes
3. Dietary restriction considerations and ingredient substitutions
4. Nutritional balance analysis and cost estimates

RECIPE DIVERSITY GUIDELINES:
- For multiple recipe requests, ensure each recipe has different main ingredients
- Vary cooking methods (grilled, baked, stir-fried, etc.)
- Include different cuisine types when possible
- Avoid repetitive ingredient combinations

To do this, you must follow these steps:
1. ALWAYS Fetch the user's profile to understand their preferences and constraints using 'fetch_user_profile'.
2. ALWAYS get the available ingredients in stock using 'fetch_available_items'
3. Suggest recipes/meals based on the user's preferences and ingredients availability 
4. Try to get diverse recipe options based on available ingredients.
5. Select recipes that offer variety in ingredients, cooking methods, and flavors.
6. Create a comprehensive shopping list from all recipe ingredients.
7. Provide ingredient substitutions for dietary restrictions or availability issues.

IMPORTANT RESPONSE RULES:
- NEVER mention user IDs, session IDs, or any internal identifiers in your responses
- NEVER include image URLs or links in your responses
- NEVER expose internal system information or technical details
- Focus only on helpful, user-friendly meal planning assistance
- Keep responses clean and professional
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
    model_to_use = model_id or os.getenv("MODEL_ID", "amazon.nova-lite-v1:0")
    
    # Create agent with or without memory
    if memory_client and memory_id and actor_id and session_id:
        # Import shared memory hook
        try:
            from agents.shared_memory_hook import ShortTermMemoryHook
        except ImportError:
            try:
                from agents.shared_memory_hook import ShortTermMemoryHook
            except ImportError:
                from shared_memory_hook import ShortTermMemoryHook
        
        memory_hooks = ShortTermMemoryHook(memory_client, memory_id)
        
        from strands.models import BedrockModel
        planner = Agent(
            hooks=[memory_hooks],
            model=BedrockModel(
                model_id=model_to_use,
                region_name="us-east-1",
                temperature=0.1,
                streaming=False  # Disable streaming for Nova Pro
            ),
            system_prompt=MEAL_PLANNER_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS + MEAL_PLANNING_TOOL_FUNCTIONS,
            state={"actor_id": actor_id, "session_id": session_id}
        )
    else:
        from strands.models import BedrockModel
        planner = Agent(
            model=BedrockModel(
                model_id=model_to_use,
                region_name="us-east-1",
                temperature=0.1,
                streaming=False  # Disable streaming for Nova Pro
            ),
            system_prompt=MEAL_PLANNER_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS + MEAL_PLANNING_TOOL_FUNCTIONS
        )
    
    # The combined prompt provides context for the specialized agent
    combined_prompt = f"User ID: {user_id}. Request: {query}"
    
    response = planner(combined_prompt)
    return str(response)

    # Check if structured output is needed based on keywords
    # if should_use_structured_output and should_use_structured_output(query) and MealPlan:
    #     try:
    #         # Use structured output for meal plans and recipe summaries
    #         structured_response = planner.structured_output(
    #             output_model=MealPlan,
    #             prompt=combined_prompt
    #         )
    #         # Convert to JSON string for consistent return type
    #         return structured_response.model_dump_json()
    #     except Exception as e:
    #         # Fallback to text response on error
    #         print(f"Structured output failed: {e}")
    #         response = planner(combined_prompt)
    #         return str(response)
    # else:
    #     # Use regular text response for simple queries
    #     response = planner(combined_prompt)
    #     return str(response)

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