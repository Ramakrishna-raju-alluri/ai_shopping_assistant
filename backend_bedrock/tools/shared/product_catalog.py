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

from rapidfuzz import fuzz, process
from nltk.stem import WordNetLemmatizer
import re

lemmatizer = WordNetLemmatizer()

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
        print("⚠️ Error importing database modules in product catalog.py")
        #sys.exit(1)
        # Fallback for testing
        # import boto3
        # try:
        #     dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        # except:
        #     dynamodb = None
        # PRODUCT_TABLE = "mock-products2_with_calories"
        # PROMO_TABLE = "mock-promo-table"
        # def db_get_all_products():
        #     return [{"name": "Sample Product", "price": 2.99, "in_stock": True, "item_id": "sample_001"}]


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


# def get_mock_products():
#     """Get mock product data for fallback scenarios."""
#     return [
#         {
#             "item_id": "eggs_001",
#             "name": "Large Eggs",
#             "description": "Fresh large eggs, dozen",
#             "price": 3.99,
#             "category": "dairy",
#             "tags": ["eggs", "protein", "breakfast"],
#             "in_stock": True,
#             "quantity_available": 50,
#             "calories_per_unit": 70
#         },
#         {
#             "item_id": "milk_001", 
#             "name": "Whole Milk",
#             "description": "Fresh whole milk, 1 gallon",
#             "price": 4.29,
#             "category": "dairy",
#             "tags": ["milk", "dairy", "calcium"],
#             "in_stock": True,
#             "quantity_available": 30,
#             "calories_per_unit": 150
#         },
#         {
#             "item_id": "bread_001",
#             "name": "White Bread",
#             "description": "Fresh white bread loaf",
#             "price": 2.49,
#             "category": "bakery",
#             "tags": ["bread", "bakery", "carbs"],
#             "in_stock": True,
#             "quantity_available": 25,
#             "calories_per_unit": 80
#         },
#         {
#             "item_id": "chicken_001",
#             "name": "Chicken Breast",
#             "description": "Fresh chicken breast, per pound",
#             "price": 6.99,
#             "category": "meat",
#             "tags": ["chicken", "protein", "meat"],
#             "in_stock": True,
#             "quantity_available": 20,
#             "calories_per_unit": 165
#         },
#         {
#             "item_id": "tomatoes_001",
#             "name": "Organic Tomatoes",
#             "description": "Fresh organic tomatoes, 1lb",
#             "price": 2.99,
#             "category": "vegetables",
#             "tags": ["tomatoes", "vegetables", "organic"],
#             "in_stock": True,
#             "quantity_available": 15,
#             "calories_per_unit": 18
#         },
#         {
#             "item_id": "spinach_001",
#             "name": "Organic Spinach",
#             "description": "Fresh organic spinach, 8oz",
#             "price": 3.99,
#             "category": "vegetables",
#             "tags": ["spinach", "vegetables", "organic", "leafy"],
#             "in_stock": True,
#             "quantity_available": 12,
#             "calories_per_unit": 7
#         },
#         {
#             "item_id": "onions_001",
#             "name": "Organic Onions",
#             "description": "Fresh organic onions, 1lb",
#             "price": 1.99,
#             "category": "vegetables",
#             "tags": ["onions", "vegetables", "organic"],
#             "in_stock": True,
#             "quantity_available": 20,
#             "calories_per_unit": 40
#         },
#         {
#             "item_id": "carrots_001",
#             "name": "Organic Carrots",
#             "description": "Fresh organic carrots, 1lb",
#             "price": 2.49,
#             "category": "vegetables",
#             "tags": ["carrots", "vegetables", "organic"],
#             "in_stock": True,
#             "quantity_available": 18,
#             "calories_per_unit": 41
#         }
#     ]




def normalize_text(text: str) -> str:
    """Clean and lemmatize text for better matching."""
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower().strip())
    words = [lemmatizer.lemmatize(w) for w in text.split()]
    return " ".join(words)

def compute_similarity_score(query: str, product: Dict[str, Any]) -> float:
    """Compute weighted similarity score between query and product fields."""
    query_norm = normalize_text(query)
    
    name = normalize_text(product.get("name", ""))
    desc = normalize_text(product.get("description", ""))
    tags = " ".join([normalize_text(str(t)) for t in product.get("tags", [])])
    
    # Weights: name = 0.6, desc = 0.3, tags = 0.1
    score_name = fuzz.partial_ratio(query_norm, name)
    score_desc = fuzz.partial_ratio(query_norm, desc)
    score_tags = fuzz.partial_ratio(query_norm, tags)
    
    # Weighted aggregate
    total_score = (0.6 * score_name) + (0.3 * score_desc) + (0.1 * score_tags)
    return total_score

