"""
Smart food matching tool that uses LLM to match user queries against DynamoDB table entries.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import database functions with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb, PRODUCT_TABLE
    from backend_bedrock.tools.shared.product_catalog import get_all_products_raw
except ImportError:
    try:
        from dynamo.client import dynamodb, PRODUCT_TABLE
        from tools.shared.product_catalog import get_all_products_raw
    except ImportError:
        # Fallback for testing
        import boto3
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        except:
            dynamodb = None
        PRODUCT_TABLE = "mock-products2_with_calories"
        def get_all_products_raw():
            return []


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
def get_full_product_table_for_matching() -> Dict[str, Any]:
    """
    Get the complete product table data for LLM-based food matching.
    This is called when exact matching fails and we need intelligent matching.
    
    Returns:
        Dict[str, Any]: Complete product table data with nutrition info
    """
    try:
        # Get all products from DynamoDB
        products_data = get_all_products_raw()
        
        if not products_data:
            return {
                'success': False,
                'data': None,
                'message': 'No product data available from database'
            }
        
        # Convert Decimal to float for JSON serialization
        products_data = convert_decimal_to_float(products_data)
        
        # Format for LLM consumption - include only relevant fields
        formatted_products = []
        for product in products_data:
            formatted_product = {
                'name': product.get('name', ''),
                'description': product.get('description', ''),
                'category': product.get('category', ''),
                'tags': product.get('tags', []),
                'calories': product.get('calories', 0),
                'calories_per_unit': product.get('calories_per_unit', 0),
                'protein': product.get('protein', 0),
                'carbs': product.get('carbs', 0),
                'fat': product.get('fat', 0),
                'item_id': product.get('item_id', ''),
                'price': product.get('price', 0)
            }
            # Only include products with some nutrition data
            if formatted_product['calories'] > 0 or formatted_product['calories_per_unit'] > 0:
                formatted_products.append(formatted_product)
        
        return {
            'success': True,
            'data': {
                'products': formatted_products,
                'total_products': len(formatted_products),
                'table_name': PRODUCT_TABLE
            },
            'message': f'Retrieved {len(formatted_products)} products with nutrition data for matching'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error retrieving product table: {str(e)}'
        }


@tool
def find_best_food_match(food_query: str, product_table_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use LLM reasoning to find the best matching food item from the product table.
    This tool is designed to be called by an agent that can reason about food similarities.
    
    Args:
        food_query (str): The food item the user is asking about (e.g., "bananas", "apple", "chicken")
        product_table_data (List[Dict[str, Any]]): Complete product table data
        
    Returns:
        Dict[str, Any]: Best matching product with confidence score and reasoning
    """
    try:
        if not product_table_data:
            return {
                'success': False,
                'data': None,
                'message': 'No product data provided for matching'
            }
        
        # This tool returns the data for the agent to process
        # The actual matching logic will be handled by the LLM agent
        return {
            'success': True,
            'data': {
                'query': food_query,
                'available_products': product_table_data,
                'matching_instructions': {
                    'task': 'Find the best matching food item',
                    'criteria': [
                        'Exact name match (highest priority)',
                        'Similar name or common variations',
                        'Same category or food type',
                        'Similar nutritional profile',
                        'Common synonyms or alternate names'
                    ],
                    'output_format': {
                        'matched_product': 'The best matching product object',
                        'confidence': 'Score from 0-100',
                        'reasoning': 'Why this match was selected',
                        'alternatives': 'Other possible matches if confidence < 90'
                    }
                }
            },
            'message': f'Prepared {len(product_table_data)} products for intelligent matching against "{food_query}"'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error preparing food matching data: {str(e)}'
        }