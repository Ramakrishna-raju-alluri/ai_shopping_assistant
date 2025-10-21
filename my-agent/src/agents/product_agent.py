"""
Product Information Agent - Handles product stock, availability, and pricing queries
"""
import sys
from pathlib import Path
from strands import Agent, tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from tools.db_tool import find_product_stock, get_products_by_names

PRODUCT_AGENT_PROMPT = """
You are a specialized product information assistant for Coles supermarket. 
Your role is to help customers with product-related queries including:

1. **Stock Availability**: Check if products are currently in stock
2. **Product Information**: Provide details about products in the catalog
3. **Product Search**: Help find products by name or category

Guidelines:
- Always use the available tools to get accurate, real-time information
- Be helpful and provide clear information about product availability
- If a product isn't found, suggest checking the spelling or similar alternatives
- Provide concise, useful responses focused on product information

Available Tools:
- find_product_stock: Check if a specific product is in stock
- get_products_by_names: Get multiple products by name with fuzzy matching
"""

@tool
def product_agent(user_id: str, query: str) -> str:
    """
    Use this agent for product-related queries like stock availability, product information, and pricing.
    Args:
        user_id: The ID of the user making the request
        query: The user's product-related query, e.g., "Are bananas in stock?"
    """
    agent = Agent(
        model="amazon.nova-lite-v1:0",
        system_prompt=PRODUCT_AGENT_PROMPT,
        tools=[
            find_product_stock,
            get_products_by_names
        ]
    )
    
    # Combine user context with query
    combined_prompt = f"User ID: {user_id}. Product Query: {query}"
    response = agent(combined_prompt)
    return str(response)

def main():
    """Test the product agent"""
    user_id = "test-user-123"
    query = "Are bananas in stock?"
    result = product_agent(user_id, query)
    print(result)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=str, default="test-user-123", help="User ID")
    parser.add_argument("--query", type=str, default="Are bananas in stock?", help="Product query")
    args = parser.parse_args()
    
    result = product_agent(args.user_id, args.query)
    print(result)