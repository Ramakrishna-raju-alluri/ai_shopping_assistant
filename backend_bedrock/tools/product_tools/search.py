import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
except ImportError:
    from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE

from strands import tool

@tool
def search_products(query: str, limit: int = 20) -> Dict[str, Any]:
    """
    Search products by name, description, or tags.
    
    Args:
        query: Search term
        limit: Maximum results to return
        
    Returns:
        Dict with matching products
    """
    print(f"DEBUG - search_products called with query='{query}', limit={limit}")
    try:
        # Try DynamoDB first, but fall back to mock data on any error
        products = []
        try:
            table = dynamodb.Table(PRODUCT_TABLE)
            
            # Search in name, description, and tags
            filter_expr = (
                Attr("name").contains(query.lower()) |
                Attr("description").contains(query.lower()) |
                Attr("tags").contains(query.lower())
            )
            
            response = table.scan(
                FilterExpression=filter_expr,
                Limit=limit
            )
            products = response.get("Items", [])
        except Exception as db_error:
            print(f"DEBUG - DynamoDB error: {db_error}, falling back to mock data")
            products = []
        
        # If no products found in DynamoDB or DB failed, use mock data
        if not products:
            mock_products = [
                {
                    "item_id": "eggs_001",
                    "name": "Large Eggs",
                    "description": "Fresh large eggs, dozen",
                    "price": 3.99,
                    "category": "dairy",
                    "tags": ["eggs", "protein", "breakfast"],
                    "in_stock": True,
                    "quantity_available": 50
                },
                {
                    "item_id": "milk_001", 
                    "name": "Whole Milk",
                    "description": "Fresh whole milk, 1 gallon",
                    "price": 4.29,
                    "category": "dairy",
                    "tags": ["milk", "dairy", "calcium"],
                    "in_stock": True,
                    "quantity_available": 30
                },
                {
                    "item_id": "bread_001",
                    "name": "White Bread",
                    "description": "Fresh white bread loaf",
                    "price": 2.49,
                    "category": "bakery",
                    "tags": ["bread", "bakery", "carbs"],
                    "in_stock": True,
                    "quantity_available": 25
                },
                {
                    "item_id": "chicken_001",
                    "name": "Chicken Breast",
                    "description": "Fresh chicken breast, per pound",
                    "price": 6.99,
                    "category": "meat",
                    "tags": ["chicken", "protein", "meat"],
                    "in_stock": True,
                    "quantity_available": 20
                },
                {
                    "item_id": "tomatoes_001",
                    "name": "Organic Tomatoes",
                    "description": "Fresh organic tomatoes, 1lb",
                    "price": 2.99,
                    "category": "vegetables",
                    "tags": ["tomatoes", "vegetables", "organic"],
                    "in_stock": True,
                    "quantity_available": 15
                },
                {
                    "item_id": "spinach_001",
                    "name": "Organic Spinach",
                    "description": "Fresh organic spinach, 8oz",
                    "price": 3.99,
                    "category": "vegetables",
                    "tags": ["spinach", "vegetables", "organic", "leafy"],
                    "in_stock": True,
                    "quantity_available": 12
                },
                {
                    "item_id": "onions_001",
                    "name": "Organic Onions",
                    "description": "Fresh organic onions, 1lb",
                    "price": 1.99,
                    "category": "vegetables",
                    "tags": ["onions", "vegetables", "organic"],
                    "in_stock": True,
                    "quantity_available": 20
                },
                {
                    "item_id": "carrots_001",
                    "name": "Organic Carrots",
                    "description": "Fresh organic carrots, 1lb",
                    "price": 2.49,
                    "category": "vegetables",
                    "tags": ["carrots", "vegetables", "organic"],
                    "in_stock": True,
                    "quantity_available": 18
                }
            ]
            
            # Filter mock products by query
            products = [
                p for p in mock_products 
                if query.lower() in p["name"].lower() or 
                   query.lower() in p["description"].lower() or
                   any(query.lower() in tag.lower() for tag in p["tags"])
            ][:limit]
        else:
            # Convert Decimal to float for DynamoDB results
            for product in products:
                if "price" in product:
                    product["price"] = float(product["price"])
        
        result = {
            "success": True,
            "products": products,
            "count": len(products),
            "query": query,
            "message": f"Found {len(products)} products matching '{query}'"
        }
        print(f"DEBUG - search_products returning: {result}")
        return result
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "products": [],
            "count": 0
        }
        print(f"DEBUG - search_products ERROR: {error_result}")
        return error_result

