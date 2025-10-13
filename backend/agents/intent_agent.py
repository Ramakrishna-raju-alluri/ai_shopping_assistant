# agents/intent_agent_fixed.py
from langchain_core.prompts import ChatPromptTemplate
from bedrock.bedrock_llm import get_bedrock_llm
import re
import json

llm = get_bedrock_llm()

PROMPT_TEMPLATE = """
You are a smart grocery shopping assistant that can handle various types of queries.
Classify the user's intent and extract relevant information.

Return a JSON object with:
- query_type (string): The type of query (meal_planning, product_recommendation, dietary_filter, cart_operation, basket_builder, general_query)
- cart_operation_type (string): For cart_operation queries, specify the operation (add, delete, view, clear)
- number_of_meals (int): The number of meals requested (only for meal_planning)
- budget (int): The maximum budget in USD (extract from phrases like "under $X", "less than $X", "within $X")
- dietary_preference (string): The dietary preference (vegetarian, vegan, keto, low-carb, gluten-free, etc.)
- product_category (string): The product category being requested (snacks, dairy, produce, etc.)
- special_requirements (string): Any special requirements (on sale, organic, etc.)

Query Types:
- meal_planning: User wants to plan meals and get shopping list (e.g., "plan 3 meals under $30")
- product_recommendation: User wants product suggestions (e.g., "suggest low carb snacks", "recommend items on sale")
- dietary_filter: User wants items filtered by diet (e.g., "show me gluten free items", "find vegan products")
- cart_operation: User wants to add/delete items to/from cart, view cart, or manage cart (e.g., "add bananas to cart", "delete milk from cart", "view my cart")
- basket_builder: User wants to add ingredients/components of a specific recipe/meal directly to cart (e.g., "add contents/components/ingredients of mediterranean quinoa bowl to cart", "add ingredients for veggie stir fry to my cart")
- general_query: User asks about product availability, delivery, store info, policies, etc. (e.g., "do you have organic milk?", "how do I get delivery?")

IMPORTANT: Product availability questions like "Do you have X?" or "Is X available?" should be classified as general_query, NOT product_recommendation.

Examples:

MEAL_PLANNING (5 examples):
- "plan 3 meals under $30" → meal_planning
- "I need meal ideas for the week" → meal_planning
- "create a shopping list for 5 dinners" → meal_planning
- "help me plan meals for a family of 4" → meal_planning
- "what should I cook this week with $50 budget" → meal_planning

PRODUCT_RECOMMENDATION (5 examples):
- "suggest low carb snacks" → product_recommendation
- "recommend items on sale" → product_recommendation
- "what are the best protein options" → product_recommendation
- "can you suggest healthy breakfast foods" → product_recommendation
- "recommend organic products for kids" → product_recommendation

DIETARY_FILTER (5 examples):
- "show me gluten free items" → dietary_filter
- "find vegan products" → dietary_filter
- "what keto options do you have" → dietary_filter
- "display vegetarian alternatives" → dietary_filter
- "filter products for low carb diet" → dietary_filter

GENERAL_QUERY (5 examples):
- "do you have organic milk?" → general_query
- "is there almond milk in stock?" → general_query
- "how do I get delivery?" → general_query
- "what are your store hours?" → general_query
- "do you carry cottage cheese?" → general_query

CART_OPERATION (10 examples):
ADD operations:
- "add bananas to cart" → cart_operation (cart_operation_type: "add")
- "add 2 organic milk to my cart" → cart_operation (cart_operation_type: "add")
- "put cottage cheese in cart" → cart_operation (cart_operation_type: "add")
- "add organic strawberries to shopping cart" → cart_operation (cart_operation_type: "add")
- "add 3 organic walnuts to cart" → cart_operation (cart_operation_type: "add")

DELETE operations:
- "delete bananas from cart" → cart_operation (cart_operation_type: "delete")
- "remove milk from my cart" → cart_operation (cart_operation_type: "delete")
- "take out cottage cheese from cart" → cart_operation (cart_operation_type: "delete")
- "delete organic strawberries from shopping cart" → cart_operation (cart_operation_type: "delete")
- "remove walnuts from my cart" → cart_operation (cart_operation_type: "delete")

VIEW/CLEAR operations:
- "show my cart" → cart_operation (cart_operation_type: "view")
- "what's in my cart" → cart_operation (cart_operation_type: "view")
- "clear my cart" → cart_operation (cart_operation_type: "clear")
- "empty my cart" → cart_operation (cart_operation_type: "clear")

User message: "{message}"

Return only valid JSON.
"""

prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)


def extract_intent(user_message: str) -> dict:
    """Fixed intent extraction that properly handles availability queries"""
    # First check if this is an availability query and force general_query
    message_lower = user_message.lower()
    availability_keywords = ["do you have", "do you carry", "is there", "are there", "available", "in stock", "carry"]
    if any(keyword in message_lower for keyword in availability_keywords):
        print(f"   Detected availability query, forcing general_query")
        return extract_intent_fallback(user_message)
    
    # For non-availability queries, use LLM
    full_prompt = prompt.format(message=user_message)
    response = llm.invoke(full_prompt)

    # Basic LLM fallback handling
    try:
        # Extract JSON from response content
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            intent = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
        
        # Additional validation and fallback for budget extraction
        if intent.get("budget") and intent["budget"] > 100:
            # If budget seems too high, try to extract from message directly
            budget_match = re.search(r'under\s+\$?(\d+)', user_message.lower())
            if budget_match:
                intent["budget"] = int(budget_match.group(1))
                print(f"   Corrected budget from message: ${intent['budget']}")
        
        return intent
    except Exception as e:
        print(f"   LLM extraction failed: {e}")
        # Fallback: try to extract from message directly
        return extract_intent_fallback(user_message)


def extract_intent_fallback(user_message: str) -> dict:
    """Enhanced intent extraction using LLM classification with keyword fallback"""
    
    try:
        # Import the LLM classifier
        from agents.llm_query_classifier import classify_query_with_llm
        
        # Use LLM classification
        llm_result = classify_query_with_llm(user_message)
        
        # Convert LLM result to intent format
        intent = {
            "query_type": llm_result['query_type'],
            "cart_operation_type": None,
            "number_of_meals": None,
            "budget": llm_result.get('extracted_budget'),
            "dietary_preference": None,
            "product_category": None,
            "special_requirements": None
        }
        
        # Extract additional details based on query type
        message_lower = user_message.lower()
        
        # Extract cart operation type for cart operations
        if intent["query_type"] == "cart_operation":
            if any(word in message_lower for word in ['delete', 'remove', 'take out', 'take away']):
                intent["cart_operation_type"] = "delete"
            elif any(word in message_lower for word in ['view', 'show', 'see', 'display']):
                intent["cart_operation_type"] = "view"
            elif any(word in message_lower for word in ['clear', 'empty']):
                intent["cart_operation_type"] = "clear"
            else:
                intent["cart_operation_type"] = "add"  # default
        
        # Extract number of meals for meal planning
        if intent["query_type"] == "meal_planning":
            meals_match = re.search(r'(\d+)\s+meals?', message_lower)
            if meals_match:
                intent["number_of_meals"] = int(meals_match.group(1))
            else:
                intent["number_of_meals"] = 1
        
        # Extract dietary preferences
        if "low carb" in message_lower or "low-carb" in message_lower:
            intent["dietary_preference"] = "low-carb"
        elif "gluten-free" in message_lower or "gluten free" in message_lower:
            intent["dietary_preference"] = "gluten-free"
        elif "vegan" in message_lower:
            intent["dietary_preference"] = "vegan"
        elif "vegetarian" in message_lower:
            intent["dietary_preference"] = "vegetarian"
        elif "keto" in message_lower:
            intent["dietary_preference"] = "keto"
        
        # Extract product category
        if "dairy" in message_lower or "milk" in message_lower:
            intent["product_category"] = "dairy"
        elif "produce" in message_lower or "vegetable" in message_lower or "fruit" in message_lower:
            intent["product_category"] = "produce"
        
        # Extract special requirements
        if "sale" in message_lower or "discount" in message_lower:
            intent["special_requirements"] = "on_sale"
        elif "organic" in message_lower:
            intent["special_requirements"] = "organic"
        
        print(f"   ✅ LLM classification: {intent['query_type']} (confidence: {llm_result.get('confidence', 0):.2f})")
        
        return intent
        
    except Exception as e:
        print(f"   ❌ LLM classification failed, using keyword fallback: {e}")
        return extract_intent_keyword_fallback(user_message)


