# agents/preference_agent.py
from dynamo.queries import get_user_profile, create_user_profile
from decimal import Decimal

# Available diet types in recipes
AVAILABLE_DIETS = {
    "gluten-free": ["gluten-free"],
    "high-protein": ["high-protein"],
    "keto": ["keto"],
    "low-fat": ["low-fat"],
    "vegan": ["vegan"],
    "vegetarian": ["vegetarian"],
    "low-carb": ["keto", "low-fat"],  # Map low-carb to keto and low-fat
    "paleo": ["high-protein", "gluten-free"],  # Map paleo to high-protein and gluten-free
    "omnivore": ["vegetarian", "high-protein", "keto", "low-fat"],  # Map omnivore to multiple diets
    "mediterranean": ["vegetarian", "low-fat"],  # Map mediterranean to vegetarian and low-fat
    "dairy-free": ["vegan", "gluten-free"],  # Map dairy-free to vegan and gluten-free
}

# Recipe categories for preference collection
RECIPE_CATEGORIES = {
    "italian": ["pasta", "pizza", "risotto", "lasagna"],
    "asian": ["stir-fry", "curry", "sushi", "noodles"],
    "mexican": ["tacos", "enchiladas", "burritos", "quesadillas"],
    "mediterranean": ["salads", "grilled fish", "hummus", "falafel"],
    "american": ["burgers", "steak", "chicken", "barbecue"],
    "indian": ["curry", "biryani", "dal", "naan"],
    "quick_easy": ["sandwiches", "wraps", "one-pot", "30-minute"],
    "healthy": ["salads", "smoothies", "bowls", "lean protein"]
}

def analyze_purchase_history(past_purchases):
    """Analyze purchase history to suggest diet preferences"""
    if not past_purchases:
        return "vegetarian"  # Default
    
    # Filter out None values and convert to lowercase
    purchases_lower = [item.lower() for item in past_purchases if item is not None]
    
    if not purchases_lower:
        return "vegetarian"  # Default if all items were None
    
    # Diet indicators based on purchase patterns
    diet_indicators = {
        "vegan": ["tofu", "almond milk", "soy milk", "plant-based", "vegan"],
        "vegetarian": ["cheese", "eggs", "milk", "yogurt", "vegetarian"],
        "keto": ["meat", "chicken", "beef", "pork", "fish", "eggs", "cheese", "butter", "avocado"],
        "high-protein": ["chicken", "beef", "fish", "eggs", "protein", "meat"],
        "low-fat": ["skim milk", "low-fat", "lean", "chicken breast", "fish"],
        "gluten-free": ["gluten-free", "quinoa", "rice", "corn", "potato"]
    }
    
    # Count matches for each diet
    diet_scores = {}
    for diet, indicators in diet_indicators.items():
        score = sum(1 for indicator in indicators if any(indicator in purchase for purchase in purchases_lower))
        diet_scores[diet] = score
    
    # Find the diet with highest score
    if diet_scores:
        suggested_diet = max(diet_scores, key=diet_scores.get)
        if diet_scores[suggested_diet] > 0:
            return suggested_diet
    
    return "vegetarian"  # Default fallback

def map_diet_to_available(diet):
    """Map user diet to available recipe diets"""
    if diet is None:
        return "vegetarian"  # Default for None
    
    diet_lower = diet.lower()
    
    # Direct match
    if diet_lower in AVAILABLE_DIETS:
        return diet_lower
    
    # Mapped diets
    for user_diet, available_diets in AVAILABLE_DIETS.items():
        if diet_lower == user_diet:
            # Return the first available diet as primary
            return available_diets[0]
    
    # If no match found, return vegetarian as default
    return "vegetarian"