@tool
def search_products(query: str, limit: int = 20) -> Dict[str, Any]:
    """
    Search products by name, description, or tags using robust fuzzy matching.
    
    Args:
        query (str): Search term
        limit (int): Maximum results to return
        
    Returns:
        Dict[str, Any]: Standardized response with matching products
    """
    try:
        try:
            table = dynamodb.Table(PRODUCT_TABLE)
            response = table.scan()
            all_products = response.get("Items", [])
        except Exception:
            all_products = db_get_all_products()

        if not all_products:
            return {
                'success': True,
                'data': [],
                'count': 0,
                'query': query,
                'message': f"No products found for '{query}'"
            }

        query_norm = normalize_text(query)
        scored_products = []

        for product in all_products:
            score = compute_similarity_score(query_norm, product)
            scored_products.append((product, score))
        
        # Sort by score, descending
        scored_products.sort(key=lambda x: x[1], reverse=True)
        
        # Keep only good matches above a threshold
        threshold = 55  # Adjust based on testing
        filtered = [p for p, s in scored_products if s >= threshold][:limit]
        
        return {
            'success': True,
            'data': convert_decimal_to_float(filtered),
            'count': len(filtered),
            'query': query,
            'message': f"Found {len(filtered)} products matching '{query}'"
        }

    except Exception as e:
        return {
            'success': False,
            'data': [],
            'count': 0,
            'query': query,
            'message': f'Error searching products: {str(e)}'
        }

# @tool
# def search_products(query: str, limit: int = 20) -> Dict[str, Any]:
#     """
#     Search products by name, description, or tags using robust fuzzy matching.
    
#     Args:
#         query (str): Search term
#         limit (int): Maximum results to return
        
#     Returns:
#         Dict[str, Any]: Standardized response with matching products
#     """
#     try:
#         products = []
        
#         # Try DynamoDB search first
#         try:
#             table = dynamodb.Table(PRODUCT_TABLE)
#             response = table.scan()
#             all_products = response.get("Items", [])
            
#             # Use enhanced fuzzy matching logic (based on get_products_by_names)
#             query_lower = query.lower()
#             matched_products = []
            
#             # Step 1: Try exact match first
#             exact_matches = [p for p in all_products if p.get("name", "").lower() == query_lower]
#             if exact_matches:
#                 matched_products.extend(exact_matches)
            
#             # Step 2: Try partial match (query is contained in product name)
#             if len(matched_products) < limit:
#                 partial_matches = [p for p in all_products 
#                                  if query_lower in p.get("name", "").lower() and p not in matched_products]
#                 matched_products.extend(partial_matches)
            
#             # Step 3: Try reverse partial match (product name is contained in query)
#             if len(matched_products) < limit:
#                 reverse_matches = [p for p in all_products 
#                                  if p.get("name", "").lower() in query_lower and p not in matched_products]
#                 matched_products.extend(reverse_matches)
            
#             # Step 4: Try word-based matching for names
#             if len(matched_products) < limit:
#                 query_words = query_lower.split()
#                 word_matches = []
#                 for product in all_products:
#                     if product in matched_products:
#                         continue
#                     product_name = product.get("name", "").lower()
#                     # Check if any word from query matches product name
#                     if any(word in product_name for word in query_words if len(word) > 2):
#                         word_matches.append(product)
#                 matched_products.extend(word_matches)
            
#             # Step 5: Search in descriptions
#             if len(matched_products) < limit:
#                 desc_matches = []
#                 for product in all_products:
#                     if product in matched_products:
#                         continue
#                     description = product.get("description", "").lower()
#                     if query_lower in description:
#                         desc_matches.append(product)
#                 matched_products.extend(desc_matches)
            
#             # Step 6: Search in tags
#             if len(matched_products) < limit:
#                 tag_matches = []
#                 for product in all_products:
#                     if product in matched_products:
#                         continue
#                     tags = [str(tag).lower() for tag in product.get("tags", [])]
#                     if any(query_lower in tag for tag in tags):
#                         tag_matches.append(product)
#                 matched_products.extend(tag_matches)
            
#             # Step 7: Handle singular/plural variations
#             if len(matched_products) < limit:
#                 def matches_with_variations(text, query):
#                     if query in text:
#                         return True
#                     # Handle singular/plural variations
#                     if query.endswith('s') and query[:-1] in text:  # "strawberries" -> "strawberry"
#                         return True
#                     if not query.endswith('s') and (query + 's') in text:  # "strawberry" -> "strawberries"
#                         return True
#                     if not query.endswith('s') and (query + 'ies') in text:  # "berry" -> "berries"
#                         return True
#                     if query.endswith('ies') and (query[:-3] + 'y') in text:  # "berries" -> "berry"
#                         return True
#                     return False
                
#                 variation_matches = []
#                 for product in all_products:
#                     if product in matched_products:
#                         continue
#                     name = product.get("name", "").lower()
#                     description = product.get("description", "").lower()
#                     tags = [str(tag).lower() for tag in product.get("tags", [])]
                    
