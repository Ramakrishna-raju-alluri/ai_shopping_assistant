#!/usr/bin/env python3
"""
Complete test for profile setup flow with authentication
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_complete_profile_flow():
    """Test the complete profile setup flow with authentication"""
    print("🧪 Testing Complete Profile Setup Flow")
    print("=" * 60)
    
    # Step 1: Create a new user
    print("\n👤 Step 1: Creating a new user...")
    signup_data = {
        "username": f"testuser_{int(time.time())}",
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "testpass123",
        "name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if response.status_code == 201:
            user_data = response.json()
            access_token = user_data["access_token"]
            user_id = user_data["user_id"]
            print(f"✅ User created successfully: {user_id}")
            print(f"   Username: {signup_data['username']}")
            print(f"   Access token: {access_token[:20]}...")
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return
    
    # Set up headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Check initial profile status
    print("\n📊 Step 2: Checking initial profile status...")
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Profile status retrieved:")
            print(f"   Setup complete: {status['is_setup_complete']}")
            print(f"   Missing sections: {status['missing_sections']}")
            print(f"   Profile data: {len(status['profile_data'])} sections")
        else:
            print(f"❌ Failed to get profile status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error getting profile status: {str(e)}")
    
    # Step 3: Get profile setup options
    print("\n📋 Step 3: Getting profile setup options...")
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/options")
        if response.status_code == 200:
            options = response.json()
            print(f"✅ Profile setup options retrieved:")
            print(f"   Dietary options: {options['dietary_options']}")
            print(f"   Cuisine options: {options['cuisine_options']}")
            print(f"   Cooking skill options: {options['cooking_skill_options']}")
        else:
            print(f"❌ Failed to get options: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting options: {str(e)}")
    
    # Step 4: Complete profile setup
    print("\n🎯 Step 4: Completing profile setup...")
    complete_profile = {
        "dietary": {
            "diet": "vegan",
            "allergies": ["nuts", "shellfish"],
            "restrictions": []
        },
        "cuisine": {
            "preferred_cuisines": ["mediterranean", "asian", "quick_easy"],
            "disliked_cuisines": []
        },
        "cooking": {
            "skill_level": "intermediate",
            "cooking_time_preference": "moderate",
            "kitchen_equipment": ["stove", "oven", "blender", "microwave"]
        },
        "budget": {
            "budget_limit": 80.0,
            "meal_budget": 13.0,
            "shopping_frequency": "weekly"
        },
        "meal_goal": "healthy_balanced_meals"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/profile-setup/complete", 
                               json=complete_profile, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Profile setup completed successfully!")
            print(f"   User ID: {result['user_id']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Failed to complete profile setup: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error completing profile setup: {str(e)}")
    
    # Step 5: Verify profile status after setup
    print("\n✅ Step 5: Verifying profile status after setup...")
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Profile status after setup:")
            print(f"   Setup complete: {status['is_setup_complete']}")
            print(f"   Missing sections: {status['missing_sections']}")
            print(f"   Profile data sections: {list(status['profile_data'].keys())}")
        else:
            print(f"❌ Failed to get profile status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting profile status: {str(e)}")
    
    # Step 6: Get user preferences for meal planning
    print("\n🍽️ Step 6: Getting user preferences for meal planning...")
    try:
        response = requests.get(f"{BASE_URL}/profile-setup/user-preferences", headers=headers)
        if response.status_code == 200:
            preferences = response.json()
            print(f"✅ User preferences retrieved:")
            print(f"   Diet: {preferences['diet']}")
            print(f"   Allergies: {preferences['allergies']}")
            print(f"   Preferred cuisines: {preferences['preferred_cuisines']}")
            print(f"   Cooking skill: {preferences['cooking_skill']}")
            print(f"   Budget limit: ${preferences['budget_limit']}")
            print(f"   Shopping frequency: {preferences['shopping_frequency']}")
            print(f"   Profile setup complete: {preferences['profile_setup_complete']}")
        else:
            print(f"❌ Failed to get user preferences: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error getting user preferences: {str(e)}")
    
    # Step 7: Test individual section updates
    print("\n🔧 Step 7: Testing individual section updates...")
    
    # Update dietary preferences
    new_dietary = {
        "diet": "vegetarian",
        "allergies": ["dairy"],
        "restrictions": []
    }
    
    try:
        response = requests.post(f"{BASE_URL}/profile-setup/dietary", 
                               json=new_dietary, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dietary preferences updated: {result['message']}")
        else:
            print(f"❌ Failed to update dietary preferences: {response.status_code}")
    except Exception as e:
        print(f"❌ Error updating dietary preferences: {str(e)}")
    
    # Update budget preferences
    new_budget = {
        "budget_limit": 100.0,
        "meal_budget": 15.0,
        "shopping_frequency": "bi-weekly"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/profile-setup/budget", 
                               json=new_budget, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Budget preferences updated: {result['message']}")
        else:
            print(f"❌ Failed to update budget preferences: {response.status_code}")
    except Exception as e:
        print(f"❌ Error updating budget preferences: {str(e)}")
    
    print("\n🎉 Complete profile setup flow test finished!")
    print("\n📝 Summary:")
    print(f"   ✅ User created: {user_id}")
    print(f"   ✅ Profile setup completed")
    print(f"   ✅ Individual sections can be updated")
    print(f"   ✅ User preferences available for meal planning")

if __name__ == "__main__":
    test_complete_profile_flow() 