def collect_new_user_preferences(user_id: str, inferred_profile: dict) -> dict:
    """
    Interactive onboarding for new users to collect preferences
    Enhanced to handle different query types and budget extraction
    """
    print(f"\n🎉 Welcome, {user_id}! Let's set up your profile for personalized recommendations.")
    print("=" * 60)
    
    # Safely extract budget with proper fallback
    budget_value = inferred_profile.get("budget")
    if budget_value is None:
        default_budget = 60
    else:
        try:
            # Try to convert to float first, then to Decimal
            if isinstance(budget_value, str):
                # Remove any non-numeric characters except decimal point
                budget_clean = ''.join(c for c in budget_value if c.isdigit() or c == '.')
                if budget_clean:
                    budget_float = float(budget_clean)
                    default_budget = budget_float
                else:
                    default_budget = 60
            elif isinstance(budget_value, (int, float)):
                default_budget = float(budget_value)
            else:
                default_budget = 60
        except (ValueError, TypeError, AttributeError):
            default_budget = 60
    
    # Ensure budget is a valid number
    if not isinstance(default_budget, (int, float)) or default_budget <= 0:
        default_budget = 60
    
    # Initialize preferences
    preferences = {
        "diet": "vegetarian",  # Default
        "budget_limit": Decimal(str(default_budget)),
        "meal_goal": f"{inferred_profile.get('number_of_meals', 3)} meals",
        "allergies": [],
        "past_purchases": [],
        "shopping_frequency": "weekly",
        "preferred_cuisines": [],
        "cooking_skill": "intermediate"
    }
    
    # Step 1: Dietary Preferences
    print("\n🥗 STEP 1: Dietary Preferences")
    print("-" * 30)
    print("What's your dietary preference? (This helps us suggest suitable recipes)")
    print("Available options:")
    print("1. Vegetarian (no meat, includes dairy and eggs)")
    print("2. Vegan (no animal products)")
    print("3. Keto (low-carb, high-fat)")
    print("4. Low-carb (reduced carbohydrates)")
    print("5. Gluten-free (no gluten)")
    print("6. High-protein (protein-focused)")
    print("7. Low-fat (reduced fat)")
    print("8. Mediterranean (healthy fats, whole grains)")
    print("9. No restrictions (omnivore)")
    print("10. Other (specify)")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-10): ").strip()
            if choice == "1":
                preferences["diet"] = "vegetarian"
                break
            elif choice == "2":
                preferences["diet"] = "vegan"
                break
            elif choice == "3":
                preferences["diet"] = "keto"
                break
            elif choice == "4":
                preferences["diet"] = "low-carb"
                break
            elif choice == "5":
                preferences["diet"] = "gluten-free"
                break
            elif choice == "6":
                preferences["diet"] = "high-protein"
                break
            elif choice == "7":
                preferences["diet"] = "low-fat"
                break
            elif choice == "8":
                preferences["diet"] = "mediterranean"
                break
            elif choice == "9":
                preferences["diet"] = "omnivore"
                break
            elif choice == "10":
                custom_diet = input("Please specify your dietary preference: ").strip().lower()
                preferences["diet"] = map_diet_to_available(custom_diet)
                print(f"   Mapped to: {preferences['diet']}")
                break
            else:
                print("❌ Please enter a valid choice (1-10)")
        except Exception as e:
            print(f"❌ Error: {e}. Please try again.")
    
    # Step 2: Cuisine Preferences
    print("\n🍽️ STEP 2: Cuisine Preferences")
    print("-" * 30)
    print("What types of cuisine do you enjoy? (Select multiple)")
    print("Available cuisines:")
    for i, (cuisine, examples) in enumerate(RECIPE_CATEGORIES.items(), 1):
        print(f"{i}. {cuisine.title()} ({', '.join(examples)})")
    
    cuisine_choices = input("\nEnter your choices (comma-separated, e.g., 1,3,5): ").strip()
    if cuisine_choices:
        try:
            choice_numbers = [int(x.strip()) for x in cuisine_choices.split(",")]
            cuisine_list = list(RECIPE_CATEGORIES.keys())
            selected_cuisines = [cuisine_list[num-1] for num in choice_numbers if 1 <= num <= len(cuisine_list)]
            preferences["preferred_cuisines"] = selected_cuisines
            print(f"   Selected cuisines: {', '.join(selected_cuisines)}")
        except:
            print("   Using default cuisines")
            preferences["preferred_cuisines"] = ["italian", "american"]
    
    # Step 3: Budget Confirmation
    print("\n💰 STEP 3: Budget Preferences")
    print("-" * 30)
    current_budget = preferences["budget_limit"]
    print(f"Current budget: ${current_budget}")
    
    budget_choice = input("Would you like to adjust your budget? (y/n): ").strip().lower()
    if budget_choice in ['y', 'yes']:
        while True:
            try:
                new_budget = input("Enter your preferred budget (e.g., 50): ").strip()
                budget_amount = int(new_budget)
                if budget_amount > 0:
                    preferences["budget_limit"] = Decimal(str(budget_amount))
                    print(f"   Budget updated to: ${budget_amount}")
                    break
                else:
                    print("❌ Budget must be greater than 0")
            except ValueError:
                print("❌ Please enter a valid number")
    
    # Step 4: Cooking Skill Level
    print("\n👨‍🍳 STEP 4: Cooking Experience")
    print("-" * 30)
    print("What's your cooking skill level?")
    print("1. Beginner (new to cooking)")
    print("2. Intermediate (can follow recipes)")
    print("3. Advanced (can improvise and modify recipes)")
    
    while True:
        try:
            skill_choice = input("\nEnter your choice (1-3): ").strip()
            if skill_choice == "1":
                preferences["cooking_skill"] = "beginner"
                break
            elif skill_choice == "2":
                preferences["cooking_skill"] = "intermediate"
                break
            elif skill_choice == "3":
                preferences["cooking_skill"] = "advanced"
                break
            else:
                print("❌ Please enter a valid choice (1-3)")
        except Exception as e:
            print(f"❌ Error: {e}. Please try again.")
    
    # Step 5: Allergies and Restrictions
    print("\n⚠️ STEP 5: Allergies and Restrictions")
    print("-" * 30)
    print("Do you have any food allergies or restrictions? (e.g., nuts, shellfish, dairy)")
    allergies_input = input("Enter allergies (comma-separated, or 'none'): ").strip().lower()
    
    if allergies_input and allergies_input != 'none':
        allergies = [allergy.strip() for allergy in allergies_input.split(",")]
        preferences["allergies"] = allergies
        print(f"   Allergies recorded: {', '.join(allergies)}")
    else:
        print("   No allergies recorded")
    
    # Summary
    print("\n✅ PROFILE SETUP COMPLETE!")
    print("=" * 60)
    print(f"Diet: {preferences['diet']}")
    print(f"Budget: ${preferences['budget_limit']}")
    print(f"Preferred cuisines: {', '.join(preferences['preferred_cuisines'])}")
    print(f"Cooking skill: {preferences['cooking_skill']}")
    if preferences['allergies']:
        print(f"Allergies: {', '.join(preferences['allergies'])}")
    else:
        print("Allergies: None")
    
    print("\n🎯 Your profile is now set up! We'll use these preferences to provide personalized recommendations.")
    print("You can update these preferences anytime by asking for dietary changes or budget adjustments.")
    
    return preferences

