from strands import Agent, tool
import argparse
import json
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

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

agent = Agent(
    model=model,
    system_prompt=(
        "You're a recipe helper and product catalog assistant. "
        "When users ask about product availability or stock, use the find_product_stock tool."
    ),
    tools=[find_product_stock]
)

@app.entrypoint
def strands_agent_bedrock(payload):
    """
    Invoke agent with payload
    """
    user_input = payload.get("prompt")
    print(f"User input: {user_input}")
    response = agent(user_input)
    return response.message['content'][0]['text']

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=str)
    args = parser.parse_args()
    payload = {"prompt": args.prompt}
    response = strands_agent_bedrock(payload)
    print(response)
    #app.run()