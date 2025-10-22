"""
Grocery product search tools for backend_bedrock.

This module provides grocery-specific product search functionality including
availability checking, substitute finding, and enhanced search capabilities.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from boto3.dynamodb.conditions import Attr, Key
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import dependencies with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
    from backend_bedrock.tools.shared.product_catalog import (
        search_products
    )

except ImportError:
    try:
        from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
        from tools.shared.product_catalog import (
            search_products
        )

    except ImportError:
        print("⚠️ Error importing database modules in product search.py")
        #sys.exit(1)
        # Fallback for testing
        # import boto3
        # try:
        #     dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        # except:
        #     dynamodb = None
        # PRODUCT_TABLE = "mock-products2_with_calories"
        # PROMO_TABLE = "mock-promo-table"
        # def search_products(query, limit=20):
        #     return {"success": True, "data": []}
        # def fetch_all_products(limit=100, category=None):
        #     return {"success": True, "data": []}
        # def get_products_by_category(category, limit=50):
        #     return {"success": True, "data": []}
        # def get_user_preferences(user_id):
        #     return {"success": True, "data": {}}


def convert_decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    import decimal
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj





@tool
def find_substitutes(product_id: str, max_price: Optional[float] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Find substitute products for a given item.
    
    Args:
        product_id (str): Original product ID
        max_price (Optional[float]): Optional maximum price for substitutes
        user_id (Optional[str]): User ID for personalized suggestions
        
    Returns:
        Dict[str, Any]: Standardized response with substitute products
    """
    try:
        # Get original product
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.get_item(Key={"item_id": product_id})
        
        if "Item" not in response:
            return {
                'success': False,
                'data': None,
                'message': f"Product {product_id} not found"
            }
        
        original = response["Item"]
        original = convert_decimal_to_float(original)
        
        original_category = original.get("category", "")
        original_tags = original.get("tags", [])
        original_price = float(original.get("price", 0))
        
        # Get user preferences for personalized suggestions
        user_preferences = {}
        # Note: get_user_preferences function was removed, so skipping user preferences
        
        # Build filter expression
        filter_expr = Attr("category").eq(original_category)
        
        # Add price filter
        if max_price:
            filter_expr = filter_expr & Attr("price").lte(max_price)
        else:
            # Default to products within 20% of original price
            max_price = original_price * 1.2
            filter_expr = filter_expr & Attr("price").lte(max_price)
        
        # Exclude the original product
        filter_expr = filter_expr & Attr("item_id").ne(product_id)
        
        # Only include in-stock items
        filter_expr = filter_expr & Attr("in_stock").eq(True)
        
        response = table.scan(FilterExpression=filter_expr)
        candidates = response.get("Items", [])
        candidates = convert_decimal_to_float(candidates)
        
        # Score candidates by various factors
        substitutes = []
        user_allergies = user_preferences.get("allergies", [])
        user_restrictions = user_preferences.get("restrictions", [])
        
        for candidate in candidates:
            candidate_tags = candidate.get("tags", [])
            candidate_name = candidate.get("name", "").lower()
            
            # Calculate tag overlap score
            tag_overlap = len(set(original_tags) & set(candidate_tags))
            
            # Check dietary compatibility
            dietary_compatible = True
            if user_allergies:
                for allergy in user_allergies:
                    if allergy.lower() in candidate_name or allergy.lower() in str(candidate_tags).lower():
                        dietary_compatible = False
                        break
            
            if user_restrictions:
                for restriction in user_restrictions:
                    if restriction.lower() in candidate_name or restriction.lower() in str(candidate_tags).lower():
                        dietary_compatible = False
                        break
            
            # Calculate price difference score (lower is better)
            price_diff = abs(candidate.get("price", 0) - original_price)
            price_score = max(0, 10 - price_diff)  # Score 0-10, higher is better
            
            # Calculate overall score
            overall_score = (tag_overlap * 3) + price_score + (5 if dietary_compatible else 0)
            
            candidate["tag_overlap"] = tag_overlap
            candidate["price_difference"] = price_diff
            candidate["dietary_compatible"] = dietary_compatible
            candidate["substitute_score"] = overall_score
            
            substitutes.append(candidate)
        
        # Sort by overall score (descending)
        substitutes.sort(key=lambda x: -x["substitute_score"])
        
        # Take top 5 substitutes
        top_substitutes = substitutes[:5]
        
        result_data = {
            'original_product': original,
            'substitutes': top_substitutes,
            'total_found': len(substitutes),
            'search_criteria': {
                'max_price': max_price,
                'category': original_category,
                'user_preferences_applied': bool(user_id)
            }
        }
        
        return {
            'success': True,
            'data': result_data,
            'message': f"Found {len(top_substitutes)} substitute products for {original.get('name', product_id)}"
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error finding substitutes: {str(e)}'
        }


