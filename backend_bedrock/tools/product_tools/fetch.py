import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
except ImportError:
    from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE

from strands import tool

@tool
def fetch_all_products(limit: int = 100, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch products from catalog with optional filtering.
    
    Args:
        limit: Maximum number of products to return
        category: Optional category filter
        
    Returns:
        Dict with products list and metadata
    """
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        scan_kwargs = {"Limit": limit}
        if category:
            scan_kwargs["FilterExpression"] = Attr("category").eq(category.lower())
        
        response = table.scan(**scan_kwargs)
        products = response.get("Items", [])
        
        # Convert Decimal to float for JSON serialization
        for product in products:
            if "price" in product:
                product["price"] = float(product["price"])
        
        return {
            "success": True,
            "products": products,
            "count": len(products),
            "message": f"Found {len(products)} products"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": [],
            "count": 0
        }

@tool
def get_products_by_category(category: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get all products in a specific category.
    
    Args:
        category: Product category
        limit: Maximum results
        
    Returns:
        Dict with products in category
    """
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        
        response = table.scan(
            FilterExpression=Attr("category").eq(category.lower()),
            Limit=limit
        )
        products = response.get("Items", [])
        
        # If no products found in DynamoDB, use mock data
        if not products:
            mock_products = {
                "vegetables": [
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
                ],
                "dairy": [
                    {
                        "item_id": "milk_001",
                        "name": "Whole Milk",
                        "description": "Fresh whole milk, 1 gallon",
                        "price": 4.29,
                        "category": "dairy",
                        "tags": ["milk", "dairy", "calcium"],
                        "in_stock": True,
                        "quantity_available": 30
                    }
                ],
                "meat": [
                    {
                        "item_id": "chicken_001",
                        "name": "Chicken Breast",
                        "description": "Fresh chicken breast, per pound",
                        "price": 6.99,
                        "category": "meat",
                        "tags": ["chicken", "protein", "meat"],
                        "in_stock": True,
                        "quantity_available": 20
                    }
                ]
            }
            
            products = mock_products.get(category.lower(), [])[:limit]
        
        # Convert Decimal to float
        for product in products:
            if "price" in product:
                product["price"] = float(product["price"])
        
        return {
            "success": True,
            "category": category,
            "products": products,
            "count": len(products),
            "message": f"Found {len(products)} products in {category} category"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "products": [],
            "count": 0
        }
