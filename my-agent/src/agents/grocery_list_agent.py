"""
Grocery List Agent using AWS Bedrock.
Handles grocery list creation, product availability checking, substitutions, and budget management.
"""

import sys
import os
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.shared.registry import SHARED_TOOL_FUNCTIONS
from tools.grocery.registry import GROCERY_TOOL_FUNCTIONS

from strands import Agent, tool
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

@tool
def grocery_list_agent(user_id: str, query: str, model_id: str = None, actor_id: str = None, session_id: str = None, memory_client=None, memory_id: str = None) -> str:
    """
    Agent for grocery list management, cart operations, product availability, and substitutions.
    
    Args:
        user_id (str): User identifier
        query (str): Grocery-related request
        model_id (str): Model ID for the agent (optional)
        actor_id (str): Actor ID for memory (optional)
        session_id (str): Session ID for memory (optional)
        memory_client: Memory client instance (optional)
        memory_id (str): Memory ID for shared memory (optional)
    
    Returns:
        str: Grocery assistance with cart operations and product info
    """
    # Combine all available tools
    all_tools = SHARED_TOOL_FUNCTIONS + GROCERY_TOOL_FUNCTIONS
    
    # Use provided model_id or default
    model_to_use = model_id or "amazon.nova-lite-v1:0"
    
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
            system_prompt=GROCERY_SYSTEM_PROMPT,
            tools=all_tools,
            state={"actor_id": actor_id, "session_id": session_id}
        )
    else:
        agent = Agent(
            model=BedrockModel(
                model_id=model_to_use,
                region_name="us-east-1",
                temperature=0.1,
            ),
            system_prompt=GROCERY_SYSTEM_PROMPT,
            tools=all_tools,
        )
    
    # The combined prompt provides context for the specialized agent
    combined_prompt = f"User ID: {user_id}. Request: {query}"
    response = agent(combined_prompt)
    return str(response)