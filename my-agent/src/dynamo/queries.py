# dynamo/queries.py
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from .client import dynamodb, USER_TABLE, PRODUCT_TABLE, RECIPE_TABLE, PROMO_TABLE

# --- USER FUNCTIONS ---
def get_user_profile(user_id):
    table = dynamodb.Table(USER_TABLE)
    response = table.get_item(Key={"user_id": user_id})
    return response.get("Item")

def create_user_profile(user_id, profile_data):
    table = dynamodb.Table(USER_TABLE)
    profile_data["user_id"] = user_id
    table.put_item(Item=profile_data)
    return profile_data

def update_user_profile(user_id, profile_data):
    """Update an existing user profile"""
    table = dynamodb.Table(USER_TABLE)
    profile_data["user_id"] = user_id
    table.put_item(Item=profile_data)
    return profile_data

# --- RECIPE FUNCTIONS ---
def get_recipes_by_diet_and_budget(diet, max_cost):
    table = dynamodb.Table(RECIPE_TABLE)
    scan_kwargs = {
        "FilterExpression": Attr("diet").contains(diet) & Attr("total_cost").lte(max_cost)
    }
    response = table.scan(**scan_kwargs)
    return response.get("Items", [])

# --- PRODUCT FUNCTIONS ---
def get_all_products():
    """Get all products from the product table"""
    table = dynamodb.Table(PRODUCT_TABLE)
    response = table.scan()
    return response.get("Items", [])

def get_products_by_names(product_names):
    table = dynamodb.Table(PRODUCT_TABLE)
    items = []
    
    # Get all products first for fuzzy matching
    response = table.scan()
    all_products = response.get("Items", [])
    
    for ingredient_name in product_names:
        # Try exact match first
        exact_matches = [p for p in all_products if p.get("name", "").lower() == ingredient_name.lower()]
        
        if exact_matches:
            items.extend(exact_matches)
            continue
        
        # Try partial match (ingredient name is contained in product name)
        partial_matches = [p for p in all_products if ingredient_name.lower() in p.get("name", "").lower()]
        
        if partial_matches:
            items.extend(partial_matches)
            continue
        
        # Try reverse partial match (product name is contained in ingredient name)
        reverse_matches = [p for p in all_products if p.get("name", "").lower() in ingredient_name.lower()]
        
        if reverse_matches:
            items.extend(reverse_matches)
            continue
        
        # Try word-based matching
        ingredient_words = ingredient_name.lower().split()
        word_matches = []
        for product in all_products:
            product_name = product.get("name", "").lower()
            # Check if any word from ingredient matches product name
            if any(word in product_name for word in ingredient_words if len(word) > 2):
                word_matches.append(product)
        
        if word_matches:
            items.extend(word_matches)
    
    # Remove duplicates based on item_id
    unique_items = []
    seen_ids = set()
    for item in items:
        item_id = item.get("item_id")
        if item_id and item_id not in seen_ids:
            unique_items.append(item)
            seen_ids.add(item_id)
    
    return unique_items

# --- PROMO/STOCK FUNCTIONS ---
def get_promo_info(item_ids):
    table = dynamodb.Table(PROMO_TABLE)
    items = []
    for item_id in item_ids:
        response = table.get_item(Key={"item_id": item_id})
        if "Item" in response:
            items.append(response["Item"])
    return items