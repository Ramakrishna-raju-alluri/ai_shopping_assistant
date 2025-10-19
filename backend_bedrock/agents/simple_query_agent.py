from strands import Agent, tool
import argparse
import json
import os
import sys
from pathlib import Path
from strands.models import BedrockModel
from dotenv import load_dotenv

load_dotenv()

# Flexible import for tools
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend_bedrock.tools.shared.registry import SHARED_TOOL_FUNCTIONS
    from backend_bedrock.tools.shared.product_catalog import check_product_availability
except ImportError:
    try:
        sys.path.insert(0, str(parent_dir))
        from tools.shared.registry import SHARED_TOOL_FUNCTIONS
        from tools.shared.product_catalog import check_product_availability
    except ImportError:
        # If import fails, define a no-op placeholder
        SHARED_TOOL_FUNCTIONS = []
        def check_product_availability(product_name: str) -> str:
            return "Product catalog unavailable."

SIMPLE_QUERY_PROMPT = """
You are a product catalog and store information assistant. Your primary role is to help users with:
- Product availability and stock status
- Store information and hours
- Simple product searches and recommendations
- General shopping assistance

You have access to shared tools for:
- Product catalog searches (search_products, fetch_all_products, get_products_by_category)
- Product availability checking (check_product_availability)
- User profile information (fetch_user_profile, get_user_preferences)
- Cost calculations (calculate_cost, calculate_calories)

Use these tools to provide accurate, helpful information about products and store services.
"""

@tool
def simple_query_agent(user_id: str, query: str, model_id: str = None, actor_id: str = None, session_id: str = None, memory_client=None, memory_id: str = None) -> str:
    """
    Agent for product availability checks, stock status, store information, and catalog searches.
    
    Args:
        user_id (str): User identifier
        query (str): Product or store-related question
        model_id (str): Model ID for the agent (optional)
        actor_id (str): Actor ID for memory (optional)
        session_id (str): Session ID for memory (optional)
        memory_client: Memory client instance (optional)
        memory_id (str): Memory ID for shared memory (optional)
    
    Returns:
        str: Product availability, store info, or catalog results
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
        
        agent = Agent(
            hooks=[memory_hooks],
            model=model_to_use,
            system_prompt=SIMPLE_QUERY_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS,
            state={"actor_id": actor_id, "session_id": session_id}
        )
    else:
        agent = Agent(
            model=BedrockModel(
                model_id=model_to_use,
                region_name="us-east-1",
                temperature=0.1,
            ),
            system_prompt=SIMPLE_QUERY_PROMPT,
            tools=SHARED_TOOL_FUNCTIONS
        )
    
    response = agent(f"User ID: {user_id}. Query: {query}")
    return str(response)

# @app.entrypoint
# def strands_agent_bedrock(payload):
#     """
#     Invoke agent with payload
#     """
#     user_input = payload.get("prompt")
#     print(f"User input: {user_input}")
#     response = agent(user_input)
#     return response.message['content'][0]['text']

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("prompt", type=str)
#     args = parser.parse_args()
#     payload = {"prompt": args.prompt}
#     response = strands_agent_bedrock(payload)
#     print(response)
#    #app.run()