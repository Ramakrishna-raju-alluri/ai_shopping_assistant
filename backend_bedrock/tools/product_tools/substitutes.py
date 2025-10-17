import json
from typing import List, Dict, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
except ImportError:
    from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE

from strands import tool
@tool
def find_product_substitutes(item_id: str, max_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Find substitute products for a given item.
    
    Args:
        item_id: Original product ID
        max_price: Optional maximum price for substitutes
        
    Returns:
        Dict with substitute products
    """
    try:
        # Get original product
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.get_item(Key={"item_id": item_id})
        
        if "Item" not in response:
            return {
                "success": False,
                "error": f"Product {item_id} not found"
            }
        
        original = response["Item"]
        original_category = original.get("category", "")
        original_tags = original.get("tags", [])
        original_price = float(original.get("price", 0))
        
        # Find products in same category with similar tags
        filter_expr = Attr("category").eq(original_category)
        
        # Add price filter if specified
        if max_price:
            filter_expr = filter_expr & Attr("price").lte(max_price)
        else:
            # Default to products within 20% of original price
            max_price = original_price * 1.2
            filter_expr = filter_expr & Attr("price").lte(max_price)
        
        # Exclude the original product
        filter_expr = filter_expr & Attr("item_id").ne(item_id)
        
        response = table.scan(FilterExpression=filter_expr)
        candidates = response.get("Items", [])
        
        # Score candidates by tag overlap
        substitutes = []
        for candidate in candidates:
            candidate_tags = candidate.get("tags", [])
            tag_overlap = len(set(original_tags) & set(candidate_tags))
            candidate["price"] = float(candidate.get("price", 0))
            candidate["tag_overlap"] = tag_overlap
            substitutes.append(candidate)
        
        # Sort by tag overlap and price
        substitutes.sort(key=lambda x: (-x["tag_overlap"], x["price"]))
        
        return {
            "success": True,
            "original_product": original,
            "substitutes": substitutes[:5],  # Top 5 substitutes
            "count": len(substitutes),
            "message": f"Found {len(substitutes)} potential substitutes for {item_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "substitutes": []
        }
