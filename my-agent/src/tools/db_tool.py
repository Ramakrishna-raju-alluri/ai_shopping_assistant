import os
import boto3
from typing import Dict, Any, List
from decimal import Decimal
from strands import tool


# DynamoDB setup
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Table names from environment
USER_TABLE = os.getenv("USER_TABLE", "mock-users2")
PRODUCT_TABLE = os.getenv("PRODUCT_TABLE", "mock-products2")
RECIPE_TABLE = os.getenv("RECIPE_TABLE", "mock-recipes2")
PROMO_TABLE = os.getenv("PROMO_TABLE", "promo_stock_feed2")
NUTRITION_TABLE = os.getenv("NUTRITION_TABLE", "nutrition_calendar")


def _to_jsonable(obj):
    """Convert DynamoDB types to JSON-serializable types"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_jsonable(v) for v in obj]
    return obj


@tool
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Fetch user profile from DynamoDB"""
    table = dynamodb.Table(USER_TABLE)
    response = table.get_item(Key={"user_id": user_id})
    return _to_jsonable(response.get("Item", {}))


@tool
def get_products_by_names(product_names: List[str]) -> List[Dict[str, Any]]:
    """Get products by name with fuzzy matching"""
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
        
        # Try partial match
        partial_matches = [p for p in all_products if ingredient_name.lower() in p.get("name", "").lower()]
        
        if partial_matches:
            items.extend(partial_matches)
            continue
        
        # Try reverse partial match
        reverse_matches = [p for p in all_products if p.get("name", "").lower() in ingredient_name.lower()]
        
        if reverse_matches:
            items.extend(reverse_matches)
            continue
        
        # Try word-based matching
        ingredient_words = ingredient_name.lower().split()
        word_matches = []
        for product in all_products:
            product_name = product.get("name", "").lower()
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
    
    return _to_jsonable(unique_items)


@tool
def find_product_stock(product_name: str) -> str:
    """Check if a product by name is in stock"""
    table = dynamodb.Table(PRODUCT_TABLE)
    resp = table.scan()
    items = resp.get("Items", [])
    
    # Fuzzy match by name
    q = (product_name or "").strip().lower()
    if not q:
        return f"I couldn't find '{product_name}' in the catalog."
    
    exact = [p for p in items if p.get("name", "").lower() == q]
    if exact:
        matches = exact
    else:
        contains = [p for p in items if q in p.get("name", "").lower()]
        if contains:
            matches = contains
        else:
            # word-based loose match
            words = [w for w in q.split() if len(w) > 2]
            matches = []
            for p in items:
                n = p.get("name", "").lower()
                if any(w in n for w in words):
                    matches.append(p)
    
    if not matches:
        return f"I couldn't find '{product_name}' in the catalog."
    
    # Check stock status
    m = matches[0]
    in_stock = bool(m.get("in_stock", False))
    name = m.get("name", product_name)
    return f"Yes, {name} are in stock." if in_stock else f"No, {name} are out of stock."


@tool
def get_nutrition_plan(user_id: str, date: str) -> Dict[str, Any]:
    """Fetch the day's nutrition plan for the user"""
    table = dynamodb.Table(NUTRITION_TABLE)
    resp = table.get_item(Key={"user_id": user_id, "date": date})
    return _to_jsonable(resp.get("Item", {"user_id": user_id, "date": date, "target": 0, "consumed": 0, "meals": []}))


@tool
def set_nutrition_target(user_id: str, date: str, target: int) -> Dict[str, Any]:
    """Set or update the daily calorie target for a given date"""
    table = dynamodb.Table(NUTRITION_TABLE)
    plan = get_nutrition_plan(user_id, date)
    meals = plan.get("meals", [])
    consumed = sum(int(m.get("calories", 0)) for m in meals)
    
    item = {
        "user_id": user_id,
        "date": date,
        "target": int(target),
        "consumed": consumed,
        "meals": meals,
    }
    table.put_item(Item=item)
    return _to_jsonable(item)


@tool
def append_meal(user_id: str, date: str, meal: Dict[str, Any]) -> Dict[str, Any]:
    """Append a single meal to the day's plan"""
    table = dynamodb.Table(NUTRITION_TABLE)
    plan = get_nutrition_plan(user_id, date)
    meals = list(plan.get("meals", [])) + [meal]
    consumed = sum(int(m.get("calories", 0)) for m in meals)
    
    item = {
        "user_id": user_id,
        "date": date,
        "target": int(plan.get("target", 0)),
        "consumed": consumed,
        "meals": meals,
    }
    table.put_item(Item=item)
    return _to_jsonable(item)


@tool
def get_calories_remaining(user_id: str, date: str, daily_target: int = None) -> int:
    """Return remaining calories for the day using stored target when available"""
    plan = get_nutrition_plan(user_id, date)
    consumed = int(plan.get("consumed", 0))
    target = int(daily_target) if daily_target is not None else int(plan.get("target", 0))
    return max(0, target - consumed)
