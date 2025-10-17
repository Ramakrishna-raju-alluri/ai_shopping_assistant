"""
Grocery List Agent using AWS Bedrock.
Handles grocery list creation, product availability checking, substitutions, and budget management.
"""

import json
import argparse
from typing import Dict, List, Any, Optional
try:
    # Try absolute import first (when run from parent directory)
    from backend_bedrock.dynamo.queries import get_user_profile
    from backend_bedrock.tools.product_tools.registry import (
        PRODUCT_TOOLS,
        PRODUCT_TOOL_FUNCTIONS,
        execute_catalog_tool,
    )
    from backend_bedrock.tools.cart_tools.registry import CART_TOOL_FUNCTIONS
except ImportError:
    # Fall back to relative imports (when run from backend_bedrock directory)
    from dynamo.queries import get_user_profile
    from tools.product_tools.registry import (
        PRODUCT_TOOLS,
        PRODUCT_TOOL_FUNCTIONS,
        execute_catalog_tool,
    )
    from tools.cart_tools.registry import CART_TOOL_FUNCTIONS
from strands import Agent
from strands.models import BedrockModel
from strands.agent.conversation_manager import SummarizingConversationManager


GROCERY_LIST_PROMPT = (
    "You are an intelligent grocery shopping assistant with advanced natural language understanding. Your role is to:\n\n"
    "1. Help users manage their shopping cart with natural language\n"
    "2. Process batch requests like 'add milk, eggs, and bread to my cart'\n"
    "3. Parse quantities from requests like 'add 2 pounds of chicken'\n"
    "4. Check product availability and suggest alternatives\n"
    "5. Monitor budget and provide cost-conscious recommendations\n"
    "6. Handle complex conversational requests intelligently\n\n"
    "Key tools available:\n"
    "- process_natural_language_request: Handle complex, multi-item requests\n"
    "- add_item_to_cart: Add individual items with quantity\n"
    "- get_cart_summary: Show current cart contents and total\n"
    "- check_item_availability: Check if items are in stock\n"
    "- find_substitutes_for_item: Find alternatives for unavailable items\n"
    "- check_budget_status: Monitor spending against user's budget\n"
    "- suggest_budget_alternatives: Recommend cheaper options\n\n"
    "Smart processing guidelines:\n"
    "1. For complex requests, use process_natural_language_request first\n"
    "2. Parse quantities automatically (2 pounds, 3 items, dozen, etc.)\n"
    "3. Handle batch requests efficiently\n"
    "4. Always check budget impact when adding items\n"
    "5. Proactively suggest alternatives for out-of-stock items\n"
    "6. Maintain conversation context across multiple turns\n\n"
    "Be conversational, intelligent, and anticipate user needs."
)


def _build_bedrock_model() -> BedrockModel:
    try:
        model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            region_name="us-east-1",
        )
        print(f"DEBUG - BedrockModel created successfully. Available methods: {[m for m in dir(model) if not m.startswith('_')]}")
        return model
    except Exception as e:
        print(f"DEBUG - Error creating BedrockModel: {str(e)}")
        raise

def _build_conversation_manager() -> SummarizingConversationManager:
    return SummarizingConversationManager(summary_ratio=0.5, preserve_recent_messages=4)

def _build_agent() -> Agent:
    model = _build_bedrock_model()
    conv = _build_conversation_manager()
    # Combine product tools and cart tools
    all_tools = PRODUCT_TOOL_FUNCTIONS + CART_TOOL_FUNCTIONS
    return Agent(
        model=model,
        system_prompt=GROCERY_LIST_PROMPT,
        conversation_manager=conv,
        tools=all_tools,
    )

