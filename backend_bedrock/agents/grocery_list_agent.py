"""
Grocery List Agent using AWS Bedrock.
Handles grocery list creation, product availability checking, substitutions, and budget management.
"""

import argparse
import sys
import os
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.product_tools.registry import PRODUCT_TOOL_FUNCTIONS
from tools.cart_tools.registry import CART_TOOL_FUNCTIONS

from strands import Agent
from strands.models import BedrockModel
from dotenv import load_dotenv

load_dotenv()


GROCERY_SYSTEM_PROMPT = """You are an intelligent grocery shopping assistant with advanced natural language understanding. 

Your role is to help users manage their shopping cart, check product availability, and provide budget-conscious recommendations.

Key capabilities:
1. Add items to cart with proper quantities (2 pounds, 3 items, dozen, etc.)
2. Handle batch requests like "add milk, eggs, and bread to my cart"
3. Check product availability and suggest alternatives when items are unavailable
4. Monitor budget and provide cost-conscious recommendations
5. Show cart contents and totals
6. Find substitute products when needed

Guidelines:
- Parse quantities naturally from user requests
- Handle multiple items in a single request efficiently
- Always check budget impact when adding expensive items
- Suggest alternatives for out-of-stock items
- Be conversational and helpful
- Maintain context across multiple turns

Use the available tools to search products, manage cart, check availability, and handle budget constraints."""


# Create BedrockModel instance
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name="us-east-1",
    temperature=0.1,  # Slightly deterministic for consistent responses
)

# Combine all available tools
all_tools = PRODUCT_TOOL_FUNCTIONS + CART_TOOL_FUNCTIONS

# Create the grocery agent (conversation manager handled by orchestrator)
grocery_agent = Agent(
    model=bedrock_model,
    system_prompt=GROCERY_SYSTEM_PROMPT,
    tools=all_tools,
)


# Entry point function (following temp.py pattern)
def strands_agent_bedrock(payload):
    """
    Invoke agent with payload
    """
    user_input = payload.get("prompt")
    print(f"User input: {user_input}")
    
    # Use the grocery agent directly
    response = grocery_agent(user_input)
    return str(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=str)
    args = parser.parse_args()
    payload = {"prompt": args.prompt}
    response = strands_agent_bedrock(payload)
    print(response)