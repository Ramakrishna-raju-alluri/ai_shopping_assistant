#!/usr/bin/env python3
"""
Test script for profile setup functionality
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_profile_setup():
    """Test the profile setup functionality"""
    print("🧪 Testing Profile Setup Functionality")
    print("=" * 50)
    
    # Test 1: Get profile setup options
    print("\n📋 Test 1: Getting profile setup options...")
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/options")
        if response.status_code == 200:
            options = response.json()
            print("✅ Profile setup options retrieved successfully:")
            print(f"   Dietary options: {len(options['dietary_options'])} options")
            print(f"   Cuisine options: {len(options['cuisine_options'])} options")
            print(f"   Cooking skill options: {len(options['cooking_skill_options'])} options")
        else:
            print(f"❌ Failed to get options: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting options: {str(e)}")
    
    # Test 2: Check profile status (requires authentication)
    print("\n📊 Test 2: Checking profile status...")
    print("   Note: This requires authentication - will show expected structure")
    
    # Example of what the profile status should look like
    example_status = {
        "is_setup_complete": False,
        "missing_sections": ["dietary", "cuisine", "cooking", "budget"],
        "profile_data": {}
    }
    print(f"   Expected structure: {json.dumps(example_status, indent=2)}")
    
    # Test 3: Complete profile setup example
    print("\n🎯 Test 3: Complete profile setup example...")
    
    example_profile = {
        "dietary": {
            "diet": "vegan",
            "allergies": ["nuts"],
            "restrictions": []
        },
        "cuisine": {
            "preferred_cuisines": ["mediterranean", "asian"],
            "disliked_cuisines": []
        },
        "cooking": {
            "skill_level": "intermediate",
            "cooking_time_preference": "moderate",
            "kitchen_equipment": ["stove", "oven", "blender"]
        },
        "budget": {
            "budget_limit": 100.0,
            "meal_budget": 15.0,
            "shopping_frequency": "weekly"
        },
        "meal_goal": "healthy_meals"
    }
    
    print("   Example complete profile setup:")
    print(f"   {json.dumps(example_profile, indent=2)}")
    
    # Test 4: Individual section updates
    print("\n🔧 Test 4: Individual section updates...")
    
    sections = [
        ("dietary", {
            "diet": "vegetarian",
            "allergies": [],
            "restrictions": []
        }),
        ("cuisine", {
            "preferred_cuisines": ["italian", "mexican"],
            "disliked_cuisines": []
        }),
        ("cooking", {
            "skill_level": "beginner",
            "cooking_time_preference": "quick",
            "kitchen_equipment": ["microwave", "stove"]
        }),
        ("budget", {
            "budget_limit": 75.0,
            "meal_budget": 12.0,
            "shopping_frequency": "bi-weekly"
        })
    ]
    
    for section_name, section_data in sections:
        print(f"   {section_name.capitalize()} section: {json.dumps(section_data, indent=4)}")
    
    print("\n✅ Profile setup test structure completed!")
    print("\n📝 Next steps:")
    print("   1. Start the backend server: python main.py")
    print("   2. Test with authenticated user")
    print("   3. Verify profile setup flow in frontend")

if __name__ == "__main__":
    test_profile_setup() 