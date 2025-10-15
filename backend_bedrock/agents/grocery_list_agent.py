from strands import Agent, tool
import argparse
import json
import boto3
from typing import Dict, Any, List, Optional
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

# Get boto session
boto_session = boto3.Session()
region = boto_session.region_name

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=region)
PRODUCT_TABLE = 'coles-products'

@tool
def lookup_in_catalog(item_name: str) -> str:
    """Look up an item in the product catalog and return detailed information"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Get all products for fuzzy matching
        response = table.scan()
        all_products = response.get("Items", [])
        
        # Try exact match first
        exact_matches = [p for p in all_products if p.get("name", "").lower() == item_name.lower()]
        
        if exact_matches:
            product = exact_matches[0]
            return json.dumps({
                "found": True,
                "name": product.get("name", "Unknown"),
                "price": product.get("price", 0),
                "in_stock": product.get("in_stock", True),
                "category": product.get("category", "Unknown"),
                "description": product.get("description", ""),
                "tags": product.get("tags", [])
            })
        
        # Try fuzzy matching
        fuzzy_matches = []
        for product in all_products:
            product_name = product.get("name", "").lower()
            if item_name.lower() in product_name or product_name in item_name.lower():
                fuzzy_matches.append(product)
        
        if fuzzy_matches:
            product = fuzzy_matches[0]  # Return first match
            return json.dumps({
                "found": True,
                "name": product.get("name", "Unknown"),
                "price": product.get("price", 0),
                "in_stock": product.get("in_stock", True),
                "category": product.get("category", "Unknown"),
                "description": product.get("description", ""),
                "tags": product.get("tags", [])
            })
        
        return json.dumps({"found": False, "message": f"Item '{item_name}' not found in catalog"})
        
    except Exception as e:
        return json.dumps({"found": False, "error": str(e)})

@tool
def get_item_price(item_name: str) -> str:
    """Get the price of a specific item in the catalog"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Get all products for fuzzy matching
        response = table.scan()
        all_products = response.get("Items", [])
        
        # Try exact match first
        exact_matches = [p for p in all_products if p.get("name", "").lower() == item_name.lower()]
        
        if exact_matches:
            product = exact_matches[0]
            price = product.get("price", 0)
            return f"${price:.2f}" if price else "Price not available"
        
        # Try fuzzy matching
        for product in all_products:
            product_name = product.get("name", "").lower()
            if item_name.lower() in product_name or product_name in item_name.lower():
                price = product.get("price", 0)
                return f"${price:.2f}" if price else "Price not available"
        
        return f"Item '{item_name}' not found in catalog"
        
    except Exception as e:
        return f"Error retrieving price: {str(e)}"

@tool
def get_item_availability(item_name: str) -> str:
    """Get the availability status of a specific item in the catalog"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Get all products for fuzzy matching
        response = table.scan()
        all_products = response.get("Items", [])
        
        # Try exact match first
        exact_matches = [p for p in all_products if p.get("name", "").lower() == item_name.lower()]
        
        if exact_matches:
            product = exact_matches[0]
            in_stock = product.get("in_stock", True)
            return "In stock" if in_stock else "Out of stock"
        
        # Try fuzzy matching
        for product in all_products:
            product_name = product.get("name", "").lower()
            if item_name.lower() in product_name or product_name in item_name.lower():
                in_stock = product.get("in_stock", True)
                return "In stock" if in_stock else "Out of stock"
        
        return f"Item '{item_name}' not found in catalog"
        
    except Exception as e:
        return f"Error checking availability: {str(e)}"

@tool
def create_grocery_list(list_name: str, items: List[str]) -> str:
    """Create a new grocery list with specified items"""
    try:
        # Validate items against catalog
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.scan()
        all_products = response.get("Items", [])
        
        validated_items = []
        missing_items = []
        
        for item in items:
            # Try to find the item in catalog
            found = False
            for product in all_products:
                product_name = product.get("name", "").lower()
                if item.lower() == product_name or item.lower() in product_name:
                    validated_items.append({
                        "name": product.get("name"),
                        "price": product.get("price", 0),
                        "in_stock": product.get("in_stock", True),
                        "category": product.get("category", "Unknown")
                    })
                    found = True
                    break
            
            if not found:
                missing_items.append(item)
        
        result = {
            "list_name": list_name,
            "items": validated_items,
            "total_items": len(validated_items),
            "estimated_total": sum(item.get("price", 0) for item in validated_items)
        }
        
        if missing_items:
            result["missing_items"] = missing_items
            result["message"] = f"Created list '{list_name}' with {len(validated_items)} items. Note: {len(missing_items)} items not found in catalog."
        else:
            result["message"] = f"Successfully created grocery list '{list_name}' with {len(validated_items)} items."
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to create grocery list: {str(e)}"})

@tool
def search_items_by_category(category: str) -> str:
    """Search for items in a specific category"""
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        # Search for products in the specified category
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('category').contains(category.lower())
        )
        
        products = response.get("Items", [])
        
        if not products:
            return json.dumps({"found": False, "message": f"No items found in category '{category}'"})
        
        # Format the results
        items = []
        for product in products[:10]:  # Limit to 10 items
            items.append({
                "name": product.get("name", "Unknown"),
                "price": product.get("price", 0),
                "in_stock": product.get("in_stock", True),
                "description": product.get("description", "")
            })
        
        return json.dumps({
            "found": True,
            "category": category,
            "items": items,
            "total_found": len(products)
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to search category: {str(e)}"})
app = BedrockAgentCoreApp()

model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
model = BedrockModel(
    model_id=model_id,
)

# Enhanced system prompt for grocery list agent
system_prompt = """You are a helpful grocery list assistant for Coles supermarket. You can help customers with:

1. **Product Information**: Look up items in the catalog, check prices, and availability
2. **Grocery List Creation**: Help create organized grocery lists with items from the catalog
3. **Category Browsing**: Search for items by category (dairy, produce, meat, etc.)
4. **Budget Planning**: Help estimate costs for grocery lists
5. **Stock Checking**: Verify if items are currently in stock

Available tools:
- lookup_in_catalog(item_name): Get detailed product information
- get_item_price(item_name): Get the price of a specific item
- get_item_availability(item_name): Check if an item is in stock
- create_grocery_list(list_name, items): Create a validated grocery list
- search_items_by_category(category): Find items in a specific category

Guidelines:
- Always use the tools to get accurate, real-time information from the catalog
- Be helpful and friendly in your responses
- If an item isn't found, suggest similar alternatives
- When creating lists, validate all items against the catalog
- Provide clear pricing and availability information
- Organize suggestions logically (by category, aisle, etc.)

Example interactions:
- "What's the price of organic milk?" → Use get_item_price tool
- "Create a breakfast list with eggs, bread, and milk" → Use create_grocery_list tool
- "Show me dairy products" → Use search_items_by_category tool
- "Is almond milk in stock?" → Use get_item_availability tool"""

agent = Agent(
    model=model,
    system_prompt=system_prompt
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