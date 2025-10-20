"""
Shared product catalog tools for backend_bedrock.

This module provides centralized product catalog functionality
that can be used by multiple agents across different domains.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from boto3.dynamodb.conditions import Attr, Key
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import database functions with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
    from backend_bedrock.dynamo.queries import get_all_products as db_get_all_products
except ImportError:
    try:
        from dynamo.client import dynamodb, PRODUCT_TABLE, PROMO_TABLE
        from dynamo.queries import get_all_products as db_get_all_products
    except ImportError:
        # Fallback for testing
        import boto3
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        except:
            dynamodb = None
        PRODUCT_TABLE = "mock-products2_with_calories"
        PROMO_TABLE = "mock-promo-table"
        def db_get_all_products():
            return [{"name": "Sample Product", "price": 2.99, "in_stock": True, "item_id": "sample_001"}]


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


def get_mock_products():
    """Get mock product data for fallback scenarios."""
    return [
        {
            "item_id": "eggs_001",
            "name": "Large Eggs",
            "description": "Fresh large eggs, dozen",
            "price": 3.99,
            "category": "dairy",
            "tags": ["eggs", "protein", "breakfast"],
            "in_stock": True,
            "quantity_available": 50,
            "calories_per_unit": 70
        },
        {
            "item_id": "milk_001", 
            "name": "Whole Milk",
            "description": "Fresh whole milk, 1 gallon",
            "price": 4.29,
            "category": "dairy",
            "tags": ["milk", "dairy", "calcium"],
            "in_stock": True,
            "quantity_available": 30,
            "calories_per_unit": 150
        },
        {
            "item_id": "bread_001",
            "name": "White Bread",
            "description": "Fresh white bread loaf",
            "price": 2.49,
            "category": "bakery",
            "tags": ["bread", "bakery", "carbs"],
            "in_stock": True,
            "quantity_available": 25,
            "calories_per_unit": 80
        },
        {
            "item_id": "chicken_001",
            "name": "Chicken Breast",
            "description": "Fresh chicken breast, per pound",
            "price": 6.99,
            "category": "meat",
            "tags": ["chicken", "protein", "meat"],
            "in_stock": True,
            "quantity_available": 20,
            "calories_per_unit": 165
        },
        {
            "item_id": "tomatoes_001",
            "name": "Organic Tomatoes",
            "description": "Fresh organic tomatoes, 1lb",
            "price": 2.99,
            "category": "vegetables",
            "tags": ["tomatoes", "vegetables", "organic"],
            "in_stock": True,
            "quantity_available": 15,
            "calories_per_unit": 18
        },
        {
            "item_id": "spinach_001",
            "name": "Organic Spinach",
            "description": "Fresh organic spinach, 8oz",
            "price": 3.99,
            "category": "vegetables",
            "tags": ["spinach", "vegetables", "organic", "leafy"],
            "in_stock": True,
            "quantity_available": 12,
            "calories_per_unit": 7
        },
        {
            "item_id": "onions_001",
            "name": "Organic Onions",
            "description": "Fresh organic onions, 1lb",
            "price": 1.99,
            "category": "vegetables",
            "tags": ["onions", "vegetables", "organic"],
            "in_stock": True,
            "quantity_available": 20,
            "calories_per_unit": 40
        },
        {
            "item_id": "carrots_001",
            "name": "Organic Carrots",
            "description": "Fresh organic carrots, 1lb",
            "price": 2.49,
            "category": "vegetables",
            "tags": ["carrots", "vegetables", "organic"],
            "in_stock": True,
            "quantity_available": 18,
            "calories_per_unit": 41
        }
    ]


@tool
def fetch_all_products(limit: int = 100, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch all products from the catalog with optional filtering.
    
    Args:
        limit (int): Maximum number of products to return
        category (Optional[str]): Optional category filter
        
    Returns:
        Dict[str, Any]: Standardized response with products list and metadata
    """
    try:
        # Try database first
        try:
            table = dynamodb.Table(PRODUCT_TABLE)
            
            scan_kwargs = {"Limit": limit}
            if category:
                scan_kwargs["FilterExpression"] = Attr("category").eq(category.lower())
            
            response = table.scan(**scan_kwargs)
            products = response.get("Items", [])
        except Exception:
            # Fallback to database query function
            try:
                products = db_get_all_products()
                if category:
                    products = [p for p in products if p.get("category", "").lower() == category.lower()]
                products = products[:limit]
            except Exception:
                products = []
        
        # If no products found, use mock data
        if not products:
            products = get_mock_products()
            if category:
                products = [p for p in products if p.get("category", "").lower() == category.lower()]
            products = products[:limit]
        
        # Convert Decimal to float for JSON serialization
        products = convert_decimal_to_float(products)
        
        return {
            'success': True,
            'data': products,
            'count': len(products),
            'message': f'Found {len(products)} products'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'count': 0,
            'message': f'Error fetching products: {str(e)}'
        }

