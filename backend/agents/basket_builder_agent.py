# agents/basket_builder_agent.py
from dynamo.queries import get_products_by_names
from typing import List
from decimal import Decimal

def build_basket(recipes: List[dict], budget_limit: Decimal = None) -> List[dict]:
    """
    Build shopping basket from recipes with budget constraint
    """
    # Extract unique ingredient names
    ingredient_names = set()
    for recipe in recipes:
        ingredient_names.update(recipe.get("ingredients", []))
    
    print(f"   🛒 Building basket from {len(recipes)} recipes")
    print(f"   📝 Total unique ingredients: {len(ingredient_names)}")
    print(f"   🥘 Ingredients: {', '.join(list(ingredient_names)[:5])}{'...' if len(ingredient_names) > 5 else ''}")
    
    # Fetch products from DynamoDB by name
    all_products = get_products_by_names(list(ingredient_names))
    
    print(f"   ✅ Found {len(all_products)} products in database")
    
    # Check which ingredients were found and which were missed
    found_ingredients = {p.get('name', '') for p in all_products}
    missing_ingredients = []
    
    for ingredient in ingredient_names:
        # Check if any product name contains this ingredient
        found = False
        for product in all_products:
            if ingredient.lower() in product.get('name', '').lower():
                found = True
                break
        if not found:
            missing_ingredients.append(ingredient)
    
    if missing_ingredients:
        print(f"   ⚠️  Missing ingredients: {', '.join(missing_ingredients)}")
    else:
        print(f"   ✅ All ingredients found!")
    
    if not budget_limit:
        return all_products
    
    # Apply budget constraint
    selected_products = []
    total_cost = Decimal('0')
    
    # Sort products by price (cheapest first) to maximize items within budget
    sorted_products = sorted(all_products, key=lambda x: Decimal(str(x.get('price', 0))))
    
    for product in sorted_products:
        product_price = Decimal(str(product.get('price', 0)))
        
        # Check if adding this product would exceed budget
        if total_cost + product_price <= budget_limit:
            selected_products.append(product)
            total_cost += product_price
        else:
            # Skip this product if it would exceed budget
            print(f"   💰 Skipping {product.get('name')} (${product_price}) - would exceed budget")
    
    print(f"   💰 Budget constraint applied: ${total_cost} / ${budget_limit}")
    print(f"   📦 Selected {len(selected_products)} out of {len(all_products)} products")
    
    return selected_products
