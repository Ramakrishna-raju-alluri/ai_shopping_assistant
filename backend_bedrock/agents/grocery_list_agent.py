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
from strands.handlers import PrintingCallbackHandler
from dotenv import load_dotenv

# Import structured output models and detection utilities
from backend_bedrock.models.structured_outputs import GrocerySummary, CartItem
from backend_bedrock.utils.output_detector import should_use_structured_output

load_dotenv()

GROCERY_SYSTEM_PROMPT = """You are an intelligent grocery shopping assistant with advanced natural language understanding. 

Your role is to help users manage their shopping cart, check product availability, and provide budget-conscious recommendations.

Key capabilities:
1. Add items to cart with proper quantities (2 pounds, 3 items, dozen, etc.)
2. Handle batch requests like "add milk, eggs, and bread to my cart"
3. Check product availability and suggest alternatives when items are unavailable
4. Monitor budget and provide cost-conscious recommendations with detailed analysis
5. Show cart contents and totals with comprehensive summaries
6. Find substitute products when needed
7. Provide structured cart summaries with budget analysis when requested

For structured outputs (when users request summaries, reports, totals, or cart analysis):
- Include detailed budget analysis with status and savings opportunities
- Provide comprehensive availability summary for all cart items
- Suggest specific product substitutions for better value or availability
- Include actionable shopping recommendations
- Calculate precise budget remaining and status

Guidelines:
- Parse quantities naturally from user requests
- Handle multiple items in a single request efficiently
- Always check budget impact when adding expensive items
- Suggest alternatives for out-of-stock items with specific reasons
- Provide detailed cost analysis and savings opportunities
- Be conversational and helpful
- Maintain context across multiple turns
- For summaries, focus on actionable insights and clear data presentation

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
    
    Returns:
        str: Grocery assistance with cart operations and product info
    """
    # Combine all available tools
    all_tools = SHARED_TOOL_FUNCTIONS + GROCERY_TOOL_FUNCTIONS
    
    # Use provided model_id or default from environment
    model_to_use = model_id or os.getenv("MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    # Create agent with or without memory (following travel-planning pattern)
    if memory_client and memory_id and actor_id and session_id:
        # Import shared memory hook
        try:
            from backend_bedrock.agents.shared_memory_hook import ShortTermMemoryHook
        except ImportError:
            try:
                from agents.shared_memory_hook import ShortTermMemoryHook
            except ImportError:
                from shared_memory_hook import ShortTermMemoryHook
        
        # Create memory hook following travel-planning pattern
        memory_hooks = ShortTermMemoryHook(memory_client, memory_id)
        
        agent = Agent(
            hooks=[memory_hooks],
            model=model_to_use,
            system_prompt=GROCERY_SYSTEM_PROMPT,
            tools=all_tools,
            state={"actor_id": actor_id, "session_id": session_id},
            callback_handler=PrintingCallbackHandler()
        )
        print(f"🧠 Grocery agent created with memory: actor_id={actor_id}, session_id={session_id}")
    else:
        # Fallback without memory
        agent = Agent(
            model=BedrockModel(
                model_id=model_to_use,
                region_name="us-east-1",
                temperature=0.1,
            ),
            system_prompt=GROCERY_SYSTEM_PROMPT,
            tools=all_tools,
            callback_handler=PrintingCallbackHandler()
        )
        print(f"🤖 Grocery agent created without memory")
    
    # The combined prompt provides context for the specialized agent
    # IMPORTANT: For cart operations, we need to use user_id as session_id to match frontend
    # The cart operations will automatically use user_id as session_id when none is provided
    combined_prompt = f"User ID: {user_id}. Request: {query}"
    
    response = agent(combined_prompt)
    return str(response)

    # # Check if structured output is needed based on keywords
    # if should_use_structured_output(query):
    #     try:
    #         # Use structured output for summaries/reports
    #         structured_response = agent.structured_output(
    #             output_model=GrocerySummary,
    #             prompt=combined_prompt
    #         )
    #         # Convert to JSON string for consistent return type
    #         return structured_response.model_dump_json()
    #     except Exception as e:
    #         # Fallback to text response on error
    #         print(f"Structured output failed for grocery agent: {e}")
    #         response = agent(combined_prompt)
    #         return str(response)
    # else:
    #     # Use regular text response for simple queries
    #     response = agent(combined_prompt)
    #     return str(response)