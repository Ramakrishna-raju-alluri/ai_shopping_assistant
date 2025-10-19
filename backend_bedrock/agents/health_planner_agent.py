import sys
import os
from pathlib import Path
from strands import Agent, tool
from strands.models import BedrockModel
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
    from backend_bedrock.tools.health.registry import HEALTH_TOOL_FUNCTIONS
    from backend_bedrock.models.structured_outputs import HealthSummary
    from backend_bedrock.utils.output_detector import should_use_structured_output
except ImportError:
    try:
        # When running from backend_bedrock directory
        sys.path.insert(0, str(parent_dir))
        from tools.shared.registry import SHARED_TOOL_FUNCTIONS
        from tools.health.registry import HEALTH_TOOL_FUNCTIONS
        from models.structured_outputs import HealthSummary
        from utils.output_detector import should_use_structured_output
    except ImportError:
        # Fallback
        SHARED_TOOL_FUNCTIONS = []
        HEALTH_TOOL_FUNCTIONS = []
        HealthSummary = None
        should_use_structured_output = None

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
def health_planner_agent(user_id: str, query: str, model_id: str = None, actor_id: str = None, session_id: str = None, memory_client=None, memory_id: str = None) -> str:
    """
    Agent for nutrition tracking, calorie management, daily meal logging, and health goal monitoring.
    Requires explicit dates (YYYY-MM-DD format) in queries.
    
    Args:
        user_id (str): User identifier
        query (str): Health/nutrition request with date
        model_id (str): Model ID for the agent (optional)
        actor_id (str): Actor ID for memory (optional)
        session_id (str): Session ID for memory (optional)
        memory_client: Memory client instance (optional)
        memory_id (str): Memory ID for shared memory (optional)
    
    Returns:
        str: Nutrition tracking results or calorie calculations
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
            system_prompt=HEALTH_PLANNER_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS + HEALTH_TOOL_FUNCTIONS,
            state={"actor_id": actor_id, "session_id": session_id}
        )
    else:
        planner = Agent(
            model=BedrockModel(
                model_id=model_to_use,
                region_name="us-east-1",
                temperature=0.1,
            ),
            system_prompt=HEALTH_PLANNER_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS + HEALTH_TOOL_FUNCTIONS
        )
    
    # Check if structured output is needed based on keywords
    if should_use_structured_output and HealthSummary and should_use_structured_output(query):
        try:
            # Use structured output for summaries/reports
            structured_response = planner.structured_output(
                output_model=HealthSummary,
                prompt=f"User ID: {user_id}. Request: {query}"
            )
            # Convert to JSON string for consistent return type
            return structured_response.model_dump_json()
        except Exception as e:
            # Fallback to text response on error
            print(f"Structured output failed: {e}")
            response = planner(f"User ID: {user_id}. Request: {query}")
            return str(response)
    else:
        # Use regular text response for simple queries
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