#                     if (matches_with_variations(name, query_lower) or 
#                         matches_with_variations(description, query_lower) or 
#                         any(matches_with_variations(tag, query_lower) for tag in tags)):
#                         variation_matches.append(product)
#                 matched_products.extend(variation_matches)
            
#             # Apply limit and remove duplicates
#             products = matched_products[:limit]
            
#         except Exception:
#             # Fallback to database query function
#             try:
#                 all_products = db_get_all_products()
#                 products = [
#                     p for p in all_products 
#                     if query.lower() in p.get("name", "").lower() or 
#                        query.lower() in p.get("description", "").lower() or
#                        any(query.lower() in str(tag).lower() for tag in p.get("tags", []))
#                 ][:limit]
#             except Exception:
#                 products = []
        
#         # Convert Decimal to float for JSON serialization
#         products = convert_decimal_to_float(products)
        
#         return {
#             'success': True,
#             'data': products,
#             'count': len(products),
#             'query': query,
#             'message': f"Found {len(products)} products matching '{query}'"
#         }
        
#     except Exception as e:
#         return {
#             'success': False,
#             'data': [],
#             'count': 0,
#             'query': query,
#             'message': f'Error searching products: {str(e)}'
#         }





@tool
def check_product_availability(product_name) -> Dict[str, Any]:
    """
    Check product availability and stock status with fuzzy name matching.
    
    Args:
        product_name (str): Product name to search for
        
    Returns:
        Dict[str, Any]: Standardized response with availability information
    """
    try:
        print(f"🔍 CHECK_PRODUCT_AVAILABILITY called with: {product_name}")
        print(f"🔍 Product name type: {type(product_name)}")
        
        # Validate input
        if not product_name:
            return convert_decimal_to_float({
                'success': False,
                'data': None,
                'message': 'No product name provided'
            })
        
        # Convert to string if needed
        product_name = str(product_name).strip()
        # Search for the product using a simple approach
        search_result = search_products(str(product_name).strip(), limit=1)
        
        if not search_result.get('success') or not search_result.get('data'):
            return convert_decimal_to_float({
                'success': False,
                'data': None,
                'message': f"Could not find '{product_name}' in the catalog"
            })
        
        # Get the best match (first result)
        product = search_result['data'][0]
        
        availability_info = {
            'product_name': str(product.get('name', product_name)),
            'item_id': str(product.get('item_id', '')),
            'in_stock': bool(product.get('in_stock', False)),
            #'quantity_available': int(product.get('quantity_available', 0)),
            'price': float(product.get('price', 0))
        }
        
        status_message = (
            f"Yes, {availability_info['product_name']} is in stock" 
            if availability_info['in_stock'] 
            else f"No, {availability_info['product_name']} is out of stock"
        )
        
        result = {
            'success': True,
            'data': availability_info,
            'message': status_message
        }
        
        # Ensure clean JSON serialization
        return convert_decimal_to_float(result)
        
    except Exception as e:
        return convert_decimal_to_float({
            'success': False,
            'data': None,
            'message': f'Error checking product availability: {str(e)}'
        })


@tool
def fetch_available_items(category: str = None, in_stock: bool = True, limit: int = 25) -> str:
    """
    Fetches available grocery items from the product catalog.
    
    Args:
        category (str, optional): Filter by product category (e.g., 'fruits', 'vegetables'). Defaults to None.
        in_stock (bool, optional): Filter by stock status. Defaults to True.
        limit (int, optional): Maximum number of products to return. Defaults to 25.
        
    Returns:
        str: JSON string containing list of available products with essential fields only
    """
    try:
        # Direct database call instead of HTTP request
        products = db_get_all_products()
        
        # Apply filters and limit
        filtered_products = []
        for product in products:
            # Filter by stock status
            if in_stock and not product.get("in_stock", True):
                continue
            
            # Filter by category if specified
            if category and product.get("category", "").lower() != category.lower():
                continue
            
            # Only include essential fields for meal planning
            essential_product = {
                "name": product.get("name"),
                "price": float(product.get("price", 0)) if product.get("price") else 0,
                "calories": int(product.get("calories", 0)) if product.get("calories") else 0,
                "category": product.get("category"),
                "tags": product.get("tags", []),
                "in_stock": product.get("in_stock", True),
            }
            
            # Convert any Decimal types
            essential_product = convert_decimal_to_float(essential_product)
            filtered_products.append(essential_product)
            
            # Apply limit
            if len(filtered_products) >= limit:
                break
        
        result = {
            "products": filtered_products,
            "count": len(filtered_products),
            "limited_to": limit
        }
        return result #json.dumps(result)
    except Exception as e:
        return {"error": f"Failed to fetch products: {str(e)}", "products": []}

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
@tool

def simple_test_tool(message: str = "test") -> str:
    """
    Simple test tool to verify tool calling is working.
    
    Args:
        message: Test message to echo back
        
    Returns:
        str: Echo of the input message
    """
    return f"Test tool working! Message: {message}"