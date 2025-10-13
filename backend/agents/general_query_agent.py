# agents/conversation_agent.py
from langchain_core.prompts import ChatPromptTemplate
from bedrock.bedrock_llm import get_bedrock_llm
from dynamo.queries import get_recipes_by_diet_and_budget, get_products_by_names, get_promo_info
from dynamo.client import dynamodb, PRODUCT_TABLE, RECIPE_TABLE, PROMO_TABLE, USER_TABLE
from boto3.dynamodb.conditions import Attr, Key
import re
import json
from decimal import Decimal
from typing import Dict, List, Any

llm = get_bedrock_llm()

# Classification prompt to determine if query is goal-based
CLASSIFICATION_PROMPT = """
You are a smart grocery shopping assistant classifier.
Analyze the user message and determine if it's a GOAL-BASED shopping request or a CASUAL/INFORMATIONAL query.

GOAL-BASED queries are requests to:
- Plan meals within a budget
- Create shopping lists
- Build meal plans
- Shop for specific number of meals
- Get product recommendations (e.g., "suggest gluten-free items", "recommend low-carb snacks")
- Filter products by dietary preferences (e.g., "show me vegan products", "find keto items")
- Get specific product suggestions
- Requests like "I need 3 meals under $50", "Plan my weekly shopping", "Create a meal plan", "suggest gluten-free items", "recommend products on sale"

CASUAL/INFORMATIONAL queries are:
- Greetings (hi, hello, how are you)
- General questions about item availability
- Asking about sales/discounts
- Store information requests
- General conversation
- Questions about delivery, hours, policies

User message: "{message}"

Respond with only one word: "GOAL" or "CASUAL"
"""

# Conversational response prompt for casual queries
CONVERSATION_PROMPT = """
You are a friendly grocery shopping assistant. The user has asked a casual or informational question.
Use the provided context from our store database to give a helpful, conversational response.

Available context:
{context}

User message: "{message}"

Guidelines:
- Be friendly and conversational
- Use the context to provide accurate information
- If asking about items, mention prices and availability
- If asking about dietary preferences, suggest relevant items
- Keep responses concise but helpful
- If you don't have specific information, offer to help in other ways

Response:
"""