class GroceryListAgent:
    """
    Grocery List Agent for managing shopping carts, checking availability, and suggesting substitutions.
    """
    
    def __init__(self):
        self._agent: Optional[Agent] = None
    
    def get_agent(self) -> Agent:
        """Get or create the Strands agent instance."""
        if self._agent is None:
            self._agent = _build_agent()
        return self._agent
    
    def process_message(
        self,
        user_message: str,
        user_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: User's message
            user_id: User ID for personalization
            session_id: Session ID for conversation history
            context: Optional context (e.g., meal plan, budget)
            
        Returns:
            Agent response with text and any actions taken
        """
        try:
            # Get user profile for personalization
            user_profile = get_user_profile(user_id) if user_id else {}
            budget_limit = float(user_profile.get("budget_limit", 100)) if user_profile else 100
            
            agent = self.get_agent()
            context_text = self._build_context(user_profile, context, budget_limit)
            prompt = f"Context:\n{context_text}\n\nUser: {user_message}"
            
            # Use the correct Strands agent method based on debug output
            try:
                # The agent has invoke_async and stream_async methods
                import asyncio
                result = asyncio.run(agent.invoke_async(prompt))
            except Exception as e:
                try:
                    # Try structured output
                    result = agent.structured_output(prompt)
                except Exception as e2:
                    # Fallback - just return the prompt for now
                    result = f"Agent processing error: {str(e)}. Fallback response: I received your request '{user_message}' but I'm having technical difficulties processing it right now."
            
            return {
                "success": True,
                "message": str(result),
                "tool_calls_made": 0,
                "session_id": session_id
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"DEBUG - Agent error: {str(e)}")
            print(f"DEBUG - Full traceback: {error_details}")
            return {
                "success": False,
                "error": str(e),
                "error_details": error_details,
                "message": f"I encountered an error while processing your request: {str(e)}"
            }
    
    def _build_context(self, user_profile: Dict[str, Any], context: Optional[Dict[str, Any]], budget_limit: float) -> str:
        """Build context information for the agent."""
        context_parts = []
        
        # User profile context
        if user_profile:
            context_parts.append(f"User Profile:")
            context_parts.append(f"- Budget limit: ${budget_limit}")
            if user_profile.get("diet"):
                context_parts.append(f"- Dietary preference: {user_profile['diet']}")
            if user_profile.get("allergies"):
                context_parts.append(f"- Allergies: {', '.join(user_profile['allergies'])}")
            if user_profile.get("preferred_cuisines"):
                context_parts.append(f"- Preferred cuisines: {', '.join(user_profile['preferred_cuisines'])}")
        
        # Additional context
        if context:
            if context.get("meal_plan"):
                context_parts.append(f"Current meal plan: {context['meal_plan']}")
            if context.get("ingredients_needed"):
                context_parts.append(f"Ingredients needed: {', '.join(context['ingredients_needed'])}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available."
    
    def _handle_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        session_id: str,
        user_id: str,
        budget_limit: float
    ) -> Dict[str, Any]:
        """Handle tool calls from the agent."""
        try:
            # With Strands Agent, tool execution happens internally via @tool.
            # This method remains for compatibility but is not used now.
            return {"success": True, "message": "Tools executed", "session_id": session_id}
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "I encountered an error while processing the tools. Please try again."
            }
    
    def _format_tool_result(self, tool_name: str, result: Dict[str, Any], budget_limit: float) -> str:
        """Format tool result for the agent."""
        if tool_name == "search_products":
            products = result.get("products", [])
            if products:
                product_list = []
                for product in products[:5]:  # Show top 5 results
                    name = product.get("name", "Unknown")
                    price = product.get("price", 0)
                    available = "✅" if product.get("in_stock", False) else "❌"
                    product_list.append(f"- {name}: ${price:.2f} {available}")
                return f"Found {len(products)} products:\n" + "\n".join(product_list)
            else:
                return "No products found matching your search."
        
        elif tool_name == "check_product_availability":
            if result.get("available"):
                product = result.get("product", {})
                name = product.get("name", "Product")
                price = product.get("price", 0)
                return f"✅ {name} is available for ${price:.2f}"
            else:
                return f"❌ {result.get('message', 'Product not available')}"
        
        elif tool_name == "find_product_substitutes":
            substitutes = result.get("substitutes", [])
            if substitutes:
                sub_list = []
                for sub in substitutes[:3]:  # Show top 3 substitutes
                    name = sub.get("name", "Unknown")
                    price = sub.get("price", 0)
                    available = "✅" if sub.get("in_stock", False) else "❌"
                    sub_list.append(f"- {name}: ${price:.2f} {available}")
                return f"Found {len(substitutes)} substitutes:\n" + "\n".join(sub_list)
            else:
                return "No suitable substitutes found."
        
        elif tool_name == "calculate_cart_total":
            total = result.get("total", 0)
            items = result.get("items", [])
            budget_status = "✅ Within budget" if total <= budget_limit else f"⚠️ Over budget by ${total - budget_limit:.2f}"
            return f"Cart total: ${total:.2f} ({budget_status})\nItems: {len(items)}"
        
        elif tool_name == "get_products_by_category":
            products = result.get("products", [])
            if products:
                product_list = []
                for product in products[:5]:
                    name = product.get("name", "Unknown")
                    price = product.get("price", 0)
                    available = "✅" if product.get("in_stock", False) else "❌"
                    product_list.append(f"- {name}: ${price:.2f} {available}")
                return f"Found {len(products)} products in {result.get('category', 'category')}:\n" + "\n".join(product_list)
            else:
                return f"No products found in {result.get('category', 'category')} category."
        
        else:
            # Generic formatting for other tools
            if result.get("success"):
                return result.get("message", "Tool executed successfully")
            else:
                return result.get("error", "Tool execution failed")
    
    def create_grocery_list(
        self,
        ingredients: List[str],
        user_id: str,
        session_id: str,
        max_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Create a grocery list from a list of ingredients.
        
        Args:
            ingredients: List of ingredient names
            user_id: User ID for personalization
            session_id: Session ID
            max_budget: Optional budget limit
            
        Returns:
            Grocery list with products and total cost
        """
        try:
            # Get user profile for budget
            user_profile = get_user_profile(user_id) if user_id else {}
            budget_limit = max_budget or float(user_profile.get("budget_limit", 100))
            
            # Search for each ingredient
            found_products = []
            missing_ingredients = []
            
            for ingredient in ingredients:
                # Search for the ingredient
                search_result = execute_catalog_tool("search_products", {"query": ingredient, "limit": 3})
                
                if search_result.get("success") and search_result.get("products"):
                    # Find the best match (first available product)
                    for product in search_result["products"]:
                        if product.get("in_stock", False):
                            found_products.append({
                                "ingredient": ingredient,
                                "product": product,
                                "quantity": 1  # Default quantity
                            })
                            break
                    else:
                        # No available products found
                        missing_ingredients.append(ingredient)
                else:
                    missing_ingredients.append(ingredient)
            
            # Calculate total cost
            total_cost = sum(item["product"]["price"] * item["quantity"] for item in found_products)
            
            # Check if within budget
            within_budget = total_cost <= budget_limit
            
            return {
                "success": True,
                "grocery_list": found_products,
                "missing_ingredients": missing_ingredients,
                "total_cost": total_cost,
                "budget_limit": budget_limit,
                "within_budget": within_budget,
                "message": f"Created grocery list with {len(found_products)} items. Total: ${total_cost:.2f}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create grocery list"
            }
    
    def suggest_substitutions(
        self,
        unavailable_items: List[str],
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Suggest substitutions for unavailable items.
        
        Args:
            unavailable_items: List of unavailable item names
            user_id: User ID for personalization
            session_id: Session ID
            
        Returns:
            Substitution suggestions
        """
        try:
            substitutions = []
            
            for item in unavailable_items:
                # First, try to find the item to get its details
                search_result = execute_catalog_tool("search_products", {"query": item, "limit": 1})
                
                if search_result.get("success") and search_result.get("products"):
                    product = search_result["products"][0]
                    item_id = product.get("item_id")
                    
                    if item_id:
                        # Find substitutes
                        sub_result = execute_catalog_tool("find_product_substitutes", {"item_id": item_id})
                        
                        if sub_result.get("success"):
                            substitutes = sub_result.get("substitutes", [])
                            substitutions.append({
                                "original_item": item,
                                "substitutes": substitutes[:3]  # Top 3 substitutes
                            })
                        else:
                            substitutions.append({
                                "original_item": item,
                                "substitutes": [],
                                "error": "Could not find substitutes"
                            })
                    else:
                        substitutions.append({
                            "original_item": item,
                            "substitutes": [],
                            "error": "Could not find product ID"
                        })
                else:
                    substitutions.append({
                        "original_item": item,
                        "substitutes": [],
                        "error": "Product not found in catalog"
                    })
            
            return {
                "success": True,
                "substitutions": substitutions,
                "message": f"Found substitution suggestions for {len(unavailable_items)} items"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate substitution suggestions"
            }


# Global instance for easy access
grocery_list_agent = GroceryListAgent()


def strands_agent_bedrock(payload):
    """
    Invoke agent with payload
    """
    user_input = payload.get("prompt")
    print(f"User input: {user_input}")
    
    # Use the global agent instance
    agent = grocery_list_agent.get_agent()
    
    # Try different method names for Strands agent
    try:
        response = agent.invoke(user_input)
    except AttributeError:
        try:
            response = agent.run(user_input)
        except AttributeError:
            try:
                response = agent(user_input)
            except Exception:
                response = "Agent is being configured. Please try again."
    return str(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=str)
    args = parser.parse_args()
    payload = {"prompt": args.prompt}
    response = strands_agent_bedrock(payload)
    print(response)