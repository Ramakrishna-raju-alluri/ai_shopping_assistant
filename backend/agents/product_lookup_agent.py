#!/usr/bin/env python3
"""
Product Lookup Agent
Handles specific product queries like price checks and availability
"""

from typing import Dict, Any, List, Optional
from dynamo.queries import get_products_by_names
import re

def extract_product_name_from_query(query: str) -> Optional[str]:
    """Extract product name from user query"""
    query_lower = query.lower()
    
    # Common misspellings and corrections
    spelling_corrections = {
        "wallnut": "walnut",
        "wallnuts": "walnuts", 
        "availabe": "available",
        "tomatos": "tomatoes",
        "strawberrys": "strawberries",
        "blueberrys": "blueberries",
        "raspberrys": "raspberries"
    }
    
    # Apply spelling corrections
    for misspelling, correction in spelling_corrections.items():
        query_lower = query_lower.replace(misspelling, correction)
    
    # Common product keywords to look for - ordered by specificity (longer/more specific first)
    product_keywords = [
        "organic walnuts", "organic walnut", "organic almonds", "organic eggs", "organic milk", 
        "organic bread", "organic cheese", "organic yogurt", "organic butter", "organic chicken", 
        "organic beef", "organic salmon", "organic spinach", "organic broccoli", "organic carrots", 
        "organic tomatoes", "organic apples", "organic bananas", "organic strawberries", 
        "organic quinoa", "organic rice", "organic pasta", "organic olive oil", "organic avocado", 
        "organic garlic", "organic onion", "organic mushroom", "organic zucchini", "organic eggplant", 
        "organic lentil", "organic chickpea", "organic black bean", "organic kidney bean",
        "organic coffee", "organic tea", "organic chocolate",
        # Multi-word products
        "cottage cheese", "greek yogurt", "protein powder", "olive oil", "bell peppers", "sweet corn",
        "sunflower seeds", "chia seeds", "flax seeds", "black beans", "kidney beans", "chicken breast",
        "salmon fillet", "brown rice", "whole wheat", "cream cheese", "blue cheese", "feta cheese",
        # Single-word products
        "oatmeal", "quinoa", "rice", "pasta", "bread", "milk", "cheese", "yogurt", "butter", "chicken",
        "beef", "salmon", "spinach", "broccoli", "carrots", "tomatoes", "apples", "bananas", 
        "strawberries", "walnut", "almonds", "eggs", "olive oil", "avocado", "garlic", "onion", 
        "mushroom", "zucchini", "eggplant", "lentil", "chickpea", "black bean", "kidney bean",
        "coffee", "tea", "chocolate"
    ]
    
    # Look for exact matches first - prioritize longer/more specific matches
    matched_keywords = []
    for keyword in product_keywords:
        # Use word boundary matching to prevent false matches (e.g., 'rice' in 'price')
        if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
            matched_keywords.append(keyword)
    
    # Return the longest/most specific match
    if matched_keywords:
        return max(matched_keywords, key=len)
    
    # If no exact match, try to extract product name using patterns
    patterns = [
        r"cost of (\w+(?:\s+\w+)*)",
        r"price of (\w+(?:\s+\w+)*)",
        r"price for (\w+(?:\s+\w+)*)",
        r"how much does (\w+(?:\s+\w+)*) cost",
        r"what is the price of (\w+(?:\s+\w+)*)",
        r"what is the price for (\w+(?:\s+\w+)*)",
        r"do you have (\w+(?:\s+\w+)*)",
        r"is (\w+(?:\s+\w+)*) available",
        r"(\w+(?:\s+\w+)*) in stock",
        r"carry (\w+(?:\s+\w+)*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            product_name = match.group(1).strip()
            # Clean up the product name - be more careful to preserve multi-word products
            product_name = re.sub(r'\b(do|you|have|is|are|the|a|an|in|stock|available|carry|or|not|what|price|cost|much|does)\b', '', product_name).strip()
            if product_name and len(product_name) > 2:
                return product_name
    
    # Additional patterns for specific query types
    additional_patterns = [
        r"is (\w+(?:\s+\w+)*) availabe",  # Handle misspelling
        r"is (\w+(?:\s+\w+)*) in the stock",
        r"(\w+(?:\s+\w+)*) available in the stock",
        r"(\w+(?:\s+\w+)*) in stock or not",
        r"(\w+(?:\s+\w+)*) available in stock or not"
    ]
    
    for pattern in additional_patterns:
        match = re.search(pattern, query_lower)
        if match:
            product_name = match.group(1).strip()
            # Clean up the product name - be more careful to preserve multi-word products
            product_name = re.sub(r'\b(do|you|have|is|are|the|a|an|in|stock|available|carry|or|not|what|price|availabe)\b', '', product_name).strip()
            if product_name and len(product_name) > 2:
                return product_name
    
    return None

def lookup_product_info(product_name: str) -> Dict[str, Any]:
    """Look up product information from database"""
    try:
        # Search for the product in the database
        products = get_products_by_names([product_name])
        
        if not products:
            return {
                "found": False,
                "message": f"I couldn't find '{product_name}' in our product database."
            }
        
        # Get the first matching product
        product = products[0]
        
        return {
            "found": True,
            "product": product,
            "name": product.get('name', 'Unknown'),
            "price": product.get('price', 0),
            "in_stock": product.get('in_stock', True),
            "category": product.get('category', 'Unknown'),
            "tags": product.get('tags', []),
            "description": product.get('description', ''),
            "promo": product.get('promo', False)
        }
        
    except Exception as e:
        print(f"Error looking up product {product_name}: {e}")
        return {
            "found": False,
            "message": f"Sorry, I encountered an error while looking up '{product_name}'."
        }

def format_product_response(product_info: Dict[str, Any], query_type: str) -> str:
    """Format the product information into a user-friendly response"""
    if not product_info.get("found"):
        return product_info.get("message", "Product not found.")
    
    product = product_info["product"]
    name = product_info["name"]
    price = product_info["price"]
    in_stock = product_info["in_stock"]
    category = product_info["category"]
    tags = product_info["tags"]
    promo = product_info["promo"]
    
    # Format price
    price_str = f"${price:.2f}" if price else "Price not available"
    
    # Format tags
    tag_str = ""
    if tags:
        tag_str = f", {', '.join(tags)}"
    
    # Format stock status
    stock_status = "in stock" if in_stock else "out of stock"
    
    # Format promo status
    promo_str = " and is currently on sale" if promo else ""
    
    # Build response in the preferred format
    response = f"Sure! The price of {name} is {price_str}. It's currently {stock_status}{promo_str} and categorized under {category} products. By the way, it's{tag_str}."
    
    return response

def handle_product_query(user_query: str) -> Dict[str, Any]:
    """Main function to handle product lookup queries"""
    print(f"🔍 Product Lookup - Processing query: {user_query}")
    
    # Extract product name from query
    product_name = extract_product_name_from_query(user_query)
    
    if not product_name:
        return {
            "success": False,
            "message": "I couldn't identify which product you're asking about. Could you please be more specific? For example: 'What's the price of organic walnuts?' or 'Do you have almond milk in stock?'"
        }
    
    print(f"🔍 Product Lookup - Extracted product name: {product_name}")
    
    # Look up product information
    product_info = lookup_product_info(product_name)
    
    if not product_info.get("found"):
        return {
            "success": False,
            "message": product_info.get("message", f"I couldn't find information about '{product_name}' in our database.")
        }
    
    # Format the response
    formatted_response = format_product_response(product_info, user_query)
    
    return {
        "success": True,
        "message": formatted_response,
        "product_info": product_info,
        "product_name": product_name
    } 