class ConversationAgent:
    def __init__(self):
        self.llm = get_bedrock_llm()
        self.classification_prompt = ChatPromptTemplate.from_template(CLASSIFICATION_PROMPT)
        self.conversation_prompt = ChatPromptTemplate.from_template(CONVERSATION_PROMPT)
    
    def classify_query(self, message: str) -> str:
        """Classify if the query is goal-based or casual"""
        try:
            prompt = self.classification_prompt.format(message=message)
            response = self.llm.invoke(prompt)
            
            # Extract the classification
            response_text = response.content if hasattr(response, 'content') else str(response)
            classification = response_text.strip().upper()
            
            # Ensure we get a valid classification
            if "GOAL" in classification:
                return "GOAL"
            elif "CASUAL" in classification:
                return "CASUAL"
            else:
                # Fallback classification based on keywords
                goal_keywords = [
                    "meal", "plan", "budget", "shop", "buy", "cart", "list", 
                    "under $", "within $", "meals for", "weekly", "daily"
                ]
                if any(keyword in message.lower() for keyword in goal_keywords):
                    return "GOAL"
                else:
                    return "CASUAL"
                    
        except Exception as e:
            print(f"   Classification error: {e}")
            # Fallback to keyword-based classification
            goal_keywords = [
                "meal", "plan", "budget", "shop", "buy", "cart", "list",
                "under $", "within $", "meals for", "weekly", "daily",
                "suggest", "recommend", "show me", "find", "gluten-free", "gluten free",
                "vegan", "vegetarian", "keto", "low-carb", "low carb"
            ]
            if any(keyword in message.lower() for keyword in goal_keywords):
                return "GOAL"
            else:
                return "CASUAL"
    
    def get_context_for_query(self, message: str) -> str:
        """Get relevant context from database based on the query"""
        context_parts = []
        
        # Check for dietary preferences
        dietary_keywords = {
            "vegetarian": ["vegetarian", "veggie", "no meat"],
            "vegan": ["vegan", "plant-based"],
            "gluten-free": ["gluten-free", "gluten free", "celiac"],
            "keto": ["keto", "ketogenic", "low-carb"],
            "low-carb": ["low-carb", "low carb"],
            "high-protein": ["high-protein", "high protein", "protein"]
        }
        
        detected_diets = []
        message_lower = message.lower()
        
        for diet, keywords in dietary_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_diets.append(diet)
        
        # Get relevant products and recipes
        if detected_diets:
            for diet in detected_diets:
                products = self.get_products_by_diet(diet)
                recipes = self.get_recipes_by_diet(diet)
                
                if products:
                    product_names = [p.get('name', '') for p in products[:3]]
                    context_parts.append(f"For {diet} diet, we have: {', '.join(product_names)}")
                
                if recipes:
                    recipe_names = [r.get('title', '') for r in recipes[:3]]
                    context_parts.append(f"{diet.capitalize()} recipes: {', '.join(recipe_names)}")
        
        # Check for sales/promotions
        if any(word in message_lower for word in ["sale", "discount", "promotion", "deal"]):
            discounted_items = self.get_discounted_items()
            if discounted_items:
                item_names = [item.get('name', '') for item in discounted_items[:3]]
                context_parts.append(f"Current sales: {', '.join(item_names)}")
        
        # Check for general product availability
        if any(word in message_lower for word in ["available", "have", "stock", "carry"]):
            sample_products = self.get_sample_products()
            if sample_products:
                product_names = [p.get('name', '') for p in sample_products[:5]]
                context_parts.append(f"Available products include: {', '.join(product_names)}")
        
        return "\n".join(context_parts) if context_parts else "We have a wide variety of products and recipes available."
    
    def get_recipes_by_diet(self, diet_type: str) -> List[Dict]:
        """Get recipes by diet type"""
        try:
            response = dynamodb.Table(RECIPE_TABLE).scan(
                FilterExpression=Attr('diet').contains(diet_type)
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting recipes by diet: {e}")
            return []
    
    def get_products_by_diet(self, diet_type: str) -> List[Dict]:
        """Get products by diet type"""
        try:
            response = dynamodb.Table(PRODUCT_TABLE).scan()
            products = response.get('Items', [])
            
            # Filter products by diet tags
            filtered_products = []
            for product in products:
                tags = product.get('tags', [])
                if diet_type in tags or any(diet_type in tag for tag in tags):
                    filtered_products.append(product)
            
            return filtered_products
        except Exception as e:
            print(f"Error getting products by diet: {e}")
            return []
    
    def get_discounted_items(self) -> List[Dict]:
        """Get items with discounts"""
        try:
            response = dynamodb.Table(PROMO_TABLE).scan()
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting discounted items: {e}")
            return []
    
    def search_products_by_keywords(self, message: str) -> List[Dict]:
        """Search products by keywords in the message"""
        try:
            response = dynamodb.Table(PRODUCT_TABLE).scan()
            products = response.get('Items', [])
            
            # Simple keyword matching
            matching_products = []
            message_lower = message.lower()
            
            for product in products:
                product_name = product.get('name', '').lower()
                if any(word in product_name for word in message_lower.split()):
                    matching_products.append(product)
            
            return matching_products
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def get_sample_products(self) -> List[Dict]:
        """Get a sample of available products"""
        try:
            response = dynamodb.Table(PRODUCT_TABLE).scan(Limit=10)
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting sample products: {e}")
            return []
    
    def generate_response(self, message: str) -> str:
        """Generate a conversational response"""
        try:
            # For goal-based queries, provide a simple acknowledgment
            classification = self.classify_query(message)
            if classification == "GOAL":
                return "I'll help you with detailed meal planning and shopping! Let me analyze your request and create a personalized plan for you."
            
            # For casual queries, use the context-based response
            context = self.get_context_for_query(message)
            prompt = self.conversation_prompt.format(context=context, message=message)
            response = self.llm.invoke(prompt)
            
            response_text = response.content if hasattr(response, 'content') else str(response)
            return response_text.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm here to help with your grocery shopping needs! What would you like to know?"

def process_conversation(message: str) -> Dict[str, Any]:
    """Process a conversation message"""
    agent = ConversationAgent()
    classification = agent.classify_query(message)
    
    # Determine the specific query type using the same logic as intent agent
    query_type = determine_query_type(message)
    
    # Only generate LLM response for casual queries or general queries
    if classification == "GOAL" and query_type != "general_query":
        response = "I'll help you with detailed meal planning and shopping! Let me analyze your request and create a personalized plan for you."
    else:
        response = agent.generate_response(message)
    
    # Determine if we should continue to goal-based flow
    # GOAL classification means it's a meal planning request that should go through the full flow
    continue_to_goal = (classification == "GOAL" and query_type != "general_query")
    
    return {
        "classification": classification,
        "query_type": query_type,
        "response": response,
        "message": message,
        "continue_to_goal_flow": continue_to_goal
    }

def determine_query_type(message: str) -> str:
    """Determine the specific query type using LLM classification with keyword fallback"""
    
    try:
        # Import the LLM classifier
        from agents.llm_query_classifier import classify_query_with_llm
        
        # Use LLM classification
        llm_result = classify_query_with_llm(message)
        
        # Return the LLM-classified query type
        print(f"   ✅ LLM query type: {llm_result['query_type']} (confidence: {llm_result.get('confidence', 0):.2f})")
        return llm_result['query_type']
        
    except Exception as e:
        print(f"   ❌ LLM query type classification failed, using keyword fallback: {e}")
        return determine_query_type_keyword_fallback(message)

def determine_query_type_keyword_fallback(message: str) -> str:
    """Legacy keyword-based query type determination for when LLM fails"""
    message_lower = message.lower()
    
    # Check for substitution keywords FIRST (highest priority)
    substitution_keywords = ["substitute", "alternative", "replacement", "instead of", "replace", "swap", "similar to"]
    if any(keyword in message_lower for keyword in substitution_keywords):
        return "substitution_request"
    
    # Check for meal planning keywords
    meal_keywords = ["meal", "meals", "plan", "planning", "cook", "recipe", "dinner", "lunch", "breakfast"]
    if any(keyword in message_lower for keyword in meal_keywords):
        return "meal_planning"
    
    # Check for product recommendation keywords
    product_keywords = ["suggest", "recommend", "show", "find", "item", "product"]
    if any(keyword in message_lower for keyword in product_keywords):
        return "product_recommendation"
    
    # Check for dietary filter keywords
    dietary_keywords = ["gluten-free", "gluten free", "vegan", "vegetarian", "keto", "low-carb", "low carb"]
    if any(keyword in message_lower for keyword in dietary_keywords):
        return "dietary_filter"
    
    # Check for general query keywords
    general_keywords = ["delivery", "hours", "open", "close", "return", "refund", "ebt", "payment", "available", "have", "carry", "stock"]
    if any(keyword in message_lower for keyword in general_keywords):
        return "general_query"
    
    # Default to general query for unrecognized patterns
    return "general_query"

# Add the handle_general_query function for compatibility with shopping graph
def handle_general_query(user_message: str, user_id: str, user_profile: dict = None) -> dict:
    """
    Handle general queries about products, availability, past purchases, etc.
    Enhanced to provide personalized responses based on user data
    Falls back to LLM when DynamoDB doesn't have relevant information
    """
    
    message_lower = user_message.lower()
    
    # Check for substitution requests first (highest priority)
    if is_substitution_query(message_lower):
        return handle_substitution_query(message_lower, user_message)
    
    # Check for recipe queries first (more specific)
    elif is_recipe_query(message_lower):
        return handle_recipe_query(message_lower, user_message)
    
    # Check for past purchase queries
    elif is_past_purchase_query(message_lower):
        return handle_past_purchase_query(user_id, user_profile, message_lower)
    
    # Check for promotional queries
    elif is_promotional_query(message_lower):
        return handle_promotional_query(message_lower, user_message)
    
    # Check for product availability queries
    elif is_product_availability_query(message_lower):
        return handle_product_availability_query(message_lower, user_message)
    
    # Check for delivery/service queries
    elif is_delivery_query(message_lower):
        return handle_delivery_query(message_lower)
    
    # Default response for unrecognized queries - use LLM
    else:
        return handle_unknown_query_with_llm(message_lower, user_message)

def is_substitution_query(message: str) -> bool:
    """Check if query is about product substitutions"""
    substitution_keywords = [
        "substitute", "alternative", "replacement", "instead of", "replace", "swap", 
        "similar to", "equivalent", "like", "can i use", "what can i use", "other than"
    ]
    return any(keyword in message for keyword in substitution_keywords)

def is_product_availability_query(message: str) -> bool:
    """Check if query is about product availability or pricing"""
    availability_keywords = [
        "available", "availabe", "avail", "in stock", "have", "carry", "sell", "find", "get",
        "do you have", "is there", "can i get", "where can i find", "is", "are", "does",
        "stock", "inventory", "cart", "store", "shop",
        # Added price-related keywords
        "cost", "price", "how much", "what's the price", "what is the cost", "price of", "cost of",
        "$", "dollar", "dollars", "expensive", "cheap", "pricing"
    ]
    return any(keyword in message for keyword in availability_keywords)

def handle_substitution_query(message_lower: str, original_message: str) -> dict:
    """Handle product substitution requests"""
    
    # Extract the product name from the substitution query
    product_name = extract_product_from_substitution_query(original_message)
    
    if not product_name:
        return {
            "type": "substitution_request",
            "message": "I'd be happy to suggest substitutes for you. Could you please specify which product you need an alternative for?",
            "substitutes": [],
            "found": False
        }
    
    # Get substitution suggestions
    substitutes = get_product_substitutes(product_name)
    
    if substitutes:
        # Format response with substitute options
        substitute_list = []
        response_message = f"Here are some great substitutes for {product_name}:\n"
        
        for i, substitute in enumerate(substitutes, 1):
            substitute_info = {
                "name": substitute.get("name", ""),
                "price": substitute.get("price", 0),
                "category": substitute.get("category", ""),
                "usage_tip": substitute.get("usage_tip", "")
            }
            substitute_list.append(substitute_info)
            
            price_str = f"${substitute['price']:.2f}" if substitute.get('price') else "Price varies"
            response_message += f"{i}. {substitute['name']} - {price_str}"
            
            if substitute.get('usage_tip'):
                response_message += f" ({substitute['usage_tip']})"
            response_message += "\n"
        
        return {
            "type": "substitution_request",
            "message": response_message.strip(),
            "substitutes": substitute_list,
            "original_product": product_name,
            "found": True
        }
    else:
        return {
            "type": "substitution_request", 
            "message": f"I don't have specific substitute recommendations for {product_name} in our database, but I'd suggest checking with our nutrition specialist or looking for similar products in the same category.",
            "substitutes": [],
            "original_product": product_name,
            "found": False
        }

def extract_product_from_substitution_query(message: str) -> str:
    """Extract product name from substitution query"""
    import re
    
    # Common patterns for substitution queries
    patterns = [
        r"substitute for ([^?.!]+)",
        r"alternative to ([^?.!]+)", 
        r"replacement for ([^?.!]+)",
        r"instead of ([^?.!]+)",
        r"replace ([^?.!]+)",
        r"substitute ([^?.!]+)",
        r"alternative ([^?.!]+)",
        r"what can i use instead of ([^?.!]+)",
        r"what can i use for ([^?.!]+)"
    ]
    
    message_lower = message.lower()
    
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            product = match.group(1).strip()
            # Clean up common words
            product = re.sub(r'\b(the|a|an|some|any)\b', '', product).strip()
            return product
    
    # Fallback: look for common product names
    common_products = ["eggs", "milk", "butter", "flour", "sugar", "oil", "bread", "cheese", "chicken", "beef"]
    for product in common_products:
        if product in message_lower:
            return product
    
    return ""

def get_product_substitutes(product_name: str) -> list:
    """Get substitute products from DynamoDB based on the original product"""
    
    # Predefined substitution mappings for common products
    substitution_mapping = {
        "eggs": [
            {"name": "Applesauce", "price": 2.99, "usage_tip": "1/4 cup per egg for baking"},
            {"name": "Mashed Banana", "price": 0.50, "usage_tip": "1/4 cup per egg, adds sweetness"},
            {"name": "Ground Flaxseed", "price": 4.99, "usage_tip": "1 tbsp + 3 tbsp water per egg"},
            {"name": "Chia Seeds", "price": 6.99, "usage_tip": "1 tbsp + 3 tbsp water per egg"},
            {"name": "Commercial Egg Replacer", "price": 3.49, "usage_tip": "Follow package instructions"}
        ],
        "milk": [
            {"name": "Almond Milk", "price": 3.99, "usage_tip": "1:1 ratio for most recipes"},
            {"name": "Soy Milk", "price": 3.49, "usage_tip": "1:1 ratio, best for baking"},
            {"name": "Oat Milk", "price": 4.49, "usage_tip": "1:1 ratio, creamy texture"},
            {"name": "Coconut Milk", "price": 2.99, "usage_tip": "Rich flavor, great for desserts"},
            {"name": "Rice Milk", "price": 3.79, "usage_tip": "Lighter taste, good for cereals"}
        ],
        "butter": [
            {"name": "Olive Oil", "price": 5.99, "usage_tip": "Use 3/4 amount of oil for baking"},
            {"name": "Coconut Oil", "price": 7.99, "usage_tip": "1:1 ratio when solid"},
            {"name": "Applesauce", "price": 2.99, "usage_tip": "1/2 amount for low-fat baking"},
            {"name": "Avocado", "price": 1.50, "usage_tip": "Mashed, 1:1 ratio for baking"},
            {"name": "Vegan Butter", "price": 4.99, "usage_tip": "1:1 ratio"}
        ],
        "flour": [
            {"name": "Almond Flour", "price": 8.99, "usage_tip": "Use 1:1 ratio, gluten-free"},
            {"name": "Coconut Flour", "price": 6.99, "usage_tip": "Use 1/4 amount, very absorbent"},
            {"name": "Oat Flour", "price": 4.99, "usage_tip": "1:1 ratio, mild flavor"},
            {"name": "Rice Flour", "price": 3.99, "usage_tip": "1:1 ratio, gluten-free"},
            {"name": "Whole Wheat Flour", "price": 3.49, "usage_tip": "1:1 ratio, denser texture"}
        ],
        "sugar": [
            {"name": "Honey", "price": 6.99, "usage_tip": "Use 3/4 amount, reduce liquid"},
            {"name": "Maple Syrup", "price": 8.99, "usage_tip": "Use 3/4 amount, reduce liquid"},
            {"name": "Stevia", "price": 4.99, "usage_tip": "Much less needed, check conversion"},
            {"name": "Coconut Sugar", "price": 5.99, "usage_tip": "1:1 ratio"},
            {"name": "Applesauce", "price": 2.99, "usage_tip": "1/2 amount for moisture"}
        ]
    }
    
    # Check predefined mappings first
    product_lower = product_name.lower()
    if product_lower in substitution_mapping:
        return substitution_mapping[product_lower]
    
    # If not in predefined mappings, try to find similar products from DynamoDB
    try:
        from dynamo.client import dynamodb, PRODUCT_TABLE
        from boto3.dynamodb.conditions import Attr
        
        # Search for products in the same category or with similar tags
        response = dynamodb.Table(PRODUCT_TABLE).scan(
            FilterExpression=Attr('name').contains(product_name) | 
                           Attr('description').contains(product_name) |
                           Attr('category').contains(product_name.split()[0] if product_name else ""),
            Limit=5
        )
        
        products = response.get('Items', [])
        
        # Format products as substitutes
        substitutes = []
        for product in products:
            if product.get('name', '').lower() != product_lower:  # Don't suggest the same product
                substitute = {
                    "name": product.get('name', ''),
                    "price": float(product.get('price', 0)),
                    "category": product.get('category', ''),
                    "usage_tip": "Check product details for usage suggestions"
                }
                substitutes.append(substitute)
        
        return substitutes
        
    except Exception as e:
        print(f"Error querying DynamoDB for substitutes: {e}")
        return []

def handle_product_availability_query(message_lower: str, original_message: str) -> dict:
    """Handle queries about product availability and pricing"""
    
    # Extract product name from query
    product_name = extract_product_name(original_message)
    
    print(f"🔍 Processing query: '{original_message}' → extracted product: '{product_name}'")
    
    if not product_name:
        return {
            "type": "product_availability",
            "message": "I'd be happy to check product availability and pricing for you. Could you please specify which product you're looking for?",
            "products": [],
            "found": False
        }
    
    # Search for product in database
    products = search_products_by_name(product_name)
    
    if products:
        # Determine if this is a price-focused query
        is_price_query = any(keyword in message_lower for keyword in 
                           ['cost', 'price', 'how much', '$', 'expensive', 'cheap'])
        
        # Format response based on query type
        product_info = []
        total_products = len(products)
        
        for i, product in enumerate(products):
            price = float(product.get('price', 0))
            in_stock = product.get('in_stock', True)
            tags = product.get('tags', [])
            description = product.get('description', '')
            
            # Format price
            price_text = f"${price:.2f}" if price > 0 else "Price not available"
            
            # Format tags
            tag_text = f" [{', '.join(tags[:2])}]" if tags else ""
            
            # Format stock status
            status = "✅ In stock" if in_stock else "❌ Out of stock"
            
            # Format product line
            if is_price_query:
                # Price-focused response
                product_line = f"• {product.get('name')} - {price_text}{tag_text}"
                if not in_stock:
                    product_line += " (Currently out of stock)"
            else:
                # Availability-focused response
                product_line = f"• {product.get('name')} - {price_text}{tag_text} ({status})"
            
            # Add description for first few products
            if i < 3 and description:
                product_line += f"\n  💡 {description[:100]}{'...' if len(description) > 100 else ''}"
            
            product_info.append(product_line)
        
        # Create response message
        if is_price_query:
            if total_products == 1:
                response_message = f"📋 **{product_name.title()} Pricing:**\n{product_info[0]}"
            else:
                response_message = f"📋 **Found {total_products} products matching '{product_name}':**\n" + "\n".join(product_info)
        else:
            if total_products == 1:
                response_message = f"✅ **{product_name.title()} Availability:**\n{product_info[0]}"
            else:
                response_message = f"✅ **Found {total_products} products matching '{product_name}':**\n" + "\n".join(product_info)
        
        return {
            "type": "product_availability",
            "message": response_message,
            "products": products,
            "found": True,
            "product_name": product_name,
            "is_price_query": is_price_query
        }
    else:
        # Enhanced no-results handling with related product search
        print(f"❌ No products found for '{product_name}', searching for related products...")
        
        # Try broader search for related products
        related_products = search_related_products(product_name)
        
        if related_products:
            related_info = []
            for product in related_products[:3]:  # Show top 3 related
                price = float(product.get('price', 0))
                price_text = f"${price:.2f}" if price > 0 else "Price varies"
                related_info.append(f"• {product.get('name')} - {price_text}")
            
            response_message = f"❌ I couldn't find '{product_name}' in our inventory.\n\n✨ **However, here are some related products you might be interested in:**\n" + "\n".join(related_info)
            
            return {
                "type": "product_availability", 
                "message": response_message,
                "products": related_products,
                "found": False,
                "product_name": product_name,
                "related_products": related_products
            }
        
        # Final fallback - no related products found
        response_message = f"❌ I couldn't find '{product_name}' or similar products in our current inventory.\n\n💡 **Suggestions:**\n• Try a different spelling or product name\n• Check if we carry this product under a different brand\n• Ask our staff for assistance finding alternatives\n• Browse our full product catalog for similar items"
        
        return {
            "type": "product_availability",
            "message": response_message,
            "products": [],
            "found": False,
            "product_name": product_name
        }

def search_related_products(product_name: str) -> list:
    """Search for related products when exact match fails"""
    try:
        response = dynamodb.Table(PRODUCT_TABLE).scan()
        products = response.get('Items', [])
        
        if not product_name:
            return []
        
        related_products = []
        product_words = product_name.lower().split()
        
        print(f"🔗 Searching for products related to: '{product_name}'")
        
        for product in products:
            product_name_db = product.get('name', '').lower()
            product_description = product.get('description', '').lower()
            product_category = product.get('category', '').lower()
            
            # Check if any word from the search matches category or description
            if any(word in product_category or word in product_description 
                   for word in product_words if len(word) > 2):
                related_products.append(product)
                
            # Check for partial word matches in product names
            elif any(word in product_name_db for word in product_words if len(word) > 2):
                related_products.append(product)
        
        print(f"🔗 Found {len(related_products)} related products")
        return related_products[:10]  # Return top 10 related products
        
    except Exception as e:
        print(f"❌ Error searching related products: {e}")
        return []

def is_past_purchase_query(message: str) -> bool:
    """Check if query is about past purchases"""
    purchase_keywords = [
        "bought", "purchased", "bought before", "previously", "last time",
        "my purchases", "my history", "what i bought", "past orders",
        "shopping history", "order history", "purchase history", "history",
        "what have i bought", "my past", "previous purchases", "before",
        "can i know", "show me my", "tell me about my"
    ]
    return any(keyword in message for keyword in purchase_keywords)

def handle_past_purchase_query(user_id: str, user_profile: dict, message_lower: str) -> dict:
    """Handle queries about user's past purchases"""
    
    if not user_profile:
        return {
            "type": "past_purchase",
            "message": "I don't have access to your purchase history yet. This feature becomes available after you make your first purchase with us.",
            "purchases": [],
            "found": False
        }
    
    past_purchases = user_profile.get('past_purchases', [])
    
    if not past_purchases:
        return {
            "type": "past_purchase",
            "message": "You haven't made any purchases yet. Once you start shopping with us, I'll be able to show you your purchase history.",
            "purchases": [],
            "found": False
        }
    
    # Check for specific product in past purchases
    if "what" in message_lower and any(word in message_lower for word in ["bought", "purchased"]):
        # Show recent purchases
        recent_purchases = past_purchases[-5:]  # Last 5 purchases
        purchase_list = "\n".join([f"• {item}" for item in recent_purchases])
        
        response_message = f"Here are your recent purchases:\n{purchase_list}\n\nYou've made {len(past_purchases)} total purchases with us."
        
        return {
            "type": "past_purchase",
            "message": response_message,
            "purchases": past_purchases,
            "found": True,
            "total_purchases": len(past_purchases)
        }
    
    # Check for specific product
    product_name = extract_product_name_from_purchases(message_lower, past_purchases)
    if product_name:
        if product_name in past_purchases:
            return {
                "type": "past_purchase",
                "message": f"Yes! You have purchased '{product_name}' before. It's in your purchase history.",
                "purchases": [product_name],
                "found": True,
                "product_name": product_name
            }
        else:
            return {
                "type": "past_purchase",
                "message": f"No, you haven't purchased '{product_name}' before. Would you like me to suggest similar products?",
                "purchases": [],
                "found": False,
                "product_name": product_name
            }
    
    # Default response
    return {
        "type": "past_purchase",
        "message": f"You have {len(past_purchases)} items in your purchase history. What specific information would you like to know about your past purchases?",
        "purchases": past_purchases,
        "found": True,
        "total_purchases": len(past_purchases)
    }

def is_recipe_query(message: str) -> bool:
    """Check if query is about recipes"""
    recipe_keywords = [
        "recipe", "cook", "how to make", "ingredients", "ingrideients", "cooking",
        "preparation", "cook time", "instructions", "make", "preparing", "cookbook",
        "dish", "meal", "food", "cuisine", "curry", "pasta", "soup", "salad"
    ]
    return any(keyword in message for keyword in recipe_keywords)

def handle_recipe_query(message_lower: str, original_message: str) -> dict:
    """Handle queries about recipes"""
    
    # Extract recipe name from query
    recipe_name = extract_recipe_name(original_message)
    
    if not recipe_name:
        return {
            "type": "recipe",
            "message": "I'd be happy to help you with recipe information. Could you please specify which recipe you're interested in?",
            "recipes": [],
            "found": False
        }
    
    # Search for recipe in database
    recipes = search_recipes_by_name(recipe_name)
    
    if recipes:
        recipe_info = []
        for recipe in recipes:
            ingredients = recipe.get('ingredients', [])
            cost = recipe.get('total_cost', 0)
            cook_time = recipe.get('cook_time_mins', 0)
            diets = recipe.get('diet', [])
            
            diet_text = f" [{', '.join(diets)}]" if diets else ""
            ingredient_list = ", ".join(ingredients[:5])  # Show first 5 ingredients
            
            recipe_info.append(f"• {recipe.get('title')}{diet_text}\n  Cost: ${cost} | Time: {cook_time} mins\n  Ingredients: {ingredient_list}...")
        
        response_message = f"I found {len(recipes)} recipe(s) matching '{recipe_name}':\n\n" + "\n\n".join(recipe_info)
        
        return {
            "type": "recipe",
            "message": response_message,
            "recipes": recipes,
            "found": True,
            "recipe_name": recipe_name
        }
    else:
        # Try LLM fallback for recipe suggestions
        try:
            llm_prompt = f"""
You are a helpful cooking assistant. A user asked: "{original_message}"

The recipe "{recipe_name}" was not found in our database. Please provide helpful information such as:
- General cooking tips for this type of dish
- Common ingredients typically used
- Alternative recipe names they might be looking for
- Basic cooking instructions for similar dishes

Be friendly and helpful in your response.

Response:"""
            
            llm_response = llm.invoke(llm_prompt)
            llm_message = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
            
            return {
                "type": "recipe",
                "message": f"I'm sorry, I couldn't find any recipes matching '{recipe_name}' in our database.\n\n{llm_message.strip()}",
                "recipes": [],
                "found": False,
                "recipe_name": recipe_name,
                "source": "llm_fallback"
            }
        except Exception as e:
            print(f"LLM fallback error: {e}")
            return {
                "type": "recipe",
                "message": f"I'm sorry, I couldn't find any recipes matching '{recipe_name}'. Would you like me to suggest similar recipes?",
                "recipes": [],
                "found": False,
                "recipe_name": recipe_name
            }

def is_promotional_query(message: str) -> bool:
    """Check if query is about promotions or sales"""
    promo_keywords = [
        "sale", "discount", "promotion", "deal", "offer", "on sale",
        "reduced", "clearance", "special", "bargain"
    ]
    return any(keyword in message for keyword in promo_keywords)

def handle_promotional_query(message_lower: str, original_message: str) -> dict:
    """Handle queries about promotions and sales"""
    
    # Get current promotions
    promotions = get_current_promotions()
    
    if promotions:
        promo_info = []
        for promo in promotions:
            item_name = promo.get('item_name', 'Unknown')
            discount = promo.get('discount_percent', 0)
            replacement = promo.get('replacement_suggestion', '')
            
            replacement_text = f" (Replacement: {replacement})" if replacement else ""
            promo_info.append(f"• {item_name} - {discount}% off{replacement_text}")
        
        response_message = f"Here are our current promotions:\n" + "\n".join(promo_info)
        
        return {
            "type": "promotion",
            "message": response_message,
            "promotions": promotions,
            "found": True
        }
    else:
        return {
            "type": "promotion",
            "message": "We don't have any active promotions at the moment. Check back soon for great deals!",
            "promotions": [],
            "found": False
        }

def is_delivery_query(message: str) -> bool:
    """Check if query is about delivery or services"""
    delivery_keywords = [
        "delivery", "deliver", "shipping", "pickup", "curbside",
        "store hours", "open", "close", "hours", "location",
        "ebt", "payment", "return", "refund"
    ]
    return any(keyword in message for keyword in delivery_keywords)

def handle_delivery_query(message_lower: str) -> dict:
    """Handle queries about delivery and services"""
    
    if "delivery" in message_lower:
        return {
            "type": "delivery",
            "message": "We offer same-day delivery for orders placed before 2 PM. Delivery fees start at $5.99 and free delivery on orders over $35. You can also choose curbside pickup at no additional cost.",
            "found": True
        }
    elif "hours" in message_lower or "open" in message_lower:
        return {
            "type": "hours",
            "message": "Our store hours are:\n• Monday-Friday: 7 AM - 10 PM\n• Saturday: 8 AM - 9 PM\n• Sunday: 8 AM - 8 PM\n\nCurbside pickup is available during all store hours.",
            "found": True
        }
    elif "ebt" in message_lower:
        return {
            "type": "payment",
            "message": "Yes, we accept EBT cards for eligible food items. You can use your EBT card for in-store purchases and online orders. Non-food items and delivery fees cannot be paid with EBT.",
            "found": True
        }
    elif "return" in message_lower or "refund" in message_lower:
        return {
            "type": "returns",
            "message": "We offer a 30-day return policy for most items. Perishable items cannot be returned. For returns, please bring your receipt and the item to any store location.",
            "found": True
        }
    else:
        return {
            "type": "service",
            "message": "I can help you with delivery, store hours, payment methods, and returns. What specific service information do you need?",
            "found": True
        }

def handle_unknown_query(message_lower: str) -> dict:
    """Handle unrecognized queries"""
    return {
        "type": "unknown",
        "message": "I'm not sure I understand your question. I can help you with:\n• Product availability and pricing\n• Your purchase history\n• Recipe information\n• Current promotions and sales\n• Delivery and store services\n\nCould you please rephrase your question?",
        "found": False
    }

def handle_unknown_query_with_llm(message_lower: str, original_message: str) -> dict:
    """Handle unrecognized queries using LLM fallback"""
    try:
        prompt = f"""
You are a helpful grocery shopping assistant. A user asked: "{original_message}"

Please provide a helpful response. You can help with:
- General grocery shopping questions
- Cooking and recipe advice
- Nutritional information
- Shopping tips
- Food storage and preparation
- Healthy eating advice

Provide a friendly, helpful response. If the question is unclear, ask for clarification.

Response:"""

        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "type": "llm_response",
            "message": response_text.strip(),
            "found": True,
            "source": "llm"
        }
    except Exception as e:
        print(f"LLM fallback error: {e}")
        return {
            "type": "unknown",
            "message": "I'm not sure I understand your question. I can help you with:\n• Product availability and pricing\n• Your purchase history\n• Recipe information\n• Current promotions and sales\n• Delivery and store services\n\nCould you please rephrase your question?",
            "found": False
        }