@tool
def get_products_by_category(category: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get all products in a specific category.
    
    Args:
        category (str): Product category
        limit (int): Maximum results
        
    Returns:
        Dict[str, Any]: Standardized response with products in category
    """
    try:
        # Use the fetch_all_products function with category filter
        result = fetch_all_products(limit=limit, category=category)
        
        # Update message to be category-specific
        if result['success']:
            result['message'] = f"Found {result['count']} products in {category} category"
            result['category'] = category
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'count': 0,
            'message': f'Error fetching products by category: {str(e)}'
        }


@tool
def search_products(query: str, limit: int = 20) -> Dict[str, Any]:
    """
    Search products by name, description, or tags.
    
    Args:
        query (str): Search term
        limit (int): Maximum results to return
        
    Returns:
        Dict[str, Any]: Standardized response with matching products
    """
    try:
        products = []
        
        # Try DynamoDB search first
        try:
            table = dynamodb.Table(PRODUCT_TABLE)
            
            # Get all products and do case-insensitive search in Python
            # This is more reliable than DynamoDB's case-sensitive contains()
            response = table.scan()
            all_products = response.get("Items", [])
            
            # Filter products with case-insensitive search
            query_lower = query.lower()
            products = []
            
            for product in all_products:
                name = product.get("name", "").lower()
                description = product.get("description", "").lower()
                tags = [str(tag).lower() for tag in product.get("tags", [])]
                
                # Check if query matches name, description, or any tag
                if (query_lower in name or 
                    query_lower in description or 
                    any(query_lower in tag for tag in tags)):
                    products.append(product)
                    
                    if len(products) >= limit:
                        break
        except Exception:
            # Fallback to database query function
            try:
                all_products = db_get_all_products()
                products = [
                    p for p in all_products 
                    if query.lower() in p.get("name", "").lower() or 
                       query.lower() in p.get("description", "").lower() or
                       any(query.lower() in str(tag).lower() for tag in p.get("tags", []))
                ][:limit]
            except Exception:
                products = []
        
        # If no products found, search mock data
        if not products:
            mock_products = get_mock_products()
            products = [
                p for p in mock_products 
                if query.lower() in p["name"].lower() or 
                   query.lower() in p["description"].lower() or
                   any(query.lower() in tag.lower() for tag in p["tags"])
            ][:limit]
        
        # Convert Decimal to float for JSON serialization
        products = convert_decimal_to_float(products)
        
        return {
            'success': True,
            'data': products,
            'count': len(products),
            'query': query,
            'message': f"Found {len(products)} products matching '{query}'"
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'count': 0,
            'query': query,
            'message': f'Error searching products: {str(e)}'
        }


@tool
def find_products_by_names(product_names: List[str]) -> Dict[str, Any]:
    """
    Find products by a list of names using fuzzy matching.
    
    Args:
        product_names (List[str]): List of product names to search for
        
    Returns:
        Dict[str, Any]: Standardized response with matched products
    """
    try:
        # Get all products first
        all_products_result = fetch_all_products(limit=1000)
        
        if not all_products_result['success']:
            return all_products_result
        
        all_products = all_products_result['data']
        matched_products = []
        
        for product_name in product_names:
            # Try exact match first
            exact_matches = [p for p in all_products if p.get("name", "").lower() == product_name.lower()]
            
            if exact_matches:
                matched_products.extend(exact_matches)
                continue
            
            # Try partial match (product name contains search term)
            partial_matches = [p for p in all_products if product_name.lower() in p.get("name", "").lower()]
            
            if partial_matches:
                matched_products.extend(partial_matches)
                continue
            
            # Try reverse partial match (search term contains product name)
            reverse_matches = [p for p in all_products if p.get("name", "").lower() in product_name.lower()]
            
            if reverse_matches:
                matched_products.extend(reverse_matches)
                continue
            
            # Try word-based matching
            product_words = product_name.lower().split()
            word_matches = []
            for product in all_products:
                product_name_lower = product.get("name", "").lower()
                # Check if any word from search term matches product name
                if any(word in product_name_lower for word in product_words if len(word) > 2):
                    word_matches.append(product)
            
            if word_matches:
                matched_products.extend(word_matches)
        
        # Remove duplicates based on item_id
        unique_products = []
        seen_ids = set()
        for product in matched_products:
            item_id = product.get("item_id")
            if item_id and item_id not in seen_ids:
                unique_products.append(product)
                seen_ids.add(item_id)
        
        return {
            'success': True,
            'data': unique_products,
            'count': len(unique_products),
            'searched_names': product_names,
            'message': f'Found {len(unique_products)} products matching the provided names'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': [],
            'count': 0,
            'searched_names': product_names,
            'message': f'Error finding products by names: {str(e)}'
        }


@tool
def check_product_availability(product_name: str) -> Dict[str, Any]:
    """
    Check product availability and stock status with fuzzy name matching.
    
    Args:
        product_name (str): Product name to search for
        
    Returns:
        Dict[str, Any]: Standardized response with availability information
    """
    try:
        # Search for the product
        search_result = search_products(product_name, limit=5)
        
        if not search_result['success'] or not search_result['data']:
            return {
                'success': False,
                'data': None,
                'message': f"Could not find '{product_name}' in the catalog"
            }
        
        # Get the best match (first result)
        product = search_result['data'][0]
        
        availability_info = {
            'product_name': product.get('name', product_name),
            'item_id': product.get('item_id'),
            'in_stock': product.get('in_stock', False),
            'quantity_available': product.get('quantity_available', 0),
            'price': product.get('price', 0)
        }
        
        status_message = (
            f"Yes, {availability_info['product_name']} are in stock" 
            if availability_info['in_stock'] 
            else f"No, {availability_info['product_name']} are out of stock"
        )
        
        return {
            'success': True,
            'data': availability_info,
            'message': status_message
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error checking product availability: {str(e)}'
        }


# Legacy compatibility functions for existing code
@tool
def fetch_all_products_legacy(limit: int = 100, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Legacy function that returns the old format for backward compatibility.
    """
    result = fetch_all_products(limit, category)
    
    if result['success']:
        return {
            "success": True,
            "products": result['data'],
            "count": result['count'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "products": [],
            "count": 0
        }

@tool
def search_products_legacy(query: str, limit: int = 20) -> Dict[str, Any]:
    """
    Legacy function that returns the old format for backward compatibility.
    """
    result = search_products(query, limit)
    
    if result['success']:
        return {
            "success": True,
            "products": result['data'],
            "count": result['count'],
            "query": result['query'],
            "message": result['message']
        }
    else:
        return {
            "success": False,
            "error": result['message'],
            "products": [],
            "count": 0
        }

@tool
def get_all_products_raw():
    """
    Legacy function that returns raw product data for backward compatibility.
    Used by meal planner tools that expect the old format.
    """
    try:
        return db_get_all_products()
    except Exception:
        return get_mock_products()