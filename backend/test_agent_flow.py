# test_agent_flow.py
import asyncio
from langgraph.shopping_graph import shopping_graph
from agents.general_query_agent import process_conversation, handle_general_query
from agents.intent_agent import extract_intent
from agents.preference_agent import get_or_create_user_profile
from agents.meal_planner_agent import plan_meals, get_product_recommendations
from agents.basket_builder_agent import build_basket
from agents.stock_checker_agent import check_stock_and_promos
from agents.feedback_agent import learn_from_feedback
from decimal import Decimal

def get_user_confirmation(prompt: str) -> bool:
    """Get user confirmation for proceeding with a step"""
    while True:
        response = input(f"\n{prompt} (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def collect_user_feedback(final_cart: list, query_type: str = "meal_planning", product_recommendations: dict = None) -> dict:
    """Collect user feedback on the final cart or recommendations"""
    print("\n" + "="*50)
    print("🎯 FEEDBACK COLLECTION")
    print("="*50)
    
    feedback = {
        "overall_satisfaction": "",
        "liked_items": [],
        "disliked_items": [],
        "suggestions": "",
        "will_purchase": False,
        "query_type": query_type
    }
    
    # Overall satisfaction
    print("\nHow satisfied are you with these recommendations?")
    print("1. Very satisfied")
    print("2. Satisfied") 
    print("3. Neutral")
    print("4. Dissatisfied")
    print("5. Very dissatisfied")
    
    while True:
        try:
            rating = int(input("Enter your rating (1-5): "))
            if 1 <= rating <= 5:
                feedback["overall_satisfaction"] = str(rating)
                break
            else:
                print("Please enter a number between 1 and 5.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Handle different query types
    if query_type in ["meal_planning", "product_recommendation", "dietary_filter"] and final_cart:
        # Items feedback for all cart-based queries
        print(f"\nYou have {len(final_cart)} items in your cart:")
        for i, item in enumerate(final_cart, 1):
            price = item.get('discounted_price', item.get('price', 0))
            replacement = item.get('replacement', '')
            replacement_text = f" [Replaced with: {replacement}]" if replacement else ""
            print(f"{i}. {item.get('name', 'Unknown')} - ${price}{replacement_text}")
        
        # Liked items
        print("\nWhich items do you like? (Enter item numbers separated by commas, or 'none'):")
        liked_input = input("Liked items: ").strip()
        if liked_input.lower() != 'none':
            try:
                # Handle both numbers and names
                if liked_input.isdigit():
                    # Single number
                    index = int(liked_input) - 1
                    if 0 <= index < len(final_cart):
                        feedback["liked_items"].append(final_cart[index].get('name'))
                else:
                    # Try to parse as comma-separated numbers or names
                    parts = [x.strip() for x in liked_input.split(',')]
                    for part in parts:
                        if part.isdigit():
                            # It's a number
                            index = int(part) - 1
                            if 0 <= index < len(final_cart):
                                feedback["liked_items"].append(final_cart[index].get('name'))
                        else:
                            # It's a name - find matching item
                            for item in final_cart:
                                if part.lower() in item.get('name', '').lower():
                                    feedback["liked_items"].append(item.get('name'))
                                    break
            except (ValueError, IndexError):
                print("Invalid input. Skipping liked items.")
        
        # Disliked items
        print("\nWhich items do you dislike? (Enter item numbers separated by commas, or 'none'):")
        disliked_input = input("Disliked items: ").strip()
        if disliked_input.lower() != 'none':
            try:
                # Handle both numbers and names
                if disliked_input.isdigit():
                    # Single number
                    index = int(disliked_input) - 1
                    if 0 <= index < len(final_cart):
                        feedback["disliked_items"].append(final_cart[index].get('name'))
                else:
                    # Try to parse as comma-separated numbers or names
                    parts = [x.strip() for x in disliked_input.split(',')]
                    for part in parts:
                        if part.isdigit():
                            # It's a number
                            index = int(part) - 1
                            if 0 <= index < len(final_cart):
                                feedback["disliked_items"].append(final_cart[index].get('name'))
                        else:
                            # It's a name - find matching item
                            for item in final_cart:
                                if part.lower() in item.get('name', '').lower():
                                    feedback["disliked_items"].append(item.get('name'))
                                    break
            except (ValueError, IndexError):
                print("Invalid input. Skipping disliked items.")
        
        # Purchase intent
        print("\nDo you plan to purchase these items?")
        print("1. Yes, I'll buy them")
        print("2. Maybe, I'll think about it")
        print("3. No, I won't buy them")
        
        while True:
            try:
                purchase_choice = int(input("Enter your choice (1-3): "))
                if 1 <= purchase_choice <= 3:
                    feedback["will_purchase"] = (purchase_choice == 1)
                    break
                else:
                    print("Please enter a number between 1 and 3.")
            except ValueError:
                print("Please enter a valid number.")
    
    # Additional suggestions
    print("\nDo you have any suggestions for improving our recommendations?")
    print("(Press Enter to skip)")
    suggestions = input("Your suggestions: ").strip()
    if suggestions:
        feedback["suggestions"] = suggestions
    
    print("\n✅ Thank you for your feedback! This helps us improve our recommendations.")
    return feedback

async def interactive_shopping_assistant():
    """Interactive shopping assistant with step-by-step confirmation and multi-query support"""
    
    print("🎉 Welcome to the AI Shopping Assistant!")
    print("="*60)
    print("I can help you with:")
    print("• Meal planning and recipes")
    print("• Product recommendations (snacks, items on sale, etc.)")
    print("• Dietary filtering (gluten-free, vegan, etc.)")
    print("• General queries (delivery, store info, etc.)")
    print()
    print("I'll ask for your confirmation at each step to ensure you're happy with the recommendations.")
    print()
    
    # Step 1: Get user input
    print("📝 STEP 1: Getting Your Request")
    print("-" * 30)
    user_id = input("Enter your User ID: ").strip()
    message = input("Enter your shopping request: ").strip()
    
    if not user_id or not message:
        print("❌ Error: User ID and message are required!")
        return
    
    print(f"\n✅ Got it! Processing request for user: {user_id}")
    print(f"📋 Your request: {message}")
    
    # Step 2: Intent Extraction
    print("\n🧭 STEP 2: Understanding Your Intent")
    print("-" * 30)
    print("Analyzing your request to understand what you need...")
    
    intent = extract_intent(message)
    query_type = intent.get("query_type", "meal_planning")
    
    print(f"✅ Extracted intent:")
    print(f"   • Query type: {query_type}")
    print(f"   • Number of meals: {intent.get('number_of_meals', 'N/A')}")
    print(f"   • Budget: ${intent.get('budget', 'N/A')}")
    print(f"   • Dietary preference: {intent.get('dietary_preference', 'N/A')}")
    print(f"   • Product category: {intent.get('product_category', 'N/A')}")
    print(f"   • Special requirements: {intent.get('special_requirements', 'N/A')}")
    
    if not get_user_confirmation("Does this look correct? Should I proceed?"):
        print("🔄 Let's start over. Please run the script again with clearer instructions.")
        return
    
    # Step 3: User Profile
    print("\n👤 STEP 3: Loading Your Profile")
    print("-" * 30)
    print("Loading your profile and preferences...")
    
    user_profile = get_or_create_user_profile(user_id, intent)
    print(f"✅ Profile loaded:")
    print(f"   • Diet: {user_profile.get('diet', 'Unknown')}")
    print(f"   • Budget limit: ${user_profile.get('budget_limit', 'Unknown')}")
    print(f"   • Meal goal: {user_profile.get('meal_goal', 'Unknown')}")
    
    if user_profile.get('past_purchases'):
        print(f"   • Past purchases: {', '.join(user_profile['past_purchases'][:3])}...")
    
    # Handle different query types
    if query_type == "meal_planning":
        await handle_meal_planning_flow(user_id, message, intent, user_profile)
    elif query_type in ["product_recommendation", "dietary_filter"]:
        await handle_product_recommendation_flow(user_id, message, intent, user_profile)
    elif query_type == "general_query":
        await handle_general_query_flow(user_id, message, intent, user_profile)
    else:
        print(f"❌ Unknown query type: {query_type}")
        return

async def handle_meal_planning_flow(user_id: str, message: str, intent: dict, user_profile: dict):
    """Handle meal planning flow with all existing interactive features"""
    
    if not get_user_confirmation("Should I proceed with finding recipes for you?"):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 4: Meal Planning
    print("\n🍽️ STEP 4: Planning Your Meals")
    print("-" * 30)
    print("Finding the best recipes for your preferences and budget...")
    
    recipes = plan_meals(user_profile)
    
    if not recipes:
        print("❌ No recipes found within your budget and dietary preferences.")
        print("💡 Try increasing your budget or being more flexible with dietary restrictions.")
        return
    
    print(f"\n✅ Found {len(recipes)} recipes for you:")
    total_recipe_cost = sum(Decimal(str(recipe.get('total_cost', 0))) for recipe in recipes)
    for i, recipe in enumerate(recipes, 1):
        cost = recipe.get('total_cost', 0)
        print(f"   {i}. {recipe.get('title')} - ${cost}")
    print(f"   📊 Total recipe cost: ${total_recipe_cost}")
    
    if not get_user_confirmation("Do you want to proceed with building your shopping cart?"):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 5: Basket Building
    print("\n🛒 STEP 5: Building Your Shopping Cart")
    print("-" * 30)
    print("Converting recipes to shopping list and finding products...")
    
    budget_limit = user_profile.get("budget_limit")
    cart = build_basket(recipes, budget_limit)
    
    if not cart:
        print("❌ No products found for the selected recipes.")
        return
    
    print(f"\n✅ Found {len(cart)} products:")
    total_cart_cost = sum(Decimal(str(item.get('price', 0))) for item in cart)
    for i, item in enumerate(cart, 1):
        price = item.get('price', 0)
        print(f"   {i}. {item.get('name')} - ${price}")
    print(f"   📊 Total cart cost: ${total_cart_cost}")
    
    if not get_user_confirmation("Should I check stock availability and apply promotions?"):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 6: Stock and Promotions
    print("\n📦 STEP 6: Checking Stock & Promotions")
    print("-" * 30)
    print("Checking stock availability and applying any available discounts...")
    
    final_cart = check_stock_and_promos(cart)
    
    print(f"\n✅ Final cart with stock and promotions:")
    total_final_cost = Decimal('0')
    for i, item in enumerate(final_cart, 1):
        original_price = item.get('price', 0)
        discounted_price = item.get('discounted_price', original_price)
        total_final_cost += Decimal(str(discounted_price))
        
        replacement = item.get('replacement', '')
        replacement_text = f" [Replaced with: {replacement}]" if replacement else ""
        discount_text = f" (Discounted: ${discounted_price})" if discounted_price != original_price else ""
        
        print(f"   {i}. {item.get('name')} | Original: ${original_price}{discount_text}{replacement_text}")
    
    print(f"   📊 Final total: ${total_final_cost}")
    
    # Step 7: Feedback Collection
    print("\n🎯 STEP 7: Collecting Your Feedback")
    print("-" * 30)
    
    user_feedback = collect_user_feedback(final_cart, "meal_planning")
    
    # Step 8: Learning from Feedback
    print("\n🧠 STEP 8: Learning from Your Feedback")
    print("-" * 30)
    print("Updating your profile with this feedback for better future recommendations...")
    
    feedback_data = {
        "current_cart": final_cart,
        "query_type": "meal_planning",
        **user_feedback
    }
    
    learn_from_feedback(user_id, feedback_data)
    
    # Final Summary
    print("\n" + "="*50)
    print("🎉 SHOPPING SESSION COMPLETE!")
    print("="*50)
    print(f"👤 User: {user_id}")
    print(f"📋 Request: {message}")
    print(f"🍽️ Recipes selected: {len(recipes)}")
    print(f"🛒 Products in cart: {len(final_cart)}")
    print(f"💰 Total cost: ${total_final_cost}")
    print(f"⭐ Satisfaction rating: {user_feedback['overall_satisfaction']}/5")
    print(f"🛍️ Purchase intent: {'Yes' if user_feedback['will_purchase'] else 'No'}")
    
    print("\nThank you for using the AI Shopping Assistant!")
    print("Your preferences have been saved for better future recommendations.")
    print("="*50)

async def handle_product_recommendation_flow(user_id: str, message: str, intent: dict, user_profile: dict):
    """Handle product recommendation flow - directly suggest products based on diet preference"""
    
    query_type = intent.get("query_type", "product_recommendation")
    dietary_preference = intent.get("dietary_preference", "general")
    
    if query_type == "dietary_filter":
        prompt = f"Should I proceed with finding {dietary_preference} products for you?"
    else:
        prompt = "Should I proceed with finding product recommendations for you?"
    
    if not get_user_confirmation(prompt):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 4: Product Recommendations
    print(f"\n🛒 STEP 4: Finding Product Recommendations")
    print("-" * 30)
    
    if query_type == "dietary_filter":
        print(f"Finding the best {dietary_preference} products for your preferences...")
    else:
        print("Finding the best products for your dietary preferences...")
    
    recommendations = get_product_recommendations(intent, user_profile)
    products = recommendations.get("products", [])
    message_text = recommendations.get("message", "No recommendations available.")
    
    if not products:
        print("❌ No products found matching your criteria.")
        print("💡 Try adjusting your preferences or budget.")
        return
    
    print(f"\n✅ {message_text}")
    print(f"🛒 Found {len(products)} products:")
    total_product_cost = sum(Decimal(str(product.get('price', 0))) for product in products)
    for i, product in enumerate(products, 1):
        price = product.get('price', 0)
        tags = product.get('tags', [])
        tag_text = f" [{', '.join(tags[:2])}]" if tags else ""
        print(f"   {i}. {product.get('name')} - ${price}{tag_text}")
    print(f"   📊 Total product cost: ${total_product_cost}")
    
    if not get_user_confirmation("Do you want to proceed with building your shopping cart from these products?"):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 5: Direct Cart Building (skip recipe conversion)
    print("\n🛒 STEP 5: Building Your Shopping Cart")
    print("-" * 30)
    print("Adding selected products to your shopping cart...")
    
    # For product recommendations, we can directly use the products as cart items
    # but we need to format them properly for the stock checking
    cart = []
    for product in products:
        cart_item = {
            'name': product.get('name'),
            'price': product.get('price'),
            'item_id': product.get('item_id'),
            'tags': product.get('tags', [])
        }
        cart.append(cart_item)
    
    if not cart:
        print("❌ No products available for your cart.")
        return
    
    print(f"\n✅ Added {len(cart)} products to your cart:")
    total_cart_cost = sum(Decimal(str(item.get('price', 0))) for item in cart)
    for i, item in enumerate(cart, 1):
        price = item.get('price', 0)
        print(f"   {i}. {item.get('name')} - ${price}")
    print(f"   📊 Total cart cost: ${total_cart_cost}")
    
    if not get_user_confirmation("Should I check stock availability and apply promotions?"):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 6: Stock and Promotions
    print("\n📦 STEP 6: Checking Stock & Promotions")
    print("-" * 30)
    print("Checking stock availability and applying any available discounts...")
    
    final_cart = check_stock_and_promos(cart)
    
    print(f"\n✅ Final cart with stock and promotions:")
    total_final_cost = Decimal('0')
    for i, item in enumerate(final_cart, 1):
        original_price = item.get('price', 0)
        discounted_price = item.get('discounted_price', original_price)
        total_final_cost += Decimal(str(discounted_price))
        
        replacement = item.get('replacement', '')
        replacement_text = f" [Replaced with: {replacement}]" if replacement else ""
        discount_text = f" (Discounted: ${discounted_price})" if discounted_price != original_price else ""
        
        print(f"   {i}. {item.get('name')} | Original: ${original_price}{discount_text}{replacement_text}")
    
    print(f"   📊 Final total: ${total_final_cost}")
    
    # Step 7: Feedback Collection
    print("\n🎯 STEP 7: Collecting Your Feedback")
    print("-" * 30)
    
    user_feedback = collect_user_feedback(final_cart, query_type, recommendations)
    
    # Step 8: Learning from Feedback
    print("\n🧠 STEP 8: Learning from Your Feedback")
    print("-" * 30)
    print("Updating your profile with this feedback for better future recommendations...")
    
    feedback_data = {
        "current_cart": final_cart,
        "recommended_products": products,
        "query_type": query_type,
        **user_feedback
    }
    
    learn_from_feedback(user_id, feedback_data)
    
    # Final Summary
    print("\n" + "="*50)
    print("🎉 PRODUCT RECOMMENDATION COMPLETE!")
    print("="*50)
    print(f"✅ Successfully found {len(products)} products for you")
    print(f"✅ Built shopping cart with {len(final_cart)} items")
    print(f"✅ Applied stock checks and promotions")
    print(f"✅ Collected and processed your feedback")
    print(f"✅ Updated your profile for better future recommendations")
    print("\nThank you for using our product recommendation system!")
    print("Your preferences have been saved for next time. 👋")

async def handle_general_query_flow(user_id: str, message: str, intent: dict, user_profile: dict):
    """Handle general query flow using the new general_query_agent"""
    
    if not get_user_confirmation("Should I process your general query?"):
        print("🔄 Let's start over. Please run the script again.")
        return
    
    # Step 4: General Query Processing
    print("\n💬 STEP 4: Processing Your Query")
    print("-" * 30)
    print("Analyzing your question and searching our database...")
    
    # Import the general query agent
    from agents.general_query_agent import handle_general_query
    
    # Process the general query
    general_response = handle_general_query(message, user_id, user_profile)
    
    # Display the response
    response_type = general_response.get("type", "unknown")
    response_message = general_response.get("message", "I'm sorry, I couldn't process your query.")
    
    print(f"\n✅ {response_type.upper().replace('_', ' ')} QUERY RESULT:")
    print("-" * 40)
    print(response_message)
    
    # Show additional details based on response type
    if response_type == "product_availability" and general_response.get("found"):
        products = general_response.get("products", [])
        if products:
            print(f"\n📊 Found {len(products)} product(s) in our inventory.")
    
    elif response_type == "past_purchase" and general_response.get("found"):
        purchases = general_response.get("purchases", [])
        if purchases:
            print(f"\n📊 You have {len(purchases)} items in your purchase history.")
    
    elif response_type == "recipe" and general_response.get("found"):
        recipes = general_response.get("recipes", [])
        if recipes:
            print(f"\n📊 Found {len(recipes)} recipe(s) in our database.")
    
    elif response_type == "promotion" and general_response.get("found"):
        promotions = general_response.get("promotions", [])
        if promotions:
            print(f"\n📊 Found {len(promotions)} active promotion(s).")
    
    # Step 5: Feedback Collection
    print("\n🎯 STEP 5: Collecting Your Feedback")
    print("-" * 30)
    
    user_feedback = collect_user_feedback([], "general_query")
    
    # Step 6: Learning from Feedback
    print("\n🧠 STEP 6: Learning from Your Feedback")
    print("-" * 30)
    print("Recording your query preferences for better future assistance...")
    
    feedback_data = {
        "general_response": general_response,
        "query_type": "general_query",
        **user_feedback
    }
    
    learn_from_feedback(user_id, feedback_data)
    
    # Final Summary
    print("\n" + "="*50)
    print("🎉 GENERAL QUERY COMPLETE!")
    print("="*50)
    print(f"✅ Successfully processed your query")
    print(f"✅ Provided relevant information")
    print(f"✅ Collected and processed your feedback")
    print(f"✅ Updated your profile for better future assistance")
    print("\nThank you for using our AI Shopping Assistant!")
    print("Your preferences have been saved for next time. 👋")

async def conversation_session():
    """Start a conversation session that handles both goal-based and casual queries"""
    print("🎉 Welcome to the AI Shopping Assistant!")
    print("="*60)
    print("I can help you with:")
    print("• Detailed meal planning with step-by-step confirmation")
    print("• Product information and availability")
    print("• Current sales and discounts")
    print("• Dietary recommendations")
    print("• General store information")
    print("• Your purchase history")
    print("• Recipe information and cooking tips")
    print("\nFor meal planning requests, I'll guide you through each step!")
    print("For casual queries, I'll provide immediate helpful responses.")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("="*60)
    
    user_id = input("Enter your User ID: ").strip()
    if not user_id:
        user_id = "demo_user"
        print(f"Using default User ID: {user_id}")
    
    while True:
        try:
            # Get user input
            user_input = input(f"\n{user_id}: ").strip()
            
            # Check for exit conditions
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("👋 Thank you for using the AI Shopping Assistant! Have a great day!")
                break
            
            if not user_input:
                print("🤖 Please enter a message or type 'quit' to exit.")
                continue
            
            # Process the message using conversation agent
            print("\n🤖 Processing your request...")
            conv_result = process_conversation(user_input)
            classification = conv_result['classification']
            query_type = conv_result.get('query_type', 'general_query')
            
            print(f"✅ Message classified as: {classification}")
            print(f"✅ Query type: {query_type}")
            
            if classification == "GOAL" and query_type != "general_query":
                # Run the detailed interactive flow for goal-based queries
                print("🎯 This appears to be a goal-based shopping request.")
                # Skip the LLM response and go directly to meal planning
                print("🤖 Assistant: I'll help you with detailed meal planning and shopping!")
                
                # Show appropriate confirmation message based on query type
                if query_type == "meal_planning":
                    confirmation_prompt = "Should I proceed with detailed meal planning?"
                elif query_type in ["product_recommendation", "dietary_filter"]:
                    confirmation_prompt = "Should I build products for your cart?"
                else:
                    confirmation_prompt = "Should I proceed with detailed shopping assistance?"
                
                if get_user_confirmation(confirmation_prompt):
                    await interactive_shopping_assistant_with_input(user_id, user_input)
                else:
                    print("🤖 Assistant: No problem! Feel free to ask me anything else.")
            else:
                # Handle casual queries or general queries directly
                response = conv_result['response']
                print(f"🤖 Assistant: {response}")
                
                # For general queries, also try to provide additional help
                if query_type == "general_query" and any(keyword in user_input.lower() for keyword in ['available', 'have', 'recipe', 'history', 'promotion', 'delivery']):
                    print("\n💡 Would you like me to provide more detailed information about this topic?")
                    if get_user_confirmation("Should I search our database for more specific information?"):
                        # Check if this is a product availability query that needs broader search
                        user_input_lower = user_input.lower()
                        if any(keyword in user_input_lower for keyword in ["do you have", "is there", "available", "in stock", "carry"]):
                            # Extract the product category from the original query
                            product_category = None
                            if "milk" in user_input_lower:
                                product_category = "milk"
                            elif "bread" in user_input_lower:
                                product_category = "bread"
                            elif "cheese" in user_input_lower:
                                product_category = "cheese"
                            elif "yogurt" in user_input_lower:
                                product_category = "yogurt"
                            elif "butter" in user_input_lower:
                                product_category = "butter"
                            elif "eggs" in user_input_lower:
                                product_category = "eggs"
                            elif "meat" in user_input_lower or "chicken" in user_input_lower or "beef" in user_input_lower:
                                product_category = "meat"
                            elif "vegetables" in user_input_lower or "vegetable" in user_input_lower:
                                product_category = "vegetables"
                            elif "fruits" in user_input_lower or "fruit" in user_input_lower:
                                product_category = "fruits"
                            
                            if product_category:
                                # Search for all products in that category
                                from agents.general_query_agent import search_products_by_name
                                all_products = search_products_by_name(product_category)
                                
                                if all_products:
                                    # Format the response to show all products in that category
                                    print(f"\n📊 Here are all the {product_category} products we have in stock:")
                                    print("-" * 50)
                                    for i, product in enumerate(all_products, 1):
                                        price = product.get('price', 0)
                                        tags = product.get('tags', [])
                                        tag_text = f" [{', '.join(tags[:2])}]" if tags else ""
                                        print(f"   {i}. {product.get('name')} - ${price}{tag_text}")
                                    
                                    # Collect feedback for general queries
                                    print("\n🎯 Quick Feedback:")
                                    print("How helpful was this information? (1-5):")
                                    try:
                                        rating = int(input("Rating: "))
                                        if 1 <= rating <= 5:
                                            feedback_data = {
                                                "general_response": {"type": "product_availability", "products": all_products, "category": product_category},
                                                "query_type": "general_query",
                                                "overall_satisfaction": str(rating)
                                            }
                                            learn_from_feedback(user_id, feedback_data)
                                            print("✅ Thank you for your feedback!")
                                    except ValueError:
                                        print("✅ Thank you for using our service!")
                                else:
                                    print(f"❌ No {product_category} products found in our inventory.")
                            else:
                                # Fallback to original general query logic
                                user_profile = get_or_create_user_profile(user_id, {})
                                general_response = handle_general_query(user_input, user_id, user_profile)
                                
                                if general_response.get('found'):
                                    print(f"\n📊 Additional Information:")
                                    print(general_response.get('message', ''))
                                    
                                    # Collect feedback for general queries
                                    print("\n🎯 Quick Feedback:")
                                    print("How helpful was this information? (1-5):")
                                    try:
                                        rating = int(input("Rating: "))
                                        if 1 <= rating <= 5:
                                            feedback_data = {
                                                "general_response": general_response,
                                                "query_type": "general_query",
                                                "overall_satisfaction": str(rating)
                                            }
                                            learn_from_feedback(user_id, feedback_data)
                                            print("✅ Thank you for your feedback!")
                                    except ValueError:
                                        print("✅ Thank you for using our service!")
                        else:
                            # Use the general query agent for more detailed responses
                            user_profile = get_or_create_user_profile(user_id, {})
                            general_response = handle_general_query(user_input, user_id, user_profile)
                            
                            if general_response.get('found'):
                                print(f"\n📊 Additional Information:")
                                print(general_response.get('message', ''))
                                
                                # Collect feedback for general queries
                                print("\n🎯 Quick Feedback:")
                                print("How helpful was this information? (1-5):")
                                try:
                                    rating = int(input("Rating: "))
                                    if 1 <= rating <= 5:
                                        feedback_data = {
                                            "general_response": general_response,
                                            "query_type": "general_query",
                                            "overall_satisfaction": str(rating)
                                        }
                                        learn_from_feedback(user_id, feedback_data)
                                        print("✅ Thank you for your feedback!")
                                except ValueError:
                                    print("✅ Thank you for using our service!")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using the AI Shopping Assistant!")
            break
        except Exception as e:
            print(f"❌ Sorry, I encountered an error: {str(e)}")
            print("🤖 Assistant: Please try again or ask me something else!")
            continue

async def interactive_shopping_assistant_with_input(user_id: str, message: str):
    """Interactive shopping assistant with pre-provided user input"""
    print(f"\n🎯 GOAL-BASED SHOPPING FLOW")
    print("="*60)
    print(f"👤 User: {user_id}")
    print(f"📋 Request: {message}")
    print("="*60)
    
    # Step 1: Intent Extraction
    print("\n🧭 STEP 1: Understanding Your Intent")
    print("-" * 30)
    print("Analyzing your request to understand what you need...")
    
    intent = extract_intent(message)
    query_type = intent.get("query_type", "meal_planning")
    
    print(f"✅ Extracted intent:")
    print(f"   • Query type: {query_type}")
    print(f"   • Number of meals: {intent.get('number_of_meals', 'N/A')}")
    print(f"   • Budget: ${intent.get('budget', 'N/A')}")
    print(f"   • Dietary preference: {intent.get('dietary_preference', 'N/A')}")
    print(f"   • Product category: {intent.get('product_category', 'N/A')}")
    print(f"   • Special requirements: {intent.get('special_requirements', 'N/A')}")
    
    if not get_user_confirmation("Does this look correct? Should I proceed?"):
        print("🔄 Let's start over. Please run the script again with clearer instructions.")
        return
    
    # Step 2: User Profile
    print("\n👤 STEP 2: Loading Your Profile")
    print("-" * 30)
    print("Loading your profile and preferences...")
    
    user_profile = get_or_create_user_profile(user_id, intent)
    print(f"✅ Profile loaded:")
    print(f"   • Diet: {user_profile.get('diet', 'Unknown')}")
    print(f"   • Budget limit: ${user_profile.get('budget_limit', 'Unknown')}")
    print(f"   • Meal goal: {user_profile.get('meal_goal', 'Unknown')}")
    
    if user_profile.get('past_purchases'):
        print(f"   • Past purchases: {', '.join(user_profile['past_purchases'][:3])}...")
    
    # Handle different query types
    if query_type == "meal_planning":
        await handle_meal_planning_flow(user_id, message, intent, user_profile)
    elif query_type in ["product_recommendation", "dietary_filter"]:
        await handle_product_recommendation_flow(user_id, message, intent, user_profile)
    elif query_type == "general_query":
        await handle_general_query_flow(user_id, message, intent, user_profile)
    else:
        print(f"❌ Unknown query type: {query_type}")
        return

if __name__ == "__main__":
    print("🎉 AI Shopping Assistant")
    print("="*40)
    print("Starting in Conversation Mode...")
    print("="*40)
    
    # Start directly in conversation mode (like a typical chatbot)
    asyncio.run(conversation_session())