# Helper functions
def extract_product_name(message: str) -> str:
    """Extract product name from query"""
    # Remove common words and extract potential product names
    words = message.split()
    product_words = []
    
    # Common words to skip (expanded for price queries)
    skip_words = {
        'is', 'are', 'do', 'you', 'have', 'any', 'the', 'a', 'an', 'in', 'stock', 'available', 
        'availabe', 'avail', 'carry', 'sell', 'cart', 'store', 'shop', 'there', 'can', 'i', 'get',
        'where', 'find', 'does', 'inventory', 'of', 'for', 'with', 'to', 'from', 'at', 'on', 'by',
        # Added price-related skip words
        'what', 'cost', 'price', 'how', 'much', 'dollar', 'dollars', '$', 'expensive', 'cheap',
        'pricing', 'about', 'tell', 'me', 'details', 'information', 'info'
    }
    
    for word in words:
        # Skip common words
        if word.lower() in skip_words:
            continue
        # Skip punctuation
        if word in [',', '.', '?', '!']:
            continue
        # Skip if it's just a single letter
        if len(word) <= 1:
            continue
        product_words.append(word)
    
    return ' '.join(product_words) if product_words else None

def extract_product_name_from_purchases(message: str, past_purchases: list) -> str:
    """Extract product name from message and check if it's in past purchases"""
    for purchase in past_purchases:
        if purchase.lower() in message.lower():
            return purchase
    return None

