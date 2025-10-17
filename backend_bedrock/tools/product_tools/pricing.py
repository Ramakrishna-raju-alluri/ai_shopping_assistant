import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
except ImportError:
    from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE

from strands import tool

@tool
def get_product_price(item_id: str) -> Dict[str, Any]:
    """
    Get the current price of a specific product.
    
    Args:
        item_id: Product ID
        
    Returns:
        Dict with price information
    """
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.get_item(Key={"item_id": item_id})
        
        if "Item" not in response:
            return {
                "success": False,
                "error": f"Product {item_id} not found"
            }
        
        product = response["Item"]
        price = float(product.get("price", 0))
        promo = product.get("promo", False)
        
        return {
            "success": True,
            "item_id": item_id,
            "price": price,
            "promo": promo,
            "currency": "USD",
            "message": f"Price for {item_id}: ${price:.2f}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@tool
def calculate_cart_total(item_quantities: Dict[str, int]) -> Dict[str, Any]:
    """
    Calculate total cost for a cart of items.
    
    Args:
        item_quantities: Dict of item_id -> quantity
        
    Returns:
        Dict with total cost and breakdown
    """
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        total = 0.0
        items = []
        
        for item_id, quantity in item_quantities.items():
            response = table.get_item(Key={"item_id": item_id})
            if "Item" in response:
                product = response["Item"]
                price = float(product.get("price", 0))
                item_total = price * quantity
                total += item_total
                
                items.append({
                    "item_id": item_id,
                    "name": product.get("name", ""),
                    "price": price,
                    "quantity": quantity,
                    "item_total": item_total
                })
        
        return {
            "success": True,
            "total": total,
            "items": items,
            "item_count": len(items),
            "message": f"Cart total: ${total:.2f}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total": 0.0
        }