def get_or_create_user_profile(user_id: str, inferred_profile: dict) -> dict:
    profile = get_user_profile(user_id)

    if profile:
        # Existing user - update profile with new preferences if provided
        print(f"Welcome back, {user_id}! Using your existing profile.")
        
        # Analyze purchase history for diet suggestions
        past_purchases = profile.get("past_purchases", [])
        if past_purchases:
            suggested_diet = analyze_purchase_history(past_purchases)
            current_diet = profile.get("diet", "vegetarian")
            
            # If current diet doesn't match available diets, suggest based on purchases
            if current_diet not in AVAILABLE_DIETS and suggested_diet != current_diet:
                mapped_diet = map_diet_to_available(suggested_diet)
                print(f"   Based on your purchase history, suggesting {mapped_diet} diet")
                profile["diet"] = mapped_diet
            elif current_diet not in AVAILABLE_DIETS:
                # Map current diet to available diet
                mapped_diet = map_diet_to_available(current_diet)
                print(f"   Mapping your {current_diet} diet to {mapped_diet} for recipe matching")
                profile["diet"] = mapped_diet
        
        # Update preferences if new ones are provided
        if inferred_profile.get("dietary_preference"):
            new_diet = inferred_profile["dietary_preference"]
            mapped_diet = map_diet_to_available(new_diet)
            profile["diet"] = mapped_diet
            print(f"   Updated diet preference to: {mapped_diet}")
            
        if inferred_profile.get("budget"):
            profile["budget_limit"] = Decimal(str(inferred_profile["budget"]))
        if inferred_profile.get("number_of_meals"):
            profile["meal_goal"] = f"{inferred_profile['number_of_meals']} meals"
        
        # Show user's past purchases for context
        if profile.get("past_purchases"):
            print(f"Based on your past purchases: {', '.join(profile['past_purchases'][:5])}")
        
        return profile
    else:
        # New user – interactive onboarding
        print(f"Welcome, {user_id}! Let's set up your profile.")
        
        # Collect preferences through interactive questions
        new_profile = collect_new_user_preferences(user_id, inferred_profile)
        
        # Create the profile in database
        create_user_profile(user_id, new_profile)
        
        return new_profile
