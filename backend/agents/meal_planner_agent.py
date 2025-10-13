# agents/meal_planner_agent.py
from dynamo.queries import get_recipes_by_diet_and_budget
from dynamo.client import dynamodb, RECIPE_TABLE, PRODUCT_TABLE, PROMO_TABLE
from decimal import Decimal
from boto3.dynamodb.conditions import Attr
import random

# Diet mapping for better recipe selection
DIET_MAPPING = {
    "low-carb": ["keto", "low-fat"],
    "paleo": ["high-protein", "gluten-free"],
    "omnivore": ["vegetarian", "high-protein", "keto", "low-fat"],
    "mediterranean": ["vegetarian", "low-fat"],
    "dairy-free": ["vegan", "gluten-free"]
}

def plan_meals(user_profile: dict) -> list:
    """Plan meals for meal planning queries with enhanced preference matching"""
    diet = user_profile.get("diet", "vegetarian")
    total_budget = user_profile.get("budget_limit", 50)
    num_meals = int(user_profile.get("meal_goal", "3 meals").split()[0])
    preferred_cuisines = user_profile.get("preferred_cuisines", [])
    cooking_skill = user_profile.get("cooking_skill", "intermediate")
    allergies = user_profile.get("allergies", [])

    # Convert to Decimal to avoid float issues
    total_budget_decimal = Decimal(str(total_budget))
    
    print(f"   Planning {num_meals} meals with total budget: ${total_budget_decimal}")
    print(f"   Diet preference: {diet}")
    print(f"   Preferred cuisines: {', '.join(preferred_cuisines) if preferred_cuisines else 'Any'}")
    print(f"   Cooking skill: {cooking_skill}")
    if allergies:
        print(f"   Allergies to avoid: {', '.join(allergies)}")
    
    # Get recipes based on diet preference
    if diet.lower() in DIET_MAPPING:
        # For mapped diets, get recipes from multiple compatible diet types
        compatible_diets = DIET_MAPPING[diet.lower()]
        print(f"   Using compatible diets: {', '.join(compatible_diets)}")
        recipes = get_recipes_by_compatible_diets(compatible_diets, total_budget_decimal)
    elif diet.lower() == "omnivore":
        # For omnivore, get all recipes regardless of diet tags
        recipes = get_all_recipes_within_budget(total_budget_decimal)
    else:
        # For specific diets, use the existing function
        recipes = get_recipes_by_diet_and_budget(diet, total_budget_decimal)
    
    # Filter recipes based on preferences
    filtered_recipes = filter_recipes_by_preferences(recipes, preferred_cuisines, cooking_skill, allergies)
    
    # Sort recipes by preference score and cost
    scored_recipes = score_recipes_by_preferences(filtered_recipes, preferred_cuisines, cooking_skill)
    sorted_recipes = sorted(scored_recipes, key=lambda x: (x['preference_score'], Decimal(str(x.get('total_cost', 0)))), reverse=True)
    
    # Select recipes that fit within total budget
    selected_recipes = []
    total_cost = Decimal('0')
    
    for recipe in sorted_recipes:
        recipe_cost = Decimal(str(recipe.get('total_cost', 0)))
        
        # Check if adding this recipe would exceed total budget
        if total_cost + recipe_cost <= total_budget_decimal and len(selected_recipes) < num_meals:
            selected_recipes.append(recipe)
            total_cost += recipe_cost
            print(f"   Selected: {recipe.get('title')} - ${recipe_cost} (Score: {recipe.get('preference_score', 0)})")
        else:
            if len(selected_recipes) < num_meals:
                print(f"   Skipped: {recipe.get('title')} - ${recipe_cost} (would exceed budget)")
    
    print(f"   Total selected recipes: {len(selected_recipes)}")
    print(f"   Total cost: ${total_cost} / ${total_budget_decimal}")
    
    return selected_recipes

def get_product_recommendations(intent: dict, user_profile: dict = None) -> dict:
    """Get product recommendations based on dietary preferences for product_recommendation and dietary_filter queries"""
    query_type = intent.get("query_type", "product_recommendation")
    dietary_preference = intent.get("dietary_preference")
    budget = intent.get("budget")
    
    print(f"   Getting product recommendations for: {query_type}")
    print(f"   Dietary preference: {dietary_preference}")
    print(f"   Budget: ${budget}")
    
    # Use user profile budget if not specified in intent
    if not budget and user_profile:
        budget = user_profile.get("budget_limit", 50)
    
    # Convert to Decimal
    budget_decimal = Decimal(str(budget)) if budget else Decimal('50')
    
    # Get products directly from products table based on dietary preference
    if dietary_preference:
        products = get_products_by_diet_preference(dietary_preference, budget_decimal)
    else:
        # If no dietary preference, get all products within budget
        products = get_all_products_within_budget(budget_decimal)
    
    # Sort products by price (cheapest first)
    sorted_products = sorted(products, key=lambda x: Decimal(str(x.get('price', 0))))
    
    # Select products that fit within budget (limit to 8 for recommendations)
    selected_products = []
    total_cost = Decimal('0')
    max_products = 8
    
    for product in sorted_products:
        product_price = Decimal(str(product.get('price', 0)))
        
        # Check if adding this product would exceed budget
        if total_cost + product_price <= budget_decimal and len(selected_products) < max_products:
            selected_products.append(product)
            total_cost += product_price
            print(f"   Selected: {product.get('name')} - ${product_price}")
        else:
            if len(selected_products) < max_products:
                print(f"   Skipped: {product.get('name')} - ${product_price} (would exceed budget)")
    
    print(f"   Total selected products: {len(selected_products)}")
    print(f"   Total cost: ${total_cost} / ${budget_decimal}")
    
    # Format response based on query type
    if query_type == "dietary_filter":
        return format_dietary_filter_response(selected_products, dietary_preference)
    else:
        return format_product_recommendation_response(selected_products, dietary_preference)

