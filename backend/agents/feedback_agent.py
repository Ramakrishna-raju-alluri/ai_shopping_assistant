# agents/feedback_agent.py
from dynamo.queries import get_user_profile, update_user_profile
from typing import List, Dict, Any

def learn_from_feedback(user_id: str, feedback: dict) -> str:
    """
    Learn from user feedback and update user profile with past purchases
    Enhanced to be more interactive and conversational
    Enhanced to handle different query types
    """
    
    try:
        # Get current user profile
        user_profile = get_user_profile(user_id)
        
        if not user_profile:
            # New user - demonstrate feedback system
            print(f"\n🎉 Welcome to the feedback system, {user_id}!")
            print("This system learns from your shopping patterns to provide better recommendations.")
            print("In a real implementation, your preferences would be stored and used for future suggestions.")
            return "Welcome! Your preferences will be learned as you shop."
        
        # Extract feedback data based on query type
        query_type = feedback.get("query_type", "meal_planning")
        
        if query_type == "meal_planning":
            return handle_meal_planning_feedback(user_id, user_profile, feedback)
        elif query_type in ["product_recommendation", "dietary_filter"]:
            return handle_product_recommendation_feedback(user_id, user_profile, feedback)
        elif query_type == "general_query":
            return handle_general_query_feedback(user_id, user_profile, feedback)
        else:
            return handle_general_feedback(user_id, user_profile, feedback)
        
    except Exception as e:
        print(f"❌ Error updating user feedback: {str(e)}")
        return "Feedback recorded (with some issues)."

def handle_meal_planning_feedback(user_id: str, user_profile: dict, feedback: dict) -> str:
    """Handle feedback for meal planning queries"""
    current_items = feedback.get("current_cart", [])
    overall_satisfaction = feedback.get("overall_satisfaction", "")
    will_purchase = feedback.get("will_purchase", False)
    liked_items = feedback.get("liked_items", [])
    disliked_items = feedback.get("disliked_items", [])
    
    print(f"\n🧠 LEARNING FROM MEAL PLANNING FEEDBACK")
    print("-" * 40)
    
    # Satisfaction analysis
    if overall_satisfaction:
        rating = int(overall_satisfaction)
        if rating >= 4:
            print("😊 Great! You're satisfied with the meal planning.")
        elif rating == 3:
            print("😐 You're neutral about the meal planning. We'll try to improve!")
        else:
            print("😔 We're sorry you weren't satisfied. We'll work on better meal planning.")
    
    # Purchase intent analysis
    if will_purchase:
        print("🛍️ Excellent! You plan to purchase these meal items.")
    else:
        print("🤔 You're not planning to purchase. We'll adjust our meal recommendations.")
    
    # Update past purchases with current items (simulating purchase completion)
    if current_items:
        item_names = [item.get("name", "") for item in current_items if item.get("name")]
        
        # Add new items to past purchases (keep last 10 items)
        existing_purchases = user_profile.get("past_purchases", [])
        updated_purchases = existing_purchases + item_names
        updated_purchases = updated_purchases[-10:]  # Keep last 10 items
        
        # Update user profile
        user_profile["past_purchases"] = updated_purchases
        
        print(f"📝 Updated your purchase history with {len(item_names)} meal items")
        print(f"🔄 Your recent purchases now include: {', '.join(updated_purchases[-5:])}")
    
    # Update cuisine preferences based on liked/disliked items
    if liked_items or disliked_items:
        update_cuisine_preferences(user_profile, liked_items, disliked_items)
    
    # Save updated profile
    update_user_profile(user_id, user_profile)
    
    return f"Thank you! We've updated your meal planning preferences for better future recommendations."