def extract_intent_keyword_fallback(user_message: str) -> dict:
    """Legacy keyword-based fallback for when LLM fails"""
    message_lower = user_message.lower()
    
    # Default values
    intent = {
        "query_type": "general_query",
        "cart_operation_type": None,
        "number_of_meals": None,
        "budget": None,
        "dietary_preference": None,
        "product_category": None,
        "special_requirements": None
    }
    
    # Check for product availability keywords (should be general_query)
    availability_keywords = [
        "do you have", "do you carry", "is there", "are there", "available", "in stock", "carry",
        "what is the price", "how much does", "cost of", "price of", "is available", "available in stock"
    ]
    if any(keyword in message_lower for keyword in availability_keywords):
        intent["query_type"] = "general_query"
        return intent  # Return early for availability queries
    
    # Check for meal planning keywords (comprehensive list)
    meal_keywords = [
        "meal", "meals", "plan", "planning", "cook", "recipe", "dinner", "lunch", "breakfast",
        "shopping list", "grocery list", "meal ideas", "what should i cook", "family meals",
        "weekly meals", "meal prep", "food planning", "dinner ideas", "lunch ideas"
    ]
    if any(keyword in message_lower for keyword in meal_keywords):
        intent["query_type"] = "meal_planning"
        
        # Extract number of meals
        meals_match = re.search(r'(\d+)\s+meals?', message_lower)
        if meals_match:
            intent["number_of_meals"] = int(meals_match.group(1))
        else:
            # Default to 3 meals if not specified
            intent["number_of_meals"] = 1
    
    # Check for substitution keywords FIRST (before product recommendations)
    substitution_keywords = [
        "substitute", "alternative", "replacement", "instead of", "replace", "swap", "similar to",
        "what can i use instead", "substitution for", "alternative to"
    ]
    if any(keyword in message_lower for keyword in substitution_keywords):
        intent["query_type"] = "substitution_request"
        return intent  # Return early for substitution queries
    
    # Check for cart operation keywords (including delete/view/clear)
    cart_add_keywords = [
        "add", "put", "place", "add to cart", "add to my cart", "add to shopping cart",
        "put in cart", "place in cart", "add to basket", "put in basket"
    ]
    cart_delete_keywords = [
        "delete", "remove", "take out", "take away", "delete from cart", "remove from cart",
        "take out from cart", "remove from my cart", "delete from my cart"
    ]
    cart_view_keywords = [
        "view cart", "show cart", "see cart", "my cart", "cart contents", "what's in my cart"
    ]
    cart_clear_keywords = [
        "clear cart", "empty cart", "clear my cart", "empty my cart"
    ]
    
    if any(keyword in message_lower for keyword in cart_add_keywords):
        intent["query_type"] = "cart_operation"
        intent["cart_operation_type"] = "add"
        return intent  # Return early for cart add operations
    elif any(keyword in message_lower for keyword in cart_delete_keywords):
        intent["query_type"] = "cart_operation"
        intent["cart_operation_type"] = "delete"
        return intent  # Return early for cart delete operations
    elif any(keyword in message_lower for keyword in cart_view_keywords):
        intent["query_type"] = "cart_operation"
        intent["cart_operation_type"] = "view"
        return intent  # Return early for cart view operations
    elif any(keyword in message_lower for keyword in cart_clear_keywords):
        intent["query_type"] = "cart_operation"
        intent["cart_operation_type"] = "clear"
        return intent  # Return early for cart clear operations
    
    # Check for product recommendation keywords (comprehensive list)
    product_keywords = [
        "suggest", "recommend", "recommendation", "what should", "what can", "best",
        "top", "favorite", "popular", "trending", "new", "fresh", "quality", "premium",
        "healthy options", "good choices", "what's good", "what's popular"
    ]
    if any(keyword in message_lower for keyword in product_keywords):
        if intent["query_type"] != "meal_planning":
            intent["query_type"] = "product_recommendation"
    
    # Check for dietary filter keywords (comprehensive list)
    dietary_keywords = [
        "gluten-free", "gluten free", "vegan", "vegetarian", "keto", "low-carb", "low carb",
        "dairy-free", "dairy free", "paleo", "whole30", "mediterranean", "plant-based",
        "show me", "find", "filter", "display", "what", "options", "alternatives"
    ]
    if any(keyword in message_lower for keyword in dietary_keywords):
        if intent["query_type"] not in ["meal_planning", "product_recommendation"]:
            intent["query_type"] = "dietary_filter"
    
    # Extract dietary preference (comprehensive list)
    if "low carb" in message_lower or "low-carb" in message_lower:
        intent["dietary_preference"] = "low-carb"
    elif "gluten-free" in message_lower or "gluten free" in message_lower:
        intent["dietary_preference"] = "gluten-free"
    elif "vegan" in message_lower:
        intent["dietary_preference"] = "vegan"
    elif "vegetarian" in message_lower:
        intent["dietary_preference"] = "vegetarian"
    elif "keto" in message_lower:
        intent["dietary_preference"] = "keto"
    elif "dairy-free" in message_lower or "dairy free" in message_lower:
        intent["dietary_preference"] = "dairy-free"
    elif "paleo" in message_lower:
        intent["dietary_preference"] = "paleo"
    elif "plant-based" in message_lower or "plant based" in message_lower:
        intent["dietary_preference"] = "plant-based"
    
    # Extract product category (comprehensive list)
    if "dairy" in message_lower or "milk" in message_lower or "cheese" in message_lower or "yogurt" in message_lower:
        intent["product_category"] = "dairy"
    elif "produce" in message_lower or "vegetable" in message_lower or "fruit" in message_lower or "fresh" in message_lower:
        intent["product_category"] = "produce"
    elif "meat" in message_lower or "chicken" in message_lower or "beef" in message_lower or "pork" in message_lower:
        intent["product_category"] = "meat"
    elif "pantry" in message_lower or "grain" in message_lower or "pasta" in message_lower or "rice" in message_lower:
        intent["product_category"] = "pantry"
    elif "frozen" in message_lower:
        intent["product_category"] = "frozen"
    elif "beverage" in message_lower or "drink" in message_lower or "juice" in message_lower:
        intent["product_category"] = "beverages"
    
    # Extract special requirements (comprehensive list)
    if "sale" in message_lower or "discount" in message_lower or "deal" in message_lower or "promotion" in message_lower:
        intent["special_requirements"] = "on_sale"
    elif "organic" in message_lower:
        intent["special_requirements"] = "organic"
    elif "fresh" in message_lower:
        intent["special_requirements"] = "fresh"
    elif "local" in message_lower:
        intent["special_requirements"] = "local"
    elif "premium" in message_lower or "high quality" in message_lower:
        intent["special_requirements"] = "premium"
    
    # Extract budget (comprehensive patterns)
    budget_patterns = [
        r'under\s+\$?(\d+)',
        r'less than\s+\$?(\d+)',
        r'within\s+\$?(\d+)',
        r'budget\s+of\s+\$?(\d+)',
        r'\$?(\d+)\s+budget',
        r'around\s+\$?(\d+)',
        r'about\s+\$?(\d+)'
    ]
    
    for pattern in budget_patterns:
        budget_match = re.search(pattern, user_message.lower())
        if budget_match:
            intent["budget"] = int(budget_match.group(1))
            break
    
    return intent 