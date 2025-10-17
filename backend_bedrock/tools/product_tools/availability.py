import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
except ImportError:
    from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE

from strands import tool
@tool
def check_product_availability(item_id: str) -> Dict[str, Any]:
    """
    Check if a specific product is available and get stock info.
    
    Args:
        item_id: Product ID to check
        
    Returns:
        Dict with availability status and product details
    """
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.get_item(Key={"item_id": item_id})
        
        if "Item" not in response:
            return {
                "success": False,
                "available": False,
                "message": f"Product {item_id} not found"
            }
        
        product = response["Item"]
        if "price" in product:
            product["price"] = float(product["price"])
        
        is_available = product.get("in_stock", False)
        
        return {
            "success": True,
            "available": is_available,
            "product": product,
            "message": f"Product {item_id} is {'available' if is_available else 'out of stock'}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "available": False
        }