def update_cuisine_preferences(user_profile: dict, liked_items: list, disliked_items: list):
    """Update cuisine preferences based on user feedback"""
    from agents.preference_agent import RECIPE_CATEGORIES
    
    current_cuisines = user_profile.get("preferred_cuisines", [])
    
    # Analyze liked items for cuisine patterns
    liked_cuisines = []
    for item in liked_items:
        item_lower = item.lower()
        for cuisine, keywords in RECIPE_CATEGORIES.items():
            for keyword in keywords:
                if keyword in item_lower:
                    liked_cuisines.append(cuisine)
                    break
    
    # Analyze disliked items for cuisine patterns
    disliked_cuisines = []
    for item in disliked_items:
        item_lower = item.lower()
        for cuisine, keywords in RECIPE_CATEGORIES.items():
            for keyword in keywords:
                if keyword in item_lower:
                    disliked_cuisines.append(cuisine)
                    break
    
    # Update cuisine preferences
    if liked_cuisines:
        # Add liked cuisines if not already present
        for cuisine in liked_cuisines:
            if cuisine not in current_cuisines:
                current_cuisines.append(cuisine)
                print(f"   Added {cuisine} to your preferred cuisines")
    
    if disliked_cuisines:
        # Remove disliked cuisines
        for cuisine in disliked_cuisines:
            if cuisine in current_cuisines:
                current_cuisines.remove(cuisine)
                print(f"   Removed {cuisine} from your preferred cuisines")
    
    # Keep only unique cuisines and limit to 5
    unique_cuisines = list(set(current_cuisines))
    user_profile["preferred_cuisines"] = unique_cuisines[:5]
    
    if liked_cuisines or disliked_cuisines:
        print(f"   Updated cuisine preferences: {', '.join(user_profile['preferred_cuisines'])}")

def handle_product_recommendation_feedback(user_id: str, user_profile: dict, feedback: dict) -> str:
    """Handle feedback for product recommendation and dietary filter queries"""
    current_items = feedback.get("current_cart", [])
    recommended_products = feedback.get("recommended_products", [])
    overall_satisfaction = feedback.get("overall_satisfaction", "")
    will_purchase = feedback.get("will_purchase", False)
    liked_items = feedback.get("liked_items", [])
    disliked_items = feedback.get("disliked_items", [])
    query_type = feedback.get("query_type", "product_recommendation")
    
    print(f"\n🧠 LEARNING FROM PRODUCT RECOMMENDATION FEEDBACK")
    print("-" * 40)
    
    # Satisfaction analysis
    if overall_satisfaction:
        rating = int(overall_satisfaction)
        if rating >= 4:
            print("😊 Great! You're satisfied with the product recommendations.")
        elif rating == 3:
            print("😐 You're neutral about the recommendations. We'll try to improve!")
        else:
            print("😔 We're sorry you weren't satisfied. We'll work on better product suggestions.")
    
    # Purchase intent analysis
    if will_purchase:
        print("🛍️ Excellent! You plan to purchase these products.")
    else:
        print("🤔 You're not planning to purchase. We'll adjust our product recommendations.")
    
    # Update past purchases with current items (simulating purchase completion)
    if current_items:
        item_names = [item.get("name", "") for item in current_items if item.get("name")]
        
        # Add new items to past purchases (keep last 10 items)
        existing_purchases = user_profile.get("past_purchases", [])
        updated_purchases = existing_purchases + item_names
        updated_purchases = updated_purchases[-10:]  # Keep last 10 items
        
        # Update user profile
        user_profile["past_purchases"] = updated_purchases
        
        print(f"📝 Updated your purchase history with {len(item_names)} products")
        print(f"🔄 Your recent purchases now include: {', '.join(updated_purchases[-5:])}")
    
    # Analyze product preferences based on liked/disliked items
    if liked_items or disliked_items:
        update_product_preferences(user_profile, liked_items, disliked_items)
    
    # Update dietary preferences based on product feedback
    if recommended_products:
        update_dietary_preferences_from_products(user_profile, recommended_products, liked_items, disliked_items)
    
    # Save updated profile
    update_user_profile(user_id, user_profile)
    
    query_type_text = "product recommendations" if query_type == "product_recommendation" else "dietary filter"
    return f"Thank you! We've updated your {query_type_text} preferences for better future suggestions."

