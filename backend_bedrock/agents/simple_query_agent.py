from strands import Agent, tool
import argparse
import json
# from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

# app = BedrockAgentCoreApp()

model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(
    model_id=model_id,
)
from pathlib import Path
import sys

# Flexible import for tools
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
project_root = parent_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend_bedrock.tools.catalog_tools import find_product_stock
except ImportError:
    try:
        sys.path.insert(0, str(parent_dir))
        from tools.catalog_tools import find_product_stock
    except ImportError:
        # If import fails, define a no-op placeholder (will be overwritten when run properly)
        def find_product_stock(product_name: str) -> str:
            return "Catalog tools unavailable."

SIMPLE_QUERY_PROMPT = """
You are a product catalog and store information assistant. Your primary role is to help users with:
- Product availability and stock status
- Store information and hours
- Simple product searches and recommendations
- General shopping assistance

When users ask about specific products, always use the find_product_stock tool to check availability.
Provide helpful, concise responses about products and store services.
"""

@tool
def simple_query_agent(user_id: str, query: str) -> str:
    """
    Agent for product availability checks, stock status, store information, and catalog searches.
    
    Args:
        user_id (str): User identifier
        query (str): Product or store-related question
    
    Returns:
        str: Product availability, store info, or catalog results
    """
    agent = Agent(
        model=model,
        system_prompt=SIMPLE_QUERY_PROMPT,
        tools=[find_product_stock]
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