def extract_recipe_name(message: str) -> str:
    """Extract recipe name from query"""
    # Similar to product name extraction but for recipes
    words = message.split()
    recipe_words = []
    
    skip_words = {
        'recipe', 'for', 'how', 'to', 'make', 'cook', 'the', 'a', 'an', 'ingredients',
        'ingrideients', 'required', 'needed', 'preparing', 'cooking', 'dish', 'meal',
        'what', 'are', 'is', 'do', 'you', 'have', 'any', 'of', 'with', 'from'
    }
    
    for word in words:
        if word.lower() in skip_words:
            continue
        if word in [',', '.', '?', '!']:
            continue
        if len(word) <= 1:
            continue
        recipe_words.append(word)
    
    return ' '.join(recipe_words) if recipe_words else None

def search_products_by_name(product_name: str) -> list:
    """Enhanced search for products by name in the database with fuzzy matching"""
    try:
        response = dynamodb.Table(PRODUCT_TABLE).scan()
        products = response.get('Items', [])
        
        if not product_name:
            return []
        
        # Enhanced fuzzy matching
        matching_products = []
        exact_matches = []
        partial_matches = []
        related_matches = []
        
        product_name_lower = product_name.lower().strip()
        product_words = product_name_lower.split()
        
        print(f"🔍 Searching for product: '{product_name}' in {len(products)} products")
        
        for product in products:
            product_name_db = product.get('name', '').lower()
            product_description = product.get('description', '').lower()
            product_category = product.get('category', '').lower()
            product_tags = [tag.lower() for tag in product.get('tags', [])]
            
            # Exact match (highest priority)
            if product_name_lower == product_name_db:
                exact_matches.append(product)
                print(f"✅ Exact match found: {product.get('name')}")
            
            # Contains match (second priority)
            elif (product_name_lower in product_name_db or 
                  product_name_db in product_name_lower or
                  product_name_lower in product_description):
                partial_matches.append(product)
                print(f"🎯 Partial match found: {product.get('name')}")
            
            # Word-based matching (third priority)
            elif any(word in product_name_db or word in product_description 
                    for word in product_words if len(word) > 2):
                related_matches.append(product)
                print(f"🔗 Related match found: {product.get('name')}")
            
            # Category/tag matching (fourth priority)
            elif any(word in product_category or 
                    any(word in tag for tag in product_tags)
                    for word in product_words if len(word) > 2):
                related_matches.append(product)
                print(f"📂 Category match found: {product.get('name')}")
        
        # Return results in priority order
        matching_products = exact_matches + partial_matches + related_matches[:5]  # Limit related matches
        
        print(f"📊 Search results: {len(exact_matches)} exact, {len(partial_matches)} partial, {len(related_matches)} related")
        
        return matching_products
        
    except Exception as e:
        print(f"❌ Error searching products: {e}")
        return []

def search_recipes_by_name(recipe_name: str) -> list:
    """Search for recipes by name in the database"""
    try:
        response = dynamodb.Table(RECIPE_TABLE).scan()
        recipes = response.get('Items', [])
        
        # Simple fuzzy matching
        matching_recipes = []
        recipe_name_lower = recipe_name.lower()
        
        for recipe in recipes:
            recipe_title = recipe.get('title', '').lower()
            if recipe_name_lower in recipe_title or recipe_title in recipe_name_lower:
                matching_recipes.append(recipe)
        
        return matching_recipes
    except Exception as e:
        print(f"Error searching recipes: {e}")
        return []

def get_current_promotions() -> list:
    """Get current promotions from the database"""
    try:
        response = dynamodb.Table(PROMO_TABLE).scan()
        promotions = response.get('Items', [])
        
        # Get product names for promotions
        product_response = dynamodb.Table(PRODUCT_TABLE).scan()
        products = {p.get('item_id'): p.get('name') for p in product_response.get('Items', [])}
        
        # Add product names to promotions
        for promo in promotions:
            item_id = promo.get('item_id')
            if item_id in products:
                promo['item_name'] = products[item_id]
        
        return promotions
    except Exception as e:
        print(f"Error getting promotions: {e}")
        return []