def update_product_preferences(user_profile: dict, liked_items: list, disliked_items: list):
    """Update product preferences based on user feedback"""
    print("🔄 Analyzing your product preferences...")
    
    # Analyze liked items for product patterns
    liked_categories = []
    for item in liked_items:
        item_lower = item.lower()
        if any(keyword in item_lower for keyword in ['organic', 'natural']):
            liked_categories.append('organic')
        if any(keyword in item_lower for keyword in ['protein', 'meat', 'fish', 'eggs']):
            liked_categories.append('protein')
        if any(keyword in item_lower for keyword in ['vegetable', 'veggie', 'greens']):
            liked_categories.append('vegetables')
        if any(keyword in item_lower for keyword in ['fruit', 'berry']):
            liked_categories.append('fruits')
        if any(keyword in item_lower for keyword in ['nut', 'seed']):
            liked_categories.append('nuts_seeds')
    
    # Update user preferences based on liked categories
    if liked_categories:
        print(f"✅ You seem to prefer: {', '.join(set(liked_categories))}")
    
    # Analyze disliked items for patterns to avoid
    disliked_categories = []
    for item in disliked_items:
        item_lower = item.lower()
        if any(keyword in item_lower for keyword in ['organic', 'natural']):
            disliked_categories.append('organic')
        if any(keyword in item_lower for keyword in ['protein', 'meat', 'fish', 'eggs']):
            disliked_categories.append('protein')
        if any(keyword in item_lower for keyword in ['vegetable', 'veggie', 'greens']):
            disliked_categories.append('vegetables')
        if any(keyword in item_lower for keyword in ['fruit', 'berry']):
            disliked_categories.append('fruits')
        if any(keyword in item_lower for keyword in ['nut', 'seed']):
            disliked_categories.append('nuts_seeds')
    
    if disliked_categories:
        print(f"❌ You seem to avoid: {', '.join(set(disliked_categories))}")

def update_dietary_preferences_from_products(user_profile: dict, recommended_products: list, liked_items: list, disliked_items: list):
    """Update dietary preferences based on product feedback"""
    print("🥗 Analyzing your dietary preferences from product feedback...")
    
    # Analyze recommended products for dietary patterns
    diet_tags = []
    for product in recommended_products:
        tags = product.get('tags', [])
        diet_tags.extend(tags)
    
    # Count diet preferences
    diet_counts = {}
    for tag in diet_tags:
        if tag in ['vegan', 'vegetarian', 'keto', 'low-carb', 'gluten-free', 'high-protein', 'low-fat', 'mediterranean']:
            diet_counts[tag] = diet_counts.get(tag, 0) + 1
    
    # Update dietary preferences based on liked products
    if liked_items and diet_counts:
        most_common_diet = max(diet_counts.items(), key=lambda x: x[1])[0]
        current_diet = user_profile.get('diet', 'omnivore')
        
        if most_common_diet != current_diet:
            print(f"🔄 Updating your diet preference from '{current_diet}' to '{most_common_diet}' based on your feedback")
            user_profile['diet'] = most_common_diet
        else:
            print(f"✅ Your current diet preference '{current_diet}' matches your product choices")
    
    print("📊 Dietary preference analysis complete!")