@tool
def get_pricing_info(product_id: str) -> Dict[str, Any]:
    """
    Get detailed pricing information for a product.
    
    Args:
        product_id (str): Product ID
        
    Returns:
        Dict[str, Any]: Standardized response with pricing information
    """
    try:
        table = dynamodb.Table(PRODUCT_TABLE)
        response = table.get_item(Key={"item_id": product_id})
        
        if "Item" not in response:
            return {
                'success': False,
                'data': None,
                'message': f"Product {product_id} not found"
            }
        
        product = response["Item"]
        product = convert_decimal_to_float(product)
        
        # Check for promotional pricing
        promo_info = None
        try:
            promo_table = dynamodb.Table(PROMO_TABLE)
            promo_response = promo_table.get_item(Key={"item_id": product_id})
            if "Item" in promo_response:
                promo_info = convert_decimal_to_float(promo_response["Item"])
        except Exception:
            # Promo table might not exist or be accessible
            pass
        
        regular_price = float(product.get("price", 0))
        current_price = regular_price
        
        pricing_info = {
            'product_id': product_id,
            'product_name': product.get('name', ''),
            'regular_price': regular_price,
            'current_price': current_price,
            'currency': 'USD',
            'has_promotion': bool(promo_info),
            'promotion_details': promo_info,
            'price_per_unit': regular_price,
            'unit': product.get('unit', 'each')
        }
        
        # Apply promotional pricing if available
        if promo_info:
            promo_price = float(promo_info.get("promo_price", regular_price))
            if promo_price < regular_price:
                pricing_info['current_price'] = promo_price
                pricing_info['savings'] = regular_price - promo_price
                pricing_info['discount_percentage'] = ((regular_price - promo_price) / regular_price) * 100
        
        message = f"Price for {product.get('name', product_id)}: ${current_price:.2f}"
        if promo_info and pricing_info.get('savings', 0) > 0:
            message += f" (Save ${pricing_info['savings']:.2f})"
        
        return {
            'success': True,
            'data': pricing_info,
            'message': message
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting pricing info: {str(e)}'
        }


@tool
def search_grocery_products(query: str, category: Optional[str] = None, max_price: Optional[float] = None, 
                           in_stock_only: bool = True, limit: int = 20) -> Dict[str, Any]:
    """
    Enhanced grocery product search with filtering options.
    
    Args:
        query (str): Search term
        category (Optional[str]): Filter by category
        max_price (Optional[float]): Maximum price filter
        in_stock_only (bool): Only return in-stock items
        limit (int): Maximum results to return
        
    Returns:
        Dict[str, Any]: Standardized response with filtered search results
    """
    try:
        # Start with basic search
        if category:
            # Search within category
            search_result = get_products_by_category(category, limit=limit*2)  # Get more to filter
        else:
            # General search
            search_result = search_products(query, limit=limit*2)  # Get more to filter
        
        if not search_result['success']:
            return search_result
        
        products = search_result['data']
        
        # Apply additional filters
        filtered_products = []
        
        for product in products:
            # Price filter
            if max_price and float(product.get('price', 0)) > max_price:
                continue
            
            # Stock filter
            if in_stock_only and not product.get('in_stock', False):
                continue
            
            # Query relevance (if not searching by category)
            if not category:
                product_name = product.get('name', '').lower()
                product_desc = product.get('description', '').lower()
                product_tags = [str(tag).lower() for tag in product.get('tags', [])]
                
                query_lower = query.lower()
                
                # Calculate relevance score
                relevance_score = 0
                if query_lower in product_name:
                    relevance_score += 10
                if query_lower in product_desc:
                    relevance_score += 5
                if any(query_lower in tag for tag in product_tags):
                    relevance_score += 3
                
                product['relevance_score'] = relevance_score
                
                # Only include if somewhat relevant
                if relevance_score > 0:
                    filtered_products.append(product)
            else:
                filtered_products.append(product)
        
        # Sort by relevance if not category search
        if not category:
            filtered_products.sort(key=lambda x: -x.get('relevance_score', 0))
        
        # Limit results
        final_products = filtered_products[:limit]
        
        search_summary = {
            'products': final_products,
            'total_found': len(final_products),
            'search_query': query,
            'filters_applied': {
                'category': category,
                'max_price': max_price,
                'in_stock_only': in_stock_only
            },
            'total_before_filtering': len(products)
        }
        
        return {
            'success': True,
            'data': search_summary,
            'message': f"Found {len(final_products)} grocery products matching your search"
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error searching grocery products: {str(e)}'
        }





# Legacy compatibility functions for existing code
def check_product_availability_legacy(item_id: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing product tools.
    """
    result = check_availability(item_id)
    
    if result['success']:
        data = result['data']
        return {
            "success": True,
            "available": data['available'],
            "product": data['product_details'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "available": False
        }


def find_product_substitutes_legacy(item_id: str, max_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing product tools.
    """
    result = find_substitutes(item_id, max_price)
    
    if result['success']:
        data = result['data']
        return {
            "success": True,
            "original_product": data['original_product'],
            "substitutes": data['substitutes'],
            "count": data['total_found'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "substitutes": []
        }


def check_item_availability_legacy(item_name: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility with existing cart manager.
    """
    result = check_item_availability_by_name(item_name)
    
    if result['success']:
        data = result['data']
        return {
            "success": True,
            "available_products": data['available_products'],
            "out_of_stock_products": data['out_of_stock_products'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "message": result['message']
        }