def format_dietary_filter_response(products: list, dietary_preference: str) -> dict:
    """Format response for dietary filter queries"""
    if not products:
        return {
            "message": f"Sorry, no {dietary_preference} products found within your budget.",
            "products": [],
            "count": 0
        }
    
    return {
        "message": f"Found {len(products)} {dietary_preference} products:",
        "products": products,
        "count": len(products),
        "dietary_preference": dietary_preference
    }

def format_product_recommendation_response(products: list, dietary_preference: str) -> dict:
    """Format response for product recommendation queries"""
    if not products:
        preference_text = f" {dietary_preference}" if dietary_preference else ""
        return {
            "message": f"Sorry, no{preference_text} products found within your budget.",
            "products": [],
            "count": 0
        }
    
    preference_text = f" {dietary_preference}" if dietary_preference else ""
    
    return {
        "message": f"Here are some{preference_text} product recommendations:",
        "products": products,
        "count": len(products),
        "dietary_preference": dietary_preference
    }

def get_recipes_by_compatible_diets(compatible_diets, max_cost):
    """Get recipes from multiple compatible diet types"""
    table = dynamodb.Table(RECIPE_TABLE)
    
    all_recipes = []
    
    for diet in compatible_diets:
        # Get recipes for each compatible diet
        response = table.scan(
            FilterExpression=Attr("diet").contains(diet) & Attr("total_cost").lte(max_cost)
        )
        diet_recipes = response.get("Items", [])
        all_recipes.extend(diet_recipes)
        print(f"   Found {len(diet_recipes)} recipes for {diet} diet")
    
    # Remove duplicates based on recipe title
    unique_recipes = []
    seen_titles = set()
    for recipe in all_recipes:
        title = recipe.get('title', '')
        if title not in seen_titles:
            unique_recipes.append(recipe)
            seen_titles.add(title)
    
    print(f"   Total unique recipes: {len(unique_recipes)}")
    return unique_recipes

def get_all_recipes_within_budget(max_cost):
    """Get all recipes within budget regardless of diet"""
    table = dynamodb.Table(RECIPE_TABLE)
    
    # Get all recipes within budget
    response = table.scan(
        FilterExpression=Attr("total_cost").lte(max_cost)
    )
    
    return response.get("Items", [])

def filter_recipes_by_preferences(recipes: list, preferred_cuisines: list, cooking_skill: str, allergies: list) -> list:
    """Filter recipes based on user preferences"""
    filtered_recipes = []
    
    for recipe in recipes:
        # Check for allergies
        if has_allergies(recipe, allergies):
            continue
        
        # Check cooking skill compatibility
        if not is_cooking_skill_compatible(recipe, cooking_skill):
            continue
        
        filtered_recipes.append(recipe)
    
    return filtered_recipes

def has_allergies(recipe: dict, allergies: list) -> bool:
    """Check if recipe contains any allergens"""
    if not allergies:
        return False
    
    # Get recipe ingredients
    ingredients = recipe.get('ingredients', [])
    recipe_text = ' '.join([str(ingredient) for ingredient in ingredients]).lower()
    recipe_title = recipe.get('title', '').lower()
    recipe_text += ' ' + recipe_title
    
    # Check for allergy matches
    for allergy in allergies:
        if allergy.lower() in recipe_text:
            return True
    
    return False

def is_cooking_skill_compatible(recipe: dict, cooking_skill: str) -> bool:
    """Check if recipe is compatible with user's cooking skill"""
    if cooking_skill == "advanced":
        return True  # Advanced cooks can handle any recipe
    
    # Get recipe complexity indicators
    recipe_title = recipe.get('title', '').lower()
    ingredients = recipe.get('ingredients', [])
    
    # Simple recipes for beginners
    beginner_keywords = ['salad', 'sandwich', 'wrap', 'smoothie', 'bowl', 'simple', 'easy', 'quick']
    complex_keywords = ['souffle', 'risotto', 'paella', 'complex', 'advanced', 'difficult', 'elaborate']
    
    # Check for complex keywords
    if cooking_skill == "beginner":
        for keyword in complex_keywords:
            if keyword in recipe_title:
                return False
    
    # Check number of ingredients (beginners prefer fewer ingredients)
    if cooking_skill == "beginner" and len(ingredients) > 8:
        return False
    
    return True