def handle_general_query_feedback(user_id: str, user_profile: dict, feedback: dict) -> str:
    """Handle feedback for general queries"""
    general_response = feedback.get("general_response", {})
    overall_satisfaction = feedback.get("overall_satisfaction", "")
    query_type = general_response.get("type", "unknown")
    source = general_response.get("source", "dynamodb")
    
    print(f"\n🧠 LEARNING FROM GENERAL QUERY FEEDBACK")
    print("-" * 40)
    
    # Satisfaction analysis
    if overall_satisfaction:
        rating = int(overall_satisfaction)
        if rating >= 4:
            print("😊 Great! You're satisfied with the information provided.")
        elif rating == 3:
            print("😐 You're neutral about the response. We'll try to improve!")
        else:
            print("😔 We're sorry you weren't satisfied. We'll work on better responses.")
    
    # Analyze query type and response
    if query_type == "product_availability":
        found = general_response.get("found", False)
        if found:
            print("✅ Successfully found product information for you.")
        else:
            if source == "llm_fallback":
                print("✅ Provided helpful suggestions using AI when product wasn't found.")
            else:
                print("❌ Couldn't find the requested product. We'll improve our search.")
    
    elif query_type == "past_purchase":
        found = general_response.get("found", False)
        if found:
            print("✅ Successfully retrieved your purchase history.")
        else:
            print("❌ Couldn't access purchase history. This feature requires previous purchases.")
    
    elif query_type == "recipe":
        found = general_response.get("found", False)
        if found:
            print("✅ Successfully found recipe information for you.")
        else:
            if source == "llm_fallback":
                print("✅ Provided helpful cooking advice using AI when recipe wasn't found.")
            else:
                print("❌ Couldn't find the requested recipe. We'll expand our recipe database.")
    
    elif query_type == "promotion":
        found = general_response.get("found", False)
        if found:
            print("✅ Successfully found current promotions for you.")
        else:
            print("ℹ️ No current promotions available. Check back soon for deals!")
    
    elif query_type == "delivery":
        print("✅ Provided delivery and service information.")
    
    elif query_type == "llm_response":
        print("✅ Provided helpful information using AI assistance.")
    
    else:
        print("ℹ️ Processed your general query and provided assistance.")
    
    # Update user profile with query preferences (if user exists)
    if user_profile:
        # Track query types for better future responses
        if 'query_preferences' not in user_profile:
            user_profile['query_preferences'] = {}
        
        query_prefs = user_profile['query_preferences']
        query_prefs[query_type] = query_prefs.get(query_type, 0) + 1
        
        # Track LLM usage
        if source in ["llm_fallback", "llm"]:
            if 'llm_usage' not in user_profile:
                user_profile['llm_usage'] = 0
            user_profile['llm_usage'] += 1
        
        # Save updated profile
        update_user_profile(user_id, user_profile)
        print(f"📝 Updated your query preferences for better future assistance.")
    
    return f"Thank you! We've recorded your feedback for better future assistance with {query_type} queries."

def handle_general_feedback(user_id: str, user_profile: dict, feedback: dict) -> str:
    """Handle general feedback for any query type"""
    overall_satisfaction = feedback.get("overall_satisfaction", "")
    suggestions = feedback.get("suggestions", "")
    
    print(f"\n🧠 LEARNING FROM GENERAL FEEDBACK")
    print("-" * 40)
    
    # Satisfaction analysis
    if overall_satisfaction:
        rating = int(overall_satisfaction)
        if rating >= 4:
            print("😊 Great! You're satisfied with the assistance.")
        elif rating == 3:
            print("😐 You're neutral about the assistance. We'll try to improve!")
        else:
            print("😔 We're sorry you weren't satisfied. We'll work on better assistance.")
    
    # Suggestions handling
    if suggestions:
        print(f"💡 Your suggestion: {suggestions}")
        # Store suggestions for future improvements
        if 'user_suggestions' not in user_profile:
            user_profile['user_suggestions'] = []
        user_profile['user_suggestions'].append(suggestions)
    
    # Save updated profile
    update_user_profile(user_id, user_profile)
    
    return f"Thank you! We've recorded your feedback for better future assistance."

def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> bool:
    """
    Update user preferences based on their interactions
    """
    try:
        user_profile = get_user_profile(user_id)
        if user_profile:
            # Update preferences
            for key, value in preferences.items():
                if key in user_profile:
                    user_profile[key] = value
            
            update_user_profile(user_id, user_profile)
            return True
    except Exception as e:
        print(f"❌ Error updating user preferences: {str(e)}")
        return False
    
    return False

def get_personalized_recommendations(user_id: str) -> Dict[str, Any]:
    """
    Get personalized recommendations based on user's feedback history
    """
    try:
        user_profile = get_user_profile(user_id)
        if not user_profile:
            return {}
        
        recommendations = {
            "preferred_products": user_profile.get('preferred_products', []),
            "avoided_items": user_profile.get('avoided_items', []),
            "past_purchases": user_profile.get('past_purchases', []),
            "suggestions": user_profile.get('user_suggestions', []),
            "query_history": user_profile.get('query_history', [])
        }
        
        return recommendations
        
    except Exception as e:
        print(f"❌ Error getting personalized recommendations: {str(e)}")
        return {}
