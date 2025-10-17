import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
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
    try:
        # First try DynamoDB
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
        
        # If no products found in DynamoDB, use mock data
        if not products:
            mock_products = [
                {
                    "id": "eggs_001",
                    "name": "Large Eggs",
                    "description": "Fresh large eggs, dozen",
                    "price": 3.99,
                    "category": "dairy",
                    "tags": ["eggs", "protein", "breakfast"],
                    "in_stock": True,
                    "quantity_available": 50
                },
                {
                    "id": "milk_001", 
                    "name": "Whole Milk",
                    "description": "Fresh whole milk, 1 gallon",
                    "price": 4.29,
                    "category": "dairy",
                    "tags": ["milk", "dairy", "calcium"],
                    "in_stock": True,
                    "quantity_available": 30
                },
                {
                    "id": "bread_001",
                    "name": "White Bread",
                    "description": "Fresh white bread loaf",
                    "price": 2.49,
                    "category": "bakery",
                    "tags": ["bread", "bakery", "carbs"],
                    "in_stock": True,
                    "quantity_available": 25
                },
                {
                    "id": "chicken_001",
                    "name": "Chicken Breast",
                    "description": "Fresh chicken breast, per pound",
                    "price": 6.99,
                    "category": "meat",
                    "tags": ["chicken", "protein", "meat"],
                    "in_stock": True,
                    "quantity_available": 20
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
        
        return {
            "success": True,
            "products": products,
            "count": len(products),
            "query": query,
            "message": f"Found {len(products)} products matching '{query}'"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": [],
            "count": 0
        }