def score_recipes_by_preferences(recipes: list, preferred_cuisines: list, cooking_skill: str) -> list:
    """Score recipes based on user preferences"""
    scored_recipes = []
    
    for recipe in recipes:
        score = 0
        recipe_title = recipe.get('title', '').lower()
        ingredients = recipe.get('ingredients', [])
        
        # Score based on cuisine preferences
        if preferred_cuisines:
            for cuisine in preferred_cuisines:
                cuisine_keywords = get_cuisine_keywords(cuisine)
                for keyword in cuisine_keywords:
                    if keyword in recipe_title:
                        score += 2
                        break
        
        # Score based on cooking skill
        if cooking_skill == "beginner":
            # Prefer simple recipes
            simple_keywords = ['simple', 'easy', 'quick', 'basic']
            for keyword in simple_keywords:
                if keyword in recipe_title:
                    score += 1
        elif cooking_skill == "intermediate":
            # Balanced scoring
            score += 1
        else:  # advanced
            # Prefer complex recipes
            complex_keywords = ['complex', 'advanced', 'elaborate', 'gourmet']
            for keyword in complex_keywords:
                if keyword in recipe_title:
                    score += 1
        
        # Score based on number of ingredients (prefer moderate complexity)
        if cooking_skill == "beginner" and 3 <= len(ingredients) <= 6:
            score += 1
        elif cooking_skill == "intermediate" and 4 <= len(ingredients) <= 8:
            score += 1
        elif cooking_skill == "advanced" and len(ingredients) >= 6:
            score += 1
        
        recipe['preference_score'] = score
        scored_recipes.append(recipe)
    
    return scored_recipes

def get_cuisine_keywords(cuisine: str) -> list:
    """Get keywords associated with a cuisine type"""
    cuisine_keywords = {
        "italian": ["pasta", "pizza", "risotto", "lasagna", "italian", "mozzarella", "parmesan", "basil"],
        "asian": ["asian", "stir-fry", "curry", "sushi", "noodles", "soy", "ginger", "sesame"],
        "mexican": ["mexican", "tacos", "enchiladas", "burritos", "quesadillas", "salsa", "guacamole"],
        "mediterranean": ["mediterranean", "salads", "grilled", "hummus", "falafel", "olive", "feta"],
        "american": ["american", "burgers", "steak", "chicken", "barbecue", "comfort"],
        "indian": ["indian", "curry", "biryani", "dal", "naan", "spice", "masala"],
        "quick_easy": ["quick", "easy", "simple", "fast", "30-minute", "one-pot"],
        "healthy": ["healthy", "salad", "smoothie", "bowl", "lean", "nutritious"]
    }
    
    return cuisine_keywords.get(cuisine.lower(), [])

def get_products_by_diet_preference(dietary_preference: str, max_cost: Decimal) -> list:
    """Get products from products table based on dietary preference"""
    table = dynamodb.Table(PRODUCT_TABLE)
    
    # Map dietary preference to product tags
    diet_to_tags = {
        "vegetarian": ["vegetarian"],
        "vegan": ["vegan"],
        "keto": ["keto"],
        "low-carb": ["low-carb"],
        "gluten-free": ["gluten-free"],
        "high-protein": ["high-protein"],
        "low-fat": ["low-fat"],
        "mediterranean": ["mediterranean"],
        "omnivore": ["protein", "vegetarian", "vegan"]  # Include all options
    }
    
    target_tags = diet_to_tags.get(dietary_preference.lower(), [dietary_preference.lower()])
    
    print(f"   Looking for products with tags: {target_tags}")
    
    # Get all products and filter by tags and budget
    response = table.scan()
    all_products = response.get("Items", [])
    
    # Filter products by tags and budget
    filtered_products = []
    for product in all_products:
        product_tags = product.get('tags', [])
        product_price = Decimal(str(product.get('price', 0)))
        
        # Check if product has any of the target tags and is within budget
        if any(tag in product_tags for tag in target_tags) and product_price <= max_cost:
            filtered_products.append(product)
    
    print(f"   Found {len(filtered_products)} products matching {dietary_preference} within budget")
    return filtered_products

def get_all_products_within_budget(max_cost: Decimal) -> list:
    """Get all products within budget regardless of diet"""
    table = dynamodb.Table(PRODUCT_TABLE)
    
    # Get all products within budget
    response = table.scan()
    all_products = response.get("Items", [])
    
    # Filter by budget
    filtered_products = []
    for product in all_products:
        product_price = Decimal(str(product.get('price', 0)))
        if product_price <= max_cost:
            filtered_products.append(product)
    
    print(f"   Found {len(filtered_products)} products within budget")
    return filtered_products
