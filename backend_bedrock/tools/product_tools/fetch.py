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
